"""Stable post-restore verification for the v0.6.6 Off-grid SOC write.

The guarded writer verifies register 43137 before restoring a temporarily
changed work-mode. Hardware testing showed that this is not sufficient proof of
persistence: the inverter may change the child setting shortly after the
original work-mode is restored. A write is therefore only considered successful
after repeated fresh settings reads across a short post-restore settle window.
"""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import AutarcoConnectionError, OFF_GRID_MINIMUM_SOC_REGISTER
from .settings_write_v066 import async_write_off_grid_minimum_soc_v066

# Delays are cumulative. The final confirmation therefore happens roughly
# 7.5 seconds after the guarded transaction completed, which is long enough to
# catch the delayed child-setting rollback observed on the home inverter while
# still keeping an interactive write reasonably quick.
POST_RESTORE_VERIFY_DELAYS_SECONDS = (0.5, 2.0, 5.0)


async def _async_fresh_settings_read(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
):
    """Read settings without blocking Home Assistant's event loop."""
    try:
        return await hass.async_add_executor_job(coordinator.client.read_settings)
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            "ONZEKER — write-transactie afgerond, maar een finale post-restore "
            f"settings-read mislukte: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(
            "Write kan niet als succesvol worden beschouwd: een finale post-restore "
            f"read-back mislukte: {err}"
        ) from err


async def async_write_off_grid_minimum_soc_v066_final(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> None:
    """Write and require stable post-restore read-back of the target register."""
    requested = int(requested)

    await async_write_off_grid_minimum_soc_v066(hass, coordinator, requested)

    elapsed = 0.0
    observed_values: list[int] = []

    for delay in POST_RESTORE_VERIFY_DELAYS_SECONDS:
        await asyncio.sleep(delay)
        elapsed += delay
        fresh = await _async_fresh_settings_read(hass, coordinator)

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
                "Write kan niet als succesvol worden beschouwd: Off-grid minimum SOC "
                "kon na het work-mode herstel niet opnieuw worden uitgelezen."
            )

        final_value = int(final_value)
        observed_values.append(final_value)
        coordinator.settings_last_write_value = final_value

        if final_value != requested:
            coordinator.settings_last_write_diagnostic = (
                f"NIET BLIJVEND — doel {requested}% was tijdens de write bevestigd, "
                f"maar {elapsed:.1f}s na herstel van de oorspronkelijke work-mode leest "
                f"register 43137 {final_value}% (post-restore reeks: {observed_values})."
            )
            coordinator.async_update_listeners()
            raise HomeAssistantError(
                f"Off-grid minimum SOC bleef niet op {requested}% staan na work-mode "
                f"herstel; na {elapsed:.1f}s is de read-back {final_value}%. Er wordt "
                "geen succes gemeld."
            )

    coordinator.settings_last_write_value = requested
    coordinator.settings_last_write_diagnostic = (
        f"SUCCES — Off-grid minimum SOC bleef na volledige work-mode restore stabiel "
        f"op {requested}% tijdens {len(observed_values)} post-restore controles over "
        f"{elapsed:.1f}s."
    )
    coordinator.async_update_listeners()
