// v0.6.6 transaction UX hardening.
//
// A safety confirmation is valid for exactly one preflight session and one
// chosen target. Closing/reopening the dialog or changing the target invalidates
// that confirmation. A new dialog always starts at the inverter's current value.

const PANEL_TRANSACTION_UX_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_TRANSACTION_UX_V066) {
  const proto = PANEL_TRANSACTION_UX_V066.prototype;
  const UX_VERSION = "0.6.6.8";

  if (proto._autarcoTransactionUxVersion !== UX_VERSION) {
    function resetConfirmation(instance, newSession = false) {
      if (newSession) {
        instance._preflightSessionId = (instance._preflightSessionId || 0) + 1;
      }
      instance._preflightConfirmedSession = null;
      instance._confirmWriteChecked = false;
    }

    function forceUncheckedDom(instance) {
      if (!instance.shadowRoot) return;
      const checkbox = instance.shadowRoot.querySelector("#confirm-write");
      const button = instance.shadowRoot.querySelector(
        '[data-action="confirm-write"]'
      );
      if (checkbox) checkbox.checked = false;
      if (button) button.disabled = true;
    }

    const previousPreflight = proto._preflight;
    proto._preflight = function transactionSafePreflight() {
      let html = previousPreflight.call(this);
      if (!this._preflightOpen) return html;

      const current = this._number("off_grid_minimum_soc");
      const session = this._preflightSessionId || 0;
      const sessionConfirmed =
        this._preflightConfirmedSession === session &&
        Boolean(this._confirmWriteChecked);

      if (!this._offGridTargetTouched && current !== null) {
        this._offGridTarget = current;
        resetConfirmation(this, false);

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
      } else if (!sessionConfirmed) {
        // A DOM-state preservation layer may still remember a checkbox from an
        // older render. Component/session state wins: never carry confirmation
        // into another preflight session.
        html = html.replace(
          /<input id="confirm-write"([^>]*)>/,
          (match, attrs) => {
            const clean = attrs.replace(
              /\schecked(?:=(?:"[^"]*"|'[^']*'|[^\s>]+))?/g,
              ""
            );
            return `<input id="confirm-write"${clean}>`;
          }
        );
        html = html.replace(
          /(<button class="primary" data-action="confirm-write")(?![^>]*disabled)(>)/,
          "$1 disabled$2"
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
            resetConfirmation(this, true);
            // The base click listener renders synchronously after capture. Force
            // the newly-created checkbox clean once that render is complete.
            window.setTimeout(() => forceUncheckedDom(this), 0);
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
              resetConfirmation(this, true);
              forceUncheckedDom(this);
            },
            { capture: true }
          );
        });

      const targetInput = this.shadowRoot.querySelector("#off-grid-target");
      const checkbox = this.shadowRoot.querySelector("#confirm-write");

      if (targetInput) {
        const markTouched = () => {
          const previousTarget = this._offGridTarget;
          const nextTarget = Number(targetInput.value);
          this._offGridTargetTouched = true;
          this._offGridTarget = nextTarget;
          if (previousTarget !== nextTarget) {
            resetConfirmation(this, false);
            forceUncheckedDom(this);
          }
        };
        targetInput.addEventListener("input", markTouched, { capture: true });
        targetInput.addEventListener("change", markTouched, { capture: true });
      }

      if (checkbox) {
        checkbox.addEventListener(
          "change",
          () => {
            if (checkbox.checked) {
              this._confirmWriteChecked = true;
              this._preflightConfirmedSession = this._preflightSessionId || 0;
            } else {
              resetConfirmation(this, false);
            }
          },
          { capture: true }
        );
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
          resetConfirmation(this, true);
        }
      }
    };

    proto._autarcoTransactionUxVersion = UX_VERSION;
  }
}
