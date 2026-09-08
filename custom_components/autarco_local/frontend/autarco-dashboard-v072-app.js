// Autarco Local v0.7.2 — app-style dashboard and Solis-inspired settings UX.
// This layer intentionally changes presentation only. It does not unlock new writes.

const PANEL_V072 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V072) {
  const proto = PANEL_V072.prototype;
  const previousOverviewV072 = proto._overview;
  const previousActiveContentV072 = proto._activeContent;
  const previousRenderV072 = proto.render;

  proto._v072FindEntity = function (terms) {
    const needles = terms.map((term) => String(term).toLowerCase());
    return this._entities().find((entity) => {
      const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
      const id = String(entity.entity_id || "").toLowerCase();
      return needles.every((needle) => name.includes(needle) || id.includes(needle.replaceAll(" ", "_")));
    }) || null;
  };

  proto._v072NumberState = function (key) {
    const value = this._number(key);
    return value == null ? 0 : value;
  };

  proto._v072PowerText = function (key) {
    const entity = this._findState(key);
    return entity ? this._formatState(entity) : "Niet beschikbaar";
  };

  proto._v072EnergyFlow = function () {
    const pv = Math.abs(this._v072NumberState("pv_power"));
    const battery = Math.abs(this._v072NumberState("battery_power"));
    const grid = Math.abs(this._v072NumberState("grid_power"));
    const house = Math.abs(this._v072NumberState("house_load_power"));
    const maxPower = Math.max(pv, battery, grid, house, 1);
    const line = (value) => Math.max(2, Math.min(7, 2 + (Math.abs(value) / maxPower) * 5));
    const connection = this._findState("connection");
    const connected = connection && ["on", "true", "1", "connected", "aan"].includes(String(connection.state).toLowerCase());
    const soc = this._v072PowerText("battery_soc");

    return `
      <div class="v072-headline">
        <div><span class="v072-eyebrow">Live energiestroom</span><strong>Wat gebeurt er nu?</strong></div>
        <div class="v072-connection ${connected ? "ok" : "bad"}"><span></span>${connected ? "Lokaal verbonden" : "Verbinding niet gezond"}</div>
      </div>
      <div class="v072-flow" aria-label="Live energiestroom tussen PV, omvormer, woning, batterij en elektriciteitsnet">
        <svg class="v072-flow-lines" viewBox="0 0 1000 520" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <marker id="v072-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 z"></path></marker>
            <marker id="v072-arrow-start" markerWidth="8" markerHeight="8" refX="1" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M8,0 L0,4 L8,8 z"></path></marker>
          </defs>
          <path class="solar" d="M500 115 L500 215" style="stroke-width:${line(pv)}" marker-end="url(#v072-arrow)"></path>
          <path class="house" d="M450 300 L235 405" style="stroke-width:${line(house)}" marker-end="url(#v072-arrow)"></path>
          <path class="battery" d="M500 325 L500 430" style="stroke-width:${line(battery)}" marker-start="url(#v072-arrow-start)" marker-end="url(#v072-arrow)"></path>
          <path class="grid" d="M550 300 L765 405" style="stroke-width:${line(grid)}" marker-start="url(#v072-arrow-start)" marker-end="url(#v072-arrow)"></path>
        </svg>
        <div class="v072-node pv"><span class="icon">☀️</span><span>PV</span><strong>${this._escape(this._v072PowerText("pv_power"))}</strong></div>
        <div class="v072-node inverter"><span class="icon">⚡</span><span>Omvormer</span><strong>${this._escape(this._v072PowerText("temperature"))}</strong></div>
        <div class="v072-node house"><span class="icon">🏠</span><span>Woning</span><strong>${this._escape(this._v072PowerText("house_load_power"))}</strong></div>
        <div class="v072-node battery"><span class="icon">🔋</span><span>Batterij</span><strong>${this._escape(this._v072PowerText("battery_power"))}</strong><small>${this._escape(soc)}</small></div>
        <div class="v072-node grid"><span class="icon">↔</span><span>Net</span><strong>${this._escape(this._v072PowerText("grid_power"))}</strong></div>
      </div>`;
  };

  proto._v072TodaySummary = function () {
    const candidates = [
      ["PV vandaag", ["pv", "energy", "today"]],
      ["PV deze maand", ["pv", "energy", "month"]],
      ["Netvermogen", null, "grid_power"],
      ["Batterij-SOC", null, "battery_soc"],
    ];
    return `<div class="v072-summary">${candidates.map(([label, terms, key]) => {
      const entity = key ? this._findState(key) : this._v072FindEntity(terms);
      return `<div><span>${this._escape(label)}</span><strong>${this._escape(entity ? this._formatState(entity) : "—")}</strong></div>`;
    }).join("")}</div>`;
  };

  proto._overview = function overviewV072() {
    return `
      <section class="content-section v072-dashboard">
        ${this._v072EnergyFlow()}
        ${this._v072TodaySummary()}
        <div class="v072-dashboard-grid">
          <div class="v072-panel"><span class="v072-eyebrow">Bedrijfsstatus</span><strong>${this._isOn("self_use_mode") ? "Zelfgebruik actief" : this._isOn("feed_in_priority_mode") ? "Feed-in priority actief" : this._isOn("off_grid_mode") ? "Off-grid actief" : "Bedrijfsmodus uitlezen"}</strong><small>Scenario's vertalen de gekoppelde inverterinstellingen naar begrijpelijke gebruiksdoelen.</small></div>
          <div class="v072-panel"><span class="v072-eyebrow">EMS</span><strong>Voorbereid op koppeling</strong><small>Autarco Local blijft nu eerst de lokale device-app. De generieke hardwarelaag en SNS EMS-besturing volgen in de volgende fase.</small></div>
        </div>
      </section>`;
  };

  proto._v072HistoryRangeMs = function () {
    const range = this._v072HistoryRange || "24h";
    return range === "6h" ? 6 * 3600000 : range === "7d" ? 7 * 86400000 : 24 * 3600000;
  };

  proto._v072HistoryEntity = function () {
    if (this._v072HistoryEntityId && this._hass.states[this._v072HistoryEntityId]) return this._hass.states[this._v072HistoryEntityId];
    const preferred = this._findState("pv_power") || this._findState("battery_soc") || this._entities()[0] || null;
    if (preferred) this._v072HistoryEntityId = preferred.entity_id;
    return preferred;
  };

  proto._v072HistoryChart = function () {
    const cache = this._v072HistoryCache;
    if (this._v072HistoryLoading) return `<div class="v072-history-empty">Historie wordt geladen…</div>`;
    if (this._v072HistoryError) return `<div class="v072-history-empty bad">Historie kon niet worden geladen: ${this._escape(this._v072HistoryError)}</div>`;
    if (!cache || !Array.isArray(cache.points) || cache.points.length < 2) return `<div class="v072-history-empty">Nog geen numerieke historie beschikbaar voor deze entiteit.</div>`;

    const numeric = cache.points.filter((point) => Number.isFinite(point.value));
    if (numeric.length < 2) return `<div class="v072-history-empty">Deze entiteit bevat geen bruikbare numerieke historie.</div>`;
    const min = Math.min(...numeric.map((point) => point.value));
    const max = Math.max(...numeric.map((point) => point.value));
    const spread = Math.max(max - min, Math.max(Math.abs(max), 1) * 0.02);
    const t0 = numeric[0].time;
    const t1 = numeric[numeric.length - 1].time;
    const dt = Math.max(t1 - t0, 1);
    const step = Math.max(1, Math.floor(numeric.length / 500));
    const sampled = numeric.filter((_, index) => index % step === 0 || index === numeric.length - 1);
    const coords = sampled.map((point) => {
      const x = 36 + ((point.time - t0) / dt) * 928;
      const y = 20 + (1 - (point.value - min) / spread) * 210;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    return `
      <div class="v072-chart-wrap">
        <div class="v072-chart-meta"><span>Min <strong>${this._escape(min.toFixed(2))}</strong></span><span>Max <strong>${this._escape(max.toFixed(2))}</strong></span><span>${this._escape(numeric.length)} metingen</span></div>
        <svg class="v072-chart" viewBox="0 0 1000 270" preserveAspectRatio="none" role="img" aria-label="Historische trend">
          <line x1="36" y1="230" x2="964" y2="230"></line><line x1="36" y1="20" x2="36" y2="230"></line>
          <polyline points="${coords}"></polyline>
        </svg>
      </div>`;
  };

  proto._v072History = function () {
    const entities = this._entities().slice().sort((a, b) => this._friendlyName(a).localeCompare(this._friendlyName(b)));
    const selected = this._v072HistoryEntity();
    const range = this._v072HistoryRange || "24h";
    return `
      <section class="content-section v072-history">
        <div class="v072-headline"><div><span class="v072-eyebrow">Recorder / historie</span><strong>Historie van alle Autarco Local-entiteiten</strong></div></div>
        <p class="muted">Kies een entiteit om rechtstreeks de door Home Assistant opgeslagen historie te bekijken. Hierdoor bouwen we geen tweede database naast Recorder.</p>
        <div class="v072-history-controls">
          <label><span>Entiteit</span><select id="v072-history-entity">${entities.map((entity) => `<option value="${this._escape(entity.entity_id)}" ${selected && selected.entity_id === entity.entity_id ? "selected" : ""}>${this._escape(this._friendlyName(entity))}</option>`).join("")}</select></label>
          <div class="v072-range" role="group" aria-label="Historieperiode">${["6h", "24h", "7d"].map((item) => `<button type="button" data-v072-range="${item}" class="${range === item ? "active" : ""}">${item === "6h" ? "6 uur" : item === "24h" ? "24 uur" : "7 dagen"}</button>`).join("")}</div>
        </div>
        <div class="v072-history-title"><div><strong>${this._escape(selected ? this._friendlyName(selected) : "Geen entiteit")}</strong><span>${this._escape(selected ? this._formatState(selected) : "—")}</span></div></div>
        ${this._v072HistoryChart()}
        <div class="v072-history-note">Langere perioden (maand/jaar) bouwen we hierna op HA long-term statistics zodat de app ook met jaren data licht en snel blijft.</div>
      </section>`;
  };

  proto._v072EnsureHistory = async function () {
    if (this._activeTab !== "history" || !this._hass || this._v072HistoryLoading) return;
    const entity = this._v072HistoryEntity();
    if (!entity || typeof this._hass.callApi !== "function") return;
    const range = this._v072HistoryRange || "24h";
    const cacheKey = `${entity.entity_id}|${range}`;
    if (this._v072HistoryCache && this._v072HistoryCache.key === cacheKey && Date.now() - this._v072HistoryCache.loadedAt < 60000) return;

    this._v072HistoryLoading = true;
    this._v072HistoryError = "";
    try {
      const end = new Date();
      const start = new Date(end.getTime() - this._v072HistoryRangeMs());
      const path = `history/period/${encodeURIComponent(start.toISOString())}?filter_entity_id=${encodeURIComponent(entity.entity_id)}&end_time=${encodeURIComponent(end.toISOString())}&no_attributes`;
      const response = await this._hass.callApi("GET", path);
      const rows = Array.isArray(response) && Array.isArray(response[0]) ? response[0] : [];
      const points = rows.map((row) => ({
        time: Date.parse(row.last_changed || row.last_updated || ""),
        value: Number.parseFloat(String(row.state).replace(",", ".")),
      })).filter((point) => Number.isFinite(point.time));
      this._v072HistoryCache = { key: cacheKey, loadedAt: Date.now(), points };
    } catch (error) {
      this._v072HistoryError = error && error.message ? error.message : String(error);
    } finally {
      this._v072HistoryLoading = false;
      if (this._activeTab === "history") this.render();
    }
  };

  proto._v072TimeActive = function (slot) {
    const keys = [`charge_slot_${slot}_start`, `charge_slot_${slot}_end`, `discharge_slot_${slot}_start`, `discharge_slot_${slot}_end`];
    return keys.some((key) => {
      const entity = this._findState(key);
      if (!entity) return false;
      const value = String(entity.state || "").trim().toLowerCase();
      return !["", "0", "00:00", "00:00:00", "unknown", "unavailable", "none"].includes(value);
    });
  };

  proto._v072ApplySettingsUX = function () {
    if (this._activeTab !== "settings" || !this.shadowRoot) return;
    const section = this.shadowRoot.querySelector(".settings-section");
    if (!section || section.querySelector(".v072-tou-planner")) return;
    if (!this._v072ShownSlots) this._v072ShownSlots = new Set();

    const row = (key) => section.querySelector(`.setting-row[data-setting-key="${key}"]`);
    const standard = Array.from(section.querySelectorAll("details.group")).find((details) => String((details.querySelector("summary") || {}).textContent || "").includes("Standaardinstellingen"));
    const planner = document.createElement("details");
    planner.className = "group v072-tou-planner";
    planner.open = this._isOn("time_of_use_mode") || this._v072ShownSlots.size > 0;
    planner.innerHTML = `<summary>🕒 Time of Use / tijdsloten<span class="chevron">⌄</span></summary><div class="v072-tou-body"><div class="v072-tou-intro"><strong>Plan laden en ontladen als perioden</strong><span>Alleen ingestelde of door jou toegevoegde perioden worden getoond. De onderliggende registers blijven dezelfde veilige Autarco Local-settings.</span></div><div class="v072-tou-core"></div><div class="v072-slot-list"></div><button type="button" class="secondary v072-add-slot">+ Tijdslot toevoegen</button><small class="v072-tou-hint">Toevoegen ordent de bestaande slotregisters in de app. Fysieke Time-of-Use writes blijven vergrendeld totdat ze op deze hardware zijn gevalideerd.</small></div>`;

    const core = planner.querySelector(".v072-tou-core");
    ["time_of_use_mode", "scheduled_charge_current", "scheduled_discharge_current"].forEach((key) => {
      const element = row(key);
      if (element) core.appendChild(element);
    });

    const list = planner.querySelector(".v072-slot-list");
    for (let slot = 1; slot <= 3; slot += 1) {
      const active = this._v072TimeActive(slot);
      const shown = active || this._v072ShownSlots.has(slot);
      if (!shown) continue;
      const card = document.createElement("div");
      card.className = `v072-slot ${active ? "active" : "draft"}`;
      card.dataset.slot = String(slot);
      card.innerHTML = `<div class="v072-slot-head"><div><strong>Periode ${slot}</strong><span>${active ? "Ingestelde tijden gevonden" : "Nieuw / nog niet ingesteld"}</span></div>${active ? "" : `<button type="button" class="secondary small" data-v072-hide-slot="${slot}">Verbergen</button>`}</div><div class="v072-slot-grid"><div class="v072-slot-column charge"><span>🔋 Laden</span></div><div class="v072-slot-column discharge"><span>⚡ Ontladen</span></div></div>`;
      const charge = card.querySelector(".charge");
      const discharge = card.querySelector(".discharge");
      [`charge_slot_${slot}_start`, `charge_slot_${slot}_end`].forEach((key) => { const element = row(key); if (element) charge.appendChild(element); });
      [`discharge_slot_${slot}_start`, `discharge_slot_${slot}_end`].forEach((key) => { const element = row(key); if (element) discharge.appendChild(element); });
      list.appendChild(card);
    }

    const anchor = section.querySelector(".v071-health") || section.querySelector(".v070-health") || section.querySelector(".lockbar");
    if (anchor) anchor.insertAdjacentElement("afterend", planner);
    else if (standard) standard.insertAdjacentElement("beforebegin", planner);
    else section.appendChild(planner);

    const hidden = [1, 2, 3].filter((slot) => !this._v072TimeActive(slot) && !this._v072ShownSlots.has(slot));
    const add = planner.querySelector(".v072-add-slot");
    if (!hidden.length) add.style.display = "none";
    add.addEventListener("click", () => {
      const next = [1, 2, 3].find((slot) => !this._v072TimeActive(slot) && !this._v072ShownSlots.has(slot));
      if (next) this._v072ShownSlots.add(next);
      this.render();
    });
    planner.querySelectorAll("[data-v072-hide-slot]").forEach((button) => button.addEventListener("click", () => {
      this._v072ShownSlots.delete(Number(button.dataset.v072HideSlot));
      this.render();
    }));
  };

  proto._activeContent = function activeContentV072() {
    if (this._activeTab === "history") return this._v072History();
    return previousActiveContentV072.call(this);
  };

  proto._v072InstallHistoryTab = function () {
    const nav = this.shadowRoot && this.shadowRoot.querySelector("nav.tabs");
    if (!nav || nav.querySelector('[data-tab="history"]')) return;
    const button = document.createElement("button");
    button.className = `tab ${this._activeTab === "history" ? "active" : ""}`;
    button.dataset.tab = "history";
    button.textContent = "Historie";
    const diagnostics = nav.querySelector('[data-tab="diagnostics"]');
    if (diagnostics) nav.insertBefore(button, diagnostics);
    else nav.appendChild(button);
    button.addEventListener("click", () => { this._activeTab = "history"; this.render(); });
  };

  proto._v072BindHistory = function () {
    if (this._activeTab !== "history" || !this.shadowRoot) return;
    const select = this.shadowRoot.querySelector("#v072-history-entity");
    if (select) select.addEventListener("change", () => {
      this._v072HistoryEntityId = select.value;
      this._v072HistoryCache = null;
      this.render();
    });
    this.shadowRoot.querySelectorAll("[data-v072-range]").forEach((button) => button.addEventListener("click", () => {
      this._v072HistoryRange = button.dataset.v072Range;
      this._v072HistoryCache = null;
      this.render();
    }));
  };

  proto.render = function renderV072() {
    previousRenderV072.call(this);
    if (!this.shadowRoot || !this._hass) return;
    this._v072InstallHistoryTab();
    this._v072ApplySettingsUX();
    this._v072BindHistory();

    if (!this.shadowRoot.querySelector("#autarco-v072-styles")) {
      const style = document.createElement("style");
      style.id = "autarco-v072-styles";
      style.textContent = `
        .v072-dashboard{display:flex;flex-direction:column;gap:14px}.v072-headline{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}.v072-headline>div:first-child{display:flex;flex-direction:column;gap:3px}.v072-headline strong{font-size:24px}.v072-eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--secondary-text-color);font-weight:700}.v072-connection{display:flex;align-items:center;gap:7px;font-size:13px;font-weight:650}.v072-connection>span{width:9px;height:9px;border-radius:50%;background:var(--error-color,#db4437)}.v072-connection.ok>span{background:var(--success-color,#43a047)}
        .v072-flow{position:relative;min-height:430px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:18px;overflow:hidden}.v072-flow-lines{position:absolute;inset:0;width:100%;height:100%}.v072-flow-lines path{fill:none;stroke:var(--disabled-text-color);opacity:.55}.v072-flow-lines path.solar{stroke:var(--warning-color,#d9a400)}.v072-flow-lines path.battery{stroke:var(--success-color,#43a047)}.v072-flow-lines path.grid{stroke:var(--info-color,#4b84c4)}.v072-flow-lines marker path{fill:context-stroke;stroke:none}.v072-node{position:absolute;transform:translate(-50%,-50%);width:150px;min-height:92px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:15px;padding:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;text-align:center;z-index:2}.v072-node .icon{font-size:24px}.v072-node>span:not(.icon),.v072-node small{color:var(--secondary-text-color);font-size:12px}.v072-node strong{font-size:18px}.v072-node.pv{left:50%;top:14%}.v072-node.inverter{left:50%;top:53%}.v072-node.house{left:20%;top:84%}.v072-node.battery{left:50%;top:88%}.v072-node.grid{left:80%;top:84%}
        .v072-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.v072-summary>div,.v072-panel{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:5px}.v072-summary span,.v072-panel small{color:var(--secondary-text-color)}.v072-dashboard-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
        .v072-history-controls{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:16px 0}.v072-history-controls label{display:flex;flex-direction:column;gap:5px;min-width:min(440px,100%)}.v072-history-controls label span{font-size:12px;color:var(--secondary-text-color);font-weight:650}.v072-history-controls select{min-height:42px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);border-radius:9px;padding:8px 10px;font-size:16px}.v072-range{display:flex;gap:5px}.v072-range button{border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);border-radius:8px;padding:9px 11px}.v072-range button.active{border-color:var(--primary-color);color:var(--primary-color);font-weight:700}.v072-history-title{display:flex;justify-content:space-between;margin:10px 0}.v072-history-title>div{display:flex;flex-direction:column;gap:3px}.v072-history-title span{color:var(--secondary-text-color)}.v072-chart-wrap{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:14px;padding:10px}.v072-chart{width:100%;height:270px}.v072-chart line{stroke:var(--divider-color);stroke-width:2}.v072-chart polyline{fill:none;stroke:var(--primary-color);stroke-width:4;vector-effect:non-scaling-stroke}.v072-chart-meta{display:flex;gap:16px;flex-wrap:wrap;color:var(--secondary-text-color);font-size:13px}.v072-history-empty,.v072-history-note{padding:16px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:12px;color:var(--secondary-text-color)}.v072-history-empty.bad{border-left:4px solid var(--error-color,#db4437)}.v072-history-note{margin-top:10px;font-size:13px}
        .v072-tou-body{border-top:1px solid var(--divider-color);padding:14px}.v072-tou-intro{display:flex;flex-direction:column;gap:3px;margin-bottom:12px}.v072-tou-intro span,.v072-tou-hint{color:var(--secondary-text-color);font-size:13px}.v072-tou-core{border:1px solid var(--divider-color);border-radius:10px;overflow:hidden;margin-bottom:12px}.v072-slot-list{display:grid;gap:10px}.v072-slot{border:1px solid var(--divider-color);border-radius:12px;overflow:hidden}.v072-slot.active{border-left:4px solid var(--success-color,#43a047)}.v072-slot-head{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:11px 12px;background:var(--secondary-background-color)}.v072-slot-head>div{display:flex;flex-direction:column;gap:2px}.v072-slot-head span{font-size:12px;color:var(--secondary-text-color)}.v072-slot-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.v072-slot-column{min-width:0}.v072-slot-column+ .v072-slot-column{border-left:1px solid var(--divider-color)}.v072-slot-column>span{display:block;padding:10px 14px 4px;font-size:13px;font-weight:700}.v072-slot-column .setting-row{padding:10px 14px}.v072-slot-column .description,.v072-slot-column .relation{display:none}.v072-add-slot{margin-top:12px}.v072-tou-hint{display:block;margin-top:8px;line-height:1.4}
        @media(max-width:700px){.v072-flow{min-height:520px}.v072-node{width:118px;min-height:82px}.v072-node.pv{top:11%}.v072-node.inverter{top:43%}.v072-node.house{left:18%;top:78%}.v072-node.battery{left:50%;top:88%}.v072-node.grid{left:82%;top:78%}.v072-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.v072-dashboard-grid,.v072-slot-grid{grid-template-columns:1fr}.v072-slot-column+ .v072-slot-column{border-left:0;border-top:1px solid var(--divider-color)}.v072-history-controls label{min-width:100%}.v072-headline{flex-direction:column}}
      `;
      this.shadowRoot.appendChild(style);
    }

    if (this._activeTab === "history") this._v072EnsureHistory();
  };
}
