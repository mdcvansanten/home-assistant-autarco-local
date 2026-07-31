# Changelog

## 0.3.4

- Battery current and battery power polarity corrected: positive means charging, negative means discharging.
- Diagnostic counters start clean after installing/restarting this version.
- Initial TCP connection is no longer counted as a reconnect.
- Separate diagnostics for complete poll duration, register read duration and TCP connect duration.
- Added average, minimum and maximum poll duration since integration startup.
- Added the last reconnect reason to downloaded diagnostics.
- Existing persistent connection, retries and three-failure availability threshold retained.


## 0.3.2

- Persistent Modbus TCP connection instead of reconnecting for every poll.
- Full socket rebuild after any communication error.
- Exponential retry delay to give the logger time to recover.
- Short interruptions keep the last valid values available.
- Connection becomes unavailable only after three consecutive failed polls.
- New diagnostics for reconnects, consecutive failures and suppressed failures.
- Clean Modbus client shutdown during reload and unload.
- No changes to the existing register mapping or battery polarity.

## 0.3.1

- Batterijstroom: positief is laden, negatief is ontladen.
- Batterijvermogen: positief is laden, negatief is ontladen.
- Verbeterde reconnect- en retrylogging.
- Logging meldt alleen de eerste uitval en het latere herstel.
- Nieuwe diagnostiek: totaal retries en laatste succesvolle meting.
- Uitgebreide netwerkgezondheidsgegevens.
- Roadmap, registerkaart en geteste hardware toegevoegd.

## 0.3.0

- Eerste benoemde sensoren en netwerkgezondheid.
