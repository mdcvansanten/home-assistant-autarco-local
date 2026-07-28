# Autarco Local

![Autarco Local](custom_components/autarco_local/brand/logo.png)

Lokale, uitsluitend-lezen Home Assistant-integratie voor Autarco-omvormers
via Modbus TCP.

> [!WARNING]
> Dit is een ontwikkelversie. De registerbetekenissen worden nog onderzocht.
> De integratie bevat geen schrijfcommando's.

## Getest systeem

- Autarco S2.LH10000-MII.1
- Modbus TCP-poort 502
- Device-ID 1
- Inputregisters 33000–33139

## Installatie via HACS

1. Voeg deze repository in HACS toe als aangepaste **Integratie**:
   `https://github.com/mdcvansanten/home-assistant-autarco-local`
2. Download **Autarco Local**.
3. Herstart Home Assistant.
4. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
5. Zoek naar **Autarco Local**.

Gebruik voor het onderzochte systeem:

- IP-adres: `192.168.178.17`
- Poort: `502`
- Device-ID: `1`
- Verversingsinterval: `30` seconden
- Timeout: `5` seconden

## Versie 0.2.0

Deze versie verbetert vooral de betrouwbaarheid en foutdiagnose:

- veilige, uitsluitend-lezen registeropvragen;
- duidelijke logging bij onverwachte fouten;
- automatische reconnect bij iedere poll;
- controle op volledige Modbus-antwoorden;
- herconfigureren vanuit Home Assistant;
- ondersteuning voor meerdere config entries;
- diagnostiek met afgeschermd IP-adres.

## Huidige entiteiten

- Aantal registers
- Ruwe Modbus-registers
- Omvormerklok (voorlopige interpretatie)

## Diagnostiek

Via **Instellingen → Apparaten & diensten → Autarco Local → drie puntjes →
Diagnostiek downloaden** kan een diagnostiekbestand worden gemaakt. Het
IP-adres wordt daarin afgeschermd.

## Licentie

MIT
