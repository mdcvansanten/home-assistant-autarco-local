// v0.6.6 compact cross-setting relationship status.
//
// Access-level dots (green/yellow/red) already mean Standard/Expert/Installer,
// so relationship health gets a separate compact status bar. Each relation has
// its own colour, hover title and clickable ? explanation for touch devices.

const PANEL_RELATION_STATUS_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_RELATION_STATUS_V066) {
  const proto = PANEL_RELATION_STATUS_V066.prototype;
  const RELATION_STATUS_VERSION = "0.6.6.14";

  if (proto._autarcoRelationStatusVersion !== RELATION_STATUS_VERSION) {
    const numberValue = (instance, key) => {
      const value = instance._number(key);
      return Number.isFinite(value) ? Number(value) : null;
    };

    const relationState = (instance) => {
      const minimum = numberValue(instance, "minimum_battery_soc");
      const offGridMinimum = numberValue(instance, "off_grid_minimum_soc");
      const forceCharge = numberValue(instance, "force_charge_soc");
      const reserve = numberValue(instance, "reserve_soc");
      const selfUse = instance._isOn("self_use_mode");
      const offGrid = instance._isOn("off_grid_mode");
      const gridCharging = instance._isOn("allow_grid_charging");
      const reserveMode = instance._isOn("reserve_battery_mode");

      let soc;
      if (minimum === null || offGridMinimum === null) {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "unknown",
          text: "SOC-relatie niet compleet beschikbaar."
        };
      } else if (offGrid) {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "danger",
          text: `Off-grid actief: ${offGridMinimum}% is nu de Off-grid ondergrens; normaal Minimum SOC is ${minimum}%.`
        };
      } else if (!selfUse) {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "warn",
          text: "Self-use staat uit: controleer welke bedrijfsmodus nu de SOC-grens bepaalt."
        };
      } else if (offGridMinimum < minimum) {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "danger",
          text: `Self-use/netbedrijf stopt normaal op ${minimum}%; Off-grid kan tot ${offGridMinimum}% ontladen.`
        };
      } else if (offGridMinimum > minimum) {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "warn",
          text: `Off-grid stopt eerder: ${offGridMinimum}% versus normaal Minimum SOC ${minimum}%.`
        };
      } else {
        soc = {
          key: "soc",
          label: "SOC-grenzen",
          level: "ok",
          text: `Normaal en Off-grid minimum zijn gelijk: ${minimum}%.`
        };
      }

      let grid;
      if (forceCharge === null) {
        grid = {
          key: "grid",
          label: "Netladen",
          level: "unknown",
          text: "Force-charge SOC is niet beschikbaar."
        };
      } else if (gridCharging) {
        grid = {
          key: "grid",
          label: "Netladen",
          level: minimum !== null && forceCharge >= minimum ? "danger" : "warn",
          text: minimum !== null && forceCharge >= minimum
            ? `Force-charge ${forceCharge}% ligt niet onder Minimum SOC ${minimum}%.`
            : `Netladen toegestaan: onder Force-charge ${forceCharge}% kan netladen starten.`
        };
      } else {
        grid = {
          key: "grid",
          label: "Netladen",
          level: "ok",
          text: `Netladen staat uit; Force-charge SOC is ${forceCharge}%.`
        };
      }

      let reserveState;
      if (reserve === null || minimum === null) {
        reserveState = {
          key: "reserve",
          label: "Reserve",
          level: "unknown",
          text: "Reserve-relatie niet compleet beschikbaar."
        };
      } else if (reserve < minimum) {
        reserveState = {
          key: "reserve",
          label: "Reserve",
          level: "danger",
          text: `Reserve SOC ${reserve}% ligt onder Minimum SOC ${minimum}%.`
        };
      } else if (!reserveMode) {
        reserveState = {
          key: "reserve",
          label: "Reserve",
          level: "info",
          text: `Reserve mode staat uit; Reserve SOC ${reserve}% is nu niet actief.`
        };
      } else {
        reserveState = {
          key: "reserve",
          label: "Reserve",
          level: "ok",
          text: `Reserve actief op ${reserve}%; Minimum SOC is ${minimum}%.`
        };
      }

      return [soc, grid, reserveState];
    };

    const badgeHtml = (instance, relation) => {
      const text = instance._escape(relation.text);
      return `
        <button class="relation-status-badge ${relation.level}"
                data-action="show-relation-help"
                data-relation-key="${relation.key}"
                title="${text}">
          <span class="relation-status-dot" aria-hidden="true"></span>
          <span>${instance._escape(relation.label)}</span>
          <span class="relation-help-mark" aria-hidden="true">?</span>
        </button>`;
    };

    const previousSettings = proto._settings;
    proto._settings = function settingsWithRelationStatus() {
      let html = previousSettings.call(this);
      const relations = relationState(this);
      const bar = `
        <div class="settings-relation-status">
          <div class="settings-relation-head">
            <strong>Onderlinge controle</strong>
            <span class="muted">Klik op ? voor uitleg</span>
          </div>
          <div class="settings-relation-badges">
            ${relations.map((relation) => badgeHtml(this, relation)).join("")}
          </div>
          <div id="settings-relation-help" class="settings-relation-help" hidden></div>
        </div>`;

      const lockbarIndex = html.indexOf('<div class="lockbar');
      if (lockbarIndex >= 0) {
        html = html.slice(0, lockbarIndex) + bar + html.slice(lockbarIndex);
      } else {
        html = html.replace("</section>", `${bar}</section>`);
      }
      return html;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindRelationStatusHelp() {
      if (previousBindEvents) previousBindEvents.call(this);

      const relations = relationState(this);
      const byKey = Object.fromEntries(relations.map((relation) => [relation.key, relation]));
      const help = this.shadowRoot.querySelector("#settings-relation-help");

      this.shadowRoot
        .querySelectorAll('[data-action="show-relation-help"]')
        .forEach((button) => {
          button.addEventListener("click", () => {
            if (!help) return;
            const key = button.getAttribute("data-relation-key") || "";
            const relation = byKey[key];
            if (!relation) return;
            const same = help.dataset.relationKey === key && !help.hidden;
            if (same) {
              help.hidden = true;
              help.dataset.relationKey = "";
              help.textContent = "";
              return;
            }
            help.dataset.relationKey = key;
            help.className = `settings-relation-help ${relation.level}`;
            help.textContent = relation.text;
            help.hidden = false;
          });
        });
    };

    const previousRender = proto.render;
    proto.render = function renderWithRelationStatusStyles() {
      previousRender.call(this);
      if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-relation-status-styles")) return;
      const style = document.createElement("style");
      style.id = "autarco-relation-status-styles";
      style.textContent = `
        .settings-relation-status {
          margin:12px 0 16px;
          padding:12px;
          border:1px solid var(--divider-color);
          border-radius:12px;
          background:var(--card-background-color);
        }
        .settings-relation-head {
          display:flex;
          justify-content:space-between;
          gap:12px;
          align-items:center;
          margin-bottom:9px;
        }
        .settings-relation-head .muted { font-size:13px; }
        .settings-relation-badges {
          display:flex;
          gap:8px;
          flex-wrap:wrap;
        }
        .relation-status-badge {
          display:inline-flex;
          align-items:center;
          gap:7px;
          border:1px solid var(--divider-color);
          border-radius:999px;
          padding:7px 10px;
          background:var(--secondary-background-color);
          color:var(--primary-text-color);
          font-weight:600;
        }
        .relation-status-dot {
          width:10px;
          height:10px;
          border-radius:50%;
          background:#9e9e9e;
          flex:0 0 10px;
        }
        .relation-status-badge.ok .relation-status-dot { background:#23c552; }
        .relation-status-badge.warn .relation-status-dot { background:#f4b400; }
        .relation-status-badge.danger .relation-status-dot { background:#ef3e42; }
        .relation-status-badge.info .relation-status-dot { background:#039be5; }
        .relation-help-mark {
          display:inline-flex;
          align-items:center;
          justify-content:center;
          width:18px;
          height:18px;
          border-radius:50%;
          border:1px solid currentColor;
          font-size:12px;
          line-height:1;
        }
        .settings-relation-help {
          margin-top:9px;
          padding:8px 10px;
          border-radius:8px;
          background:var(--secondary-background-color);
          line-height:1.4;
          font-size:14px;
        }
        .settings-relation-help.ok { border-left:4px solid #23c552; }
        .settings-relation-help.warn { border-left:4px solid #f4b400; }
        .settings-relation-help.danger { border-left:4px solid #ef3e42; }
        .settings-relation-help.info { border-left:4px solid #039be5; }
        .settings-relation-help.unknown { border-left:4px solid #9e9e9e; }
        @media (max-width:650px) {
          .settings-relation-head { align-items:flex-start; flex-direction:column; gap:2px; }
          .relation-status-badge { flex:1 1 auto; justify-content:center; }
        }
      `;
      this.shadowRoot.appendChild(style);
    };

    proto._autarcoRelationStatusVersion = RELATION_STATUS_VERSION;
  }
}
