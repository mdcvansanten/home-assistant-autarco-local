"""Autarco Local integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import AutarcoLocalCoordinator
from .settings_panel import async_register_settings_panel, unregister_settings_panel
from .settings_security import (
    clear_entry_unlocks,
    lock_settings,
    pin_is_configured,
    settings_are_unlocked,
    unlock_settings,
    verify_pin,
)
from .settings_write_v066 import (
    OFF_GRID_MINIMUM_SOC_MAX,
    OFF_GRID_MINIMUM_SOC_MIN,
)
from .settings_write_v066_safety import (
    async_write_off_grid_minimum_soc_v066_safe,
)

type AutarcoLocalConfigEntry = ConfigEntry[AutarcoLocalCoordinator]

SERVICE_UNLOCK_SETTINGS = "unlock_settings"
SERVICE_LOCK_SETTINGS = "lock_settings"
SERVICE_SET_OFF_GRID_MINIMUM_SOC = "set_off_grid_minimum_soc"
DATA_SERVICES_REGISTERED = f"{DOMAIN}_services_registered"

UNLOCK_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("pin"): str,
        vol.Optional("config_entry_id"): str,
    }
)

LOCK_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("config_entry_id"): str,
    }
)

WRITE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("soc"): vol.All(
            vol.Coerce(int),
            vol.Range(min=OFF_GRID_MINIMUM_SOC_MIN, max=OFF_GRID_MINIMUM_SOC_MAX),
        ),
        vol.Required("confirm"): vol.In([True]),
        vol.Optional("config_entry_id"): str,
    }
)


def _loaded_entry_and_coordinator(
    hass: HomeAssistant,
    config_entry_id: str | None,
) -> tuple[AutarcoLocalConfigEntry, AutarcoLocalCoordinator]:
    """Resolve exactly one loaded Autarco Local config entry."""
    if config_entry_id:
        entry = hass.config_entries.async_get_entry(config_entry_id)
        if (
            entry is None
            or entry.domain != DOMAIN
            or entry.state is not ConfigEntryState.LOADED
        ):
            raise HomeAssistantError(
                "De gekozen Autarco Local-configuratie is niet geladen."
            )
        return entry, entry.runtime_data

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
    entry = loaded[0]
    return entry, entry.runtime_data


def _service_user_id(call: ServiceCall) -> str:
    """Return the Home Assistant user behind an interactive settings action."""
    user_id = call.context.user_id
    if not user_id:
        raise HomeAssistantError(
            "Deze instellingenactie vereist een ingelogde Home Assistant-gebruiker."
        )
    return user_id


async def _async_handle_unlock_settings(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Unlock write-capable settings for one user for ten minutes."""
    user_id = _service_user_id(call)
    entry, _ = _loaded_entry_and_coordinator(
        hass,
        call.data.get("config_entry_id"),
    )
    if not pin_is_configured(entry):
        raise HomeAssistantError(
            "Er is nog geen instellingen-PIN ingesteld. Open Autarco Local → Configureren "
            "en stel eerst een PIN van 4 tot 8 cijfers in."
        )

    # PBKDF2 verification is deliberately moved off Home Assistant's event loop.
    # This keeps the UI responsive even on slower Raspberry Pi hardware.
    pin_valid = await hass.async_add_executor_job(
        verify_pin,
        entry,
        str(call.data["pin"]),
    )
    if not pin_valid:
        raise HomeAssistantError("Onjuiste instellingen-PIN.")
    unlock_settings(hass, entry.entry_id, user_id)


async def _async_handle_lock_settings(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Immediately lock write-capable settings for one user."""
    user_id = _service_user_id(call)
    entry, _ = _loaded_entry_and_coordinator(
        hass,
        call.data.get("config_entry_id"),
    )
    lock_settings(hass, entry.entry_id, user_id)


async def _async_handle_set_off_grid_minimum_soc(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Execute the guarded dependency-aware Off-grid minimum SOC write."""
    user_id = _service_user_id(call)
    entry, coordinator = _loaded_entry_and_coordinator(
        hass,
        call.data.get("config_entry_id"),
    )
    if not settings_are_unlocked(hass, entry.entry_id, user_id):
        raise HomeAssistantError(
            "Autarco Local-instellingen zijn vergrendeld. Ontgrendel eerst met de instellingen-PIN."
        )
    await async_write_off_grid_minimum_soc_v066_safe(
        hass,
        coordinator,
        int(call.data["soc"]),
    )


def _async_register_services(hass: HomeAssistant) -> None:
    """Register Autarco Local service actions once per Home Assistant runtime."""
    if hass.data.get(DATA_SERVICES_REGISTERED):
        return

    async def unlock_handler(call: ServiceCall) -> None:
        await _async_handle_unlock_settings(hass, call)

    async def lock_handler(call: ServiceCall) -> None:
        await _async_handle_lock_settings(hass, call)

    async def write_handler(call: ServiceCall) -> None:
        await _async_handle_set_off_grid_minimum_soc(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNLOCK_SETTINGS,
        unlock_handler,
        schema=UNLOCK_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOCK_SETTINGS,
        lock_handler,
        schema=LOCK_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_OFF_GRID_MINIMUM_SOC,
        write_handler,
        schema=WRITE_SERVICE_SCHEMA,
    )
    hass.data[DATA_SERVICES_REGISTERED] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration-level Autarco Local services."""
    _async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Set up Autarco Local from a config entry."""
    # Register the UI before talking to the logger. This keeps the Autarco Local
    # dashboard/diagnostics route available when the LAN stick is temporarily
    # unavailable during Home Assistant startup.
    await async_register_settings_panel(hass, entry.entry_id)

    coordinator = AutarcoLocalCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Unload Autarco Local from a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        clear_entry_unlocks(hass, entry.entry_id)
        unregister_settings_panel(hass, entry.entry_id)
        await entry.runtime_data.async_shutdown()
    return unloaded


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> None:
    """Reload the integration after the entry changes."""
    await hass.config_entries.async_reload(entry.entry_id)
