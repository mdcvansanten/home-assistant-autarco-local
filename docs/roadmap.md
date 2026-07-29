# Autarco Local Roadmap

## Fase 1 — Stabiliteit

### v0.3.1

- [x] Bekabelde loggerverbinding
- [x] Vast IP-adres
- [x] Nieuwe TCP-sessie per poll
- [x] Configureerbare retries
- [x] Batterijstroompolariteit gecorrigeerd
- [x] Batterijvermogenspolariteit gecorrigeerd
- [x] Logging bij uitval en herstel
- [x] Diagnostiek voor retries en laatste succesvolle meting
- [ ] Zeven dagen praktijktest zonder onverwachte uitval
- [ ] Waarden opnieuw vergelijken met Dyness en Autarco

**Exit-criterium:** minimaal zeven dagen stabiel en correcte polariteit,
schaalfactoren en beschikbaarheid.

## Fase 2 — Registermapping (v0.4.0)

- [ ] Registerkaart afronden
- [ ] PV-, AC-, net- en batterijregisters valideren
- [ ] Status-, fout- en firmwarevelden identificeren
- [ ] Niet-gevalideerde sensoren duidelijk markeren

## Fase 3 — Dashboard (v0.5.0)

- [ ] Live energiestromen
- [ ] Sessy P1 integreren
- [ ] Dyness batterijgegevens integreren
- [ ] Omvormer-, net-, batterij- en diagnosepagina

## Fase 4 — Expertmodus (v0.6.0)

- [ ] Register Explorer
- [ ] Register Monitor
- [ ] CSV-export
- [ ] Live Modbus Viewer

## Fase 5 — Veilige schrijffuncties (v1.0.0)

- [ ] Holding registers uitsluitend lezen
- [ ] Registeradressen en grenzen bevestigen
- [ ] Expertmodus standaard uitgeschakeld
- [ ] Schrijven, teruglezen en valideren
- [ ] Alleen bewezen veilige instellingen aanbieden
