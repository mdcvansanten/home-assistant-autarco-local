# Autarco Local Roadmap

## Fase 1 — Stabiliteit (v0.3.x)

- [x] Bekabelde loggerverbinding en vast IP-adres
- [x] Persistente Modbus TCP-verbinding (v0.3.2)
- [x] Reconnect/retry-afhandeling en drie-failure beschikbaarheidsdrempel
- [x] Batterijpolariteit gecorrigeerd (v0.3.3)
- [x] Uptime/downtime en verbindingslogging (v0.3.4)
- [x] Persistente verbindingshistorie na herstart (v0.3.5)
- [ ] Meerdaagse praktijktest en vergelijking met netwerkmonitoring
- [ ] Waarden opnieuw vergelijken met Dyness en Autarco

**Exit-criterium:** stabiele communicatie, verklaarbare uitval en gevalideerde
polariteit, schaalfactoren en beschikbaarheid.

## Fase 2 — Installer-instellingen uitlezen (v0.4.x)

- [ ] Opties uit de Autarco Installer App volledig inventariseren
- [x] Eerste relevante Modbus holding registers identificeren en documenteren
- [x] Eerste set instellingen read-only in Home Assistant aanbieden (v0.4.0)
- [ ] Waarden en benamingen vergelijken met de Autarco Installer App
- [ ] Grenzen, schaalfactoren en enumeraties valideren
- [ ] TOU/charge-discharge schedules inventariseren en read-only toevoegen

## Fase 3 — Veilige schrijffuncties (v0.5.x en verder)

- [ ] Alleen bewezen veilige instellingen schrijfbaar maken
- [ ] Waarden vóór schrijven valideren
- [ ] Na schrijven opnieuw uitlezen en resultaat bevestigen
- [ ] Oude en nieuwe waarde loggen
- [ ] Foutafhandeling en herstelpad testen

## v1.0 MVP

- [ ] Stabiele lokale monitoring
- [ ] Belangrijkste Installer App-instellingen herkenbaar uitlezen
- [ ] Geselecteerde instellingen veilig lokaal wijzigen
- [ ] Documentatie en installatie-instructies voor andere gebruikers

Het gecombineerde Home Assistant-energiedashboard (Sessy P1 + Autarco + Dyness)
is een apart project en geen afhankelijkheid van Autarco Local.
