"""Read-only inverter setting definitions and decoders."""

from __future__ import annotations

from typing import Any, Final

# Initial read-only settings set for v0.4.0.
#
# These are Solis hybrid holding registers used by the S2.LH-MII platform.
# v0.4.x deliberately reads them only; no Modbus write function exists.
SETTING_REGISTER_ADDRESSES: Final[tuple[int, ...]] = (
    43009,  # Battery model
    43010,  # Max charge SOC
    43011,  # Overdischarge SOC
    43012,  # Max charge current
    43013,  # Max discharge current
    43018,  # Force charge SOC
    43024,  # Backup SOC
    43110,  # Storage mode / modifiers
    43117,  # Battery max charge current
    43118,  # Battery max discharge current
)

# Register 43009 values for HV batteries. Unknown values are kept visible
# as hexadecimal so new battery models can be identified safely.
HV_BATTERY_MODELS: Final[dict[int, str]] = {
    0x0000: "No battery",
    0x0100: "PYLON_HV",
    0x0200: "User define",
    0x0300: "B_BOX_HV BYD",
    0x0400: "LG_HV",
    0x0500: "SOLUNA_HV",
    0x0600: "Dyness HV",
    0x0700: "Aoboet HV",
    0x0800: "WECO HV",
    0x0900: "Alpha HV",
    0x0A00: "GS Energy",
    0x0B00: "BYD-HVS/HVM/HVL",
    0x0C00: "Jinko",
    0x0D00: "FOX",
    0x0E00: "LG_16H",
    0x0F00: "PureDrive",
    0x1000: "UZ ENERGY",
    0x1200: "Lotus",
    0x1300: "Fortress",
    0x1400: "AMPACE_HV",
    0x1500: "WTS",
    0x1600: "J-PACK-HV",
    0x1700: "SUNWODA HV",
    0x2600: "LG Enblock S",
    0x6300: "General-LiBat-HV",
}


def decode_battery_model(value: int | None) -> str | None:
    """Return a human-readable HV battery model."""
    if value is None:
        return None
    return HV_BATTERY_MODELS.get(value, f"Unknown (0x{value:04X})")


def decode_storage_mode(value: int | None) -> str | None:
    """Decode the mode-defining bits of holding register 43110."""
    if value is None:
        return None

    tou = bool(value & (1 << 1))
    if value & (1 << 11):
        return "Peak Shaving"
    if value & (1 << 2):
        return "Off-Grid Operation"
    if (value & (1 << 4)) and (value & (1 << 0)):
        return "Reserve / Backup + TOU" if tou else "Reserve / Backup"
    if value & (1 << 6):
        return "Feed-in Priority + TOU" if tou else "Feed-in Priority"
    if value & (1 << 0):
        return "Self-Use + TOU" if tou else "Self-Use"
    return f"Unknown ({value})"


def storage_mode_attributes(value: int | None) -> dict[str, Any]:
    """Expose independent 43110 modifiers without creating extra entities."""
    if value is None:
        return {}
    return {
        "raw_value": value,
        "time_of_use": bool(value & (1 << 1)),
        "battery_wakeup": bool(value & (1 << 3)),
        "reserve_battery_mode": bool(value & (1 << 4)),
        "grid_charge_allowed": bool(value & (1 << 5)),
        "battery_ovc": bool(value & (1 << 7)),
        "battery_forcecharge_peakshaving": bool(value & (1 << 8)),
        "battery_current_correction": bool(value & (1 << 9)),
        "battery_healing_mode": bool(value & (1 << 10)),
    }
