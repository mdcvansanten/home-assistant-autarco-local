"""Coordinator for Autarco Local."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_ID,
    CONF_BLE_ADDRESS,
    CONF_TRANSPORT,
    CONF_RUNTIME_VALIDATED,
    TRANSPORT_TCP,
    TRANSPORT_BLE,
    TRANSPORT_BLE_TCP,
    BLE_TRANSPORTS,
    SETTINGS_SCAN_INTERVAL,
    CONF_RETRIES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    FAILURE_THRESHOLD,
)
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoConnectionSettings,
    AutarcoModbusClient,
)
from .runtime_quality import runtime_quality

_LOGGER = logging.getLogger(__name__)


class AutarcoLocalCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Coordinate stable, read-only Modbus polling."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.configured_transport = entry.data.get(CONF_TRANSPORT, TRANSPORT_TCP)
        self.transport = TRANSPORT_BLE if self.configured_transport in BLE_TRANSPORTS else TRANSPORT_TCP
        self.settings_transport = self.transport
        self._primary_probe_task = None
        self._ble_pause_requested = False
        self._next_settings_read_at = 0.0
        self.runtime_read_span_ms: float | None = None
        self.max_runtime_age = max(30, 2 * int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        self.successful_polls = 0
        self.failed_polls = 0
        self.consecutive_failures = 0
        self.total_retries = 0
        self.reconnect_count = 0
        self.suppressed_failures = 0

        self.last_response_ms: float | None = None
        self.last_read_ms: float | None = None
        self.last_connect_ms: float | None = None
        self.poll_duration_min_ms: float | None = None
        self.poll_duration_max_ms: float | None = None
        self.poll_duration_total_ms = 0.0
        self.last_attempts = 0
        self.last_success_at = None
        self.last_failure_at = None
        self.last_poll_at = None
        self.last_error: str | None = None
        self.last_reconnect_reason: str | None = None
        self.connected_since = None
        self.last_disconnect_at = None
        self.last_reconnect_at = None
        self.last_disconnect_reason: str | None = None
        self.outage_started_at = None
        self.longest_connection_seconds = 0.0
        self.total_downtime_seconds = 0.0
        self.connection_events: list[dict[str, Any]] = []
        self.disconnect_count = 0
        self.history_started_at = None
        self._connection_established_once = False
        self._history_store: Store[dict[str, Any]] = Store(
            hass, 1, f"{DOMAIN}.{entry.entry_id}.connection_history"
        )
        self.last_unsupported_blocks: tuple[str, ...] = ()

        # Settings are deliberately kept separate from the stable 33xxx runtime
        # snapshot. A failed holding-register read must never make normal
        # monitoring unavailable.
        self.settings_data: dict[int, int] = {}
        self.settings_read_time_ms: float | None = None
        self.settings_last_success_at = None
        self.settings_last_failure_at = None
        self.settings_last_error: str | None = None
        self.settings_unsupported_blocks: tuple[str, ...] = ()

        settings = AutarcoConnectionSettings(
            str(entry.data[CONF_BLE_ADDRESS] if self.configured_transport in BLE_TRANSPORTS else entry.data[CONF_HOST]),
            int(entry.data.get(CONF_PORT, DEFAULT_PORT)),
            int(entry.data.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID)),
            int(entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
            int(entry.data.get(CONF_RETRIES, DEFAULT_RETRIES)),
        )
        if self.configured_transport == TRANSPORT_BLE_TCP:
            from .failover_client import AutarcoFailoverClient
            tcp_settings = AutarcoConnectionSettings(
                str(entry.data[CONF_HOST]), settings.port, settings.device_id, settings.timeout, settings.retries
            )
            self.client = AutarcoFailoverClient(hass, settings, tcp_settings)
        elif self.configured_transport == TRANSPORT_BLE:
            from .ble_client import AutarcoBleClient
            self.client = AutarcoBleClient(hass, settings)
        else:
            self.client = AutarcoModbusClient(settings)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
            ),
            always_update=True,
        )

    async def async_initialize(self) -> None:
        """Restore persistent connection history before the first poll."""
        stored = await self._history_store.async_load()
        if not stored:
            return

        self.total_downtime_seconds = float(stored.get("total_downtime_seconds", 0.0))
        self.longest_connection_seconds = float(stored.get("longest_connection_seconds", 0.0))
        self.disconnect_count = int(stored.get("disconnect_count", 0))
        self.last_disconnect_reason = stored.get("last_disconnect_reason")
        self.last_disconnect_at = self._parse_stored_datetime(stored.get("last_disconnect_at"))
        self.last_reconnect_at = self._parse_stored_datetime(stored.get("last_reconnect_at"))
        self.history_started_at = self._parse_stored_datetime(stored.get("history_started_at"))
        self.outage_started_at = self._parse_stored_datetime(stored.get("outage_started_at"))
        self.connection_events = []
        for event in stored.get("connection_events", []):
            when = self._parse_stored_datetime(event.get("timestamp"))
            if when is not None:
                self.connection_events.append({
                    "event": event.get("event"),
                    "timestamp": when,
                    "reason": event.get("reason"),
                    "downtime_seconds": event.get("downtime_seconds"),
                })
        self.connection_events = self.connection_events[-50:]

    async def async_shutdown(self) -> None:
        """Persist diagnostics and close the socket during unload/reload."""
        await super().async_shutdown()
        await self._async_cancel_primary_probe()
        if self.connected_since is not None:
            self.longest_connection_seconds = max(
                self.longest_connection_seconds, self.current_connection_uptime_seconds
            )
        await self._async_save_history()
        await self.hass.async_add_executor_job(self.client.close)

    async def _async_cancel_primary_probe(self) -> None:
        if self._primary_probe_task is not None:
            self._primary_probe_task.cancel()
            try:
                await self._primary_probe_task
            except asyncio.CancelledError:
                pass
            self._primary_probe_task = None

    def _async_schedule_primary_probe(self) -> None:
        if (self.configured_transport != TRANSPORT_BLE_TCP or self._ble_pause_requested
                or not self.client.primary_probe_due):
            return
        if self._primary_probe_task is None or self._primary_probe_task.done():
            self._primary_probe_task = self.hass.async_create_background_task(
                self.client.async_probe_primary(), f"Autarco BLE recovery {self.config_entry.entry_id}"
            )

    async def async_set_ble_paused(self, paused: bool) -> None:
        self._ble_pause_requested = paused
        await self._async_cancel_primary_probe()
        await self.hass.async_add_executor_job(self.client.set_paused, paused)

    @staticmethod
    def _parse_stored_datetime(value):
        if not value:
            return None
        return dt_util.parse_datetime(value)

    async def _async_save_history(self) -> None:
        """Persist only long-term connection diagnostics."""
        events = []
        for event in self.connection_events[-50:]:
            events.append({
                "event": event.get("event"),
                "timestamp": event["timestamp"].isoformat() if event.get("timestamp") else None,
                "reason": event.get("reason"),
                "downtime_seconds": event.get("downtime_seconds"),
            })
        await self._history_store.async_save({
            "history_started_at": self.history_started_at.isoformat() if self.history_started_at else None,
            "last_disconnect_at": self.last_disconnect_at.isoformat() if self.last_disconnect_at else None,
            "last_reconnect_at": self.last_reconnect_at.isoformat() if self.last_reconnect_at else None,
            "last_disconnect_reason": self.last_disconnect_reason,
            "outage_started_at": self.outage_started_at.isoformat() if self.outage_started_at else None,
            "longest_connection_seconds": round(self.longest_connection_seconds, 1),
            "total_downtime_seconds": round(self.total_downtime_seconds, 1),
            "disconnect_count": self.disconnect_count,
            "connection_events": events,
        })

    async def _async_update_data(self) -> dict[int, int]:
        """Fetch one complete runtime snapshot plus non-critical settings."""
        self.last_poll_at = dt_util.utcnow()
        was_failing = self.consecutive_failures > 0

        try:
            result = await self.hass.async_add_executor_job(self.client.read_all)
        except AutarcoConnectionError as err:
            self.failed_polls += 1
            self.consecutive_failures += 1
            self.last_failure_at = dt_util.utcnow()
            self.last_error = str(err)

            if self.consecutive_failures == 1:
                _LOGGER.warning("Autarco-poll mislukt: %s", err)
            else:
                _LOGGER.debug(
                    "Autarco-poll %s achtereen mislukt: %s",
                    self.consecutive_failures,
                    err,
                )

            if self.consecutive_failures == FAILURE_THRESHOLD and self.connected_since is not None:
                now = self.last_failure_at
                uptime = max((now - self.connected_since).total_seconds(), 0.0)
                self.longest_connection_seconds = max(self.longest_connection_seconds, uptime)
                self.last_disconnect_at = now
                self.last_disconnect_reason = str(err)
                self.outage_started_at = now
                self.connected_since = None
                self.disconnect_count += 1
                self._record_connection_event("disconnected", now, str(err), None)
                await self._async_save_history()
                _LOGGER.warning(
                    "Autarco-verbinding verbroken na %s opeenvolgende mislukte polls: %s",
                    self.consecutive_failures,
                    err,
                )

            # Keep the previous snapshot available during a brief interruption.
            if self.data and self.consecutive_failures < FAILURE_THRESHOLD:
                self.suppressed_failures += 1
                return self.data

            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
        finally:
            self._async_schedule_primary_probe()

        previous_transport = self.transport
        self.transport = result.source_transport
        if previous_transport != self.transport:
            self._next_settings_read_at = 0.0
            self.settings_last_error = "Verbindingsbron gewijzigd; instellingen opnieuw lezen"
            self._record_connection_event("transport_changed", dt_util.utcnow(),
                                          f"{previous_transport} → {self.transport}", None)
            await self._async_save_history()

        self.successful_polls += 1
        self.total_retries += max(result.attempts - 1, 0)
        self.reconnect_count += result.reconnects
        if result.reconnect_reason:
            self.last_reconnect_reason = result.reconnect_reason
        self.last_response_ms = result.poll_duration_ms
        self.last_read_ms = result.read_duration_ms
        self.runtime_read_span_ms = result.read_duration_ms
        self.last_connect_ms = result.connect_duration_ms
        self.poll_duration_total_ms += result.poll_duration_ms
        self.poll_duration_min_ms = (
            result.poll_duration_ms
            if self.poll_duration_min_ms is None
            else min(self.poll_duration_min_ms, result.poll_duration_ms)
        )
        self.poll_duration_max_ms = (
            result.poll_duration_ms
            if self.poll_duration_max_ms is None
            else max(self.poll_duration_max_ms, result.poll_duration_ms)
        )
        self.last_attempts = result.attempts
        self.last_success_at = dt_util.utcnow()
        self.last_error = None
        self.last_unsupported_blocks = result.unsupported_blocks

        # Settings read is best-effort. Never feed its failures into the normal
        # connection failure counters or DataUpdateCoordinator availability.
        if time.monotonic() >= self._next_settings_read_at:
            self._next_settings_read_at = time.monotonic() + SETTINGS_SCAN_INTERVAL
            await self.async_refresh_settings()

        if not self._connection_established_once:
            self._connection_established_once = True
            self.connected_since = self.last_success_at
            if self.history_started_at is None:
                self.history_started_at = self.last_success_at

            if self.outage_started_at is not None:
                downtime = max(
                    (self.last_success_at - self.outage_started_at).total_seconds(), 0.0
                )
                self.total_downtime_seconds += downtime
                self.last_reconnect_at = self.last_success_at
                self.outage_started_at = None
                self._record_connection_event(
                    "reconnected", self.last_success_at, None, downtime
                )
                _LOGGER.info(
                    "Autarco-verbinding na herstart hersteld na %.1f seconden",
                    downtime,
                )
            else:
                self._record_connection_event("connected", self.last_success_at, None, None)
                _LOGGER.info(
                    "Autarco %s-verbinding opgebouwd met %s:%s (device_id=%s)",
                    self.transport,
                    self.client._settings.host,
                    self.client._settings.port,
                    self.client._settings.device_id,
                )
            await self._async_save_history()
        elif self.connected_since is None:
            downtime = 0.0
            if self.outage_started_at is not None:
                downtime = max((self.last_success_at - self.outage_started_at).total_seconds(), 0.0)
                self.total_downtime_seconds += downtime
            self.last_reconnect_at = self.last_success_at
            self.connected_since = self.last_success_at
            self.outage_started_at = None
            self._record_connection_event("reconnected", self.last_success_at, None, downtime)
            await self._async_save_history()
            _LOGGER.info(
                "Autarco-verbinding hersteld na %.1f seconden (%s mislukte polls)",
                downtime,
                self.consecutive_failures,
            )
        elif was_failing:
            _LOGGER.info(
                "Autarco-polling hersteld na %s tijdelijke mislukte poll(s)",
                self.consecutive_failures,
            )

        self.consecutive_failures = 0
        return result.registers

    async def async_refresh_settings(self) -> None:
        """Read settings separately; failures never invalidate runtime polling."""
        try:
            result = await self.hass.async_add_executor_job(self.client.read_settings)
        except AutarcoConnectionError as err:
            self.settings_last_failure_at = dt_util.utcnow()
            self.settings_last_error = str(err)
            _LOGGER.debug("Autarco settings-read mislukt: %s", err)
        else:
            self.settings_data = result.registers
            self.settings_read_time_ms = result.read_duration_ms
            self.settings_unsupported_blocks = result.unsupported_blocks
            self.settings_transport = result.source_transport
            self.settings_last_success_at = dt_util.utcnow()
            self.settings_last_error = None

    @property
    def runtime_age_seconds(self) -> float | None:
        if self.last_success_at is None:
            return None
        return max(0.0, (dt_util.utcnow() - self.last_success_at).total_seconds())

    @property
    def data_quality(self) -> str:
        if self.configured_transport == TRANSPORT_BLE and self.client.paused:
            return "paused"
        return runtime_quality(self.data, failed=self.consecutive_failures > 0,
                               age=self.runtime_age_seconds, max_age=self.max_runtime_age)

    @property
    def ems_data_ready(self) -> bool:
        """A telemetry gate, never permission for machine-generated writes."""
        return bool(self.config_entry.options.get(CONF_RUNTIME_VALIDATED, False)
                    and self.data_quality == "live" and self.connection_available
                    and self.successful_polls >= 5
                    and self.runtime_read_span_ms is not None
                    and self.runtime_read_span_ms <= 10000)

    def _record_connection_event(
        self, event: str, when, reason: str | None, downtime: float | None
    ) -> None:
        self.connection_events.append({
            "event": event,
            "timestamp": when,
            "reason": reason,
            "downtime_seconds": round(downtime, 1) if downtime is not None else None,
        })
        self.connection_events = self.connection_events[-50:]

    @property
    def current_connection_uptime_seconds(self) -> float:
        if self.connected_since is None or not self.connection_available:
            return 0.0
        return max((dt_util.utcnow() - self.connected_since).total_seconds(), 0.0)

    @property
    def current_outage_seconds(self) -> float:
        if self.outage_started_at is None:
            return 0.0
        return max((dt_util.utcnow() - self.outage_started_at).total_seconds(), 0.0)

    @property
    def connection_available(self) -> bool:
        """Return true while connection is healthy or only briefly degraded."""
        if self.configured_transport == TRANSPORT_BLE_TCP and not self.client.connected:
            return False
        if self.configured_transport == TRANSPORT_BLE and not self.client.session.connected:
            return False
        return self.consecutive_failures < FAILURE_THRESHOLD and self.data is not None

    @property
    def settings_available(self) -> bool:
        """Return true when at least one requested setting register was read."""
        if self.settings_last_success_at is None or self.settings_last_error:
            return False
        age = (dt_util.utcnow() - self.settings_last_success_at).total_seconds()
        return bool(self.settings_data) and age <= 2 * SETTINGS_SCAN_INTERVAL

    @property
    def settings_status(self) -> str:
        """Return a compact settings-layer health state."""
        if not self.settings_data:
            return "unavailable"
        if not self.settings_available:
            return "stale"
        if self.settings_last_error or self.settings_unsupported_blocks:
            return "partial"
        return "available"

    @property
    def network_health(self) -> dict[str, Any]:
        total = self.successful_polls + self.failed_polls
        success_rate = round(self.successful_polls / total * 100, 1) if total else None
        average_poll_ms = (
            round(self.poll_duration_total_ms / self.successful_polls, 1)
            if self.successful_polls
            else None
        )
        elapsed = 0.0
        if self.history_started_at is not None:
            elapsed = max((dt_util.utcnow() - self.history_started_at).total_seconds(), 0.0)
        downtime = self.total_downtime_seconds + self.current_outage_seconds
        availability = round(max(0.0, (elapsed - downtime) / elapsed * 100), 3) if elapsed else None
        health_score = success_rate
        return {
            **getattr(self.client, "transport_health", {}),
            "transport": self.transport,
            "active_transport": getattr(self.client, "active_transport", self.transport),
            "configured_transport": self.configured_transport,
            "settings_transport": self.settings_transport,
            "write_supported": self.configured_transport == TRANSPORT_TCP,
            "data_quality": self.data_quality,
            "runtime_age_seconds": self.runtime_age_seconds,
            "runtime_read_span_ms": self.runtime_read_span_ms,
            "runtime_mapping_validated": bool(self.config_entry.options.get(CONF_RUNTIME_VALIDATED, False)),
            "ems_data_ready": self.ems_data_ready,
            "ems_control_ready": False,
            "successful_polls": self.successful_polls,
            "failed_polls": self.failed_polls,
            "consecutive_failures": self.consecutive_failures,
            "failure_threshold": FAILURE_THRESHOLD,
            "suppressed_failures": self.suppressed_failures,
            "success_rate": success_rate,
            "last_response_ms": self.last_response_ms,
            "last_read_ms": self.last_read_ms,
            "last_connect_ms": self.last_connect_ms,
            "average_poll_ms": average_poll_ms,
            "min_poll_ms": self.poll_duration_min_ms,
            "max_poll_ms": self.poll_duration_max_ms,
            "last_attempts": self.last_attempts,
            "total_retries": self.total_retries,
            "reconnect_count": self.reconnect_count,
            "disconnect_count": self.disconnect_count,
            "history_started_at": self.history_started_at,
            "last_poll_at": self.last_poll_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "connected_since": self.connected_since,
            "current_connection_uptime_seconds": round(
                self.current_connection_uptime_seconds, 1
            ),
            "longest_connection_seconds": round(
                max(
                    self.longest_connection_seconds,
                    self.current_connection_uptime_seconds,
                ),
                1,
            ),
            "last_disconnect_at": self.last_disconnect_at,
            "last_reconnect_at": self.last_reconnect_at,
            "last_disconnect_reason": self.last_disconnect_reason,
            "outage_started_at": self.outage_started_at,
            "total_downtime_seconds": round(downtime, 1),
            "availability_percent": availability,
            "health_score": health_score,
            "connection_events": self.connection_events,
            "last_error": self.last_error,
            "last_reconnect_reason": self.last_reconnect_reason,
            "connection_available": self.connection_available,
            "unsupported_blocks": self.last_unsupported_blocks,
            "settings_status": self.settings_status,
            "settings_available": self.settings_available,
            "settings_register_count": len(self.settings_data),
            "settings_read_time_ms": self.settings_read_time_ms,
            "settings_last_success_at": self.settings_last_success_at,
            "settings_last_failure_at": self.settings_last_failure_at,
            "settings_last_error": self.settings_last_error,
            "unsupported_setting_blocks": self.settings_unsupported_blocks,
        }
