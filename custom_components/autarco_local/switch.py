"""Diagnostic switches for Autarco Local."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_RUNTIME_KEY = f"{DOMAIN}_runtime_controls"
_LOGGER_NAMES = (
    "custom_components.autarco_local",
    "custom_components.autarco_local.coordinator",
    "custom_components.autarco_local.modbus_client",
    "custom_components.autarco_local.settings_write",
    "custom_components.autarco_local.settings_write_v066",
)


def _runtime_controls(hass):
    return hass.data.setdefault(_RUNTIME_KEY, {"detailed_logging": False})


def _set_detailed_logging(enabled: bool) -> None:
    """Change only Autarco Local logger verbosity; never touch HA root logging."""
    level = logging.DEBUG if enabled else logging.INFO
    for logger_name in _LOGGER_NAMES:
        logging.getLogger(logger_name).setLevel(level)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up diagnostic runtime controls."""
    controls = _runtime_controls(hass)
    _set_detailed_logging(bool(controls.get("detailed_logging", False)))
    async_add_entities([DetailedLoggingSwitch(entry)])


class DetailedLoggingSwitch(SwitchEntity):
    """Temporarily enable verbose Autarco Local debug logging.

    This control deliberately does not inherit coordinator availability: logging
    should remain switchable when a previously loaded inverter connection is in
    trouble. After a Home Assistant restart verbose logging defaults to OFF.
    """

    _attr_has_entity_name = True
    _attr_name = "Detailed logging"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:text-box-search-outline"

    def __init__(self, entry):
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_detailed_logging"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )

    @property
    def is_on(self) -> bool:
        return bool(_runtime_controls(self.hass).get("detailed_logging", False))

    @property
    def extra_state_attributes(self):
        return {
            "scope": "Autarco Local only",
            "persistent": False,
            "restart_behavior": "off",
        }

    async def async_turn_on(self, **kwargs) -> None:
        controls = _runtime_controls(self.hass)
        controls["detailed_logging"] = True
        _set_detailed_logging(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        controls = _runtime_controls(self.hass)
        controls["detailed_logging"] = False
        _set_detailed_logging(False)
        self.async_write_ha_state()
