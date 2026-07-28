"""Sensor platform for Autarco Local."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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
            AutarcoRegisterCountSensor(coordinator, entry),
            AutarcoRawRegistersSensor(coordinator, entry),
            AutarcoDeviceTimeSensor(coordinator, entry),
        ]
    )


class AutarcoBaseSensor(
    CoordinatorEntity[AutarcoLocalCoordinator],
    SensorEntity,
):
    """Base class for Autarco sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutarcoLocalCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize an Autarco sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
            configuration_url=(
                f"http://{entry.data['host']}"
                if entry.data.get("host")
                else None
            ),
        )


class AutarcoRegisterCountSensor(AutarcoBaseSensor):
    """Number of registers received in the latest poll."""

    def __init__(
        self,
        coordinator: AutarcoLocalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key="register_count",
                translation_key="register_count",
                icon="mdi:counter",
                entity_category=EntityCategory.DIAGNOSTIC,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> int:
        """Return the register count."""
        return len(self.coordinator.data or {})


class AutarcoRawRegistersSensor(AutarcoBaseSensor):
    """Raw Modbus register diagnostic sensor."""

    def __init__(
        self,
        coordinator: AutarcoLocalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key="raw_registers",
                translation_key="raw_registers",
                icon="mdi:code-json",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        )

    @property
    def native_value(self) -> str:
        """Return a compact state."""
        return "beschikbaar"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all registers as diagnostic attributes."""
        return {
            f"register_{address}": value
            for address, value in sorted((self.coordinator.data or {}).items())
        }


class AutarcoDeviceTimeSensor(AutarcoBaseSensor):
    """Best-effort inverter clock based on observed registers."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: AutarcoLocalCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key="device_time",
                translation_key="device_time",
                icon="mdi:clock-outline",
                entity_category=EntityCategory.DIAGNOSTIC,
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the interpreted inverter date and time."""
        data = self.coordinator.data or {}
        try:
            value = datetime(
                2000 + int(data[33022]),
                int(data[33023]),
                int(data[33024]),
                int(data[33025]),
                int(data[33026]),
                int(data[33027]),
                tzinfo=dt_util.DEFAULT_TIME_ZONE,
            )
        except (KeyError, TypeError, ValueError):
            return None
        return value
