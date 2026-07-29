"""Diagnostics support."""
from homeassistant.components.diagnostics import async_redact_data
TO_REDACT={'host'}
async def async_get_config_entry_diagnostics(hass,entry):
    co=entry.runtime_data
    return {'config_entry':async_redact_data(entry.as_dict(),TO_REDACT),'last_update_success':co.last_update_success,'last_exception':str(co.last_exception) if co.last_exception else None,'network_health':co.network_health,'register_count':len(co.data or {}),'registers':{str(k):v for k,v in sorted((co.data or {}).items())}}
