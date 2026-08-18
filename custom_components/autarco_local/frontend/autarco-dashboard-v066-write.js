// v0.6.6 write/preflight extension for the single validated Off-grid minimum SOC setting.

const PANEL_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V066) {
  const proto = PANEL_V066.prototype;
  const baseRender = proto.render;

  proto._offGridControls = function offGridRangeControls(entity) {
    const current = this._number("off_grid_minimum_soc");
    const writeAvailable = this._serviceAvailable("set_off_grid_minimum_soc");
    const formatted = this._escape(this._formatState(entity));

    if (current === null || current < 10 || current > 100) {
      return `<div class="controls" title="Waarde valt buiten het gevalideerde bereik"><div class="value locked">🔒 ${formatted}</div></div>`;
    }

    if (writeAvailable && this._isUnlocked()) {
      return `<div class="controls"><div class="value">${formatted}</div><button class="primary small" data-action="open-preflight">Wijzigen</button></div>`;
    }

    return `<div class="controls" title="Ontgrendel instellingen om te wijzigen"><div class="value locked">🔒 ${formatted}</div></div>`;
  };

  proto._preflight = function offGridRangePreflight() {
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

    if (this._offGridTarget == null || this._offGridTarget === current) {
      this._offGridTarget = current == null ? 20 : (current < 100 ? current + 1 : current - 1);
    }
    const target = Number(this._offGridTarget);
    const targetValid = Number.isInteger(target) && target >= 10 && target <= 100 && target !== current;
    const canExecute = this._isUnlocked() && safe && current !== null && targetValid && !this._writeBusy;

    const dependency = offGridOn
      ? "Off-grid staat al AAN. Autarco Local verandert deze mode niet; hij blijft na de SOC-wijziging AAN."
      : "Voor deze instelling moet Off-grid tijdelijk actief zijn. Autarco Local bewaart de complete work-mode, activeert Off-grid alleen voor de write en herstelt daarna de oorspronkelijke state.";
    const safety = !temporary
      ? "Geen tijdelijke modewissel nodig."
      : batterySoc === null
        ? "Geblokkeerd: de actuele batterij-SOC is niet betrouwbaar beschikbaar."
        : batterySoc < 30
          ? `Geblokkeerd: batterij-SOC is ${batterySoc}%. Voor tijdelijke Off-grid-activatie is minimaal 30% vereist.`
          : `Batterij-SOC is ${batterySoc}%. De 30%-veiligheidsgrens voor deze hardwaretest is gehaald.`;

    return `
      <div class="backdrop">
        <div class="dialog wide" role="dialog" aria-modal="true">
          <div class="dialog-head">
            <div><div class="eyebrow">🟡 Expert-wijziging · hardwaretest</div><h3>Minimum-SOC off-grid wijzigen</h3></div>
            <button class="close" data-action="cancel-preflight" ${this._writeBusy ? "disabled" : ""}>×</button>
          </div>

          <div class="target v066-target">
            <span>Huidige waarde</span><strong>${current == null ? "?" : this._escape(current)}%</strong>
            <span>Nieuwe waarde</span>
            <div class="target-input-wrap"><input id="off-grid-target" type="number" min="10" max="100" step="1" value="${this._escape(target)}"><strong>%</strong></div>
          </div>
          <div class="hint">Voor de eerste hardwaretest: 20% → 21%. Na controle zetten we hem desgewenst via dezelfde route terug naar 20%.</div>

          <h4>Huidige situatie</h4>
          <div class="pregrid">
            <div><span>Self-use</span><strong>${this._escape(selfUse)}</strong></div>
            <div><span>Off-grid</span><strong>${this._escape(offGrid)}</strong></div>
            <div><span>Minimum battery SOC</span><strong>${this._escape(minimum)}</strong></div>
            <div><span>Force-charge SOC</span><strong>${this._escape(force)}</strong></div>
            <div><span>Laden vanuit net</span><strong>${this._escape(gridCharging)}</strong></div>
            <div><span>Live batterij-SOC</span><strong>${this._escape(battery)}</strong></div>
          </div>

          <h4>Afhankelijkheid</h4>
          <div class="callout">${this._escape(dependency)}</div>
          <div class="callout ${safe ? "ok" : "bad"}">${this._escape(safety)}</div>

          <h4>Autarco Local zal</h4>
          <ol>
            <li>Een verse settings-read uitvoeren en huidige SOC + volledige work-mode vastleggen.</li>
            <li>${offGridOn ? "Off-grid ongemoeid laten omdat deze al actief is." : "Off-grid tijdelijk activeren en die activatie via read-back bevestigen."}</li>
            <li>Alleen holding-register 43137 naar de gekozen waarde schrijven.</li>
            <li>De nieuwe SOC via read-back bevestigen.</li>
            <li>${offGridOn ? "Off-grid AAN laten, omdat die toestand al van jou was." : "De oorspronkelijke complete work-mode terugzetten en via read-back bevestigen."}</li>
            <li>De oude/nieuwe waarde, dependency-afhandeling, duur en eventuele fout vastleggen in de write-diagnose.</li>
          </ol>

          <label class="confirm">
            <input id="confirm-write" type="checkbox" ${canExecute ? "" : "disabled"}>
            <span>Ik bevestig deze wijziging en de hierboven beschreven tijdelijke mode-afhandeling.</span>
          </label>
          <div class="dialog-actions">
            <button class="secondary" data-action="cancel-preflight" ${this._writeBusy ? "disabled" : ""}>Annuleren</button>
            <button class="primary" data-action="confirm-write" disabled>${this._writeBusy ? "Bezig…" : "Bevestig wijziging"}</button>
          </div>
        </div>
      </div>`;
  };

  proto._performWrite = async function performRangeWrite() {
    if (this._writeBusy || !this._isUnlocked()) return;
    const current = this._number("off_grid_minimum_soc");
    const target = Number(this._offGridTarget);
    if (!Number.isInteger(target) || target < 10 || target > 100) {
      this._writeMessage = { type: "error", text: "Ongeldige doelwaarde. Kies een heel percentage van 10 t/m 100." };
      this.render();
      return;
    }
    if (target === current) {
      this._writeMessage = { type: "progress", text: "Geen wijziging nodig: de gekozen waarde is gelijk aan de actuele waarde." };
      this._preflightOpen = false;
      this.render();
      return;
    }

    this._writeBusy = true;
    this._writeMessage = {
      type: "progress",
      text: `Write ${current}% → ${target}% gestart: pre-read, dependency-check, write, read-back en eventueel herstel worden uitgevoerd.`
    };
    this.render();
    try {
      await this._hass.callService("autarco_local", "set_off_grid_minimum_soc", { soc: target, confirm: true });
      this._writeMessage = {
        type: "success",
        text: `Wijziging ${current}% → ${target}% bevestigd. Doelwaarde en work-mode state zijn door de backend gecontroleerd.`
      };
      this._preflightOpen = false;
      this._offGridTarget = null;
    } catch (error) {
      this._writeMessage = {
        type: "error",
        text: "Write mislukt of afgebroken: " + ((error && error.message) ? error.message : String(error))
      };
    } finally {
      this._writeBusy = false;
      this.render();
    }
  };

  const previousBindEvents = proto._bindEvents;
  proto._bindEvents = function bindV066RangeEvents() {
    if (previousBindEvents) previousBindEvents.call(this);
    const input = this.shadowRoot.querySelector("#off-grid-target");
    const checkbox = this.shadowRoot.querySelector("#confirm-write");
    const confirmButton = this.shadowRoot.querySelector('[data-action="confirm-write"]');
    if (input) {
      const refreshValidity = () => {
        const value = Number(input.value);
        this._offGridTarget = value;
        const current = this._number("off_grid_minimum_soc");
        const valid = Number.isInteger(value) && value >= 10 && value <= 100 && value !== current;
        if (checkbox) {
          checkbox.disabled = !valid;
          if (!valid) checkbox.checked = false;
        }
        if (confirmButton) confirmButton.disabled = !valid || !checkbox || !checkbox.checked || this._writeBusy;
      };
      input.addEventListener("input", refreshValidity);
      input.addEventListener("change", refreshValidity);
    }
  };

  proto.render = function renderWithV066Styles() {
    baseRender.call(this);
    if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v066-styles")) return;
    const style = document.createElement("style");
    style.id = "autarco-v066-styles";
    style.textContent = `
      .dashboard-block { margin-top:16px; padding:15px; border:1px solid var(--divider-color); border-radius:12px; background:var(--card-background-color); }
      .dashboard-block.compact p { margin:5px 0; }
      .dashboard-columns { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
      .scenario-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; padding:0 16px 16px; border-top:1px solid var(--divider-color); padding-top:14px; }
      .scenario-card { border:1px solid var(--divider-color); border-radius:10px; padding:13px; background:var(--secondary-background-color); }
      .scenario-card p { color:var(--secondary-text-color); line-height:1.45; min-height:42px; }
      .scenario-title { font-size:17px; font-weight:700; margin-bottom:5px; }
      .scenario-state { display:inline-block; margin-top:4px; padding:5px 8px; border-radius:999px; font-size:12px; background:var(--card-background-color); color:var(--secondary-text-color); }
      .scenario-state.basis { border:1px solid var(--warning-color,#f4b400); }
      .target-input-wrap { display:flex; align-items:center; gap:6px; }
      .target-input-wrap input { width:90px; padding:7px 9px; border:1px solid var(--divider-color); border-radius:8px; background:var(--primary-background-color); color:var(--primary-text-color); font-size:18px; }
      .v066-target { display:grid; grid-template-columns:1fr auto; }
      @media (max-width:650px) { .dashboard-columns { grid-template-columns:1fr; } }
    `;
    this.shadowRoot.appendChild(style);
  };
}
