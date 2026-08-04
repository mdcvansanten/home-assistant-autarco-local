# Register Map

Statuswaarden:

- `bevestigd`: gecontroleerd met een onafhankelijke bron op de Autarco-installatie.
- `waarschijnlijk`: register/schaal is extern onderbouwd maar moet nog op Autarco worden gevalideerd.
- `onderzoek`: betekenis of schaal is nog onbekend.

## Input registers — monitoring

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

## Holding registers — read-only settings (v0.4.0)

Deze registers worden in v0.4.0 **alleen gelezen**. De status blijft
`waarschijnlijk` totdat de waarde op de Autarco S2.LH-MII is vergeleken met de
Autarco Installer App.

| Register | Instelling | Schaal / codering | Status |
|---|---|---|---|
| 43009 | Batterijmodel | enum; Dyness HV = `0x0600` | waarschijnlijk |
| 43010 | Maximale laad-SOC | 1 % | waarschijnlijk |
| 43011 | Minimale ontlaad-SOC | 1 % | waarschijnlijk |
| 43012 | Maximale laadstroom | 0,1 A | waarschijnlijk |
| 43013 | Maximale ontlaadstroom | 0,1 A | waarschijnlijk |
| 43018 | Geforceerde laad-SOC | 1 % | waarschijnlijk |
| 43024 | Backup-SOC | 1 % | waarschijnlijk |
| 43110 | Opslagmodus | bitmask | waarschijnlijk |
| 43117 | Batterij maximale laadstroom | 0,1 A | waarschijnlijk |
| 43118 | Batterij maximale ontlaadstroom | 0,1 A | waarschijnlijk |

Register 43110 bevat naast de hoofdmodus onafhankelijke bits voor onder andere
Time Of Use, battery wakeup, reserve mode en grid charging. v0.4.0 exposeert die
alleen als attributen van de read-only opslagmodussensor.
