"""Frontend dashboard registration for Autarco Local."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PANEL_COMPONENT = "autarco-local-dashboard-panel"
PANEL_URL_PATH = "autarco-local"
PANEL_MODULE_URL = "/autarco_local/frontend/autarco-dashboard-entry.js?v=0.6.6.5"
DATA_PANEL = f"{DOMAIN}_dashboard_panel"

_FRONTEND_FILES = (
    "autarco-dashboard-panel.js",
    "autarco-dashboard-bootstrap.js",
    "autarco-dashboard-v066-patch.js",
    "autarco-dashboard-v066-diagnostics.js",
    "autarco-dashboard-v066-data-quality.js",
    "autarco-dashboard-v066-write.js",
    "autarco-dashboard-v066-ui-state.js",
    "autarco-dashboard-entry.js",
)


async def async_register_settings_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Register the Autarco Local tabbed dashboard once.

    The custom sidebar panel is deliberately kept separate from Home Assistant's
    native integration Options flow. The integration gear opens the native
    Configure/Options flow, which is PIN/security-only. Inverter settings live
    exclusively in the Autarco Local dashboard.
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
                    f"/autarco_local/frontend/{filename}",
                    str(frontend_dir / filename),
                    False,
                )
                for filename in _FRONTEND_FILES
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
