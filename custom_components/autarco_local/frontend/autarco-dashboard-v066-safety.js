// v0.6.6 final hardware safety gate.
//
// Register-derived battery SOC is currently not trusted as a safety prerequisite
// because hardware testing showed a plausible 99% even while the Dyness towers
// were not connected to the Connectbox. Until a reliable source is validated,
// Autarco Local must not temporarily enable Off-grid based on that value.

const PANEL_SAFETY_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_SAFETY_V066) {
  const proto = PANEL_SAFETY_V066.prototype;
  const SAFETY_VERSION = "0.6.6.9";

  if (proto._autarcoSafetyVersion !== SAFETY_VERSION) {
    const previousPreflight = proto._preflight;
    proto._preflight = function safetyGatedPreflight() {
      let html = previousPreflight.call(this);
      if (!this._preflightOpen) return html;

      const offGridOn = this._isOn("off_grid_mode");

      html = html.replace(
        "<span>Live batterij-SOC</span>",
        "<span>Live batterij-SOC (onbevestigd)</span>"
      );

      if (!offGridOn) {
        this._confirmWriteChecked = false;

        html = html.replace(
          /<div class="callout (?:ok|bad)">(?:Batterij-SOC|Geblokkeerd: de actuele batterij-SOC)[\s\S]*?<\/div>/,
          '<div class="callout bad">Geblokkeerd: de huidige batterij-SOC bron is nog niet betrouwbaar genoeg voor tijdelijke Off-grid-activatie. De getoonde waarde kan plausibel lijken terwijl de batterijverbinding ontbreekt.</div>'
        );

        html = html.replace(
          "Off-grid tijdelijk activeren en die activatie via read-back bevestigen.",
          "Tijdelijke Off-grid-activatie NIET uitvoeren zolang geen betrouwbare batterij-SOC bron is gevalideerd."
        );

        html = html.replace(
          /<input id="confirm-write"([^>]*)>/,
          (match, attrs) => {
            const clean = attrs
              .replace(/\schecked(?:=(?:"[^"]*"|'[^']*'|[^\s>]+))?/g, "")
              .replace(/\sdisabled(?:=(?:"[^"]*"|'[^']*'|[^\s>]+))?/g, "");
            return `<input id="confirm-write"${clean} disabled>`;
          }
        );

        html = html.replace(
          /(<button class="primary" data-action="confirm-write")(?: disabled)?(>)/,
          "$1 disabled$2"
        );
      }

      return html;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function safetyGatedBindEvents() {
      if (previousBindEvents) previousBindEvents.call(this);

      if (!this._preflightOpen || this._isOn("off_grid_mode")) return;

      const checkbox = this.shadowRoot.querySelector("#confirm-write");
      const confirmButton = this.shadowRoot.querySelector(
        '[data-action="confirm-write"]'
      );
      const targetInput = this.shadowRoot.querySelector("#off-grid-target");

      const enforceBlocked = () => {
        this._confirmWriteChecked = false;
        if (checkbox) {
          checkbox.checked = false;
          checkbox.disabled = true;
        }
        if (confirmButton) confirmButton.disabled = true;
      };

      if (targetInput) {
        targetInput.addEventListener("input", enforceBlocked);
        targetInput.addEventListener("change", enforceBlocked);
      }
      if (checkbox) checkbox.addEventListener("change", enforceBlocked);
      enforceBlocked();
    };

    proto._autarcoSafetyVersion = SAFETY_VERSION;
  }
}
