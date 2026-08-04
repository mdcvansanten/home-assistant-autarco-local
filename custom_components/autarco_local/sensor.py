"""Sensors for Autarco Local."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .settings import (
    decode_battery_model,
    decode_storage_mode,
    storage_mode_attributes,
)


def u16(data: dict[int, int], address: int) -> int | None:
    return data.get(address)


def s16(data: dict[int, int], address: int) -> int | None:
    value = data.get(address)
    return None if value is None else (
        value - 65536 if value >= 32768 else value
    )


def u32(data: dict[int, int], high: int, low: int) -> int | None:
    if high not in data or low not in data:
        return None
    return (data[high] << 16) | data[low]


def s32(data: dict[int, int], high: int, low: int) -> int | None:
    value = u32(data, high, low)
    return None if value is None else (
        value - 4294967296 if value >= 2147483648 else value
    )


@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription):
    value_fn: Callable[[dict[int, int]], Any]


@dataclass(frozen=True, kw_only=True)
class SettingDesc(SensorEntityDescription):
    register: int
    value_fn: Callable[[dict[int, int]], Any]
    attrs_fn: Callable[[int | None], dict[str, Any]] | None = None


SENSORS = (
    Desc(
        key="pv_voltage_1",
        translation_key="pv_voltage_1",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33049) / 10
        if u16(d, 33049) is not None
        else None,
    ),
    Desc(
        key="pv_current_1",
        translation_key="pv_current_1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33050) / 10
        if u16(d, 33050) is not None
        else None,
    ),
    Desc(
        key="pv_voltage_2",
        translation_key="pv_voltage_2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33051) / 10
        if u16(d, 33051) is not None
        else None,
    ),
    Desc(
        key="pv_current_2",
        translation_key="pv_current_2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33052) / 10
        if u16(d, 33052) is not None
        else None,
    ),
    Desc(
        key="pv_power",
        translation_key="pv_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u32(d, 33057, 33058),
    ),
    Desc(
        key="phase_voltage_l1",
        translation_key="phase_voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33073) / 10
        if u16(d, 33073) is not None
        else None,
    ),
    Desc(
        key="phase_voltage_l2",
        translation_key="phase_voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33074) / 10
        if u16(d, 33074) is not None
        else None,
    ),
    Desc(
        key="phase_voltage_l3",
        translation_key="phase_voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33075) / 10
        if u16(d, 33075) is not None
        else None,
    ),
    Desc(
        key="active_power",
        translation_key="active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: s32(d, 33079, 33080),
    ),
    Desc(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: s16(d, 33093) / 10
        if s16(d, 33093) is not None
        else None,
    ),
    Desc(
        key="grid_frequency",
        translation_key="grid_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33094) / 100
        if u16(d, 33094) is not None
        else None,
    ),
    Desc(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33133) / 10
        if u16(d, 33133) is not None
        else None,
    ),
    Desc(
        key="battery_current",
        translation_key="battery_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            (-1 if u16(d, 33135) == 1 else 1) * u16(d, 33134) / 10
            if u16(d, 33134) is not None
            else None
        ),
    ),
    Desc(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33139),
    ),
    Desc(
        key="house_load_power",
        translation_key="house_load_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: u16(d, 33147),
    ),
    Desc(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            (-1 if u16(d, 33135) == 1 else 1) * u32(d, 33149, 33150)
            if u32(d, 33149, 33150) is not None
            else None
        ),
    ),
    Desc(
        key="grid_power",
        translation_key="grid_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: s32(d, 33151, 33152),
    ),
)


SETTINGS = (
    SettingDesc(
        key="setting_battery_model",
        translation_key="setting_battery_model",
        register=43009,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: decode_battery_model(u16(d, 43009)),
    ),
    SettingDesc(
        key="setting_max_charge_soc",
        translation_key="setting_max_charge_soc",
        register=43010,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: u16(d, 43010),
    ),
    SettingDesc(
        key="setting_overdischarge_soc",
        translation_key="setting_overdischarge_soc",
        register=43011,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: u16(d, 43011),
    ),
    SettingDesc(
        key="setting_max_charge_current",
        translation_key="setting_max_charge_current",
        register=43012,
        entity_category=EntityCategory.CONFIG,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: u16(d, 43012) / 10
        if u16(d, 43012) is not None
        else None,
    ),
    SettingDesc(
        key="setting_max_discharge_current",
        translation_key="setting_max_discharge_current",
        register=43013,
        entity_category=EntityCategory.CONFIG,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: u16(d, 43013) / 10
        if u16(d, 43013) is not None
        else None,
    ),
    SettingDesc(
        key="setting_force_charge_soc",
        translation_key="setting_force_charge_soc",
        register=43018,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: u16(d, 43018),
    ),
    SettingDesc(
        key="setting_backup_soc",
        translation_key="setting_backup_soc",
        register=43024,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: u16(d, 43024),
    ),
    SettingDesc(
        key="setting_storage_mode",
        translation_key="setting_storage_mode",
        register=43110,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: decode_storage_mode(u16(d, 43110)),
        attrs_fn=storage_mode_attributes,
    ),
    SettingDesc(
        key="setting_battery_max_charge_current",
        translation_key="setting_battery_max_charge_current",
        register=43117,
        entity_category=EntityCategory.CONFIG,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: u16(d, 43117) / 10
        if u16(d, 43117) is not None
        else None,
    ),
    SettingDesc(
        key="setting_battery_max_discharge_current",
        translation_key="setting_battery_max_discharge_current",
        register=43118,
        entity_category=EntityCategory.CONFIG,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: u16(d, 43118) / 10
        if u16(d, 43118) is not None
        else None,
    ),
)


METRICS = {
    "response_time": SensorEntityDescription(
        key="response_time",
        translation_key="response_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "read_time": SensorEntityDescription(
        key="read_time",
        translation_key="read_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "connect_time": SensorEntityDescription(
        key="connect_time",
        translation_key="connect_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "average_poll_time": SensorEntityDescription(
        key="average_poll_time",
        translation_key="average_poll_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "min_poll_time": SensorEntityDescription(
        key="min_poll_time",
        translation_key="min_poll_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "max_poll_time": SensorEntityDescription(
        key="max_poll_time",
        translation_key="max_poll_time",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "success_rate": SensorEntityDescription(
        key="success_rate",
        translation_key="success_rate",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "failed_polls": SensorEntityDescription(
        key="failed_polls",
        translation_key="failed_polls",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "total_retries": SensorEntityDescription(
        key="total_retries",
        translation_key="total_retries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "reconnect_count": SensorEntityDescription(
        key="reconnect_count",
        translation_key="reconnect_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "disconnect_count": SensorEntityDescription(
        key="disconnect_count",
        translation_key="disconnect_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "consecutive_failures": SensorEntityDescription(
        key="consecutive_failures",
        translation_key="consecutive_failures",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "last_success": SensorEntityDescription(
        key="last_success",
        translation_key="last_success",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "connected_since": SensorEntityDescription(
        key="connected_since",
        translation_key="connected_since",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "connection_uptime": SensorEntityDescription(
        key="connection_uptime",
        translation_key="connection_uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "longest_connection": SensorEntityDescription(
        key="longest_connection",
        translation_key="longest_connection",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "last_disconnect": SensorEntityDescription(
        key="last_disconnect",
        translation_key="last_disconnect",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "last_reconnect": SensorEntityDescription(
        key="last_reconnect",
        translation_key="last_reconnect",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "total_downtime": SensorEntityDescription(
        key="total_downtime",
        translation_key="total_downtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "availability": SensorEntityDescription(
        key="availability",
        translation_key="availability",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "health_score": SensorEntityDescription(
        key="health_score",
        translation_key="health_score",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = [RegisterSensor(coordinator, entry, desc) for desc in SENSORS]
    entities.extend(
        SettingSensor(coordinator, entry, desc) for desc in SETTINGS
    )
    entities.extend(
        MetricSensor(coordinator, entry, key) for key in METRICS
    )
    entities.extend(
        [
            CountSensor(coordinator, entry),
            ClockSensor(coordinator, entry),
        ]
    )
    async_add_entities(entities)


class Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, desc):
        super().__init__(coordinator)
        self.entity_description = desc
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )


class RegisterSensor(Base):
    @property
    def native_value(self):
        return self.entity_description.value_fn(
            self.coordinator.data or {}
        )


class SettingSensor(Base):
    """Read-only view of a selected holding-register setting."""

    entity_description: SettingDesc

    @property
    def native_value(self):
        return self.entity_description.value_fn(
            self.coordinator.settings_data or {}
        )

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.entity_description.register
            in self.coordinator.settings_data
        )

    @property
    def extra_state_attributes(self):
        if self.entity_description.attrs_fn is None:
            return None
        raw = self.coordinator.settings_data.get(
            self.entity_description.register
        )
        return self.entity_description.attrs_fn(raw)


class MetricSensor(Base):
    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator, entry, METRICS[key])

    @property
    def native_value(self):
        health = self.coordinator.network_health
        values = {
            "response_time": health["last_response_ms"],
            "read_time": health["last_read_ms"],
            "connect_time": health["last_connect_ms"],
            "average_poll_time": health["average_poll_ms"],
            "min_poll_time": health["min_poll_ms"],
            "max_poll_time": health["max_poll_ms"],
            "success_rate": health["success_rate"],
            "failed_polls": health["failed_polls"],
            "total_retries": health["total_retries"],
            "reconnect_count": health["reconnect_count"],
            "disconnect_count": health["disconnect_count"],
            "consecutive_failures": health["consecutive_failures"],
            "last_success": health["last_success_at"],
            "connected_since": health["connected_since"],
            "connection_uptime": health[
                "current_connection_uptime_seconds"
            ],
            "longest_connection": health["longest_connection_seconds"],
            "last_disconnect": health["last_disconnect_at"],
            "last_reconnect": health["last_reconnect_at"],
            "total_downtime": health["total_downtime_seconds"],
            "availability": health["availability_percent"],
            "health_score": health["health_score"],
        }
        return values[self.entity_description.key]


class CountSensor(Base):
    def __init__(self, coordinator, entry):
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key="register_count",
                translation_key="register_count",
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        )

    @property
    def native_value(self):
        return len(self.coordinator.data or {})


class ClockSensor(Base):
    def __init__(self, coordinator, entry):
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key="device_time",
                translation_key="device_time",
                device_class=SensorDeviceClass.TIMESTAMP,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        )

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            return datetime(
                2000 + data[33022],
                data[33023],
                data[33024],
                data[33025],
                data[33026],
                data[33027],
                tzinfo=dt_util.DEFAULT_TIME_ZONE,
            )
        except (KeyError, ValueError, TypeError):
            return None
