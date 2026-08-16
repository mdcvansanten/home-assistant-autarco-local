# Autarco Local → Local EMS Roadmap

## Visie

Autarco Local begon als een lokale Home Assistant-integratie om een Autarco hybride omvormer betrouwbaar uit te lezen en instellingen veilig te kunnen benaderen. De ontdekking dat de officiële Autarco/Solis-app lokale installerbediening via Bluetooth aanbiedt verandert het bestaansrecht van het project niet, maar wel de positionering.

Het doel wordt:

> **een lokaal, veilig, gebruiksvriendelijk en uiteindelijk vendor-onafhankelijk Energy Management System (EMS), met Autarco als eerste volledig ondersteunde device-driver en Home Assistant als eerste platform.**

De officiële fabrikant-app blijft geschikt voor commissioning en handmatige service. Local EMS voegt daar bovenop toe:

- begrijpelijke instellingen met context en uitleg;
- dependency-aware writes en veilige transacties;
- automatische validatie en read-back;
- historie/audit van wijzigingen;
- energie-optimalisatie op basis van PV, batterij, net, dynamische prijzen, EV, weer en gebruikersdoelen;
- lokale werking zonder verplichte cloud;
- multi-vendor ondersteuning;
- een installer/fleet-laag voor beheer van meerdere installaties.

## Productprincipes

1. **Local first** — kernfuncties moeten lokaal blijven werken.
2. **Safe by design** — een setting is nooit alleen een register; dependencies, grenzen en oorspronkelijke state horen bij dezelfde transactie.
3. **Original state wins** — een parent mode die al actief was, blijft actief. Alleen tijdelijke wijzigingen die Local EMS zelf heeft aangebracht mogen automatisch worden hersteld.
4. **No guessing** — geen onbekende registers, schaalfactoren of unlock-routes schrijven zonder validatie.
5. **Read → validate → write → read-back → verify → audit** voor iedere wijziging.
6. **Expert support, not expert punishment** — ook geavanceerde gebruikers krijgen beslisondersteuning in plaats van alleen waarschuwingen.
7. **Vendor abstraction** — de toekomstige EMS-kern kent capabilities en semantische settings; vendor-drivers vertalen deze naar Autarco/Solis, GoodWe, enzovoort.
8. **Privacy by design** — fleet-management kan met een uniek installatie-ID, health/version-status en opt-in telemetrie zonder standaard persoonsgegevens of volledige energiehistorie te verzamelen.

---

# Track A — Autarco Local device-driver

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

## Fase 3 — Settings inventory en UI (v0.5.x)

- [x] Eerste Installer App-opties geïnventariseerd
- [x] Eerste holding-registerblokken geïdentificeerd en gedocumenteerd
- [x] Belangrijkste instellingen read-only in Home Assistant aangeboden
- [x] Instellingen ingedeeld in 🟢 Standard, 🟡 Expert en 🔴 Installer/system
- [x] Settings-polling geïsoleerd van runtime-monitoring
- [x] Settings Center met grotere namen, waarde rechts en uitleg eronder
- [ ] Alle huidige mappings, grenzen, schaalfactoren en enumeraties hardware-valideren
- [ ] Register 43027 / Force-charge power limit opnieuw valideren tegen de officiële UI
- [ ] Battery Select / accutype exact identificeren; nooit raden
- [ ] Aanvullende lokale Installer-instellingen inventariseren en classificeren

Zie [`settings.md`](settings.md) voor de huidige mapping.

## Fase 4 — Dependency-aware writes (v0.6.x)

- [x] Eerste smalle write-pilot voor Off-grid minimum SOC
- [x] Read-back failure zichtbaar gemaakt
- [x] Hardwarebevinding: Off-grid minimum SOC is alleen wijzigbaar wanneer Off-grid actief is
- [x] State-preserving dependency-model ontworpen
- [x] Volledige work-mode state snapshotten wanneer een tijdelijke parent-mode wijziging nodig is
- [x] Als parent mode al actief is: niet uitschakelen na de target write
- [x] Cleanup/herstel ook na target-write failure
- [x] Conflict detecteren wanneer een externe actor tijdens de transactie de mode wijzigt
- [ ] Hardwaretest van de nieuwe dependency-aware 10% → 20% Off-grid SOC-transactie
- [ ] Exacte Modbus TCP write-semantiek van de LAN-stick bevestigen
- [ ] LAN-stick firmware en write-capabilities bevestigen
- [ ] RS485 EMS-route als officiële fallback/pro-route valideren
- [ ] Iedere nieuwe write eerst als één beperkte hardwarepilot toevoegen

Zie [`write-dependencies.md`](write-dependencies.md) en [`settings-decision-tree.md`](settings-decision-tree.md).

## Fase 5 — Complete Autarco v1.0 driver

- [ ] Alle ondersteunde settings hebben semantische metadata: bereik, unit, access-level, dependencies, effect-dependencies en safety-relaties
- [ ] Standard writes beschikbaar waar veilig bewezen
- [ ] Expert writes met preflight, waarschuwing, bevestiging en rollback/restore-pad
- [ ] Installer/system instellingen standaard read-only
- [ ] Auditlog met tijd, oude/nieuwe waarde, trigger en verificatie
- [ ] Diagnose van communicatie, meter, batterij/BMS en PV
- [ ] Documentatie/installatie voor andere Autarco LH-MII gebruikers
- [ ] Release-kanaal en hardware compatibility matrix

---

# Track B — Local EMS Core

De Home Assistant-integratie mag op termijn niet de plaats zijn waar alle vendorlogica, dependencyregels en optimalisatiealgoritmen permanent vastzitten.

Doelarchitectuur:

```text
                    Local EMS Core
               ┌──────────────────────┐
               │ Capability model     │
               │ Settings catalog     │
               │ Dependency engine    │
               │ Safety policies      │
               │ Transaction engine   │
               │ Audit/history        │
               │ Optimizer            │
               └──────────┬───────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
 Autarco driver      GoodWe driver      andere drivers
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
 Home Assistant       Web/PWA          EMS appliance
 integration             UI             Raspberry Pi/
                                        mini-PC
```

## Core milestones

- [ ] Semantisch capability-model ontwerpen (`battery.reserve_soc`, `storage.off_grid`, `schedule.charge_slot`, etc.)
- [ ] Vendor-driver interface definiëren
- [ ] Generieke dependency engine uit de huidige v0.6.x logica halen
- [ ] Transaction planner met preflight/restore/conflict detection
- [ ] Audit/event store vendor-onafhankelijk maken
- [ ] Policy engine voor Standard / Expert / Installer
- [ ] Test simulator/fake inverter voor settings-transacties
- [ ] Home Assistant adapter bovenop de core bouwen

---

# Track C — Slim EMS en energie-optimalisatie

## Home EMS

- [ ] Dynamische prijsintegratie (o.a. Nord Pool/EPEX bronnen via platformlaag)
- [ ] Batterijreserve dynamisch aanpassen op weersverwachting, nachtverbruik en backupdoel
- [ ] Goedkope uren gebruiken voor laden wanneer zinvol
- [ ] Dure uren gebruiken voor lokaal verbruik of gecontroleerde export
- [ ] PV-curtailment/exportstrategie
- [ ] EV-laadcoördinatie
- [ ] Water/verwarming/andere flexibele loads als optionele consumers
- [ ] Forecast versus werkelijkheid en zelflerende kalibratie
- [ ] Virtuele/simulatiemodus vóór automatische aansturing
- [ ] Financiële historie en eindafrekening

## Explainable EMS

Iedere automatische beslissing moet uitlegbaar zijn, bijvoorbeeld:

> Batterijreserve verhoogd van 30% naar 45% omdat vannacht 9,2 kWh verwacht verbruik wordt, de PV-forecast morgen laag is en 20% als technische minimumreserve geldt.

- [ ] Reden per beslissing opslaan
- [ ] Preview: “wat gaat het EMS de komende 24 uur doen?”
- [ ] Optionele handmatige override met automatische vervaltijd

---

# Track D — Multi-vendor

Autarco is de referentie-implementatie, niet de eindgrens.

Prioriteitsvolgorde pas bepalen na Autarco v1.0, maar architectuur voorbereiden voor:

- [ ] Solis direct
- [ ] GoodWe
- [ ] Dyness batterij/BMS waar lokaal protocol beschikbaar is
- [ ] BYD / Pylontech / andere batterijen via inverter of directe driver
- [ ] EVSE/wallbox drivers
- [ ] slimme meters / P1 / Modbus meters

Voor ieder merk dezelfde semantische UX: dezelfde betekenis, vendor-specifieke implementatie onder de motorkap.

---

# Track E — Distributie en commercieel model

Het commerciële onderscheid moet niet gebaseerd zijn op “een verborgen instelling kunnen wijzigen”. Waarde ontstaat door veiligheid, gemak, automatisering, diagnose en fleet-management.

## Mogelijke productlagen

### Community / Open Core
- lokale monitoring;
- basisdiagnose;
- Home Assistant integratie;
- publieke hardware compatibility informatie.

### Home
- veilige settings-bediening;
- beslisondersteuning;
- slimme batterij-/PV-/EV-automatisering;
- dashboards en historie.

### Pro / Advanced Home
- trading/prijsoptimalisatie;
- uitgebreide forecasting;
- rapportages;
- geavanceerde policies en meerdere assets.

### Installer / Fleet
- unieke installatie-ID's;
- online/offline/health;
- softwareversie;
- compatibility/firmware waarschuwingen;
- remote diagnose en opt-in supportdata;
- staged updates;
- geen standaard toegang tot persoonsgegevens vereist.

### Turnkey appliance
- Raspberry Pi / mini-PC image of SD-card/installer;
- eenvoudige onboarding;
- automatische updates;
- lokale recovery/backup.

Prijzen en licentiemodel worden pas vastgezet nadat supportlast, doelgroep en concrete waarde met pilots zijn gevalideerd.

---

# Track F — UX: van settingslijst naar beslisassistent

De UI moet uiteindelijk niet vragen: “welk register wil je wijzigen?”, maar: **“wat wil je bereiken?”**

Voorbeelden:

- Meer noodreserve bewaren
- Goedkope netstroom gebruiken
- Batterij 's nachts niet onder X% laten komen
- Laden/ontladen op tijdschema
- Export beperken
- Piekbelasting begrenzen
- Off-grid gedrag instellen

De app vertaalt het doel naar betrokken settings en toont vóór opslaan:

1. huidige toestand;
2. gewenste toestand;
3. betrokken dependencies;
4. eventuele tijdelijke modewijzigingen;
5. veiligheidschecks;
6. wat na afloop actief blijft;
7. verwachte functionele impact.

De levende specificatie hiervoor staat in [`settings-decision-tree.md`](settings-decision-tree.md).

---

# Release gates

Een setting mag pas van read-only naar schrijfbaar wanneer alle onderstaande punten waar zijn:

- [ ] register/command officieel of hardwarematig betrouwbaar gevalideerd;
- [ ] unit/schaalfactor gevalideerd;
- [ ] geldig bereik bekend;
- [ ] access-level beoordeeld;
- [ ] write-dependencies bekend;
- [ ] effect-dependencies bekend;
- [ ] safety-relaties bekend;
- [ ] pre-read aanwezig;
- [ ] write-result gecontroleerd;
- [ ] read-back gevalideerd;
- [ ] state restore getest indien nodig;
- [ ] conflictgedrag getest;
- [ ] foutpad getest;
- [ ] auditlog aanwezig;
- [ ] minstens één echte hardwaretest uitgevoerd.

## Strategisch einddoel

**Autarco Local v1.0** wordt de betrouwbare referentie-driver. Daarna wordt de generieke intelligentie stapsgewijs losgemaakt naar **Local EMS Core**, zodat dezelfde veilige en gebruiksvriendelijke logica op Home Assistant, een web/PWA-interface en een zelfstandige EMS-appliance kan draaien.
