"""Small read-only Modbus client for Autarco Local."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import REGISTER_BLOCKS


class AutarcoConnectionError(Exception):
    """Raised when the inverter cannot be read."""


@dataclass(slots=True)
class AutarcoModbusClient:
    """Read-only Modbus TCP client."""

    host: str
    port: int
    device_id: int
    timeout: int

    async def async_read_all(self) -> dict[int, int]:
        """Read the known input-register blocks."""
        client = AsyncModbusTcpClient(
            self.host,
            port=self.port,
            timeout=self.timeout,
            retries=1,
        )

        registers: dict[int, int] = {}

        try:
            connected = await client.connect()
            if not connected:
                raise AutarcoConnectionError(
                    f"Geen verbinding met {self.host}:{self.port}"
                )

            for start, count in REGISTER_BLOCKS:
                try:
                    result = await client.read_input_registers(
                        start,
                        count=count,
                        device_id=self.device_id,
                    )
                except (ModbusException, OSError, asyncio.TimeoutError) as err:
                    raise AutarcoConnectionError(str(err)) from err

                if result.isError():
                    raise AutarcoConnectionError(
                        f"Modbus-fout bij registers "
                        f"{start}-{start + count - 1}: {result}"
                    )

                for offset, value in enumerate(result.registers):
                    registers[start + offset] = value

            return registers
        finally:
            client.close()
