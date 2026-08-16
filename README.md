# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale Home Assistant-integratie voor de Autarco hybride omvormer in de thuisinstallatie, met Autarco LH-MII als huidige gevalideerde hardwarelijn.

> [!CAUTION]
> De `v0.6.x` ontwikkellijn bevat **beperkte hardware-write pilots**. Dit is nog geen algemene vrijgave om invertersettings te schrijven. Alleen expliciet gevalideerde transacties mogen worden uitgevoerd; overige settings blijven read-only of locked.

## Scope van dit project

Autarco Local blijft bewust een **Autarco-thuisproject**. Het doel is om de lokale Autarco-installatie betrouwbaar, veilig en prettig vanuit Home Assistant te monitoren, diagnosticeren en waar verantwoord te bedienen.

Dit repository wordt **geen generiek multi-vendor EMS-platform**.

De kennis die hier ontstaat — zoals dependency-aware writes, state preservation, settings-metadata, beslisondersteuning en diagnose — wordt later gebruikt als referentie voor een **apart SNS-platformproject in een eigen GitHub-repository**. Daar komt pas de configureerbare multi-vendor architectuur voor installateurs.

Zie **[`docs/roadmap.md`](docs/roadmap.md)** voor de scopegrens en planning.

## Settings en beslisondersteuning

De invertersettings zijn ingedeeld in:

- 🟢 **Standard** — normale gebruikersinstellingen na write-validatie;
- 🟡 **Expert** — alleen met context, preflight en bevestiging;
- 🔴 **Installer/system** — zichtbaar voor diagnose, standaard hard read-only.

Belangrijk uitgangspunt: een setting wordt niet als een los register behandeld. Autarco Local houdt rekening met parent modes, onderlinge uitsluiting, safety-relaties en de oorspronkelijke toestand van de installatie.

Voorbeeld: Off-grid minimum SOC is op de huidige hardware alleen wijzigbaar wanneer Off-grid actief is. Als Off-grid al actief was, blijft het actief. Alleen wanneer de integratie een mode zelf tijdelijk heeft gewijzigd, mag zij die na afloop herstellen.

Lees:

- **[`docs/settings-decision-tree.md`](docs/settings-decision-tree.md)** — volledige Autarco-beslisboom, dependency-matrix en expert-preflight;
- **[`docs/write-dependencies.md`](docs/write-dependencies.md)** — state-preservation en transactionregels;
- **[`docs/settings.md`](docs/settings.md)** — huidige registermapping en validatiegegevens.

## Bestaande monitoring

Autarco Local biedt onder andere:

- inverter-, net- en batterijmonitoring;
- PV1/PV2 spanning, stroom en berekend vermogen;
- PV-opbrengst vandaag, maand, jaar en totaal;
- PV3/PV4 voorbereid en standaard uitgeschakeld;
- verbindingsdiagnostiek, retries, uptime/downtime en persistente historie;
- aparte non-critical holding-register polling voor invertersettings.

## Veilige write-policy

Een setting wordt pas schrijfbaar als minimaal bekend en getest is:

1. exact register/command;
2. unit en schaalfactor;
3. geldig bereik;
4. access-level;
5. write- en effect-dependencies;
6. cross-setting safetyregels;
7. hardware/config prerequisites;
8. fresh pre-read;
9. write-result;
10. read-back verificatie;
11. restore/conflictgedrag indien een parent mode betrokken is;
12. audit/foutpad;
13. echte hardwarevalidatie.

Geen guessed registers, geen undocumented unlocks en geen blind rollback.

## Installatie via HACS

Voor een officiële release:

1. Gebruik de nieuwste gepubliceerde GitHub release.
2. Werk **Autarco Local** bij via HACS.
3. Herstart Home Assistant volledig.
4. Open **Instellingen → Apparaten & diensten → Autarco Local**.

Featurebranches en draft PR's zijn uitsluitend testbuilds en moeten eerst op echte hardware worden gevalideerd.

Aanbevolen verbindingsinstellingen voor de huidige testopstelling:

- Modbus TCP-poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

## Belangrijke documentatie

- [Roadmap](docs/roadmap.md)
- [Settings decision tree](docs/settings-decision-tree.md)
- [Write dependencies](docs/write-dependencies.md)
- [Settings/register map](docs/settings.md)

## Toekomstig SNS-platform

Het SNS-platform wordt **niet in deze repository ontwikkeld**. Zodra Autarco Local thuis voldoende bewezen is, starten we daarvoor een apart GitHub-project met eigen architectuur, installerconfiguratie en multi-vendor device-selectie.

## Licentie

MIT