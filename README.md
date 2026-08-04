# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> v0.4.0 is nog steeds **uitsluitend-lezen**. Er worden geen Modbus-schrijfopdrachten uitgevoerd.

## Versie 0.4.0 — Installer-instellingen uitlezen

v0.4.0 start fase 2 van de roadmap. Naast de bestaande realtime monitoring leest
de integratie nu een eerste, bewust beperkte set inverterinstellingen uit via
**Modbus holding registers**.

De eerste read-only instellingen zijn:

- Batterijmodel
- Maximale laad-SOC
- Minimale ontlaad-SOC
- Maximale laadstroom
- Maximale ontlaadstroom
- Geforceerde laad-SOC
- Backup-SOC
- Opslagmodus
- Batterij maximale laadstroom
- Batterij maximale ontlaadstroom

De opslagmodus toont daarnaast als attributen onder andere Time Of Use,
battery wakeup, reserve mode en of laden vanaf het net is toegestaan.

### Veiligheidskeuze

De normale meetwaarden blijven elke ingestelde scanperiode worden gepolld.
Instellingen veranderen veel minder vaak en worden daarom slechts iedere
**5 minuten** gelezen. Een fout of niet-ondersteund instellingsregister maakt
de normale Autarco-monitoring niet onbeschikbaar.

De registers zijn gebaseerd op de Solis Hybrid Modbus-registerindeling die bij
de S2.LH-MII-familie hoort. In v0.4.x valideren we de waarden stap voor stap
tegen de Autarco Installer App op echte hardware voordat er enige
schrijffunctionaliteit wordt toegevoegd.

Zie [`docs/settings.md`](docs/settings.md) voor de validatiestatus per instelling.

## Installatie via HACS

Voor een officiële release:

1. Publiceer GitHub release `v0.4.0`.
2. Werk **Autarco Local** bij via HACS.
3. Herstart Home Assistant volledig.
4. Open **Instellingen → Apparaten & diensten → Autarco Local**.
5. De read-only instellingen verschijnen in de sectie **Configuratie**.

Aanbevolen verbindingsinstellingen voor het testsysteem:

- Modbus TCP-poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

## Roadmap

Zie [`docs/roadmap.md`](docs/roadmap.md).

## Licentie

MIT
