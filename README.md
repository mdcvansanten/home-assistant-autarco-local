# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers via Modbus TCP.

> [!WARNING]
> Dit is een vroege ontwikkelversie. De registerbetekenissen worden nog onderzocht.
> De integratie bevat geen schrijfcommando's.

## Getest systeem

- Autarco S2.LH10000-MII.1
- Modbus TCP-poort 502
- Device-ID 1
- Inputregisters 33000–33139

## Installatie via HACS

1. Open **HACS** in Home Assistant.
2. Kies **Integraties**.
3. Open rechtsboven het menu met de drie puntjes.
4. Kies **Aangepaste repositories**.
5. Voeg toe:
   `https://github.com/mdcvansanten/home-assistant-autarco-local`
6. Selecteer categorie **Integratie**.
7. Installeer **Autarco Local**.
8. Herstart Home Assistant.
9. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
10. Zoek naar **Autarco Local**.

Gebruik voor het onderzochte systeem:

- IP-adres: `192.168.178.17`
- Poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden

## Huidige entiteiten

- Verbinding
- Ruwe Modbus-registers
- Omvormerklok (voorlopige interpretatie)

## Handmatige installatie

Kopieer `custom_components/autarco_local` naar:

`/config/custom_components/autarco_local`

Herstart daarna Home Assistant.

## Licentie

MIT


## Diagnostiek

Via het apparaatmenu kan diagnostische informatie worden gedownload. Het IP-adres wordt daarbij afgeschermd.
