"""Sensors for Autarco Local."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from homeassistant.components.sensor import SensorDeviceClass,SensorEntity,SensorEntityDescription,SensorStateClass
from homeassistant.const import EntityCategory,UnitOfElectricCurrent,UnitOfElectricPotential,UnitOfFrequency,UnitOfPower,UnitOfTemperature,UnitOfTime,PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util
from .const import DOMAIN

def u16(d,a): return d.get(a)
def s16(d,a):
    v=d.get(a); return None if v is None else (v-65536 if v>=32768 else v)
def u32(d,h,l): return None if h not in d or l not in d else (d[h]<<16)|d[l]
def s32(d,h,l):
    v=u32(d,h,l); return None if v is None else (v-4294967296 if v>=2147483648 else v)
@dataclass(frozen=True,kw_only=True)
class Desc(SensorEntityDescription): value_fn:Callable
S=(
Desc(key='pv_voltage_1',translation_key='pv_voltage_1',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33049)/10 if u16(d,33049) is not None else None),
Desc(key='pv_current_1',translation_key='pv_current_1',device_class=SensorDeviceClass.CURRENT,native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33050)/10 if u16(d,33050) is not None else None),
Desc(key='pv_voltage_2',translation_key='pv_voltage_2',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33051)/10 if u16(d,33051) is not None else None),
Desc(key='pv_current_2',translation_key='pv_current_2',device_class=SensorDeviceClass.CURRENT,native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33052)/10 if u16(d,33052) is not None else None),
Desc(key='pv_power',translation_key='pv_power',device_class=SensorDeviceClass.POWER,native_unit_of_measurement=UnitOfPower.WATT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u32(d,33057,33058)),
Desc(key='phase_voltage_l1',translation_key='phase_voltage_l1',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33073)/10 if u16(d,33073) is not None else None),
Desc(key='phase_voltage_l2',translation_key='phase_voltage_l2',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33074)/10 if u16(d,33074) is not None else None),
Desc(key='phase_voltage_l3',translation_key='phase_voltage_l3',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33075)/10 if u16(d,33075) is not None else None),
Desc(key='active_power',translation_key='active_power',device_class=SensorDeviceClass.POWER,native_unit_of_measurement=UnitOfPower.WATT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:s32(d,33079,33080)),
Desc(key='temperature',translation_key='temperature',device_class=SensorDeviceClass.TEMPERATURE,native_unit_of_measurement=UnitOfTemperature.CELSIUS,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:s16(d,33093)/10 if s16(d,33093) is not None else None),
Desc(key='grid_frequency',translation_key='grid_frequency',device_class=SensorDeviceClass.FREQUENCY,native_unit_of_measurement=UnitOfFrequency.HERTZ,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33094)/100 if u16(d,33094) is not None else None),
Desc(key='battery_voltage',translation_key='battery_voltage',device_class=SensorDeviceClass.VOLTAGE,native_unit_of_measurement=UnitOfElectricPotential.VOLT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33133)/10 if u16(d,33133) is not None else None),
Desc(key='battery_current',translation_key='battery_current',device_class=SensorDeviceClass.CURRENT,native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:(-1 if u16(d,33135)==1 else 1)*u16(d,33134)/10 if u16(d,33134) is not None else None),
Desc(key='battery_soc',translation_key='battery_soc',device_class=SensorDeviceClass.BATTERY,native_unit_of_measurement=PERCENTAGE,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33139)),
Desc(key='house_load_power',translation_key='house_load_power',device_class=SensorDeviceClass.POWER,native_unit_of_measurement=UnitOfPower.WATT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:u16(d,33147)),
Desc(key='battery_power',translation_key='battery_power',device_class=SensorDeviceClass.POWER,native_unit_of_measurement=UnitOfPower.WATT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:(-1 if u16(d,33135)==1 else 1)*u32(d,33149,33150) if u32(d,33149,33150) is not None else None),
Desc(key='grid_power',translation_key='grid_power',device_class=SensorDeviceClass.POWER,native_unit_of_measurement=UnitOfPower.WATT,state_class=SensorStateClass.MEASUREMENT,value_fn=lambda d:s32(d,33151,33152)),
)
async def async_setup_entry(hass,entry,async_add_entities):
    co=entry.runtime_data; async_add_entities([RegisterSensor(co,entry,x) for x in S]+[MetricSensor(co,entry,'response_time'),MetricSensor(co,entry,'read_time'),MetricSensor(co,entry,'connect_time'),MetricSensor(co,entry,'average_poll_time'),MetricSensor(co,entry,'min_poll_time'),MetricSensor(co,entry,'max_poll_time'),MetricSensor(co,entry,'success_rate'),MetricSensor(co,entry,'failed_polls'),MetricSensor(co,entry,'total_retries'),MetricSensor(co,entry,'reconnect_count'),MetricSensor(co,entry,'consecutive_failures'),MetricSensor(co,entry,'last_success'),MetricSensor(co,entry,'connected_since'),MetricSensor(co,entry,'connection_uptime'),MetricSensor(co,entry,'longest_connection'),MetricSensor(co,entry,'last_disconnect'),MetricSensor(co,entry,'last_reconnect'),MetricSensor(co,entry,'total_downtime'),MetricSensor(co,entry,'availability'),MetricSensor(co,entry,'health_score'),CountSensor(co,entry),ClockSensor(co,entry)])
class Base(CoordinatorEntity,SensorEntity):
    _attr_has_entity_name=True
    def __init__(self,co,entry,desc):
        super().__init__(co); self.entity_description=desc; self._attr_unique_id=f"{entry.entry_id}_{desc.key}"; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,entry.entry_id)},name=entry.title,manufacturer='Autarco',model='S2.LH-MII (Modbus TCP)')
class RegisterSensor(Base):
    @property
    def native_value(self): return self.entity_description.value_fn(self.coordinator.data or {})
class MetricSensor(Base):
    def __init__(self,co,entry,key):
        m={'response_time':SensorEntityDescription(key='response_time',translation_key='response_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),'read_time':SensorEntityDescription(key='read_time',translation_key='read_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'connect_time':SensorEntityDescription(key='connect_time',translation_key='connect_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'average_poll_time':SensorEntityDescription(key='average_poll_time',translation_key='average_poll_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'min_poll_time':SensorEntityDescription(key='min_poll_time',translation_key='min_poll_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'max_poll_time':SensorEntityDescription(key='max_poll_time',translation_key='max_poll_time',native_unit_of_measurement='ms',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'success_rate':SensorEntityDescription(key='success_rate',translation_key='success_rate',native_unit_of_measurement=PERCENTAGE,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),'failed_polls':SensorEntityDescription(key='failed_polls',translation_key='failed_polls',state_class=SensorStateClass.TOTAL_INCREASING,entity_category=EntityCategory.DIAGNOSTIC),
'total_retries':SensorEntityDescription(key='total_retries',translation_key='total_retries',state_class=SensorStateClass.TOTAL_INCREASING,entity_category=EntityCategory.DIAGNOSTIC),
'reconnect_count':SensorEntityDescription(key='reconnect_count',translation_key='reconnect_count',state_class=SensorStateClass.TOTAL_INCREASING,entity_category=EntityCategory.DIAGNOSTIC),
'consecutive_failures':SensorEntityDescription(key='consecutive_failures',translation_key='consecutive_failures',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'last_success':SensorEntityDescription(key='last_success',translation_key='last_success',device_class=SensorDeviceClass.TIMESTAMP,entity_category=EntityCategory.DIAGNOSTIC),
'connected_since':SensorEntityDescription(key='connected_since',translation_key='connected_since',device_class=SensorDeviceClass.TIMESTAMP,entity_category=EntityCategory.DIAGNOSTIC),
'connection_uptime':SensorEntityDescription(key='connection_uptime',translation_key='connection_uptime',device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.SECONDS,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'longest_connection':SensorEntityDescription(key='longest_connection',translation_key='longest_connection',device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.SECONDS,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'last_disconnect':SensorEntityDescription(key='last_disconnect',translation_key='last_disconnect',device_class=SensorDeviceClass.TIMESTAMP,entity_category=EntityCategory.DIAGNOSTIC),
'last_reconnect':SensorEntityDescription(key='last_reconnect',translation_key='last_reconnect',device_class=SensorDeviceClass.TIMESTAMP,entity_category=EntityCategory.DIAGNOSTIC),
'total_downtime':SensorEntityDescription(key='total_downtime',translation_key='total_downtime',device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.SECONDS,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'availability':SensorEntityDescription(key='availability',translation_key='availability',native_unit_of_measurement=PERCENTAGE,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC),
'health_score':SensorEntityDescription(key='health_score',translation_key='health_score',native_unit_of_measurement=PERCENTAGE,state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC)}; super().__init__(co,entry,m[key])
    @property
    def native_value(self):
        h=self.coordinator.network_health; return {'response_time':h['last_response_ms'],'read_time':h['last_read_ms'],'connect_time':h['last_connect_ms'],'average_poll_time':h['average_poll_ms'],'min_poll_time':h['min_poll_ms'],'max_poll_time':h['max_poll_ms'],'success_rate':h['success_rate'],'failed_polls':h['failed_polls'],'total_retries':h['total_retries'],'reconnect_count':h['reconnect_count'],'consecutive_failures':h['consecutive_failures'],'last_success':h['last_success_at'],'connected_since':h['connected_since'],'connection_uptime':h['current_connection_uptime_seconds'],'longest_connection':h['longest_connection_seconds'],'last_disconnect':h['last_disconnect_at'],'last_reconnect':h['last_reconnect_at'],'total_downtime':h['total_downtime_seconds'],'availability':h['availability_percent'],'health_score':h['health_score']}[self.entity_description.key]
class CountSensor(Base):
    def __init__(self,co,entry): super().__init__(co,entry,SensorEntityDescription(key='register_count',translation_key='register_count',state_class=SensorStateClass.MEASUREMENT,entity_category=EntityCategory.DIAGNOSTIC))
    @property
    def native_value(self): return len(self.coordinator.data or {})
class ClockSensor(Base):
    def __init__(self,co,entry): super().__init__(co,entry,SensorEntityDescription(key='device_time',translation_key='device_time',device_class=SensorDeviceClass.TIMESTAMP,entity_category=EntityCategory.DIAGNOSTIC))
    @property
    def native_value(self):
        d=self.coordinator.data or {}
        try: return datetime(2000+d[33022],d[33023],d[33024],d[33025],d[33026],d[33027],tzinfo=dt_util.DEFAULT_TIME_ZONE)
        except (KeyError,ValueError,TypeError): return None
