# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> Dit is een ontwikkelversie. Er worden geen Modbus-schrijfopdrachten uitgevoerd.

## Versie 0.4.2 — PV / zonnepanelenmonitoring

v0.4.2 bevat de v0.4 PV/zonnepanelenmonitoring plus een packaging/translation-fix zodat Home Assistant en HACS de nieuwe entiteiten en versie correct herkennen.

Nieuw in de v0.4-serie:

- berekend vermogen per PV-ingang/MPPT voor PV1 en PV2;
- PV3/PV4 spanning, stroom en berekend vermogen aanwezig maar standaard uitgeschakeld;
- actuele totale PV-productie;
- PV-opbrengst vandaag, deze maand, dit jaar en totaal;
- binaire status **PV-productie actief**;
- optionele diagnostiek voor PV-alarmcode en DC-busspanning;
- alle bestaande inverter-, batterij- en verbindingssensoren blijven behouden;
- geen nieuwe Modbus-registerblokken nodig: de gebruikte PV-registers vallen binnen het bestaande input-registerbereik;
- geen write-functionaliteit.

v0.4.2 corrigeert daarnaast de Engelse runtimevertalingen voor de nieuwe PV-entiteiten en verhoogt de manifestversie correct. De eerder gepubliceerde `v0.4.1`-tag rapporteerde intern nog versie `0.4.0`; gebruik daarom v0.4.2 of nieuwer.

De vermogenssensoren per PV-ingang worden afgeleid uit lokale spanning × stroom. Ze zijn bedoeld als MPPT/string-monitoring en hoeven door afronding of omzettingsverliezen niet exact op te tellen tot het totale DC-PV-vermogen van de omvormer.

Een automatische "gezond / defect"-beoordeling per string wordt bewust nog niet toegevoegd. Daarvoor moeten eerst de fysieke stringindeling, oriëntatie en normale productiepatronen bekend en gevalideerd zijn.

Zie [`docs/pv_monitoring.md`](docs/pv_monitoring.md) voor de registers en het testplan.

## Installatie via HACS

1. Gebruik de nieuwste gepubliceerde GitHub release (v0.4.2 of nieuwer).
2. Werk **Autarco Local** bij via HACS.
3. Herstart Home Assistant volledig.
4. Open **Instellingen → Apparaten & diensten → Autarco Local**.

Aanbevolen instellingen voor het testsysteem:

- Modbus TCP-poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

> Bestaande installaties behouden eerdere entity-registrykeuzes. Nieuwe PV3/PV4- en detaildiagnostiek zijn standaard uitgeschakeld en kunnen handmatig worden aangezet.

## Roadmap

Zie [`docs/roadmap.md`](docs/roadmap.md).

## Licentie

MIT
