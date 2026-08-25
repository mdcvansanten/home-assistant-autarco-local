"""Deep connection monitoring for Autarco Local v0.7.1.

This layer separates transport reachability from Modbus protocol health. It does
not change the normal polling cadence and performs an independent TCP/502 probe
only after a failed runtime poll. Successful Modbus polls imply TCP reachability
without opening an extra socket.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import socket
import time
from typing import Any

from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from .coordinator import AutarcoLocalCoordinator

_INSTALLED = False


@dataclass(slots=True, frozen=True)
class TcpProbeResult:
    reachable: bool
    duration_ms: float
    error: str | None


def probe_tcp(host: str, port: int, timeout: float = 2.0) -> TcpProbeResult:
    """Probe TCP reachability without sending a Modbus request."""
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except (OSError, TimeoutError) as err:
        return TcpProbeResult(
            reachable=False,
            duration_ms=round((time.monotonic() - started) * 1000, 1),
            error=f"{type(err).__name__}: {err}",
        )
    return TcpProbeResult(
        reachable=True,
        duration_ms=round((time.monotonic() - started) * 1000, 1),
        error=None,
    )


def _ensure_state(coordinator: AutarcoLocalCoordinator) -> None:
    if hasattr(coordinator, "connection_monitor_events"):
        return
    coordinator.connection_monitor_state = "unknown"
    coordinator.connection_monitor_stage = "startup"
    coordinator.connection_monitor_classification = "unknown"
    coordinator.connection_monitor_last_error = None
    coordinator.connection_monitor_last_failed_group = None
    coordinator.connection_monitor_last_tcp_probe_ms = None
    coordinator.connection_monitor_last_tcp_probe_at = None
    coordinator.connection_monitor_last_tcp_success_at = None
    coordinator.connection_monitor_last_tcp_failure_at = None
    coordinator.connection_monitor_last_modbus_success_at = None
    coordinator.connection_monitor_last_modbus_failure_at = None
    coordinator.connection_monitor_tcp_reachable = None
    coordinator.connection_monitor_events = deque(maxlen=100)


def _record(
    coordinator: AutarcoLocalCoordinator,
    *,
    state: str,
    stage: str,
    classification: str,
    error: str | None = None,
    tcp_reachable: bool | None = None,
    tcp_probe_ms: float | None = None,
    failed_group: str | None = None,
) -> None:
    _ensure_state(coordinator)
    now = dt_util.utcnow()
    previous_classification = coordinator.connection_monitor_classification

    coordinator.connection_monitor_state = state
    coordinator.connection_monitor_stage = stage
    coordinator.connection_monitor_classification = classification
    coordinator.connection_monitor_last_error = error
    coordinator.connection_monitor_last_failed_group = failed_group
    coordinator.connection_monitor_tcp_reachable = tcp_reachable
    if tcp_probe_ms is not None:
        coordinator.connection_monitor_last_tcp_probe_ms = tcp_probe_ms
        coordinator.connection_monitor_last_tcp_probe_at = now
    if tcp_reachable is True:
        coordinator.connection_monitor_last_tcp_success_at = now
    elif tcp_reachable is False:
        coordinator.connection_monitor_last_tcp_failure_at = now

    # Store transitions and every failure/degraded poll; do not fill history with
    # identical healthy polls.
    if classification != previous_classification or state != "healthy":
        coordinator.connection_monitor_events.append(
            {
                "timestamp": now,
                "state": state,
                "stage": stage,
                "classification": classification,
                "tcp_reachable": tcp_reachable,
                "tcp_probe_ms": tcp_probe_ms,
                "failed_group": failed_group,
                "error": error,
            }
        )


def snapshot(coordinator: AutarcoLocalCoordinator) -> dict[str, Any]:
    """Return serialisable deep connection diagnostics."""
    _ensure_state(coordinator)
    events = []
    for event in coordinator.connection_monitor_events:
        events.append(
            {
                **event,
                "timestamp": event["timestamp"].isoformat()
                if event.get("timestamp")
                else None,
            }
        )
    return {
        "state": coordinator.connection_monitor_state,
        "stage": coordinator.connection_monitor_stage,
        "classification": coordinator.connection_monitor_classification,
        "tcp_502_reachable": coordinator.connection_monitor_tcp_reachable,
        "last_tcp_probe_ms": coordinator.connection_monitor_last_tcp_probe_ms,
        "last_tcp_probe_at": coordinator.connection_monitor_last_tcp_probe_at,
        "last_tcp_success_at": coordinator.connection_monitor_last_tcp_success_at,
        "last_tcp_failure_at": coordinator.connection_monitor_last_tcp_failure_at,
        "last_modbus_success_at": coordinator.connection_monitor_last_modbus_success_at,
        "last_modbus_failure_at": coordinator.connection_monitor_last_modbus_failure_at,
        "last_failed_group": coordinator.connection_monitor_last_failed_group,
        "last_error": coordinator.connection_monitor_last_error,
        "poll_strategy": getattr(
            coordinator.client, "last_runtime_poll_strategy", "legacy_full_range"
        ),
        "poll_request_count": getattr(
            coordinator.client, "last_runtime_request_count", None
        ),
        "current_runtime_group": getattr(
            coordinator.client, "current_runtime_group", None
        ),
        "runtime_fallback_groups": list(
            getattr(coordinator.client, "last_runtime_fallback_groups", ())
        ),
        "events": events[-50:],
    }


def install_connection_monitoring() -> None:
    """Wrap the coordinator update path exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return

    original_update = AutarcoLocalCoordinator._async_update_data

    async def classify_failure(self: AutarcoLocalCoordinator, *, hard: bool) -> None:
        self.connection_monitor_last_modbus_failure_at = dt_util.utcnow()
        host = str(self.client._settings.host)
        port = int(self.client._settings.port)
        probe = await self.hass.async_add_executor_job(probe_tcp, host, port, 2.0)
        failed_group = getattr(self.client, "last_runtime_failed_group", None)
        if probe.reachable:
            classification = "tcp_up_modbus_failed"
            stage = "modbus_protocol_or_logger"
        else:
            classification = "tcp_502_down"
            stage = "network_or_logger_tcp"
        _record(
            self,
            state="failed" if hard else "degraded",
            stage=stage,
            classification=classification,
            error=self.last_error,
            tcp_reachable=probe.reachable,
            tcp_probe_ms=probe.duration_ms,
            failed_group=failed_group,
        )
        self.async_update_listeners()

    async def monitored_update(self: AutarcoLocalCoordinator):
        _ensure_state(self)
        self.connection_monitor_stage = "runtime_modbus_poll"
        failed_before = self.failed_polls
        try:
            data = await original_update(self)
        except UpdateFailed:
            await classify_failure(self, hard=True)
            raise
        else:
            # The coordinator deliberately suppresses the first short outages and
            # returns the previous snapshot. Detect those via failed_polls so they
            # remain visible to diagnostics.
            if self.failed_polls > failed_before:
                await classify_failure(self, hard=False)
                return data

            now = dt_util.utcnow()
            self.connection_monitor_last_modbus_success_at = now
            self.connection_monitor_last_tcp_success_at = now
            _record(
                self,
                state="healthy",
                stage="runtime_modbus_poll",
                classification="modbus_healthy",
                error=None,
                tcp_reachable=True,
                failed_group=None,
            )
            return data

    AutarcoLocalCoordinator._async_update_data = monitored_update
    _INSTALLED = True
