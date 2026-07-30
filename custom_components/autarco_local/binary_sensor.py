"""Binary sensors."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass,BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
async def async_setup_entry(hass,entry,async_add_entities): async_add_entities([ConnectionSensor(entry.runtime_data,entry)])
class ConnectionSensor(CoordinatorEntity,BinarySensorEntity):
    _attr_device_class=BinarySensorDeviceClass.CONNECTIVITY; _attr_has_entity_name=True; _attr_translation_key='connection'
    def __init__(self,coordinator,entry):
        super().__init__(coordinator); self._attr_unique_id=f"{entry.entry_id}_connection"; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,entry.entry_id)},name=entry.title,manufacturer='Autarco',model='S2.LH-MII (Modbus TCP)')
    @property
    def is_on(self): return self.coordinator.connection_available
    @property
    def extra_state_attributes(self): return self.coordinator.network_health
