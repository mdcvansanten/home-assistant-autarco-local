"""Guarded v0.7.0 hardware tests for newly opened settings.

Only Reserve SOC is included initially. The transaction is deliberately much
narrower than a production writer: it permits a one-percentage-point reversible
test only in normal Self-use operation while Battery Reserve and Off-grid are
both OFF, so the configured reserve target is not actively governing battery
behaviour during the mapping/write test.
"""

from __future__ import annotations

from dataclasses import dataclass
import time

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .coordinator import AutarcoLocalCoordinator
from .modbus_client import AutarcoConnectionError, STORAGE_MODE_REGISTER

RESERVE_SOC_REGISTER = 43024
MINIMUM_BATTERY_SOC_REGISTER = 43011
SELF_USE_MODE_MASK = 1 << 0
OFF_GRID_MODE_MASK = 1 << 2
RESERVE_MODE_MASK = 1 << 4
RESERVE_SOC_MIN = 20
RESERVE_SOC_MAX = 100


@dataclass(frozen=True, slots=True)
class ReserveSocTestResult:
    """Verified result of the one-step Reserve SOC hardware test."""

    previous: int
    requested: int
    minimum_soc: int
    stability_samples: tuple[int, ...]
    duration_ms: float


def _reserve_soc_test_sync(coordinator: AutarcoLocalCoordinator, requested: int) -> ReserveSocTestResult:
    """Perform a narrow one-point Reserve SOC write with persistent read-back."""
    client = coordinator.client
    requested = int(requested)
    if not RESERVE_SOC_MIN <= requested <= RESERVE_SOC_MAX:
        raise AutarcoConnectionError(
            f"Reserve SOC test verwacht {RESERVE_SOC_MIN}–{RESERVE_SOC_MAX}%, ontvangen {requested}%"
        )

    with client._lock:
        client._ensure_connected_locked("socket was niet verbonden vóór Reserve SOC test")
        started = time.monotonic()

        previous = client._read_single_holding_locked(
            RESERVE_SOC_REGISTER,
            "Pre-write read Reserve SOC mislukt",
        )
        minimum_soc = client._read_single_holding_locked(
            MINIMUM_BATTERY_SOC_REGISTER,
            "Pre-write read Minimum battery SOC mislukt",
        )
        mode_value = client._read_single_holding_locked(
            STORAGE_MODE_REGISTER,
            "Pre-write read work-mode mislukt",
        )

        if not mode_value & SELF_USE_MODE_MASK:
            raise AutarcoConnectionError(
                "Reserve SOC hardwaretest vereist Self-use AAN"
            )
        if mode_value & OFF_GRID_MODE_MASK:
            raise AutarcoConnectionError(
                "Reserve SOC hardwaretest vereist Off-grid UIT"
            )
        if mode_value & RESERVE_MODE_MASK:
            raise AutarcoConnectionError(
                "Reserve SOC hardwaretest vereist Reserve battery mode UIT"
            )

        if abs(requested - previous) != 1:
            raise AutarcoConnectionError(
                "Reserve SOC hardwaretest staat alleen een wijziging van precies 1 procentpunt toe "
                f"(actueel {previous}%, gevraagd {requested}%)"
            )

        safe_floor = max(RESERVE_SOC_MIN, int(minimum_soc))
        if requested < safe_floor:
            raise AutarcoConnectionError(
                f"Reserve SOC {requested}% mag in deze test niet lager zijn dan {safe_floor}% "
                f"(Minimum battery SOC {minimum_soc}%)"
            )

        client._write_single_holding_locked(
            RESERVE_SOC_REGISTER,
            requested,
            "Reserve SOC write mislukt",
        )
        client._verify_single_holding_locked(
            RESERVE_SOC_REGISTER,
            requested,
            "Reserve SOC read-back kon niet worden bevestigd",
            attempts=5,
            delay=0.4,
        )

        samples: list[int] = []
        for delay in (1.5, 2.5, 3.5):
            time.sleep(delay)
            observed = client._read_single_holding_locked(
                RESERVE_SOC_REGISTER,
                "Reserve SOC stabiliteitscontrole mislukt",
            )
            samples.append(observed)
            if observed != requested:
                raise AutarcoConnectionError(
                    "Reserve SOC write is NIET BLIJVEND: "
                    f"doel {requested}%, latere read-back {observed}%"
                )

        return ReserveSocTestResult(
            previous=previous,
            requested=requested,
            minimum_soc=int(minimum_soc),
            stability_samples=tuple(samples),
            duration_ms=round((time.monotonic() - started) * 1000, 1),
        )


async def async_test_reserve_soc_v070(
    hass: HomeAssistant,
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> ReserveSocTestResult:
    """Execute the guarded test and refresh the settings snapshot afterwards."""
    try:
        result = await hass.async_add_executor_job(
            _reserve_soc_test_sync,
            coordinator,
            int(requested),
        )
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = f"AFGEBROKEN — Reserve SOC test: {err}"
        coordinator.async_update_listeners()
        raise HomeAssistantError(f"Reserve SOC test afgebroken: {err}") from err

    try:
        fresh = await hass.async_add_executor_job(coordinator.client.read_settings)
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            "WRITE BEVESTIGD, maar settings-refresh mislukte — "
            f"Reserve SOC {result.previous}% → {result.requested}%: {err}"
        )
    else:
        coordinator.settings_data = fresh.registers
        coordinator.settings_read_time_ms = fresh.read_duration_ms
        coordinator.settings_unsupported_blocks = fresh.unsupported_blocks
        coordinator.settings_last_write_diagnostic = (
            f"SUCCES — Reserve SOC {result.previous}% → {result.requested}% bleef stabiel "
            f"in {len(result.stability_samples)} extra read-backs; Self-use bleef AAN, "
            "Off-grid en Reserve mode bleven UIT."
        )

    coordinator.async_update_listeners()
    return result
