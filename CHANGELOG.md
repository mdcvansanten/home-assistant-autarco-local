# Changelog

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
