"""Frontend panel registration for Autarco Local Settings Center."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PANEL_COMPONENT = "autarco-local-settings-panel"
PANEL_URL_PATH = "autarco-local-settings"
PANEL_STATIC_URL = "/autarco_local/frontend/autarco-settings-panel.js"
PANEL_MODULE_URL = f"{PANEL_STATIC_URL}?v=0.6.4"
DATA_PANEL = f"{DOMAIN}_settings_panel"


async def async_register_settings_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Register the custom Settings Center panel once and track active entries."""
    state = hass.data.setdefault(
        DATA_PANEL,
        {
            "static_registered": False,
            "module_registered": False,
            "entries": set(),
        },
    )
    state["entries"].add(entry_id)

    if not state["static_registered"]:
        frontend_path = Path(__file__).parent / "frontend" / "autarco-settings-panel.js"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_STATIC_URL, str(frontend_path), False)]
        )
        state["static_registered"] = True

    if not state["module_registered"]:
        frontend.add_extra_js_url(hass, PANEL_MODULE_URL)
        state["module_registered"] = True

    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        return

    frontend.async_register_built_in_panel(
        hass,
        component_name=PANEL_COMPONENT,
        sidebar_title="Autarco Local",
        sidebar_icon="mdi:solar-power",
        sidebar_default_visible=True,
        frontend_url_path=PANEL_URL_PATH,
        config={"domain": DOMAIN},
        require_admin=False,
        config_panel_domain=DOMAIN,
        show_in_sidebar=True,
    )


def unregister_settings_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Remove the visible panel when the last Autarco Local entry unloads."""
    state = hass.data.get(DATA_PANEL)
    if not state:
        return

    state["entries"].discard(entry_id)
    if state["entries"]:
        return

    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
