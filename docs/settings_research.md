# Settings research notes

Deze notities leggen vast waar de eerste v0.4.x read-only mappings vandaan komen
en wat nog op de Autarco S2.LH-MII moet worden bevestigd.

## Referentie

De eerste mappings zijn vergeleken met de publieke `Pho3niX90/solis_modbus`
implementatie voor Solis Hybrid omvormers, gebaseerd op het Solis Hybrid Modbus
protocol. Autarco Local neemt daarvan alleen een kleine, doelgerichte set over.

Belangrijk: een register wordt pas als **bevestigd voor Autarco** beschouwd na
praktijkvergelijking met de Autarco Installer App op de eigen omvormer.

## v0.4.0 selectie

- 43009 — battery model
- 43010 — max charge SOC
- 43011 — overdischarge SOC
- 43012 — max charge current
- 43013 — max discharge current
- 43018 — force charge SOC
- 43024 — backup SOC
- 43110 — storage mode bitmask
- 43117 — battery max charge current
- 43118 — battery max discharge current

## Waarom nog geen TOU-slots?

De Time Of Use-registers vormen een grotere set met meerdere firmwarevarianten.
Die voegen we pas toe nadat de eerste basisinstellingen op de Autarco-hardware
zijn gevalideerd. Daarmee houden we v0.4.0 klein en controleerbaar.

## Write-beleid

v0.4.x bevat geen Modbus-writepad. Een toekomstige write in v0.5.x wordt pas
toegevoegd wanneer register, schaal, geldige grenswaarden en readback op echte
hardware zijn bevestigd.
