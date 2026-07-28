# Changelog

## 0.2.3

- Gebruikt dezelfde synchrone `ModbusTcpClient` die in de terminaltest werkte.
- Voert alle blokkerende Modbus-communicatie uit via de Home Assistant executor.
- Leest registers in bevestigde blokken van 10.
- Accepteert ook korte antwoorden van de logger.
- Blijft volledig uitsluitend-lezen.

## 0.2.2

- Verwijdert de conflicterende vaste PyModbus-versie.
- Leest registerblokken van 10.
