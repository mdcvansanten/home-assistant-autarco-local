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
    """Verified result of the deliberately narrow v0.6.0 write pilot."""

    register: int
    previous_value: int
    requested_value: int
    verified_value: int
    duration_ms: float


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
        """Ensure a usable TCP connection.

        Returns connect duration, whether this was a reconnect (not the first
        connection), and the reconnect reason.
        """
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
        """Perform the single guarded v0.6.0 write pilot.

        Safety guardrails are deliberately hard-coded for the first hardware
        validation: only holding register 43137, only a transition from the
        verified current value 10 to 20, and mandatory read-back verification.
        No other register or value can be written through this method.
        """
        if int(requested_value) != OFF_GRID_MINIMUM_SOC_PILOT_TO:
            raise AutarcoConnectionError(
                "Write pilot staat alleen Off-grid minimum SOC 10% -> 20% toe"
            )

        with self._lock:
            self._ensure_connected_locked("socket was niet verbonden vóór settings-write")
            client = self._client
            if client is None or not client.connected:
                raise AutarcoConnectionError("Modbus-socket is niet verbonden")

            started = time.monotonic()
            try:
                before = client.read_holding_registers(
                    OFF_GRID_MINIMUM_SOC_REGISTER,
                    count=1,
                    device_id=self._settings.device_id,
                )
            except (ModbusException, OSError, TimeoutError) as err:
                self._disconnect_locked()
                raise AutarcoConnectionError(
                    f"Pre-write read mislukt: {type(err).__name__}: {err}"
                ) from err

            if before.isError():
                raise AutarcoConnectionError(f"Pre-write Modbus-fout: {before}")
            before_values = getattr(before, "registers", None) or []
            if not before_values:
                raise AutarcoConnectionError("Pre-write read gaf geen registerwaarde")
            previous_value = int(before_values[0])
            if previous_value != OFF_GRID_MINIMUM_SOC_PILOT_FROM:
                raise AutarcoConnectionError(
                    "Write afgebroken: Off-grid minimum SOC is niet meer 10% "
                    f"maar {previous_value}%"
                )

            try:
                write_result = client.write_register(
                    OFF_GRID_MINIMUM_SOC_REGISTER,
                    OFF_GRID_MINIMUM_SOC_PILOT_TO,
                    device_id=self._settings.device_id,
                )
            except (ModbusException, OSError, TimeoutError) as err:
                self._disconnect_locked()
                raise AutarcoConnectionError(
                    f"Settings-write mislukt: {type(err).__name__}: {err}"
                ) from err

            if write_result.isError():
                raise AutarcoConnectionError(f"Modbus-write geweigerd: {write_result}")

            verified_value: int | None = None
            last_read_error: str | None = None
            for _attempt in range(5):
                time.sleep(0.4)
                try:
                    verify = client.read_holding_registers(
                        OFF_GRID_MINIMUM_SOC_REGISTER,
                        count=1,
                        device_id=self._settings.device_id,
                    )
                except (ModbusException, OSError, TimeoutError) as err:
                    last_read_error = f"{type(err).__name__}: {err}"
                    continue
                if verify.isError():
                    last_read_error = str(verify)
                    continue
                values = getattr(verify, "registers", None) or []
                if not values:
                    last_read_error = "leeg read-back antwoord"
                    continue
                verified_value = int(values[0])
                if verified_value == OFF_GRID_MINIMUM_SOC_PILOT_TO:
                    break

            if verified_value != OFF_GRID_MINIMUM_SOC_PILOT_TO:
                raise AutarcoConnectionError(
                    "Write kon niet worden bevestigd via read-back: "
                    f"verwacht 20%, ontvangen {verified_value!r}; "
                    f"laatste fout={last_read_error}"
                )

            duration_ms = round((time.monotonic() - started) * 1000, 1)
            _LOGGER.warning(
                "Gecontroleerde settings-write uitgevoerd: register %s %s%% -> %s%% "
                "en via read-back bevestigd in %.1f ms",
                OFF_GRID_MINIMUM_SOC_REGISTER,
                previous_value,
                verified_value,
                duration_ms,
            )
            return AutarcoWriteResult(
                register=OFF_GRID_MINIMUM_SOC_REGISTER,
                previous_value=previous_value,
                requested_value=OFF_GRID_MINIMUM_SOC_PILOT_TO,
                verified_value=verified_value,
                duration_ms=duration_ms,
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
