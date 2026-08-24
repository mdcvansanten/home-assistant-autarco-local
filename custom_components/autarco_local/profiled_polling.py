"""Solis-inspired grouped runtime polling for Autarco Local v0.7.1.

The original v0.6.x reader scanned the complete 33000-33170 range in small
chunks. v0.7.1 keeps the same retry/reconnect layer but reads only the validated
runtime groups required by Autarco Local entities. A group that is rejected by
the device automatically falls back to the proven small-chunk strategy for that
group only.
"""
from __future__ import annotations

import logging

from pymodbus.exceptions import ModbusException

from .const import REGISTER_CHUNK_SIZE
from .device_profile import AUTARCO_LH_MII_PROFILE
from .modbus_client import AutarcoConnectionError, AutarcoModbusClient

_LOGGER = logging.getLogger(__name__)
_INSTALLED = False


def _read_range(client_obj, start: int, count: int):
    client = client_obj._client
    if client is None or not client.connected:
        raise AutarcoConnectionError("Modbus-socket is niet verbonden")
    end = start + count - 1
    try:
        return client.read_input_registers(
            start,
            count=count,
            device_id=client_obj._settings.device_id,
        )
    except (ModbusException, OSError, TimeoutError) as err:
        raise AutarcoConnectionError(
            f"Leesfout {start}-{end}: {type(err).__name__}: {err}"
        ) from err


def _store_values(registers: dict[int, int], start: int, count: int, result) -> bool:
    if result.isError():
        return False
    values = getattr(result, "registers", None) or []
    if not values:
        return False
    for offset, value in enumerate(values[:count]):
        registers[start + offset] = int(value)
    return True


def _profiled_read_once_locked(self: AutarcoModbusClient) -> tuple[dict[int, int], list[str]]:
    """Read the validated Autarco runtime profile using four logical groups.

    Normal operation uses one Modbus request per group. If the inverter rejects a
    broad request, only that group falls back to <=10-register reads. This keeps
    compatibility with the proven v0.6.x behaviour without paying its latency on
    every poll.
    """
    client = self._client
    if client is None or not client.connected:
        raise AutarcoConnectionError("Modbus-socket is niet verbonden")

    registers: dict[int, int] = {}
    unsupported: list[str] = []
    requests = 0
    fallback_groups: list[str] = []

    for group in AUTARCO_LH_MII_PROFILE.runtime_groups:
        result = _read_range(self, group.start, group.count)
        requests += 1
        if _store_values(registers, group.start, group.count, result):
            continue

        fallback_groups.append(group.key)
        _LOGGER.debug(
            "Runtimegroep %s (%s-%s) niet als één blok leesbaar; fallback naar kleine chunks",
            group.key,
            group.start,
            group.end,
        )
        start = group.start
        while start <= group.end:
            count = min(REGISTER_CHUNK_SIZE, group.end - start + 1)
            end = start + count - 1
            chunk_result = _read_range(self, start, count)
            requests += 1
            if not _store_values(registers, start, count, chunk_result):
                unsupported.append(f"{start}-{end}")
                _LOGGER.debug("Runtimeblok %s-%s niet ondersteund", start, end)
            start += count

    if not registers:
        raise AutarcoConnectionError("Geen registers gelezen")

    self.last_runtime_request_count = requests
    self.last_runtime_poll_strategy = "grouped_with_fallback" if fallback_groups else "grouped"
    self.last_runtime_fallback_groups = tuple(fallback_groups)
    return registers, unsupported


def install_profiled_runtime_polling() -> None:
    """Install the grouped reader exactly once for this Home Assistant process."""
    global _INSTALLED
    if _INSTALLED:
        return
    AutarcoModbusClient._read_once_locked = _profiled_read_once_locked
    _INSTALLED = True
