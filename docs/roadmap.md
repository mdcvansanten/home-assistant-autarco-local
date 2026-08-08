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

- [x] Eerste set Installer App-opties geïnventariseerd
- [x] Eerste holding-registerblokken geïdentificeerd en gedocumenteerd
- [x] Belangrijkste instellingen read-only in Home Assistant aangeboden
- [x] Instellingen ingedeeld in standaard-, expert- en installer-niveau
- [x] Settings-polling geïsoleerd van de bestaande runtime-monitoring
- [ ] Waarden, grenzen, schaalfactoren en enumeraties op echte Autarco-hardware valideren
- [ ] Battery Select / accutype-register exact identificeren voordat dit wordt toegevoegd
- [ ] Aanvullende Installer App-instellingen inventariseren en per register valideren

Zie [`settings.md`](settings.md) voor de huidige registermapping en het testplan.

## Fase 4 — Veilige schrijffuncties (v0.6.x en verder)

- [ ] Alleen bewezen veilige standaardinstellingen schrijfbaar maken
- [ ] Expert-instellingen alleen via Expert Mode met waarschuwing en bevestiging aanbieden
- [ ] Installer- en systeeminstellingen read-only houden
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
