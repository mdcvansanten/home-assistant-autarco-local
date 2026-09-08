// Autarco Local v0.7.2 — Home Assistant Energy-style animated flow.
// Presentation only: no new Modbus writes are enabled here.

const PANEL_V072_FLOW = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V072_FLOW) {
  const proto = PANEL_V072_FLOW.prototype;
  const previousRenderV072Flow = proto.render;

  proto._v072FlowEntity = function (groups) {
    const entities = this._entities();
    for (const terms of groups) {
      const needles = terms.map((term) => String(term).toLowerCase());
      const found = entities.find((entity) => {
        const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
        const id = String(entity.entity_id || "").toLowerCase();
        const haystack = `${id} ${name}`;
        return needles.every((needle) => haystack.includes(needle));
      });
      if (found) return found;
    }
    return null;
  };

  proto._v072FlowValue = function (entity) {
    return entity ? this._formatState(entity) : "—";
  };

  proto._v072DailyEnergy = function () {
    const pvToday = this._v072FlowEntity([
      ["pv", "energy", "today"],
      ["pv", "energie", "vandaag"],
    ]);
    const chargeToday = this._v072FlowEntity([
      ["battery", "charge", "today"],
      ["battery", "charged", "today"],
      ["batterij", "geladen", "vandaag"],
      ["charge", "energy", "today"],
    ]);
    const dischargeToday = this._v072FlowEntity([
      ["battery", "discharge", "today"],
      ["battery", "discharged", "today"],
      ["batterij", "ontladen", "vandaag"],
      ["discharge", "energy", "today"],
    ]);
    const importToday = this._v072FlowEntity([
      ["grid", "import", "today"],
      ["grid", "consumed", "today"],
      ["net", "afname", "vandaag"],
      ["import", "energy", "today"],
    ]);
    const exportToday = this._v072FlowEntity([
      ["grid", "export", "today"],
      ["grid", "produced", "today"],
      ["net", "teruglever", "vandaag"],
      ["export", "energy", "today"],
    ]);
    return { pvToday, chargeToday, dischargeToday, importToday, exportToday };
  };

  proto._v072FlowDirectionClass = function (raw, positiveClass, negativeClass) {
    const deadband = 20;
    if (!Number.isFinite(raw) || Math.abs(raw) < deadband) return "idle";
    return raw > 0 ? positiveClass : negativeClass;
  };

  proto._v072EnergyFlow = function () {
    const pvRaw = this._number("pv_power");
    const batteryRaw = this._number("battery_power");
    const gridRaw = this._number("grid_power");
    const houseRaw = this._number("house_load_power");
    const pv = Math.abs(Number.isFinite(pvRaw) ? pvRaw : 0);
    const battery = Math.abs(Number.isFinite(batteryRaw) ? batteryRaw : 0);
    const grid = Math.abs(Number.isFinite(gridRaw) ? gridRaw : 0);
    const house = Math.abs(Number.isFinite(houseRaw) ? houseRaw : 0);
    const maxPower = Math.max(pv, battery, grid, house, 1);
    const speed = (value) => Math.max(1.0, Math.min(4.5, 4.5 - (Math.abs(value) / maxPower) * 3.5));
    const width = (value) => Math.max(2.2, Math.min(6.5, 2.2 + (Math.abs(value) / maxPower) * 4.3));

    // Current Autarco/Solis convention used for the field test:
    // battery + = discharge, battery - = charge; grid + = import, grid - = export.
    // If the live installation proves the opposite sign, only these two mappings change.
    const batteryDirection = this._v072FlowDirectionClass(batteryRaw, "from-battery", "to-battery");
    const gridDirection = this._v072FlowDirectionClass(gridRaw, "from-grid", "to-grid");
    const pvDirection = pv > 20 ? "active" : "idle";
    const houseDirection = house > 20 ? "active" : "idle";

    const connection = this._findState("connection");
    const connected = connection && ["on", "true", "1", "connected", "aan"].includes(String(connection.state).toLowerCase());
    const soc = this._v072PowerText("battery_soc");
    const daily = this._v072DailyEnergy();

    const energyPair = (leftLabel, leftEntity, rightLabel, rightEntity) => `
      <div class="v072-node-totals">
        <span><small>${this._escape(leftLabel)}</small><strong>${this._escape(this._v072FlowValue(leftEntity))}</strong></span>
        <span><small>${this._escape(rightLabel)}</small><strong>${this._escape(this._v072FlowValue(rightEntity))}</strong></span>
      </div>`;

    return `
      <div class="v072-headline">
        <div><span class="v072-eyebrow">Live energiestroom</span><strong>Wat gebeurt er nu?</strong></div>
        <div class="v072-connection ${connected ? "ok" : "bad"}"><span></span>${connected ? "Lokaal verbonden" : "Verbinding niet gezond"}</div>
      </div>
      <div class="v072-flow v072-flow-ha" aria-label="Live energiestroom tussen PV, omvormer, woning, batterij en elektriciteitsnet">
        <svg class="v072-flow-lines" viewBox="0 0 1000 540" preserveAspectRatio="none" aria-hidden="true">
          <path class="v072-energy-path solar ${pvDirection}" d="M500 112 L500 215" style="--flow-speed:${speed(pv)}s;stroke-width:${width(pv)}"></path>
          <path class="v072-energy-path house ${houseDirection}" d="M450 300 L235 410" style="--flow-speed:${speed(house)}s;stroke-width:${width(house)}"></path>
          <path class="v072-energy-path battery ${batteryDirection}" d="M500 325 L500 435" style="--flow-speed:${speed(battery)}s;stroke-width:${width(battery)}"></path>
          <path class="v072-energy-path grid ${gridDirection}" d="M550 300 L765 410" style="--flow-speed:${speed(grid)}s;stroke-width:${width(grid)}"></path>
        </svg>

        <div class="v072-node pv">
          <span class="icon">☀️</span><span>PV</span><strong>${this._escape(this._v072PowerText("pv_power"))}</strong>
          <small class="v072-today-line">Vandaag ${this._escape(this._v072FlowValue(daily.pvToday))}</small>
        </div>
        <div class="v072-node inverter"><span class="icon">⚡</span><span>Omvormer</span><strong>${this._escape(this._v072PowerText("temperature"))}</strong></div>
        <div class="v072-node house"><span class="icon">🏠</span><span>Woning</span><strong>${this._escape(this._v072PowerText("house_load_power"))}</strong></div>
        <div class="v072-node battery">
          <span class="icon">🔋</span><span>Batterij</span><strong>${this._escape(this._v072PowerText("battery_power"))}</strong><small>${this._escape(soc)}</small>
          ${energyPair("Geladen", daily.chargeToday, "Ontladen", daily.dischargeToday)}
        </div>
        <div class="v072-node grid">
          <span class="icon">⚡</span><span>Net</span><strong>${this._escape(this._v072PowerText("grid_power"))}</strong>
          ${energyPair("Afname", daily.importToday, "Terug", daily.exportToday)}
        </div>
      </div>
      <div class="v072-flow-legend">
        <span class="solar">● PV</span><span class="house">● Woning</span><span class="battery">● Batterij</span><span class="grid">● Net</span>
        <small>Bewegende segmenten tonen de actuele energiestroom. Batterij- en netrichting worden tijdens de hardwaretest gevalideerd.</small>
      </div>`;
  };

  proto.render = function renderV072Flow() {
    previousRenderV072Flow.call(this);
    if (!this.shadowRoot || !this._hass) return;
    if (this.shadowRoot.querySelector("#autarco-v072-flow-styles")) return;

    const style = document.createElement("style");
    style.id = "autarco-v072-flow-styles";
    style.textContent = `
      .v072-flow-ha{min-height:470px}
      .v072-flow-ha .v072-flow-lines path.v072-energy-path{fill:none;opacity:.95;stroke-linecap:round;stroke-dasharray:2 14;animation:v072-flow-forward var(--flow-speed,2s) linear infinite}
      .v072-flow-ha .v072-flow-lines path.v072-energy-path.idle{opacity:.22;stroke-dasharray:none;animation:none}
      .v072-flow-ha .v072-flow-lines path.solar{stroke:#e5a900}.v072-flow-ha .v072-flow-lines path.house{stroke:#3f8fd2}.v072-flow-ha .v072-flow-lines path.battery{stroke:#43a047}.v072-flow-ha .v072-flow-lines path.grid{stroke:#8b9198}
      .v072-flow-ha .v072-flow-lines path.from-battery,.v072-flow-ha .v072-flow-lines path.to-grid{animation-name:v072-flow-reverse}
      .v072-flow-ha .v072-node{border-width:2px}.v072-flow-ha .v072-node.pv{border-color:#e5a900}.v072-flow-ha .v072-node.house{border-color:#3f8fd2}.v072-flow-ha .v072-node.battery{border-color:#43a047}.v072-flow-ha .v072-node.grid{border-color:#8b9198}.v072-flow-ha .v072-node.inverter{border-color:var(--divider-color)}
      .v072-node-totals{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));width:100%;gap:4px;margin-top:5px;padding-top:5px;border-top:1px solid var(--divider-color)}.v072-node-totals>span{display:flex;flex-direction:column;min-width:0}.v072-node-totals small{font-size:9px;color:var(--secondary-text-color)}.v072-node-totals strong{font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v072-today-line{margin-top:3px;font-size:10px!important}
      .v072-flow-legend{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:2px 4px}.v072-flow-legend>span{font-size:12px;font-weight:700}.v072-flow-legend .solar{color:#e5a900}.v072-flow-legend .house{color:#3f8fd2}.v072-flow-legend .battery{color:#43a047}.v072-flow-legend .grid{color:#8b9198}.v072-flow-legend small{color:var(--secondary-text-color);margin-left:auto}
      @keyframes v072-flow-forward{from{stroke-dashoffset:32}to{stroke-dashoffset:0}}@keyframes v072-flow-reverse{from{stroke-dashoffset:0}to{stroke-dashoffset:32}}
      @media(prefers-reduced-motion:reduce){.v072-flow-ha .v072-flow-lines path.v072-energy-path{animation:none;stroke-dasharray:none}}
      @media(max-width:700px){.v072-flow-ha{min-height:560px}.v072-flow-ha .v072-node{width:126px}.v072-node-totals{gap:2px}.v072-flow-legend small{width:100%;margin-left:0}}
    `;
    this.shadowRoot.appendChild(style);
  };
}
