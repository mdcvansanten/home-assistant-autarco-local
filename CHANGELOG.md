# Changelog

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
- Supersedes the accidentally published `v0.4.1` tag whose manifest still reported version `0.4.0`.
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
- No holding-register settings polling and no Modbus write functionality in this release.
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
