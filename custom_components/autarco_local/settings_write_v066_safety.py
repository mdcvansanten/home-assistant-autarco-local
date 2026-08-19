"""Safety gate for the v0.6.6 Off-grid minimum SOC hardware test.

The inverter-derived battery-SOC register is not trusted as a safety prerequisite
because hardware testing showed a plausible 99% while the Dyness towers were not
actually connected to the Connectbox.

Instead, the user explicitly selects a Home Assistant sensor as the trusted
battery-SOC source. This keeps the design vendor-neutral: today that can be the
Dyness SOC sensor, while another battery integration can be selected later.
"""

from __future__ import annotations

from homeassistant.const import PERCENTAGE, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_BATTERY_SOC_ENTITY
from .coordinator import AutarcoLocalCoordinator
from .modbus_client import AutarcoConnectionError, OFF_GRID_MODE_MASK, STORAGE_MODE_REGISTER
from .settings_write_v066 import TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC
from .settings_write_v066_final_verify import (
    async_write_off_grid_minimum_soc_v066_final,
)


def _trusted_battery_soc(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
) -> tuple[float, str]:
    """Return the explicitly configured live battery SOC and its entity id."""
    entity_id = str(
        coordinator.config_entry.options.get(CONF_BATTERY_SOC_ENTITY, "") or ""
    ).strip()
    if not entity_id:
        raise HomeAssistantError(
            "Geen betrouwbare batterij-SOC bron ingesteld. Kies in Autarco Local → "
            "Configureren een Home Assistant batterij-SOC sensor."
        )

    state = hass.states.get(entity_id)
    if state is None:
        raise HomeAssistantError(
            f"De ingestelde batterij-SOC bron {entity_id} bestaat niet in Home Assistant."
        )
    if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, "none", "None", ""):
        raise HomeAssistantError(
            f"De ingestelde batterij-SOC bron {entity_id} is momenteel niet beschikbaar."
        )

    unit = state.attributes.get("unit_of_measurement")
    if unit != PERCENTAGE:
        raise HomeAssistantError(
            f"De ingestelde batterij-SOC bron {entity_id} gebruikt een onverwachte eenheid "
            f"({unit or 'geen'} in plaats van %)."
        )

    try:
        value = float(str(state.state).replace(",", "."))
    except ValueError as err:
        raise HomeAssistantError(
            f"De ingestelde batterij-SOC bron {entity_id} bevat geen numeriek percentage."
        ) from err

    if not 0 <= value <= 100:
        raise HomeAssistantError(
            f"De ingestelde batterij-SOC bron {entity_id} geeft {value:g}%; verwacht 0–100%."
        )

    return value, entity_id


async def async_write_off_grid_minimum_soc_v066_safe(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> None:
    """Validate the trusted SOC source before any temporary Off-grid activation."""
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
    trusted_soc: float | None = None
    trusted_entity_id: str | None = None

    if not off_grid_is_active:
        try:
            trusted_soc, trusted_entity_id = _trusted_battery_soc(hass, coordinator)
        except HomeAssistantError as err:
            coordinator.settings_last_write_diagnostic = f"AFGEBROKEN — {err}"
            coordinator.async_update_listeners()
            raise

        if trusted_soc < TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC:
            coordinator.settings_last_write_diagnostic = (
                "AFGEBROKEN — betrouwbare batterij-SOC bron "
                f"{trusted_entity_id} geeft {trusted_soc:g}%; voor tijdelijke Off-grid-"
                f"activatie is minimaal {TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC}% vereist."
            )
            coordinator.async_update_listeners()
            raise HomeAssistantError(
                "Tijdelijke Off-grid-activatie geblokkeerd: betrouwbare batterij-SOC is "
                f"{trusted_soc:g}% en moet minimaal "
                f"{TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC}% zijn."
            )

        coordinator.settings_last_write_diagnostic = (
            "SAFETY OK — tijdelijke Off-grid-activatie toegestaan op basis van "
            f"{trusted_entity_id} = {trusted_soc:g}%."
        )
        coordinator.async_update_listeners()

    await async_write_off_grid_minimum_soc_v066_final(
        hass,
        coordinator,
        int(requested),
        trusted_battery_soc=trusted_soc,
    )
