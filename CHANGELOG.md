# Changelog

## 0.4.0

- Start van fase 2: read-only uitlezen van inverterinstellingen via holding registers.
- Eerste set instellingen: batterijmodel, SOC-limieten, laad-/ontlaadstroomlimieten,
  force-charge SOC, backup SOC en opslagmodus.
- Opslagmodus decodeert de mode-bits en toont onafhankelijke modifiers als attributen.
- Instellingen worden bewust slechts iedere 5 minuten gelezen.
- Niet-ondersteunde instellingsregisters worden afzonderlijk overgeslagen.
- Een settings-read fout maakt de normale realtime monitoring niet onbeschikbaar.
- Settings-registers en leesstatus toegevoegd aan het diagnostische downloadbestand.
- Geen Modbus write-functionaliteit toegevoegd.
- Kleine correctie in de diagnostiek: dubbele `outage_started_at`-waarde verwijderd.

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
