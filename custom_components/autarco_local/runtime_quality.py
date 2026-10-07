"""Register dependencies and quality gates; no communication or value guessing."""

SENSOR_REGISTERS = {
    "pv_power": (33057, 33058),
    "pv_energy_total": (33029, 33030),
    "pv_energy_month": (33031, 33032),
    "pv_energy_today": (33035,),
    "pv_energy_year": (33037, 33038),
    "pv_alarm_code": (33070,),
    "pv_bus_voltage": (33071,),
    "phase_voltage_l1": (33073,),
    "phase_voltage_l2": (33074,),
    "phase_voltage_l3": (33075,),
    "active_power": (33079, 33080),
    "temperature": (33093,),
    "grid_frequency": (33094,),
    "battery_voltage": (33133,),
    "battery_current": (33134, 33135),
    "battery_soc": (33139,),
    "house_load_power": (33147,),
    "battery_power": (33135, 33149, 33150),
    "grid_power": (33151, 33152),
}
for _index in range(1, 5):
    _voltage = 33049 + (_index - 1) * 2
    SENSOR_REGISTERS[f"pv_voltage_{_index}"] = (_voltage,)
    SENSOR_REGISTERS[f"pv_current_{_index}"] = (_voltage + 1,)
    SENSOR_REGISTERS[f"pv_power_{_index}"] = (_voltage, _voltage + 1)

EMS_KEYS = ("pv_power", "grid_power", "house_load_power", "battery_soc", "battery_power")
EMS_REGISTERS = frozenset(address for key in EMS_KEYS for address in SENSOR_REGISTERS[key])


def runtime_quality(registers, *, failed: bool, age: float | None, max_age: float) -> str:
    if not registers or age is None:
        return "unavailable"
    if failed or age > max_age:
        return "stale"
    if not EMS_REGISTERS.issubset(registers):
        return "partial"
    return "live"
