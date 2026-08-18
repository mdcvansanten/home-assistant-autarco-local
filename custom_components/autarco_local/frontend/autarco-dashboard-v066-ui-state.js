// v0.6.6 UI-state preservation for live Home Assistant updates.
//
// Normal dashboard cards may refresh with Home Assistant telemetry. Interactive
// dialogs are different: while a PIN or Expert preflight dialog is open, a
// telemetry update must not rebuild the dialog DOM underneath the user. That
// caused fields, scroll position and the modal itself to jump every few seconds.
//
// Explicit user actions still call render() themselves, so validation,
// busy/error/success states continue to update normally.

const PANEL_UI_STATE_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_UI_STATE_V066) {
  const proto = PANEL_UI_STATE_V066.prototype;
  const previousRender = proto.render;
  const previousConnectedCallback = proto.connectedCallback;
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

  // Home Assistant assigns a new hass object for every state update. Keep the
  // latest object available to the backend/UI, but do not rebuild an open
  // interactive dialog just because telemetry changed in the background.
  if (hassDescriptor && hassDescriptor.set) {
    Object.defineProperty(proto, "hass", {
      configurable: true,
      enumerable: hassDescriptor.enumerable,
      get: hassDescriptor.get,
      set(value) {
        this._hass = value;
        if (!dialogOpen(this)) {
          this.render();
        }
      },
    });
  }

  // The base panel updates the 10-minute unlock countdown every five seconds by
  // re-rendering. Replace that timer with a modal-aware variant so an open
  // preflight/PIN dialog remains physically stationary while the countdown
  // continues in memory.
  proto.connectedCallback = function connectedWithStableDialogs() {
    if (previousConnectedCallback) {
      previousConnectedCallback.call(this);
    }

    if (this._timer) {
      window.clearInterval(this._timer);
    }

    this._timer = window.setInterval(() => {
      if (this._activeTab !== "settings" || this._unlockedUntil <= 0) return;

      const expired = Date.now() >= this._unlockedUntil;
      if (expired) {
        this._unlockedUntil = 0;
      }

      if (!dialogOpen(this)) {
        this.render();
      }
    }, 5000);
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

      // Preserve local scroll containers as a defensive fallback for explicit
      // renders (validation/busy/error/success). Ordinary telemetry renders are
      // suppressed entirely while a dialog is open.
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
  };
}
