"""Autarco device profile and Solis-compatible register grouping metadata.

The profile separates physical transport from device knowledge. It is intentionally
small in v0.7.0: the existing proven poller remains authoritative while these groups
provide the basis for future multi-cadence polling and an SNS EMS device adapter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final


@dataclass(frozen=True, slots=True)
class RegisterGroup:
    """One coherent group of registers that can be polled together."""

    key: str
    register_type: str
    start: int
    count: int
    cadence: str
    purpose: str
    validated: bool = True

    @property
    def end(self) -> int:
        return self.start + self.count - 1

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["end"] = self.end
        return data


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Known device-family capabilities for one Autarco inverter line."""

    key: str
    manufacturer: str
    model_family: str
    protocol_family: str
    register_reference: str
    runtime_groups: tuple[RegisterGroup, ...]
    setting_groups: tuple[RegisterGroup, ...]
    supports_scenario_model: bool = True
    supports_verified_off_grid_soc_write: bool = True
    supports_generic_scenario_write: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "manufacturer": self.manufacturer,
            "model_family": self.model_family,
            "protocol_family": self.protocol_family,
            "register_reference": self.register_reference,
            "supports_scenario_model": self.supports_scenario_model,
            "supports_verified_off_grid_soc_write": self.supports_verified_off_grid_soc_write,
            "supports_generic_scenario_write": self.supports_generic_scenario_write,
            "runtime_groups": [group.as_dict() for group in self.runtime_groups],
            "setting_groups": [group.as_dict() for group in self.setting_groups],
        }


RUNTIME_GROUPS: Final = (
    RegisterGroup(
        key="clock_energy",
        register_type="input",
        start=33022,
        count=17,
        cadence="slow",
        purpose="Device time and PV energy counters",
    ),
    RegisterGroup(
        key="pv_live",
        register_type="input",
        start=33049,
        count=10,
        cadence="fast",
        purpose="PV/MPPT live values and total PV power",
    ),
    RegisterGroup(
        key="inverter_live",
        register_type="input",
        start=33070,
        count=25,
        cadence="normal",
        purpose="Alarm, AC phase, active power, temperature and frequency",
    ),
    RegisterGroup(
        key="battery_meter_live",
        register_type="input",
        start=33133,
        count=20,
        cadence="fast",
        purpose="Battery, house load and grid power",
    ),
)

SETTING_GROUPS: Final = (
    RegisterGroup("battery_soc_limits", "holding", 43010, 2, "normal", "Battery SOC limits"),
    RegisterGroup("force_charge_soc", "holding", 43018, 1, "normal", "Force-charge threshold"),
    RegisterGroup("reserve_soc", "holding", 43024, 1, "normal", "Reserve SOC"),
    RegisterGroup("force_charge_power", "holding", 43027, 1, "normal", "Force-charge power limit"),
    RegisterGroup("storage_mode", "holding", 43110, 1, "normal", "Storage/work-mode bit field"),
    RegisterGroup("off_grid_soc", "holding", 43137, 1, "normal", "Off-grid minimum SOC"),
    RegisterGroup("tou_slot_1", "holding", 43141, 10, "slow", "TOU currents and slot 1"),
    RegisterGroup("tou_slot_2", "holding", 43153, 8, "slow", "TOU slot 2"),
    RegisterGroup("tou_slot_3", "holding", 43163, 8, "slow", "TOU slot 3"),
)

AUTARCO_LH_MII_PROFILE: Final = DeviceProfile(
    key="autarco_lh_mii_solis_compatible",
    manufacturer="Autarco",
    model_family="S2.LH-MII",
    protocol_family="Solis-compatible Modbus",
    register_reference="Autarco validated registers + Solis Modbus reference patterns",
    runtime_groups=RUNTIME_GROUPS,
    setting_groups=SETTING_GROUPS,
)
