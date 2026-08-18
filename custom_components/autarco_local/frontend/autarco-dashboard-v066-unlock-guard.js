// v0.6.6 PIN unlock guard.
//
// The unlock dialog must never trap the user in a permanent "Controleren…"
// state when a Home Assistant service call is slow or does not return. This
// final layer keeps cancel available, limits one unlock attempt to a bounded
// wait, and ignores/locks any late result after cancel or timeout.

const PANEL_UNLOCK_GUARD_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_UNLOCK_GUARD_V066) {
  const proto = PANEL_UNLOCK_GUARD_V066.prototype;
  const UNLOCK_GUARD_VERSION = "0.6.6.7";
  const UNLOCK_TIMEOUT_MS = 12000;

  if (proto._autarcoUnlockGuardVersion !== UNLOCK_GUARD_VERSION) {
    proto._unlock = async function guardedUnlock() {
      if (this._unlockBusy) return;

      const input = this.shadowRoot && this.shadowRoot.querySelector("#unlock-pin");
      const pin = input ? String(input.value || "").trim() : "";
      if (!pin) {
        this._unlockError = "Vul de PIN in.";
        this.render();
        return;
      }

      const token = (this._unlockAttemptToken || 0) + 1;
      this._unlockAttemptToken = token;
      this._unlockBusy = true;
      this._unlockError = "";
      this.render();

      let timeoutHandle = null;
      let timedOut = false;
      const callPromise = this._hass.callService("autarco_local", "unlock_settings", { pin });

      // If a cancelled/timed-out call eventually succeeds, immediately revoke
      // that late backend unlock so UI and backend security state stay aligned.
      callPromise
        .then(() => {
          if (timedOut || this._unlockAttemptToken !== token) {
            return this._hass
              .callService("autarco_local", "lock_settings", {})
              .catch(() => undefined);
          }
          return undefined;
        })
        .catch(() => undefined);

      const timeoutPromise = new Promise((_, reject) => {
        timeoutHandle = window.setTimeout(() => {
          timedOut = true;
          reject(new Error("unlock_timeout"));
        }, UNLOCK_TIMEOUT_MS);
      });

      try {
        await Promise.race([callPromise, timeoutPromise]);
        if (this._unlockAttemptToken !== token) return;
        this._unlockedUntil = Date.now() + 10 * 60 * 1000;
        this._unlockOpen = false;
        this._unlockError = "";
      } catch (error) {
        if (this._unlockAttemptToken !== token) return;
        if (timedOut || (error && error.message === "unlock_timeout")) {
          this._unlockError =
            "Ontgrendelen kreeg binnen 12 seconden geen antwoord. Probeer opnieuw; de knop is weer vrijgegeven.";
        } else {
          this._unlockError =
            error && error.message ? error.message : String(error);
        }
      } finally {
        if (timeoutHandle !== null) window.clearTimeout(timeoutHandle);
        if (this._unlockAttemptToken === token) {
          this._unlockBusy = false;
          this.render();
          if (this._unlockOpen) {
            window.setTimeout(() => {
              const pinField =
                this.shadowRoot && this.shadowRoot.querySelector("#unlock-pin");
              if (pinField) pinField.focus({ preventScroll: true });
            }, 0);
          }
        }
      }
    };

    const previousUnlockDialog = proto._unlockDialog;
    proto._unlockDialog = function unlockDialogWithEscapeRoute() {
      const html = previousUnlockDialog.call(this);
      // Cancel must remain available while a request is pending.
      return html.replace(
        /(<button class="secondary" data-action="cancel-unlock") disabled(>)/g,
        "$1$2"
      );
    };

    const previousBindEvents = proto._bindEvents;
    proto._bindEvents = function bindGuardedUnlockEvents() {
      if (previousBindEvents) previousBindEvents.call(this);

      const cancel = this.shadowRoot.querySelector('[data-action="cancel-unlock"]');
      if (cancel) {
        cancel.addEventListener(
          "click",
          (event) => {
            event.preventDefault();
            event.stopImmediatePropagation();
            this._unlockAttemptToken = (this._unlockAttemptToken || 0) + 1;
            this._unlockBusy = false;
            this._unlockError = "";
            this._unlockOpen = false;
            this.render();
            // Best-effort cleanup in case the backend already accepted the PIN.
            this._hass
              .callService("autarco_local", "lock_settings", {})
              .catch(() => undefined);
          },
          { capture: true }
        );
      }
    };

    proto._autarcoUnlockGuardVersion = UNLOCK_GUARD_VERSION;
  }
}
