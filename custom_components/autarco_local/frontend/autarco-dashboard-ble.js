// Bluetooth beta: explicit source, freshness, phone handoff and settings status.
const BLE_PANEL = customElements.get("autarco-local-dashboard-panel");
if (BLE_PANEL) {
  const proto = BLE_PANEL.prototype;
  const oldFind = proto._findState;
  proto._findState = function (key) {
    // Stable backend keys avoid collisions with SOC settings or translated names.
    return this._entities().find(e => e.attributes?.autarco_key === key) || oldFind.call(this, key);
  };
  const health = panel => panel._entities().find(e => e.attributes?.autarco_key === "data_quality")?.attributes || {};
  const oldFormat = proto._formatState;
  proto._formatState = function (entity) {
    const quality = entity?.attributes?.data_quality;
    if (quality === "stale") return "Verouderd";
    if (quality === "paused") return "Gepauzeerd";
    if (["missing", "unavailable"].includes(quality)) return "Niet beschikbaar";
    return oldFormat.call(this, entity);
  };
  const oldNumber = proto._number;
  proto._number = function (key) {
    const quality = this._findState(key)?.attributes?.data_quality;
    if (["stale", "paused", "missing", "unavailable"].includes(quality)) return null;
    return oldNumber.call(this, key);
  };
  const oldService = proto._serviceAvailable;
  proto._serviceAvailable = function (name) {
    if (name === "set_off_grid_minimum_soc" && health(this).write_supported === false) return false;
    return oldService.call(this, name);
  };
  const oldOverview = proto._overview;
  const oldDiagnostics = proto._diagnostics;
  const oldSettings = proto._settings;
  proto._transportCard = function () {
    const h = health(this);
    const labels = {live: "Actueel", partial: "Gedeeltelijk", stale: "Verouderd", unavailable: "Niet beschikbaar", paused: "Gepauzeerd"};
    const age = Number.isFinite(h.runtime_age_seconds) ? `${Math.round(h.runtime_age_seconds)} s` : "—";
    const pause = this._entities().find(e => e.entity_id.startsWith("switch.") && e.attributes?.control === "ble_pause");
    const paused = pause?.state === "on";
    const active = h.active_transport || h.transport;
    const automatic = h.configured_transport === "ble_tcp";
    const connection = active === "ble" ? "Bluetooth LE" : automatic ? "Wifi-terugval" : "Lokale verbinding";
    const route = automatic
      ? (h.fallback_active ? (paused ? "Bluetooth vrijgegeven voor de Solis-app. Meetgegevens blijven via wifi binnenkomen." : "Bluetooth tijdelijk niet beschikbaar. Meetgegevens komen via wifi binnen; Bluetooth-herstel wordt automatisch getest.")
         : "Bluetooth is de hoofdverbinding. Bij uitval schakelt Autarco Local automatisch naar wifi.")
      : "Meetgegevens en instellingen hebben ieder een eigen status.";
    return `<div class="dashboard-block compact">
      <h3>${connection}</h3>
      <p><strong>${this._escape(labels[h.data_quality] || "Wachten op data")}</strong> · Meetleeftijd ${this._escape(age)}</p>
      <p class="muted">${route}</p>
      ${pause ? `<button class="secondary" data-action="ble-pause" data-entity-id="${this._escape(pause.entity_id)}">${paused ? "Bluetooth hervatten" : "Vrijgeven voor Solis-app"}</button>` : ""}
      <p class="muted">EMS-data: ${h.ems_data_ready ? "gereed voor monitoring" : "nog te valideren"}. Automatische invertersturing: nog niet actief.</p>
    </div>`;
  };
  proto._overview = function () { return this._transportCard() + oldOverview.call(this); };
  proto._diagnostics = function () { return this._transportCard() + oldDiagnostics.call(this); };
  proto._settings = function () {
    const h = health(this);
    const banner = h.write_supported === false ? `<div class="callout">Instellingen zijn in deze Bluetooth-beta alleen-lezen, ook tijdens wifi-terugval. Ze worden ongeveer iedere minuut ververst.</div>` : "";
    return banner + `<button class="secondary" data-action="ble-refresh-settings">Instellingen opnieuw lezen</button>` + oldSettings.call(this);
  };
  const oldBind = proto._bindEvents;
  proto._bindEvents = function () {
    oldBind.call(this);
    this.shadowRoot.querySelectorAll('[data-action="ble-pause"]').forEach(button => {
      button.onclick = async () => {
        const id = button.dataset.entityId;
        const paused = this._hass.states[id]?.state === "on";
        button.disabled = true;
        try {
          await this._hass.callService("switch", paused ? "turn_off" : "turn_on", {entity_id: id});
        } catch (err) { this._error = String(err.message || err); this.render(); }
        finally { button.disabled = false; }
      };
    });
    this.shadowRoot.querySelectorAll('[data-action="ble-refresh-settings"]').forEach(button => {
      button.onclick = async () => {
        button.disabled = true;
        try { await this._hass.callService("autarco_local", "refresh_settings", {}); }
        catch (err) { this._error = String(err.message || err); this.render(); }
        finally { button.disabled = false; }
      };
    });
  };
}
