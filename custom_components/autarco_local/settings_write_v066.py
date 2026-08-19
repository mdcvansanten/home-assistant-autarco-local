"""Validated-range Off-grid SOC writer for the v0.6.6 hardware test.

This deliberately reuses the already proven state-preservation rules from the
v0.6.3-v0.6.5 pilot, but opens the *same* register to the documented 10-100%
range so the current installation can perform a small reversible write test.
No other setting/register becomes writable here.
"""

from __future__ import annotations

import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoWriteResult,
    OFF_GRID_MINIMUM_SOC_REGISTER,
    OFF_GRID_MODE_MASK,
    STORAGE_MODE_REGISTER,
)

_LOGGER = logging.getLogger(__name__)

OFF_GRID_MINIMUM_SOC_MIN = 10
OFF_GRID_MINIMUM_SOC_MAX = 100
TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC = 30


def _write_transaction(client, requested_value: int) -> AutarcoWriteResult:
    """Write one Off-grid minimum SOC value while preserving original mode state."""
    requested_value = int(requested_value)
    if not OFF_GRID_MINIMUM_SOC_MIN <= requested_value <= OFF_GRID_MINIMUM_SOC_MAX:
        raise AutarcoConnectionError(
            f"Off-grid minimum SOC moet tussen {OFF_GRID_MINIMUM_SOC_MIN}% en "
            f"{OFF_GRID_MINIMUM_SOC_MAX}% liggen"
        )

    # The helpers are private to the client because this remains a narrowly
    # guarded development transaction rather than a generic public write API.
    with client._lock:  # noqa: SLF001
        client._ensure_connected_locked(  # noqa: SLF001
            "socket was niet verbonden vóór Off-grid SOC settings-write"
        )
        started = time.monotonic()

        previous_value = client._read_single_holding_locked(  # noqa: SLF001
            OFF_GRID_MINIMUM_SOC_REGISTER,
            "Pre-write read Off-grid minimum SOC mislukt",
        )
        if not OFF_GRID_MINIMUM_SOC_MIN <= previous_value <= OFF_GRID_MINIMUM_SOC_MAX:
            raise AutarcoConnectionError(
                f"Write afgebroken: onverwachte huidige Off-grid SOC {previous_value}%"
            )
        if previous_value == requested_value:
            return AutarcoWriteResult(
                register=OFF_GRID_MINIMUM_SOC_REGISTER,
                previous_value=previous_value,
                requested_value=requested_value,
                verified_value=previous_value,
                duration_ms=round((time.monotonic() - started) * 1000, 1),
                dependency_was_active=False,
                dependency_temporarily_enabled=False,
                dependency_restored=True,
            )

        original_mode_value = client._read_single_holding_locked(  # noqa: SLF001
            STORAGE_MODE_REGISTER,
            "Pre-write read storage mode mislukt",
        )
        dependency_was_active = bool(original_mode_value & OFF_GRID_MODE_MASK)
        dependency_temporarily_enabled = False
        dependency_restored = True
        mode_after_enable = original_mode_value
        target_verified_value: int | None = None
        target_error: AutarcoConnectionError | None = None
        cleanup_error: AutarcoConnectionError | None = None

        try:
            if not dependency_was_active:
                enable_value = original_mode_value | OFF_GRID_MODE_MASK
                client._write_single_holding_locked(  # noqa: SLF001
                    STORAGE_MODE_REGISTER,
                    enable_value,
                    "Tijdelijk activeren Off-grid mode mislukt",
                )
                # Validate the Off-grid bit, but keep the *actual* resulting full
                # mode register. The inverter may itself clear mutually exclusive
                # mode bits when Off-grid is activated.
                mode_after_enable = client._verify_single_holding_locked(  # noqa: SLF001
                    STORAGE_MODE_REGISTER,
                    enable_value,
                    "Off-grid mode kon niet worden bevestigd",
                    mask=OFF_GRID_MODE_MASK,
                )
                dependency_temporarily_enabled = True

            client._write_single_holding_locked(  # noqa: SLF001
                OFF_GRID_MINIMUM_SOC_REGISTER,
                requested_value,
                "Off-grid minimum SOC write mislukt",
            )
            target_verified_value = client._verify_single_holding_locked(  # noqa: SLF001
                OFF_GRID_MINIMUM_SOC_REGISTER,
                requested_value,
                "Off-grid minimum SOC kon niet worden bevestigd",
            )
        except AutarcoConnectionError as err:
            target_error = err
        finally:
            if dependency_temporarily_enabled:
                try:
                    observed_before_restore = client._read_single_holding_locked(  # noqa: SLF001
                        STORAGE_MODE_REGISTER,
                        "Mode-state vóór restore kon niet worden gelezen",
                    )
                    if observed_before_restore != mode_after_enable:
                        raise AutarcoConnectionError(
                            "Restore afgebroken: storage mode veranderde extern tijdens "
                            f"de transactie (verwacht {mode_after_enable}, ontvangen "
                            f"{observed_before_restore})"
                        )
                    client._write_single_holding_locked(  # noqa: SLF001
                        STORAGE_MODE_REGISTER,
                        original_mode_value,
                        "Herstellen oorspronkelijke storage mode mislukt",
                    )
                    client._verify_single_holding_locked(  # noqa: SLF001
                        STORAGE_MODE_REGISTER,
                        original_mode_value,
                        "Oorspronkelijke storage mode kon niet worden bevestigd",
                    )
                    dependency_restored = True
                except AutarcoConnectionError as err:
                    dependency_restored = False
                    cleanup_error = err

        if cleanup_error is not None:
            if target_error is not None:
                raise AutarcoConnectionError(
                    f"Target write mislukt ({target_error}); bovendien kon de "
                    f"oorspronkelijke mode niet veilig worden hersteld ({cleanup_error})"
                ) from cleanup_error
            raise AutarcoConnectionError(
                "Off-grid minimum SOC is mogelijk gewijzigd, maar de oorspronkelijke "
                f"storage mode kon niet veilig worden hersteld: {cleanup_error}"
            ) from cleanup_error

        if target_error is not None:
            raise target_error
        if target_verified_value != requested_value:
            raise AutarcoConnectionError(
                f"Interne fout: target write is niet als {requested_value}% geverifieerd"
            )

        duration_ms = round((time.monotonic() - started) * 1000, 1)
        _LOGGER.warning(
            "Gecontroleerde Off-grid SOC settings-write: register %s %s%% -> %s%%; "
            "off-grid vooraf=%s, tijdelijk geactiveerd=%s, restore=%s, %.1f ms",
            OFF_GRID_MINIMUM_SOC_REGISTER,
            previous_value,
            target_verified_value,
            dependency_was_active,
            dependency_temporarily_enabled,
            dependency_restored,
            duration_ms,
        )
        return AutarcoWriteResult(
            register=OFF_GRID_MINIMUM_SOC_REGISTER,
            previous_value=previous_value,
            requested_value=requested_value,
            verified_value=target_verified_value,
            duration_ms=duration_ms,
            dependency_was_active=dependency_was_active,
            dependency_temporarily_enabled=dependency_temporarily_enabled,
            dependency_restored=dependency_restored,
        )


async def async_write_off_grid_minimum_soc_v066(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
    *,
    trusted_battery_soc: float | None = None,
) -> None:
    """Execute one guarded Off-grid SOC write in the documented 10-100% range.

    ``trusted_battery_soc`` is deliberately supplied by the outer safety layer.
    The inverter runtime register is not used for temporary Off-grid activation,
    because hardware testing proved that it can report a plausible value while
    the external battery is not actually connected.
    """
    requested = int(requested)
    if not OFF_GRID_MINIMUM_SOC_MIN <= requested <= OFF_GRID_MINIMUM_SOC_MAX:
        raise HomeAssistantError(
            f"Off-grid minimum SOC moet tussen {OFF_GRID_MINIMUM_SOC_MIN}% en "
            f"{OFF_GRID_MINIMUM_SOC_MAX}% liggen."
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

    if current is None:
        raise HomeAssistantError("Off-grid minimum SOC kon niet vers worden uitgelezen.")
    if mode_value is None:
        raise HomeAssistantError(
            f"Work-mode register {STORAGE_MODE_REGISTER} is niet beschikbaar; write afgebroken."
        )
    if current == requested:
        coordinator.settings_last_write_diagnostic = (
            f"GEEN WIJZIGING — Off-grid minimum SOC staat al op {requested}%"
        )
        coordinator.async_update_listeners()
        return

    off_grid_was_active = bool(mode_value & OFF_GRID_MODE_MASK)
    if not off_grid_was_active:
        if trusted_battery_soc is None:
            raise HomeAssistantError(
                "Betrouwbare batterij-SOC is niet beschikbaar. Autarco Local activeert "
                "Off-grid daarom niet tijdelijk."
            )
        if float(trusted_battery_soc) < TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC:
            raise HomeAssistantError(
                "Write afgebroken: tijdelijke Off-grid-activatie is alleen toegestaan "
                f"vanaf {TEMPORARY_OFF_GRID_MINIMUM_BATTERY_SOC}% betrouwbare "
                f"batterij-SOC (actueel {trusted_battery_soc:g}%)."
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
            _write_transaction,
            coordinator.client,
            requested,
        )
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            f"MISLUKT — Off-grid minimum SOC {current}% → {requested}%: {err}"
        )
        coordinator.async_update_listeners()
        raise HomeAssistantError(str(err)) from err

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
        f"TUSSENCONTROLE — Off-grid minimum SOC {result.previous_value}% → "
        f"{result.verified_value}% tijdens de write geverifieerd; "
        + (
            "Off-grid stond al AAN en is AAN gebleven."
            if result.dependency_was_active
            else "tijdelijke Off-grid activatie is afgerond en de oorspronkelijke work-mode is hersteld."
        )
        + " Finale stabiliteitscontrole volgt nog."
    )
    coordinator.async_update_listeners()
