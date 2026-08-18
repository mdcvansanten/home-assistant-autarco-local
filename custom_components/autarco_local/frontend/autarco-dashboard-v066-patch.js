// v0.6.6 runtime patch for the Autarco Local dashboard.
// Keeps the stable v0.6.5 panel implementation small while improving entity
// resolution, integrating the former dashboard view, diagnostics controls and
// scenario guidance.

const PANEL = customElements.get("autarco-local-dashboard-panel");

if (PANEL) {
  const proto = PANEL.prototype;
  const originalFindState = proto._findState;
  const originalSettings = proto._settings;

  const LIVE_KEYS = new Set([
    "pv_power",
    "battery_soc",
    "battery_power",
    "grid_power",
    "house_load_power",
    "temperature",
  ]);

  proto._findState = function patchedFindState(key) {
    if (!key) return null;

    const states = this._entities();

    // Prefer the actual runtime battery SOC sensor. A loose suffix match on
    // `_battery_soc` also matched the holding-register setting
    // `minimum_battery_soc` and therefore showed 20% instead of the live SOC.
    if (key === "battery_soc") {
      const exact = states.find((entity) => {
        const attrs = entity.attributes || {};
        if (attrs.register_type === "holding") return false;
        const id = entity.entity_id.toLowerCase();
        const name = String(attrs.friendly_name || "").toLowerCase();
        return (
          id.endsWith("_battery_state_of_charge") ||
          id.endsWith("_battery_soc") ||
          (attrs.device_class === "battery" && name.indexOf("minimum") === -1)
        );
      });
      if (exact) return exact;
    }

    const resolved = originalFindState.call(this, key);
    if (!resolved) return null;

    // Runtime overview cards must never silently resolve to a holding-register
    // settings sensor.
    if (
      LIVE_KEYS.has(key) &&
      resolved.attributes &&
      resolved.attributes.register_type === "holding"
    ) {
      return null;
    }
    return resolved;
  };

  proto._overview = function integratedDashboard() {
    const connection = this._findState("connection");
    const pv = this._findState("pv_power");
    const batterySoc = this._findState("battery_soc");
    const batteryPower = this._findState("battery_power");
    const grid = this._findState("grid_power");
    const load = this._findState("house_load_power");
    const temperature = this._findState("temperature");

    const status = (entity) => this._escape(this._formatState(entity));

    return `
      <section class="content-section">
        <h2>Dashboard</h2>
        <p class="muted">Het oorspronkelijke Autarco-dashboard is vanaf v0.6.6 onderdeel van Autarco Local. De detailtabs blijven beschikbaar voor verdieping.</p>

        <div class="dashboard-block">
          <h3>⚡ Energie & omvormer</h3>
          <div class="metrics">
            <div class="metric-card"><span>PV-vermogen</span><strong>${status(pv)}</strong></div>
            <div class="metric-card"><span>Huisverbruik</span><strong>${status(load)}</strong></div>
            <div class="metric-card"><span>Netvermogen</span><strong>${status(grid)}</strong></div>
            <div class="metric-card"><span>Batterijvermogen</span><strong>${status(batteryPower)}</strong></div>
            <div class="metric-card"><span>Batterij-SOC</span><strong>${status(batterySoc)}</strong></div>
            <div class="metric-card"><span>Omvormertemperatuur</span><strong>${status(temperature)}</strong></div>
          </div>
        </div>

        <div class="dashboard-columns">
          <div class="dashboard-block compact">
            <h3>☀️ Zonnepanelen</h3>
            <p><strong>${status(pv)}</strong> actuele productie.</p>
            <p class="muted">Gebruik de tab <strong>PV</strong> voor MPPT/PV1/PV2, energie vandaag, maand, jaar en totaal.</p>
          </div>
          <div class="dashboard-block compact">
            <h3>🩺 Diagnose</h3>
            <p><strong>${status(connection)}</strong> lokale Modbusverbinding.</p>
            <p class="muted">Gebruik de tab <strong>Diagnose</strong> voor polling, beschikbaarheid, storingshistorie en logging.</p>
          </div>
        </div>

        <div class="dashboard-block compact">
          <h3>📈 Historie & grafieken</h3>
          <p class="muted">De live gegevens zijn nu geïntegreerd. Recorder-/historiegrafieken uit het oude Lovelace-dashboard migreren we als volgende UI-stap naar deze pagina, zodat er uiteindelijk nog maar één Autarco-scherm nodig is.</p>
        </div>
      </section>`;
  };

  proto._diagnostics = function enhancedDiagnostics() {
    const logger = this._entities().find((entity) =>
      entity.entity_id.endsWith("_detailed_logging") ||
      entity.entity_id.endsWith("_diagnostic_logging")
    );
    const loggerState = logger ? String(logger.state).toLowerCase() : "off";
    const loggingOn = ["on", "true", "1", "aan"].includes(loggerState);

    return `
      <section class="content-section">
        <h2>Diagnose & monitoring</h2>
        <p class="muted">Verbinding, polling, retries en beschikbaarheidsinformatie. Monitoring blijft altijd actief; uitgebreide debuglogging kan apart worden geschakeld.</p>
        <div class="lockbar ${loggingOn ? "unlocked" : "lockedbar"}">
          <div>
            <strong>${loggingOn ? "📝 Uitgebreide logging AAN" : "📝 Uitgebreide logging UIT"}</strong>
            <span>${loggingOn ? "Meer technische details worden tijdelijk naar de Home Assistant-log geschreven." : "Normale waarschuwingen en verbindingsmonitoring blijven actief."}</span>
          </div>
          ${logger ? `<button class="${loggingOn ? "secondary" : "primary"}" data-action="toggle-detailed-logging" data-entity-id="${this._escape(logger.entity_id)}">${loggingOn ? "Logging uit" : "Logging aan"}</button>` : `<span class="muted">Logging-switch wordt na v0.6.6 reload beschikbaar.</span>`}
        </div>
        ${this._entityList(["retry", "retries", "poll", "connect", "disconnect", "uptime", "downtime", "availability", "beschikbaarheid", "health", "gezondheid", "response"], "Geen diagnose-entiteiten gevonden.")}
        <details class="group dependencies" open>
          <summary>⚠️ Bekende foutcodes<span class="chevron">⌄</span></summary>
          <div class="dependency-list">
            <div><strong>2012 — CAN_Comm_FAIL</strong><span>Batterijcommunicatie mislukt. Controleer vooral CAN/BMS-communicatie en of de storing terugkeert.</span></div>
            <div><strong>105C</strong><span>Nog niet eenduidig gevonden in de actuele publiek geïndexeerde Solis-alarmdocumentatie. Niet raden: exacte alarmnaam/subcode en tijdstip gebruiken voor identificatie.</span></div>
          </div>
        </details>
      </section>`;
  };

  proto._scenarioSection = function scenarioSection() {
    const cards = [
      ["Normaal zelfgebruik", "Huis eerst → accu → net", "Self-use AAN; normale SOC-grenzen blijven leidend.", "basis"],
      ["Accu vasthouden", "Niet ontladen onder gekozen reserve", "Battery Reserve + Reserved SOC. Handig om energie voor later/noodreserve te bewaren.", "pending"],
      ["Nu laden vanaf het net", "Handmatig laden tot gekozen doel-SOC", "Allow Grid Charging + tijdelijke laadregeling; Autarco Local stopt zodra het doel-SOC is bereikt.", "pending"],
      ["Nacht-/tijdladen", "Laden in een gekozen tijdvak", "Time of Use + laadstroom + laadslot; buiten het tijdvak terug naar normale Self-use.", "pending"],
      ["Maximaal terugleveren", "PV-export krijgt voorrang", "Feed-in Priority. Batterij blijft buiten ingestelde charge/discharge-tijden grotendeels inactief.", "pending"],
      ["Peak shaving", "Netpiek begrenzen", "Peak Shaving + Max Usable Grid Power + Baseline SOC; vereist correcte meter/BMS-data.", "pending"],
      ["Backupreserve", "Vaste noodreserve aanhouden", "Battery Reserve met gekozen SOC; alleen de reserve wordt beschermd voor netuitval.", "pending"],
      ["Onderhoud / battery healing", "Accu gecontroleerd herstellen", "Expert-scenario. Alleen activeren nadat Battery Healing-dependencies op deze hardware zijn gevalideerd.", "pending"],
    ];

    return `
      <details class="group dependencies" open>
        <summary>🎛️ Scenario's<span class="chevron">⌄</span></summary>
        <div class="scenario-grid">
          ${cards.map(([name, goal, desc, state]) => `
            <div class="scenario-card">
              <div class="scenario-title">${this._escape(name)}</div>
              <strong>${this._escape(goal)}</strong>
              <p>${this._escape(desc)}</p>
              <span class="scenario-state ${state}">${state === "basis" ? "Beschreven / write-validatie volgt" : "Voorbereid — nog niet activeren"}</span>
            </div>`).join("")}
        </div>
        <p class="hint">Scenario's worden pas activeerbaar wanneer alle onderliggende registers, parent modes, read-back en restorepaden op jouw Autarco-installatie hardwarematig zijn getest. De eerste instellingstest blijft Minimum-SOC off-grid.</p>
      </details>`;
  };

  proto._settings = function settingsWithScenarios() {
    let html = originalSettings.call(this);
    html = html.replace(
      "Dezelfde groen/geel/rood-indeling als voorheen, nu als tab in Autarco Local. De originele Home Assistant Configureren-route blijft als fallback beschikbaar.",
      "Alle inverterinstellingen staan hier centraal. Home Assistant → Configureren wordt alleen gebruikt om de instellingen-PIN te beheren."
    );
    return html.replace("</section>", `${this._scenarioSection()}</section>`);
  };

  const originalBindEvents = proto._bindEvents;
  proto._bindEvents = function patchedBindEvents() {
    if (originalBindEvents) originalBindEvents.call(this);
    this.shadowRoot.querySelectorAll('[data-action="toggle-detailed-logging"]').forEach((button) => {
      button.onclick = async () => {
        const entityId = button.dataset.entityId;
        if (!entityId || !this._hass) return;
        const logger = this._hass.states[entityId];
        const isOn = logger && ["on", "true", "1", "aan"].includes(String(logger.state).toLowerCase());
        try {
          await this._hass.callService("switch", isOn ? "turn_off" : "turn_on", { entity_id: entityId });
        } catch (err) {
          console.error("Autarco Local logging toggle failed", err);
        }
      };
    });
  };
}
