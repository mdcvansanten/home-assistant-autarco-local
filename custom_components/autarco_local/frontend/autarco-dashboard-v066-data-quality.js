// v0.6.6 data-quality guard for battery values that are not yet hardware-validated.

const PANEL_DATA_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_DATA_V066) {
  const proto = PANEL_DATA_V066.prototype;

  proto._battery = function batteryWithValidationGuard() {
    const batteryEntities = this._entities().filter((entity) => {
      const haystack = (entity.entity_id + " " + this._friendlyName(entity)).toLowerCase();
      return haystack.indexOf("battery") !== -1 || haystack.indexOf("batterij") !== -1 || haystack.indexOf("soc") !== -1;
    });

    const suspect = [];
    const trustedForDashboard = [];
    for (const entity of batteryEntities) {
      const haystack = (entity.entity_id + " " + this._friendlyName(entity)).toLowerCase();
      if (haystack.indexOf("battery_voltage") !== -1 || haystack.indexOf("battery voltage") !== -1 ||
          haystack.indexOf("battery_current") !== -1 || haystack.indexOf("battery current") !== -1) {
        suspect.push(entity);
      } else {
        trustedForDashboard.push(entity);
      }
    }

    trustedForDashboard.sort((a, b) => this._friendlyName(a).localeCompare(this._friendlyName(b)));
    suspect.sort((a, b) => this._friendlyName(a).localeCompare(this._friendlyName(b)));

    const cards = trustedForDashboard.length
      ? `<div class="entity-grid">${trustedForDashboard.map((entity) => `
          <div class="entity-card"><span>${this._escape(this._friendlyName(entity))}</span><strong>${this._escape(this._formatState(entity))}</strong></div>`).join("")}</div>`
      : `<div class="empty">Geen gevalideerde batterij-entiteiten gevonden.</div>`;

    const raw = suspect.length
      ? `<details class="group dependencies">
          <summary>🧪 Onbevestigde batterijmetingen<span class="chevron">⌄</span></summary>
          <div class="callout bad">Battery voltage/current worden voorlopig niet als packwaarden vertrouwd. De huidige registers en schaalfactoren worden in issue #14 tegen de officiële Autarco/Solis-weergave gevalideerd. Deze waarden worden nergens gebruikt voor safety- of scenariologica.</div>
          <div class="entity-grid validation-grid">${suspect.map((entity) => `
            <div class="entity-card"><span>${this._escape(this._friendlyName(entity))}</span><strong>${this._escape(this._formatState(entity))}</strong><small>onbevestigde mapping</small></div>`).join("")}</div>
        </details>`
      : "";

    return `<section class="content-section"><h2>Batterij</h2><p class="muted">Batterijstatus, gevalideerde SOC-instellingen en batterijvermogen.</p>${cards}${raw}</section>`;
  };

  const previousRender = proto.render;
  proto.render = function renderDataQualityStyles() {
    previousRender.call(this);
    if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v066-data-styles")) return;
    const style = document.createElement("style");
    style.id = "autarco-v066-data-styles";
    style.textContent = `
      .validation-grid { padding:0 14px 14px; }
      .entity-card small { color:var(--secondary-text-color); }
    `;
    this.shadowRoot.appendChild(style);
  };
}
