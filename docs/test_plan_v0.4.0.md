# v0.4.0 praktijk-testplan

## Doel

Controleren dat de eerste read-only holding-register instellingen op de Autarco
S2.LH-MII overeenkomen met de officiële Autarco Installer App, zonder de normale
monitoring te verstoren.

## Voor installatie

- v0.3.5 draait stabiel.
- Noteer de huidige waarden uit de Autarco Installer App voor de instellingen
  die in `docs/settings.md` staan.

## Na installatie

1. Controleer dat de bestaande realtime sensoren blijven werken.
2. Controleer dat **Modbus-verbinding** verbonden blijft.
3. Open het Autarco Local-apparaat en controleer de sectie **Configuratie**.
4. Vergelijk elke read-only instelling met de Autarco Installer App.
5. Controleer bij **Opslagmodus** ook de attributen, vooral Time Of Use,
   reserve mode en grid charging.
6. Laat de integratie minstens 15 minuten draaien zodat meerdere settings-polls
   van 5 minuten zijn uitgevoerd.
7. Controleer het Home Assistant-log op `autarco_local` en `pymodbus`.

## Verwachte uitkomst

- Normale monitoring blijft op het bestaande pollinterval functioneren.
- Settings worden maximaal eens per 5 minuten gelezen.
- Niet-ondersteunde settings blijven unavailable zonder de hoofdverbinding te
  laten falen.
- Er worden geen holding registers geschreven.

## Terugkoppeling

Leg per instelling vast: Home Assistant-waarde, Installer App-waarde en
`gelijk / afwijkend / niet beschikbaar`. Deze vergelijking bepaalt welke
registers in de volgende v0.4.x stap als bevestigd worden gemarkeerd.
