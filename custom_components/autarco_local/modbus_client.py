"""Read-only Modbus TCP client for Autarco Local."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from pymodbus.client import AsyncModbusTcpClient
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
    """Raised when the inverter cannot be contacted or no data is readable."""


@dataclass(slots=True, frozen=True)
class AutarcoConnectionSettings:
    """Connection settings for an Autarco logger."""

    host: str
    port: int
    device_id: int
    timeout: int


class AutarcoModbusClient:
    """Read-only Modbus TCP client."""

    def __init__(self, settings: AutarcoConnectionSettings) -> None:
        """Initialize the client."""
        self._settings = settings
        self._io_lock = asyncio.Lock()

    def _new_client(self) -> AsyncModbusTcpClient:
        """Create a fresh Modbus TCP client."""
        return AsyncModbusTcpClient(
            self._settings.host,
            port=self._settings.port,
            timeout=self._settings.timeout,
            retries=1,
        )

    async def async_validate(self) -> None:
        """Validate the connection with one small known-readable request."""
        async with self._io_lock:
            client = self._new_client()
            try:
                connected = await client.connect()
                if not connected:
                    raise AutarcoConnectionError(
                        f"Geen verbinding met "
                        f"{self._settings.host}:{self._settings.port}"
                    )

                result = await client.read_input_registers(
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
            except (TimeoutError, asyncio.TimeoutError) as err:
                raise AutarcoConnectionError("Timeout tijdens validatie") from err
            except (ModbusException, OSError) as err:
                raise AutarcoConnectionError(str(err)) from err
            finally:
                client.close()

    async def async_read_all(self) -> dict[int, int]:
        """Read known registers in small chunks.

        Unsupported chunks are skipped. This is needed because the logger
        returns Modbus exception code 2 when a request crosses an
        unsupported address.
        """
        async with self._io_lock:
            client = self._new_client()
            registers: dict[int, int] = {}

            try:
                connected = await client.connect()
                if not connected:
                    raise AutarcoConnectionError(
                        f"Geen verbinding met "
                        f"{self._settings.host}:{self._settings.port}"
                    )

                start = REGISTER_START
                while start <= REGISTER_END:
                    count = min(
                        REGISTER_CHUNK_SIZE,
                        REGISTER_END - start + 1,
                    )

                    try:
                        result = await client.read_input_registers(
                            start,
                            count=count,
                            device_id=self._settings.device_id,
                        )
                    except (TimeoutError, asyncio.TimeoutError, ModbusException, OSError) as err:
                        _LOGGER.debug(
                            "Registerblok %s-%s kon niet worden gelezen: %s",
                            start,
                            start + count - 1,
                            err,
                        )
                        start += count
                        continue

                    if result.isError():
                        _LOGGER.debug(
                            "Registerblok %s-%s wordt niet ondersteund: %s",
                            start,
                            start + count - 1,
                            result,
                        )
                        start += count
                        continue

                    values = getattr(result, "registers", None)
                    if values:
                        registers.update(
                            {
                                start + offset: int(value)
                                for offset, value in enumerate(values)
                            }
                        )

                    start += count

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
                    "Verbinding gelukt, maar geen ondersteunde registers gelezen"
                )

            return registers
