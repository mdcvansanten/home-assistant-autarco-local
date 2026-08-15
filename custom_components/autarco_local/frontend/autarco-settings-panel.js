const GROUPS = [
  {
    id: "standard",
    title: "Standaardinstellingen",
    dot: "green",
    open: true,
    items: [
      ["reserve_soc", "Reserve SOC", "Batterijreserve-doelwaarde. Reserve SOC mag nooit lager worden dan Minimum battery SOC."],
      ["self_use_mode", "Self-use mode", "Gebruikt PV eerst voor huis en batterij voordat overschot wordt teruggeleverd."],
      ["time_of_use_mode", "Time-of-use mode", "Schakelt gepland laden en ontladen met de ingestelde tijdsloten in."],
      ["reserve_battery_mode", "Reserve battery mode", "Schakelt het gebruik van de ingestelde Reserve SOC als batterijreserve in."],
      ["feed_in_priority_mode", "Feed-in priority mode", "Wijzigt de bedrijfsprioriteit richting teruglevering waar dit wordt ondersteund."],
      ["charge_slot_1_start", "Laadslot 1 start", "Starttijd van laadperiode 1."],
      ["charge_slot_1_end", "Laadslot 1 einde", "Eindtijd van laadperiode 1."],
      ["discharge_slot_1_start", "Ontlaadslot 1 start", "Starttijd van ontlaadperiode 1."],
      ["discharge_slot_1_end", "Ontlaadslot 1 einde", "Eindtijd van ontlaadperiode 1."],
      ["charge_slot_2_start", "Laadslot 2 start", "Starttijd van laadperiode 2."],
      ["charge_slot_2_end", "Laadslot 2 einde", "Eindtijd van laadperiode 2."],
      ["discharge_slot_2_start", "Ontlaadslot 2 start", "Starttijd van ontlaadperiode 2."],
      ["discharge_slot_2_end", "Ontlaadslot 2 einde", "Eindtijd van ontlaadperiode 2."],
      ["charge_slot_3_start", "Laadslot 3 start", "Starttijd van laadperiode 3."],
      ["charge_slot_3_end", "Laadslot 3 einde", "Eindtijd van laadperiode 3."],
      ["discharge_slot_3_start", "Ontlaadslot 3 start", "Starttijd van ontlaadperiode 3."],
      ["discharge_slot_3_end", "Ontlaadslot 3 einde", "Eindtijd van ontlaadperiode 3."]
    ]
  },
  {
    id: "expert",
    title: "Expert-instellingen",
    dot: "yellow",
    open: true,
    items: [
      ["minimum_battery_soc", "Minimum battery SOC", "Normale ondergrens voor batterijontlading. Hoger houdt meer batterijreserve beschikbaar."],
      ["force_charge_soc", "Force-charge SOC", "Lage SOC-beschermingsdrempel die samenhangt met geforceerd laden."],
      ["force_charge_power_limit", "Force-charge power limit", "Vermogenslimiet die wordt gebruikt bij force-charge gedrag."],
      ["off_grid_mode", "Off-grid mode", "Stuurt off-gridbedrijf. Alleen gebruiken bij een elektrisch geschikte installatie en correcte omschakeling."],
      ["allow_grid_charging", "Laden vanuit net toestaan", "Staat laden vanuit het elektriciteitsnet toe wanneer de actieve bedrijfsmodus dit gebruikt."],
      ["off_grid_minimum_soc", "Minimum-SOC off-grid", "Minimum-SOC tijdens off-gridbedrijf. Hoger bewaart meer noodreserve."],
      ["scheduled_charge_current", "Geplande laadstroom", "Batterijlaadstroom voor gepland Time-of-use-bedrijf."],
      ["scheduled_discharge_current", "Geplande ontlaadstroom", "Batterijontlaadstroom voor gepland Time-of-use-bedrijf."]
    ]
  },
  {
    id: "installer",
    title: "Installer-/systeeminstellingen",
    dot: "red",
    open: false,
    items: [
      ["overcharge_soc", "Overcharge SOC", "Bovenste SOC-beschermingsinstelling van de batterij. Installer/read-only."],
      [null, "Grid standard / grid code", "Netcode moet overeenkomen met lokale neteisen. Nog niet veilig gemapt."],
      [null, "Grid voltage protection limits", "Netspanningsbeveiligingsgrenzen. Installer/systeem, nog niet veilig gemapt."],
      [null, "Grid frequency protection limits", "Netfrequentiebeveiligingsgrenzen. Installer/systeem, nog niet veilig gemapt."],
      [null, "Anti-islanding / grid protection", "Veiligheids- en anti-islandingbeveiliging. Blijft read-only."],
      [null, "Meter type", "Selecteert het gebruikte metertype. Verkeerde instelling kan vermogensmetingen ongeldig maken."],
      [null, "Meter function / position", "Definieert de rol en positie van de meter in de installatie."],
      [null, "CT direction / configuration", "Definieert stroomtransformatorrichting/configuratie. Verkeerd instellen kan de vermogensrichting omkeren."],
      [null, "Battery Select / battery type", "Selecteert batterij/BMS-profiel. Exact register wordt niet gegokt."],
      [null, "Battery communication", "Batterij CAN/RS485-communicatieconfiguratie. Installer-only."],
      [null, "Battery parameters", "Batterij-elektrische en chemieparameters. Installer/fabrikant gestuurd."],
      [null, "Modbus address / communication", "Communicatieparameters. Wijzigen kan lokale toegang tot de omvormer verbreken."],
      [null, "Factory / calibration", "Fabriekskalibratie en testwaarden. Diagnose/read-only."],
      [null, "Firmware / factory parameters", "Firmware- en fabrieksparameters blijven read-only."]
    ]
  }
];

const ALIASES = {
  reserve_soc: ["_reserve_soc"],
  self_use_mode: ["_self_use_mode"],
  time_of_use_mode: ["_time_of_use_mode"],
  reserve_battery_mode: ["_reserve_battery_mode"],
  feed_in_priority_mode: ["_feed_in_priority_mode"],
  minimum_battery_soc: ["_minimum_battery_soc"],
  force_charge_soc: ["_force_charge_soc"],
  force_charge_power_limit: ["_force_charge_power_limit"],
  off_grid_mode: ["_off_grid_mode"],
  allow_grid_charging: ["_allow_grid_charging", "_allow_grid_charge"],
  off_grid_minimum_soc: ["_off_grid_minimum_soc", "_off_grid_overdischarge_soc"],
  scheduled_charge_current: ["_scheduled_charge_current", "_time_charge_current"],
  scheduled_discharge_current: ["_scheduled_discharge_current", "_time_discharge_current"],
  overcharge_soc: ["_overcharge_soc"],
  charge_slot_1_start: ["_charge_slot_1_start", "_charge_start_1"],
  charge_slot_1_end: ["_charge_slot_1_end", "_charge_end_1"],
  discharge_slot_1_start: ["_discharge_slot_1_start", "_discharge_start_1"],
  discharge_slot_1_end: ["_discharge_slot_1_end", "_discharge_end_1"],
  charge_slot_2_start: ["_charge_slot_2_start", "_charge_start_2"],
  charge_slot_2_end: ["_charge_slot_2_end", "_charge_end_2"],
  discharge_slot_2_start: ["_discharge_slot_2_start", "_discharge_start_2"],
  discharge_slot_2_end: ["_discharge_slot_2_end", "_discharge_end_2"],
  charge_slot_3_start: ["_charge_slot_3_start", "_charge_start_3"],
  charge_slot_3_end: ["_charge_slot_3_end", "_charge_end_3"],
  discharge_slot_3_start: ["_discharge_slot_3_start", "_discharge_start_3"],
  discharge_slot_3_end: ["_discharge_slot_3_end", "_discharge_end_3"]
};

class AutarcoSettingsPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
  }

  set hass(value) {
    this._hass = value;
    this.render();
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    this._narrow = value;
  }

  set route(value) {
    this._route = value;
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    this.render();
  }

  _findState(key) {
    if (!this._hass || !key) return null;
    const aliases = ALIASES[key] || [];
    const states = Object.values(this._hass.states || {});
    return states.find((entity) => {
      if (!entity.entity_id.startsWith("sensor.")) return false;
      if (!entity.entity_id.includes("autarco_local")) return false;
      return aliases.some((suffix) => entity.entity_id.endsWith(suffix));
    }) || null;
  }

  _formatState(entity) {
    if (!entity || ["unknown", "unavailable", "none"].includes(entity.state)) {
      return "Niet beschikbaar";
    }
    const unit = entity.attributes?.unit_of_measurement;
    return unit ? `${entity.state} ${unit}` : entity.state;
  }

  _row(item, group) {
    const [key, label, description] = item;
    const entity = key ? this._findState(key) : null;
    const value = key ? this._formatState(entity) : "Niet gemapt";
    const locked = group.id === "installer" || key === "off_grid_minimum_soc";
    const lockLabel = key === "off_grid_minimum_soc" ? "Schrijftoegang wordt nog gevalideerd" : "Read-only";
    return `
      <div class="setting-row">
        <div class="setting-main">
          <div class="setting-name-wrap">
            <span class="dot ${group.dot}" aria-hidden="true"></span>
            <span class="setting-name">${label}</span>
          </div>
          <div class="setting-value ${locked ? "locked" : ""}" title="${locked ? lockLabel : "Huidige waarde"}">
            ${locked ? '<span class="lock">🔒</span>' : ""}${value}
          </div>
        </div>
        <div class="setting-description">${description}</div>
      </div>`;
  }

  _group(group) {
    return `
      <details class="group" ${group.open ? "open" : ""}>
        <summary>
          <span class="dot ${group.dot}" aria-hidden="true"></span>
          <span>${group.title}</span>
        </summary>
        <div class="rows">${group.items.map((item) => this._row(item, group)).join("")}</div>
      </details>`;
  }

  _safety() {
    const reserve = this._findState("reserve_soc");
    const minimum = this._findState("minimum_battery_soc");
    const force = this._findState("force_charge_soc");
    const offgrid = this._findState("off_grid_minimum_soc");
    return `
      <details class="group safety" open>
        <summary>🛡️ <span>Veiligheidsregels en write-status</span></summary>
        <div class="safety-grid">
          <div><span>Reserve SOC</span><strong>${this._formatState(reserve)}</strong></div>
          <div><span>Minimum battery SOC</span><strong>${this._formatState(minimum)}</strong></div>
          <div><span>Force-charge SOC</span><strong>${this._formatState(force)}</strong></div>
          <div><span>Minimum-SOC off-grid</span><strong>${this._formatState(offgrid)}</strong></div>
        </div>
        <div class="notice warning">
          <strong>Fysieke writes tijdelijk vergrendeld.</strong>
          De eerste gecontroleerde write naar register 43137 (10% → 20%) werd niet door de omvormer bevestigd: read-back bleef 10%. We breiden writes niet uit totdat de officiële Autarco write-/EMS-route en eventuele permissie of unlock is bevestigd.
        </div>
        <div class="notice rule"><strong>Harde backendregel:</strong> Reserve SOC ≥ Minimum battery SOC.</div>
      </details>`;
  }

  render() {
    if (!this.shadowRoot) return;
    if (!this._hass) {
      this.shadowRoot.innerHTML = `<style>:host{display:block;padding:24px;font-family:var(--paper-font-body1_-_font-family,Arial,sans-serif)}</style><p>Autarco Local wordt geladen…</p>`;
      return;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100%;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          font-family: var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
          box-sizing: border-box;
        }
        * { box-sizing: border-box; }
        .page { max-width: 980px; margin: 0 auto; padding: 22px 18px 44px; }
        .header { margin-bottom: 18px; }
        h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; font-weight: 650; }
        .lead { color: var(--secondary-text-color); font-size: 16px; line-height: 1.5; margin: 0; }
        .group {
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 14px;
          margin: 12px 0;
          overflow: hidden;
          box-shadow: var(--ha-card-box-shadow, none);
        }
        summary {
          cursor: pointer;
          list-style: none;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 17px 18px;
          font-size: 19px;
          font-weight: 650;
          user-select: none;
        }
        summary::-webkit-details-marker { display: none; }
        summary::after { content: "⌄"; margin-left: auto; color: var(--secondary-text-color); font-size: 20px; transform: rotate(-90deg); transition: transform .15s ease; }
        details[open] > summary::after { transform: rotate(0deg); }
        .rows { border-top: 1px solid var(--divider-color); }
        .setting-row { padding: 15px 18px 14px; border-bottom: 1px solid var(--divider-color); }
        .setting-row:last-child { border-bottom: 0; }
        .setting-main { display: flex; align-items: center; gap: 16px; justify-content: space-between; }
        .setting-name-wrap { display: flex; align-items: center; gap: 10px; min-width: 0; }
        .setting-name { font-size: 18px; line-height: 1.3; font-weight: 600; }
        .setting-value { flex: 0 0 auto; min-width: 110px; text-align: right; font-size: 18px; font-weight: 600; line-height: 1.3; font-variant-numeric: tabular-nums; }
        .setting-value.locked { color: var(--secondary-text-color); }
        .lock { font-size: 13px; margin-right: 6px; opacity: .8; }
        .setting-description { margin-top: 7px; padding-left: 24px; color: var(--secondary-text-color); font-size: 15.5px; line-height: 1.45; }
        .dot { display: inline-block; width: 14px; height: 14px; min-width: 14px; border-radius: 50%; box-shadow: inset 0 0 0 1px rgba(255,255,255,.2), 0 1px 2px rgba(0,0,0,.25); }
        .green { background: #23c552; }
        .yellow { background: #ffcc00; }
        .red { background: #ef3e42; }
        .safety-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; padding: 0 18px 14px; border-top: 1px solid var(--divider-color); padding-top: 16px; }
        .safety-grid div { background: var(--secondary-background-color); border-radius: 10px; padding: 11px 12px; display: flex; justify-content: space-between; gap: 12px; font-size: 15px; }
        .safety-grid strong { font-size: 16px; }
        .notice { margin: 0 18px 14px; padding: 13px 14px; border-radius: 10px; font-size: 15.5px; line-height: 1.5; }
        .warning { background: color-mix(in srgb, var(--warning-color, #ff9800) 14%, var(--card-background-color)); border: 1px solid color-mix(in srgb, var(--warning-color, #ff9800) 40%, transparent); }
        .rule { background: var(--secondary-background-color); }
        @media (max-width: 620px) {
          .page { padding: 16px 10px 34px; }
          h1 { font-size: 24px; }
          summary { padding: 16px 14px; font-size: 18px; }
          .setting-row { padding: 14px; }
          .setting-main { align-items: flex-start; gap: 10px; }
          .setting-name { font-size: 17px; }
          .setting-value { min-width: auto; font-size: 17px; }
          .setting-description { padding-left: 24px; font-size: 15px; }
          .safety-grid { grid-template-columns: 1fr; padding-left: 14px; padding-right: 14px; }
          .notice { margin-left: 14px; margin-right: 14px; }
        }
        @media (max-width: 410px) {
          .setting-main { flex-wrap: wrap; }
          .setting-value { width: 100%; text-align: left; padding-left: 24px; }
        }
      </style>
      <div class="page">
        <div class="header">
          <h1>Autarco Local Instellingencentrum</h1>
          <p class="lead">Grotere settingnamen, de actuele waarde ernaast en de uitleg direct eronder. De bestaande groen/geel/rood-indeling blijft behouden.</p>
        </div>
        ${GROUPS.map((group) => this._group(group)).join("")}
        ${this._safety()}
      </div>`;
  }
}

if (!customElements.get("autarco-local-settings-panel")) {
  customElements.define("autarco-local-settings-panel", AutarcoSettingsPanel);
}
