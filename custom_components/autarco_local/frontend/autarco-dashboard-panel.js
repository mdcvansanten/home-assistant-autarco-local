const TABS = [
  ["overview", "Overzicht", "mdi:view-dashboard-outline"],
  ["pv", "PV", "mdi:solar-power"],
  ["battery", "Batterij", "mdi:battery-high"],
  ["diagnostics", "Diagnose", "mdi:stethoscope"],
  ["settings", "Instellingen", "mdi:cog-outline"]
];

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
      ["force_charge_power_limit", "Force-charge power limit", "Vermogenslimiet voor force-charge gedrag. Mapping en schaal blijven nog gelockt."],
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
      [null, "Meter type", "Selecteert het gebruikte metertype. Verkeerd instellen kan vermogensmetingen ongeldig maken."],
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
  connection: ["_connection"],
  pv_power: ["_pv_power"],
  battery_soc: ["_battery_soc"],
  battery_power: ["_battery_power"],
  grid_power: ["_grid_power"],
  house_load_power: ["_house_load_power"],
  temperature: ["_temperature"],
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

const RELATIONS = {
  reserve_soc: "Effect-afhankelijkheid: deze waarde is actief wanneer Reserve battery mode AAN staat. Local policy: Reserve SOC ≥ Minimum battery SOC.",
  self_use_mode: "Work-mode relatie: Self-use, Feed-in Priority, Peak Shaving en Off-grid worden als gekoppelde bedrijfsstate behandeld.",
  time_of_use_mode: "Parent mode voor laad-/ontlaadstromen en tijdsloten. Die child-instellingen hebben pas effect wanneer Time-of-use AAN staat.",
  reserve_battery_mode: "Parent mode voor Reserve SOC en het bijbehorende reservegedrag.",
  feed_in_priority_mode: "Work-mode relatie: Feed-in Priority is geen onafhankelijk los bit naast Self-use.",
  minimum_battery_soc: "Safety-relatie: samen beoordelen met Force-charge SOC, overdischarge-hysterese en ECO/herstelgedrag.",
  force_charge_soc: "Effect-relatie: samen beoordelen met Allow Grid Charging en Minimum battery SOC.",
  force_charge_power_limit: "Nog niet schrijfbaar: register/scaling is nog niet voldoende bewezen.",
  off_grid_mode: "Hoofd-work-mode. Een tijdelijke activatie kan andere mode-state beïnvloeden; daarom wordt de complete oorspronkelijke state bewaard.",
  allow_grid_charging: "Effect-relatie met Force-charge, Battery Reserve en tijdgestuurd netladen.",
  off_grid_minimum_soc: "Write + effect dependency: Off-grid moet actief zijn om deze setting op de huidige hardware te wijzigen.",
  scheduled_charge_current: "Effect-afhankelijkheid: alleen functioneel bij Time-of-use AAN en begrensd door inverter/BMS-capabilities.",
  scheduled_discharge_current: "Effect-afhankelijkheid: alleen functioneel bij Time-of-use AAN en begrensd door inverter/BMS-capabilities."
};

class AutarcoDashboardPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._activeTab = "overview";
    this._unlockOpen = false;
    this._unlockBusy = false;
    this._unlockError = "";
    this._unlockedUntil = 0;
    this._preflightOpen = false;
    this._writeBusy = false;
    this._writeMessage = null;
    this._timer = null;
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
    if (!this._timer) {
      this._timer = window.setInterval(() => {
        if (this._activeTab === "settings" && this._unlockedUntil > 0) {
          if (Date.now() >= this._unlockedUntil) this._unlockedUntil = 0;
          this.render();
        }
      }, 5000);
    }
    this.render();
  }

  disconnectedCallback() {
    if (this._timer) {
      window.clearInterval(this._timer);
      this._timer = null;
    }
  }

  _escape(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  _entities() {
    if (!this._hass || !this._hass.states) return [];
    return Object.values(this._hass.states).filter((entity) =>
      entity.entity_id.indexOf("autarco_local") !== -1
    );
  }

  _findState(key) {
    if (!key) return null;
    const aliases = ALIASES[key] || [];
    const states = this._entities();
    for (const entity of states) {
      for (const suffix of aliases) {
        if (entity.entity_id.endsWith(suffix)) return entity;
      }
    }
    return null;
  }

  _formatState(entity) {
    if (!entity) return "Niet beschikbaar";
    const state = String(entity.state);
    if (["unknown", "unavailable", "none"].indexOf(state.toLowerCase()) !== -1) {
      return "Niet beschikbaar";
    }
    const unit = entity.attributes && entity.attributes.unit_of_measurement;
    return unit ? state + " " + unit : state;
  }

  _friendlyName(entity) {
    if (!entity) return "Onbekend";
    return (entity.attributes && entity.attributes.friendly_name) || entity.entity_id;
  }

  _number(key) {
    const entity = this._findState(key);
    if (!entity) return null;
    const parsed = Number.parseFloat(String(entity.state).replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }

  _isOn(key) {
    const entity = this._findState(key);
    const state = entity ? String(entity.state).trim().toLowerCase() : "";
    return ["on", "aan", "true", "1"].indexOf(state) !== -1;
  }

  _serviceAvailable(name) {
    return Boolean(
      this._hass &&
      this._hass.services &&
      this._hass.services.autarco_local &&
      this._hass.services.autarco_local[name]
    );
  }

  _isUnlocked() {
    return this._unlockedUntil > Date.now();
  }

  _remainingUnlock() {
    if (!this._isUnlocked()) return "00:00";
    const seconds = Math.max(0, Math.floor((this._unlockedUntil - Date.now()) / 1000));
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return String(minutes).padStart(2, "0") + ":" + String(rest).padStart(2, "0");
  }

  _statusCard(label, key) {
    const entity = this._findState(key);
    return `
      <div class="metric-card">
        <span>${this._escape(label)}</span>
        <strong>${this._escape(this._formatState(entity))}</strong>
      </div>`;
  }

  _overview() {
    return `
      <section class="content-section">
        <h2>Overzicht</h2>
        <p class="muted">Live samenvatting van de Autarco-installatie. De verdere dashboardtabs kunnen we vanaf deze basis gericht uitbreiden.</p>
        <div class="metrics">
          ${this._statusCard("PV-vermogen", "pv_power")}
          ${this._statusCard("Batterij-SOC", "battery_soc")}
          ${this._statusCard("Batterijvermogen", "battery_power")}
          ${this._statusCard("Netvermogen", "grid_power")}
          ${this._statusCard("Huisverbruik", "house_load_power")}
          ${this._statusCard("Omvormertemperatuur", "temperature")}
        </div>
      </section>`;
  }

  _entityList(filterWords, emptyText) {
    const words = filterWords.map((word) => word.toLowerCase());
    const matches = this._entities().filter((entity) => {
      const haystack = (entity.entity_id + " " + this._friendlyName(entity)).toLowerCase();
      return words.some((word) => haystack.indexOf(word) !== -1);
    });
    if (!matches.length) return `<div class="empty">${this._escape(emptyText)}</div>`;
    matches.sort((a, b) => this._friendlyName(a).localeCompare(this._friendlyName(b)));
    return `<div class="entity-grid">${matches.map((entity) => `
      <div class="entity-card">
        <span>${this._escape(this._friendlyName(entity))}</span>
        <strong>${this._escape(this._formatState(entity))}</strong>
      </div>`).join("")}</div>`;
  }

  _pv() {
    return `<section class="content-section"><h2>PV</h2><p class="muted">PV- en MPPT-metingen uit Autarco Local.</p>${this._entityList(["pv", "solar"], "Geen PV-entiteiten gevonden.")}</section>`;
  }

  _battery() {
    return `<section class="content-section"><h2>Batterij</h2><p class="muted">Batterijstatus en batterijmetingen.</p>${this._entityList(["battery", "batterij", "soc"], "Geen batterij-entiteiten gevonden.")}</section>`;
  }

  _diagnostics() {
    return `<section class="content-section"><h2>Diagnose</h2><p class="muted">Verbinding, polling, retries en beschikbaarheidsinformatie.</p>${this._entityList(["retry", "retries", "poll", "connect", "disconnect", "uptime", "downtime", "availability", "beschikbaarheid", "health", "gezondheid", "response"], "Geen diagnose-entiteiten gevonden.")}</section>`;
  }

  _relation(key) {
    const relation = RELATIONS[key];
    if (!relation) return "";
    return `<div class="relation">↳ ${this._escape(relation)}</div>`;
  }

  _offGridControls(entity) {
    const current = this._number("off_grid_minimum_soc");
    const writeAvailable = this._serviceAvailable("set_off_grid_minimum_soc");
    if (current === 20) {
      return `<div class="value verified">✓ ${this._escape(this._formatState(entity))}</div>`;
    }
    if (current === 10 && writeAvailable && this._isUnlocked()) {
      return `<div class="controls"><div class="value">${this._escape(this._formatState(entity))}</div><button class="primary small" data-action="open-preflight">Wijzigen</button></div>`;
    }
    const lockText = this._isUnlocked() ? "Pilot ondersteunt alleen 10% → 20%." : "Ontgrendel instellingen om te wijzigen.";
    return `<div class="controls" title="${this._escape(lockText)}"><div class="value locked">🔒 ${this._escape(this._formatState(entity))}</div></div>`;
  }

  _settingRow(item, group) {
    const key = item[0];
    const label = item[1];
    const description = item[2];
    const entity = key ? this._findState(key) : null;
    const installerLocked = group.id === "installer";
    const mappingLocked = key === "force_charge_power_limit";
    let control;
    if (key === "off_grid_minimum_soc") {
      control = this._offGridControls(entity);
    } else {
      const locked = installerLocked || mappingLocked || group.id !== "standard";
      control = `<div class="value ${locked ? "locked" : ""}">${locked ? "🔒 " : ""}${this._escape(key ? this._formatState(entity) : "Niet gemapt")}</div>`;
    }
    const message = key === "off_grid_minimum_soc" && this._writeMessage
      ? `<div class="write-message ${this._escape(this._writeMessage.type)}">${this._escape(this._writeMessage.text)}</div>`
      : "";
    return `
      <div class="setting-row">
        <div class="setting-main">
          <div class="setting-title"><span class="dot ${group.dot}"></span><span>${this._escape(label)}</span></div>
          ${control}
        </div>
        <div class="description">${this._escape(description)}</div>
        ${this._relation(key)}
        ${message}
      </div>`;
  }

  _settingsGroup(group) {
    return `
      <details class="group" ${group.open ? "open" : ""}>
        <summary><span class="dot ${group.dot}"></span>${this._escape(group.title)}<span class="chevron">⌄</span></summary>
        <div class="rows">${group.items.map((item) => this._settingRow(item, group)).join("")}</div>
      </details>`;
  }

  _lockBar() {
    if (this._isUnlocked()) {
      return `
        <div class="lockbar unlocked">
          <div><strong>🔓 Instellingen ontgrendeld</strong><span>Nog ${this._remainingUnlock()} beschikbaar. Expert-writes vragen daarnaast altijd een preflight.</span></div>
          <button class="secondary" data-action="lock-settings">Nu vergrendelen</button>
        </div>`;
    }
    return `
      <div class="lockbar lockedbar">
        <div><strong>🔒 Instellingen vergrendeld</strong><span>Alle waarden blijven zichtbaar. Ontgrendel met je PIN om toegestane wijzigingen uit te voeren.</span></div>
        <button class="primary" data-action="open-unlock">Ontgrendelen</button>
      </div>`;
  }

  _settings() {
    return `
      <section class="content-section settings-section">
        <h2>Instellingen</h2>
        <p class="muted">Dezelfde groen/geel/rood-indeling als voorheen, nu als tab in Autarco Local. De originele Home Assistant Configureren-route blijft als fallback beschikbaar.</p>
        ${this._lockBar()}
        ${GROUPS.map((group) => this._settingsGroup(group)).join("")}
        <details class="group dependencies">
          <summary>🧭 Onderlinge afhankelijkheden<span class="chevron">⌄</span></summary>
          <div class="dependency-list">
            <div><strong>Work modes</strong><span>Self-use, Feed-in Priority, Peak Shaving en Off-grid worden als gekoppelde bedrijfsstate behandeld.</span></div>
            <div><strong>Off-grid minimum SOC</strong><span>Off-grid actief is een write-prerequisite op de huidige hardware. Als Off-grid al AAN staat blijft hij AAN.</span></div>
            <div><strong>Time of Use</strong><span>Laad-/ontlaadtijden en geplande stromen hebben pas effect wanneer Time-of-use AAN staat.</span></div>
            <div><strong>Reserve SOC</strong><span>Heeft effect wanneer Battery Reserve AAN staat; Reserve SOC blijft minimaal gelijk aan Minimum battery SOC.</span></div>
            <div><strong>Force-charge SOC</strong><span>Samen beoordelen met Allow Grid Charging en Minimum battery SOC.</span></div>
            <div><strong>Meter / CT / grid-code</strong><span>Hardware- en safety-prerequisites voor export-, peak- en netfuncties; blijven Installer/read-only.</span></div>
          </div>
        </details>
      </section>`;
  }

  _unlockDialog() {
    if (!this._unlockOpen) return "";
    return `
      <div class="backdrop">
        <div class="dialog" role="dialog" aria-modal="true">
          <h3>Instellingen ontgrendelen</h3>
          <p>Voer de Autarco Local-instellingen-PIN in. De backend ontgrendelt writes voor deze ingelogde Home Assistant-gebruiker gedurende 10 minuten.</p>
          <input id="unlock-pin" class="pin" type="password" inputmode="numeric" maxlength="8" autocomplete="off" placeholder="PIN">
          ${this._unlockError ? `<div class="dialog-error">${this._escape(this._unlockError)}</div>` : ""}
          <div class="dialog-actions">
            <button class="secondary" data-action="cancel-unlock" ${this._unlockBusy ? "disabled" : ""}>Annuleren</button>
            <button class="primary" data-action="submit-unlock" ${this._unlockBusy ? "disabled" : ""}>${this._unlockBusy ? "Controleren…" : "Ontgrendelen"}</button>
          </div>
          <p class="hint">Nog geen PIN? Stel hem in via Instellingen → Apparaten & diensten → Autarco Local → Configureren.</p>
        </div>
      </div>`;
  }

  _preflight() {
    if (!this._preflightOpen) return "";
    const current = this._number("off_grid_minimum_soc");
    const batterySoc = this._number("battery_soc");
    const offGridOn = this._isOn("off_grid_mode");
    const selfUse = this._formatState(this._findState("self_use_mode"));
    const offGrid = this._formatState(this._findState("off_grid_mode"));
    const minimum = this._formatState(this._findState("minimum_battery_soc"));
    const force = this._formatState(this._findState("force_charge_soc"));
    const gridCharging = this._formatState(this._findState("allow_grid_charging"));
    const battery = this._formatState(this._findState("battery_soc"));
    const temporary = !offGridOn;
    const safe = !temporary || (batterySoc !== null && batterySoc >= 30);
    const canExecute = this._isUnlocked() && safe && current === 10 && !this._writeBusy;
    const dependency = offGridOn
      ? "Off-grid staat al AAN. Autarco Local verandert deze mode niet; hij blijft na de SOC-wijziging AAN."
      : "Voor deze instelling moet Off-grid tijdelijk actief zijn. Autarco Local bewaart de complete work-mode, activeert Off-grid voor de write en herstelt daarna de oorspronkelijke state.";
    const safety = !temporary
      ? "Geen tijdelijke modewissel nodig."
      : batterySoc === null
        ? "Geblokkeerd: batterij-SOC is niet betrouwbaar beschikbaar."
        : batterySoc < 30
          ? "Geblokkeerd: batterij-SOC is " + batterySoc + "%. Voor deze pilot is minimaal 30% vereist voor tijdelijke Off-grid-activatie."
          : "Batterij-SOC is " + batterySoc + "%. De 30%-pilotgrens is gehaald.";
    return `
      <div class="backdrop">
        <div class="dialog wide" role="dialog" aria-modal="true">
          <div class="dialog-head"><div><div class="eyebrow">🟡 Expert-wijziging</div><h3>Wijziging controleren</h3></div><button class="close" data-action="cancel-preflight" ${this._writeBusy ? "disabled" : ""}>×</button></div>
          <div class="target"><span>Off-grid minimum SOC</span><strong>${current == null ? "?" : this._escape(current)}% → 20%</strong></div>
          <h4>Huidige situatie</h4>
          <div class="pregrid">
            <div><span>Self-use</span><strong>${this._escape(selfUse)}</strong></div>
            <div><span>Off-grid</span><strong>${this._escape(offGrid)}</strong></div>
            <div><span>Minimum SOC</span><strong>${this._escape(minimum)}</strong></div>
            <div><span>Force-charge SOC</span><strong>${this._escape(force)}</strong></div>
            <div><span>Laden vanuit net</span><strong>${this._escape(gridCharging)}</strong></div>
            <div><span>Batterij SOC</span><strong>${this._escape(battery)}</strong></div>
          </div>
          <h4>Afhankelijkheid</h4><div class="callout">${this._escape(dependency)}</div><div class="callout ${safe ? "ok" : "bad"}">${this._escape(safety)}</div>
          <h4>Autarco Local zal</h4>
          <ol>
            <li>Een verse settings-read uitvoeren.</li>
            <li>De oorspronkelijke complete work-mode vastleggen.</li>
            <li>${offGridOn ? "Off-grid ongemoeid laten omdat deze al actief is." : "Off-grid tijdelijk activeren en dit via read-back bevestigen."}</li>
            <li>Off-grid minimum SOC naar 20% schrijven en teruglezen.</li>
            <li>${offGridOn ? "Off-grid AAN laten." : "De oorspronkelijke work-mode herstellen en teruglezen."}</li>
            <li>Stoppen bij een onverwachte externe modewijziging in plaats van blind te overschrijven.</li>
          </ol>
          <label class="confirm"><input id="confirm-write" type="checkbox" ${canExecute ? "" : "disabled"}><span>Ik bevestig deze wijziging en de hierboven beschreven tijdelijke mode-afhandeling.</span></label>
          <div class="dialog-actions"><button class="secondary" data-action="cancel-preflight" ${this._writeBusy ? "disabled" : ""}>Annuleren</button><button class="primary" data-action="confirm-write" disabled>${this._writeBusy ? "Bezig…" : "Bevestig wijziging"}</button></div>
        </div>
      </div>`;
  }

  async _unlock() {
    const input = this.shadowRoot.querySelector("#unlock-pin");
    const pin = input ? String(input.value || "").trim() : "";
    if (!pin) {
      this._unlockError = "Vul de PIN in.";
      this.render();
      return;
    }
    this._unlockBusy = true;
    this._unlockError = "";
    this.render();
    try {
      await this._hass.callService("autarco_local", "unlock_settings", { pin: pin });
      this._unlockedUntil = Date.now() + 10 * 60 * 1000;
      this._unlockOpen = false;
    } catch (error) {
      this._unlockError = (error && error.message) ? error.message : String(error);
    } finally {
      this._unlockBusy = false;
      this.render();
    }
  }

  async _lock() {
    try {
      await this._hass.callService("autarco_local", "lock_settings", {});
    } catch (error) {
      this._writeMessage = { type: "error", text: "Vergrendelen via backend gaf een fout: " + ((error && error.message) ? error.message : String(error)) };
    }
    this._unlockedUntil = 0;
    this._preflightOpen = false;
    this.render();
  }

  async _performWrite() {
    if (this._writeBusy || !this._isUnlocked()) return;
    this._writeBusy = true;
    this._writeMessage = { type: "progress", text: "Write gestart: pre-read, dependency-check, write, read-back en eventueel herstel worden uitgevoerd." };
    this.render();
    try {
      await this._hass.callService("autarco_local", "set_off_grid_minimum_soc", { soc: 20, confirm: true });
      this._writeMessage = { type: "success", text: "Wijziging bevestigd. SOC en work-mode state zijn door de backend gecontroleerd." };
      this._preflightOpen = false;
    } catch (error) {
      this._writeMessage = { type: "error", text: "Write mislukt of afgebroken: " + ((error && error.message) ? error.message : String(error)) };
    } finally {
      this._writeBusy = false;
      this.render();
    }
  }

  _bindEvents() {
    this.shadowRoot.querySelectorAll("[data-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        this._activeTab = button.getAttribute("data-tab") || "overview";
        this.render();
      });
    });
    const openUnlock = this.shadowRoot.querySelector('[data-action="open-unlock"]');
    if (openUnlock) openUnlock.addEventListener("click", () => { this._unlockOpen = true; this._unlockError = ""; this.render(); });
    const cancelUnlock = this.shadowRoot.querySelector('[data-action="cancel-unlock"]');
    if (cancelUnlock) cancelUnlock.addEventListener("click", () => { if (!this._unlockBusy) { this._unlockOpen = false; this.render(); } });
    const submitUnlock = this.shadowRoot.querySelector('[data-action="submit-unlock"]');
    if (submitUnlock) submitUnlock.addEventListener("click", () => this._unlock());
    const pinInput = this.shadowRoot.querySelector("#unlock-pin");
    if (pinInput) pinInput.addEventListener("keydown", (event) => { if (event.key === "Enter") this._unlock(); });
    const lockButton = this.shadowRoot.querySelector('[data-action="lock-settings"]');
    if (lockButton) lockButton.addEventListener("click", () => this._lock());
    const openPreflight = this.shadowRoot.querySelector('[data-action="open-preflight"]');
    if (openPreflight) openPreflight.addEventListener("click", () => { this._preflightOpen = true; this._writeMessage = null; this.render(); });
    this.shadowRoot.querySelectorAll('[data-action="cancel-preflight"]').forEach((button) => button.addEventListener("click", () => { if (!this._writeBusy) { this._preflightOpen = false; this.render(); } }));
    const checkbox = this.shadowRoot.querySelector("#confirm-write");
    const confirmButton = this.shadowRoot.querySelector('[data-action="confirm-write"]');
    if (checkbox && confirmButton) {
      checkbox.addEventListener("change", () => { confirmButton.disabled = !checkbox.checked || this._writeBusy; });
      confirmButton.addEventListener("click", () => { if (checkbox.checked && !confirmButton.disabled) this._performWrite(); });
    }
  }

  _activeContent() {
    if (this._activeTab === "pv") return this._pv();
    if (this._activeTab === "battery") return this._battery();
    if (this._activeTab === "diagnostics") return this._diagnostics();
    if (this._activeTab === "settings") return this._settings();
    return this._overview();
  }

  render() {
    if (!this.shadowRoot) return;
    if (!this._hass) {
      this.shadowRoot.innerHTML = `<div style="padding:24px">Autarco Local wordt geladen…</div>`;
      return;
    }
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; min-height:100%; background:var(--primary-background-color); color:var(--primary-text-color); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
        * { box-sizing:border-box; }
        button,input { font:inherit; }
        button { cursor:pointer; }
        button:disabled { opacity:.5; cursor:not-allowed; }
        .shell { max-width:1180px; margin:0 auto; padding:18px 16px 42px; }
        .top { display:flex; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:14px; }
        .top h1 { margin:0; font-size:28px; }
        .top p { margin:5px 0 0; color:var(--secondary-text-color); }
        .tabs { display:flex; gap:6px; overflow:auto; border-bottom:1px solid var(--divider-color); margin-bottom:18px; }
        .tab { border:0; background:transparent; color:var(--secondary-text-color); padding:11px 14px; border-bottom:3px solid transparent; white-space:nowrap; font-weight:600; }
        .tab.active { color:var(--primary-color); border-bottom-color:var(--primary-color); }
        h2 { margin:0 0 6px; font-size:24px; }
        h3 { margin:0 0 10px; font-size:21px; }
        h4 { margin:18px 0 8px; }
        .muted,.hint { color:var(--secondary-text-color); line-height:1.5; }
        .metrics,.entity-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:10px; margin-top:16px; }
        .metric-card,.entity-card { background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:12px; padding:14px; display:flex; flex-direction:column; gap:8px; }
        .metric-card span,.entity-card span { color:var(--secondary-text-color); font-size:14px; }
        .metric-card strong,.entity-card strong { font-size:20px; }
        .empty { padding:18px; background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:12px; color:var(--secondary-text-color); }
        .lockbar { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:13px 14px; border:1px solid var(--divider-color); border-radius:12px; margin:16px 0; background:var(--card-background-color); }
        .lockbar div { display:flex; flex-direction:column; gap:4px; }
        .lockbar span { color:var(--secondary-text-color); font-size:14px; }
        .unlocked { border-color:var(--success-color,#2e7d32); }
        .primary,.secondary,.close { border:0; border-radius:9px; padding:9px 13px; font-weight:650; }
        .primary { background:var(--primary-color); color:white; }
        .secondary,.close { background:var(--secondary-background-color); color:var(--primary-text-color); }
        .small { padding:7px 10px; }
        .group { background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:12px; margin:10px 0; overflow:hidden; }
        summary { display:flex; align-items:center; gap:9px; padding:15px 16px; cursor:pointer; font-size:18px; font-weight:650; list-style:none; }
        summary::-webkit-details-marker { display:none; }
        .chevron { margin-left:auto; color:var(--secondary-text-color); }
        .rows { border-top:1px solid var(--divider-color); }
        .setting-row { padding:14px 16px; border-bottom:1px solid var(--divider-color); }
        .setting-row:last-child { border-bottom:0; }
        .setting-main { display:flex; align-items:center; justify-content:space-between; gap:16px; }
        .setting-title { display:flex; align-items:center; gap:9px; font-size:17px; font-weight:600; }
        .dot { width:13px; height:13px; border-radius:50%; flex:0 0 13px; }
        .green { background:#23c552; } .yellow { background:#ffcc00; } .red { background:#ef3e42; }
        .value { font-size:17px; font-weight:650; text-align:right; }
        .locked { color:var(--secondary-text-color); }
        .verified { color:var(--success-color,#2e7d32); }
        .controls { display:flex; align-items:center; gap:9px; }
        .description { margin:6px 0 0 22px; color:var(--secondary-text-color); line-height:1.45; }
        .relation { margin:7px 0 0 22px; padding:8px 10px; background:var(--secondary-background-color); border-radius:8px; color:var(--secondary-text-color); line-height:1.4; font-size:14px; }
        .write-message { margin:8px 0 0 22px; padding:9px 10px; border-radius:8px; background:var(--secondary-background-color); }
        .write-message.success { border-left:4px solid var(--success-color,#2e7d32); }
        .write-message.error { border-left:4px solid var(--error-color,#db4437); }
        .dependency-list { border-top:1px solid var(--divider-color); padding:8px 16px 14px; }
        .dependency-list>div { display:grid; grid-template-columns:190px 1fr; gap:14px; padding:10px 0; border-bottom:1px solid var(--divider-color); line-height:1.45; }
        .dependency-list>div:last-child { border-bottom:0; }
        .dependency-list span { color:var(--secondary-text-color); }
        .backdrop { position:fixed; inset:0; z-index:1000; background:rgba(0,0,0,.55); display:flex; align-items:flex-start; justify-content:center; overflow:auto; padding:30px 12px; }
        .dialog { width:min(470px,100%); background:var(--card-background-color); color:var(--primary-text-color); border-radius:14px; padding:18px; box-shadow:0 18px 50px rgba(0,0,0,.4); }
        .dialog.wide { width:min(760px,100%); }
        .dialog p { line-height:1.5; }
        .dialog-head { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
        .close { font-size:24px; width:38px; height:38px; padding:0; }
        .pin { width:100%; padding:11px 12px; border:1px solid var(--divider-color); border-radius:9px; background:var(--primary-background-color); color:var(--primary-text-color); font-size:18px; letter-spacing:.15em; }
        .dialog-error { margin-top:10px; padding:9px 10px; border-left:4px solid var(--error-color,#db4437); background:var(--secondary-background-color); }
        .dialog-actions { display:flex; justify-content:flex-end; gap:9px; margin-top:16px; }
        .eyebrow { color:var(--secondary-text-color); font-size:13px; font-weight:650; }
        .target { display:flex; align-items:center; justify-content:space-between; gap:12px; border:1px solid var(--divider-color); border-radius:10px; padding:12px; margin-top:14px; }
        .target span { color:var(--secondary-text-color); }
        .target strong { font-size:20px; }
        .pregrid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
        .pregrid>div { display:flex; justify-content:space-between; gap:10px; background:var(--secondary-background-color); border-radius:8px; padding:10px; }
        .callout { margin-top:8px; padding:10px 11px; background:var(--secondary-background-color); border-radius:8px; line-height:1.5; }
        .callout.ok { border-left:4px solid var(--success-color,#2e7d32); }
        .callout.bad { border-left:4px solid var(--error-color,#db4437); }
        ol { line-height:1.5; padding-left:23px; }
        .confirm { display:flex; gap:10px; align-items:flex-start; padding:11px; background:var(--secondary-background-color); border-radius:8px; margin-top:14px; line-height:1.45; }
        .confirm input { margin-top:3px; width:18px; height:18px; }
        @media (max-width:650px) {
          .shell { padding:12px 8px 30px; }
          .top h1 { font-size:24px; }
          .tab { padding:10px 11px; }
          .setting-main,.lockbar { align-items:flex-start; }
          .setting-main { flex-wrap:wrap; }
          .controls,.value { margin-left:22px; text-align:left; }
          .lockbar { flex-direction:column; }
          .lockbar button { width:100%; }
          .dependency-list>div { grid-template-columns:1fr; gap:3px; }
          .pregrid { grid-template-columns:1fr; }
          .backdrop { padding:10px 6px; }
          .dialog-actions { flex-direction:column-reverse; }
          .dialog-actions button { width:100%; }
        }
      </style>
      <div class="shell">
        <div class="top"><div><h1>Autarco Local</h1><p>Lokale monitoring, diagnose en veilige instellingen voor de thuisinstallatie.</p></div></div>
        <nav class="tabs">${TABS.map((tab) => `<button class="tab ${this._activeTab === tab[0] ? "active" : ""}" data-tab="${tab[0]}">${this._escape(tab[1])}</button>`).join("")}</nav>
        ${this._activeContent()}
      </div>
      ${this._unlockDialog()}
      ${this._preflight()}`;
    this._bindEvents();
  }
}

if (!customElements.get("autarco-local-dashboard-panel")) {
  customElements.define("autarco-local-dashboard-panel", AutarcoDashboardPanel);
}
