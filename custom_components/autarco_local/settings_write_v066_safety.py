"""Safety gate for the v0.6.6 Off-grid minimum SOC hardware test.

The current inverter battery-SOC register can show a plausible value even when
the Dyness towers are not actually connected to the Connectbox. That source is
therefore not trusted for deciding whether Autarco Local may temporarily enable
Off-grid mode.

Until a reliable live battery-SOC source is validated, Autarco Local only allows
this write when Off-grid is already active before the transaction. In that case
no temporary mode activation is needed and the unreliable SOC value is not used
as a safety prerequisite.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import AutarcoConnectionError, OFF_GRID_MODE_MASK, STORAGE_MODE_REGISTER
from .settings_write_v066_final_verify import (
    async_write_off_grid_minimum_soc_v066_final,
)

BATTERY_SOC_TRUSTED_FOR_TEMPORARY_OFF_GRID = False


async def async_write_off_grid_minimum_soc_v066_safe(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> None:
    """Apply the current hardware safety gate, then run the final verified write."""
    try:
        fresh = await hass.async_add_executor_job(coordinator.client.read_settings)
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            f"AFGEBROKEN — safety pre-read mislukt: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            f"Safety pre-read mislukt; write niet uitgevoerd: {err}"
        ) from err

    coordinator.settings_data = fresh.registers
    coordinator.settings_read_time_ms = fresh.read_duration_ms
    coordinator.settings_unsupported_blocks = fresh.unsupported_blocks

    mode_value = fresh.registers.get(STORAGE_MODE_REGISTER)
    if mode_value is None:
        coordinator.settings_last_write_diagnostic = (
            f"AFGEBROKEN — work-mode register {STORAGE_MODE_REGISTER} ontbreekt in safety pre-read."
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            f"Work-mode register {STORAGE_MODE_REGISTER} is niet beschikbaar; write afgebroken."
        )

    off_grid_is_active = bool(int(mode_value) & OFF_GRID_MODE_MASK)
    if not off_grid_is_active and not BATTERY_SOC_TRUSTED_FOR_TEMPORARY_OFF_GRID:
        coordinator.settings_last_write_diagnostic = (
            "AFGEBROKEN — Off-grid staat UIT en de huidige live batterij-SOC bron is "
            "nog niet betrouwbaar genoeg om tijdelijke Off-grid-activatie veilig toe te staan."
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            "Tijdelijke Off-grid-activatie is geblokkeerd: de huidige batterij-SOC bron "
            "is nog niet als betrouwbaar safety-signaal gevalideerd. Zet Off-grid niet "
            "automatisch aan vanuit Autarco Local totdat een betrouwbare SOC-bron is bewezen."
        )

    await async_write_off_grid_minimum_soc_v066_final(
        hass,
        coordinator,
        int(requested),
    )
