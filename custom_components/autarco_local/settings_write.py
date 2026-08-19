"""Guarded settings write controller for Autarco Local."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import (
    AutarcoConnectionError,
    OFF_GRID_MINIMUM_SOC_PILOT_FROM,
    OFF_GRID_MINIMUM_SOC_PILOT_TO,
    OFF_GRID_MINIMUM_SOC_REGISTER,
    OFF_GRID_MODE_MASK,
    STORAGE_MODE_REGISTER,
)

_LOGGER = logging.getLogger(__name__)

BATTERY_SOC_REGISTER = 33139
TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC = 30


async def async_write_off_grid_minimum_soc(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> None:
    """Execute the single dependency-aware Off-grid minimum SOC hardware pilot."""
    requested = int(requested)
    if requested != OFF_GRID_MINIMUM_SOC_PILOT_TO:
        raise HomeAssistantError(
            "Deze hardwarepilot staat uitsluitend Off-grid minimum SOC 10% → 20% toe."
        )

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
                "Write afgebroken: Autarco Local activeert Off-grid voor deze eerste pilot "
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
        _LOGGER.exception("Onverwachte fout tijdens Off-grid SOC write")
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
