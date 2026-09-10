"""SOC jump/drop monitoring for Autarco Local v0.7.3.

This layer is read-only. It observes consecutive successful runtime polls and
classifies abrupt battery SOC corrections so Home Assistant can record and
visualise them. It never writes inverter or battery settings.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import AutarcoLocalCoordinator

_INSTALLED = False
_SENSOR_PATCHED = False
SOC_REGISTER = 33139
BATTERY_DIRECTION_REGISTER = 33135
BATTERY_POWER_HIGH_REGISTER = 33149
BATTERY_POWER_LOW_REGISTER = 33150
SOC_EVENT_THRESHOLD_PERCENT = 5.0
SOC_EVENT_MAX_INTERVAL_SECONDS = 180.0


def _battery_power(data: dict[int, int]) -> int | None:
    if BATTERY_POWER_HIGH_REGISTER not in data or BATTERY_POWER_LOW_REGISTER not in data:
        return None
    value = (data[BATTERY_POWER_HIGH_REGISTER] << 16) | data[BATTERY_POWER_LOW_REGISTER]
    # Same sign convention as sensor.py: negative = charging, positive = discharging.
    if data.get(BATTERY_DIRECTION_REGISTER) == 1:
        value *= -1
    return value


def _ensure_state(coordinator: AutarcoLocalCoordinator) -> None:
    if hasattr(coordinator, "soc_monitor_events"):
        return
    coordinator.soc_monitor_previous_soc = None
    coordinator.soc_monitor_previous_at = None
    coordinator.soc_monitor_state = "normal"
    coordinator.soc_monitor_last_event = None
    coordinator.soc_monitor_event_count = 0
    coordinator.soc_monitor_events = deque(maxlen=100)


def _serialize_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    result = dict(event)
    timestamp = result.get("timestamp")
    if isinstance(timestamp, datetime):
        result["timestamp"] = timestamp.isoformat()
    return result


def snapshot(coordinator: AutarcoLocalCoordinator) -> dict[str, Any]:
    """Return a serialisable SOC-monitor snapshot."""
    _ensure_state(coordinator)
    return {
        "state": coordinator.soc_monitor_state,
        "threshold_percent": SOC_EVENT_THRESHOLD_PERCENT,
        "max_interval_seconds": SOC_EVENT_MAX_INTERVAL_SECONDS,
        "previous_soc": coordinator.soc_monitor_previous_soc,
        "previous_at": coordinator.soc_monitor_previous_at.isoformat()
        if coordinator.soc_monitor_previous_at
        else None,
        "event_count": coordinator.soc_monitor_event_count,
        "last_event": _serialize_event(coordinator.soc_monitor_last_event),
        "events": [_serialize_event(event) for event in list(coordinator.soc_monitor_events)[-50:]],
    }


def _observe(coordinator: AutarcoLocalCoordinator, data: dict[int, int]) -> None:
    _ensure_state(coordinator)
    raw_soc = data.get(SOC_REGISTER)
    if raw_soc is None:
        return
    try:
        soc = float(raw_soc)
    except (TypeError, ValueError):
        return
    if not 0 <= soc <= 100:
        return

    now = dt_util.utcnow()
    previous_soc = coordinator.soc_monitor_previous_soc
    previous_at = coordinator.soc_monitor_previous_at

    coordinator.soc_monitor_previous_soc = soc
    coordinator.soc_monitor_previous_at = now

    if previous_soc is None or previous_at is None:
        return

    elapsed = max(0.0, (now - previous_at).total_seconds())
    if elapsed <= 0 or elapsed > SOC_EVENT_MAX_INTERVAL_SECONDS:
        return

    delta = soc - float(previous_soc)
    if abs(delta) < SOC_EVENT_THRESHOLD_PERCENT:
        coordinator.soc_monitor_state = "normal"
        return

    classification = "jump" if delta > 0 else "drop"
    power_w = _battery_power(data)
    event = {
        "timestamp": now,
        "classification": classification,
        "from_soc": round(float(previous_soc), 1),
        "to_soc": round(soc, 1),
        "delta_percent": round(delta, 1),
        "elapsed_seconds": round(elapsed, 1),
        "battery_power_w": power_w,
    }
    coordinator.soc_monitor_state = classification
    coordinator.soc_monitor_last_event = event
    coordinator.soc_monitor_event_count += 1
    coordinator.soc_monitor_events.append(event)

    coordinator.hass.bus.async_fire(
        "autarco_local_soc_anomaly",
        {
            **_serialize_event(event),
            "threshold_percent": SOC_EVENT_THRESHOLD_PERCENT,
        },
    )


class SocChangeMonitorSensor(CoordinatorEntity, SensorEntity):
    """Recorder-visible SOC jump/drop monitor."""

    _attr_has_entity_name = True
    _attr_name = "SOC jump/drop monitor"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-alert-variant-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_soc_jump_drop_monitor"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )

    @property
    def native_value(self):
        return snapshot(self.coordinator)["state"]

    @property
    def extra_state_attributes(self):
        monitor = snapshot(self.coordinator)
        return {
            "threshold_percent": monitor["threshold_percent"],
            "max_interval_seconds": monitor["max_interval_seconds"],
            "event_count": monitor["event_count"],
            "last_event": monitor["last_event"],
            "events": monitor["events"][-20:],
        }


def _install_sensor_entity() -> None:
    """Append the diagnostic sensor to the existing sensor platform once."""
    global _SENSOR_PATCHED
    if _SENSOR_PATCHED:
        return
    from . import sensor as sensor_platform

    original_setup_entry = sensor_platform.async_setup_entry

    async def setup_entry_with_soc_monitor(hass, entry, async_add_entities):
        await original_setup_entry(hass, entry, async_add_entities)
        async_add_entities([SocChangeMonitorSensor(entry.runtime_data, entry)])

    sensor_platform.async_setup_entry = setup_entry_with_soc_monitor
    _SENSOR_PATCHED = True


def install_soc_monitoring() -> None:
    """Wrap the already instrumented coordinator update path exactly once."""
    global _INSTALLED
    _install_sensor_entity()
    if _INSTALLED:
        return

    original_update = AutarcoLocalCoordinator._async_update_data

    async def monitored_update(self: AutarcoLocalCoordinator):
        _ensure_state(self)
        try:
            data = await original_update(self)
        except UpdateFailed:
            raise
        else:
            if isinstance(data, dict):
                _observe(self, data)
            return data

    AutarcoLocalCoordinator._async_update_data = monitored_update
    _INSTALLED = True
