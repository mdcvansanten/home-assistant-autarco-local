// v0.6.6 streamlined unlock-to-preflight flow + explicit verified-success UX.
//
// When a user starts an allowed write while Settings are locked, remember that
// intent, unlock with the PIN, and continue directly into a fresh preflight after
// the backend accepted the PIN. The actual inverter write still requires the
// separate one-session confirmation checkbox.
//
// A successful write service call only returns after backend post-restore
// verification has completed, so the success message explicitly says the target
// survived the complete work-mode restore and repeated read-backs.

const PANEL_FLOW_UX_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_FLOW_UX_V066) {
  const proto = PANEL_FLOW_UX_V066.prototype;
  const FLOW_UX_VERSION = "0.6.6.12";

  if (proto._autarcoFlowUxVersion !== FLOW_UX_VERSION) {
    const previousOffGridControls = proto._offGridControls;
    proto._offGridControls = function offGridControlsWithDirectUnlock(entity) {
      const current = this._number("off_grid_minimum_soc");
      const writeAvailable = this._serviceAvailable("set_off_grid_minimum_soc");
      const formatted = this._escape(this._formatState(entity));

      if (
        current !== null &&
        current >= 10 &&
        current <= 100 &&
        writeAvailable &&
        !this._isUnlocked()
      ) {
        return `<div class="controls"><div class="value locked">🔒 ${formatted}</div><button class="primary small" data-action="unlock-for-preflight">Wijzigen</button></div>`;
      }

      return previousOffGridControls.call(this, entity);
    };

    function startFreshPreflight(instance) {
      instance._offGridTargetTouched = false;
      instance._offGridTarget = null;
      instance._preflightSessionId = (instance._preflightSessionId || 0) + 1;
      instance._preflightConfirmedSession = null;
      instance._confirmWriteChecked = false;
      instance._writeMessage = null;
      instance._preflightOpen = true;
    }

    const previousUnlock = proto._unlock;
    proto._unlock = async function unlockAndContinue() {
      await previousUnlock.call(this);

      if (
        this._pendingSettingsAction === "off-grid-preflight" &&
        this._isUnlocked() &&
        !this._unlockOpen
      ) {
        this._pendingSettingsAction = null;
        startFreshPreflight(this);
        this.render();
      }
    };

    const previousPerformWrite = proto._performWrite;
    proto._performWrite = async function performWriteWithVerifiedSuccessText() {
      const current = this._number("off_grid_minimum_soc");
      const target = Number(this._offGridTarget);
      const result = await previousPerformWrite.call(this);

      if (
        !this._preflightOpen &&
        this._writeMessage &&
        this._writeMessage.type === "success" &&
        Number.isInteger(target) &&
        current !== null
      ) {
        this._writeMessage = {
          type: "success",
          text:
            `Wijziging ${current}% → ${target}% definitief bevestigd. ` +
            "De doelwaarde bleef na volledig herstel van de oorspronkelijke work-mode " +
            "stabiel tijdens 3 extra post-restore read-backs (ca. 7,5 s)."
        };
        this.render();
      }

      return result;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindDirectUnlockFlow() {
      if (previousBindEvents) previousBindEvents.call(this);

      const unlockForPreflight = this.shadowRoot.querySelector(
        '[data-action="unlock-for-preflight"]'
      );
      if (unlockForPreflight) {
        unlockForPreflight.addEventListener("click", () => {
          this._pendingSettingsAction = "off-grid-preflight";
          this._unlockOpen = true;
          this._unlockError = "";
          this.render();
        });
      }

      const normalUnlock = this.shadowRoot.querySelector(
        '[data-action="open-unlock"]'
      );
      if (normalUnlock) {
        normalUnlock.addEventListener(
          "click",
          () => {
            this._pendingSettingsAction = null;
          },
          { capture: true }
        );
      }

      const cancelUnlock = this.shadowRoot.querySelector(
        '[data-action="cancel-unlock"]'
      );
      if (cancelUnlock) {
        cancelUnlock.addEventListener(
          "click",
          () => {
            this._pendingSettingsAction = null;
          },
          { capture: true }
        );
      }
    };

    proto._autarcoFlowUxVersion = FLOW_UX_VERSION;
  }
}
