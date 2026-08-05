# Register Map

Statuswaarden:

- `bevestigd`: gecontroleerd met een onafhankelijke bron op de Autarco-installatie.
- `waarschijnlijk`: publieke Solis Hybrid-map en waarde/schaal zijn consistent; verdere Autarco-validatie nodig.
- `afgeleid`: geen zelfstandig register; berekend uit andere registers.
- `onderzoek`: betekenis of schaal is nog onbekend.

## PV / MPPT

| Register(s) | Sensor | Schaal | Status |
|---|---|---:|---|
| 33029–33030 | PV-opbrengst totaal | 1 kWh | waarschijnlijk |
| 33031–33032 | PV-opbrengst deze maand | 1 kWh | waarschijnlijk |
| 33035 | PV-opbrengst vandaag | 0,1 kWh | waarschijnlijk |
| 33037–33038 | PV-opbrengst dit jaar | 1 kWh | waarschijnlijk |
| 33049 | PV1-spanning | 0,1 V | bevestigd |
| 33050 | PV1-stroom | 0,1 A | waarschijnlijk |
| 33049 × 33050 | PV1-vermogen | V × A | afgeleid |
| 33051 | PV2-spanning | 0,1 V | bevestigd |
| 33052 | PV2-stroom | 0,1 A | waarschijnlijk |
| 33051 × 33052 | PV2-vermogen | V × A | afgeleid |
| 33053 | PV3-spanning | 0,1 V | waarschijnlijk, standaard uit |
| 33054 | PV3-stroom | 0,1 A | waarschijnlijk, standaard uit |
| 33053 × 33054 | PV3-vermogen | V × A | afgeleid, standaard uit |
| 33055 | PV4-spanning | 0,1 V | waarschijnlijk, standaard uit |
| 33056 | PV4-stroom | 0,1 A | waarschijnlijk, standaard uit |
| 33055 × 33056 | PV4-vermogen | V × A | afgeleid, standaard uit |
| 33057–33058 | Totaal PV-vermogen | 1 W | waarschijnlijk |
| 33070 | PV/alarmcode | ruwe waarde | onderzoek, diagnostiek |
| 33071 | PV DC-busspanning | 0,1 V | waarschijnlijk, diagnostiek |

De per-input vermogens zijn berekende DC-waarden. Door afronding, MPPT-gedrag en omzettingsverliezen hoeven PV1 + PV2 (+ PV3/PV4) niet exact gelijk te zijn aan het totale PV-vermogen van de omvormer.

## Overige monitoring

| Register(s) | Sensor | Schaal | Status |
|---|---|---:|---|
| 33073–33075 | Fasespanning L1–L3 | 0,1 V | bevestigd |
| 33079–33080 | Actief omvormervermogen | 1 W | waarschijnlijk |
| 33093 | Omvormertemperatuur | 0,1 °C | bevestigd |
| 33094 | Netfrequentie | 0,01 Hz | bevestigd |
| 33133 | Batterijspanning | 0,1 V | bevestigd |
| 33134–33135 | Batterijstroom/richting | 0,1 A | bevestigd |
| 33139 | Batterij-SOC | 1 % | bevestigd |
| 33147 | Huisverbruik | 1 W | waarschijnlijk |
| 33149–33150 | Batterijvermogen | 1 W | bevestigd |
| 33151–33152 | Netvermogen | 1 W | waarschijnlijk |

Polariteitsconventie vanaf v0.3.3:

- positief batterijvermogen/stroom = laden;
- negatief batterijvermogen/stroom = ontladen.
