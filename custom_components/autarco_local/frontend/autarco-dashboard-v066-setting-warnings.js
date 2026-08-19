// v0.6.6 concise dependency/effect warnings for inverter settings.
//
// These warnings are deliberately derived from settings we already read and
// understand. They do not invent new register semantics and do not change any
// write permission. The same warning logic is also shown while choosing an
// Off-grid minimum SOC target.

const PANEL_SETTING_WARNINGS_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_SETTING_WARNINGS_V066) {
  const proto = PANEL_SETTING_WARNINGS_V066.prototype;
  const WARNING_VERSION = "0.6.6.13";

  if (proto._autarcoSettingWarningsVersion !== WARNING_VERSION) {
    const numberValue = (instance, key) => {
      const value = instance._number(key);
      return Number.isFinite(value) ? Number(value) : null;
    };

    const stateText = (instance, key) => {
      const entity = instance._findState(key);
      if (!entity) return "";
      return String(entity.state || "").trim().toLowerCase();
    };

    const hasConfiguredSlot = (instance, key) => {
      const value = stateText(instance, key);
      return Boolean(value) && !["00:00", "0:00", "unknown", "unavailable", "none"].includes(value);
    };

    const timeKeys = [
      "charge_slot_1_start", "charge_slot_1_end",
      "discharge_slot_1_start", "discharge_slot_1_end",
      "charge_slot_2_start", "charge_slot_2_end",
      "discharge_slot_2_start", "discharge_slot_2_end",
      "charge_slot_3_start", "charge_slot_3_end",
      "discharge_slot_3_start", "discharge_slot_3_end"
    ];

    const timeOfUseConfigured = (instance) => {
      const charge = numberValue(instance, "scheduled_charge_current") || 0;
      const discharge = numberValue(instance, "scheduled_discharge_current") || 0;
      return charge > 0 || discharge > 0 || timeKeys.some((key) => hasConfiguredSlot(instance, key));
    };

    const warningForSetting = (instance, key) => {
      const minimum = numberValue(instance, "minimum_battery_soc");
      const offGridMinimum = numberValue(instance, "off_grid_minimum_soc");
      const forceCharge = numberValue(instance, "force_charge_soc");
      const reserve = numberValue(instance, "reserve_soc");
      const gridCharging = instance._isOn("allow_grid_charging");
      const reserveMode = instance._isOn("reserve_battery_mode");
      const timeOfUse = instance._isOn("time_of_use_mode");

      if (key === "off_grid_minimum_soc" && minimum !== null && offGridMinimum !== null) {
        if (offGridMinimum < minimum) {
          return {
            level: "warn",
            text: `⚠ Off-grid ${offGridMinimum}% < normaal minimum ${minimum}%: alleen Off-grid kan zo laag ontladen; netgekoppeld blijft ${minimum}% de ontlaadgrens.`
          };
        }
        if (offGridMinimum > minimum) {
          return {
            level: "info",
            text: `ℹ Off-grid stopt eerder met ontladen: ${offGridMinimum}% i.p.v. normaal ${minimum}%.`
          };
        }
      }

      if (key === "force_charge_soc" && forceCharge !== null) {
        if (minimum !== null && forceCharge >= minimum) {
          return {
            level: "danger",
            text: `⚠ Force-charge ${forceCharge}% hoort lager te zijn dan Minimum battery SOC ${minimum}%.`
          };
        }
        if (gridCharging) {
          return {
            level: "warn",
            text: `⚡ Onder ${forceCharge}% kan netladen starten.`
          };
        }
        return {
          level: "info",
          text: `ℹ Force-charge ${forceCharge}%, maar netladen staat uit.`
        };
      }

      if (key === "allow_grid_charging" && gridCharging && forceCharge !== null) {
        return {
          level: "warn",
          text: `⚡ Netladen toegestaan: onder Force-charge ${forceCharge}% kan de accu via het net laden.`
        };
      }

      if (key === "reserve_soc" && reserve !== null) {
        if (minimum !== null && reserve < minimum) {
          return {
            level: "danger",
            text: `⚠ Reserve SOC ${reserve}% < Minimum battery SOC ${minimum}%.`
          };
        }
        if (!reserveMode) {
          return {
            level: "info",
            text: "ℹ Reserve mode uit: deze waarde is nu niet actief."
          };
        }
      }

      if (key === "off_grid_mode" && instance._isOn("off_grid_mode")) {
        return {
          level: "danger",
          text: "⚠ Off-grid AAN: alleen gebruiken met geschikte elektrische omschakeling."
        };
      }

      if (key === "time_of_use_mode" && !timeOfUse && timeOfUseConfigured(instance)) {
        return {
          level: "info",
          text: "ℹ Time-of-use uit: geplande laad/ontlaadwaarden zijn nu niet actief."
        };
      }

      if (
        ["scheduled_charge_current", "scheduled_discharge_current"].includes(key) &&
        !timeOfUse &&
        (numberValue(instance, key) || 0) > 0
      ) {
        return {
          level: "info",
          text: "ℹ Time-of-use uit: deze ingestelde stroom is nu niet actief."
        };
      }

      if (timeKeys.includes(key) && !timeOfUse && hasConfiguredSlot(instance, key)) {
        return {
          level: "info",
          text: "ℹ Time-of-use uit: dit tijdstip is nu niet actief."
        };
      }

      return null;
    };

    const targetWarning = (instance, target) => {
      const minimum = numberValue(instance, "minimum_battery_soc");
      if (minimum === null || !Number.isFinite(target)) return null;
      if (target < minimum) {
        return {
          level: "warn",
          text: `⚠ Lager dan Minimum battery SOC (${minimum}%). Alleen Off-grid kan tot ${target}% ontladen; netgekoppeld blijft ${minimum}% de ontlaadgrens.`
        };
      }
      if (target > minimum) {
        return {
          level: "info",
          text: `ℹ Off-grid stopt dan eerder met ontladen: ${target}% i.p.v. normaal ${minimum}%.`
        };
      }
      return null;
    };

    const warningHtml = (instance, warning, id = "") => {
      if (!warning) {
        return id ? `<div id="${id}" class="setting-warning" hidden></div>` : "";
      }
      const idAttr = id ? ` id="${id}"` : "";
      return `<div${idAttr} class="setting-warning ${warning.level}">${instance._escape(warning.text)}</div>`;
    };

    const previousSettingRow = proto._settingRow;
    proto._settingRow = function settingRowWithWarnings(item, group) {
      let html = previousSettingRow.call(this, item, group);
      const key = item && item[0];
      if (!key) return html;
      const warning = warningForSetting(this, key);
      if (!warning) return html;

      const insertAt = html.lastIndexOf("</div>");
      if (insertAt < 0) return html;
      html =
        html.slice(0, insertAt) +
        warningHtml(this, warning) +
        html.slice(insertAt);
      return html;
    };

    const previousPreflight = proto._preflight;
    proto._preflight = function preflightWithTargetRelationWarning() {
      let html = previousPreflight.call(this);
      if (!this._preflightOpen) return html;

      const target = Number(this._offGridTarget);
      const relationWarning = targetWarning(this, target);
      const block = warningHtml(this, relationWarning, "off-grid-target-relation-warning");

      const hintPattern = /(<div class="hint">[\s\S]*?<\/div>)/;
      if (hintPattern.test(html)) {
        html = html.replace(hintPattern, `$1${block}`);
      } else {
        const targetPattern = /(<div class="target v066-target">[\s\S]*?<\/div>)/;
        html = html.replace(targetPattern, `$1${block}`);
      }
      return html;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindSettingWarningUpdates() {
      if (previousBindEvents) previousBindEvents.call(this);

      const input = this.shadowRoot.querySelector("#off-grid-target");
      const warningNode = this.shadowRoot.querySelector("#off-grid-target-relation-warning");
      if (input && warningNode) {
        const refreshWarning = () => {
          const warning = targetWarning(this, Number(input.value));
          if (!warning) {
            warningNode.hidden = true;
            warningNode.textContent = "";
            warningNode.className = "setting-warning";
            return;
          }
          warningNode.hidden = false;
          warningNode.textContent = warning.text;
          warningNode.className = `setting-warning ${warning.level}`;
        };
        input.addEventListener("input", refreshWarning);
        input.addEventListener("change", refreshWarning);
        refreshWarning();
      }
    };

    const previousRender = proto.render;
    proto.render = function renderWithSettingWarningStyles() {
      previousRender.call(this);
      if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-setting-warning-styles")) return;
      const style = document.createElement("style");
      style.id = "autarco-setting-warning-styles";
      style.textContent = `
        .setting-warning {
          margin:8px 0 0 22px;
          padding:8px 10px;
          border-radius:8px;
          background:var(--secondary-background-color);
          line-height:1.4;
          font-size:14px;
        }
        .setting-warning.warn { border-left:4px solid var(--warning-color,#f4b400); }
        .setting-warning.danger { border-left:4px solid var(--error-color,#db4437); }
        .setting-warning.info { border-left:4px solid var(--info-color,#039be5); }
        #off-grid-target-relation-warning { margin-left:0; margin-top:8px; }
      `;
      this.shadowRoot.appendChild(style);
    };

    proto._autarcoSettingWarningsVersion = WARNING_VERSION;
  }
}
