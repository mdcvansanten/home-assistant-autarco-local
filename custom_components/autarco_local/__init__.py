"""Autarco Local integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, PLATFORMS
from .coordinator import AutarcoLocalCoordinator
from .modbus_client import (
    AutarcoConnectionError,
    OFF_GRID_MINIMUM_SOC_PILOT_FROM,
    OFF_GRID_MINIMUM_SOC_PILOT_TO,
    OFF_GRID_MINIMUM_SOC_REGISTER,
    OFF_GRID_MODE_MASK,
    STORAGE_MODE_REGISTER,
)
from .settings_panel import async_register_settings_panel, unregister_settings_panel

type AutarcoLocalConfigEntry = ConfigEntry[AutarcoLocalCoordinator]

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_OFF_GRID_MINIMUM_SOC = "set_off_grid_minimum_soc"
DATA_WRITE_SERVICE_REGISTERED = f"{DOMAIN}_write_service_registered"
BATTERY_SOC_REGISTER = 33139
TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC = 30

WRITE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("soc"): vol.All(
            vol.Coerce(int),
            vol.In([OFF_GRID_MINIMUM_SOC_PILOT_TO]),
        ),
        vol.Required("confirm"): vol.In([True]),
        vol.Optional("config_entry_id"): str,
    }
)


def _loaded_coordinator(
    hass: HomeAssistant, config_entry_id: str | None
) -> AutarcoLocalCoordinator:
    """Resolve exactly one loaded Autarco Local coordinator for a write."""
    if config_entry_id:
        entry = hass.config_entries.async_get_entry(config_entry_id)
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise HomeAssistantError(
                "De gekozen Autarco Local-configuratie is niet geladen."
            )
        return entry.runtime_data

    loaded = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if not loaded:
        raise HomeAssistantError("Er is geen geladen Autarco Local-configuratie.")
    if len(loaded) > 1:
        raise HomeAssistantError(
            "Er zijn meerdere Autarco Local-configuraties geladen; geef config_entry_id op."
        )
    return loaded[0].runtime_data


async def _async_handle_set_off_grid_minimum_soc(
    hass: HomeAssistant, call: ServiceCall
) -> None:
    """Execute the single dependency-aware Off-grid minimum SOC write pilot."""
    coordinator = _loaded_coordinator(hass, call.data.get("config_entry_id"))
    requested = int(call.data["soc"])

    # Refresh the settings snapshot before the UI/service-level safety preflight.
    try:
        fresh = await hass.async_add_executor_job(coordinator.client.read_settings)
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            f"AFGEBROKEN — verse settings-read mislukt: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            f"Verse settings-read mislukt; write niet uitgevoerd: {err}"
        ) from err

    coordinator.settings_data = fresh.registers
    coordinator.settings_read_time_ms = fresh.read_duration_ms
    coordinator.settings_unsupported_blocks = fresh.unsupported_blocks

    current = coordinator.settings_data.get(OFF_GRID_MINIMUM_SOC_REGISTER)
    mode_value = coordinator.settings_data.get(STORAGE_MODE_REGISTER)
    battery_soc = (coordinator.data or {}).get(BATTERY_SOC_REGISTER)

    if current == requested:
        coordinator.settings_last_write_diagnostic = (
            f"GEEN WIJZIGING — Off-grid minimum SOC staat al op {requested}%"
        )
        coordinator.async_update_listeners()
        return

    if current != OFF_GRID_MINIMUM_SOC_PILOT_FROM:
        raise HomeAssistantError(
            "Deze hardwarepilot staat alleen de gevalideerde overgang "
            f"{OFF_GRID_MINIMUM_SOC_PILOT_FROM}% → {OFF_GRID_MINIMUM_SOC_PILOT_TO}% toe; "
            f"actueel is {current!r}%."
        )
    if mode_value is None:
        raise HomeAssistantError(
            f"Work-mode register {STORAGE_MODE_REGISTER} is niet beschikbaar; write afgebroken."
        )

    off_grid_was_active = bool(mode_value & OFF_GRID_MODE_MASK)
    if not off_grid_was_active:
        if battery_soc is None:
            raise HomeAssistantError(
                "Batterij-SOC is niet beschikbaar. Autarco Local activeert Off-grid daarom "
                "niet tijdelijk voor deze pilot."
            )
        if int(battery_soc) < TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC:
            raise HomeAssistantError(
                "Write afgebroken: voor deze eerste pilot activeert Autarco Local Off-grid "
                f"niet tijdelijk onder {TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC}% batterij-SOC "
                f"(actueel {battery_soc}%)."
            )

    coordinator.settings_last_write_diagnostic = (
        f"GESTART — Off-grid minimum SOC {current}% → {requested}%; "
        + (
            "Off-grid stond al AAN en blijft AAN."
            if off_grid_was_active
            else "Off-grid wordt tijdelijk geactiveerd en de oorspronkelijke work-mode wordt hersteld."
        )
    )
    coordinator.async_update_listeners()

    try:
        result = await hass.async_add_executor_job(
            coordinator.client.write_off_grid_minimum_soc_pilot,
            requested,
        )
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            f"MISLUKT — Off-grid minimum SOC {current}% → {requested}%: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(str(err)) from err
    except Exception as err:
        _LOGGER.exception("Onverwachte fout tijdens Off-grid SOC write-service")
        coordinator.settings_last_write_diagnostic = (
            f"MISLUKT — onverwachte {type(err).__name__}: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            f"Onverwachte fout tijdens Off-grid SOC write: {err}"
        ) from err

    coordinator.settings_data[result.register] = result.verified_value
    coordinator.settings_last_write_register = result.register
    coordinator.settings_last_write_previous_value = result.previous_value
    coordinator.settings_last_write_value = result.verified_value
    coordinator.settings_last_write_duration_ms = result.duration_ms
    coordinator.settings_last_write_dependency_was_active = result.dependency_was_active
    coordinator.settings_last_write_dependency_temporarily_enabled = (
        result.dependency_temporarily_enabled
    )
    coordinator.settings_last_write_dependency_restored = result.dependency_restored
    coordinator.settings_last_write_diagnostic = (
        f"SUCCES — Off-grid minimum SOC {result.previous_value}% → "
        f"{result.verified_value}% geverifieerd; "
        + (
            "Off-grid stond al AAN en is AAN gebleven."
            if result.dependency_was_active
            else "tijdelijke Off-grid activatie is afgerond en de oorspronkelijke work-mode is hersteld."
        )
    )
    coordinator.async_update_listeners()
    _LOGGER.warning(
        "Off-grid minimum SOC succesvol gewijzigd: %s%% -> %s%% "
        "(dependency_was_active=%s, temporarily_enabled=%s, restored=%s)",
        result.previous_value,
        result.verified_value,
        result.dependency_was_active,
        result.dependency_temporarily_enabled,
        result.dependency_restored,
    )


def _async_register_write_service(hass: HomeAssistant) -> None:
    """Register the guarded write service once per Home Assistant runtime."""
    if hass.data.get(DATA_WRITE_SERVICE_REGISTERED):
        return

    async def handle(call: ServiceCall) -> None:
        await _async_handle_set_off_grid_minimum_soc(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_OFF_GRID_MINIMUM_SOC,
        handle,
        schema=WRITE_SERVICE_SCHEMA,
    )
    hass.data[DATA_WRITE_SERVICE_REGISTERED] = True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Set up Autarco Local from a config entry."""
    coordinator = AutarcoLocalCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_settings_panel(hass, entry.entry_id)
    _async_register_write_service(hass)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        unregister_settings_panel(hass, entry.entry_id)
        await entry.runtime_data.async_shutdown()
    return unloaded


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> None:
    """Reload the integration after the entry changes."""
    await hass.config_entries.async_reload(entry.entry_id)
