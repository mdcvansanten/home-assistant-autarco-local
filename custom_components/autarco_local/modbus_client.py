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
    """Result of one complete register poll."""

    registers: dict[int, int]
    response_ms: float
    attempts: int
    unsupported_blocks: tuple[str, ...]
    reconnects: int


class AutarcoModbusClient:
    """Persistent Modbus TCP client with clean reconnects."""

    def __init__(self, settings: AutarcoConnectionSettings) -> None:
        self._settings = settings
        self._lock = Lock()
        self._client: ModbusTcpClient | None = None

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
            except Exception:  # Defensive cleanup; never hide original error.
                _LOGGER.debug("Fout bij sluiten Modbus-client", exc_info=True)

    def close(self) -> None:
        """Close the persistent connection."""
        with self._lock:
            self._disconnect_locked()

    def _ensure_connected_locked(self) -> bool:
        """Ensure a usable TCP connection and report whether a reconnect occurred."""
        if self._client is not None and self._client.connected:
            return False

        self._disconnect_locked()
        self._client = self._new_client()
        if not self._client.connect():
            self._disconnect_locked()
            raise AutarcoConnectionError(
                f"Geen verbinding met {self._settings.host}:{self._settings.port}"
            )
        return True

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
        """Read all known registers, retrying through clean TCP reconnects."""
        with self._lock:
            started = time.monotonic()
            last_error: AutarcoConnectionError | None = None
            reconnects = 0

            for attempt in range(1, self._settings.retries + 2):
                try:
                    reconnected = self._ensure_connected_locked()
                    reconnects += int(reconnected)
                    registers, unsupported = self._read_once_locked()
                    return AutarcoReadResult(
                        registers=registers,
                        response_ms=round((time.monotonic() - started) * 1000, 1),
                        attempts=attempt,
                        unsupported_blocks=tuple(unsupported),
                        reconnects=reconnects,
                    )
                except AutarcoConnectionError as err:
                    last_error = err
                    # A failed request can leave the socket half-open. Always rebuild it.
                    self._disconnect_locked()
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

    def _read_once_locked(self) -> tuple[dict[int, int], list[str]]:
        """Read one snapshot over the existing connection."""
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
