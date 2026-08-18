// v0.6.6 UI-state preservation for live Home Assistant updates.
//
// Normal dashboard cards may refresh with Home Assistant telemetry. Interactive
// dialogs are different: while a PIN or Expert preflight dialog is open, a
// telemetry update must not rebuild the dialog DOM underneath the user.
//
// Important: Home Assistant may instantiate the custom element immediately when
// the bootstrap calls customElements.define(), before this final patch module has
// been evaluated. Therefore an old base 5-second timer may already be running.
// This patch replaces that timer lazily from the hass setter as well, making the
// fix effective for already-connected panel instances.

const PANEL_UI_STATE_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_UI_STATE_V066) {
  const proto = PANEL_UI_STATE_V066.prototype;
  const previousRender = proto.render;
  const hassDescriptor = Object.getOwnPropertyDescriptor(proto, "hass");

  function dialogOpen(instance) {
    return Boolean(instance && (instance._unlockOpen || instance._preflightOpen));
  }

  function detailsKey(details) {
    const explicit = details.getAttribute("data-state-key");
    if (explicit) return explicit;
    const summary = details.querySelector(":scope > summary");
    return summary ? summary.textContent.trim().replace(/\s+/g, " ") : null;
  }

  function inputKey(input) {
    return input.id || input.name || null;
  }

  function installStableTimer(instance) {
    if (!instance || instance._autarcoStableTimerInstalled) return;

    // A base timer may already exist because the element can be connected before
    // this patch module is evaluated. Always replace it once.
    if (instance._timer) {
      window.clearInterval(instance._timer);
      instance._timer = null;
    }

    instance._timer = window.setInterval(() => {
      if (instance._activeTab !== "settings" || instance._unlockedUntil <= 0) return;

      if (Date.now() >= instance._unlockedUntil) {
        instance._unlockedUntil = 0;
        // An expired unlock invalidates the preflight. Closing it is deliberate,
        // not a telemetry refresh.
        instance._preflightOpen = false;
        instance._unlockOpen = false;
        instance.render();
        return;
      }

      // Refresh the visible countdown only when no interactive dialog is open.
      if (!dialogOpen(instance)) {
        instance.render();
      }
    }, 5000);

    instance._autarcoStableTimerInstalled = true;
  }

  // Home Assistant assigns a new hass object for every state update. Keep the
  // latest object available for a fresh backend pre-read, but never rebuild an
  // open interactive dialog because of telemetry.
  if (hassDescriptor && hassDescriptor.set) {
    Object.defineProperty(proto, "hass", {
      configurable: true,
      enumerable: hassDescriptor.enumerable,
      get: hassDescriptor.get,
      set(value) {
        this._hass = value;
        installStableTimer(this);
        if (!dialogOpen(this)) {
          this.render();
        }
      },
    });
  }

  // Also cover panel instances connected only after this patch is loaded.
  const previousConnectedCallback = proto.connectedCallback;
  proto.connectedCallback = function connectedWithStableDialogs() {
    if (previousConnectedCallback) {
      previousConnectedCallback.call(this);
    }
    // previousConnectedCallback may have created the base timer; replace it.
    this._autarcoStableTimerInstalled = false;
    installStableTimer(this);
  };

  proto.render = function renderWithPersistentUiState() {
    const openState = new Map();
    const inputState = new Map();
    const scrollState = new Map();
    let focusState = null;

    if (this.shadowRoot) {
      this.shadowRoot.querySelectorAll("details").forEach((details) => {
        const key = detailsKey(details);
        if (key) openState.set(key, details.open);
      });

      this.shadowRoot.querySelectorAll("input").forEach((input) => {
        const key = inputKey(input);
        if (!key) return;
        inputState.set(key, {
          value: input.value,
          checked: input.checked,
          type: input.type,
        });
      });

      [
        ["backdrop", this.shadowRoot.querySelector(".backdrop")],
        ["dialog", this.shadowRoot.querySelector(".dialog")],
      ].forEach(([key, element]) => {
        if (element) {
          scrollState.set(key, {
            top: element.scrollTop,
            left: element.scrollLeft,
          });
        }
      });

      const active = this.shadowRoot.activeElement;
      if (active && active.tagName === "INPUT") {
        const key = inputKey(active);
        if (key) {
          focusState = {
            key,
            start: typeof active.selectionStart === "number" ? active.selectionStart : null,
            end: typeof active.selectionEnd === "number" ? active.selectionEnd : null,
          };
        }
      }
    }

    previousRender.call(this);

    if (!this.shadowRoot) return;

    if (openState.size) {
      this.shadowRoot.querySelectorAll("details").forEach((details) => {
        const key = detailsKey(details);
        if (key && openState.has(key)) {
          details.open = openState.get(key);
        }
      });
    }

    if (inputState.size) {
      this.shadowRoot.querySelectorAll("input").forEach((input) => {
        const key = inputKey(input);
        if (!key || !inputState.has(key)) return;
        const state = inputState.get(key);
        if (state.type === "checkbox" || state.type === "radio") {
          input.checked = state.checked;
        } else {
          input.value = state.value;
        }
      });
    }

    if (scrollState.has("backdrop")) {
      const backdrop = this.shadowRoot.querySelector(".backdrop");
      const state = scrollState.get("backdrop");
      if (backdrop) {
        backdrop.scrollTop = state.top;
        backdrop.scrollLeft = state.left;
      }
    }
    if (scrollState.has("dialog")) {
      const dialog = this.shadowRoot.querySelector(".dialog");
      const state = scrollState.get("dialog");
      if (dialog) {
        dialog.scrollTop = state.top;
        dialog.scrollLeft = state.left;
      }
    }

    if (focusState) {
      const active = this.shadowRoot.getElementById(focusState.key);
      if (active) {
        active.focus({ preventScroll: true });
        if (
          focusState.start !== null &&
          focusState.end !== null &&
          typeof active.setSelectionRange === "function"
        ) {
          try {
            active.setSelectionRange(focusState.start, focusState.end);
          } catch (_error) {
            // Number inputs do not support selection ranges; focus is enough.
          }
        }
      }
    }

    // Defensive consistency check for explicit renders while the Expert dialog
    // is open. Restoring a checked checkbox must also restore the enabled state
    // of the confirmation button.
    const targetInput = this.shadowRoot.querySelector("#off-grid-target");
    const confirmCheckbox = this.shadowRoot.querySelector("#confirm-write");
    const confirmButton = this.shadowRoot.querySelector('[data-action="confirm-write"]');
    if (targetInput && confirmCheckbox && confirmButton) {
      const value = Number(targetInput.value);
      const current = this._number("off_grid_minimum_soc");
      const valid = Number.isInteger(value) && value >= 10 && value <= 100 && value !== current;
      confirmCheckbox.disabled = !valid || this._writeBusy;
      confirmButton.disabled = !valid || !confirmCheckbox.checked || this._writeBusy;
    }
  };
}
