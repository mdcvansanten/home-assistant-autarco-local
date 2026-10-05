"""Persistent BLE transport using Home Assistant's shared Bluetooth manager.

The synchronous facade preserves the existing TCP client's executor/transaction
lock contract. All actual Bluetooth I/O runs on HA's event loop. It must never
be invoked directly on that loop. BLE configuration writes remain disabled in
this beta until a physical write/read-back/restore test is completed.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError
import logging
import time
from typing import Any, Coroutine

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .ble_protocol import ModbusReadException, ReadFrameStream, decode_read, read_request
from .const import BLE_RUNTIME_BLOCKS, SETTING_REGISTER_BLOCKS
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoConnectionSettings,
    AutarcoModbusClient,
    AutarcoSettingsReadResult,
)

_LOGGER = logging.getLogger(__name__)
TX_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
RX_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"


class BleSession:
    """Own exactly one BLE client, subscription and outstanding RTU request."""

    def __init__(self, hass: HomeAssistant, address: str, unit: int, timeout: float) -> None:
        self.hass = hass
        self.address = address
        self.timeout = timeout
        self.client = None
        self.stream = ReadFrameStream({unit, 0xFE})
        self.pending: asyncio.Future[bytes] | None = None
        self.expected: tuple[int, int] | None = None
        self.generation = 0
        self.lock = asyncio.Lock()
        self.notifications = 0
        self.valid_frames = 0
        self.unmatched_frames = 0
        self.timeouts = 0
        self.connect_count = 0
        self.last_rssi: int | None = None
        self.rssi_timestamp: float | None = None
        self.adapter_source: str | None = None
        self.next_connect_at = 0.0
        self.connect_failures = 0

    @property
    def connected(self) -> bool:
        return self.client is not None and self.client.is_connected

    def _disconnected(self, client) -> None:
        if client is not self.client:
            return
        self.client = None
        self.generation += 1
        self.stream.clear()
        if self.pending is not None and not self.pending.done():
            self.pending.set_exception(AutarcoConnectionError("Bluetooth-verbinding verbroken"))

    async def ensure_connected(self) -> bool:
        if self.connected:
            return False
        remaining = self.next_connect_at - time.monotonic()
        if remaining > 0:
            raise AutarcoConnectionError(f"Bluetooth-herstel wacht nog {remaining:.0f} s")
        device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if device is None:
            raise AutarcoConnectionError(
                "Omvormer niet bereikbaar via een HA-Bluetoothadapter. "
                "Controleer bereik en verbreek de lokale Solis-appverbinding."
            )
        info = bluetooth.async_last_service_info(self.hass, self.address, connectable=True)
        if info:
            self.last_rssi = info.rssi
            self.rssi_timestamp = time.time()
            self.adapter_source = info.source
        candidate = None
        try:
            async with asyncio.timeout(40):
                candidate = await establish_connection(
                    BleakClientWithServiceCache,
                    device,
                    device.name or self.address,
                    disconnected_callback=self._disconnected,
                    max_attempts=2,
                    timeout=20,
                )
                self.client = candidate
                if not candidate.services.get_characteristic(TX_UUID) or not candidate.services.get_characteristic(RX_UUID):
                    await candidate.clear_cache()
                    raise AutarcoConnectionError("Omvormer mist BLE-kenmerken FFE1/FFE2")
                self.generation += 1
                generation = self.generation
                self.stream.clear()

                def notification(_sender, data) -> None:
                    if generation == self.generation:
                        self.receive(bytes(data))

                await candidate.start_notify(RX_UUID, notification)
                if not candidate.is_connected:
                    raise AutarcoConnectionError("Bluetooth-verbinding viel weg tijdens aanmelden")
        except BaseException:
            await self.disconnect()
            if candidate is not None and candidate.is_connected:
                await candidate.disconnect()
            self.connect_failures += 1
            self.next_connect_at = time.monotonic() + min(2 ** self.connect_failures, 60)
            raise
        self.connect_failures = 0
        self.next_connect_at = 0.0
        self.connect_count += 1
        return True

    def receive(self, data: bytes) -> None:
        self.notifications += 1
        for frame in self.stream.feed(data):
            self.valid_frames += 1
            if self.pending is None or self.pending.done() or self.expected is None:
                self.unmatched_frames += 1
                continue
            function, count = self.expected
            if frame[1] not in (function, function | 0x80):
                self.unmatched_frames += 1
                continue
            if frame[1] == function and frame[2] != count * 2:
                self.unmatched_frames += 1
                continue
            self.pending.set_result(frame)

    async def disconnect(self) -> None:
        candidate = self.client
        self.client = None
        self.generation += 1
        self.stream.clear()
        if self.pending is not None and not self.pending.done():
            self.pending.set_exception(AutarcoConnectionError("Bluetooth-verbinding gesloten"))
        if candidate is not None:
            try:
                async with asyncio.timeout(10):
                    await candidate.disconnect()
            except Exception:
                _LOGGER.debug("Bluetooth-afsluiten mislukt", exc_info=True)

    async def read(self, function: int, address: int, count: int) -> list[int]:
        async with self.lock:
            if not self.connected:
                raise AutarcoConnectionError("Bluetooth-verbinding is niet actief")
            self.stream.clear()
            self.expected = (function, count)
            pending = self.pending = asyncio.get_running_loop().create_future()
            try:
                async with asyncio.timeout(self.timeout):
                    await self.client.write_gatt_char(
                        TX_UUID, read_request(function, address, count), response=False
                    )
                    frame = await pending
                return decode_read(frame, function, count)
            except ModbusReadException:
                # Illegal register != broken link. The block reader can skip it.
                raise
            except BaseException as err:
                if isinstance(err, TimeoutError):
                    self.timeouts += 1
                # A late response has no register address. Discard the entire
                # connection before another read to prevent false correlation.
                self.pending = None
                await self.disconnect()
                raise
            finally:
                if not pending.done():
                    pending.cancel()
                elif not pending.cancelled():
                    pending.exception()  # Retrieve disconnect/write errors too.
                self.pending = None
                self.expected = None


class AutarcoBleClient(AutarcoModbusClient):
    """Executor-only facade reusing existing polling and transaction locking."""

    transport = "ble"

    def __init__(self, hass: HomeAssistant, settings: AutarcoConnectionSettings) -> None:
        super().__init__(settings)
        self._loop = asyncio.get_running_loop()
        self.session = BleSession(hass, settings.host, settings.device_id, settings.timeout)
        self.paused = False

    def _submit(self, operation: Coroutine[Any, Any, Any]):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is self._loop:
            operation.close()
            raise RuntimeError("BLE facade must run in the HA executor")
        future = asyncio.run_coroutine_threadsafe(operation, self._loop)
        try:
            return future.result(timeout=60)
        except ModbusReadException:
            raise
        except FutureTimeoutError as err:
            future.cancel()
            raise AutarcoConnectionError("Bluetooth-bewerking duurde te lang") from err
        except Exception as err:
            raise AutarcoConnectionError(f"{type(err).__name__}: {err}") from err

    def _disconnect_locked(self) -> None:
        self._submit(self.session.disconnect())

    def _ensure_connected_locked(self, reason: str | None = None) -> tuple[float, bool, str | None]:
        if self.paused:
            raise AutarcoConnectionError("Bluetooth gepauzeerd voor lokale Solis-appbediening")
        started = time.monotonic()
        connected = self._submit(self.session.ensure_connected())
        reconnect = connected and self._ever_connected
        if connected:
            self._ever_connected = True
        return (time.monotonic() - started) * 1000, reconnect, reason if reconnect else None

    def validate(self) -> None:
        with self._lock:
            try:
                self._ensure_connected_locked()
                self._submit(self.session.read(4, 33093, 1))
            finally:
                self._disconnect_locked()

    def _read_blocks_locked(self, function: int, blocks) -> tuple[dict[int, int], list[str]]:
        registers: dict[int, int] = {}
        unsupported: list[str] = []

        def read_range(start, count):
            try:
                values = self._submit(self.session.read(function, start, count))
            except ModbusReadException as err:
                if err.code == 2 and count > 1:
                    half = count // 2
                    read_range(start, half)
                    read_range(start + half, count - half)
                    return
                if err.code in (1, 2):
                    unsupported.append(f"{start}-{start + count - 1}")
                    return
                raise AutarcoConnectionError(f"Register {start}: {err}") from err
            registers.update({start + offset: value for offset, value in enumerate(values)})
            # Serialise modestly; an extra ping is unnecessary because each poll
            # itself is a read-only heartbeat.
            time.sleep(0.03)
        for start, count in blocks:
            read_range(start, count)
        return registers, unsupported

    def _read_once_locked(self) -> tuple[dict[int, int], list[str]]:
        registers, unsupported = self._read_blocks_locked(4, BLE_RUNTIME_BLOCKS)
        if 33093 not in registers:
            raise AutarcoConnectionError("Temperatuurregister ontbreekt in de BLE-poll")
        return registers, unsupported

    def read_settings(self) -> AutarcoSettingsReadResult:
        with self._lock:
            self._ensure_connected_locked()
            started = time.monotonic()
            registers, unsupported = self._read_blocks_locked(3, SETTING_REGISTER_BLOCKS)
            return AutarcoSettingsReadResult(
                registers, round((time.monotonic() - started) * 1000, 1), tuple(unsupported)
            )

    def _read_single_holding_locked(self, register: int, context: str) -> int:
        try:
            return self._submit(self.session.read(3, register, 1))[0]
        except ModbusReadException as err:
            raise AutarcoConnectionError(f"{context}: {err}") from err

    def _write_single_holding_locked(self, register: int, value: int, context: str) -> None:
        raise AutarcoConnectionError(
            "BLE-instellingen zijn alleen-lezen in deze beta. "
            "Schrijven/read-back/restore via BLE moet eerst op de omvormer worden gevalideerd."
        )

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            self.paused = paused
            if paused:
                self._disconnect_locked()

    @property
    def transport_health(self) -> dict[str, Any]:
        return {
            "transport": "ble",
            "ble_connected": self.session.connected,
            "ble_paused": self.paused,
            "ble_rssi_at_connect": self.session.last_rssi,
            "ble_rssi_observed_at": self.session.rssi_timestamp,
            "ble_notifications": self.session.notifications,
            "ble_valid_frames": self.session.valid_frames,
            "ble_unmatched_frames": self.session.unmatched_frames,
            "ble_discarded_bytes": self.session.stream.dropped_bytes,
            "ble_timeouts": self.session.timeouts,
            "ble_connections": self.session.connect_count,
            "ble_write_supported": False,
        }
