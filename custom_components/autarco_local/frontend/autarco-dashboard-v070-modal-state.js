// v0.7.0 modal-state coordinator.
//
// v0.6.6 knew only the unlock and Off-grid preflight dialogs. v0.7.0 adds a
// second write preflight (Reserve SOC), so explicitly coordinate both flows:
// exactly one settings preflight may be active, an open Reserve dialog must not
// be rebuilt by ordinary HA telemetry refreshes, and one Cancel click closes the
// complete write-preflight state.

const PANEL_MODAL_STATE_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_MODAL_STATE_V070) {
  const proto = PANEL_MODAL_STATE_V070.prototype;
  const VERSION = "0.7.0.1";

  if (proto._autarcoModalStateV070Version !== VERSION) {
    function clearOffGridPreflight(instance) {
      instance._preflightOpen = false;
      instance._confirmWriteChecked = false;
      instance._preflightConfirmed = false;
      instance._preflightConfirmedSession = null;
      instance._offGridTarget = null;
      instance._offGridTargetTouched = false;
      instance._pendingSettingsAction = null;
    }

    function clearReservePreflight(instance) {
      instance._v070ReservePreflightOpen = false;
      instance._v070ReserveConfirmed = false;
      instance._v070ReserveTarget = null;
      instance._v070PendingReserveWrite = false;
    }

    // Opening Reserve SOC always closes any stale Off-grid preflight state first.
    if (proto._v070OpenReserveTest) {
      const previousOpenReserve = proto._v070OpenReserveTest;
      proto._v070OpenReserveTest = function openOnlyReservePreflight() {
        clearOffGridPreflight(this);
        return previousOpenReserve.call(this);
      };
    }

    // The v0.6.6 HA-state setter suppresses renders only for the dialogs it knew
    // about. While Reserve SOC is open, keep the latest hass object but do not
    // rebuild the modal underneath the user's input.
    const hassDescriptor = Object.getOwnPropertyDescriptor(proto, "hass");
    if (hassDescriptor && hassDescriptor.set) {
      const previousGet = hassDescriptor.get;
      const previousSet = hassDescriptor.set;
      Object.defineProperty(proto, "hass", {
        configurable: true,
        enumerable: hassDescriptor.enumerable,
        get: previousGet,
        set(value) {
          if (this._v070ReservePreflightOpen) {
            this._hass = value;
            return;
          }
          previousSet.call(this, value);
        },
      });
    }

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindExclusiveSettingsModals() {
      if (previousBindEvents) previousBindEvents.call(this);
      if (!this.shadowRoot) return;

      // One click must close the Reserve dialog and any stale older preflight
      // that might otherwise become visible underneath it.
      this.shadowRoot
        .querySelectorAll('[data-action="v070-cancel-reserve"]')
        .forEach((button) => {
          button.addEventListener(
            "click",
            (event) => {
              if (this._v070ReserveBusy) return;
              event.preventDefault();
              event.stopImmediatePropagation();
              clearReservePreflight(this);
              clearOffGridPreflight(this);
              this.render();
            },
            { capture: true }
          );
        });

      // Starting the proven Off-grid flow must similarly discard any stale
      // Reserve preflight state before the older handler renders its dialog.
      this.shadowRoot
        .querySelectorAll('[data-action="unlock-for-preflight"], [data-action="open-preflight"]')
        .forEach((button) => {
          button.addEventListener(
            "click",
            () => clearReservePreflight(this),
            { capture: true }
          );
        });
    };

    const previousRender = proto.render;
    proto.render = function renderExclusiveSettingsModal() {
      // If an old browser state ever contains both flags, Reserve is the action
      // the user most recently opened in v0.7.0, so discard the stale Off-grid
      // layer. Also close Reserve immediately when the PIN unlock has expired.
      if (this._v070ReservePreflightOpen) {
        clearOffGridPreflight(this);
        if (!this._isUnlocked()) clearReservePreflight(this);
      }

      previousRender.call(this);

      if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v070-modal-state-style")) {
        return;
      }
      const style = document.createElement("style");
      style.id = "autarco-v070-modal-state-style";
      style.textContent = `
        .dialog.v070-reserve-dialog {
          width:min(760px,100%) !important;
          max-width:760px;
        }
        @media (max-width:650px) {
          .dialog.v070-reserve-dialog { width:100% !important; }
        }
      `;
      this.shadowRoot.appendChild(style);
    };

    proto._autarcoModalStateV070Version = VERSION;
  }
}
