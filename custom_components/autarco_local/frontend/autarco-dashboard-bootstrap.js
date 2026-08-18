import "./autarco-dashboard-panel.js";

const SETTING_KEYS = new Set([
  "reserve_soc",
  "self_use_mode",
  "time_of_use_mode",
  "reserve_battery_mode",
  "feed_in_priority_mode",
  "minimum_battery_soc",
  "force_charge_soc",
  "force_charge_power_limit",
  "off_grid_mode",
  "allow_grid_charging",
  "off_grid_minimum_soc",
  "scheduled_charge_current",
  "scheduled_discharge_current",
  "overcharge_soc",
  "charge_slot_1_start",
  "charge_slot_1_end",
  "discharge_slot_1_start",
  "discharge_slot_1_end",
  "charge_slot_2_start",
  "charge_slot_2_end",
  "discharge_slot_2_start",
  "discharge_slot_2_end",
  "charge_slot_3_start",
  "charge_slot_3_end",
  "discharge_slot_3_start",
  "discharge_slot_3_end"
]);

const LIVE_HINTS = {
  battery_soc: ["battery_state_of_charge", "battery_soc"],
  battery_power: ["battery_power"],
  grid_power: ["grid_power"],
  house_load_power: ["house_load_power"],
  pv_power: ["pv_power", "local_pv_power"],
  temperature: ["inverter_temperature", "temperature"]
};

const Panel = customElements.get("autarco-local-dashboard-panel");
if (Panel) {
  const prototype = Panel.prototype;
  const originalFindState = prototype._findState;

  prototype._findState = function findStateWithoutSettingCollisions(key) {
    if (!key) return null;

    const wantsSetting = SETTING_KEYS.has(key);
    const candidates = this._entities().filter((entity) => {
      const isSetting = entity.attributes && entity.attributes.register_type === "holding";
      return wantsSetting ? isSetting : !isSetting;
    });

    if (!wantsSetting) {
      const hints = LIVE_HINTS[key] || [];
      for (const hint of hints) {
        for (const entity of candidates) {
          const entityId = entity.entity_id.toLowerCase();
          const friendlyName = String(
            (entity.attributes && entity.attributes.friendly_name) || ""
          ).toLowerCase().replace(/[^a-z0-9]+/g, "_");
          if (entityId.endsWith(`_${hint}`) || friendlyName.endsWith(`_${hint}`)) {
            return entity;
          }
        }
      }
    }

    const fallback = originalFindState.call(this, key);
    if (!fallback) return null;
    const fallbackIsSetting =
      fallback.attributes && fallback.attributes.register_type === "holding";
    if (wantsSetting === Boolean(fallbackIsSetting)) return fallback;

    return null;
  };
}
