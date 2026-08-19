"""Guarded v0.7.0 hardware tests for newly opened settings.

Reserve SOC is the first new write candidate after Off-grid minimum SOC.
Hardware testing showed that a direct write while Battery Reserve mode is OFF is
accepted at Modbus level but immediately reads back the old value.  Therefore
this validation step deliberately requires the user to enable Battery Reserve in
the official/local inverter UI first.  Autarco Local does not toggle the parent
mode yet; it only writes register 43024 and proves that the value persists.

To avoid an unexpected reserve-maintenance grid charge during this parent-mode
test, Allow Grid Charging must remain OFF.  Self-use must remain ON and Off-grid
must remain OFF.  The complete work-mode register is checked before and after the
write and must not change during the transaction.
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
ALLOW_GRID_CHARGING_MASK = 1 << 5
RESERVE_SOC_MIN = 20
RESERVE_SOC_MAX = 100


@dataclass(frozen=True, slots=True)
class ReserveSocTestResult:
    """Verified result of the one-step Reserve SOC parent-mode test."""

    previous: int
    requested: int
    minimum_soc: int
    stability_samples: tuple[int, ...]
    duration_ms: float


def _reserve_soc_test_sync(
    coordinator: AutarcoLocalCoordinator,
    requested: int,
) -> ReserveSocTestResult:
    """Write Reserve SOC only while its parent mode is explicitly active."""
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
        original_mode_value = client._read_single_holding_locked(
            STORAGE_MODE_REGISTER,
            "Pre-write read work-mode mislukt",
        )

        if not original_mode_value & SELF_USE_MODE_MASK:
            raise AutarcoConnectionError("Reserve SOC dependencytest vereist Self-use AAN")
        if original_mode_value & OFF_GRID_MODE_MASK:
            raise AutarcoConnectionError("Reserve SOC dependencytest vereist Off-grid UIT")
        if not original_mode_value & RESERVE_MODE_MASK:
            raise AutarcoConnectionError(
                "Reserve SOC dependencytest vereist Reserve battery mode AAN. "
                "Activeer die eerst handmatig in de officiële Solis/Autarco lokale bediening."
            )
        if original_mode_value & ALLOW_GRID_CHARGING_MASK:
            raise AutarcoConnectionError(
                "Reserve SOC dependencytest vereist Laden vanuit net UIT om onverwacht "
                "reserve-onderhoud via het net te voorkomen"
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
        try:
            client._verify_single_holding_locked(
                RESERVE_SOC_REGISTER,
                requested,
                "Reserve SOC read-back kon niet worden bevestigd",
                attempts=5,
                delay=0.4,
            )
        except AutarcoConnectionError as err:
            raise AutarcoConnectionError(
                f"Reserve SOC bleef niet op {requested}% terwijl Reserve mode AAN stond; {err}"
            ) from err

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

        mode_after = client._read_single_holding_locked(
            STORAGE_MODE_REGISTER,
            "Work-mode eindcontrole mislukt",
        )
        if mode_after != original_mode_value:
            raise AutarcoConnectionError(
                "Reserve SOC is mogelijk gewijzigd, maar work-mode veranderde tijdens de test "
                f"(voor {original_mode_value}, na {mode_after}); geen automatische rollback uitgevoerd"
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
    """Execute the guarded parent-mode test and refresh settings afterwards."""
    try:
        result = await hass.async_add_executor_job(
            _reserve_soc_test_sync,
            coordinator,
            int(requested),
        )
    except AutarcoConnectionError as err:
        coordinator.settings_last_write_diagnostic = (
            f"AFGEBROKEN — Reserve SOC dependencytest: {err}"
        )
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
            f"in {len(result.stability_samples)} extra read-backs terwijl Reserve mode AAN bleef; "
            "Autarco Local wijzigde geen work-mode."
        )

    coordinator.async_update_listeners()
    return result
