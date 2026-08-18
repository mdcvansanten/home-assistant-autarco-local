// v0.6.6 UI-state preservation for live Home Assistant updates.
// The panel re-renders whenever HA states change. Preserve user-controlled UI
// state so live telemetry cannot collapse menus or clear in-progress form input.

const PANEL_UI_STATE_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_UI_STATE_V066) {
  const proto = PANEL_UI_STATE_V066.prototype;
  const previousRender = proto.render;

  function detailsKey(details) {
    const explicit = details.getAttribute("data-state-key");
    if (explicit) return explicit;
    const summary = details.querySelector(":scope > summary");
    return summary ? summary.textContent.trim().replace(/\s+/g, " ") : null;
  }

  function inputKey(input) {
    return input.id || input.name || null;
  }

  proto.render = function renderWithPersistentUiState() {
    const openState = new Map();
    const inputState = new Map();
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
