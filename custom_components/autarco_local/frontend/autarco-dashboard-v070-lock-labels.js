// v0.7.0 visual lock-state consistency for write-capable settings.
// A locked write remains clickable so it can start the PIN flow, but the button
// explicitly shows that authentication is still required.

const PANEL_LOCK_LABELS_V070 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_LOCK_LABELS_V070) {
  const proto = PANEL_LOCK_LABELS_V070.prototype;
  const VERSION = "0.7.0.1";

  if (proto._autarcoLockLabelsV070Version !== VERSION) {
    const previousOffGridControls = proto._offGridControls;
    proto._offGridControls = function offGridControlsWithLockLabel(entity) {
      let html = previousOffGridControls.call(this, entity);
      if (!this._isUnlocked()) {
        html = html.replace(
          'data-action="unlock-for-preflight">Wijzigen</button>',
          'data-action="unlock-for-preflight">🔒 Wijzigen</button>'
        );
      }
      return html;
    };

    const previousSettingRow = proto._settingRow;
    proto._settingRow = function settingRowWithLockLabel(item, group) {
      let html = previousSettingRow.call(this, item, group);
      if (item && item[0] === "reserve_soc" && !this._isUnlocked()) {
        html = html.replace(
          /(<button[^>]*data-action="v070-open-reserve"[^>]*>)Wijzigen(<\/button>)/,
          "$1🔒 Wijzigen$2"
        );
      }
      return html;
    };

    proto._autarcoLockLabelsV070Version = VERSION;
  }
}
