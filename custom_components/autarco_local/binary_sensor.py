"""Binary sensors for Autarco Local."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .connection_monitoring import snapshot as connection_monitor_snapshot
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([
        ConnectionSensor(coordinator, entry),
        TCP502Sensor(coordinator, entry),
        PVProductionSensor(coordinator, entry),
    ])


class BaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Autarco",
            model="S2.LH-MII (Modbus TCP)",
        )


class ConnectionSensor(BaseBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "connection"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_connection"

    @property
    def is_on(self):
        return self.coordinator.connection_available

    @property
    def extra_state_attributes(self):
        return {
            **self.coordinator.network_health,
            "deep_connection_monitor": connection_monitor_snapshot(self.coordinator),
        }


class TCP502Sensor(BaseBinarySensor):
    """Expose the independently classified TCP/502 layer for recorder history."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "TCP 502 bereikbaar"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tcp_502_reachable"

    @property
    def is_on(self):
        value = connection_monitor_snapshot(self.coordinator)["tcp_502_reachable"]
        return value

    @property
    def extra_state_attributes(self):
        monitor = connection_monitor_snapshot(self.coordinator)
        return {
            "classification": monitor["classification"],
            "stage": monitor["stage"],
            "last_probe_ms": monitor["last_tcp_probe_ms"],
            "last_probe_at": monitor["last_tcp_probe_at"],
            "last_tcp_success_at": monitor["last_tcp_success_at"],
            "last_tcp_failure_at": monitor["last_tcp_failure_at"],
            "last_failed_group": monitor["last_failed_group"],
            "last_error": monitor["last_error"],
        }


class PVProductionSensor(BaseBinarySensor):
    """Report whether the inverter currently sees PV production."""

    _attr_translation_key = "pv_production"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pv_production"

    @property
    def is_on(self):
        data = self.coordinator.data or {}
        if 33057 not in data or 33058 not in data:
            return None
        return ((data[33057] << 16) | data[33058]) > 0
