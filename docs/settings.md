# Autarco Local — inverter settings

## v0.5.0: read-only first

Autarco Local v0.5.0 introduces a separate Modbus holding-register layer for inverter settings.

**No Modbus write functions are implemented in v0.5.0.** All setting entities are sensors and expose `write_policy: read_only`.

The colour in the entity name describes the intended future access level, not current write access:

- 🟢 Standard — candidate for normal end-user write access after validation.
- 🟡 Expert — candidate for Expert Mode with warning, validation and confirmation.
- 🔴 Installer — intended to remain read-only in Autarco Local.

## Isolation from runtime monitoring

The existing 33xxx input-register monitoring remains the primary coordinator update. Holding-register settings are read afterwards as a best-effort, non-critical layer.

A failed or unsupported settings read must not:

- increment the normal failed-poll counter;
- trip the three-failure connection threshold;
- make PV, battery or grid sensors unavailable;
- cause a DataUpdateCoordinator update failure.

The `Settings read status` diagnostic sensor reports `available`, `partial` or `unavailable` and exposes unsupported register blocks and the last settings error.

## Initial register map

| Setting | Register(s) | Access | Decode |
| --- | ---: | --- | --- |
| Overcharge SOC | 43010 | 🔴 Installer | % |
| Minimum battery / overdischarge SOC | 43011 | 🟡 Expert | % |
| Force-charge SOC | 43018 | 🟡 Expert | % |
| Reserve / backup SOC | 43024 | 🟢 Standard | % |
| Force-charge power limit | 43027 | 🟡 Expert | W; validate on hardware |
| Self-use mode | 43110 bit 0 | 🟢 Standard | On/Off |
| Time-of-use mode | 43110 bit 1 | 🟢 Standard | On/Off |
| Off-grid mode | 43110 bit 2 | 🟡 Expert | On/Off |
| Reserve battery mode | 43110 bit 4 | 🟢 Standard | On/Off |
| Allow grid charging | 43110 bit 5 | 🟡 Expert | On/Off |
| Feed-in priority mode | 43110 bit 6 | 🟢 Standard | On/Off |
| Off-grid minimum SOC | 43137 | 🟡 Expert | % |
| Scheduled charge current | 43141 | 🟡 Expert | raw × 0.1 A |
| Scheduled discharge current | 43142 | 🟡 Expert | raw × 0.1 A |
| Charge slot 1 start/end | 43143-43146 | 🟢 Standard | hour/minute pairs |
| Discharge slot 1 start/end | 43147-43150 | 🟢 Standard | hour/minute pairs |
| Charge slot 2 start/end | 43153-43156 | 🟢 Standard | hour/minute pairs |
| Discharge slot 2 start/end | 43157-43160 | 🟢 Standard | hour/minute pairs |
| Charge slot 3 start/end | 43163-43166 | 🟢 Standard | hour/minute pairs |
| Discharge slot 3 start/end | 43167-43170 | 🟢 Standard | hour/minute pairs |

The time schedule is intentionally limited to three slots in this first Autarco mapping, matching the current Autarco workflow being validated.

## Intentionally not mapped yet

### Battery Select / battery type

Battery Select chooses the battery/BMS compatibility profile used by the inverter. A wrong value can break or invalidate battery communication. The exact holding register for the supported Autarco/Solis generation has not yet been validated, so v0.5.0 deliberately does not expose a guessed register.

Other grid-code, protection, meter/CT, factory and calibration settings remain outside this first read-only set until their mappings are verified.

## Hardware validation checklist

After installing the v0.5.0 test build:

1. Confirm all existing PV, battery, grid and connection entities still update normally.
2. Open the diagnostic entity `Settings read status`.
3. Record its state and `unsupported_blocks` attribute.
4. Compare Reserve SOC with the value shown in the Autarco Installer App / inverter menu.
5. Compare Off-grid mode and Off-grid minimum SOC.
6. Compare scheduled charge and discharge current; verify 0.1 A scaling.
7. Compare all three charge/discharge time slots.
8. Check whether Force-charge SOC and Force-charge power limit match the inverter UI.
9. If any time entity displays `raw:<hour>/<minute>`, record the raw values instead of assuming the mapping is correct.
10. Do not enable write functionality until these values have been validated on real hardware.

Each setting entity includes these diagnostic attributes:

- `access_level`
- `write_policy`
- `register_type`
- `registers`
- `raw_values`
