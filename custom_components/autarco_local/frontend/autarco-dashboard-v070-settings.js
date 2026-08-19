// v0.7.0 settings architecture: keep core settings concise and move Time-of-use
// currents/windows to a dedicated schedules subpage.  The UI deliberately uses
// vendor-neutral concepts; Autarco/Solis register details remain in the adapter.

const PANEL_SETTINGS_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_SETTINGS_V070) {
  const proto = PANEL_SETTINGS_V070.prototype;
  const VERSION = "0.7.0.1";

  if (proto._autarcoSettingsV070Version !== VERSION) {
    const SCHEDULE_KEYS = new Set([
      "time_of_use_mode",
      "scheduled_charge_current",
      "scheduled_discharge_current",
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

    const fmt = (instance, key) => instance._formatState(instance._findState(key));

    const timeValue = (instance, key) => {
      const entity = instance._findState(key);
      if (!entity) return "Niet beschikbaar";
      const value = String(entity.state || "");
      return ["unknown", "unavailable", "none"].includes(value.toLowerCase())
        ? "Niet beschikbaar"
        : value;
    };

    const windowState = (start, end) => {
      if (start === "Niet beschikbaar" || end === "Niet beschikbaar") return "onbekend";
      return start === "00:00" && end === "00:00" ? "uit" : "ingesteld";
    };

    const scheduleSlot = (instance, slot) => {
      const chargeStart = timeValue(instance, `charge_slot_${slot}_start`);
      const chargeEnd = timeValue(instance, `charge_slot_${slot}_end`);
      const dischargeStart = timeValue(instance, `discharge_slot_${slot}_start`);
      const dischargeEnd = timeValue(instance, `discharge_slot_${slot}_end`);
      const chargeState = windowState(chargeStart, chargeEnd);
      const dischargeState = windowState(dischargeStart, dischargeEnd);
      return `
        <article class="v070-window-card">
          <div class="v070-window-title">
            <strong>Venster ${slot}</strong>
            <span class="v070-readonly-pill">🧪 read-only</span>
          </div>
          <div class="v070-window-row">
            <span>🔋 Laden</span>
            <strong>${instance._escape(chargeStart)} → ${instance._escape(chargeEnd)}</strong>
            <small>${chargeState}</small>
          </div>
          <div class="v070-window-row">
            <span>⚡ Ontladen</span>
            <strong>${instance._escape(dischargeStart)} → ${instance._escape(dischargeEnd)}</strong>
            <small>${dischargeState}</small>
          </div>
        </article>`;
    };

    const scheduleSummary = (instance) => {
      const tou = fmt(instance, "time_of_use_mode");
      const chargeCurrent = fmt(instance, "scheduled_charge_current");
      const dischargeCurrent = fmt(instance, "scheduled_discharge_current");
      let configured = 0;
      for (const slot of [1, 2, 3]) {
        const cs = timeValue(instance, `charge_slot_${slot}_start`);
        const ce = timeValue(instance, `charge_slot_${slot}_end`);
        const ds = timeValue(instance, `discharge_slot_${slot}_start`);
        const de = timeValue(instance, `discharge_slot_${slot}_end`);
        if (windowState(cs, ce) === "ingesteld" || windowState(ds, de) === "ingesteld") configured += 1;
      }
      return { tou, chargeCurrent, dischargeCurrent, configured };
    };

    const previousSettingsGroup = proto._settingsGroup;
    proto._settingsGroup = function settingsGroupWithoutSchedules(group) {
      if (!previousSettingsGroup || !group || !Array.isArray(group.items)) {
        return previousSettingsGroup ? previousSettingsGroup.call(this, group) : "";
      }
      const filtered = {
        ...group,
        items: group.items.filter((item) => !SCHEDULE_KEYS.has(item && item[0]))
      };
      if (!filtered.items.length) return "";
      return previousSettingsGroup.call(this, filtered);
    };

    const previousSettings = proto._settings;
    proto._settings = function settingsWithSchedulesEntry() {
      let html = previousSettings.call(this);
      const summary = scheduleSummary(this);
      const schedulesTile = `
        <section class="v070-schedules-tile">
          <div class="v070-schedules-icon">🕒</div>
          <div class="v070-schedules-copy">
            <div class="v070-schedules-heading">
              <strong>Tijdschema's</strong>
              <span class="v070-generic-pill">generiek energieconcept</span>
            </div>
            <span>Time-of-use: <b>${this._escape(summary.tou)}</b> · ${summary.configured} venster(s) ingesteld</span>
            <small>Laadlimiet ${this._escape(summary.chargeCurrent)} · ontlaadlimiet ${this._escape(summary.dischargeCurrent)}</small>
          </div>
          <button class="primary" data-action="v070-open-schedules">Beheren →</button>
        </section>
        <section class="v070-validation-strip">
          <strong>Schrijfvalidatie</strong>
          <span class="v070-validation-ok">✓ Off-grid minimum SOC gevalideerd</span>
          <span class="v070-validation-test">🧪 Reserve SOC volgende kandidaat</span>
          <span class="v070-validation-lock">🔒 overige writes per functie testen</span>
        </section>`;

      const firstGroup = html.indexOf('<details class="group');
      if (firstGroup >= 0) {
        html = html.slice(0, firstGroup) + schedulesTile + html.slice(firstGroup);
      } else {
        html = html.replace("</section>", `${schedulesTile}</section>`);
      }
      return html;
    };

    proto._v070Schedules = function schedulesSubpage() {
      const summary = scheduleSummary(this);
      return `
        <section class="content-section settings-section v070-schedules-page">
          <div class="v070-subpage-head">
            <button class="v070-back" data-action="v070-close-schedules">← Instellingen</button>
            <div>
              <h2>🕒 Tijdschema's</h2>
              <p class="muted">Gepland laden en ontladen als één functioneel geheel. De hardware-registers blijven merk-/modelafhankelijk.</p>
            </div>
          </div>

          <div class="v070-schedule-master">
            <div><span>Time-of-use</span><strong>${this._escape(summary.tou)}</strong></div>
            <div><span>Geplande laadstroom</span><strong>${this._escape(summary.chargeCurrent)}</strong></div>
            <div><span>Geplande ontlaadstroom</span><strong>${this._escape(summary.dischargeCurrent)}</strong></div>
          </div>

          <div class="v070-info-box">
            <strong>🧪 Hardwarevalidatie</strong>
            <span>De schemawaarden zijn nu leesbaar. Wijzigen wordt pas geopend nadat Time-of-use, stroomlimieten en één volledig laad/ontlaadvenster veilig op de inverter zijn getest.</span>
          </div>

          <div class="v070-windows">
            ${[1, 2, 3].map((slot) => scheduleSlot(this, slot)).join("")}
          </div>

          <div class="v070-generic-note">
            <strong>Waarom apart?</strong>
            <span>Scenario's gebruiken straks generieke acties zoals “laad in dit venster”. De Autarco-adapter vertaalt dat naar de drie fysieke inverter-slots.</span>
          </div>
        </section>`;
    };

    const previousActiveContent = proto._activeContent;
    proto._activeContent = function activeContentWithSchedules() {
      if (this._activeTab === "settings" && this._v070SettingsSubpage === "schedules") {
        return this._v070Schedules();
      }
      return previousActiveContent.call(this);
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindV070SettingsEvents() {
      if (previousBindEvents) previousBindEvents.call(this);
      const open = this.shadowRoot && this.shadowRoot.querySelector('[data-action="v070-open-schedules"]');
      if (open) {
        open.addEventListener("click", () => {
          this._v070SettingsSubpage = "schedules";
          this.render();
        });
      }
      const close = this.shadowRoot && this.shadowRoot.querySelector('[data-action="v070-close-schedules"]');
      if (close) {
        close.addEventListener("click", () => {
          this._v070SettingsSubpage = "overview";
          this.render();
        });
      }
    };

    const previousRender = proto.render;
    proto.render = function renderV070Settings() {
      previousRender.call(this);
      if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v070-settings-style")) return;
      const style = document.createElement("style");
      style.id = "autarco-v070-settings-style";
      style.textContent = `
        .v070-schedules-tile {
          display:grid; grid-template-columns:auto 1fr auto; gap:14px; align-items:center;
          margin:12px 0; padding:16px; border:1px solid var(--divider-color);
          border-radius:14px; background:var(--card-background-color);
        }
        .v070-schedules-icon { font-size:28px; }
        .v070-schedules-copy { display:flex; flex-direction:column; gap:4px; min-width:0; }
        .v070-schedules-heading { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:17px; }
        .v070-schedules-copy small { color:var(--secondary-text-color); }
        .v070-generic-pill, .v070-readonly-pill {
          font-size:11px; line-height:1; padding:5px 7px; border-radius:999px;
          background:var(--secondary-background-color); color:var(--secondary-text-color);
          border:1px solid var(--divider-color); font-weight:600;
        }
        .v070-validation-strip {
          display:flex; gap:8px; flex-wrap:wrap; align-items:center;
          margin:0 0 14px; padding:10px 12px; border-radius:10px;
          background:var(--secondary-background-color); font-size:13px;
        }
        .v070-validation-strip > span { padding:4px 7px; border-radius:7px; }
        .v070-validation-ok { border-left:3px solid #23c552; }
        .v070-validation-test { border-left:3px solid #f4b400; }
        .v070-validation-lock { border-left:3px solid #9e9e9e; }
        .v070-subpage-head { display:flex; gap:14px; align-items:flex-start; margin-bottom:16px; }
        .v070-subpage-head h2 { margin:0 0 4px; }
        .v070-back {
          border:1px solid var(--divider-color); border-radius:9px; padding:8px 10px;
          background:var(--secondary-background-color); color:var(--primary-text-color); cursor:pointer;
        }
        .v070-schedule-master {
          display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:12px;
        }
        .v070-schedule-master > div {
          display:flex; flex-direction:column; gap:5px; padding:12px;
          border:1px solid var(--divider-color); border-radius:10px;
          background:var(--card-background-color);
        }
        .v070-schedule-master span { color:var(--secondary-text-color); font-size:13px; }
        .v070-info-box, .v070-generic-note {
          display:flex; flex-direction:column; gap:4px; padding:11px 13px; margin:12px 0;
          border-radius:10px; background:var(--secondary-background-color);
          border-left:4px solid #f4b400;
        }
        .v070-generic-note { border-left-color:#039be5; }
        .v070-windows { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
        .v070-window-card {
          border:1px solid var(--divider-color); border-radius:12px; padding:12px;
          background:var(--card-background-color); display:flex; flex-direction:column; gap:10px;
        }
        .v070-window-title { display:flex; justify-content:space-between; gap:8px; align-items:center; }
        .v070-window-row {
          display:grid; grid-template-columns:1fr; gap:3px; padding-top:8px;
          border-top:1px solid var(--divider-color);
        }
        .v070-window-row small { color:var(--secondary-text-color); }
        @media (max-width:800px) {
          .v070-schedules-tile { grid-template-columns:auto 1fr; }
          .v070-schedules-tile button { grid-column:1 / -1; width:100%; }
          .v070-schedule-master, .v070-windows { grid-template-columns:1fr; }
          .v070-subpage-head { flex-direction:column; }
        }
      `;
      this.shadowRoot.appendChild(style);
    };

    proto._autarcoSettingsV070Version = VERSION;
  }
}
