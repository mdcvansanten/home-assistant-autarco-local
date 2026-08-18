// v0.6.6 UI-state preservation for live Home Assistant updates.
// The panel re-renders when HA states change. Without this guard native <details>
// elements are recreated and therefore jump back to their HTML default state.

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

  proto.render = function renderWithPersistentDetailsState() {
    const openState = new Map();

    if (this.shadowRoot) {
      this.shadowRoot.querySelectorAll("details").forEach((details) => {
        const key = detailsKey(details);
        if (key) openState.set(key, details.open);
      });
    }

    previousRender.call(this);

    if (!this.shadowRoot || openState.size === 0) return;

    this.shadowRoot.querySelectorAll("details").forEach((details) => {
      const key = detailsKey(details);
      if (key && openState.has(key)) {
        details.open = openState.get(key);
      }
    });
  };
}
