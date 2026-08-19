// v0.7.0 guided Reserve SOC write test.
// This intentionally opens only the next low-impact hardware test and does not
// generalize physical writes to other settings.

const PANEL_RESERVE_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_RESERVE_V070) {
  const proto = PANEL_RESERVE_V070.prototype;
  const VERSION = "0.7.0.3";

  if (proto._autarcoReserveWriteV070Version !== VERSION) {
    const previousSettingRow = proto._settingRow;
    proto._settingRow = function settingRowWithReserveTest(item, group) {
      const key = item && item[0];
      if (key !== "reserve_soc") return previousSettingRow.call(this, item, group);

      const label = item[1];
      const description = item[2];
      const entity = this._findState("reserve_soc");
      const available = Boolean(entity) && !["unknown", "unavailable"].includes(String(entity.state).toLowerCase());
      const serviceAvailable = this._serviceAvailable("test_reserve_soc");
      const value = this._escape(this._formatState(entity));
      const control = serviceAvailable
        ? `<div class="controls"><div class="value">${value}</div><button class="primary" data-action="v070-open-reserve" ${available ? "" : "disabled"}>Wijzigen</button></div>`
        : `<div class="value locked">🔒 ${value}</div>`;
      const message = this._v070ReserveWriteMessage
        ? `<div class="write-message ${this._escape(this._v070ReserveWriteMessage.type)}">${this._escape(this._v070ReserveWriteMessage.text)}</div>`
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
    };

    proto._v070ReservePreflight = function reservePreflight() {
      const current = this._number("reserve_soc");
      const minimum = this._number("minimum_battery_soc");
      const selfUse = this._isOn("self_use_mode");
      const offGrid = this._isOn("off_grid_mode");
      const reserveMode = this._isOn("reserve_battery_mode");
      if (this._v070ReserveTarget == null && current != null) this._v070ReserveTarget = current;
      const target = Number(this._v070ReserveTarget);
      const floor = Math.max(20, Number.isFinite(minimum) ? minimum : 20);
      const validTarget = Number.isInteger(target)
        && current != null
        && Math.abs(target - current) === 1
        && target >= floor
        && target <= 100;
      const modeSafe = selfUse && !offGrid && !reserveMode;
      const canConfirm = validTarget && modeSafe && !this._v070ReserveBusy;
      const checked = Boolean(this._v070ReserveConfirmed) && canConfirm;
      let modeNote;
      if (!selfUse || offGrid || reserveMode) {
        const reasons = [];
        if (!selfUse) reasons.push("Self-use staat UIT");
        if (offGrid) reasons.push("Off-grid staat AAN");
        if (reserveMode) reasons.push("Reserve mode staat AAN");
        modeNote = `<div class="v070-reserve-warning danger"><strong>Geblokkeerd</strong><span>${this._escape(reasons.join(" · "))}. De eerste Reserve SOC-test vereist Self-use AAN, Off-grid UIT en Reserve mode UIT.</span></div>`;
      } else {
        modeNote = `<div class="v070-reserve-warning ok"><strong>Veilige testsituatie</strong><span>Self-use is AAN; Off-grid en Reserve mode zijn UIT. Reserve SOC is daardoor niet actief als reserve-doelwaarde tijdens deze mapping/write-test.</span></div>`;
      }
      const targetNote = current == null
        ? "Actuele Reserve SOC is niet beschikbaar."
        : validTarget
          ? `Teststap ${current}% → ${target}% is toegestaan.`
          : `Kies voor deze hardwaretest precies één procentpunt hoger of lager dan ${current}%, met minimaal ${floor}%.`;

      return `
        <div class="backdrop" id="v070-reserve-backdrop">
          <div class="dialog v070-reserve-dialog">
            <div class="dialog-head">
              <div><span class="eyebrow">🟢 Standaardinstelling · hardwaretest</span><h2>Reserve SOC wijzigen</h2></div>
              <button class="icon" data-action="v070-cancel-reserve" ${this._v070ReserveBusy ? "disabled" : ""}>×</button>
            </div>

            <div class="pregrid">
              <div><span>Huidige waarde</span><strong>${current == null ? "—" : `${current}%`}</strong></div>
              <label><span>Nieuwe waarde</span><div class="input-suffix"><input id="v070-reserve-target" type="number" min="20" max="100" step="1" value="${this._escape(current == null ? "" : target)}" ${this._v070ReserveBusy ? "disabled" : ""}><b>%</b></div></label>
            </div>
            <p class="muted">De doelwaarde start op de actuele waarde. Voor deze eerste test is alleen ±1 procentpunt toegestaan.</p>

            <h3>Huidige situatie</h3>
            <div class="pregrid">
              <div><span>Self-use</span><strong>${selfUse ? "On" : "Off"}</strong></div>
              <div><span>Off-grid</span><strong>${offGrid ? "On" : "Off"}</strong></div>
              <div><span>Reserve battery mode</span><strong>${reserveMode ? "On" : "Off"}</strong></div>
              <div><span>Minimum battery SOC</span><strong>${minimum == null ? "—" : `${minimum}%`}</strong></div>
            </div>

            ${modeNote}
            <div class="v070-reserve-warning ${validTarget ? "ok" : "warn"}"><span>${this._escape(targetNote)}</span></div>

            <h3>Autarco Local zal</h3>
            <ol>
              <li>Reserve SOC, Minimum battery SOC en complete work-mode vers uitlezen.</li>
              <li>Afbreken tenzij Self-use AAN, Off-grid UIT en Reserve mode UIT zijn.</li>
              <li>Alleen register 43024 één procentpunt wijzigen.</li>
              <li>De doelwaarde direct via read-back bevestigen.</li>
              <li>Daarna drie extra stabiliteitsreads uitvoeren.</li>
              <li>Geen work-mode of andere setting automatisch wijzigen.</li>
            </ol>

            <label class="confirm ${canConfirm ? "" : "disabled"}">
              <input id="v070-confirm-reserve" type="checkbox" ${checked ? "checked" : ""} ${canConfirm ? "" : "disabled"}>
              <span>Ik bevestig deze beperkte en reversibele Reserve SOC hardwaretest.</span>
            </label>

            <div class="dialog-actions">
              <button class="secondary" data-action="v070-cancel-reserve" ${this._v070ReserveBusy ? "disabled" : ""}>Annuleren</button>
              <button class="primary" data-action="v070-confirm-reserve" ${checked && canConfirm ? "" : "disabled"}>${this._v070ReserveBusy ? "Bezig…" : "Bevestig wijziging"}</button>
            </div>
          </div>
        </div>`;
    };

    const previousSettings = proto._settings;
    proto._settings = function settingsWithReservePreflight() {
      const html = previousSettings.call(this);
      return this._v070ReservePreflightOpen ? html + this._v070ReservePreflight() : html;
    };

    proto._v070OpenReserveTest = function openReserveTest() {
      const current = this._number("reserve_soc");
      this._v070ReserveTarget = current;
      this._v070ReserveConfirmed = false;
      this._v070ReservePreflightOpen = true;
      this._v070ReserveWriteMessage = null;
      this.render();
    };

    const previousUnlock = proto._unlock;
    proto._unlock = async function unlockThenContinueReserve() {
      await previousUnlock.call(this);
      if (this._v070PendingReserveWrite && this._isUnlocked() && !this._unlockOpen) {
        this._v070PendingReserveWrite = false;
        this._v070OpenReserveTest();
      }
    };

    proto._v070PerformReserveTest = async function performReserveTest() {
      const current = this._number("reserve_soc");
      const target = Number(this._v070ReserveTarget);
      if (current == null || !Number.isInteger(target) || Math.abs(target - current) !== 1) return;
      if (!this._v070ReserveConfirmed) return;
      if (!this._isOn("self_use_mode") || this._isOn("off_grid_mode") || this._isOn("reserve_battery_mode")) return;

      this._v070ReserveBusy = true;
      this.render();
      try {
        await this._hass.callService("autarco_local", "test_reserve_soc", {
          soc: target,
          confirm: true
        });
        this._v070ReserveWriteMessage = {
          type: "success",
          text: `Reserve SOC ${current}% → ${target}% door backend bevestigd en drie keer stabiel teruggelezen.`
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
    proto._bindEvents = function bindReserveWriteEvents() {
      if (previousBindEvents) previousBindEvents.call(this);

      const open = this.shadowRoot && this.shadowRoot.querySelector('[data-action="v070-open-reserve"]');
      if (open) open.addEventListener("click", () => {
        if (!this._isUnlocked()) {
          this._v070PendingReserveWrite = true;
          this._unlockOpen = true;
          this._unlockError = "";
          this.render();
          return;
        }
        this._v070OpenReserveTest();
      });

      this.shadowRoot && this.shadowRoot.querySelectorAll('[data-action="v070-cancel-reserve"]').forEach((button) => {
        button.addEventListener("click", () => {
          if (this._v070ReserveBusy) return;
          this._v070ReservePreflightOpen = false;
          this._v070ReserveConfirmed = false;
          this._v070ReserveTarget = null;
          this.render();
        });
      });

      const target = this.shadowRoot && this.shadowRoot.querySelector("#v070-reserve-target");
      if (target) {
        target.addEventListener("input", () => {
          this._v070ReserveTarget = Number(target.value);
          this._v070ReserveConfirmed = false;
          this.render();
        });
      }

      const confirm = this.shadowRoot && this.shadowRoot.querySelector("#v070-confirm-reserve");
      if (confirm) {
        confirm.addEventListener("change", () => {
          this._v070ReserveConfirmed = Boolean(confirm.checked);
          this.render();
        });
      }

      const submit = this.shadowRoot && this.shadowRoot.querySelector('[data-action="v070-confirm-reserve"]');
      if (submit) submit.addEventListener("click", () => this._v070PerformReserveTest());
    };

    const previousRender = proto.render;
    proto.render = function renderReserveWriteStyles() {
      previousRender.call(this);
      if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v070-reserve-style")) return;
      const style = document.createElement("style");
      style.id = "autarco-v070-reserve-style";
      style.textContent = `
        .v070-reserve-dialog { max-width:760px; }
        .v070-reserve-warning { display:flex; flex-direction:column; gap:3px; margin:10px 0; padding:10px 12px; border-radius:9px; background:var(--secondary-background-color); }
        .v070-reserve-warning.ok { border-left:4px solid #23c552; }
        .v070-reserve-warning.warn { border-left:4px solid #f4b400; }
        .v070-reserve-warning.danger { border-left:4px solid #ef3e42; }
        .confirm.disabled { opacity:.65; }
      `;
      this.shadowRoot.appendChild(style);
    };

    proto._autarcoReserveWriteV070Version = VERSION;
  }
}
