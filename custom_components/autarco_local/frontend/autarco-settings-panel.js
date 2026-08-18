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
  battery_soc: ["_battery_soc"],
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
  reserve_soc: "Effect-afhankelijkheid: deze reservewaarde is actief wanneer Reserve battery mode AAN staat. Local policy: Reserve SOC ≥ Minimum battery SOC.",
  self_use_mode: "Modus-afhankelijkheid: Self-use is een hoofd-work-mode. Activeren van Feed-in Priority, Peak Shaving of Off-grid kan Self-use uitschakelen.",
  time_of_use_mode: "Parent mode voor geplande laad-/ontlaadstromen en tijdsloten. Die child-instellingen hebben pas effect wanneer Time-of-use AAN staat.",
  reserve_battery_mode: "Parent mode voor Reserve SOC en het bijbehorende grid-reservegedrag.",
  feed_in_priority_mode: "Modus-afhankelijkheid: Feed-in Priority is een hoofd-work-mode en kan niet als onafhankelijk bit naast Self-use worden behandeld.",
  minimum_battery_soc: "Safety-relatie: samen beoordelen met Force-charge SOC, overdischarge-hysterese en ECO/herstelgedrag. Er is geen parent mode nodig voor de normale ontlaadondergrens.",
  force_charge_soc: "Effect-relatie: Force-charge SOC bepaalt de lage laadtrigger; grid charging bepaalt of netstroom daarvoor beschikbaar is. Vergelijk deze waarde altijd met Minimum battery SOC.",
  force_charge_power_limit: "🔒 Nog niet schrijfbaar. De huidige 43027-mapping/schaal is niet bewezen; Solis koppelt Max Grid Power when Force Charge aan de Peak Shaving-setting.",
  off_grid_mode: "Hoofd-work-mode. Tijdelijk activeren kan andere mode-state beïnvloeden; daarom bewaart Autarco Local de volledige work-mode state.",
  allow_grid_charging: "Effect-relatie met Force-charge, Battery Reserve en tijdgestuurd netladen: deze schakelaar bepaalt of laden vanuit het net is toegestaan.",
  off_grid_minimum_soc: "Write + effect dependency: Off-grid moet actief zijn om deze setting op de huidige hardware te wijzigen; de waarde is bedoeld voor off-gridbedrijf.",
  scheduled_charge_current: "Effect-afhankelijkheid: alleen functioneel bij Time-of-use AAN; daarnaast begrensd door inverter/BMS-capabilities.",
  scheduled_discharge_current: "Effect-afhankelijkheid: alleen functioneel bij Time-of-use AAN; daarnaast begrensd door inverter/BMS-capabilities.",
  charge_slot_1_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  charge_slot_1_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_1_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_1_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  charge_slot_2_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  charge_slot_2_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_2_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_2_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  charge_slot_3_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  charge_slot_3_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_3_start: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat.",
  discharge_slot_3_end: "Effect-afhankelijkheid: tijdslot is actief wanneer Time-of-use AAN staat."
};

class AutarcoSettingsPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._preflightOpen = false;
    this._writeBusy = false;
    this._writeMessage = null;
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

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
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

  _number(key) {
    const entity = this._findState(key);
    if (!entity || ["unknown", "unavailable", "none"].includes(entity.state)) return null;
    const parsed = Number.parseFloat(String(entity.state).replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }

  _isOn(key) {
    const state = String(this._findState(key)?.state ?? "").trim().toLowerCase();
    return ["on", "aan", "true", "1"].includes(state);
  }

  _serviceAvailable() {
    return Boolean(this._hass?.services?.autarco_local?.set_off_grid_minimum_soc);
  }

  _relation(key) {
    const relation = RELATIONS[key];
    if (!relation) return "";
    return `<div class="setting-relation"><span class="relation-icon">↳</span>${this._escape(relation)}</div>`;
  }

  _offGridControls(entity) {
    const current = this._number("off_grid_minimum_soc");
    const serviceAvailable = this._serviceAvailable();

    if (current === 10 && serviceAvailable) {
      return `
        <div class="setting-controls">
          <div class="setting-value">${this._escape(this._formatState(entity))}</div>
          <button class="edit-button" data-action="open-offgrid-preflight" ${this._writeBusy ? "disabled" : ""}>Wijzigen</button>
        </div>`;
    }
    if (current === 20) {
      return `
        <div class="setting-controls">
          <div class="setting-value verified"><span class="check">✓</span>${this._escape(this._formatState(entity))}</div>
        </div>`;
    }

    const reason = !serviceAvailable
      ? "Write-service is niet geladen; herstart Home Assistant na installatie van v0.6.4."
      : "De huidige pilot ondersteunt uitsluitend 10% → 20%.";
    return `
      <div class="setting-controls" title="${this._escape(reason)}">
        <div class="setting-value locked"><span class="lock">🔒</span>${this._escape(this._formatState(entity))}</div>
      </div>`;
  }

  _row(item, group) {
    const [key, label, description] = item;
    const entity = key ? this._findState(key) : null;
    const value = key ? this._formatState(entity) : "Niet gemapt";
    const installerLocked = group.id === "installer";
    const mappingLocked = key === "force_charge_power_limit";
    const locked = installerLocked || mappingLocked;

    const controls = key === "off_grid_minimum_soc"
      ? this._offGridControls(entity)
      : `<div class="setting-value ${locked ? "locked" : ""}" title="${locked ? "Read-only" : "Huidige waarde"}">
          ${locked ? '<span class="lock">🔒</span>' : ""}${this._escape(value)}
        </div>`;

    const writeMessage = key === "off_grid_minimum_soc" && this._writeMessage
      ? `<div class="write-message ${this._escape(this._writeMessage.type)}">${this._escape(this._writeMessage.text)}</div>`
      : "";

    return `
      <div class="setting-row ${key === "off_grid_minimum_soc" ? "write-candidate" : ""}">
        <div class="setting-main">
          <div class="setting-name-wrap">
            <span class="dot ${group.dot}" aria-hidden="true"></span>
            <span class="setting-name">${this._escape(label)}</span>
          </div>
          ${controls}
        </div>
        <div class="setting-description">${this._escape(description)}</div>
        ${this._relation(key)}
        ${writeMessage}
      </div>`;
  }

  _group(group) {
    return `
      <details class="group" ${group.open ? "open" : ""}>
        <summary>
          <span class="dot ${group.dot}" aria-hidden="true"></span>
          <span>${this._escape(group.title)}</span>
        </summary>
        <div class="rows">${group.items.map((item) => this._row(item, group)).join("")}</div>
      </details>`;
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

    const temporaryModeNeeded = !offGridOn;
    const batterySafe = !temporaryModeNeeded || (batterySoc !== null && batterySoc >= 30);
    const correctSource = current === 10;
    const canExecute = batterySafe && correctSource && this._serviceAvailable() && !this._writeBusy;

    const dependencyText = offGridOn
      ? "Off-grid staat al AAN. Autarco Local verandert deze mode niet; hij blijft na de SOC-wijziging AAN."
      : "Voor deze instelling moet Off-grid tijdelijk actief zijn. Autarco Local bewaart eerst de volledige work-mode state, activeert Off-grid alleen voor de write en herstelt daarna exact de oorspronkelijke state.";

    const safetyText = !temporaryModeNeeded
      ? "Geen tijdelijke modewissel nodig."
      : batterySoc === null
        ? "Pilot geblokkeerd: batterij-SOC is niet betrouwbaar beschikbaar."
        : batterySoc < 30
          ? `Pilot geblokkeerd: batterij-SOC is ${batterySoc}%. Voor deze eerste automatische modewissel hanteert Autarco Local minimaal 30%.`
          : `Batterij-SOC is ${batterySoc}%. De 30%-veiligheidsgrens voor deze eerste pilot is gehaald.`;

    const expectedOffGrid = offGridOn ? "AAN (blijft zoals vooraf)" : "UIT (oorspronkelijke toestand hersteld)";

    return `
      <div class="preflight-backdrop" role="presentation">
        <section class="preflight" role="dialog" aria-modal="true" aria-labelledby="preflight-title">
          <div class="preflight-head">
            <div>
              <div class="eyebrow">🟡 Expert-wijziging</div>
              <h2 id="preflight-title">Wijziging controleren</h2>
            </div>
            <button class="icon-button" data-action="cancel-offgrid-preflight" aria-label="Sluiten" ${this._writeBusy ? "disabled" : ""}>×</button>
          </div>

          <div class="target-change">
            <span>Off-grid minimum SOC</span>
            <strong>${current === null ? "?" : this._escape(current)}% <span class="arrow">→</span> 20%</strong>
          </div>

          <h3>Huidige situatie</h3>
          <div class="preflight-grid">
            <div><span>Self-use</span><strong>${this._escape(selfUse)}</strong></div>
            <div><span>Off-grid</span><strong>${this._escape(offGrid)}</strong></div>
            <div><span>Minimum SOC</span><strong>${this._escape(minimum)}</strong></div>
            <div><span>Force-charge SOC</span><strong>${this._escape(force)}</strong></div>
            <div><span>Laden vanuit net</span><strong>${this._escape(gridCharging)}</strong></div>
            <div><span>Batterij SOC</span><strong>${this._escape(battery)}</strong></div>
          </div>

          <h3>Afhankelijkheid</h3>
          <div class="dependency-callout">${this._escape(dependencyText)}</div>
          <div class="safety-callout ${batterySafe ? "ok" : "blocked"}">${this._escape(safetyText)}</div>

          <h3>Autarco Local zal</h3>
          <ol class="steps">
            <li>Een verse read doen van de target- en work-mode-settings.</li>
            <li>De volledige oorspronkelijke work-mode state vastleggen.</li>
            <li>${offGridOn ? "Off-grid ongemoeid laten, omdat deze al actief is." : "Off-grid tijdelijk activeren en de activatie via read-back bevestigen."}</li>
            <li>Off-grid minimum SOC schrijven naar 20% en via read-back bevestigen.</li>
            <li>${offGridOn ? "Off-grid AAN laten; er wordt geen restore uitgevoerd." : "De volledige oorspronkelijke work-mode state herstellen en opnieuw via read-back bevestigen."}</li>
            <li>Bij een onverwachte externe modewijziging stoppen in plaats van die wijziging blind te overschrijven.</li>
          </ol>

          <h3>Verwachte eindtoestand</h3>
          <div class="preflight-grid expected">
            <div><span>Self-use</span><strong>zelfde als vooraf (${this._escape(selfUse)})</strong></div>
            <div><span>Off-grid</span><strong>${this._escape(expectedOffGrid)}</strong></div>
            <div><span>Off-grid minimum SOC</span><strong>20%</strong></div>
            <div><span>Minimum / Force-charge SOC</span><strong>ongewijzigd</strong></div>
          </div>

          <label class="confirm-line ${canExecute ? "" : "disabled"}">
            <input id="expert-confirm" type="checkbox" ${canExecute ? "" : "disabled"}>
            <span>${offGridOn
              ? "Ik bevestig de wijziging naar 20% en begrijp dat de bestaande Off-grid mode AAN blijft."
              : "Ik bevestig de wijziging naar 20% en begrijp dat Off-grid hiervoor kort tijdelijk geactiveerd kan worden en daarna moet worden hersteld."}</span>
          </label>

          <div class="preflight-actions">
            <button class="secondary-button" data-action="cancel-offgrid-preflight" ${this._writeBusy ? "disabled" : ""}>Annuleren</button>
            <button class="primary-button" data-action="confirm-offgrid-write" disabled>
              ${this._writeBusy ? "Bezig met schrijven…" : "Bevestig wijziging"}
            </button>
          </div>
        </section>
      </div>`;
  }

  _dependencyOverview() {
    return `
      <details class="group dependencies">
        <summary>🧭 <span>Onderlinge afhankelijkheden</span></summary>
        <div class="dependency-list">
          <div><strong>Work modes</strong><span>Self-use, Feed-in Priority, Peak Shaving en Off-grid zijn geen losse onafhankelijke schakelaars. Modewissels moeten als één state-transactie worden behandeld.</span></div>
          <div><strong>Off-grid minimum SOC</strong><span>Write/effect: Off-grid actief. Op jouw hardware is de write-prerequisite praktisch bevestigd.</span></div>
          <div><strong>Time-of-use schema</strong><span>Laad-/ontlaadtijden en geplande stromen hebben effect wanneer Time-of-use AAN staat.</span></div>
          <div><strong>Reserve SOC</strong><span>Heeft effect wanneer Battery Reserve AAN staat; Local policy bewaakt Reserve SOC ≥ Minimum SOC.</span></div>
          <div><strong>Force-charge SOC</strong><span>Samen beoordelen met Allow Grid Charging en Minimum battery SOC.</span></div>
          <div><strong>Force-charge power limit</strong><span>Blijft locked: 43027 is nog niet gevalideerd en Solis koppelt de overeenkomstige functie aan Peak Shaving.</span></div>
          <div><strong>Peak Shaving</strong><span>Vereist een lithiumbatterij met communicatie; bruikbaar netvermogen, baseline SOC en grid charging vormen samen één regelset.</span></div>
          <div><strong>Meter / CT / grid-code</strong><span>Hardware- en veiligheidsprerequisites voor export-, peak- en netfuncties. Deze Installer/systeminstellingen blijven read-only.</span></div>
        </div>
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
          <div><span>Reserve SOC</span><strong>${this._escape(this._formatState(reserve))}</strong></div>
          <div><span>Minimum battery SOC</span><strong>${this._escape(this._formatState(minimum))}</strong></div>
          <div><span>Force-charge SOC</span><strong>${this._escape(this._formatState(force))}</strong></div>
          <div><span>Minimum-SOC off-grid</span><strong>${this._escape(this._formatState(offgrid))}</strong></div>
        </div>
        <div class="notice success-note">
          <strong>Dependency-aware writepilot beschikbaar.</strong>
          Alleen Minimum-SOC off-grid 10% → 20% kan vanuit dit scherm worden gewijzigd. De eerdere directe write bleef op 10%; de nieuwe route verwerkt eerst de hardware-afhankelijkheid met Off-grid mode en bewaart de oorspronkelijke work-mode state.
        </div>
        <div class="notice warning">
          <strong>Geen uitbreiding naar andere writes.</strong>
          De afhankelijkheden van andere settings worden al getoond, maar automatische parent-mode wijzigingen blijven geblokkeerd totdat hun exacte write-volgorde op deze Autarco-hardware is gevalideerd.
        </div>
        <div class="notice rule"><strong>Harde backendregel:</strong> Reserve SOC ≥ Minimum battery SOC.</div>
      </details>`;
  }

  async _performOffGridWrite() {
    if (this._writeBusy) return;
    this._writeBusy = true;
    this._writeMessage = {
      type: "progress",
      text: "Write gestart: pre-read, dependency-check, write, read-back en eventueel herstel worden uitgevoerd."
    };
    this.render();

    try {
      await this._hass.callService(
        "autarco_local",
        "set_off_grid_minimum_soc",
        { soc: 20, confirm: true }
      );
      this._writeMessage = {
        type: "success",
        text: "Wijziging bevestigd. De backend heeft de SOC-write en de vereiste mode-state gecontroleerd."
      };
      this._preflightOpen = false;
    } catch (error) {
      const message = error?.message || error?.body?.message || String(error);
      this._writeMessage = {
        type: "error",
        text: `Write mislukt of afgebroken: ${message}`
      };
    } finally {
      this._writeBusy = false;
      this.render();
    }
  }

  _bindEvents() {
    const open = this.shadowRoot.querySelector('[data-action="open-offgrid-preflight"]');
    if (open) {
      open.addEventListener("click", () => {
        this._preflightOpen = true;
        this._writeMessage = null;
        this.render();
      });
    }

    this.shadowRoot.querySelectorAll('[data-action="cancel-offgrid-preflight"]').forEach((button) => {
      button.addEventListener("click", () => {
        if (this._writeBusy) return;
        this._preflightOpen = false;
        this.render();
      });
    });

    const checkbox = this.shadowRoot.querySelector("#expert-confirm");
    const confirmButton = this.shadowRoot.querySelector('[data-action="confirm-offgrid-write"]');
    if (checkbox && confirmButton) {
      checkbox.addEventListener("change", () => {
        confirmButton.disabled = !checkbox.checked || this._writeBusy;
      });
      confirmButton.addEventListener("click", () => {
        if (!checkbox.checked || confirmButton.disabled) return;
        this._performOffGridWrite();
      });
    }
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
        button, input { font: inherit; }
        .page { max-width: 980px; margin: 0 auto; padding: 22px 18px 44px; }
        .header { margin-bottom: 18px; }
        h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; font-weight: 650; }
        h2 { font-size: 24px; margin: 2px 0 0; }
        h3 { font-size: 16px; margin: 20px 0 9px; }
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
        .write-candidate { background: color-mix(in srgb, var(--warning-color, #ff9800) 5%, var(--card-background-color)); }
        .setting-main { display: flex; align-items: center; gap: 16px; justify-content: space-between; }
        .setting-name-wrap { display: flex; align-items: center; gap: 10px; min-width: 0; }
        .setting-name { font-size: 18px; line-height: 1.3; font-weight: 600; }
        .setting-controls { display: flex; align-items: center; gap: 10px; flex: 0 0 auto; }
        .setting-value { flex: 0 0 auto; min-width: 110px; text-align: right; font-size: 18px; font-weight: 600; line-height: 1.3; font-variant-numeric: tabular-nums; }
        .setting-value.locked { color: var(--secondary-text-color); }
        .setting-value.verified { color: var(--success-color, #2e7d32); }
        .lock { font-size: 13px; margin-right: 6px; opacity: .8; }
        .check { margin-right: 6px; }
        .setting-description { margin-top: 7px; padding-left: 24px; color: var(--secondary-text-color); font-size: 15.5px; line-height: 1.45; }
        .setting-relation { margin-top: 7px; margin-left: 24px; padding: 8px 10px; border-radius: 8px; background: var(--secondary-background-color); color: var(--secondary-text-color); font-size: 14.5px; line-height: 1.4; }
        .relation-icon { margin-right: 7px; font-weight: 700; }
        .dot { display: inline-block; width: 14px; height: 14px; min-width: 14px; border-radius: 50%; box-shadow: inset 0 0 0 1px rgba(255,255,255,.2), 0 1px 2px rgba(0,0,0,.25); }
        .green { background: #23c552; }
        .yellow { background: #ffcc00; }
        .red { background: #ef3e42; }
        .edit-button, .primary-button, .secondary-button, .icon-button { border: 0; border-radius: 9px; cursor: pointer; }
        .edit-button { padding: 8px 12px; background: var(--primary-color); color: var(--text-primary-color, white); font-weight: 600; }
        button:disabled { opacity: .5; cursor: not-allowed; }
        .write-message { margin: 10px 0 0 24px; padding: 10px 12px; border-radius: 8px; font-size: 14.5px; line-height: 1.4; }
        .write-message.progress { background: var(--secondary-background-color); }
        .write-message.success { background: color-mix(in srgb, var(--success-color, #2e7d32) 13%, var(--card-background-color)); }
        .write-message.error { background: color-mix(in srgb, var(--error-color, #db4437) 13%, var(--card-background-color)); }
        .safety-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; padding: 16px 18px 14px; border-top: 1px solid var(--divider-color); }
        .safety-grid div, .preflight-grid div { background: var(--secondary-background-color); border-radius: 10px; padding: 11px 12px; display: flex; justify-content: space-between; gap: 12px; font-size: 15px; }
        .safety-grid strong { font-size: 16px; }
        .notice { margin: 0 18px 14px; padding: 13px 14px; border-radius: 10px; font-size: 15.5px; line-height: 1.5; }
        .warning { background: color-mix(in srgb, var(--warning-color, #ff9800) 14%, var(--card-background-color)); border: 1px solid color-mix(in srgb, var(--warning-color, #ff9800) 40%, transparent); }
        .success-note { background: color-mix(in srgb, var(--success-color, #2e7d32) 12%, var(--card-background-color)); border: 1px solid color-mix(in srgb, var(--success-color, #2e7d32) 32%, transparent); }
        .rule { background: var(--secondary-background-color); }
        .dependency-list { border-top: 1px solid var(--divider-color); padding: 8px 18px 18px; }
        .dependency-list > div { display: grid; grid-template-columns: minmax(170px, .7fr) 2fr; gap: 18px; padding: 12px 0; border-bottom: 1px solid var(--divider-color); font-size: 15px; line-height: 1.45; }
        .dependency-list > div:last-child { border-bottom: 0; }
        .dependency-list span { color: var(--secondary-text-color); }
        .preflight-backdrop { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.48); display: flex; align-items: flex-start; justify-content: center; overflow: auto; padding: 34px 16px; }
        .preflight { width: min(760px, 100%); background: var(--card-background-color); color: var(--primary-text-color); border-radius: 16px; box-shadow: 0 16px 50px rgba(0,0,0,.35); padding: 20px; }
        .preflight-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
        .eyebrow { color: var(--secondary-text-color); font-size: 14px; font-weight: 650; }
        .icon-button { width: 38px; height: 38px; font-size: 28px; line-height: 1; background: var(--secondary-background-color); color: var(--primary-text-color); }
        .target-change { margin-top: 18px; border: 1px solid var(--divider-color); border-radius: 12px; padding: 14px 15px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
        .target-change span { color: var(--secondary-text-color); }
        .target-change strong { font-size: 21px; }
        .arrow { padding: 0 7px; color: var(--primary-color); }
        .preflight-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; }
        .preflight-grid strong { text-align: right; }
        .preflight-grid.expected div { border: 1px solid color-mix(in srgb, var(--success-color, #2e7d32) 25%, transparent); }
        .dependency-callout, .safety-callout { padding: 12px 14px; border-radius: 10px; line-height: 1.5; margin-top: 8px; }
        .dependency-callout { background: color-mix(in srgb, var(--warning-color, #ff9800) 12%, var(--card-background-color)); border: 1px solid color-mix(in srgb, var(--warning-color, #ff9800) 35%, transparent); }
        .safety-callout.ok { background: color-mix(in srgb, var(--success-color, #2e7d32) 10%, var(--card-background-color)); }
        .safety-callout.blocked { background: color-mix(in srgb, var(--error-color, #db4437) 12%, var(--card-background-color)); border: 1px solid color-mix(in srgb, var(--error-color, #db4437) 35%, transparent); }
        .steps { padding-left: 25px; margin: 8px 0; line-height: 1.55; }
        .steps li { margin: 5px 0; }
        .confirm-line { display: flex; gap: 11px; align-items: flex-start; margin-top: 20px; padding: 13px 14px; background: var(--secondary-background-color); border-radius: 10px; line-height: 1.45; }
        .confirm-line input { margin-top: 3px; width: 18px; height: 18px; }
        .confirm-line.disabled { opacity: .65; }
        .preflight-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
        .primary-button, .secondary-button { padding: 10px 15px; font-weight: 650; }
        .primary-button { background: var(--primary-color); color: var(--text-primary-color, white); }
        .secondary-button { background: var(--secondary-background-color); color: var(--primary-text-color); }
        @media (max-width: 620px) {
          .page { padding: 16px 10px 34px; }
          h1 { font-size: 24px; }
          h2 { font-size: 21px; }
          summary { padding: 16px 14px; font-size: 18px; }
          .setting-row { padding: 14px; }
          .setting-main { align-items: flex-start; gap: 10px; }
          .setting-name { font-size: 17px; }
          .setting-value { min-width: auto; font-size: 17px; }
          .setting-description, .setting-relation { margin-left: 0; padding-left: 24px; font-size: 15px; }
          .setting-relation { margin-left: 24px; padding: 8px 10px; }
          .safety-grid, .preflight-grid { grid-template-columns: 1fr; padding-left: 14px; padding-right: 14px; }
          .preflight-grid { padding: 0; }
          .notice { margin-left: 14px; margin-right: 14px; }
          .dependency-list { padding-left: 14px; padding-right: 14px; }
          .dependency-list > div { grid-template-columns: 1fr; gap: 4px; }
          .preflight-backdrop { padding: 12px 8px; }
          .preflight { padding: 16px 14px; }
          .target-change { align-items: flex-start; flex-direction: column; }
        }
        @media (max-width: 410px) {
          .setting-main { flex-wrap: wrap; }
          .setting-controls { width: 100%; padding-left: 24px; justify-content: space-between; }
          .setting-value:not(.setting-controls .setting-value) { width: 100%; text-align: left; padding-left: 24px; }
          .preflight-actions { flex-direction: column-reverse; }
          .preflight-actions button { width: 100%; }
        }
      </style>
      <div class="page">
        <div class="header">
          <h1>Autarco Local Instellingencentrum</h1>
          <p class="lead">Actuele waarden, betekenis en onderlinge afhankelijkheden bij elkaar. Alleen hardwarematig gevalideerde writes krijgen een begeleide wijzigingsroute.</p>
        </div>
        ${GROUPS.map((group) => this._group(group)).join("")}
        ${this._dependencyOverview()}
        ${this._safety()}
      </div>
      ${this._preflight()}`;

    this._bindEvents();
  }
}

if (!customElements.get("autarco-local-settings-panel")) {
  customElements.define("autarco-local-settings-panel", AutarcoSettingsPanel);
}
