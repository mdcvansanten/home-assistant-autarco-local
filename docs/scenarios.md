# Autarco Local scenarios

Scenario's zijn doelgerichte combinaties van inverterinstellingen. Ze worden niet geactiveerd door één register te gokken: iedere onderliggende setting moet eerst hardwarematig zijn gevalideerd, inclusief dependencies, read-back en restoregedrag.

## Ontwerpregels

- Original state wins: alleen toestand die Autarco Local zelf tijdelijk wijzigt mag automatisch worden hersteld.
- Een scenario toont vóór activatie alle geplande wijzigingen en de verwachte eindtoestand.
- Parent modes worden expliciet behandeld.
- Externe wijzigingen tijdens uitvoering geven een conflict; geen blind rollback.
- Installer/systemsettings worden nooit stilzwijgend aangepast.
- Een scenario is pas uitvoerbaar als alle gebruikte writes op de thuisinstallatie zijn bewezen.

## Scenario's

### Normaal zelfgebruik
Doel: huis eerst voeden, daarna batterij laden, daarna overschot terugleveren.

Basis: Self-use.

### Accu vasthouden / niet ontladen
Doel: een gekozen hoeveelheid batterijenergie bewaren.

Beoogde bouwstenen:
- Battery Reserve aan;
- Reserved SOC = gekozen ondergrens;
- controle dat Reserved SOC niet onder Minimum battery SOC komt.

### Nu laden vanaf het net
Doel: onafhankelijk van tarieven of PV de batterij handmatig vanaf het net laden tot een gekozen doel-SOC.

Beoogde bouwstenen:
- Allow Grid Charging;
- tijdelijke laadregeling / Time of Use;
- gekozen laadstroom binnen inverter/BMS-limieten;
- actieve SOC-monitoring;
- automatisch stoppen zodra doel-SOC is bereikt;
- oorspronkelijke settings herstellen.

Dit is bewust geen 'Forcecharge SOC omhoogzetten'-truc: het scenario moet een expliciete, tijdelijke transactie zijn.

### Nacht-/tijdladen
Doel: laden binnen een gekozen tijdvak en daarbuiten normale Self-use hervatten.

Beoogde bouwstenen:
- Time of Use aan;
- charge slot;
- charge current;
- Allow Grid Charging indien netladen gewenst is;
- geen discharge slot tenzij expliciet gekozen.

### Maximaal terugleveren
Doel: PV-export prioriteit geven.

Basis: Feed-in Priority. Volgens Solis blijft de batterij in deze mode buiten geconfigureerde charge/discharge-tijden inactief.

### Peak shaving
Doel: maximale netimport begrenzen en pieken vanuit batterij/PV aanvullen.

Beoogde bouwstenen:
- Peak Shaving;
- Max Usable Grid Power;
- Baseline SOC;
- Allow Grid Charging indien gewenst;
- correcte lithium-BMS-communicatie en meterdata.

### Backupreserve
Doel: een vaste noodreserve bewaren voor netuitval.

Basis: Battery Reserve + Reserved SOC.

### Onderhoud / Battery Healing
Doel: gecontroleerd batterijherstel bij langdurig lage SOC.

Expert-only. Pas beschikbaar nadat Battery Healing, Healing SOC en Forcecharge-relaties op de Autarco-hardware zijn gevalideerd.

## Niet als algemeen scenario aanbieden

Off-grid mode is geen dagelijkse gebruikerspreset. Deze mode hoort bij een elektrisch geschikte off-grid/EPS-configuratie. Autarco Local mag Off-grid alleen tijdelijk gebruiken als technische write-dependency wanneer dat voor een afzonderlijk gevalideerde setting nodig is en de volledige oorspronkelijke state daarna veilig wordt hersteld.
