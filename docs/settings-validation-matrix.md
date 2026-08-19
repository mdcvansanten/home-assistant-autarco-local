# Autarco Local settings validation matrix

This document is the hardware-validation gate for settings writes.  A generic
energy concept does **not** become writable merely because a register is known.
Each setting must have a proven read mapping, allowed range, dependencies,
read-back behaviour and (where relevant) restoration behaviour on the actual
Autarco S2.LH-MII hardware.

## Status language

- **Read confirmed** — value has been compared with the official/local inverter UI.
- **Read documented** — mapping is documented/consistent but has not yet been exercised with a changed value.
- **Write confirmed** — write + read-back + dependency handling + persistence are hardware tested.
- **Test candidate** — suitable for the next small reversible hardware test.
- **Pending** — keep read-only until prerequisite tests are complete.
- **Blocked** — mapping/scaling or safety context is not sufficient for a write test.

## Core settings

| Generic concept | Autarco setting | Read | Write | Next action |
|---|---|---:|---:|---|
| `battery.maximum_soc` | Overcharge SOC | confirmed | blocked | Installer/system read-only |
| `battery.minimum_soc` | Minimum battery SOC | confirmed | test candidate | Test later; changes the real grid-connected discharge floor |
| `battery.force_charge_soc` | Force-charge SOC | confirmed | pending | Test after grid-charge dependency is validated |
| `battery.reserve_soc` | Reserve SOC | confirmed | **test candidate** | Preferred next low-impact test while Reserve mode is Off |
| `battery.force_charge_power_limit` | Force-charge power limit | suspect | blocked | Resolve scaling/register mismatch first |
| `mode.self_use` | Self-use | confirmed | pending | Validate as complete work-mode transaction, not isolated bit |
| `mode.battery_reserve` | Reserve battery mode | confirmed | pending | Validate together with Reserve SOC behaviour |
| `grid.allow_battery_charging` | Laden vanuit net toestaan | confirmed | pending | Validate with Force-charge SOC and operational safeguards |
| `mode.feed_in_priority` | Feed-in priority | confirmed | pending | Validate as complete work-mode transaction |
| `mode.off_grid` | Off-grid mode | confirmed | blocked standalone | May only be changed temporarily inside a validated transaction |
| `battery.off_grid_minimum_soc` | Minimum-SOC off-grid | confirmed | **confirmed** | 10→11→10 and 10→11 persistent tests passed; Solis UI independently confirmed |

## Time schedules

Time-of-use is shown as a separate functional submenu.  The three physical
Autarco slots are adapter details; scenarios should later work with generic
charge/discharge windows.

| Generic concept | Autarco mapping | Read | Write | Next action |
|---|---|---:|---:|---|
| `schedule.enabled` | Time-of-use mode | confirmed | pending | Validate parent-mode behaviour first |
| `schedule.charge_current_limit` | Scheduled charge current | documented | pending | Exercise a small non-zero value with TOU controlled |
| `schedule.discharge_current_limit` | Scheduled discharge current | documented | pending | Exercise a small non-zero value with TOU controlled |
| `schedule.charge.N.start/end` | Charge slots 1–3 | documented | pending | Validate one complete window before enabling all slots |
| `schedule.discharge.N.start/end` | Discharge slots 1–3 | documented | pending | Validate one complete window before enabling all slots |

## Proposed hardware test order

1. **Reserve SOC** — current value → current+1 → current, only while Reserve mode is Off.  This is deliberately chosen because the value should be inactive in that state, making it a low-impact mapping/write test.
2. **Reserve battery mode** — after Reserve SOC itself is proven, validate the parent mode with complete work-mode snapshot/read-back and immediate restore.
3. **Minimum battery SOC** — one-point reversible test only when battery/grid conditions are suitable; this changes the normal discharge floor and therefore has more operational impact.
4. **Force-charge SOC + Allow grid charging** — validate as one dependency family, never as unrelated switches.
5. **Work modes** — Self-use / Feed-in priority using full register-state transactions and conflict detection.
6. **Time-of-use** — first parent mode, then current limits, then one charge/discharge window; only after those pass expose editing for all three schedule slots.

## Permanent read-only principle

Installer/system values such as grid code, meter/CT configuration, battery type,
factory/calibration and unproven communication parameters remain read-only unless
there is a strong product reason, authoritative mapping and a safe hardware test.
