"""Thread-safe, read-only Modbus TCP client for Autarco Local."""

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
    VALIDATION_REGISTER_COUNT,
    VALIDATION_REGISTER_START,
)
from .settings import SETTING_REGISTER_ADDRESSES

_LOGGER = logging.getLogger(__name__)


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
    """Result of one complete input-register poll."""

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
    """Result of one optional read-only holding-register settings poll."""

    registers: dict[int, int]
    read_duration_ms: float
    unsupported_registers: tuple[int, ...]


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
        """Read all known input registers with clean TCP reconnects."""
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
        """Read selected holding registers without ever writing to the inverter.

        Settings are deliberately polled separately and slowly. Unsupported
        holding registers are skipped individually so one firmware difference
        does not affect normal monitoring.
        """
        with self._lock:
            started = time.monotonic()
            try:
                self._ensure_connected_locked("socket niet verbonden vóór settings-poll")
                client = self._client
                if client is None or not client.connected:
                    raise AutarcoConnectionError("Modbus-socket is niet verbonden")

                registers: dict[int, int] = {}
                unsupported: list[int] = []

                for address in SETTING_REGISTER_ADDRESSES:
                    try:
                        result = client.read_holding_registers(
                            address,
                            count=1,
                            device_id=self._settings.device_id,
                        )
                    except (ModbusException, OSError, TimeoutError) as err:
                        self._disconnect_locked()
                        raise AutarcoConnectionError(
                            f"Leesfout instelling {address}: "
                            f"{type(err).__name__}: {err}"
                        ) from err

                    if result.isError():
                        unsupported.append(address)
                        _LOGGER.debug(
                            "Instellingsregister %s niet ondersteund: %s",
                            address,
                            result,
                        )
                        continue

                    values = getattr(result, "registers", None) or []
                    if not values:
                        unsupported.append(address)
                        continue
                    registers[address] = int(values[0])

                return AutarcoSettingsReadResult(
                    registers=registers,
                    read_duration_ms=round((time.monotonic() - started) * 1000, 1),
                    unsupported_registers=tuple(unsupported),
                )
            except AutarcoConnectionError:
                raise
            except (ModbusException, OSError, TimeoutError) as err:
                self._disconnect_locked()
                raise AutarcoConnectionError(str(err)) from err

    def _read_once_locked(self) -> tuple[dict[int, int], list[str]]:
        """Read one input-register snapshot over the existing connection."""
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
