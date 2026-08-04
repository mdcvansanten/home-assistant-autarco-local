# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> Dit is een ontwikkelversie. Er worden geen Modbus-schrijfopdrachten uitgevoerd.

## Versie 0.3.5 — Persistente en compactere diagnostiek

- Verbindingshistorie blijft behouden na een Home Assistant- of integratieherstart.
- Persistent opgeslagen: totale downtime, laatste disconnect/reconnect, disconnectreden, langste verbinding, disconnectaantal en de laatste 50 verbindingsgebeurtenissen.
- Beschikbaarheid wordt berekend over de bewaarde meetperiode in plaats van alleen sinds de laatste herstart.
- Belangrijkste verbindingsdiagnostiek blijft standaard zichtbaar.
- Detailmetingen zoals minimum/maximum/gemiddelde pollduur, TCP-connectduur, retrytellers en health score zijn voor nieuwe installaties standaard uitgeschakeld maar blijven beschikbaar.
- De bestaande persistente Modbus TCP-verbinding en drempel van drie mislukte polls blijven ongewijzigd.

## Installatie via HACS

1. Maak/publish GitHub release `v0.3.5`.
2. Werk **Autarco Local** bij via HACS.
3. Herstart Home Assistant volledig.
4. Open **Instellingen → Apparaten & diensten → Autarco Local**.

Aanbevolen instellingen voor het testsysteem:

- Modbus TCP-poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

> Bestaande installaties behouden de eerdere entity-registrykeuzes. Detaildiagnostiek die al ingeschakeld was kan daarom zichtbaar blijven; die kan handmatig worden uitgeschakeld.

## Roadmap

Zie [`docs/roadmap.md`](docs/roadmap.md).

## Licentie

MIT
