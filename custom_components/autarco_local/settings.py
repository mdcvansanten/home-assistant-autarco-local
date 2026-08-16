"""Inverter setting definitions and safety metadata for Autarco Local."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfElectricCurrent, UnitOfPower

ACCESS_STANDARD = "standard"
ACCESS_EXPERT = "expert"
ACCESS_INSTALLER = "installer"

WRITE_POLICY_ALLOWED = "allowed"
WRITE_POLICY_CONFIRM = "confirm"
WRITE_POLICY_READ_ONLY = "read_only"

DEPENDENCY_HARDWARE_VALIDATED = "hardware_validated"
DEPENDENCY_DOCUMENTED = "documented_pending_hardware_validation"

# Physical writes remain guarded/pilot-only. Dependency metadata is deliberately
# separate from write enablement so UI and transaction planning can be built
# without making unvalidated settings writable.
PHYSICAL_WRITES_ENABLED = False

AUTARCO_LH_MII_MANUAL_URL = (
    "https://www.autarco.com/fileadmin/user_upload/downloads/Inverters/"
    "Hybrid_Inverters/LH-MII/IM-S2.LH-MII-EN-V1.4.pdf"
)


class SettingValidationError(ValueError):
    """Raised when a requested setting combination violates a safety rule."""


def validate_soc_relationship(reserve_soc: int | float, minimum_soc: int | float) -> None:
    """Enforce the battery SOC safety relationship."""
    if reserve_soc < minimum_soc:
        raise SettingValidationError(
            "Reserve SOC must be greater than or equal to Minimum battery SOC"
        )


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
class SettingDependency:
    """Describe a parent-mode dependency for a setting write.

    `restore_original_state` does not mean the parent is always turned off after
    a write. It means Autarco Local may restore the pre-write state only when the
    integration itself had to change that state temporarily.
    """

    parent_key: str
    required_state: str
    validation_status: str
    restore_original_state: bool = True
    note: str | None = None


@dataclass(frozen=True, kw_only=True)
class SettingDesc(SensorEntityDescription):
    """Describe a known inverter setting."""

    registers: tuple[int, ...]
    value_fn: Callable[[dict[int, int]], object]
    access_level: str
    planned_write_policy: str
    dependency: SettingDependency | None = None
    documentation_url: str | None = AUTARCO_LH_MII_MANUAL_URL


def setting(
    key: str,
    registers: tuple[int, ...],
    value_fn: Callable[[dict[int, int]], object],
    access_level: str,
    planned_write_policy: str,
    *,
    device_class=None,
    unit=None,
    enabled: bool = True,
    dependency: SettingDependency | None = None,
    documentation_url: str | None = AUTARCO_LH_MII_MANUAL_URL,
):
    return SettingDesc(
        key=key,
        translation_key=key,
        registers=registers,
        value_fn=value_fn,
        access_level=access_level,
        planned_write_policy=planned_write_policy,
        dependency=dependency,
        documentation_url=documentation_url,
        device_class=device_class,
        native_unit_of_measurement=unit,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=enabled,
    )


DEPENDENCY_OFF_GRID_ACTIVE = SettingDependency(
    parent_key="setting_off_grid_mode",
    required_state="On",
    validation_status=DEPENDENCY_HARDWARE_VALIDATED,
    restore_original_state=True,
    note=(
        "Hardware validated: Off-grid minimum SOC is editable only while Off-grid "
        "mode is active. If Off-grid was already active before the write, it must "
        "remain active afterwards."
    ),
)

DEPENDENCY_TIME_OF_USE_ACTIVE = SettingDependency(
    parent_key="setting_time_of_use_mode",
    required_state="On",
    validation_status=DEPENDENCY_DOCUMENTED,
    restore_original_state=True,
    note=(
        "Solis documents scheduled currents/times as effective only when Time of "
        "Use is enabled. Automatic temporary toggling is blocked until hardware "
        "write behaviour is validated."
    ),
)

DEPENDENCY_RESERVE_ACTIVE = SettingDependency(
    parent_key="setting_reserve_battery_mode",
    required_state="On",
    validation_status=DEPENDENCY_DOCUMENTED,
    restore_original_state=True,
    note=(
        "Reserve SOC belongs to Battery Reserve mode. Automatic temporary toggling "
        "is blocked until local Autarco hardware behaviour is validated."
    ),
)


SETTINGS = (
    setting("setting_overcharge_soc", (43010,), lambda x: u16(x, 43010), ACCESS_INSTALLER, WRITE_POLICY_READ_ONLY, unit=PERCENTAGE),
    setting("setting_overdischarge_soc", (43011,), lambda x: u16(x, 43011), ACCESS_EXPERT, WRITE_POLICY_CONFIRM, unit=PERCENTAGE),
    setting("setting_force_charge_soc", (43018,), lambda x: u16(x, 43018), ACCESS_EXPERT, WRITE_POLICY_CONFIRM, unit=PERCENTAGE),
    setting(
        "setting_reserve_soc",
        (43024,),
        lambda x: u16(x, 43024),
        ACCESS_STANDARD,
        WRITE_POLICY_ALLOWED,
        unit=PERCENTAGE,
        dependency=DEPENDENCY_RESERVE_ACTIVE,
    ),
    setting(
        "setting_force_charge_power_limit",
        (43027,),
        lambda x: u16(x, 43027),
        ACCESS_EXPERT,
        WRITE_POLICY_CONFIRM,
        device_class=SensorDeviceClass.POWER,
        unit=UnitOfPower.WATT,
    ),
    setting("setting_self_use_mode", (43110,), lambda x: bit_state(x, 43110, 0), ACCESS_STANDARD, WRITE_POLICY_ALLOWED),
    setting("setting_time_of_use_mode", (43110,), lambda x: bit_state(x, 43110, 1), ACCESS_STANDARD, WRITE_POLICY_ALLOWED),
    setting("setting_off_grid_mode", (43110,), lambda x: bit_state(x, 43110, 2), ACCESS_EXPERT, WRITE_POLICY_CONFIRM),
    setting("setting_reserve_battery_mode", (43110,), lambda x: bit_state(x, 43110, 4), ACCESS_STANDARD, WRITE_POLICY_ALLOWED),
    setting("setting_allow_grid_charge", (43110,), lambda x: bit_state(x, 43110, 5), ACCESS_EXPERT, WRITE_POLICY_CONFIRM),
    setting("setting_feed_in_priority_mode", (43110,), lambda x: bit_state(x, 43110, 6), ACCESS_STANDARD, WRITE_POLICY_ALLOWED),
    setting(
        "setting_off_grid_overdischarge_soc",
        (43137,),
        lambda x: u16(x, 43137),
        ACCESS_EXPERT,
        WRITE_POLICY_CONFIRM,
        unit=PERCENTAGE,
        dependency=DEPENDENCY_OFF_GRID_ACTIVE,
    ),
    setting(
        "setting_time_charge_current",
        (43141,),
        lambda x: scaled(x, 43141, 0.1),
        ACCESS_EXPERT,
        WRITE_POLICY_CONFIRM,
        device_class=SensorDeviceClass.CURRENT,
        unit=UnitOfElectricCurrent.AMPERE,
        dependency=DEPENDENCY_TIME_OF_USE_ACTIVE,
    ),
    setting(
        "setting_time_discharge_current",
        (43142,),
        lambda x: scaled(x, 43142, 0.1),
        ACCESS_EXPERT,
        WRITE_POLICY_CONFIRM,
        device_class=SensorDeviceClass.CURRENT,
        unit=UnitOfElectricCurrent.AMPERE,
        dependency=DEPENDENCY_TIME_OF_USE_ACTIVE,
    ),
    setting("setting_charge_start_1", (43143, 43144), lambda x: hhmm(x, 43143, 43144), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_charge_end_1", (43145, 43146), lambda x: hhmm(x, 43145, 43146), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_start_1", (43147, 43148), lambda x: hhmm(x, 43147, 43148), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_end_1", (43149, 43150), lambda x: hhmm(x, 43149, 43150), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_charge_start_2", (43153, 43154), lambda x: hhmm(x, 43153, 43154), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_charge_end_2", (43155, 43156), lambda x: hhmm(x, 43155, 43156), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_start_2", (43157, 43158), lambda x: hhmm(x, 43157, 43158), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_end_2", (43159, 43160), lambda x: hhmm(x, 43159, 43160), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_charge_start_3", (43163, 43164), lambda x: hhmm(x, 43163, 43164), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_charge_end_3", (43165, 43166), lambda x: hhmm(x, 43165, 43166), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_start_3", (43167, 43168), lambda x: hhmm(x, 43167, 43168), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
    setting("setting_discharge_end_3", (43169, 43170), lambda x: hhmm(x, 43169, 43170), ACCESS_STANDARD, WRITE_POLICY_ALLOWED, dependency=DEPENDENCY_TIME_OF_USE_ACTIVE),
)

SETTINGS_BY_KEY = {description.key: description for description in SETTINGS}

# Known storage/work modes share register 43110. Solis documents some of these
# modes as mutually exclusive. Future writes must therefore snapshot the complete
# relevant mode state, not assume each bit is independent.
MUTUALLY_EXCLUSIVE_STORAGE_MODES = (
    "setting_self_use_mode",
    "setting_feed_in_priority_mode",
    "setting_off_grid_mode",
)

# Installer/system settings that should remain visible in the Settings Center
# even though their exact register mapping is not yet validated.
UNMAPPED_INSTALLER_SETTINGS = (
    "installer_grid_standard",
    "installer_grid_voltage_limits",
    "installer_grid_frequency_limits",
    "installer_anti_islanding",
    "installer_meter_type",
    "installer_meter_function",
    "installer_ct_direction",
    "installer_battery_select",
    "installer_battery_communication",
    "installer_battery_parameters",
    "installer_modbus_address",
    "installer_factory_calibration",
    "installer_firmware_parameters",
)
