// v0.6.6 relationship-help state persistence.
//
// The relationship status help originally lived only in DOM state. Home Assistant
// state updates re-render the custom panel, which recreated the help block as
// hidden. Persist the selected relation key in component state and restore the
// help block after every render. Clicking the same ? again deliberately closes it.

const PANEL_RELATION_STATE_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_RELATION_STATE_V066) {
  const proto = PANEL_RELATION_STATE_V066.prototype;
  const RELATION_STATE_VERSION = "0.6.6.15";

  if (proto._autarcoRelationStateVersion !== RELATION_STATE_VERSION) {
    const restoreRelationHelp = (instance) => {
      if (!instance.shadowRoot) return;
      const key = instance._relationHelpOpenKey || "";
      const help = instance.shadowRoot.querySelector("#settings-relation-help");
      if (!help) return;

      if (!key) {
        help.hidden = true;
        help.dataset.relationKey = "";
        help.textContent = "";
        return;
      }

      const button = instance.shadowRoot.querySelector(
        `[data-action="show-relation-help"][data-relation-key="${key}"]`
      );
      if (!button) {
        instance._relationHelpOpenKey = null;
        help.hidden = true;
        help.dataset.relationKey = "";
        help.textContent = "";
        return;
      }

      const levels = ["ok", "warn", "danger", "info", "unknown"];
      const level = levels.find((name) => button.classList.contains(name)) || "unknown";
      const text = button.getAttribute("title") || "Geen uitleg beschikbaar.";

      help.dataset.relationKey = key;
      help.className = `settings-relation-help ${level}`;
      help.textContent = text;
      help.hidden = false;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindPersistentRelationHelp() {
      if (previousBindEvents) previousBindEvents.call(this);

      this.shadowRoot
        .querySelectorAll('[data-action="show-relation-help"]')
        .forEach((button) => {
          button.addEventListener("click", () => {
            const key = button.getAttribute("data-relation-key") || "";
            const help = this.shadowRoot.querySelector("#settings-relation-help");
            // The original relation-status handler has already toggled the DOM.
            // Mirror that resulting state into component state.
            if (help && !help.hidden && help.dataset.relationKey === key) {
              this._relationHelpOpenKey = key;
            } else if (this._relationHelpOpenKey === key) {
              this._relationHelpOpenKey = null;
            }
          });
        });
    };

    const previousRender = proto.render;
    proto.render = function renderWithPersistentRelationHelp() {
      previousRender.call(this);
      restoreRelationHelp(this);
    };

    proto._autarcoRelationStateVersion = RELATION_STATE_VERSION;
  }
}
