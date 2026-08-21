// Autarco Local v0.7.0 — scenario-first UX and relation-aware settings view.
// Unvalidated scenario writes remain disabled; v0.6.6 stays the physical-write baseline.

const PANEL_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V070) {
  const proto = PANEL_V070.prototype;
  const originalSettingsV070 = proto._settings;
  const originalSettingRowV070 = proto._settingRow;
  const originalBindEventsV070 = proto._bindEvents;

  const LINKED_SETTING_KEYS = new Set([
    "reserve_soc", "self_use_mode", "time_of_use_mode", "reserve_battery_mode",
    "feed_in_priority_mode", "minimum_battery_soc", "force_charge_soc",
    "force_charge_power_limit", "off_grid_mode", "allow_grid_charging",
    "off_grid_minimum_soc", "scheduled_charge_current", "scheduled_discharge_current"
  ]);

  const SCENARIO_DEFS_V070 = [
    {key:"self_use",name:"Normaal zelfgebruik",goal:"Huis eerst → accu → net",description:"Dagelijks standaardbedrijf met Self-use als herkenbaar scenario in plaats van een los work-mode bit.",settings:["self_use_mode","minimum_battery_soc","reserve_battery_mode","reserve_soc"],readiness:"guided",active:(p)=>p._isOn("self_use_mode")},
    {key:"reserve",name:"Accu vasthouden",goal:"Energie bewaren tot gekozen reserve-SOC",description:"Bundelt Battery Reserve, Reserve SOC en Minimum SOC tot één begrijpelijke gebruikersflow.",settings:["reserve_battery_mode","reserve_soc","minimum_battery_soc"],readiness:"pending",active:(p)=>p._isOn("reserve_battery_mode")},
    {key:"manual_grid_charge",name:"Nu laden vanaf het net",goal:"Handmatig laden tot gekozen doel-SOC",description:"Voorbereid voor gecontroleerd netladen, onafhankelijk van tarieven en PV. Activering volgt na hardwarevalidatie van start, stop en herstel.",settings:["allow_grid_charging","force_charge_soc","force_charge_power_limit","minimum_battery_soc"],readiness:"pending",active:(p)=>p._isOn("allow_grid_charging")},
    {key:"time_of_use",name:"Nacht-/tijdladen",goal:"Laden of ontladen binnen tijdvakken",description:"Groepeert Time of Use, stromen en tijdsloten zodat de gebruiker de registerrelaties niet zelf hoeft te begrijpen.",settings:["time_of_use_mode","scheduled_charge_current","scheduled_discharge_current","charge_slot_1_start","charge_slot_1_end"],readiness:"pending",active:(p)=>p._isOn("time_of_use_mode")},
    {key:"feed_in_priority",name:"Maximaal terugleveren",goal:"PV-export krijgt voorrang",description:"Feed-in Priority wordt als bedrijfsmodus behandeld en niet als onafhankelijk los bit.",settings:["feed_in_priority_mode","self_use_mode","time_of_use_mode"],readiness:"pending",active:(p)=>p._isOn("feed_in_priority_mode")},
    {key:"peak_shaving",name:"Peak shaving",goal:"Netpiek begrenzen",description:"Voorbereid voor het toekomstige SNS EMS. Benodigde Autarco-registers moeten nog lokaal worden bewezen.",settings:["minimum_battery_soc"],readiness:"unavailable",active:()=>false},
    {key:"backup_reserve",name:"Backupreserve",goal:"Vaste noodreserve beschikbaar houden",description:"Maakt Reserve SOC, Minimum SOC en off-grid reserve als samenhangende veiligheidsinstellingen zichtbaar.",settings:["reserve_battery_mode","reserve_soc","minimum_battery_soc","off_grid_minimum_soc"],readiness:"pending",active:(p)=>p._isOn("reserve_battery_mode")},
    {key:"battery_maintenance",name:"Onderhoud / battery healing",goal:"Accu gecontroleerd naar onderhoudstoestand",description:"Expert-scenario; blijft uitgeschakeld totdat batterij/BMS-afhankelijkheden volledig zijn gevalideerd.",settings:["allow_grid_charging","force_charge_power_limit","minimum_battery_soc","off_grid_minimum_soc"],readiness:"unavailable",active:()=>false}
  ];

  proto._v070ConfigurationHealth = function () {
    const reserve = this._number("reserve_soc");
    const minimum = this._number("minimum_battery_soc");
    const force = this._number("force_charge_soc");
    const findings = [];
    if (reserve !== null && minimum !== null && reserve < minimum) {
      findings.push({severity:"blocking",title:"Reserve SOC lager dan Minimum SOC",text:`Reserve SOC is ${reserve}% en Minimum SOC is ${minimum}%. Scenario-writes blijven geblokkeerd totdat deze relatie klopt.`});
    }
    const activeModes = [["Self-use",this._isOn("self_use_mode")],["Feed-in Priority",this._isOn("feed_in_priority_mode")],["Off-grid",this._isOn("off_grid_mode")]].filter((x)=>x[1]).map((x)=>x[0]);
    if (activeModes.length > 1) {
      findings.push({severity:"warning",title:"Meerdere work-mode bits actief",text:`${activeModes.join(", ")} worden als één gekoppelde toestand behandeld. Een toekomstige write moet de complete mode snapshotten en teruglezen.`});
    }
    if (force !== null && minimum !== null && force > minimum) {
      findings.push({severity:"warning",title:"Force-charge SOC boven Minimum SOC",text:`Force-charge SOC is ${force}% en Minimum SOC is ${minimum}%. Controleer de beschermingsdrempels voordat netlaadscenario's worden vrijgegeven.`});
    }
    const blocking = findings.some((x)=>x.severity === "blocking");
    const warning = findings.some((x)=>x.severity === "warning");
    return {state:blocking?"blocked":warning?"warning":"healthy",findings};
  };

  proto._scenarioSection = function () {
    const health = this._v070ConfigurationHealth();
    const cards = SCENARIO_DEFS_V070.map((scenario) => {
      const active = Boolean(scenario.active(this));
      let stateLabel = "Voorbereid — hardwarevalidatie volgt";
      let stateClass = "pending";
      if (scenario.readiness === "unavailable") { stateLabel = "Nog niet gemapt / gevalideerd"; }
      else if (health.state === "blocked") { stateLabel = "Geblokkeerd door configuratieconflict"; }
      else if (active) { stateLabel = "Momenteel actief / gedetecteerd"; stateClass = "basis"; }
      else if (scenario.readiness === "guided") { stateLabel = "Beschikbaar als begeleide configuratie"; stateClass = "basis"; }
      return `<div class="scenario-card v070-scenario ${active?"active":""}"><div class="scenario-title">${active?"● ":""}${this._escape(scenario.name)}</div><strong>${this._escape(scenario.goal)}</strong><p>${this._escape(scenario.description)}</p><span class="scenario-state ${stateClass}">${this._escape(stateLabel)}</span><button class="secondary small v070-show-settings" data-scenario="${this._escape(scenario.key)}">Bekijk gekoppelde instellingen</button></div>`;
    }).join("");
    return `<details class="group dependencies v070-scenarios" data-v070-scenarios open><summary>🎛️ Scenario's & bedrijfsmodi<span class="chevron">⌄</span></summary><div class="v070-intro"><strong>Scenario eerst, registers daarna.</strong><span>Autarco Local vertaalt samenhangende Solis-hybrid instellingen naar herkenbare Autarco-scenario's. Onbewezen writes blijven bewust vergrendeld.</span></div><div class="scenario-grid">${cards}</div></details>`;
  };

  proto._v070HealthPanel = function () {
    const health = this._v070ConfigurationHealth();
    const title = health.state === "blocked" ? "⛔ Configuratieconflict" : health.state === "warning" ? "⚠️ Configuratie vraagt aandacht" : "✅ Gekoppelde instellingen zijn consistent";
    const items = health.findings.length ? `<div class="v070-findings">${health.findings.map((item)=>`<div class="v070-finding ${item.severity}"><strong>${this._escape(item.title)}</strong><span>${this._escape(item.text)}</span></div>`).join("")}</div>` : `<span>Geen blokkerende of waarschuwende relaties gevonden in de momenteel beschikbare instellingen.</span>`;
    return `<div class="v070-health ${health.state}"><strong>${title}</strong>${items}</div>`;
  };

  proto._settingRow = function (item, group) {
    let html = originalSettingRowV070.call(this, item, group);
    const key = item && item[0];
    if (!key) return html;
    html = html.replace('<div class="setting-row">', `<div class="setting-row" data-setting-key="${this._escape(key)}">`);
    if (LINKED_SETTING_KEYS.has(key)) {
      html = html.replace('<div class="setting-title">','<div class="setting-title"><span class="v070-linked">🔗 Gekoppeld</span>');
    }
    return html;
  };

  proto._settings = function () {
    const scenarioHtml = this._scenarioSection();
    let html = originalSettingsV070.call(this);
    html = html.replace(scenarioHtml, "");
    const enhancedHeading = `<h2>Instellingen</h2><style>.v070-intro{display:flex;flex-direction:column;gap:4px;margin:8px 0 14px}.v070-scenario.active{outline:2px solid var(--primary-color)}.v070-show-settings{margin-top:10px}.v070-health{display:flex;flex-direction:column;gap:8px;padding:12px 14px;border-radius:12px;margin:10px 0 16px;background:var(--secondary-background-color)}.v070-health.blocked{border-left:4px solid var(--error-color)}.v070-health.warning{border-left:4px solid var(--warning-color,#f6a821)}.v070-health.healthy{border-left:4px solid var(--success-color,#43a047)}.v070-findings{display:grid;gap:8px}.v070-finding{display:flex;flex-direction:column;gap:2px}.v070-linked{font-size:11px;font-weight:600;opacity:.75;margin-right:6px;white-space:nowrap}.setting-main{gap:14px}.setting-title{font-size:15px}.setting-row.v070-highlight{outline:2px solid var(--primary-color);outline-offset:-2px;border-radius:10px}@media(max-width:700px){.v070-linked{display:block}.setting-title{font-size:16px}}</style>${scenarioHtml}${this._v070HealthPanel()}`;
    return html.replace("<h2>Instellingen</h2>", enhancedHeading);
  };

  proto._bindEvents = function () {
    if (originalBindEventsV070) originalBindEventsV070.call(this);
    this.shadowRoot.querySelectorAll(".v070-show-settings").forEach((button) => {
      button.onclick = () => {
        const scenario = SCENARIO_DEFS_V070.find((item)=>item.key === button.dataset.scenario);
        if (!scenario) return;
        this.shadowRoot.querySelectorAll(".setting-row.v070-highlight").forEach((row)=>row.classList.remove("v070-highlight"));
        let first = null;
        scenario.settings.forEach((key) => {
          const row = this.shadowRoot.querySelector(`.setting-row[data-setting-key="${key}"]`);
          if (!row) return;
          row.classList.add("v070-highlight");
          const details = row.closest("details"); if (details) details.open = true;
          if (!first) first = row;
        });
        if (first) first.scrollIntoView({behavior:"smooth",block:"center"});
      };
    });
  };
}
