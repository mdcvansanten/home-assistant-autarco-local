# PV / zonnepanelenmonitoring

## Doel van v0.4.0

De eerste PV-release van Autarco Local moet lokaal en zonder cloud duidelijk maken:

- hoeveel DC-vermogen de omvormer totaal uit PV ontvangt;
- wat spanning, stroom en berekend vermogen per gebruikte PV-ingang/MPPT zijn;
- hoeveel energie vandaag, deze maand, dit jaar en in totaal is geproduceerd;
- of er op dit moment PV-productie aanwezig is;
- welke ruwe PV-diagnostiek beschikbaar is voor vervolgonderzoek.

## Entiteiten

Standaard zichtbaar:

- PV1 spanning, stroom en vermogen
- PV2 spanning, stroom en vermogen
- totaal PV-vermogen
- PV-opbrengst vandaag
- PV-opbrengst deze maand
- PV-opbrengst dit jaar
- PV-opbrengst totaal
- PV-productie actief

Standaard uitgeschakeld:

- PV3/PV4 spanning, stroom en vermogen
- PV-alarmcode
- PV DC-busspanning

PV3/PV4 zijn voorbereid omdat de publieke Solis Hybrid-registermap deze adressen definieert. Ze worden pas standaard ingeschakeld voor modellen waarop we hebben bevestigd dat die ingangen werkelijk bestaan.

## Geen automatische health-score in v0.4.0

Een verschil tussen PV1 en PV2 is niet automatisch een defect. Strings kunnen verschillen in:

- aantal panelen;
- oriëntatie;
- hellingshoek;
- schaduw;
- aangesloten vermogen.

Daarom voegt v0.4.0 nog geen alarm toe op basis van een percentageverschil tussen PV1 en PV2. Na documentatie van de echte installatie kunnen we historische baseline-detectie toevoegen.

## Praktijktest

Na installatie:

1. Controleer overdag PV1/PV2 spanning en stroom.
2. Vergelijk totaal PV-vermogen met de huidige Autarco-weergave.
3. Controleer of PV1/PV2-vermogen logisch overeenkomt met spanning × stroom.
4. Vergelijk `PV-opbrengst vandaag` met de Autarco-app aan het einde van de dag.
5. Controleer de maand-, jaar- en totaaltellers.
6. Controleer dat `PV-productie actief` overdag aan is en 's nachts uit.
7. Laat de integratie minimaal een volledige zonnige dag draaien voordat we conclusies trekken over stringgedrag.

v0.4.0 voert uitsluitend input-register reads uit en bevat geen Modbus write-pad.
