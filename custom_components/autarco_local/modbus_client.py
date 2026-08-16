"""Thread-safe Modbus TCP client for Autarco Local."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import Lock
import time

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    REGISTER_CHUNK_SIZE,
    REGISTER_END,
    REGISTER_START,
    SETTING_REGISTER_BLOCKS,
    VALIDATION_REGISTER_COUNT,
    VALIDATION_REGISTER_START,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_MODE_REGISTER = 43110
OFF_GRID_MODE_BIT = 2
OFF_GRID_MODE_MASK = 1 << OFF_GRID_MODE_BIT
OFF_GRID_MINIMUM_SOC_REGISTER = 43137
OFF_GRID_MINIMUM_SOC_PILOT_FROM = 10
OFF_GRID_MINIMUM_SOC_PILOT_TO = 20


class AutarcoConnectionError(Exception):
    """Communication error."""


@dataclass(slots=True, frozen=True)
class AutarcoConnectionSettings:
    """Connection settings."""

    host: str
    port: int
    device_id: int
    timeout: int
    retries: int = 2


@dataclass(slots=True, frozen=True)
class AutarcoReadResult:
    """Result of one complete runtime/input-register poll."""

    registers: dict[int, int]
    poll_duration_ms: float
    read_duration_ms: float
    connect_duration_ms: float
    attempts: int
    unsupported_blocks: tuple[str, ...]
    reconnects: int
    reconnect_reason: str | None


@dataclass(slots=True, frozen=True)
class AutarcoSettingsReadResult:
    """Result of one non-critical settings poll."""

    registers: dict[int, int]
    read_duration_ms: float
    unsupported_blocks: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class AutarcoWriteResult:
    """Verified result of a guarded settings write transaction."""

    register: int
    previous_value: int
    requested_value: int
    verified_value: int
    duration_ms: float
    dependency_was_active: bool = False
    dependency_temporarily_enabled: bool = False
    dependency_restored: bool = True


class AutarcoModbusClient:
    """Persistent Modbus TCP client with clean reconnects."""

    def __init__(self, settings: AutarcoConnectionSettings) -> None:
        self._settings = settings
        self._lock = Lock()
        self._client: ModbusTcpClient | None = None
        self._ever_connected = False

    def _new_client(self) -> ModbusTcpClient:
        return ModbusTcpClient(
            self._settings.host,
            port=self._settings.port,
            timeout=self._settings.timeout,
            retries=0,
        )

    def _disconnect_locked(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            try:
                client.close()
            except Exception:
                _LOGGER.debug("Fout bij sluiten Modbus-client", exc_info=True)

    def close(self) -> None:
        """Close the persistent connection."""
        with self._lock:
            self._disconnect_locked()

    def _ensure_connected_locked(
        self, reason: str | None = None
    ) -> tuple[float, bool, str | None]:
        """Ensure a usable TCP connection."""
        if self._client is not None and self._client.connected:
            return 0.0, False, None

        self._disconnect_locked()
        self._client = self._new_client()
        started = time.monotonic()
        if not self._client.connect():
            duration = (time.monotonic() - started) * 1000
            self._disconnect_locked()
            raise AutarcoConnectionError(
                f"Geen verbinding met {self._settings.host}:{self._settings.port} "
                f"na {duration:.1f} ms"
            )

        duration = (time.monotonic() - started) * 1000
        is_reconnect = self._ever_connected
        self._ever_connected = True
        return duration, is_reconnect, reason if is_reconnect else None

    def _read_single_holding_locked(self, register: int, context: str) -> int:
        client = self._client
        if client is None or not client.connected:
            raise AutarcoConnectionError("Modbus-socket is niet verbonden")
        try:
            result = client.read_holding_registers(
                register,
                count=1,
                device_id=self._settings.device_id,
            )
        except (ModbusException, OSError, TimeoutError) as err:
            self._disconnect_locked()
            raise AutarcoConnectionError(
                f"{context}: {type(err).__name__}: {err}"
            ) from err
        if result.isError():
            raise AutarcoConnectionError(f"{context}: Modbus-fout {result}")
        values = getattr(result, "registers", None) or []
        if not values:
            raise AutarcoConnectionError(f"{context}: geen registerwaarde ontvangen")
        return int(values[0])

    def _write_single_holding_locked(self, register: int, value: int, context: str) -> None:
        client = self._client
        if client is None or not client.connected:
            raise AutarcoConnectionError("Modbus-socket is niet verbonden")
        try:
            result = client.write_register(
                register,
                int(value),
                device_id=self._settings.device_id,
            )
        except (ModbusException, OSError, TimeoutError) as err:
            self._disconnect_locked()
            raise AutarcoConnectionError(
                f"{context}: {type(err).__name__}: {err}"
            ) from err
        if result.isError():
            raise AutarcoConnectionError(f"{context}: Modbus-write geweigerd: {result}")

    def _verify_single_holding_locked(
        self,
        register: int,
        expected: int,
        context: str,
        *,
        attempts: int = 5,
        delay: float = 0.4,
        mask: int | None = None,
    ) -> int:
        last_value: int | None = None
        last_error: str | None = None
        for _attempt in range(attempts):
            time.sleep(delay)
            try:
                value = self._read_single_holding_locked(register, context)
            except AutarcoConnectionError as err:
                last_error = str(err)
                continue
            last_value = value
            if mask is None:
                if value == expected:
                    return value
            elif (value & mask) == (expected & mask):
                return value
        raise AutarcoConnectionError(
            f"{context}: read-back verwacht {expected}, ontvangen {last_value!r}; "
            f"laatste fout={last_error}"
        )

    def validate(self) -> None:
        """Validate settings with one read-only request."""
        with self._lock:
            temporary = self._new_client()
            try:
                if not temporary.connect():
                    raise AutarcoConnectionError(
                        f"Geen verbinding met {self._settings.host}:{self._settings.port}"
                    )
                result = temporary.read_input_registers(
                    VALIDATION_REGISTER_START,
                    count=VALIDATION_REGISTER_COUNT,
                    device_id=self._settings.device_id,
                )
                if result.isError():
                    raise AutarcoConnectionError(f"Modbus-validatiefout: {result}")
                if not getattr(result, "registers", None):
                    raise AutarcoConnectionError("Geen registerwaarden ontvangen")
            except AutarcoConnectionError:
                raise
            except (ModbusException, OSError, TimeoutError) as err:
                raise AutarcoConnectionError(str(err)) from err
            finally:
                temporary.close()

    def read_all(self) -> AutarcoReadResult:
        """Read all known runtime registers, retrying through clean reconnects."""
        with self._lock:
            poll_started = time.monotonic()
            last_error: AutarcoConnectionError | None = None
            reconnects = 0
            total_connect_ms = 0.0
            reconnect_reason: str | None = None
            next_connect_reason: str | None = "socket was niet verbonden vóór de poll"

            for attempt in range(1, self._settings.retries + 2):
                try:
                    connect_ms, is_reconnect, reason = self._ensure_connected_locked(
                        next_connect_reason
                    )
                    total_connect_ms += connect_ms
                    if is_reconnect:
                        reconnects += 1
                        reconnect_reason = reason

                    read_started = time.monotonic()
                    registers, unsupported = self._read_once_locked()
                    read_ms = (time.monotonic() - read_started) * 1000
                    poll_ms = (time.monotonic() - poll_started) * 1000
                    return AutarcoReadResult(
                        registers=registers,
                        poll_duration_ms=round(poll_ms, 1),
                        read_duration_ms=round(read_ms, 1),
                        connect_duration_ms=round(total_connect_ms, 1),
                        attempts=attempt,
                        unsupported_blocks=tuple(unsupported),
                        reconnects=reconnects,
                        reconnect_reason=reconnect_reason,
                    )
                except AutarcoConnectionError as err:
                    last_error = err
                    self._disconnect_locked()
                    next_connect_reason = f"herstel na {type(err).__name__}: {err}"
                    if attempt <= self._settings.retries:
                        delay = min(0.75 * (2 ** (attempt - 1)), 3.0)
                        _LOGGER.debug(
                            "Modbus-poging %s van %s mislukt (%s); schone reconnect over %.2f s",
                            attempt,
                            self._settings.retries + 1,
                            err,
                            delay,
                        )
                        time.sleep(delay)

            raise AutarcoConnectionError(
                str(last_error) if last_error else "Onbekende communicatiefout"
            )

    def read_settings(self) -> AutarcoSettingsReadResult:
        """Read selected holding registers without writing to the inverter."""
        with self._lock:
            self._ensure_connected_locked("socket was niet verbonden vóór settings-read")
            client = self._client
            if client is None or not client.connected:
                raise AutarcoConnectionError("Modbus-socket is niet verbonden")

            started = time.monotonic()
            registers: dict[int, int] = {}
            unsupported: list[str] = []

            for start, count in SETTING_REGISTER_BLOCKS:
                end = start + count - 1
                try:
                    result = client.read_holding_registers(
                        start,
                        count=count,
                        device_id=self._settings.device_id,
                    )
                except (ModbusException, OSError, TimeoutError) as err:
                    self._disconnect_locked()
                    raise AutarcoConnectionError(
                        f"Settings-leesfout {start}-{end}: {type(err).__name__}: {err}"
                    ) from err

                if result.isError():
                    unsupported.append(f"{start}-{end}")
                    _LOGGER.debug(
                        "Holding-registerblok %s-%s niet ondersteund: %s",
                        start,
                        end,
                        result,
                    )
                    continue

                values = getattr(result, "registers", None) or []
                if not values:
                    unsupported.append(f"{start}-{end}")
                    _LOGGER.debug(
                        "Leeg antwoord voor holding-registerblok %s-%s", start, end
                    )
                    continue

                for offset, value in enumerate(values[:count]):
                    registers[start + offset] = int(value)

            return AutarcoSettingsReadResult(
                registers=registers,
                read_duration_ms=round((time.monotonic() - started) * 1000, 1),
                unsupported_blocks=tuple(unsupported),
            )

    def write_off_grid_minimum_soc_pilot(self, requested_value: int) -> AutarcoWriteResult:
        """Perform the guarded dependency-aware Off-grid SOC write pilot.

        Hardware validation showed that Off-grid minimum SOC can only be changed
        while Off-grid mode is active. This transaction preserves the user's
        original work-mode state:

        * if Off-grid is already active, it is left active;
        * if Autarco Local temporarily activates Off-grid, the complete original
          storage-mode register is restored afterwards;
        * cleanup is attempted even when the target write fails;
        * an unverified restore is a hard failure.
        """
        if int(requested_value) != OFF_GRID_MINIMUM_SOC_PILOT_TO:
            raise AutarcoConnectionError(
                "Write pilot staat alleen Off-grid minimum SOC 10% -> 20% toe"
            )

        with self._lock:
            self._ensure_connected_locked("socket was niet verbonden vóór settings-write")
            started = time.monotonic()

            previous_value = self._read_single_holding_locked(
                OFF_GRID_MINIMUM_SOC_REGISTER,
                "Pre-write read Off-grid minimum SOC mislukt",
            )
            if previous_value != OFF_GRID_MINIMUM_SOC_PILOT_FROM:
                raise AutarcoConnectionError(
                    "Write afgebroken: Off-grid minimum SOC is niet meer 10% "
                    f"maar {previous_value}%"
                )

            original_mode_value = self._read_single_holding_locked(
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
                    self._write_single_holding_locked(
                        STORAGE_MODE_REGISTER,
                        enable_value,
                        "Tijdelijk activeren Off-grid mode mislukt",
                    )
                    mode_after_enable = self._verify_single_holding_locked(
                        STORAGE_MODE_REGISTER,
                        enable_value,
                        "Off-grid mode kon niet worden bevestigd",
                        mask=OFF_GRID_MODE_MASK,
                    )
                    dependency_temporarily_enabled = True

                self._write_single_holding_locked(
                    OFF_GRID_MINIMUM_SOC_REGISTER,
                    OFF_GRID_MINIMUM_SOC_PILOT_TO,
                    "Off-grid minimum SOC write mislukt",
                )
                target_verified_value = self._verify_single_holding_locked(
                    OFF_GRID_MINIMUM_SOC_REGISTER,
                    OFF_GRID_MINIMUM_SOC_PILOT_TO,
                    "Off-grid minimum SOC kon niet worden bevestigd",
                )
            except AutarcoConnectionError as err:
                target_error = err
            finally:
                if dependency_temporarily_enabled:
                    try:
                        observed_before_restore = self._read_single_holding_locked(
                            STORAGE_MODE_REGISTER,
                            "Mode-state vóór restore kon niet worden gelezen",
                        )
                        if observed_before_restore != mode_after_enable:
                            raise AutarcoConnectionError(
                                "Restore afgebroken: storage mode veranderde extern tijdens "
                                f"de transactie (verwacht {mode_after_enable}, ontvangen "
                                f"{observed_before_restore})"
                            )
                        self._write_single_holding_locked(
                            STORAGE_MODE_REGISTER,
                            original_mode_value,
                            "Herstellen oorspronkelijke storage mode mislukt",
                        )
                        self._verify_single_holding_locked(
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

            if target_verified_value != OFF_GRID_MINIMUM_SOC_PILOT_TO:
                raise AutarcoConnectionError(
                    "Interne fout: target write is niet als 20% geverifieerd"
                )

            duration_ms = round((time.monotonic() - started) * 1000, 1)
            _LOGGER.warning(
                "Gecontroleerde dependency-aware settings-write: register %s %s%% -> %s%%; "
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
                requested_value=OFF_GRID_MINIMUM_SOC_PILOT_TO,
                verified_value=target_verified_value,
                duration_ms=duration_ms,
                dependency_was_active=dependency_was_active,
                dependency_temporarily_enabled=dependency_temporarily_enabled,
                dependency_restored=dependency_restored,
            )

    def _read_once_locked(self) -> tuple[dict[int, int], list[str]]:
        """Read one runtime snapshot over the existing connection."""
        client = self._client
        if client is None or not client.connected:
            raise AutarcoConnectionError("Modbus-socket is niet verbonden")

        registers: dict[int, int] = {}
        unsupported: list[str] = []
        start = REGISTER_START

        while start <= REGISTER_END:
            count = min(REGISTER_CHUNK_SIZE, REGISTER_END - start + 1)
            end = start + count - 1
            try:
                result = client.read_input_registers(
                    start,
                    count=count,
                    device_id=self._settings.device_id,
                )
            except (ModbusException, OSError, TimeoutError) as err:
                raise AutarcoConnectionError(
                    f"Leesfout {start}-{end}: {type(err).__name__}: {err}"
                ) from err

            if result.isError():
                unsupported.append(f"{start}-{end}")
                _LOGGER.debug(
                    "Registerblok %s-%s niet ondersteund: %s", start, end, result
                )
            else:
                values = getattr(result, "registers", None) or []
                if not values:
                    raise AutarcoConnectionError(
                        f"Leeg antwoord voor registerblok {start}-{end}"
                    )
                for offset, value in enumerate(values[:count]):
                    registers[start + offset] = int(value)
            start += count

        if not registers:
            raise AutarcoConnectionError("Geen registers gelezen")
        return registers, unsupported
