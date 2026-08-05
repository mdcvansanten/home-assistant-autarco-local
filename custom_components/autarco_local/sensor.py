"""Sensors for Autarco Local."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

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
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN


def u16(data, address):
    return data.get(address)


def s16(data, address):
    value = data.get(address)
    return None if value is None else (value - 65536 if value >= 32768 else value)


def u32(data, high, low):
    return None if high not in data or low not in data else (data[high] << 16) | data[low]


def s32(data, high, low):
    value = u32(data, high, low)
    return None if value is None else (value - 4294967296 if value >= 2147483648 else value)


def scaled(data, address, factor):
    value = u16(data, address)
    return None if value is None else value * factor


def pv_power(data, voltage_register, current_register):
    voltage = scaled(data, voltage_register, 0.1)
    current = scaled(data, current_register, 0.1)
    return None if voltage is None or current is None else round(voltage * current, 1)


@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription):
    value_fn: Callable


def d(
    key,
    value_fn,
    device_class=None,
    unit=None,
    state_class=SensorStateClass.MEASUREMENT,
    *,
    enabled=True,
    category=None,
):
    return Desc(
        key=key,
        translation_key=key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=state_class,
        entity_registry_enabled_default=enabled,
        entity_category=category,
        value_fn=value_fn,
    )


SENSORS = (
    # PV / MPPT
    d("pv_voltage_1", lambda x: scaled(x, 33049, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d("pv_current_1", lambda x: scaled(x, 33050, 0.1), SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE),
    d("pv_power_1", lambda x: pv_power(x, 33049, 33050), SensorDeviceClass.POWER, UnitOfPower.WATT),
    d("pv_voltage_2", lambda x: scaled(x, 33051, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d("pv_current_2", lambda x: scaled(x, 33052, 0.1), SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE),
    d("pv_power_2", lambda x: pv_power(x, 33051, 33052), SensorDeviceClass.POWER, UnitOfPower.WATT),
    d("pv_voltage_3", lambda x: scaled(x, 33053, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, enabled=False),
    d("pv_current_3", lambda x: scaled(x, 33054, 0.1), SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE, enabled=False),
    d("pv_power_3", lambda x: pv_power(x, 33053, 33054), SensorDeviceClass.POWER, UnitOfPower.WATT, enabled=False),
    d("pv_voltage_4", lambda x: scaled(x, 33055, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, enabled=False),
    d("pv_current_4", lambda x: scaled(x, 33056, 0.1), SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE, enabled=False),
    d("pv_power_4", lambda x: pv_power(x, 33055, 33056), SensorDeviceClass.POWER, UnitOfPower.WATT, enabled=False),
    d("pv_power", lambda x: u32(x, 33057, 33058), SensorDeviceClass.POWER, UnitOfPower.WATT),
    d("pv_energy_total", lambda x: u32(x, 33029, 33030), SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    d("pv_energy_month", lambda x: u32(x, 33031, 33032), SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    d("pv_energy_today", lambda x: scaled(x, 33035, 0.1), SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    d("pv_energy_year", lambda x: u32(x, 33037, 33038), SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    d("pv_alarm_code", lambda x: u16(x, 33070), enabled=False, category=EntityCategory.DIAGNOSTIC),
    d("pv_bus_voltage", lambda x: scaled(x, 33071, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, enabled=False, category=EntityCategory.DIAGNOSTIC),

    # Existing inverter / battery monitoring
    d("phase_voltage_l1", lambda x: scaled(x, 33073, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d("phase_voltage_l2", lambda x: scaled(x, 33074, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d("phase_voltage_l3", lambda x: scaled(x, 33075, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d("active_power", lambda x: s32(x, 33079, 33080), SensorDeviceClass.POWER, UnitOfPower.WATT),
    d("temperature", lambda x: None if s16(x, 33093) is None else s16(x, 33093) / 10, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    d("grid_frequency", lambda x: None if u16(x, 33094) is None else u16(x, 33094) / 100, SensorDeviceClass.FREQUENCY, UnitOfFrequency.HERTZ),
    d("battery_voltage", lambda x: scaled(x, 33133, 0.1), SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    d(
        "battery_current",
        lambda x: ((-1 if u16(x, 33135) == 1 else 1) * u16(x, 33134) / 10) if u16(x, 33134) is not None else None,
        SensorDeviceClass.CURRENT,
        UnitOfElectricCurrent.AMPERE,
    ),
    d("battery_soc", lambda x: u16(x, 33139), SensorDeviceClass.BATTERY, PERCENTAGE),
    d("house_load_power", lambda x: u16(x, 33147), SensorDeviceClass.POWER, UnitOfPower.WATT),
    d(
        "battery_power",
        lambda x: ((-1 if u16(x, 33135) == 1 else 1) * u32(x, 33149, 33150)) if u32(x, 33149, 33150) is not None else None,
        SensorDeviceClass.POWER,
        UnitOfPower.WATT,
    ),
    d("grid_power", lambda x: s32(x, 33151, 33152), SensorDeviceClass.POWER, UnitOfPower.WATT),
)


METRICS = {
    "response_time": ("last_response_ms", "ms", None, True, SensorStateClass.MEASUREMENT),
    "read_time": ("last_read_ms", "ms", None, False, SensorStateClass.MEASUREMENT),
    "connect_time": ("last_connect_ms", "ms", None, False, SensorStateClass.MEASUREMENT),
    "average_poll_time": ("average_poll_ms", "ms", None, False, SensorStateClass.MEASUREMENT),
    "min_poll_time": ("min_poll_ms", "ms", None, False, SensorStateClass.MEASUREMENT),
    "max_poll_time": ("max_poll_ms", "ms", None, False, SensorStateClass.MEASUREMENT),
    "success_rate": ("success_rate", PERCENTAGE, None, True, SensorStateClass.MEASUREMENT),
    "failed_polls": ("failed_polls", None, None, False, SensorStateClass.TOTAL_INCREASING),
    "total_retries": ("total_retries", None, None, False, SensorStateClass.TOTAL_INCREASING),
    "reconnect_count": ("reconnect_count", None, None, False, SensorStateClass.TOTAL_INCREASING),
    "disconnect_count": ("disconnect_count", None, None, True, SensorStateClass.TOTAL_INCREASING),
    "consecutive_failures": ("consecutive_failures", None, None, False, SensorStateClass.MEASUREMENT),
    "last_success": ("last_success_at", None, SensorDeviceClass.TIMESTAMP, True, None),
    "connected_since": ("connected_since", None, SensorDeviceClass.TIMESTAMP, True, None),
    "connection_uptime": ("current_connection_uptime_seconds", UnitOfTime.SECONDS, SensorDeviceClass.DURATION, True, SensorStateClass.MEASUREMENT),
    "longest_connection": ("longest_connection_seconds", UnitOfTime.SECONDS, SensorDeviceClass.DURATION, False, SensorStateClass.MEASUREMENT),
    "last_disconnect": ("last_disconnect_at", None, SensorDeviceClass.TIMESTAMP, True, None),
    "last_reconnect": ("last_reconnect_at", None, SensorDeviceClass.TIMESTAMP, True, None),
    "total_downtime": ("total_downtime_seconds", UnitOfTime.SECONDS, SensorDeviceClass.DURATION, True, SensorStateClass.MEASUREMENT),
    "availability": ("availability_percent", PERCENTAGE, None, True, SensorStateClass.MEASUREMENT),
    "health_score": ("health_score", PERCENTAGE, None, False, SensorStateClass.MEASUREMENT),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(
        [RegisterSensor(coordinator, entry, desc) for desc in SENSORS]
        + [MetricSensor(coordinator, entry, key) for key in METRICS]
        + [CountSensor(coordinator, entry), ClockSensor(coordinator, entry)]
    )


class Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )


class RegisterSensor(Base):
    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})


class MetricSensor(Base):
    def __init__(self, coordinator, entry, key):
        source, unit, device_class, enabled, state_class = METRICS[key]
        self._source_key = source
        super().__init__(
            coordinator,
            entry,
            SensorEntityDescription(
                key=key,
                translation_key=key,
                native_unit_of_measurement=unit,
                device_class=device_class,
                state_class=state_class,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=enabled,
            ),
        )

    @property
    def native_value(self):
        return self.coordinator.network_health[self._source_key]


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
