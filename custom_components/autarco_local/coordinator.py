"""DataUpdateCoordinator for Autarco Local."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .modbus_client import (
    AutarcoConnectionError,
    AutarcoConnectionSettings,
    AutarcoModbusClient,
)

_LOGGER = logging.getLogger(__name__)


class AutarcoLocalCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Coordinate read-only Modbus requests."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry

        settings = AutarcoConnectionSettings(
            host=str(entry.data[CONF_HOST]),
            port=int(entry.data.get(CONF_PORT, DEFAULT_PORT)),
            device_id=int(entry.data.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID)),
            timeout=int(entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
        )
        self.client = AutarcoModbusClient(settings)

        scan_interval = int(
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[int, int]:
        """Fetch data from the inverter."""
        try:
            return await self.hass.async_add_executor_job(self.client.read_all)
        except AutarcoConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
