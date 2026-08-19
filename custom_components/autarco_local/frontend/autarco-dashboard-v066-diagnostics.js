// v0.6.6 diagnostics presentation: persistent connection events + runtime log toggle.

const PANEL_DIAG_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_DIAG_V066) {
  const proto = PANEL_DIAG_V066.prototype;

  proto._diagnostics = function diagnosticsWithHistory() {
    const logger = this._entities().find((entity) => {
      const id = entity.entity_id.toLowerCase();
      const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
      return id.endsWith("_detailed_logging") || name.indexOf("detailed logging") !== -1;
    });
    const loggerState = logger ? String(logger.state).toLowerCase() : "off";
    const loggingOn = ["on", "true", "1", "aan"].includes(loggerState);

    const connection = this._findState("connection");
    const attrs = connection && connection.attributes ? connection.attributes : {};
    const events = Array.isArray(attrs.connection_events) ? attrs.connection_events.slice(-10).reverse() : [];
    const lastError = attrs.last_error || attrs.last_disconnect_reason || "Geen actuele fout";

    const eventRows = events.length
      ? events.map((event) => {
          const kind = event.event === "disconnected"
            ? "🔴 Verbinding verbroken"
            : event.event === "reconnected"
              ? "🟢 Verbinding hersteld"
              : "🔵 Verbonden";
          const downtime = event.downtime_seconds == null ? "—" : `${event.downtime_seconds} s`;
          const reason = event.reason || "—";
          return `<div class="diag-event"><strong>${this._escape(kind)}</strong><span>${this._escape(event.timestamp || "")}</span><span>${this._escape(downtime)}</span><span title="${this._escape(reason)}">${this._escape(reason)}</span></div>`;
        }).join("")
      : `<div class="empty">Nog geen verbindingshistorie beschikbaar.</div>`;

    return `
      <section class="content-section">
        <h2>Diagnose & monitoring</h2>
        <p class="muted">Modbus/TCP is hier de bron voor bereikbaarheid. De LAN-stick hoeft niet op ICMP/ping te reageren om lokaal via poort 502 gewoon bereikbaar te zijn.</p>

        <div class="lockbar ${loggingOn ? "unlocked" : "lockedbar"}">
          <div>
            <strong>${loggingOn ? "📝 Uitgebreide logging AAN" : "📝 Uitgebreide logging UIT"}</strong>
            <span>${loggingOn ? "Autarco Local schrijft tijdelijk DEBUG-details naar de Home Assistant-log. Na een HA-herstart staat dit automatisch weer UIT." : "Normale waarschuwingen, monitoring en persistente verbindingshistorie blijven actief."}</span>
          </div>
          ${logger ? `<button class="${loggingOn ? "secondary" : "primary"}" data-action="toggle-detailed-logging" data-entity-id="${this._escape(logger.entity_id)}">${loggingOn ? "Logging uit" : "Logging aan"}</button>` : `<span class="muted">Logging-switch niet gevonden.</span>`}
        </div>

        <div class="callout"><strong>Laatste verbindingsmelding:</strong> ${this._escape(lastError)}</div>

        ${this._entityList(["retry", "retries", "poll", "connect", "disconnect", "uptime", "downtime", "availability", "beschikbaarheid", "health", "gezondheid", "response"], "Geen diagnose-entiteiten gevonden.")}

        <details class="group dependencies" open>
          <summary>🕘 Recente verbindingshistorie<span class="chevron">⌄</span></summary>
          <div class="diag-events">${eventRows}</div>
        </details>

        <details class="group dependencies" open>
          <summary>⚠️ Bekende foutcodes<span class="chevron">⌄</span></summary>
          <div class="dependency-list">
            <div><strong>2012 — CAN_Comm_FAIL</strong><span>Batterijcommunicatiefout: de inverter verliest of mist CAN/BMS-communicatie met de batterij. Bij een terugkerende melding zijn CAN-kabel/connector, BMS-status, batterijselectie/protocol en firmwarecompatibiliteit de logische controles.</span></div>
            <div><strong>105C</strong><span>Nog niet eenduidig gekoppeld in de actuele publiek doorzoekbare Solis-documentatie. Autarco Local toont deze voorlopig als onbekend en gaat de betekenis niet gokken. Alarmnaam, subcode en tijdstip zijn nodig voor definitieve identificatie.</span></div>
          </div>
        </details>
      </section>`;
  };

  const previousRender = proto.render;
  proto.render = function renderDiagnosticsStyles() {
    previousRender.call(this);
    if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v066-diag-styles")) return;
    const style = document.createElement("style");
    style.id = "autarco-v066-diag-styles";
    style.textContent = `
      .diag-events { border-top:1px solid var(--divider-color); padding:8px 16px 14px; }
      .diag-event { display:grid; grid-template-columns:180px 220px 100px minmax(180px,1fr); gap:10px; padding:9px 0; border-bottom:1px solid var(--divider-color); align-items:start; }
      .diag-event:last-child { border-bottom:0; }
      .diag-event span { color:var(--secondary-text-color); overflow:hidden; text-overflow:ellipsis; }
      @media (max-width:750px) { .diag-event { grid-template-columns:1fr; gap:3px; } }
    `;
    this.shadowRoot.appendChild(style);
  };
}
