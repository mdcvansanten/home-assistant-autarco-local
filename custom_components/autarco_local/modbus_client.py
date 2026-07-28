"""Synchronous, read-only Modbus TCP client for Autarco Local."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import Lock

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
    """Raised when the inverter cannot be contacted or read."""


@dataclass(slots=True, frozen=True)
class AutarcoConnectionSettings:
    """Connection settings for an Autarco logger."""

    host: str
    port: int
    device_id: int
    timeout: int


class AutarcoModbusClient:
    """Synchronous, read-only Modbus TCP client."""

    def __init__(self, settings: AutarcoConnectionSettings) -> None:
        """Initialize the client."""
        self._settings = settings
        self._io_lock = Lock()

    def _new_client(self) -> ModbusTcpClient:
        """Create a fresh client."""
        return ModbusTcpClient(
            self._settings.host,
            port=self._settings.port,
            timeout=self._settings.timeout,
            retries=1,
        )

    def validate(self) -> None:
        """Validate using a small, confirmed-readable request."""
        with self._io_lock:
            client = self._new_client()
            try:
                if not client.connect():
                    raise AutarcoConnectionError(
                        f"Geen verbinding met "
                        f"{self._settings.host}:{self._settings.port}"
                    )

                result = client.read_input_registers(
                    VALIDATION_REGISTER_START,
                    count=VALIDATION_REGISTER_COUNT,
                    device_id=self._settings.device_id,
                )
                if result.isError():
                    raise AutarcoConnectionError(
                        "Modbus-validatiefout bij inputregisters "
                        f"{VALIDATION_REGISTER_START}-"
                        f"{VALIDATION_REGISTER_START + VALIDATION_REGISTER_COUNT - 1}: "
                        f"{result}"
                    )

                values = getattr(result, "registers", None)
                if not values:
                    raise AutarcoConnectionError(
                        "De logger antwoordde zonder registerwaarden"
                    )
            except AutarcoConnectionError:
                raise
            except (ModbusException, OSError) as err:
                raise AutarcoConnectionError(str(err)) from err
            except Exception as err:
                _LOGGER.exception("Onverwachte fout tijdens Modbus-validatie")
                raise AutarcoConnectionError(
                    f"{type(err).__name__}: {err}"
                ) from err
            finally:
                client.close()

    def read_all(self) -> dict[int, int]:
        """Read registers 33000 through 33139 in blocks of ten."""
        with self._io_lock:
            client = self._new_client()
            registers: dict[int, int] = {}

            try:
                if not client.connect():
                    raise AutarcoConnectionError(
                        f"Geen verbinding met "
                        f"{self._settings.host}:{self._settings.port}"
                    )

                start = REGISTER_START
                while start <= REGISTER_END:
                    requested_count = min(
                        REGISTER_CHUNK_SIZE,
                        REGISTER_END - start + 1,
                    )
                    end = start + requested_count - 1

                    try:
                        result = client.read_input_registers(
                            start,
                            count=requested_count,
                            device_id=self._settings.device_id,
                        )
                    except (ModbusException, OSError) as err:
                        _LOGGER.debug(
                            "Registerblok %s-%s kon niet worden gelezen: %s",
                            start,
                            end,
                            err,
                        )
                        start += requested_count
                        continue

                    if result.isError():
                        _LOGGER.debug(
                            "Registerblok %s-%s wordt niet ondersteund: %s",
                            start,
                            end,
                            result,
                        )
                        start += requested_count
                        continue

                    values = getattr(result, "registers", None) or []
                    if len(values) != requested_count:
                        _LOGGER.debug(
                            "Registerblok %s-%s gaf %s van %s waarden terug",
                            start,
                            end,
                            len(values),
                            requested_count,
                        )

                    for offset, value in enumerate(values):
                        if offset >= requested_count:
                            break
                        registers[start + offset] = int(value)

                    start += requested_count

            except AutarcoConnectionError:
                raise
            except Exception as err:
                _LOGGER.exception("Onverwachte fout in de Modbus-client")
                raise AutarcoConnectionError(
                    f"{type(err).__name__}: {err}"
                ) from err
            finally:
                client.close()

            if not registers:
                raise AutarcoConnectionError(
                    "Verbinding gelukt, maar geen registers gelezen"
                )

            return registers
