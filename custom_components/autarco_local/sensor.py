"""Sensor platform for Autarco Local."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AutarcoLocalCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Autarco Local sensors."""
    coordinator: AutarcoLocalCoordinator = entry.runtime_data
    async_add_entities(
        [
            AutarcoConnectionSensor(coordinator, entry),
            AutarcoRawRegistersSensor(coordinator, entry),
            AutarcoDeviceTimeSensor(coordinator, entry),
        ]
    )


class AutarcoBaseSensor(CoordinatorEntity[AutarcoLocalCoordinator], SensorEntity):
    """Base Autarco sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutarcoLocalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )


class AutarcoConnectionSensor(AutarcoBaseSensor):
    """Connection status sensor."""

    _attr_name = "Verbinding"
    _attr_unique_id = "autarco_local_connection"
    _attr_icon = "mdi:lan-connect"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        return "online" if self.coordinator.last_update_success else "offline"


class AutarcoRawRegistersSensor(AutarcoBaseSensor):
    """Raw register diagnostic sensor."""

    _attr_name = "Ruwe Modbus-registers"
    _attr_unique_id = "autarco_local_raw_registers"
    _attr_icon = "mdi:code-json"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            f"register_{address}": value
            for address, value in sorted(data.items())
        }


class AutarcoDeviceTimeSensor(AutarcoBaseSensor):
    """Best-effort inverter clock sensor based on observed registers."""

    _attr_name = "Omvormerklok"
    _attr_unique_id = "autarco_local_device_time"
    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = "timestamp"

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data or {}
        try:
            year = 2000 + int(data[33022])
            month = int(data[33023])
            day = int(data[33024])
            hour = int(data[33025])
            minute = int(data[33026])
            second = int(data[33027])
            return datetime(year, month, day, hour, minute, second)
        except (KeyError, TypeError, ValueError):
            return None
