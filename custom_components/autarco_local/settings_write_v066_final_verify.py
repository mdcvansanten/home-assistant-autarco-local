"""Final post-restore verification for the v0.6.6 Off-grid SOC write.

The guarded writer verifies register 43137 before restoring a temporarily
changed work-mode. Hardware testing showed that this is not sufficient proof of
persistence: the inverter may change the child setting when the original
work-mode is restored. A write is therefore only considered successful after a
fresh settings read *after* the complete transaction has finished.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import AutarcoConnectionError, OFF_GRID_MINIMUM_SOC_REGISTER
from .settings_write_v066 import async_write_off_grid_minimum_soc_v066


async def async_write_off_grid_minimum_soc_v066_final(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> None:
    """Write and require a fresh post-restore read-back of the target register."""
    requested = int(requested)

    await async_write_off_grid_minimum_soc_v066(hass, coordinator, requested)

    try:
        fresh = await hass.async_add_executor_job(coordinator.client.read_settings)
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            "ONZEKER — write-transactie afgerond, maar finale post-restore settings-read "
            f"mislukte: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            "Write kan niet als succesvol worden beschouwd: de finale post-restore "
            f"read-back mislukte: {err}"
        ) from err

    coordinator.settings_data = fresh.registers
    coordinator.settings_read_time_ms = fresh.read_duration_ms
    coordinator.settings_unsupported_blocks = fresh.unsupported_blocks

    final_value = fresh.registers.get(OFF_GRID_MINIMUM_SOC_REGISTER)
    if final_value is None:
        coordinator.settings_last_write_diagnostic = (
            "ONZEKER — finale post-restore read bevatte register 43137 niet."
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            "Write kan niet als succesvol worden beschouwd: Off-grid minimum SOC kon "
            "na het work-mode herstel niet opnieuw worden uitgelezen."
        )

    if int(final_value) != requested:
        coordinator.settings_last_write_diagnostic = (
            f"NIET BLIJVEND — doel {requested}% was tijdens de write bevestigd, maar "
            f"na herstel van de oorspronkelijke work-mode leest register 43137 "
            f"{final_value}%."
        )
        coordinator.settings_last_write_value = int(final_value)
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            f"Off-grid minimum SOC bleef niet op {requested}% staan na work-mode herstel; "
            f"finale read-back is {final_value}%. Er wordt geen succes gemeld."
        )

    coordinator.settings_last_write_value = int(final_value)
    coordinator.settings_last_write_diagnostic = (
        f"SUCCES — Off-grid minimum SOC staat na volledige work-mode restore en finale "
        f"read-back nog steeds op {final_value}%."
    )
    coordinator.async_update_listeners()
