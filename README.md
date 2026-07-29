# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers
via Modbus TCP.

> [!WARNING]
> Dit is een ontwikkelversie. Er worden geen Modbus-schrijfopdrachten
> uitgevoerd.

## Versie 0.3.1 — Stabiliteit

- Correcte batterijpolariteit:
  - positief = laden;
  - negatief = ontladen.
- Configureerbare retries.
- Nieuwe TCP-sessie per poll.
- Logging bij eerste uitval en herstel.
- Diagnostiek voor responstijd, succespercentage, fouten, retries en laatste
  succesvolle meting.

## Installatie via HACS

1. Upload de inhoud van dit pakket naar de repository.
2. Maak release `v0.3.1`.
3. Werk Autarco Local bij in HACS.
4. Herstart Home Assistant.
5. Open **Instellingen → Apparaten & diensten → Autarco Local**.

Aanbevolen instellingen voor het testsysteem:

- IP-adres: `192.168.178.171`
- Poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden
- Nieuwe pogingen: `2`

## Roadmap

Zie [`docs/roadmap.md`](docs/roadmap.md).

## Licentie

MIT
