"""Autarco Local integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import AutarcoLocalCoordinator

type AutarcoLocalConfigEntry = ConfigEntry[AutarcoLocalCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Set up Autarco Local from a config entry."""
    coordinator = AutarcoLocalCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AutarcoLocalConfigEntry,
) -> None:
    """Reload the integration after the entry changes."""
    await hass.config_entries.async_reload(entry.entry_id)
