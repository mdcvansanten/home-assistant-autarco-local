"""Diagnostics support."""

from homeassistant.components.diagnostics import async_redact_data

TO_REDACT = {"host"}


async def async_get_config_entry_diagnostics(hass, entry):
    """Return diagnostics while redacting connection details."""
    coordinator = entry.runtime_data
    return {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "last_exception": (
            str(coordinator.last_exception)
            if coordinator.last_exception
            else None
        ),
        "network_health": coordinator.network_health,
        "settings": coordinator.settings_info,
        "register_count": len(coordinator.data or {}),
        "registers": {
            str(key): value
            for key, value in sorted((coordinator.data or {}).items())
        },
    }
