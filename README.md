# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> Dit is een ontwikkelversie. Er worden geen Modbus-schrijfopdrachten uitgevoerd.

## Versie 0.3.3 — Stabiliteit en diagnostiek

- Correcte batterijpolariteit:
  - positief = laden;
  - negatief = ontladen.
- Persistente Modbus TCP-verbinding.
- Volledige herbouw van de verbinding na een communicatiefout.
- Retries met oplopende wachttijd.
- Laatst geldige waarden blijven beschikbaar tijdens een korte storing.
- De integratie wordt pas na drie opeenvolgende mislukte polls niet beschikbaar.
- De eerste TCP-verbinding telt niet als reconnect.
- Uitgebreide diagnostiek voor:
  - complete pollduur;
  - Modbus-leestijd;
  - TCP-verbindingsduur;
  - gemiddelde, minimale en maximale pollduur;
  - reconnects, retries en opeenvolgende fouten;
  - laatste succesvolle poll;
  - laatste reconnectreden in het diagnostische downloadbestand.

## Installatie via HACS

1. Upload de inhoud van dit pakket naar de GitHub-repository.
2. Maak release `v0.3.3`.
3. Werk **Autarco Local** bij via HACS.
4. Herstart Home Assistant volledig.
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
