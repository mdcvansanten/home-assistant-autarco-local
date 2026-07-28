# Changelog

## 0.2.2

- Verwijdert de conflicterende vaste PyModbus-versie uit `manifest.json`.
- Configuratiecontrole leest slechts 10 eerder bevestigde registers.
- De volledige scan gebruikt blokken van 10 registers.
- Niet-ondersteunde registerblokken met Modbus exception code 2 worden overgeslagen.
- Een groot verzoek van 125 registers wordt niet meer gebruikt.

## 0.2.0

- Eerste herbouwde ontwikkelversie.
