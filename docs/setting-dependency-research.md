# Setting dependency research — Autarco Local

Status: living research document for the Autarco/Solis LH-MII family used by Autarco Local.

This document records **functional relationships** found in official Solis documentation. A documented relationship is **not** write permission. Registers, scaling, valid ranges and the exact write sequence still require validation on the supported Autarco hardware before a setting can become writable.

Primary official references:

- Solis Cloud Remote Control Settings — Desktop Version: https://solis-service.solisinverters.com/en/support/solutions/articles/44002638862-solis-cloud-remote-control-settings-desktop-version
- S6 Hybrid Series — SolisCloud App Local Bluetooth Connection Guide: https://solis-service.solisinverters.com/en/support/solutions/articles/44002504766-s6-hybrid-series-soliscloud-app-local-bluetooth-connection-guide

## Dependency types

- **W — write prerequisite:** parent state is needed to edit/write the child setting.
- **E — effect prerequisite:** the child may exist, but only has functional effect when its parent/context is active.
- **S — safety relationship:** values/states must be evaluated together.
- **X — mutual exclusion:** modes cannot be treated as independent simultaneous switches.
- **H — hardware/config prerequisite:** behaviour depends on wiring, battery chemistry/BMS, meter, neutral, generator, etc.
- **R — restore rule:** temporary state changed by Autarco Local must be restored to the original state; state already owned by the installation/user must not be changed back.

---

## 1. Work modes

### Self-use ↔ Feed-in Priority ↔ Peak-Shaving ↔ Off-grid

**X / R — documented.**

Solis states that Self-use cannot be active simultaneously with Feed-in Priority, Peak-Shaving or Off-grid. Activating another main mode can automatically disable Self-use.

**Autarco Local rule:** never treat these mode bits as independent toggles. Snapshot and verify the complete relevant work-mode state before and after a mode transaction.

---

## 2. Off-grid

### Off-grid mode → Off-grid minimum / Overdischarge SOC

**W / E / R — hardware observed + documented.**

- Solis documents Off-grid Overdischarge SOC as the minimum SOC during off-grid operation.
- Official documentation states Off-grid mode cannot be enabled below 30% battery SOC.
- On the current Autarco hardware, the local Installer UI only exposes the Off-grid minimum SOC field after Off-grid mode is enabled.
- The earlier direct Modbus write to `43137` while Off-grid was OFF returned no exception, but read-back remained unchanged.

**Current v0.6.4 pilot:** only `43137: 10% → 20%` is allowed. If Off-grid is already ON it stays ON. If Autarco Local must temporarily enable it, the original complete work-mode state is restored and verified.

### Off-grid mode enable → battery SOC ≥ 30%

**S — documented; hard pilot gate.**

Temporary activation is blocked by Autarco Local when battery SOC is unavailable or below 30%.

---

## 3. Time of Use

### Time-of-use switch → charge/discharge times

**E — documented.**

Solis states charge and discharge times are effective only when Time of Use is enabled.

Applies to current mapped Autarco Local settings:

- scheduled charge current;
- scheduled discharge current;
- charge slots 1–3;
- discharge slots 1–3.

**UI rule:** a user may prepare a schedule while TOU is OFF, but the UI must clearly state that it is inactive. Do not silently activate TOU merely because a child value was edited.

### RTC/time → scheduling

**E — documented.**

Solis describes inverter real-time clock as essential for scheduling/load-control operations.

**Future check:** time-slot validation should include inverter time/HA time drift before automatic schedule operation.

---

## 4. Battery Reserve

### Battery Reserve switch → Reserved SOC

**E — documented.**

Reserved SOC is effective only when Battery Reserve is ON.

### Battery Reserve switch → Grid Charging Power Limit

**E — documented.**

The reserve-related Grid Charging Power Limit is effective only when Battery Reserve is ON.

**Important:** this is a separate concept from the battery-level `Max Grid Power when Force Charge`/Peak Shaving setting.

### Reserve SOC ↔ Minimum battery SOC

**S — Autarco Local policy.**

Current backend invariant: `Reserve SOC >= Minimum battery SOC`.

---

## 5. Force charge and grid charging

### Force-charge SOC ↔ Allow Grid Charging

**E / S — documented context.**

Force-charge SOC defines the low-SOC trigger for active battery charging. The local Bluetooth guide recommends `Allow Charging from Grid` so the inverter can recharge from the grid at the force-charge threshold and avoid deep discharge.

**UI rule:** always show Force-charge SOC together with Minimum battery SOC and Allow Grid Charging status.

### Battery-level Peak Shaving switch → Max Grid Power when Force Charge

**E — documented.**

Solis explicitly describes the battery-level Peak Shaving Setting as the parent/context for dynamic limiting of grid power during force charge.

**Current Autarco Local status:** 🔒 locked. Candidate register `43027` is not trusted because the previous Home Assistant value and official Installer UI value differed by a factor of ten. Do not write until switch register, value register and scaling are proven.

---

## 6. Peak-Shaving work mode

### Peak-Shaving mode → communicating lithium battery

**H — documented.**

Solis states this work mode is supported only with lithium batteries that have communication functionality.

### Peak-Shaving mode → Max Usable Grid Power + Baseline SOC + Allow Grid Charging

**E / S — documented.**

These parameters jointly define peak-shaving behaviour. Baseline SOC is used together with measured grid power and the Max Usable Grid Power threshold; Allow Grid Charging controls whether the system can use grid energy to charge the battery.

**Future rule:** Peak-Shaving must be modelled as one policy bundle rather than independent sliders.

---

## 7. Grid feed-in limits

### Feed-in Power Limit Switch → Feed-in Power Limit Value

**E — documented.**

The value has functional meaning when the power-limit function is enabled.

### Feed-in Current Limit Switch → Feed-in Current Limit Value

**E — documented.**

Current-based export limiting is a separate mode from power-based limiting.

### Unbalance Output → neutral conductor connected

**H — documented.**

Solis states Unbalance Output cannot be activated unless the neutral conductor is properly connected.

### Export control → meter/CT correctness

**H / S — documented architecture + installer safety rule.**

Accurate meter type/location and CT direction are prerequisites for reliable grid-flow control. Autarco Local keeps these installer/system settings read-only until mappings are proven.

### FailSafe switch → communication/control failure

**E / S — documented.**

FailSafe is intended to force a safe default state when communication/control fails. Any future export-control implementation must define FailSafe behaviour together with the export-control policy, not as an unrelated switch.

---

## 8. Battery settings

### Overdischarge Hysteresis SOC ↔ Overdischarge SOC / off-grid backup behaviour

**S / E — documented.**

Solis describes hysteresis as preventing repeated backup-output toggling around the low-SOC threshold.

### Battery Healing switch → Battery Healing SOC

**E — documented.**

The target Healing SOC only has meaning with Battery Healing enabled.

### Battery Healing → Force-charge SOC

**E / S — documented.**

Solis states the healing process is triggered when the battery reaches Force-charge SOC; available PV is then used to charge toward Healing SOC while the grid powers the load.

### ECO → Overdischarge / Force-charge behaviour

**E / S — documented.**

ECO uses low-SOC thresholds to reduce battery self-discharge at night. The local guide further describes reconnect/recharge behaviour around Force-charge and Overdischarge SOC. These values should therefore be shown together if ECO is ever mapped.

### Battery wake-up → voltage + time

**E / H — documented.**

Manual and automatic battery wake-up use configured voltage/time conditions and directly interact with the battery/BMS. Treat as Installer/service functionality until hardware support is proven.

---

## 9. Smart Port / Backup / AC coupling

### Backup Port enable → Backup Voltage / overload-droop settings

**E / H — documented.**

Backup Voltage and overload/droop behaviour belong to the enabled backup output and depend on physical backup wiring/load design.

### AC Coupling Control → no grid + no generator

**H / E — documented.**

Solis states AC Coupling Control is active only when both grid and generator are disconnected.

### AC Coupling threshold type → battery chemistry

**H — documented.**

Solis describes SOC threshold control for lithium batteries and voltage threshold control for lead-acid batteries.

**Policy:** these remain red/installer until the physical topology and exact Autarco support are established.

---

## 10. Generator settings

### Generator position → physical connection point

**H — documented.**

Generator Position must match whether the generator is connected to GEN or Grid port. Solis warns incorrect Grid-port power-source configuration can damage the generator.

### GEN Start SOC / Stop SOC → no-grid condition

**E — documented.**

Automatic generator start/stop by SOC is described for periods without grid power.

### GEN Signal → automatic start/stop capability

**H / E — documented.**

When generator auto-control is unsupported, start/stop must remain manual.

### GEN Force / Stop → automatic SOC logic

**Override — documented.**

Manual force/stop can override normal automatic conditions. Any future UI must show this explicitly as an override, not a normal persistent target.

---

## 11. Advanced settings

### MPPT Multi-peak Scan switch → Scan Interval

**E — documented.**

The interval controls scan frequency when multi-peak scanning is enabled. Solis warns overly frequent scanning can reduce yield during scan events.

### Power Factor → Power Down Storage

**E — documented.**

Solis exposes whether the chosen power-factor setting is retained after shutdown. Persistence is therefore part of the setting transaction semantics.

### Inverter output limits → grid/site requirements

**H / regulatory — documented.**

Active/reactive power limits and grid-code-related power/frequency functions depend on site/grid requirements and remain Installer/system territory.

### Only PV Power Load → source eligibility

**E / mode behaviour — documented.**

When enabled, only PV is permitted to supply the load; battery and grid input are excluded. This is not a normal end-user toggle for the current project.

### Factory reset / calibration / special functions

**🔒 Service domain.**

These can reset or materially alter system behaviour/measurements and must remain hard read-only in Autarco Local.

---

## Implementation priority for Autarco Local

1. **Now:** Off-grid minimum SOC dependency-aware pilot `10 → 20` with full preflight and state preservation.
2. **Next hardware validation candidates:**
   - Time of Use ↔ schedule/current;
   - Battery Reserve ↔ Reserve SOC;
   - Allow Grid Charging ↔ Force-charge behaviour.
3. **Keep locked until mapping is proven:** force-charge power limit/Peak-Shaving child settings.
4. **Installer/system read-only:** meter/CT, grid code, export protection, Smart Port, generator, calibration and factory/service settings.

The decision-tree UX should display these relationships even when the underlying setting remains read-only. Understanding a dependency never grants permission to write it.
