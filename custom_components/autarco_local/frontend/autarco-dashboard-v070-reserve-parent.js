// v0.7.0 Reserve SOC parent-mode dependency validation.
//
// Direct hardware testing showed that register 43024 reads correctly while a
// write is ignored when Battery Reserve mode is OFF.  For the next validation
// step Autarco Local therefore does NOT toggle that parent mode itself.  The
// user enables Reserve mode in the official/local inverter UI first, while
// Allow Grid Charging remains OFF.  This layer then permits only the existing
// one-percentage-point 43024 test and leaves the complete work-mode untouched.

const PANEL_RESERVE_PARENT_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_RESERVE_PARENT_V070) {
  const proto = PANEL_RESERVE_PARENT_V070.prototype;
  const VERSION = "0.7.0.1";

  if (proto._autarcoReserveParentV070Version !== VERSION) {
    proto._v070ReservePreflight = function reserveParentPreflight() {
      const current = this._number("reserve_soc");
      const minimum = this._number("minimum_battery_soc");
      const selfUse = this._isOn("self_use_mode");
      const offGrid = this._isOn("off_grid_mode");
      const reserveMode = this._isOn("reserve_battery_mode");
      const gridCharging = this._isOn("allow_grid_charging");

      if (this._v070ReserveTarget == null && current != null) {
        this._v070ReserveTarget = current;
      }

      const target = Number(this._v070ReserveTarget);
      const floor = Math.max(20, Number.isFinite(minimum) ? minimum : 20);
      const validTarget = Number.isInteger(target)
        && current != null
        && Math.abs(target - current) === 1
        && target >= floor
        && target <= 100;
      const modeSafe = selfUse && !offGrid && reserveMode && !gridCharging;
      const canConfirm = validTarget && modeSafe && !this._v070ReserveBusy;
      const checked = Boolean(this._v070ReserveConfirmed) && canConfirm;

      const reasons = [];
      if (!selfUse) reasons.push("Self-use moet AAN staan");
      if (offGrid) reasons.push("Off-grid moet UIT staan");
      if (!reserveMode) reasons.push("Reserve battery mode moet eerst handmatig AAN");
      if (gridCharging) reasons.push("Laden vanuit net moet UIT staan");

      const modeNote = modeSafe
        ? `<div class="v070-reserve-warning ok"><strong>Dependency klaar voor test</strong><span>Reserve mode staat AAN en netladen UIT. Autarco Local wijzigt tijdens deze test alleen Reserve SOC en laat de complete work-mode ongemoeid.</span></div>`
        : `<div class="v070-reserve-warning danger"><strong>Nog niet testen</strong><span>${this._escape(reasons.join(" · "))}. Gebruik de officiële Solis/Autarco lokale bediening voor de parent-mode; Autarco Local schakelt hem in deze fase nog niet zelf.</span></div>`;

      const targetNote = current == null
        ? "Actuele Reserve SOC is niet beschikbaar."
        : validTarget
          ? `Teststap ${current}% → ${target}% is toegestaan.`
          : `Kies precies één procentpunt hoger of lager dan ${current}%, met minimaal ${floor}%.`;

      return `
        <div class="backdrop" id="v070-reserve-backdrop">
          <div class="dialog wide v070-reserve-dialog" role="dialog" aria-modal="true">
            <div class="dialog-head">
              <div><span class="eyebrow">🟢 Standaardinstelling · dependencytest</span><h2>Reserve SOC wijzigen</h2></div>
              <button class="close" data-action="v070-cancel-reserve" ${this._v070ReserveBusy ? "disabled" : ""}>×</button>
            </div>

            <div class="pregrid">
              <div><span>Huidige waarde</span><strong>${current == null ? "—" : `${current}%`}</strong></div>
              <label><span>Nieuwe waarde</span><div class="input-suffix"><input id="v070-reserve-target" type="number" min="20" max="100" step="1" value="${this._escape(current == null ? "" : target)}" ${this._v070ReserveBusy ? "disabled" : ""}><b>%</b></div></label>
            </div>
            <p class="muted">De vorige test bewees dat 43024 niet wijzigt terwijl Reserve mode UIT staat. Deze test controleert dezelfde write met de parent-mode handmatig AAN.</p>

            <h3>Huidige situatie</h3>
            <div class="pregrid">
              <div><span>Self-use</span><strong>${selfUse ? "On" : "Off"}</strong></div>
              <div><span>Off-grid</span><strong>${offGrid ? "On" : "Off"}</strong></div>
              <div><span>Reserve battery mode</span><strong>${reserveMode ? "On" : "Off"}</strong></div>
              <div><span>Laden vanuit net</span><strong>${gridCharging ? "On" : "Off"}</strong></div>
              <div><span>Minimum battery SOC</span><strong>${minimum == null ? "—" : `${minimum}%`}</strong></div>
            </div>

            ${modeNote}
            <div id="v070-reserve-target-note" class="v070-reserve-warning ${validTarget ? "ok" : "warn"}"><span>${this._escape(targetNote)}</span></div>

            <div class="v070-reserve-warning warn"><strong>Na de test</strong><span>Zet Reserve battery mode in de officiële lokale bediening weer UIT als dat jouw normale situatie is. Autarco Local verandert die mode in deze dependencytest bewust niet.</span></div>

            <h3>Autarco Local zal</h3>
            <ol>
              <li>Reserve SOC, Minimum battery SOC en complete work-mode vers uitlezen.</li>
              <li>Alleen doorgaan bij Self-use AAN, Off-grid UIT, Reserve mode AAN en netladen UIT.</li>
              <li>Alleen holding-register 43024 één procentpunt wijzigen.</li>
              <li>De doelwaarde direct via read-back bevestigen.</li>
              <li>Daarna drie extra stabiliteitsreads uitvoeren.</li>
              <li>Bevestigen dat de complete work-mode tijdens de test exact gelijk bleef.</li>
            </ol>

            <label class="confirm ${canConfirm ? "" : "disabled"}">
              <input id="v070-confirm-reserve" type="checkbox" ${checked ? "checked" : ""} ${canConfirm ? "" : "disabled"}>
              <span>Ik bevestig deze beperkte Reserve SOC dependencytest.</span>
            </label>

            <div class="dialog-actions">
              <button class="secondary" data-action="v070-cancel-reserve" ${this._v070ReserveBusy ? "disabled" : ""}>Annuleren</button>
              <button class="primary" data-action="v070-confirm-reserve" ${checked && canConfirm ? "" : "disabled"}>${this._v070ReserveBusy ? "Bezig…" : "Bevestig wijziging"}</button>
            </div>
          </div>
        </div>`;
    };

    proto._v070PerformReserveTest = async function performReserveParentTest() {
      const current = this._number("reserve_soc");
      const target = Number(this._v070ReserveTarget);
      const modeSafe = this._isOn("self_use_mode")
        && !this._isOn("off_grid_mode")
        && this._isOn("reserve_battery_mode")
        && !this._isOn("allow_grid_charging");

      if (current == null || !Number.isInteger(target) || Math.abs(target - current) !== 1) return;
      if (!this._v070ReserveConfirmed || !modeSafe) return;

      this._v070ReserveBusy = true;
      this.render();
      try {
        await this._hass.callService("autarco_local", "test_reserve_soc", {
          soc: target,
          confirm: true
        });
        this._v070ReserveWriteMessage = {
          type: "success",
          text: `Reserve SOC ${current}% → ${target}% bevestigd en drie keer stabiel teruggelezen terwijl Reserve mode AAN bleef; work-mode bleef ongewijzigd.`
        };
        this._v070ReservePreflightOpen = false;
        this._v070ReserveConfirmed = false;
        this._v070ReserveTarget = null;
      } catch (error) {
        this._v070ReserveWriteMessage = {
          type: "error",
          text: (error && error.message) ? error.message : String(error)
        };
      } finally {
        this._v070ReserveBusy = false;
        this.render();
      }
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindReserveParentEvents() {
      if (previousBindEvents) previousBindEvents.call(this);

      const target = this.shadowRoot && this.shadowRoot.querySelector("#v070-reserve-target");
      const confirm = this.shadowRoot && this.shadowRoot.querySelector("#v070-confirm-reserve");
      const submit = this.shadowRoot && this.shadowRoot.querySelector('[data-action="v070-confirm-reserve"]');

      const sync = () => {
        if (!target || !confirm || !submit) return;
        const current = this._number("reserve_soc");
        const minimum = this._number("minimum_battery_soc");
        const floor = Math.max(20, Number.isFinite(minimum) ? minimum : 20);
        const value = Number(target.value);
        const validTarget = Number.isInteger(value)
          && current != null
          && Math.abs(value - current) === 1
          && value >= floor
          && value <= 100;
        const modeSafe = this._isOn("self_use_mode")
          && !this._isOn("off_grid_mode")
          && this._isOn("reserve_battery_mode")
          && !this._isOn("allow_grid_charging");
        const valid = validTarget && modeSafe && !this._v070ReserveBusy;

        this._v070ReserveTarget = value;
        if (!valid) {
          this._v070ReserveConfirmed = false;
          confirm.checked = false;
        }
        confirm.disabled = !valid;
        const label = confirm.closest(".confirm");
        if (label) label.classList.toggle("disabled", !valid);
        submit.disabled = !valid || !this._v070ReserveConfirmed;

        const note = this.shadowRoot.querySelector("#v070-reserve-target-note");
        if (note) {
          note.className = `v070-reserve-warning ${validTarget ? "ok" : "warn"}`;
          note.textContent = validTarget
            ? `Teststap ${current}% → ${value}% is toegestaan.`
            : `Kies precies één procentpunt hoger of lager dan ${current}%, met minimaal ${floor}%.`;
        }
      };

      if (target) {
        target.addEventListener("input", () => {
          this._v070ReserveConfirmed = false;
          sync();
        });
        target.addEventListener("change", sync);
      }
      if (confirm) {
        confirm.addEventListener("change", () => {
          this._v070ReserveConfirmed = Boolean(confirm.checked);
          sync();
        });
      }
      sync();
    };

    proto._autarcoReserveParentV070Version = VERSION;
  }
}
