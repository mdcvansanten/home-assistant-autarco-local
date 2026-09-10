"""Diagnostics support for Autarco Local."""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data

from .connection_monitoring import snapshot as connection_monitor_snapshot
from .device_profile import AUTARCO_LH_MII_PROFILE
from .energy_logic import configuration_health, evaluate_scenarios, normalized_settings
from .soc_monitoring import snapshot as soc_monitor_snapshot
from .write_readiness import readiness_summary

TO_REDACT = {"host"}


async def async_get_config_entry_diagnostics(hass, entry):
    """Return communication, device-profile and configuration diagnostics."""
    coordinator = entry.runtime_data
    runtime_registers = coordinator.data or {}
    setting_registers = coordinator.settings_data or {}
    return {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "last_exception": (
            str(coordinator.last_exception) if coordinator.last_exception else None
        ),
        "network_health": coordinator.network_health,
        "deep_connection_monitor": connection_monitor_snapshot(coordinator),
        "soc_jump_drop_monitor": soc_monitor_snapshot(coordinator),
        "polling": {
            "strategy": getattr(
                coordinator.client, "last_runtime_poll_strategy", "legacy_full_range"
            ),
            "last_request_count": getattr(
                coordinator.client, "last_runtime_request_count", None
            ),
            "current_group": getattr(coordinator.client, "current_runtime_group", None),
            "last_failed_group": getattr(
                coordinator.client, "last_runtime_failed_group", None
            ),
            "fallback_groups": list(
                getattr(coordinator.client, "last_runtime_fallback_groups", ())
            ),
        },
        "device_profile": AUTARCO_LH_MII_PROFILE.as_dict(),
        "configuration": {
            "normalized_settings": normalized_settings(setting_registers),
            "health": configuration_health(setting_registers),
            "scenarios": evaluate_scenarios(setting_registers),
        },
        "write_readiness": readiness_summary(),
        "runtime_register_count": len(runtime_registers),
        "runtime_registers": {
            str(key): value for key, value in sorted(runtime_registers.items())
        },
        "setting_register_count": len(setting_registers),
        "setting_registers": {
            str(key): value for key, value in sorted(setting_registers.items())
        },
    }
