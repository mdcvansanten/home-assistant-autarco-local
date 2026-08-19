// v0.6.6 trusted battery-SOC safety gate.
//
// The inverter-derived battery SOC is deliberately not trusted for temporary
// Off-grid activation. A user-selected Home Assistant sensor is used instead,
// which keeps this safety mechanism vendor-neutral (Dyness today, another
// battery integration later).

const PANEL_SAFETY_V066 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_SAFETY_V066) {
  const proto = PANEL_SAFETY_V066.prototype;
  const SAFETY_VERSION = "0.6.6.11";
  const MIN_TEMPORARY_OFF_GRID_SOC = 30;

  function configuredSource(instance) {
    return (
      instance &&
      instance._panel &&
      instance._panel.config &&
      instance._panel.config.battery_soc_entity
    ) || "";
  }

  function sourceInfo(instance) {
    const entityId = configuredSource(instance);
    if (!entityId) {
      return {
        entityId: "",
        entity: null,
        valid: false,
        value: null,
        name: "Niet ingesteld",
        reason: "Geen betrouwbare batterij-SOC bron ingesteld via Autarco Local → Configureren."
      };
    }

    const entity = instance._hass && instance._hass.states
      ? instance._hass.states[entityId]
      : null;
    if (!entity) {
      return {
        entityId,
        entity: null,
        valid: false,
        value: null,
        name: entityId,
        reason: `De ingestelde batterij-SOC bron ${entityId} bestaat niet in Home Assistant.`
      };
    }

    const state = String(entity.state || "").trim();
    const unavailable = ["unknown", "unavailable", "none", ""].includes(
      state.toLowerCase()
    );
    const unit = entity.attributes && entity.attributes.unit_of_measurement;
    const value = Number.parseFloat(state.replace(",", "."));
    const name =
      (entity.attributes && entity.attributes.friendly_name) || entityId;

    if (unavailable) {
      return {
        entityId,
        entity,
        valid: false,
        value: null,
        name,
        reason: `${name} is momenteel niet beschikbaar.`
      };
    }
    if (unit !== "%") {
      return {
        entityId,
        entity,
        valid: false,
        value: null,
        name,
        reason: `${name} gebruikt ${unit || "geen eenheid"}; voor de veiligheids-SOC is % vereist.`
      };
    }
    if (!Number.isFinite(value) || value < 0 || value > 100) {
      return {
        entityId,
        entity,
        valid: false,
        value: null,
        name,
        reason: `${name} bevat geen geldig SOC-percentage tussen 0 en 100.`
      };
    }

    return { entityId, entity, valid: true, value, name, reason: "" };
  }

  if (proto._autarcoSafetyVersion !== SAFETY_VERSION) {
    const previousPreflight = proto._preflight;
    proto._preflight = function safetyGatedPreflight() {
      let html = previousPreflight.call(this);
      if (!this._preflightOpen) return html;

      const offGridOn = this._isOn("off_grid_mode");
      const info = sourceInfo(this);

      // Replace the known-untrusted inverter SOC card with the explicitly chosen
      // Home Assistant safety source. Keep the source name visible so it is
      // obvious which integration supplies the decision value.
      const displayValue = info.valid ? `${info.value}%` : "Niet beschikbaar";
      const displayName = info.valid
        ? `Veiligheids-SOC · ${info.name}`
        : "Veiligheids-SOC";
      html = html.replace(
        /<div><span>Live batterij-SOC(?: \(onbevestigd\))?<\/span><strong>[\s\S]*?<\/strong><\/div>/,
        `<div><span>${this._escape(displayName)}</span><strong>${this._escape(displayValue)}</strong></div>`
      );

      let safe = offGridOn;
      let safetyText;

      if (offGridOn) {
        safetyText = info.valid
          ? `Off-grid staat al AAN; tijdelijke activatie is niet nodig. Geselecteerde batterij-SOC bron ${info.name} geeft ${info.value}%.`
          : "Off-grid staat al AAN; tijdelijke activatie is niet nodig en een batterij-SOC safetybron is daarom geen write-prerequisite.";
      } else if (!info.valid) {
        safe = false;
        safetyText = `Geblokkeerd: ${info.reason}`;
      } else if (info.value < MIN_TEMPORARY_OFF_GRID_SOC) {
        safe = false;
        safetyText = `Geblokkeerd: betrouwbare batterij-SOC via ${info.name} is ${info.value}%. Voor tijdelijke Off-grid-activatie is minimaal ${MIN_TEMPORARY_OFF_GRID_SOC}% vereist.`;
      } else {
        safe = true;
        safetyText = `Betrouwbare batterij-SOC via ${info.name} is ${info.value}%. De ${MIN_TEMPORARY_OFF_GRID_SOC}%-veiligheidsgrens voor tijdelijke Off-grid-activatie is gehaald.`;
      }

      html = html.replace(
        /<div class="callout (?:ok|bad)">(?:Batterij-SOC|Geblokkeerd: de actuele batterij-SOC)[\s\S]*?<\/div>/,
        `<div class="callout ${safe ? "ok" : "bad"}">${this._escape(safetyText)}</div>`
      );

      if (!safe) {
        this._confirmWriteChecked = false;
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
      if (!this._preflightOpen) return;

      const offGridOn = this._isOn("off_grid_mode");
      const info = sourceInfo(this);
      const safe =
        offGridOn ||
        (info.valid && info.value >= MIN_TEMPORARY_OFF_GRID_SOC);
      if (safe) return;

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
