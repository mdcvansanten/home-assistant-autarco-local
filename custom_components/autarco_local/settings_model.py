"""Vendor-neutral energy-setting concepts used by Autarco Local.

This module deliberately contains no Modbus register addresses.  It describes
what a setting *means*, where it belongs in the UI and how far read/write
validation has progressed.  The Autarco/Solis adapter in ``settings.py`` remains
responsible for the actual hardware mapping.

A generic concept never grants write permission by itself.  Writes are enabled
only by an explicit hardware-specific transaction implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

SECTION_CORE = "core"
SECTION_SCHEDULES = "schedules"
SECTION_INSTALLER = "installer"

READ_CONFIRMED = "hardware_confirmed"
READ_DOCUMENTED = "documented"
READ_SUSPECT = "suspect"

WRITE_CONFIRMED = "hardware_confirmed"
WRITE_TEST_CANDIDATE = "test_candidate"
WRITE_PENDING = "pending_validation"
WRITE_BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class GenericSettingMeta:
    """Describe the vendor-neutral meaning and validation state of a setting."""

    concept: str
    section: str
    read_validation: str
    write_validation: str
    note: str = ""


GENERIC_SETTING_META: dict[str, GenericSettingMeta] = {
    "setting_overcharge_soc": GenericSettingMeta(
        "battery.maximum_soc",
        SECTION_INSTALLER,
        READ_CONFIRMED,
        WRITE_BLOCKED,
        "Battery protection ceiling; installer/system controlled.",
    ),
    "setting_overdischarge_soc": GenericSettingMeta(
        "battery.minimum_soc",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_TEST_CANDIDATE,
        "Normal grid-connected discharge floor; operational impact requires a guarded test.",
    ),
    "setting_force_charge_soc": GenericSettingMeta(
        "battery.force_charge_soc",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Coupled to grid charging and low-SOC recovery behaviour.",
    ),
    "setting_reserve_soc": GenericSettingMeta(
        "battery.reserve_soc",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_TEST_CANDIDATE,
        "Preferred next low-impact write test while reserve mode is inactive.",
    ),
    "setting_force_charge_power_limit": GenericSettingMeta(
        "battery.force_charge_power_limit",
        SECTION_CORE,
        READ_SUSPECT,
        WRITE_BLOCKED,
        "Displayed scaling does not yet match the official local installer value.",
    ),
    "setting_self_use_mode": GenericSettingMeta(
        "mode.self_use",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Part of the shared work-mode state; never treat as an isolated bit write.",
    ),
    "setting_time_of_use_mode": GenericSettingMeta(
        "schedule.enabled",
        SECTION_SCHEDULES,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Parent mode for scheduled charge/discharge windows.",
    ),
    "setting_off_grid_mode": GenericSettingMeta(
        "mode.off_grid",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_BLOCKED,
        "Validated as a temporary transaction dependency, not as a free-standing user toggle.",
    ),
    "setting_reserve_battery_mode": GenericSettingMeta(
        "mode.battery_reserve",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Parent mode for Reserve SOC.",
    ),
    "setting_allow_grid_charge": GenericSettingMeta(
        "grid.allow_battery_charging",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Coupled to force-charge, reserve and scheduled charging behaviour.",
    ),
    "setting_feed_in_priority_mode": GenericSettingMeta(
        "mode.feed_in_priority",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_PENDING,
        "Part of the shared work-mode state.",
    ),
    "setting_off_grid_overdischarge_soc": GenericSettingMeta(
        "battery.off_grid_minimum_soc",
        SECTION_CORE,
        READ_CONFIRMED,
        WRITE_CONFIRMED,
        "Register 43137 and the temporary Off-grid dependency are hardware validated.",
    ),
    "setting_time_charge_current": GenericSettingMeta(
        "schedule.charge_current_limit",
        SECTION_SCHEDULES,
        READ_DOCUMENTED,
        WRITE_PENDING,
        "Effective only with Time-of-use enabled.",
    ),
    "setting_time_discharge_current": GenericSettingMeta(
        "schedule.discharge_current_limit",
        SECTION_SCHEDULES,
        READ_DOCUMENTED,
        WRITE_PENDING,
        "Effective only with Time-of-use enabled.",
    ),
}


for slot in (1, 2, 3):
    for direction in ("charge", "discharge"):
        for edge in ("start", "end"):
            GENERIC_SETTING_META[f"setting_{direction}_{edge}_{slot}"] = GenericSettingMeta(
                f"schedule.{direction}.{slot}.{edge}",
                SECTION_SCHEDULES,
                READ_DOCUMENTED,
                WRITE_PENDING,
                "Time window register pair; write behaviour still needs hardware validation.",
            )


def setting_meta(key: str) -> GenericSettingMeta | None:
    """Return generic metadata for one hardware-specific setting key."""
    return GENERIC_SETTING_META.get(key)
