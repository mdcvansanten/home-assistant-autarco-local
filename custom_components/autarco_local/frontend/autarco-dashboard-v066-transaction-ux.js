// v0.6.6 transaction UX hardening.
//
// A safety confirmation is valid for one preflight session only. Closing the
// dialog must discard the checkbox and provisional target. A newly opened
// dialog starts at the inverter's current value; the user must deliberately
// choose a different valid target before confirmation becomes possible.

const PANEL_TRANSACTION_UX_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_TRANSACTION_UX_V066) {
  const proto = PANEL_TRANSACTION_UX_V066.prototype;
  const UX_VERSION = "0.6.6.6";

  if (proto._autarcoTransactionUxVersion !== UX_VERSION) {
    const previousPreflight = proto._preflight;
    proto._preflight = function transactionSafePreflight() {
      let html = previousPreflight.call(this);
      if (!this._preflightOpen) return html;

      const current = this._number("off_grid_minimum_soc");
      if (!this._offGridTargetTouched && current !== null) {
        this._offGridTarget = current;
        this._confirmWriteChecked = false;

        html = html.replace(
          /(<input id="off-grid-target"[^>]*\bvalue=")[^"]*(")/,
          `$1${current}$2`
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

        html = html.replace(
          "Voor de eerste hardwaretest: 20% → 21%. Na controle zetten we hem desgewenst via dezelfde route terug naar 20%.",
          "De doelwaarde start bewust op de actuele waarde. Kies zelf een andere geldige waarde om deze wijziging te kunnen bevestigen."
        );
      }

      return html;
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function transactionSafeBindEvents() {
      if (previousBindEvents) previousBindEvents.call(this);

      const openPreflight = this.shadowRoot.querySelector(
        '[data-action="open-preflight"]'
      );
      if (openPreflight) {
        openPreflight.addEventListener(
          "click",
          () => {
            this._offGridTargetTouched = false;
            this._offGridTarget = null;
            this._confirmWriteChecked = false;
          },
          { capture: true }
        );
      }

      this.shadowRoot
        .querySelectorAll('[data-action="cancel-preflight"]')
        .forEach((button) => {
          button.addEventListener(
            "click",
            () => {
              this._offGridTargetTouched = false;
              this._offGridTarget = null;
              this._confirmWriteChecked = false;
            },
            { capture: true }
          );
        });

      const targetInput = this.shadowRoot.querySelector("#off-grid-target");
      if (targetInput) {
        const markTouched = () => {
          this._offGridTargetTouched = true;
          this._offGridTarget = Number(targetInput.value);
        };
        targetInput.addEventListener("input", markTouched, { capture: true });
        targetInput.addEventListener("change", markTouched, { capture: true });
      }
    };

    if (!proto._autarcoPerformWriteBeforeTransactionUx) {
      proto._autarcoPerformWriteBeforeTransactionUx = proto._performWrite;
    }
    const performWriteBase = proto._autarcoPerformWriteBeforeTransactionUx;
    proto._performWrite = async function transactionSafePerformWrite() {
      try {
        return await performWriteBase.call(this);
      } finally {
        if (!this._preflightOpen) {
          this._offGridTargetTouched = false;
          this._offGridTarget = null;
          this._confirmWriteChecked = false;
        }
      }
    };

    proto._autarcoTransactionUxVersion = UX_VERSION;
  }
}
