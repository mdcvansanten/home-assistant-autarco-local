"""Read-only Modbus TCP client for Autarco Local."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import REGISTER_BLOCKS

_LOGGER = logging.getLogger(__name__)


class AutarcoConnectionError(Exception):
    """Raised when the inverter cannot be read."""


@dataclass(slots=True, frozen=True)
class AutarcoConnectionSettings:
    """Connection settings for an Autarco logger."""

    host: str
    port: int
    device_id: int
    timeout: int


class AutarcoModbusClient:
    """Small, read-only Modbus TCP client.

    A fresh TCP client is used for every poll. This avoids stale Modbus
    transactions after a logger or network interruption.
    """

    def __init__(self, settings: AutarcoConnectionSettings) -> None:
        """Initialize the client."""
        self._settings = settings
        self._io_lock = asyncio.Lock()

    async def async_read_all(self) -> dict[int, int]:
        """Read all known input-register blocks."""
        async with self._io_lock:
            return await self._async_read_all_locked()

    async def _async_read_all_locked(self) -> dict[int, int]:
        """Read registers while holding the client lock."""
        settings = self._settings
        client = AsyncModbusTcpClient(
            settings.host,
            port=settings.port,
            timeout=settings.timeout,
            retries=1,
        )
        registers: dict[int, int] = {}

        try:
            async with asyncio.timeout(settings.timeout + 10):
                connected = await client.connect()
                if not connected:
                    raise AutarcoConnectionError(
                        f"Geen verbinding met {settings.host}:{settings.port}"
                    )

                for start, count in REGISTER_BLOCKS:
                    result = await client.read_input_registers(
                        start,
                        count=count,
                        device_id=settings.device_id,
                    )

                    if result.isError():
                        raise AutarcoConnectionError(
                            "Modbus-fout bij inputregisters "
                            f"{start}-{start + count - 1}: {result}"
                        )

                    values = getattr(result, "registers", None)
                    if values is None or len(values) != count:
                        received = 0 if values is None else len(values)
                        raise AutarcoConnectionError(
                            f"Onvolledig antwoord vanaf register {start}: "
                            f"{received} van {count} registers ontvangen"
                        )

                    registers.update(
                        {
                            start + offset: int(value)
                            for offset, value in enumerate(values)
                        }
                    )

        except AutarcoConnectionError:
            raise
        except (TimeoutError, asyncio.TimeoutError) as err:
            raise AutarcoConnectionError(
                f"Timeout bij verbinding met {settings.host}:{settings.port}"
            ) from err
        except (ModbusException, OSError) as err:
            raise AutarcoConnectionError(str(err)) from err
        except Exception as err:
            _LOGGER.exception("Onverwachte fout in de Modbus-client")
            raise AutarcoConnectionError(
                f"{type(err).__name__}: {err}"
            ) from err
        finally:
            client.close()

        if not registers:
            raise AutarcoConnectionError("Geen registers ontvangen")

        return registers
