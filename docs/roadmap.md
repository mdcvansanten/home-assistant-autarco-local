# Autarco Local Roadmap

## Projectscope

**Autarco Local blijft bewust gericht op de Autarco-installatie thuis en op betrouwbare ondersteuning van deze Autarco/Solis-hardware in Home Assistant.**

Dit repository wordt dus **geen multi-vendor EMS-platform**, geen installer-fleetplatform en geen generieke commerciële productlaag.

De bredere inzichten die hier ontstaan — dependency-aware writes, state preservation, settings-metadata, veilige transacties, diagnose en gebruiksvriendelijke beslisondersteuning — dienen later als **referentie en praktijkproef** voor een afzonderlijk SNS-platform.

Dat SNS-platform krijgt een **eigen GitHub-repository, eigen architectuur en eigen roadmap**. Daar wordt later pas de configureerbare multi-vendor aanpak gebouwd waarbij een installateur op locatie de aanwezige apparaten selecteert en configureert.

### Scopegrens

**In Autarco Local:**

- Autarco/Solis inverter lokaal uitlezen;
- instellingen van de thuisinstallatie begrijpen, valideren en veilig bedienen;
- Home Assistant-integratie en Settings Center;
- dependency- en safetyregels voor deze hardware;
- diagnose, logging, historie en hardwarevalidatie;
- eventueel Autarco-specifieke automatisering die nodig is om de integratie goed te testen.

**Niet in Autarco Local:**

- GoodWe/Solis-direct/andere inverterdrivers als generiek product;
- configureerbare device-selectie voor installateurs;
- generieke vendor abstraction/core;
- installer fleet/cloud management;
- commerciële subscriptions/licensing;
- turnkey multi-vendor appliance.

Deze onderwerpen horen later in het afzonderlijke **SNS-platformproject**.

---

# Fase 1 — Stabiliteit (v0.3.x)

- [x] Bekabelde loggerverbinding en vast IP-adres
- [x] Persistente Modbus TCP-verbinding (v0.3.2)
- [x] Reconnect/retry-afhandeling en drie-failure beschikbaarheidsdrempel
- [x] Batterijpolariteit gecorrigeerd (v0.3.3)
- [x] Uptime/downtime en verbindingslogging (v0.3.4)
- [x] Persistente verbindingshistorie na herstart (v0.3.5)
- [ ] Meerdaagse praktijktest en vergelijking met netwerkmonitoring

# Fase 2 — PV / zonnepanelenmonitoring (v0.4.x)

- [x] PV1/PV2 spanning en stroom lokaal uitlezen
- [x] Vermogen per PV-ingang afleiden uit spanning × stroom
- [x] PV-opbrengst vandaag, maand, jaar en totaal uitlezen
- [x] PV-productiestatus toevoegen
- [x] PV3/PV4 voorbereid en standaard uitgeschakeld
- [ ] Waarden op echte Autarco-hardware vergelijken met Installer App/cloud
- [ ] Fysieke strings/MPPT's documenteren
- [ ] Veilige afwijkingsdetectie per string ontwikkelen nadat de mapping bewezen is
- [ ] Later: verwachte versus werkelijke opbrengst met lokale forecastgegevens

# Fase 3 — Settings inventory en UI (v0.5.x)

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

Zie [`settings.md`](settings.md) voor de huidige mapping en [`settings-decision-tree.md`](settings-decision-tree.md) voor de functionele afhankelijkheden.

# Fase 4 — Dependency-aware writes (v0.6.x)

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
- [ ] RS485 EMS-route als mogelijke officiële fallback valideren
- [ ] Iedere nieuwe write eerst als één beperkte hardwarepilot toevoegen

Zie [`write-dependencies.md`](write-dependencies.md).

# Fase 5 — Complete dependency- en beslisboom

Doel: ook een expert moet vóór een wijziging kunnen zien **wat de instelling doet, waarvan hij afhankelijk is en welke andere waarden of modes geraakt kunnen worden**.

- [x] Dependency-types definiëren: write, effect, safety, exclusivity, hardware en restore
- [x] Eerste master decision tree en settings-matrix documenteren
- [ ] Iedere momenteel gemapte setting hardwarematig nalopen
- [ ] Per setting geldig bereik en schaalfactor bevestigen
- [ ] Per setting parent/effect-mode bevestigen
- [ ] Alle cross-setting safetyrelaties valideren
- [ ] Onderlinge exclusiviteit van work modes op hardware controleren
- [ ] Time-of-Use slots/stromen inclusief overlap en `00:00` gedrag testen
- [ ] Battery Reserve / Reserve SOC afhankelijkheid testen
- [ ] Allow Grid Charging / Force-charge gedrag testen
- [ ] Off-grid dependency en herstelpad testen zonder ongewenst installatiestate te wijzigen
- [ ] Installer/system dependencies meenemen als read-only preconditions
- [ ] Beslisboom voeden vanuit gestructureerde metadata zodat UI en backend dezelfde regels gebruiken

# Fase 6 — Diagnose en historie

- [ ] Communicatie-/Modbus-diagnose verder verdiepen
- [ ] LAN-stick versus inverterproblemen beter onderscheiden
- [ ] Batterij/BMS-communicatie diagnostiek
- [ ] Meter/CT-diagnose
- [ ] PV/MPPT-diagnose
- [ ] Setting-wijzigingen auditen: tijd, oude waarde, nieuwe waarde, trigger, read-back
- [ ] Herstel-/conflictmeldingen duidelijk in Home Assistant tonen
- [ ] Meerdaagse/historische trends bewaren waar nuttig

# Autarco Local v1.0 doel

Autarco Local v1.0 is **geen generiek EMS**, maar een zeer betrouwbare en gebruiksvriendelijke lokale Home Assistant-integratie voor de thuis-Autarco-installatie.

Voor v1.0 willen we minimaal:

- [ ] stabiele lokale inverter-, PV-, grid- en batterijmonitoring;
- [ ] betrouwbare verbindingsdiagnostiek;
- [ ] gevalideerde settingscatalogus;
- [ ] duidelijke Standard / Expert / Installer-classificatie;
- [ ] volledige dependency-/safetybeslisboom voor ondersteunde settings;
- [ ] geselecteerde bewezen veilige writes;
- [ ] state-preserving transactions en verplichte read-back;
- [ ] audit/diagnose van writes;
- [ ] prettig Settings Center op mobiel en desktop;
- [ ] duidelijke installatie- en herstelprocedure.

---

# Handoff naar toekomstig SNS-platform — apart project

Pas **nadat Autarco Local thuis voldoende volwassen en bewezen is**, starten we een nieuw GitHub-project voor SNS.

Dat project mag de opgedane kennis gebruiken, maar bouwt bewust een nieuwe generieke architectuur voor:

- installateur kiest op locatie welke apparaten aanwezig zijn;
- configureerbare inverter-, batterij-, meter- en EVSE-drivers;
- meerdere leveranciers/modellen;
- rollen voor installateur en eindgebruiker;
- lokale EMS-functies;
- veilige updates;
- optionele monitoring/fleetfunctionaliteit;
- commerciële distributie/subscription indien gewenst.

**Belangrijk:** deze toekomstige functionaliteit wordt niet alvast in Autarco Local ingebouwd. Autarco Local blijft de praktische Autarco-referentie en testomgeving; SNS wordt een apart product/repository.

# Release gates voor Autarco settings

Een setting mag pas van read-only naar schrijfbaar wanneer:

- [ ] exact register/command gevalideerd is;
- [ ] unit en schaalfactor gevalideerd zijn;
- [ ] geldig bereik bekend is;
- [ ] access-level beoordeeld is;
- [ ] write-dependencies bekend zijn;
- [ ] effect-dependencies bekend zijn;
- [ ] safety-relaties bekend zijn;
- [ ] hardware/config prerequisites bekend zijn;
- [ ] pre-read aanwezig is;
- [ ] write-result gecontroleerd wordt;
- [ ] read-back gevalideerd wordt;
- [ ] state restore getest is indien nodig;
- [ ] conflictgedrag getest is;
- [ ] foutpad getest is;
- [ ] auditlog aanwezig is;
- [ ] minstens één echte hardwaretest is uitgevoerd.
