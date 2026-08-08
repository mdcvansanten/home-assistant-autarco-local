"""Read-only inverter setting definitions for Autarco Local."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfPower,
)

ACCESS_STANDARD = "standard"
ACCESS_EXPERT = "expert"
ACCESS_INSTALLER = "installer"
WRITE_POLICY_READ_ONLY = "read_only"


def u16(data: dict[int, int], address: int):
    return data.get(address)


def scaled(data: dict[int, int], address: int, factor: float):
    value = u16(data, address)
    return None if value is None else round(value * factor, 3)


def bit_state(data: dict[int, int], address: int, bit: int):
    value = u16(data, address)
    if value is None:
        return None
    return "On" if value & (1 << bit) else "Off"


def hhmm(data: dict[int, int], hour_register: int, minute_register: int):
    hour = u16(data, hour_register)
    minute = u16(data, minute_register)
    if hour is None or minute is None:
        return None
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return f"raw:{hour}/{minute}"
    return f"{hour:02d}:{minute:02d}"


@dataclass(frozen=True, kw_only=True)
class SettingDesc(SensorEntityDescription):
    """Describe a read-only inverter setting."""

    registers: tuple[int, ...]
    value_fn: Callable[[dict[int, int]], object]
    access_level: str


def setting(
    key: str,
    registers: tuple[int, ...],
    value_fn: Callable[[dict[int, int]], object],
    access_level: str,
    *,
    device_class=None,
    unit=None,
    enabled: bool = True,
):
    return SettingDesc(
        key=key,
        translation_key=key,
        registers=registers,
        value_fn=value_fn,
        access_level=access_level,
        device_class=device_class,
        native_unit_of_measurement=unit,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=enabled,
    )


SETTINGS = (
    # Battery SOC limits.
    setting(
        "setting_overcharge_soc",
        (43010,),
        lambda x: u16(x, 43010),
        ACCESS_INSTALLER,
        unit=PERCENTAGE,
    ),
    setting(
        "setting_overdischarge_soc",
        (43011,),
        lambda x: u16(x, 43011),
        ACCESS_EXPERT,
        unit=PERCENTAGE,
    ),
    setting(
        "setting_force_charge_soc",
        (43018,),
        lambda x: u16(x, 43018),
        ACCESS_EXPERT,
        unit=PERCENTAGE,
    ),
    setting(
        "setting_reserve_soc",
        (43024,),
        lambda x: u16(x, 43024),
        ACCESS_STANDARD,
        unit=PERCENTAGE,
    ),
    setting(
        "setting_force_charge_power_limit",
        (43027,),
        lambda x: u16(x, 43027),
        ACCESS_EXPERT,
        device_class=SensorDeviceClass.POWER,
        unit=UnitOfPower.WATT,
    ),

    # Storage mode bit field (holding register 43110).
    setting(
        "setting_self_use_mode",
        (43110,),
        lambda x: bit_state(x, 43110, 0),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_time_of_use_mode",
        (43110,),
        lambda x: bit_state(x, 43110, 1),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_off_grid_mode",
        (43110,),
        lambda x: bit_state(x, 43110, 2),
        ACCESS_EXPERT,
    ),
    setting(
        "setting_reserve_battery_mode",
        (43110,),
        lambda x: bit_state(x, 43110, 4),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_allow_grid_charge",
        (43110,),
        lambda x: bit_state(x, 43110, 5),
        ACCESS_EXPERT,
    ),
    setting(
        "setting_feed_in_priority_mode",
        (43110,),
        lambda x: bit_state(x, 43110, 6),
        ACCESS_STANDARD,
    ),

    # Expert battery/current settings.
    setting(
        "setting_off_grid_overdischarge_soc",
        (43137,),
        lambda x: u16(x, 43137),
        ACCESS_EXPERT,
        unit=PERCENTAGE,
    ),
    setting(
        "setting_time_charge_current",
        (43141,),
        lambda x: scaled(x, 43141, 0.1),
        ACCESS_EXPERT,
        device_class=SensorDeviceClass.CURRENT,
        unit=UnitOfElectricCurrent.AMPERE,
    ),
    setting(
        "setting_time_discharge_current",
        (43142,),
        lambda x: scaled(x, 43142, 0.1),
        ACCESS_EXPERT,
        device_class=SensorDeviceClass.CURRENT,
        unit=UnitOfElectricCurrent.AMPERE,
    ),

    # Autarco exposes three charge/discharge time slots in the Installer UI.
    setting(
        "setting_charge_start_1",
        (43143, 43144),
        lambda x: hhmm(x, 43143, 43144),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_charge_end_1",
        (43145, 43146),
        lambda x: hhmm(x, 43145, 43146),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_start_1",
        (43147, 43148),
        lambda x: hhmm(x, 43147, 43148),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_end_1",
        (43149, 43150),
        lambda x: hhmm(x, 43149, 43150),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_charge_start_2",
        (43153, 43154),
        lambda x: hhmm(x, 43153, 43154),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_charge_end_2",
        (43155, 43156),
        lambda x: hhmm(x, 43155, 43156),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_start_2",
        (43157, 43158),
        lambda x: hhmm(x, 43157, 43158),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_end_2",
        (43159, 43160),
        lambda x: hhmm(x, 43159, 43160),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_charge_start_3",
        (43163, 43164),
        lambda x: hhmm(x, 43163, 43164),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_charge_end_3",
        (43165, 43166),
        lambda x: hhmm(x, 43165, 43166),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_start_3",
        (43167, 43168),
        lambda x: hhmm(x, 43167, 43168),
        ACCESS_STANDARD,
    ),
    setting(
        "setting_discharge_end_3",
        (43169, 43170),
        lambda x: hhmm(x, 43169, 43170),
        ACCESS_STANDARD,
    ),
)
