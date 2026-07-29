"""Coordinator for Autarco Local."""
from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from .const import CONF_DEVICE_ID,CONF_RETRIES,CONF_SCAN_INTERVAL,CONF_TIMEOUT,DEFAULT_DEVICE_ID,DEFAULT_PORT,DEFAULT_RETRIES,DEFAULT_SCAN_INTERVAL,DEFAULT_TIMEOUT,DOMAIN
from .modbus_client import AutarcoConnectionError,AutarcoConnectionSettings,AutarcoModbusClient
_LOGGER=logging.getLogger(__name__)
class AutarcoLocalCoordinator(DataUpdateCoordinator[dict[int,int]]):
    config_entry:ConfigEntry
    def __init__(self,hass:HomeAssistant,entry:ConfigEntry)->None:
        self.config_entry=entry; self.successful_polls=0; self.failed_polls=0; self.consecutive_failures=0
        self.last_response_ms=None; self.last_attempts=0; self.last_success_at=None; self.last_failure_at=None; self.last_unsupported_blocks=()
        settings=AutarcoConnectionSettings(str(entry.data[CONF_HOST]),int(entry.data.get(CONF_PORT,DEFAULT_PORT)),int(entry.data.get(CONF_DEVICE_ID,DEFAULT_DEVICE_ID)),int(entry.data.get(CONF_TIMEOUT,DEFAULT_TIMEOUT)),int(entry.data.get(CONF_RETRIES,DEFAULT_RETRIES)))
        self.client=AutarcoModbusClient(settings)
        super().__init__(hass,_LOGGER,config_entry=entry,name=DOMAIN,update_interval=timedelta(seconds=int(entry.data.get(CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL))),always_update=True)
    async def _async_update_data(self)->dict[int,int]:
        try: result=await self.hass.async_add_executor_job(self.client.read_all)
        except AutarcoConnectionError as err:
            self.failed_polls+=1; self.consecutive_failures+=1; self.last_failure_at=dt_util.utcnow()
            raise UpdateFailed(translation_domain=DOMAIN,translation_key='communication_error',translation_placeholders={'error':str(err)}) from err
        self.successful_polls+=1; self.consecutive_failures=0; self.last_success_at=dt_util.utcnow(); self.last_response_ms=result.response_ms; self.last_attempts=result.attempts; self.last_unsupported_blocks=result.unsupported_blocks
        return result.registers
    @property
    def network_health(self):
        total=self.successful_polls+self.failed_polls
        return {'successful_polls':self.successful_polls,'failed_polls':self.failed_polls,'consecutive_failures':self.consecutive_failures,'success_rate':round(self.successful_polls/total*100,1) if total else None,'last_response_ms':self.last_response_ms,'last_attempts':self.last_attempts,'last_success_at':self.last_success_at,'last_failure_at':self.last_failure_at,'unsupported_blocks':self.last_unsupported_blocks}
