"""BLE-first read-only connection with TCP fallback and background recovery."""

from __future__ import annotations

import asyncio
from dataclasses import replace
import time
from threading import Lock
from typing import Any

from .ble_client import AutarcoBleClient
from .const import BLE_RECOVERY_INTERVAL, TRANSPORT_BLE, TRANSPORT_BLE_TCP, TRANSPORT_TCP
from .modbus_client import AutarcoConnectionError, AutarcoConnectionSettings, AutarcoModbusClient
from .runtime_quality import EMS_REGISTERS


class AutarcoFailoverClient:
    """Publish each poll from one source; never route a write across transports.

    BLE recovery uses one temperature read on the existing BLE session in a
    background task. TCP telemetry keeps flowing while BLE connects. A recovered
    link is promoted only after the next complete BLE runtime poll succeeds.
    """

    write_supported = False

    def __init__(self, hass, ble_settings: AutarcoConnectionSettings,
                 tcp_settings: AutarcoConnectionSettings) -> None:
        self.ble = AutarcoBleClient(hass, ble_settings)
        self.tcp = AutarcoModbusClient(tcp_settings)
        self._settings = ble_settings
        self._lock = Lock()
        self._state_lock = Lock()
        self._active_transport = TRANSPORT_BLE
        self._primary_ready = False
        self._next_probe_at = 0.0
        self._probe_running = False
        self._probe_generation = 0
        self._closed = False
        self.last_ble_error: str | None = None
        self.last_tcp_error: str | None = None
        self.fallback_count = 0
        self.recovery_count = 0

    @property
    def paused(self) -> bool:
        return self.ble.paused

    @property
    def active_transport(self) -> str:
        return self._active_transport

    @property
    def connected(self) -> bool:
        if self._active_transport == TRANSPORT_BLE:
            return self.ble.session.connected and not self.paused
        return self.tcp._client is not None and self.tcp._client.connected

    def validate(self) -> None:
        """Accept a usable primary or fallback; both tests only read registers."""
        try:
            self.ble.validate()
        except AutarcoConnectionError as ble_error:
            try:
                self.tcp.validate()
            except AutarcoConnectionError as tcp_error:
                raise AutarcoConnectionError(
                    f"Bluetooth: {ble_error}; wifi/TCP: {tcp_error}"
                ) from tcp_error

    def read_all(self):
        with self._lock:
            started = time.monotonic()
            with self._state_lock:
                if self._closed:
                    raise AutarcoConnectionError("Verbindingsbeheer is afgesloten")
                try_primary = not self.paused and (
                    self._active_transport == TRANSPORT_BLE or self._primary_ready
                )
                self._primary_ready = False
            if try_primary:
                try:
                    result = self.ble.read_all()
                    if not EMS_REGISTERS.issubset(result.registers):
                        raise AutarcoConnectionError("Bluetooth mist benodigde runtime-registers; wifi-terugval gebruiken")
                except AutarcoConnectionError as error:
                    self.last_ble_error = str(error)
                    self.ble.close()
                    with self._state_lock:
                        self._next_probe_at = time.monotonic() + BLE_RECOVERY_INTERVAL
                else:
                    if self._active_transport == TRANSPORT_TCP:
                        self.recovery_count += 1
                    self._active_transport = TRANSPORT_BLE
                    self.last_ble_error = None
                    self.tcp.close()
                    return replace(result, source_transport=TRANSPORT_BLE,
                                   poll_duration_ms=round((time.monotonic() - started) * 1000, 1))
            try:
                result = self.tcp.read_all()
            except AutarcoConnectionError as error:
                self.last_tcp_error = str(error)
                # Ensure recovery is still scheduled if the first ever poll
                # fails on both routes before HA finishes setup.
                self._active_transport = TRANSPORT_TCP
                raise AutarcoConnectionError(
                    f"Bluetooth: {self.last_ble_error or 'gepauzeerd'}; wifi/TCP: {error}"
                ) from error
            if self._active_transport != TRANSPORT_TCP:
                self.fallback_count += 1
            self._active_transport = TRANSPORT_TCP
            self.last_tcp_error = None
            return replace(result, source_transport=TRANSPORT_TCP,
                           poll_duration_ms=round((time.monotonic() - started) * 1000, 1))

    def read_settings(self):
        with self._lock:
            if self._active_transport == TRANSPORT_BLE and not self.paused:
                return replace(self.ble.read_settings(), source_transport=TRANSPORT_BLE)
            return replace(self.tcp.read_settings(), source_transport=TRANSPORT_TCP)

    @property
    def primary_probe_due(self) -> bool:
        with self._state_lock:
            return bool(not self._closed and not self.paused and not self._probe_running
                        and not self._primary_ready and self._active_transport == TRANSPORT_TCP
                        and time.monotonic() >= self._next_probe_at)

    async def async_probe_primary(self) -> None:
        """Test BLE without blocking TCP reads or creating a second BLE client."""
        if not self.primary_probe_due:
            return
        with self._state_lock:
            self._probe_running = True
            generation = self._probe_generation
            self._next_probe_at = time.monotonic() + BLE_RECOVERY_INTERVAL
        try:
            await self.ble.session.ensure_connected()
            with self._state_lock:
                valid = not self._closed and not self.paused and generation == self._probe_generation
            if not valid:
                await self.ble.session.disconnect()
                return
            await self.ble.session.read(4, 33093, 1)
        except asyncio.CancelledError:
            await self.ble.session.disconnect()
            raise
        except Exception as error:
            self.last_ble_error = str(error)
            await self.ble.session.disconnect()
        else:
            with self._state_lock:
                valid = not self._closed and not self.paused and generation == self._probe_generation
                self._primary_ready = valid
            if not valid:
                await self.ble.session.disconnect()
        finally:
            with self._state_lock:
                self._probe_running = False
                self._next_probe_at = time.monotonic() + BLE_RECOVERY_INTERVAL

    def set_paused(self, paused: bool) -> None:
        # Invalidates a recovery already in flight. A late successful probe
        # must never reclaim the radio after the user releases it to their app.
        with self._state_lock:
            self._probe_generation += 1
            self._primary_ready = False
            self._next_probe_at = 0.0 if not paused else float("inf")
        self.ble.set_paused(paused)

    def close(self) -> None:
        with self._state_lock:
            self._closed = True
            self._primary_ready = False
            self._probe_generation += 1
        with self._lock:
            self.ble.close()
            self.tcp.close()

    def _write_single_holding_locked(self, *args, **kwargs) -> None:
        raise AutarcoConnectionError("Bluetooth met wifi-terugval is alleen-lezen in deze beta")

    @property
    def transport_health(self) -> dict[str, Any]:
        return {
            **self.ble.transport_health,
            "transport": self._active_transport,
            "configured_transport": TRANSPORT_BLE_TCP,
            "primary_transport": TRANSPORT_BLE,
            "fallback_enabled": True,
            "fallback_active": self._active_transport == TRANSPORT_TCP,
            "fallback_reason": "Bluetooth vrijgegeven voor Solis-app" if self.paused else self.last_ble_error,
            "fallback_count": self.fallback_count,
            "ble_recovery_count": self.recovery_count,
            "ble_recovery_running": self._probe_running,
            "ble_recovery_interval_seconds": BLE_RECOVERY_INTERVAL,
            "tcp_last_error": self.last_tcp_error,
            "write_supported": False,
        }
