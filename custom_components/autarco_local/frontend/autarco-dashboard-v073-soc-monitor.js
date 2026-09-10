// Autarco Local v0.7.3 — SOC jump/drop visualisation.
// Presentation only: reads the diagnostic SOC monitor entity created by the backend.

const PANEL_V073 = customElements.get("autarco-local-dashboard-panel");

if (PANEL_V073) {
  const proto = PANEL_V073.prototype;
  const previousHistoryChartV073 = proto._v072HistoryChart;
  const previousHistoryV073 = proto._v072History;
  const previousRenderV073 = proto.render;

  proto._v073SocMonitorEntity = function () {
    return this._entities().find((entity) => {
      const id = String(entity.entity_id || "").toLowerCase();
      const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
      return id.includes("soc_jump_drop_monitor") || name.includes("soc jump/drop monitor");
    }) || null;
  };

  proto._v073SocEvents = function () {
    const entity = this._v073SocMonitorEntity();
    const events = entity && entity.attributes ? entity.attributes.events : null;
    return Array.isArray(events) ? events.filter((event) => event && event.timestamp) : [];
  };

  proto._v073IsBatterySocHistory = function () {
    const entity = this._v072HistoryEntity ? this._v072HistoryEntity() : null;
    if (!entity) return false;
    const id = String(entity.entity_id || "").toLowerCase();
    const name = String((entity.attributes || {}).friendly_name || "").toLowerCase();
    return id.includes("battery_soc") || name.includes("battery soc") || name.includes("batterij-soc");
  };

  proto._v072HistoryChart = function historyChartV073() {
    const html = previousHistoryChartV073.call(this);
    if (!this._v073IsBatterySocHistory() || !html.includes("</svg>")) return html;

    const cache = this._v072HistoryCache;
    const numeric = cache && Array.isArray(cache.points)
      ? cache.points.filter((point) => Number.isFinite(point.value) && Number.isFinite(point.time))
      : [];
    if (numeric.length < 2) return html;

    const min = Math.min(...numeric.map((point) => point.value));
    const max = Math.max(...numeric.map((point) => point.value));
    const spread = Math.max(max - min, Math.max(Math.abs(max), 1) * 0.02);
    const t0 = numeric[0].time;
    const t1 = numeric[numeric.length - 1].time;
    const dt = Math.max(t1 - t0, 1);
    const events = this._v073SocEvents().filter((event) => {
      const timestamp = Date.parse(event.timestamp);
      return Number.isFinite(timestamp) && timestamp >= t0 && timestamp <= t1 && Number.isFinite(Number(event.to_soc));
    });
    if (!events.length) return html;

    const markers = events.map((event) => {
      const timestamp = Date.parse(event.timestamp);
      const value = Number(event.to_soc);
      const x = 36 + ((timestamp - t0) / dt) * 928;
      const y = 20 + (1 - (value - min) / spread) * 210;
      const type = event.classification === "jump" ? "jump" : "drop";
      const label = `${type === "jump" ? "SOC jump" : "SOC drop"}: ${event.from_soc}% → ${event.to_soc}% (${Number(event.delta_percent) > 0 ? "+" : ""}${event.delta_percent}%)`;
      return `<circle class="v073-soc-marker ${type}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9"><title>${this._escape(label)}</title></circle>`;
    }).join("");

    return html.replace("</svg>", `<g class="v073-soc-markers">${markers}</g></svg>`);
  };

  proto._v073SocEventPanel = function () {
    const monitor = this._v073SocMonitorEntity();
    const events = this._v073SocEvents().slice().reverse();
    const threshold = monitor && monitor.attributes ? monitor.attributes.threshold_percent : 5;
    const last = events[0] || null;
    const summary = last
      ? `${last.classification === "jump" ? "Laatste jump" : "Laatste drop"}: ${last.from_soc}% → ${last.to_soc}% (${Number(last.delta_percent) > 0 ? "+" : ""}${last.delta_percent}%)`
      : "Nog geen abrupte SOC jump/drop gedetecteerd sinds deze Home Assistant-start.";

    return `
      <div class="v073-soc-panel">
        <div class="v073-soc-head">
          <div><span class="v072-eyebrow">SOC-correcties</span><strong>Jump/drop monitoring</strong></div>
          <span class="v073-soc-threshold">≥ ${this._escape(String(threshold))}% per korte meetperiode</span>
        </div>
        <p>${this._escape(summary)}</p>
        <div class="v073-soc-legend"><span class="jump"></span>Jump <span class="drop"></span>Drop</div>
        ${events.length ? `<div class="v073-soc-events">${events.slice(0, 8).map((event) => {
          const when = new Date(event.timestamp);
          const type = event.classification === "jump" ? "jump" : "drop";
          const power = event.battery_power_w == null ? "—" : `${event.battery_power_w} W`;
          return `<div class="v073-soc-event ${type}"><span class="dot"></span><div><strong>${type === "jump" ? "SOC jump" : "SOC drop"} ${event.from_soc}% → ${event.to_soc}%</strong><small>${this._escape(when.toLocaleString())} · Δ ${event.delta_percent}% · ${this._escape(power)}</small></div></div>`;
        }).join("")}</div>` : ""}
        <small class="v073-soc-note">De rode/groene punten worden ook direct op de SOC-historiegrafiek gezet. Home Assistant ontvangt daarnaast het event <code>autarco_local_soc_anomaly</code>, zodat je er een pushmelding aan kunt koppelen.</small>
      </div>`;
  };

  proto._v072History = function historyV073() {
    const html = previousHistoryV073.call(this);
    if (!this._v073IsBatterySocHistory()) return html;
    return html.replace("</section>", `${this._v073SocEventPanel()}</section>`);
  };

  proto.render = function renderV073() {
    previousRenderV073.call(this);
    if (!this.shadowRoot || this.shadowRoot.querySelector("#autarco-v073-soc-styles")) return;
    const style = document.createElement("style");
    style.id = "autarco-v073-soc-styles";
    style.textContent = `
      .v073-soc-marker{stroke:var(--card-background-color);stroke-width:4;vector-effect:non-scaling-stroke}.v073-soc-marker.jump{fill:var(--success-color,#43a047)}.v073-soc-marker.drop{fill:var(--error-color,#db4437)}
      .v073-soc-panel{margin-top:12px;padding:14px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:14px}.v073-soc-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.v073-soc-head>div{display:flex;flex-direction:column;gap:3px}.v073-soc-threshold{font-size:12px;color:var(--secondary-text-color)}.v073-soc-panel p{margin:10px 0}.v073-soc-legend{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--secondary-text-color)}.v073-soc-legend span{width:10px;height:10px;border-radius:50%;margin-left:8px}.v073-soc-legend span.jump{background:var(--success-color,#43a047)}.v073-soc-legend span.drop{background:var(--error-color,#db4437)}.v073-soc-events{display:grid;gap:7px;margin-top:12px}.v073-soc-event{display:flex;align-items:flex-start;gap:9px;padding:8px 10px;border:1px solid var(--divider-color);border-radius:10px}.v073-soc-event .dot{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:0 0 auto}.v073-soc-event.jump .dot{background:var(--success-color,#43a047)}.v073-soc-event.drop .dot{background:var(--error-color,#db4437)}.v073-soc-event>div{display:flex;flex-direction:column;gap:2px}.v073-soc-event small,.v073-soc-note{color:var(--secondary-text-color)}.v073-soc-note{display:block;margin-top:10px;line-height:1.4}
      @media(max-width:700px){.v073-soc-head{flex-direction:column}}
    `;
    this.shadowRoot.appendChild(style);
  };
}
