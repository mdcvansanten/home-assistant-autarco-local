# Changelog

## 0.6.5

- Replaced the separate v0.6.4 Settings Center page with one Autarco Local dashboard shell containing `Overzicht`, `PV`, `Batterij`, `Diagnose` and `Instellingen` tabs.
- Moved the dependency-aware Settings UI into the `Instellingen` tab while retaining the existing green/yellow/red access classification.
- Restored the native Home Assistant `Configureren` / Options flow as a functional settings fallback instead of keeping it read-only.
- Added a backend-protected settings PIN: 4–8 digits, stored only as a salted PBKDF2-SHA256 hash in config-entry options.
- Added per-Home-Assistant-user temporary settings unlocks with a ten-minute lifetime and an explicit re-lock action.
- The Off-grid minimum SOC write service now refuses writes when the caller does not have a valid backend unlock.
- Restored the native `10% -> 20%` Off-grid minimum SOC pilot in `Configureren`; that fallback requires the configured PIN explicitly before a write.
- Both UI routes use the same shared dependency-aware write controller and the same temporary Off-grid safety gate.
- Kept the actual inverter write limited to register `43137`, transition `10% -> 20%`, with fresh pre-read, target read-back, complete work-mode restore where needed and conflict detection.
- Removed the obsolete v0.6.4 `autarco-settings-panel.js` frontend after the black-screen hardware test.
- Added frontend JavaScript syntax validation (`node --check`) to CI so custom-panel syntax is checked alongside Python, JSON, Hassfest and HACS validation.
- No additional inverter setting registers were opened for writing.

## 0.6.4

- Added a guided Expert preflight in the custom Settings Center for the single hardware-validated Off-grid minimum SOC pilot (`10% -> 20%`).
- The preflight shows current Self-use, Off-grid, Minimum SOC, Force-charge SOC, grid-charging status and battery SOC before confirmation.
- Added a Home Assistant service `autarco_local.set_off_grid_minimum_soc` with explicit confirmation and the same narrow `10% -> 20%` guard.
- The service performs a fresh settings read before the write and uses the dependency-aware v0.6.3 transaction engine.
- If Off-grid is already active, the service leaves it active. If it is inactive, temporary activation is permitted only when battery SOC is available and at least 30% for this pilot.
- The complete original work-mode state is restored only when Autarco Local temporarily changed it; read-back and conflict detection remain mandatory.
- The Settings Center now shows documented dependency guidance for mapped Standard and Expert settings.
- Added a dependency overview for work modes, Time of Use, Battery Reserve, Force-charge, Peak-Shaving and meter/CT prerequisites.
- Added `docs/setting-dependency-research.md` with additional official Solis dependency research covering export limits, Battery Healing, ECO, Smart Port, AC coupling, generator and advanced settings.
- Force-charge power limit remains locked because the current register/scaling mapping is not yet proven.
- No additional setting register has been made writable.

## 0.6.3

- Added dependency-aware setting metadata for parent-mode requirements.
- Hardware-validated Off-grid minimum SOC as dependent on Off-grid mode being active.
- Reworked the guarded Off-grid minimum SOC write pilot to preserve the user's original work-mode state.
- If Off-grid is already active before the write, Autarco Local leaves it active afterwards.
- If Autarco Local temporarily activates Off-grid, it restores and verifies the complete original storage/work-mode register after the SOC write.
- Cleanup/restoration is attempted even when the target write fails; an unverified restore is reported as a hard failure.
- Added conflict detection so an unexpected external mode change during the transaction is not blindly overwritten.
- Recorded documented-but-not-yet-hardware-validated dependencies for Time of Use schedules/currents and Battery Reserve SOC.
- Added `docs/write-dependencies.md` with the generic state-preservation and dependency policy.
- No additional setting registers have been opened for writing.

## 0.6.2

- Added a dedicated Autarco Local Settings Center panel with a mobile-friendly layout.
- Setting names are larger; current values are aligned to the right and descriptions are larger below the setting row.
- Kept the existing green/yellow/red access-level dots at the existing visual size.
- Standard, Expert, Installer/system and Safety sections stay on one page and are collapsible.
- Added an explicit write-access warning after the failed register 43137 hardware pilot.
- Added official third-party EMS/write-access research and a support checklist for Autarco/Solis.
- No additional registers are writable in this release.

## 0.6.1

- Kept the single guarded Off-grid minimum SOC write pilot limited to register `43137`, `10% -> 20%`.
- Added detailed write diagnostics to distinguish Modbus rejection from an accepted write whose read-back remains unchanged.
- Hardware test result: pre-read `10`, requested `20`, no Modbus exception, repeated read-back remained `10`.
- No writes were added for any other setting.

## 0.6.0

- Added the first deliberately narrow physical write pilot for Off-grid minimum SOC.
- Only holding register `43137` and only transition `10% -> 20%` are allowed by the pilot.
- Requires a fresh pre-read and immediate read-back verification.
- All other setting writes remain blocked.

## 0.5.2

- Replaced the four-page Settings Center menu with one mobile-friendly form using native Home Assistant collapsible sections.
- 🟢 Standard settings and 🛡️ Safety rules open by default; 🟡 Expert and 🔴 Installer/system settings are collapsed by default.
- Added Force-charge SOC to the Safety Rules overview so Reserve SOC, Minimum battery SOC and Force-charge SOC can be compared in one place.
- Kept the existing backend invariant **Reserve SOC >= Minimum battery SOC** unchanged.
- The Force-charge/minimum relationship is displayed for review only and is not yet enforced as a write rule.
- Physical Modbus writes remain locked (`PHYSICAL_WRITES_ENABLED = False`).
- No register mapping, runtime polling or inverter write behaviour changed in this release.

## 0.5.1

- Added a dedicated Home Assistant **Settings Center** through the integration Configure/Options flow.
- Settings are grouped into 🟢 standard, 🟡 expert and 🔴 installer/system sections.
- Known installer/system settings remain visible even when their register mapping is not yet validated; they are shown as intentionally unmapped/read-only instead of guessing addresses.
- Added concise per-setting explanations and an official Autarco LH-MII documentation link in the standard and expert sections.
- Added planned write-policy metadata (`allowed`, `confirm`, `read_only`) for the later controlled-write phase.
- Added a backend safety invariant: **Reserve SOC must never be lower than Minimum battery SOC**.
- Added a Safety Rules page showing the current Reserve SOC, Minimum battery SOC, relationship status and physical-write status.
- Physical Modbus writes remain locked in v0.5.1 (`PHYSICAL_WRITES_ENABLED = False`) pending installer review and write-register validation.
- Added Dutch Settings Center translations.

## 0.5.0

- Added a separate read-only Modbus holding-register layer for inverter settings.
- Settings reads are deliberately non-critical: unsupported or failed setting reads do not make the existing PV, battery or connection monitoring unavailable.
- Added read-only Home Assistant configuration sensors for battery SOC limits, storage-mode flags, grid charging, off-grid mode, off-grid minimum SOC, scheduled charge/discharge current and three charge/discharge time slots.
- Added future access-level metadata and visual classification: 🟢 standard user, 🟡 expert user and 🔴 installer/read-only.
- Every setting entity exposes its holding-register address, raw value, access level and `read_only` write policy as attributes.
- Added a settings-read diagnostic sensor reporting available/partial/unavailable state, read duration, unsupported blocks and last error.
- Battery Select is intentionally not exposed yet because its exact register mapping has not been validated for the supported Autarco/Solis generation.
- Fixed duplicate `outage_started_at` output in connection diagnostics.
- No Modbus write functions are implemented in this release.

## 0.4.2

- Corrected English runtime translations for the new v0.4 PV entities so Home Assistant shows descriptive entity names instead of generic `Power`, `Current`, `Voltage` and `Energy` labels.
- Corrected the integration manifest version to `0.4.2` so HACS can identify the release properly.
- Supersedes the accidentally published `v0.4.1` tag whose manifest still reported version `0.4.0`; use v0.4.2 instead.
- No Modbus register, polling, retry or write-behaviour changes.

## 0.4.1

- Packaging-only patch attempt for the v0.4 PV entity translation fix.
- The published tag still contained manifest version `0.4.0`; use v0.4.2 instead.

## 0.4.0

- Repurposed v0.4.0 as a dedicated PV / solar monitoring release.
- Added calculated power per PV input/MPPT for PV1 and PV2.
- Added PV3/PV4 voltage, current and calculated power as disabled-by-default entities.
- Added PV energy today, current month, current year and lifetime total.
- Added a binary sensor showing whether PV production is currently active.
- Added optional PV alarm-code and DC-bus-voltage diagnostics.
- Existing inverter, battery and connection monitoring retained.
- No holding-register settings polling and no Modbus write functionality changed in this release.
- Read-only inverter-settings work moved to the next roadmap phase.

## 0.3.5

- Persistent connection history across Home Assistant and integration restarts.
- Persist total downtime, last disconnect/reconnect, last disconnect reason, longest connection, disconnect count and the last 50 connection events.
- Connection availability now spans the persisted observation period.
- Added a dedicated disconnect count.
- Reduced default diagnostic clutter for new installs; detailed poll/network counters remain available but are disabled by default.
- No changes to register mapping, polling interval, retry policy or the three-failure availability threshold.
- Documentation and historical version references corrected.

## 0.3.4

- Added connection uptime, downtime, availability and connection-transition diagnostics.
- Added connection established/lost/restored logging.
- Added last disconnect, last reconnect, longest connection and connection health diagnostics.
- Initial TCP connection is not counted as a reconnect.
- Separate diagnostics for complete poll duration, register read duration and TCP connect duration.
- Existing persistent connection, retries and three-failure availability threshold retained.

## 0.3.3

- Battery current and battery power polarity corrected: positive means charging, negative means discharging.
- No register mapping changes.

## 0.3.2

- Persistent Modbus TCP connection instead of reconnecting for every poll.
- Full socket rebuild after any communication error.
- Exponential retry delay to give the logger time to recover.
- Short interruptions keep the last valid values available.
- Connection becomes unavailable only after three consecutive failed polls.
- New diagnostics for reconnects, consecutive failures and suppressed failures.
- Clean Modbus client shutdown during reload and unload.

## 0.3.1

- Improved reconnect and retry logging.
- Logging reports the first failure and later recovery.
- Added retry and last-success diagnostics.
- Roadmap, register map and tested-hardware documentation added.

## 0.3.0

- First named sensors and network-health diagnostics.
