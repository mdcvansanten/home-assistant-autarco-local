# Read-only inverter settings

v0.4.x gebruikt deze pagina als validatielijst voor de instellingen die later
mogelijk schrijfbaar worden.

## Uitgangspunten

1. Eerst uitsluitend lezen.
2. Waarde en schaal vergelijken met de Autarco Installer App.
3. Alleen een register als `bevestigd` markeren na vergelijking op echte hardware.
4. Pas in v0.5.x een schrijfpad toevoegen.
5. Een toekomstige write moet invoer valideren, schrijven, opnieuw uitlezen en
   de wijziging bevestigen.

## Eerste set in v0.4.0

| HA-entiteit | Register | Doel | Validatie |
|---|---:|---|---|
| Batterijmodel | 43009 | Geselecteerd batterij/BMS-profiel | nog valideren |
| Maximale laad-SOC | 43010 | Bovengrens SOC | nog valideren |
| Minimale ontlaad-SOC | 43011 | Ondergrens SOC | nog valideren |
| Maximale laadstroom | 43012 | Laadstroomlimiet | nog valideren |
| Maximale ontlaadstroom | 43013 | Ontlaadstroomlimiet | nog valideren |
| Geforceerde laad-SOC | 43018 | SOC-drempel voor force charge | nog valideren |
| Backup-SOC | 43024 | Reserve voor backupbedrijf | nog valideren |
| Opslagmodus | 43110 | Self-Use / TOU / Reserve / Off-Grid / Peak Shaving | nog valideren |
| Batterij maximale laadstroom | 43117 | Batterij-laadstroominstelling | nog valideren |
| Batterij maximale ontlaadstroom | 43118 | Batterij-ontlaadstroominstelling | nog valideren |

## Testprocedure

Maak na installatie van v0.4.0 een screenshot van **Configuratie** onder het
Autarco Local-apparaat en vergelijk elke weergegeven waarde met dezelfde
instelling in de Autarco Installer App.

Wijzig tijdens v0.4.x niets via Modbus. Als we een instelling in de officiële
Installer App bewust aanpassen, wachten we maximaal vijf minuten en controleren
we of de read-only Home Assistant-waarde dezelfde wijziging laat zien.
