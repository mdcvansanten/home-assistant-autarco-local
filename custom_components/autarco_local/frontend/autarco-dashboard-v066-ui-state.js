// v0.6.6 UI-state preservation for live Home Assistant updates.
//
// Normal dashboard cards may refresh with Home Assistant telemetry. Interactive
// dialogs are different: while a PIN or Expert preflight dialog is open, a
// telemetry update must not rebuild the dialog DOM underneath the user.
//
// Home Assistant can keep an already-instantiated custom panel alive across
// frontend module/cache refreshes. Therefore timer ownership is versioned: a
// newer frontend patch ALWAYS replaces a timer installed by an older patch.

const PANEL_UI_STATE_V066 = customElements.get("autarco-local-dashboard-panel");
const STABLE_TIMER_VERSION = "0.6.6.5";

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
    if (!instance) return;

    // Never trust a boolean marker from an older hot-loaded frontend patch.
    // Only the exact current version is allowed to keep its timer.
    if (instance._autarcoStableTimerVersion === STABLE_TIMER_VERSION && instance._timer) {
      return;
    }

    if (instance._timer) {
      window.clearInterval(instance._timer);
      instance._timer = null;
    }

    instance._timer = window.setInterval(() => {
      if (instance._activeTab !== "settings" || instance._unlockedUntil <= 0) return;

      if (Date.now() >= instance._unlockedUntil) {
        instance._unlockedUntil = 0;
        // Expiry is a deliberate security transition. Close interactive dialogs
        // and render the locked state once.
        instance._preflightOpen = false;
        instance._unlockOpen = false;
        instance._preflightConfirmed = false;
        instance.render();
        return;
      }

      // The countdown may refresh only when no interactive dialog is open.
      if (!dialogOpen(instance)) {
        instance.render();
      }
    }, 5000);

    instance._autarcoStableTimerVersion = STABLE_TIMER_VERSION;
    // Clean up the old boolean marker used by earlier v0.6.6 patches.
    instance._autarcoStableTimerInstalled = undefined;
  }

  function syncPreflightControls(instance) {
    if (!instance || !instance.shadowRoot) return;
    const targetInput = instance.shadowRoot.querySelector("#off-grid-target");
    const confirmCheckbox = instance.shadowRoot.querySelector("#confirm-write");
    const confirmButton = instance.shadowRoot.querySelector('[data-action="confirm-write"]');
    if (!targetInput || !confirmCheckbox || !confirmButton) return;

    const value = Number(targetInput.value);
    const current = instance._number("off_grid_minimum_soc");
    const valid = Number.isInteger(value) && value >= 10 && value <= 100 && value !== current;

    // Keep confirmation as component state as well as DOM state. This removes
    // the final dependency on whether a browser/HA render recreated the checkbox.
    if (instance._preflightConfirmed == null) {
      instance._preflightConfirmed = Boolean(confirmCheckbox.checked);
    }
    confirmCheckbox.checked = Boolean(instance._preflightConfirmed);
    confirmCheckbox.disabled = !valid || instance._writeBusy;
    confirmButton.disabled =
      !valid ||
      !instance._preflightConfirmed ||
      instance._writeBusy ||
      !instance._isUnlocked();
  }

  function bindPersistentPreflightState(instance) {
    if (!instance || !instance.shadowRoot) return;
    const targetInput = instance.shadowRoot.querySelector("#off-grid-target");
    const confirmCheckbox = instance.shadowRoot.querySelector("#confirm-write");
    if (targetInput && !targetInput.dataset.autarcoPersistentBound) {
      targetInput.dataset.autarcoPersistentBound = "1";
      const updateTarget = () => {
        instance._offGridTarget = Number(targetInput.value);
        syncPreflightControls(instance);
      };
      targetInput.addEventListener("input", updateTarget);
      targetInput.addEventListener("change", updateTarget);
    }
    if (confirmCheckbox && !confirmCheckbox.dataset.autarcoPersistentBound) {
      confirmCheckbox.dataset.autarcoPersistentBound = "1";
      confirmCheckbox.addEventListener("change", () => {
        instance._preflightConfirmed = Boolean(confirmCheckbox.checked);
        syncPreflightControls(instance);
      });
    }
    syncPreflightControls(instance);
  }

  function focusUnlockPin(instance) {
    if (!instance || !instance._unlockOpen || !instance.shadowRoot) return;
    const pin = instance.shadowRoot.querySelector("#unlock-pin");
    if (!pin) return;
    // Do not steal focus while the user is already interacting with another
    // field, but focus immediately on first opening the unlock dialog.
    const active = instance.shadowRoot.activeElement;
    if (!active || active === instance.shadowRoot) {
      window.requestAnimationFrame(() => {
        const current = instance.shadowRoot && instance.shadowRoot.querySelector("#unlock-pin");
        if (current) current.focus({ preventScroll: true });
      });
    }
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

      const existingCheckbox = this.shadowRoot.querySelector("#confirm-write");
      if (existingCheckbox) {
        this._preflightConfirmed = Boolean(existingCheckbox.checked);
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
    } else {
      focusUnlockPin(this);
    }

    bindPersistentPreflightState(this);
  };
}
