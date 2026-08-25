// Autarco Local v0.7.1 — deep connection monitor presentation.
// Loaded after the v0.7.1 UX layer so it can extend diagnostics without
// disturbing the settings/scenario fixes.

const PANEL_CONN_V071 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_CONN_V071) {
  const proto = PANEL_CONN_V071.prototype;
  const previousDiagnosticsV071 = proto._diagnostics;
  const previousRenderConnV071 = proto.render;

  proto._v071DeepMonitor = function () {
    const connection = this._findState("connection");
    const attrs = connection && connection.attributes ? connection.attributes : {};
    const monitor = attrs.deep_connection_monitor || {};
    const classification = monitor.classification || "unknown";
    const stage = monitor.stage || "unknown";
    const tcp = monitor.tcp_502_reachable;
    const failedGroup = monitor.last_failed_group || "—";
    const probeMs = monitor.last_tcp_probe_ms == null ? "—" : `${monitor.last_tcp_probe_ms} ms`;
    const requests = monitor.poll_request_count == null ? "—" : monitor.poll_request_count;
    const strategy = monitor.poll_strategy || "—";
    const error = monitor.last_error || "Geen actuele fout";
    const events = Array.isArray(monitor.events) ? monitor.events.slice(-12).reverse() : [];

    let verdictTitle = "⚪ Nog onvoldoende meetdata";
    let verdictText = "Na de eerstvolgende succesvolle of mislukte Modbus-poll wordt de verbindingslaag geclassificeerd.";
    let verdictClass = "unknown";
    if (classification === "modbus_healthy") {
      verdictTitle = "🟢 TCP 502 en Modbus momenteel gezond";
      verdictText = "De runtime-poll is volledig geslaagd; TCP-bereikbaarheid wordt daarom als bewezen beschouwd zonder extra socket.";
      verdictClass = "ok";
    } else if (classification === "tcp_502_down") {
      verdictTitle = "🔴 TCP-poort 502 niet bereikbaar";
      verdictText = "Na een mislukte Modbus-poll faalde ook een onafhankelijke TCP/502-probe. Kijk dan vooral naar Wi-Fi/logger/netwerkpad.";
      verdictClass = "bad";
    } else if (classification === "tcp_up_modbus_failed") {
      verdictTitle = "🟠 TCP 502 bereikbaar, Modbus faalt";
      verdictText = "De logger accepteert nog een TCP-verbinding, maar de Modbus-runtimepoll mislukt. Dit wijst eerder richting logger/Modbus-protocol, requestbelasting of firmware dan naar volledige Wi-Fi-uitval.";
      verdictClass = "warn";
    }

    const eventRows = events.length
      ? events.map((event) => {
          const tcpText = event.tcp_reachable === true ? "TCP OK" : event.tcp_reachable === false ? "TCP DOWN" : "TCP —";
          return `<div class="conn-event"><span>${this._escape(event.timestamp || "")}</span><strong>${this._escape(event.classification || "unknown")}</strong><span>${this._escape(tcpText)}</span><span>${this._escape(event.failed_group || "—")}</span><span title="${this._escape(event.error || "")}">${this._escape(event.error || "—")}</span></div>`;
        }).join("")
      : `<div class="empty">Nog geen deep-monitor gebeurtenissen geregistreerd.</div>`;

    return `
      <details class="group dependencies v071-connection-monitor" open>
        <summary>📡 Verbindingsanalyse: Wi-Fi / TCP 502 / Modbus<span class="chevron">⌄</span></summary>
        <div class="conn-monitor-body">
          <div class="conn-verdict ${verdictClass}"><strong>${this._escape(verdictTitle)}</strong><span>${this._escape(verdictText)}</span></div>
          <div class="conn-grid">
            <div><span>TCP 502</span><strong>${tcp === true ? "Bereikbaar" : tcp === false ? "Niet bereikbaar" : "Nog onbekend"}</strong></div>
            <div><span>Laatste fase</span><strong>${this._escape(stage)}</strong></div>
            <div><span>Classificatie</span><strong>${this._escape(classification)}</strong></div>
            <div><span>Laatste TCP-probe</span><strong>${this._escape(probeMs)}</strong></div>
            <div><span>Pollingstrategie</span><strong>${this._escape(strategy)}</strong></div>
            <div><span>Requests laatste poll</span><strong>${this._escape(requests)}</strong></div>
            <div><span>Laatste mislukte registergroep</span><strong>${this._escape(failedGroup)}</strong></div>
            <div><span>Laatste fout</span><strong title="${this._escape(error)}">${this._escape(error)}</strong></div>
          </div>
          <p class="hint">Combineer deze timestamps met de Home Assistant Ping-integratie en de MikroTik registration/log-data. Als ping én TCP 502 tegelijk wegvallen, ligt de oorzaak vrijwel zeker vóór de Modbus-protocollaag.</p>
          <h4>Laatste geclassificeerde gebeurtenissen</h4>
          <div class="conn-events">${eventRows}</div>
        </div>
      </details>`;
  };

  proto._diagnostics = function diagnosticsWithDeepMonitor() {
    let html = previousDiagnosticsV071.call(this);
    const monitor = this._v071DeepMonitor();
    return html.replace("</section>", `${monitor}</section>`);
  };

  proto.render = function renderConnectionMonitorStyles() {
    previousRenderConnV071.call(this);
    if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v071-conn-styles")) return;
    const style = document.createElement("style");
    style.id = "autarco-v071-conn-styles";
    style.textContent = `
      .conn-monitor-body { padding:12px 16px 16px; }
      .conn-verdict { display:flex; flex-direction:column; gap:4px; padding:12px 14px; border-radius:10px; background:var(--secondary-background-color); margin-bottom:12px; }
      .conn-verdict.ok { border-left:4px solid var(--success-color,#43a047); }
      .conn-verdict.warn { border-left:4px solid var(--warning-color,#ffb300); }
      .conn-verdict.bad { border-left:4px solid var(--error-color,#db4437); }
      .conn-verdict.unknown { border-left:4px solid var(--disabled-text-color); }
      .conn-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
      .conn-grid>div { display:flex; flex-direction:column; gap:3px; padding:10px 12px; border:1px solid var(--divider-color); border-radius:9px; min-width:0; }
      .conn-grid span { color:var(--secondary-text-color); font-size:12px; }
      .conn-grid strong { overflow:hidden; text-overflow:ellipsis; }
      .conn-events { border-top:1px solid var(--divider-color); }
      .conn-event { display:grid; grid-template-columns:190px 170px 90px 180px minmax(150px,1fr); gap:8px; padding:8px 0; border-bottom:1px solid var(--divider-color); font-size:12px; }
      .conn-event span { overflow:hidden; text-overflow:ellipsis; }
      @media(max-width:750px) { .conn-grid { grid-template-columns:1fr; } .conn-event { grid-template-columns:1fr; gap:2px; } }
    `;
    this.shadowRoot.appendChild(style);
  };
}
