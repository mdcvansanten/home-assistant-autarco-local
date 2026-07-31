"""Coordinator for Autarco Local."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_ID,
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

_LOGGER = logging.getLogger(__name__)


class AutarcoLocalCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Coordinate stable, read-only Modbus polling."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry

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
        self._connection_established_once = False
        self.last_unsupported_blocks: tuple[str, ...] = ()

        settings = AutarcoConnectionSettings(
            str(entry.data[CONF_HOST]),
            int(entry.data.get(CONF_PORT, DEFAULT_PORT)),
            int(entry.data.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID)),
            int(entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
            int(entry.data.get(CONF_RETRIES, DEFAULT_RETRIES)),
        )
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

    async def async_shutdown(self) -> None:
        """Close the persistent socket during unload/reload."""
        await self.hass.async_add_executor_job(self.client.close)

    async def _async_update_data(self) -> dict[int, int]:
        """Fetch one complete register snapshot."""
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
                _LOGGER.warning("Autarco Modbus-poll mislukt: %s", err)
            else:
                _LOGGER.debug(
                    "Autarco Modbus-poll %s achtereen mislukt: %s",
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
                self._record_connection_event("disconnected", now, str(err), None)
                _LOGGER.warning(
                    "Autarco Modbus-verbinding verbroken na %s opeenvolgende mislukte polls: %s",
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

        self.successful_polls += 1
        self.total_retries += max(result.attempts - 1, 0)
        self.reconnect_count += result.reconnects
        if result.reconnect_reason:
            self.last_reconnect_reason = result.reconnect_reason
        self.last_response_ms = result.poll_duration_ms
        self.last_read_ms = result.read_duration_ms
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

        if not self._connection_established_once:
            self._connection_established_once = True
            self.connected_since = self.last_success_at
            self._record_connection_event("connected", self.last_success_at, None, None)
            _LOGGER.info(
                "Autarco Modbus-verbinding opgebouwd met %s:%s (device_id=%s)",
                self.client._settings.host,
                self.client._settings.port,
                self.client._settings.device_id,
            )
        elif self.connected_since is None:
            downtime = 0.0
            if self.outage_started_at is not None:
                downtime = max((self.last_success_at - self.outage_started_at).total_seconds(), 0.0)
                self.total_downtime_seconds += downtime
            self.last_reconnect_at = self.last_success_at
            self.connected_since = self.last_success_at
            self.outage_started_at = None
            self._record_connection_event("reconnected", self.last_success_at, None, downtime)
            _LOGGER.info(
                "Autarco Modbus-verbinding hersteld na %.1f seconden (%s mislukte polls)",
                downtime,
                self.consecutive_failures,
            )
        elif was_failing:
            _LOGGER.info(
                "Autarco Modbus-polling hersteld na %s tijdelijke mislukte poll(s)",
                self.consecutive_failures,
            )

        self.consecutive_failures = 0
        return result.registers


    def _record_connection_event(self, event: str, when, reason: str | None, downtime: float | None) -> None:
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
        return self.consecutive_failures < FAILURE_THRESHOLD and self.data is not None

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
        if self.last_poll_at is not None and self._connection_established_once:
            first = self.connection_events[0]["timestamp"] if self.connection_events else self.last_poll_at
            elapsed = max((dt_util.utcnow() - first).total_seconds(), 0.0)
        downtime = self.total_downtime_seconds + self.current_outage_seconds
        availability = round(max(0.0, (elapsed - downtime) / elapsed * 100), 3) if elapsed else None
        health_score = round(max(0.0, min(100.0, (success_rate or 0.0) - self.reconnect_count * 0.25)), 1) if total else None
        return {
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
            "last_poll_at": self.last_poll_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "connected_since": self.connected_since,
            "current_connection_uptime_seconds": round(self.current_connection_uptime_seconds, 1),
            "longest_connection_seconds": round(max(self.longest_connection_seconds, self.current_connection_uptime_seconds), 1),
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
        }
