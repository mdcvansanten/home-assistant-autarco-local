# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> v0.5.0 leest inverterinstellingen uit, maar voert nog steeds **geen Modbus-schrijfopdrachten** uit.

## Versie 0.5.0 — inverterinstellingen read-only

v0.5.0 voegt een aparte holding-registerlaag toe om belangrijke inverterinstellingen lokaal uit te lezen zonder de bestaande PV-, batterij- en verbindingsmonitoring te verstoren.

Nieuw in v0.5.0:

- read-only uitlezen van belangrijke batterij- en bedrijfsinstellingen;
- Reserve-SOC, minimum-SOC, force-charge-SOC en off-grid minimum-SOC;
- Self-use, Time-of-use, Off-grid, Reserve Battery, Grid Charge en Feed-in Priority status;
- geplande laad- en ontlaadstroom;
- drie laad-/ontlaadtijdsloten;
- zichtbare classificatie per instelling:
  - 🟢 standaardgebruiker;
  - 🟡 Expert Mode;
  - 🔴 installer/systeem — bedoeld om read-only te blijven;
- een aparte diagnostische sensor **Status instellingen uitlezen** met registeraantal, leestijd, unsupported blocks en laatste fout;
- settings-read is niet-kritisch: een niet-ondersteund holding-register maakt de bestaande monitoring niet unavailable;
- de eerder aanwezige dubbele `outage_started_at` diagnosewaarde is opgeschoond.

**Battery Select / accutype is bewust nog niet toegevoegd.** De functie is duidelijk, maar het exacte holding-register voor deze Autarco/Solis-generatie moet eerst betrouwbaar worden gevalideerd.

Zie [`docs/settings.md`](docs/settings.md) voor de registermapping, toegangsclassificatie en het hardwaretestplan.

## Bestaande monitoring

De v0.4 PV/zonnepanelenmonitoring blijft volledig behouden:

- berekend vermogen per PV-ingang/MPPT voor PV1 en PV2;
- PV3/PV4 spanning, stroom en berekend vermogen aanwezig maar standaard uitgeschakeld;
- actuele totale PV-productie;
- PV-opbrengst vandaag, deze maand, dit jaar en totaal;
- binaire status **PV-productie actief**;
- optionele diagnostiek voor PV-alarmcode en DC-busspanning;
- bestaande inverter-, batterij- en verbindingssensoren.

## Installatie via HACS

Voor een officiële release:

1. Gebruik de nieuwste gepubliceerde GitHub release.
2. Werk **Autarco Local** bij via HACS.
3. Herstart Home Assistant volledig.
4. Open **Instellingen → Apparaten & diensten → Autarco Local**.

Voor de v0.5.0 testbranch moet eerst de featurebranch/PR-build worden geïnstalleerd en op echte hardware worden gevalideerd voordat deze als release wordt gepubliceerd.

Aanbevolen verbindingsinstellingen voor het testsysteem:

- Modbus TCP-poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

## Roadmap

Zie [`docs/roadmap.md`](docs/roadmap.md).

## Licentie

MIT
