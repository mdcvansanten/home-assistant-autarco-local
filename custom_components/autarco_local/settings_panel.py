"""Frontend dashboard registration for Autarco Local."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PANEL_COMPONENT = "autarco-local-dashboard-panel"
PANEL_URL_PATH = "autarco-local"
PANEL_STATIC_URL = "/autarco_local/frontend/autarco-dashboard-panel.js"
PANEL_BOOTSTRAP_URL = "/autarco_local/frontend/autarco-dashboard-bootstrap.js"
PANEL_MODULE_URL = f"{PANEL_BOOTSTRAP_URL}?v=0.6.5.2"
DATA_PANEL = f"{DOMAIN}_dashboard_panel"


async def async_register_settings_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Register the Autarco Local tabbed dashboard once.

    Custom web components must be registered through Home Assistant's
    ``panel_custom`` API. Registering the component as a built-in panel creates
    a sidebar route, but the frontend does not instantiate the custom element.
    """
    state = hass.data.setdefault(
        DATA_PANEL,
        {
            "static_registered": False,
            "entries": set(),
        },
    )
    state["entries"].add(entry_id)

    if not state["static_registered"]:
        frontend_dir = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_STATIC_URL,
                    str(frontend_dir / "autarco-dashboard-panel.js"),
                    False,
                ),
                StaticPathConfig(
                    PANEL_BOOTSTRAP_URL,
                    str(frontend_dir / "autarco-dashboard-bootstrap.js"),
                    False,
                ),
            ]
        )
        state["static_registered"] = True

    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        return

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT,
        sidebar_title="Autarco Local",
        sidebar_icon="mdi:solar-power",
        module_url=PANEL_MODULE_URL,
        config={"domain": DOMAIN},
        require_admin=False,
        config_panel_domain=DOMAIN,
    )


def unregister_settings_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Remove the dashboard when the last Autarco Local entry unloads."""
    state = hass.data.get(DATA_PANEL)
    if not state:
        return

    state["entries"].discard(entry_id)
    if state["entries"]:
        return

    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
