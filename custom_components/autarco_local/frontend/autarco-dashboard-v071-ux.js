// Autarco Local v0.7.1 — field-test UX corrections.
// Keeps the proven v0.6.6/v0.7.0 behaviour, but makes scenarios genuinely
// scenario-first and separates current connection state from historical faults.

const PANEL_V071 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V071) {
  const proto = PANEL_V071.prototype;
  const previousRenderV071 = proto.render;

  const LINKED_LABELS_V071 = new Set([
    "Reserve SOC",
    "Self-use mode",
    "Time-of-use mode",
    "Reserve battery mode",
    "Feed-in priority mode",
    "Minimum battery SOC",
    "Force-charge SOC",
    "Force-charge power limit",
    "Off-grid mode",
    "Laden vanuit net toestaan",
    "Minimum-SOC off-grid",
    "Geplande laadstroom",
    "Geplande ontlaadstroom",
  ]);

  proto._v071ConfigurationHealth = function () {
    const reserve = this._number("reserve_soc");
    const minimum = this._number("minimum_battery_soc");
    const force = this._number("force_charge_soc");
    const findings = [];

    if (reserve !== null && minimum !== null && reserve < minimum) {
      findings.push({
        severity: "blocked",
        title: "Reserve SOC lager dan Minimum SOC",
        text: `Reserve SOC is ${reserve}% en Minimum SOC is ${minimum}%. Writes blijven geblokkeerd totdat Reserve SOC minimaal gelijk is aan Minimum SOC.`,
      });
    }
    if (force !== null && minimum !== null && force > minimum) {
      findings.push({
        severity: "warning",
        title: "Force-charge SOC boven Minimum SOC",
        text: `Force-charge SOC is ${force}% en Minimum SOC is ${minimum}%. Controleer deze beschermingsdrempels voordat netlaadfuncties worden vrijgegeven.`,
      });
    }

    const state = findings.some((item) => item.severity === "blocked")
      ? "blocked"
      : findings.some((item) => item.severity === "warning")
        ? "warning"
        : "healthy";
    return { state, findings };
  };

  proto._v071DecorateSettings = function () {
    if (!this.shadowRoot || this._activeTab !== "settings") return;
    const section = this.shadowRoot.querySelector(".settings-section");
    if (!section) return;

    // Move the already-rendered scenario block to the top instead of duplicating
    // scenario definitions in another frontend layer.
    const details = Array.from(section.querySelectorAll("details"));
    const scenario = details.find((item) => {
      const summary = item.querySelector("summary");
      return summary && String(summary.textContent || "").toLowerCase().includes("scenario");
    });
    const lockbar = section.querySelector(".lockbar");
    if (scenario && lockbar) {
      scenario.open = true;
      scenario.classList.add("v071-scenario-first");
      lockbar.insertAdjacentElement("afterend", scenario);
    }

    // Installer/system settings start collapsed on every fresh panel instance.
    const installer = details.find((item) => {
      const summary = item.querySelector("summary");
      return summary && String(summary.textContent || "").toLowerCase().includes("installer-/systeeminstellingen");
    });
    if (installer && !this._v071InstallerInitialised) {
      installer.open = false;
      this._v071InstallerInitialised = true;
    }

    // Mark relationships in the rendered UI even when an older cached v0.7.0
    // extension did not decorate the rows correctly.
    section.querySelectorAll(".setting-row").forEach((row) => {
      const title = row.querySelector(".setting-title");
      if (!title || title.querySelector(".v071-linked")) return;
      const label = String(title.textContent || "").replace("🔗 Gekoppeld", "").trim();
      if (!LINKED_LABELS_V071.has(label)) return;
      const badge = document.createElement("span");
      badge.className = "v071-linked";
      badge.textContent = "🔗 Gekoppeld";
      title.insertBefore(badge, title.firstChild);
    });

    if (!section.querySelector(".v071-health")) {
      const health = this._v071ConfigurationHealth();
      const panel = document.createElement("div");
      panel.className = `v071-health ${health.state}`;
      const title = health.state === "blocked"
        ? "⛔ Configuratieconflict"
        : health.state === "warning"
          ? "⚠️ Gekoppelde instellingen vragen aandacht"
          : "✅ Gekoppelde instellingen zijn consistent";
      panel.innerHTML = `<strong>${this._escape(title)}</strong>` + (
        health.findings.length
          ? health.findings.map((item) => `<div><strong>${this._escape(item.title)}</strong><span>${this._escape(item.text)}</span></div>`).join("")
          : `<span>Geen blokkerende relatie gevonden in de momenteel beschikbare instellingen.</span>`
      );
      if (scenario) scenario.insertAdjacentElement("afterend", panel);
      else if (lockbar) lockbar.insertAdjacentElement("afterend", panel);
    }
  };

  proto._diagnostics = function diagnosticsV071() {
    const logger = this._entities().find((entity) => {
      const id = entity.entity_id.toLowerCase();
      const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
      return id.endsWith("_detailed_logging") || name.indexOf("detailed logging") !== -1;
    });
    const loggerState = logger ? String(logger.state).toLowerCase() : "off";
    const loggingOn = ["on", "true", "1", "aan"].includes(loggerState);

    const connection = this._findState("connection");
    const connectionState = connection ? String(connection.state || "").toLowerCase() : "unknown";
    const connectionOn = ["on", "true", "1", "aan", "connected"].includes(connectionState);
    const attrs = connection && connection.attributes ? connection.attributes : {};
    const events = Array.isArray(attrs.connection_events) ? attrs.connection_events.slice(-10).reverse() : [];
    const currentError = attrs.last_error || null;
    const historicalError = attrs.last_disconnect_reason || null;

    const currentTitle = connectionOn && !currentError
      ? "🟢 Modbus/TCP momenteel verbonden"
      : "🔴 Modbus/TCP momenteel niet gezond";
    const currentText = connectionOn && !currentError
      ? "De huidige verbinding is actief. Een fout hieronder bij verbindingshistorie is historisch en niet per definitie nog actueel."
      : (currentError || "De actuele verbinding is niet beschikbaar.");

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
        <p class="muted">Modbus/TCP is de bron voor actuele bereikbaarheid. v0.7.1 gebruikt gegroepeerde reads voor de bekende Autarco-registers en valt per groep terug op kleine blokken wanneer dat nodig is.</p>

        <div class="v071-current-connection ${connectionOn && !currentError ? "ok" : "bad"}">
          <strong>${this._escape(currentTitle)}</strong>
          <span>${this._escape(currentText)}</span>
        </div>

        <div class="lockbar ${loggingOn ? "unlocked" : "lockedbar"}">
          <div><strong>${loggingOn ? "📝 Uitgebreide logging AAN" : "📝 Uitgebreide logging UIT"}</strong><span>${loggingOn ? "DEBUG-details worden tijdelijk naar de Home Assistant-log geschreven." : "Normale waarschuwingen, monitoring en persistente verbindingshistorie blijven actief."}</span></div>
          ${logger ? `<button class="${loggingOn ? "secondary" : "primary"}" data-action="toggle-detailed-logging" data-entity-id="${this._escape(logger.entity_id)}">${loggingOn ? "Logging uit" : "Logging aan"}</button>` : `<span class="muted">Logging-switch niet gevonden.</span>`}
        </div>

        ${historicalError ? `<div class="callout"><strong>Laatste historische verbreking:</strong> ${this._escape(historicalError)}</div>` : ""}

        ${this._entityList(["retry", "retries", "poll", "connect", "disconnect", "uptime", "downtime", "availability", "beschikbaarheid", "health", "gezondheid", "response"], "Geen diagnose-entiteiten gevonden.")}

        <details class="group dependencies" open><summary>🕘 Recente verbindingshistorie<span class="chevron">⌄</span></summary><div class="diag-events">${eventRows}</div></details>
        <details class="group dependencies"><summary>⚠️ Bekende foutcodes<span class="chevron">⌄</span></summary><div class="dependency-list"><div><strong>2012 — CAN_Comm_FAIL</strong><span>Batterijcommunicatiefout: controleer bij herhaling CAN/BMS-communicatie, connectoren, batterijselectie/protocol en firmwarecompatibiliteit.</span></div><div><strong>105C</strong><span>Nog niet eenduidig gekoppeld. Autarco Local gokt de betekenis niet; alarmnaam, subcode en tijdstip zijn nodig voor definitieve identificatie.</span></div></div></details>
      </section>`;
  };

  proto.render = function renderV071() {
    previousRenderV071.call(this);
    if (!this.shadowRoot) return;

    this._v071DecorateSettings();

    if (!this.shadowRoot.querySelector("#autarco-v071-styles")) {
      const style = document.createElement("style");
      style.id = "autarco-v071-styles";
      style.textContent = `
        .v071-scenario-first { margin-top:16px; border:1px solid var(--primary-color); }
        .v071-health { display:flex; flex-direction:column; gap:7px; padding:12px 14px; margin:12px 0 16px; border-radius:10px; background:var(--secondary-background-color); }
        .v071-health.healthy { border-left:4px solid var(--success-color,#43a047); }
        .v071-health.warning { border-left:4px solid var(--warning-color,#ffb300); }
        .v071-health.blocked { border-left:4px solid var(--error-color,#db4437); }
        .v071-health div { display:flex; flex-direction:column; gap:2px; }
        .v071-linked { font-size:11px; font-weight:600; opacity:.78; margin-right:7px; white-space:nowrap; }
        .v071-current-connection { display:flex; flex-direction:column; gap:4px; padding:12px 14px; border-radius:10px; margin:12px 0; background:var(--secondary-background-color); }
        .v071-current-connection.ok { border-left:4px solid var(--success-color,#43a047); }
        .v071-current-connection.bad { border-left:4px solid var(--error-color,#db4437); }
        @media(max-width:700px) { .v071-linked { display:block; margin-bottom:3px; } }
      `;
      this.shadowRoot.appendChild(style);
    }
  };
}
