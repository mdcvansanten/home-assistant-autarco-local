"""Controlled write-enablement roadmap for Autarco Local.

A setting is never made writable only because the equivalent Solis register is
known. Every Autarco write moves through explicit qualification stages so the UI,
diagnostics and future EMS can distinguish proven actions from research targets.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final

STATUS_VALIDATED = "hardware_validated"
STATUS_NEXT = "next_hardware_candidate"
STATUS_DEPENDENCY = "dependency_validation_required"
STATUS_MAPPING = "mapping_validation_required"
STATUS_READ_ONLY = "permanent_read_only"


@dataclass(frozen=True, slots=True)
class WriteReadiness:
    key: str
    label: str
    status: str
    risk: str
    prerequisite: str
    register: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


WRITE_READINESS: Final[tuple[WriteReadiness, ...]] = (
    WriteReadiness(
        "off_grid_minimum_soc",
        "Minimum-SOC off-grid",
        STATUS_VALIDATED,
        "expert",
        "Validated temporary Off-grid dependency, read-back, restore and final verify.",
        43137,
    ),
    WriteReadiness(
        "reserve_soc",
        "Reserve SOC",
        STATUS_NEXT,
        "standard",
        "Validate register write/read-back and Battery Reserve dependency without changing unrelated mode bits.",
        43024,
    ),
    WriteReadiness(
        "self_use_mode",
        "Self-use mode",
        STATUS_DEPENDENCY,
        "standard",
        "Validate complete storage-mode bitfield transaction and mutual-exclusion behaviour.",
        43110,
    ),
    WriteReadiness(
        "reserve_battery_mode",
        "Reserve battery mode",
        STATUS_DEPENDENCY,
        "standard",
        "Validate bit transition together with Reserve SOC effect and work-mode preservation.",
        43110,
    ),
    WriteReadiness(
        "time_of_use_mode",
        "Time-of-use mode",
        STATUS_DEPENDENCY,
        "standard",
        "Validate parent mode plus schedule/current read-back and restore behaviour.",
        43110,
    ),
    WriteReadiness(
        "feed_in_priority_mode",
        "Feed-in priority mode",
        STATUS_DEPENDENCY,
        "standard",
        "Validate work-mode exclusivity and complete bitfield snapshot/restore.",
        43110,
    ),
    WriteReadiness(
        "allow_grid_charging",
        "Laden vanuit net toestaan",
        STATUS_DEPENDENCY,
        "expert",
        "Validate interaction with Force-charge, Reserve and Time-of-Use before enabling.",
        43110,
    ),
    WriteReadiness(
        "minimum_battery_soc",
        "Minimum battery SOC",
        STATUS_MAPPING,
        "expert",
        "Confirm exact Autarco semantics and interaction with Force-charge/overdischarge behaviour.",
        43011,
    ),
    WriteReadiness(
        "force_charge_soc",
        "Force-charge SOC",
        STATUS_MAPPING,
        "expert",
        "Confirm safe bounds and net-charge interaction before enabling.",
        43018,
    ),
    WriteReadiness(
        "force_charge_power_limit",
        "Force-charge power limit",
        STATUS_MAPPING,
        "expert",
        "Register scaling and actual effect must be hardware-proven.",
        43027,
    ),
    WriteReadiness(
        "scheduled_charge_current",
        "Geplande laadstroom",
        STATUS_DEPENDENCY,
        "expert",
        "Validate current scaling, BMS limits and Time-of-Use dependency.",
        43141,
    ),
    WriteReadiness(
        "scheduled_discharge_current",
        "Geplande ontlaadstroom",
        STATUS_DEPENDENCY,
        "expert",
        "Validate current scaling, BMS limits and Time-of-Use dependency.",
        43142,
    ),
    WriteReadiness(
        "overcharge_soc",
        "Overcharge SOC",
        STATUS_READ_ONLY,
        "installer",
        "Battery protection setting remains installer/factory controlled.",
        43010,
    ),
)


def readiness_summary() -> dict[str, Any]:
    items = [item.as_dict() for item in WRITE_READINESS]
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "policy": "one_setting_or_transaction_at_a_time",
        "next_candidate": "reserve_soc",
        "items": items,
        "counts": counts,
    }
