# Autarco Local Roadmap

## Fase 1 — Stabiliteit (v0.3.x)

- [x] Bekabelde loggerverbinding en vast IP-adres
- [x] Persistente Modbus TCP-verbinding (v0.3.2)
- [x] Reconnect/retry-afhandeling en drie-failure beschikbaarheidsdrempel
- [x] Batterijpolariteit gecorrigeerd (v0.3.3)
- [x] Uptime/downtime en verbindingslogging (v0.3.4)
- [x] Persistente verbindingshistorie na herstart (v0.3.5)
- [ ] Meerdaagse praktijktest en vergelijking met netwerkmonitoring

## Fase 2 — PV / zonnepanelenmonitoring (v0.4.x)

- [x] PV1/PV2 spanning en stroom lokaal uitlezen
- [x] Vermogen per PV-ingang afleiden uit spanning × stroom
- [x] PV-opbrengst vandaag, maand, jaar en totaal uitlezen
- [x] PV-productiestatus toevoegen
- [x] PV3/PV4 voorbereid en standaard uitgeschakeld
- [ ] Waarden op echte Autarco-hardware vergelijken met Installer App/cloud
- [ ] Fysieke strings/MPPT's documenteren
- [ ] Pas daarna veilige afwijkingsdetectie per string ontwikkelen
- [ ] Later: verwachte versus werkelijke opbrengst met weer/PV-forecast

## Fase 3 — Installer-instellingen uitlezen (v0.5.x)

- [ ] Opties uit de Autarco Installer App inventariseren
- [ ] Bijbehorende Modbus holding registers identificeren en documenteren
- [ ] Belangrijkste instellingen eerst read-only in Home Assistant aanbieden
- [ ] Grenzen, schaalfactoren en enumeraties valideren

## Fase 4 — Veilige schrijffuncties (v0.6.x en verder)

- [ ] Alleen bewezen veilige instellingen schrijfbaar maken
- [ ] Waarden vóór schrijven valideren
- [ ] Na schrijven opnieuw uitlezen en resultaat bevestigen
- [ ] Oude en nieuwe waarde loggen
- [ ] Foutafhandeling en herstelpad testen

## v1.0 MVP

- [ ] Stabiele lokale monitoring
- [ ] Uitgebreide PV/MPPT-monitoring
- [ ] Belangrijkste Installer App-instellingen herkenbaar uitlezen
- [ ] Geselecteerde instellingen veilig lokaal wijzigen
- [ ] Documentatie en installatie-instructies voor andere gebruikers

Het gecombineerde Home Assistant-energiedashboard (Sessy P1 + Autarco + Dyness) blijft een apart project en geen afhankelijkheid van Autarco Local.
