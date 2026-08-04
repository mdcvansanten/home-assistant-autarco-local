# Register Map

Statuswaarden:

- `bevestigd`: gecontroleerd met een onafhankelijke bron.
- `waarschijnlijk`: waarde en schaal lijken correct, verdere controle nodig.
- `onderzoek`: betekenis of schaal is nog onbekend.

| Register(s) | Sensor | Schaal | Status |
|---|---|---:|---|
| 33049 | PV1-spanning | 0,1 V | bevestigd |
| 33050 | PV1-stroom | 0,1 A | waarschijnlijk |
| 33051 | PV2-spanning | 0,1 V | bevestigd |
| 33052 | PV2-stroom | 0,1 A | waarschijnlijk |
| 33057–33058 | PV-vermogen | 1 W | waarschijnlijk |
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
