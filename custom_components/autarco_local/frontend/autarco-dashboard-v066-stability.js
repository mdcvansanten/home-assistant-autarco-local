// v0.6.6 interaction stability layer.
//
// This module is deliberately loaded last. Earlier v0.6.6 builds patched the
// same custom element incrementally, so a browser session could retain an older
// five-second timer or stack the scenario Settings wrapper more than once after
// cache-busted frontend reloads. Keep the final interactive state explicit and
// make this layer idempotent.

const PANEL_STABILITY_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_STABILITY_V066) {
  const proto = PANEL_STABILITY_V066.prototype;
  const STABILITY_VERSION = "0.6.6.5";

  function dialogOpen(instance) {
    return Boolean(instance && (instance._unlockOpen || instance._preflightOpen));
  }

  function installQuietUnlockTimer(instance) {
    if (!instance) return;
    if (
      instance._autarcoQuietTimerVersion === STABILITY_VERSION &&
      instance._timer
    ) {
      return;
    }

    // A timer from an earlier hot-loaded patch may still be alive. Replace it
    // unconditionally when the stability version changes.
    if (instance._timer) {
      window.clearInterval(instance._timer);
      instance._timer = null;
    }

    instance._timer = window.setInterval(() => {
      if (instance._activeTab !== "settings" || instance._unlockedUntil <= 0) {
        return;
      }

      if (Date.now() >= instance._unlockedUntil) {
        instance._unlockedUntil = 0;
        instance._preflightOpen = false;
        instance._unlockOpen = false;
        instance._confirmWriteChecked = false;
        instance.render();
        return;
      }

      // Never rebuild Settings every five seconds just to update a clock. The
      // countdown is the only DOM node that changes between user actions.
      if (instance.shadowRoot) {
        const countdown = instance.shadowRoot.querySelector(
          '[data-role="unlock-countdown"]'
        );
        if (countdown) countdown.textContent = instance._remainingUnlock();
      }
    }, 1000);

    instance._autarcoQuietTimerVersion = STABILITY_VERSION;
  }

  // Wrap the final hass setter. The previous setter keeps background telemetry
  // current and already suppresses full renders while a dialog is open. After
  // it runs, enforce our no-render countdown timer for this exact build.
  const previousHassDescriptor = Object.getOwnPropertyDescriptor(proto, "hass");
  if (
    previousHassDescriptor &&
    previousHassDescriptor.set &&
    proto._autarcoStabilityHassVersion !== STABILITY_VERSION
  ) {
    const previousGet = previousHassDescriptor.get;
    const previousSet = previousHassDescriptor.set;
    Object.defineProperty(proto, "hass", {
      configurable: true,
      enumerable: previousHassDescriptor.enumerable,
      get: previousGet,
      set(value) {
        previousSet.call(this, value);
        installQuietUnlockTimer(this);
      },
    });
    proto._autarcoStabilityHassVersion = STABILITY_VERSION;
  }

  // Cover instances connected after this module is evaluated. The previous
  // callback may create a legacy timer; replace it immediately afterwards.
  if (!proto._autarcoConnectedBeforeStability) {
    proto._autarcoConnectedBeforeStability = proto.connectedCallback;
  }
  const connectedBase = proto._autarcoConnectedBeforeStability;
  proto.connectedCallback = function stableConnectedCallback() {
    if (connectedBase) connectedBase.call(this);
    installQuietUnlockTimer(this);
  };

  // Render the countdown with a stable target so the timer can update only this
  // text instead of rebuilding the complete Settings DOM.
  if (!proto._autarcoLockBarBeforeStability) {
    proto._autarcoLockBarBeforeStability = proto._lockBar;
  }
  const lockBarBase = proto._autarcoLockBarBeforeStability;
  proto._lockBar = function stableLockBar() {
    let html = lockBarBase.call(this);
    if (!this._isUnlocked()) return html;
    const remaining = this._remainingUnlock();
    return html.replace(
      `Nog ${remaining} beschikbaar.`,
      `Nog <span data-role="unlock-countdown">${remaining}</span> beschikbaar.`
    );
  };

  // Give Scenario's its own component state. This survives ordinary telemetry
  // renders without relying on DOM reconstruction heuristics.
  if (!proto._autarcoScenarioSectionBeforeStability) {
    proto._autarcoScenarioSectionBeforeStability = proto._scenarioSection;
  }
  const scenarioBase = proto._autarcoScenarioSectionBeforeStability;
  proto._scenarioSection = function stableScenarioSection() {
    if (typeof this._scenarioOpen !== "boolean") this._scenarioOpen = true;
    let html = scenarioBase.call(this);
    html = html.replace(
      /<details class="group dependencies"(?: open)?>/,
      `<details class="group dependencies" data-state-key="scenarios"${
        this._scenarioOpen ? " open" : ""
      }>`
    );
    return html;
  };

  // The v0.6.6 patch can be evaluated more than once in a long-lived HA browser
  // session through cache-busted module URLs. Older wrappers then each append a
  // Scenario's block. Let the existing Settings implementation render, remove
  // every marked Scenario's block, and append exactly one canonical block.
  if (!proto._autarcoSettingsBeforeScenarioDedup) {
    proto._autarcoSettingsBeforeScenarioDedup = proto._settings;
  }
  const settingsBase = proto._autarcoSettingsBeforeScenarioDedup;
  proto._settings = function stableSettingsWithOneScenarioSection() {
    let html = settingsBase.call(this);
    html = html.replace(
      /\s*<details class="group dependencies"[^>]*data-state-key="scenarios"[^>]*>[\s\S]*?<\/details>/g,
      ""
    );
    return html.replace("</section>", `${this._scenarioSection()}</section>`);
  };

  // Keep confirmation as real component state. A DOM checkbox is presentation;
  // its value must never be the only source of truth for a safety confirmation.
  if (!proto._autarcoPreflightBeforeStability) {
    proto._autarcoPreflightBeforeStability = proto._preflight;
  }
  const preflightBase = proto._autarcoPreflightBeforeStability;
  proto._preflight = function stablePreflight() {
    let html = preflightBase.call(this);
    if (!this._preflightOpen) return html;
    if (typeof this._confirmWriteChecked !== "boolean") {
      this._confirmWriteChecked = false;
    }

    const checkboxDisabled = /<input id="confirm-write"[^>]*disabled/.test(html);
    if (this._confirmWriteChecked && !checkboxDisabled) {
      html = html.replace(
        /(<input id="confirm-write"[^>]*)(>)/,
        (match, start, end) =>
          /\schecked(?:\s|=|>)/.test(match) ? match : `${start} checked${end}`
      );
      if (!this._writeBusy) {
        html = html.replace(
          /(<button class="primary" data-action="confirm-write") disabled(>)/,
          "$1$2"
        );
      }
    }
    return html;
  };

  if (!proto._autarcoPerformWriteBeforeStability) {
    proto._autarcoPerformWriteBeforeStability = proto._performWrite;
  }
  const performWriteBase = proto._autarcoPerformWriteBeforeStability;
  proto._performWrite = async function stablePerformWrite() {
    try {
      return await performWriteBase.call(this);
    } finally {
      if (!this._preflightOpen) this._confirmWriteChecked = false;
    }
  };

  // Add final event behavior once per render. Existing handlers still perform
  // the normal actions; this layer only owns persistent UI state and autofocus.
  if (!proto._autarcoBindBeforeStability) {
    proto._autarcoBindBeforeStability = proto._bindEvents;
  }
  const bindBase = proto._autarcoBindBeforeStability;
  proto._bindEvents = function stableBindEvents() {
    if (bindBase) bindBase.call(this);

    installQuietUnlockTimer(this);

    const scenarioDetails = this.shadowRoot.querySelector(
      'details[data-state-key="scenarios"]'
    );
    if (scenarioDetails) {
      scenarioDetails.addEventListener("toggle", () => {
        this._scenarioOpen = scenarioDetails.open;
      });
    }

    const openUnlock = this.shadowRoot.querySelector(
      '[data-action="open-unlock"]'
    );
    if (openUnlock) {
      openUnlock.addEventListener(
        "click",
        () => {
          window.setTimeout(() => {
            const pin = this.shadowRoot && this.shadowRoot.querySelector("#unlock-pin");
            if (pin) pin.focus({ preventScroll: true });
          }, 0);
        },
        { capture: true }
      );
    }

    const openPreflight = this.shadowRoot.querySelector(
      '[data-action="open-preflight"]'
    );
    if (openPreflight) {
      // Capture runs before the existing bubble listener that renders the modal.
      openPreflight.addEventListener(
        "click",
        () => {
          this._confirmWriteChecked = false;
        },
        { capture: true }
      );
    }

    const checkbox = this.shadowRoot.querySelector("#confirm-write");
    const confirmButton = this.shadowRoot.querySelector(
      '[data-action="confirm-write"]'
    );
    const targetInput = this.shadowRoot.querySelector("#off-grid-target");

    const syncConfirmation = () => {
      if (!checkbox || !confirmButton || !targetInput) return;
      const value = Number(targetInput.value);
      const current = this._number("off_grid_minimum_soc");
      const valid =
        Number.isInteger(value) &&
        value >= 10 &&
        value <= 100 &&
        value !== current &&
        this._isUnlocked() &&
        !this._writeBusy;

      if (!valid) {
        this._confirmWriteChecked = false;
        checkbox.checked = false;
      } else {
        this._confirmWriteChecked = Boolean(checkbox.checked);
      }
      checkbox.disabled = !valid;
      confirmButton.disabled = !valid || !this._confirmWriteChecked;
    };

    if (checkbox) checkbox.addEventListener("change", syncConfirmation);
    if (targetInput) {
      targetInput.addEventListener("input", () => {
        this._offGridTarget = Number(targetInput.value);
        syncConfirmation();
      });
      targetInput.addEventListener("change", syncConfirmation);
    }

    this.shadowRoot
      .querySelectorAll('[data-action="cancel-preflight"]')
      .forEach((button) =>
        button.addEventListener("click", () => {
          this._confirmWriteChecked = false;
        })
      );

    // Reconcile the DOM with component state after any explicit render.
    if (checkbox && this._confirmWriteChecked && !checkbox.disabled) {
      checkbox.checked = true;
    }
    syncConfirmation();
  };

  // Make the PIN field request focus even when the dialog is opened by keyboard.
  if (!proto._autarcoUnlockDialogBeforeStability) {
    proto._autarcoUnlockDialogBeforeStability = proto._unlockDialog;
  }
  const unlockDialogBase = proto._autarcoUnlockDialogBeforeStability;
  proto._unlockDialog = function stableUnlockDialog() {
    return unlockDialogBase
      .call(this)
      .replace('id="unlock-pin" class="pin"', 'id="unlock-pin" class="pin" autofocus');
  };
}
