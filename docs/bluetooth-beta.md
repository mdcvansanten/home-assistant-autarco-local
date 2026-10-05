# Bluetooth beta 0.7.0b1

Deze beta voegt Bluetooth LE toe aan de bestaande Autarco Local-integratie.
De bestaande config entry, entiteit-ID's en het Autarco-dashboard blijven behouden
wanneer dezelfde entry wordt geherconfigureerd van TCP naar BLE.

## Twee functies boven één verbinding

| Onderdeel | Werking | Huidige bewijsstatus |
|---|---|---|
| Gebruikersdata | Modbus 04 via BLE, periodieke runtime-poll | Temperatuurregister 33093 fysiek bevestigd; overige mappings overgenomen uit Autarco Local en opnieuw vergelijken |
| Instellingen | Modbus 03 via dezelfde sessie, eenmaal per minuut en handmatig verversbaar | Transport geïmplementeerd; fysieke vergelijking met Installer UI nodig |
| Installerbediening | Bestaande HA-instellingenlaag en PIN; BLE-writes geblokkeerd | Permanent aangemelde installerrechten en BLE-write/apply/restore zijn niet bewezen |
| EMS | Snapshot met bron, tijdstip, kwaliteit en expliciete validatievlag | Telemetrie kan na vergelijking worden gebruikt; automatische writes zijn niet actief |

De Bluetooth-verbinding blijft open tussen polls. De leesaanvragen dienen ook als
heartbeat; extra willekeurige pings of wachtwoordaanvragen zijn niet nodig.
Dat is een verbindingssessie, geen bewezen installerlogin. De code leest geen
Solis-/Autarco-accountgegevens en verstuurt geen installerwachtwoord.

De omvormer biedt FFE1 voor aanvragen en FFE2 voor notificaties. De fysiek
bevestigde temperatuurtest verstuurt `FE 04 81 45 00 01 1C 2C`. Het apparaat
antwoordde met unit `01` en geldige CRC: 347/348 betekende 34,7/34,8 °C.
De BLE-client accepteert het gekozen antwoordadres en FE, houdt slechts één
RTU-aanvraag tegelijk actief en controleert CRC, functie en antwoordlengte.
Een timeout verbreekt de sessie voordat een nieuwe aanvraag wordt verstuurd.
Dat voorkomt dat een laat leesantwoord bij een ander register wordt ingedeeld.

## Eerst de bestaande virtualenv gebruiken

Pak het pakket uit onder `/config/autarco-ble-test` en gebruik de meegeleverde
`tools/ble_probe.py`. De virtualenv uit de eerdere temperatuurtest is voldoende:

```bash
/config/solis-ble-venv/bin/python /config/autarco-ble-test/tools/ble_probe.py --address AA:BB:CC:DD:EE:FF --polls 5 --output /config/autarco-ble-probe.json
```

Vervang het voorbeeldadres door het adres uit de HA Bluetooth-monitor. De lokale
Solis-app moet losgekoppeld zijn. Een eventueel al actief BLE-transport in HA
moet gepauzeerd zijn. Deze proef houdt één verbinding open en leest temperatuur,
de bestaande runtime-registers en de bekende instellingen. Alle resultaten
zijn ruwe registers met tijdstippen. Een transporttimeout beëindigt de proef;
een expliciet niet-ondersteund register wordt herkenbaar vermeld.

## Installeren in Home Assistant

### Vanuit de GitHub-branch via de terminal

Plak dit in de **Terminal & SSH**-add-on van Home Assistant OS:

```bash
(
  set -e
  autarco_script="$(mktemp /tmp/autarco-ble-deploy.XXXXXX)"
  trap 'rm -f -- "$autarco_script"' EXIT
  curl -fSL --connect-timeout 15 --max-time 60 \
    https://raw.githubusercontent.com/mdcvansanten/home-assistant-autarco-local/codex/ble-transport-20261005/tools/deploy_ble_from_github.sh \
    -o "$autarco_script"
  bash "$autarco_script"
)
```

Het script haalt `codex/ble-transport-20261005` op, valideert het archief en versie
`0.7.0b1`, bewaart de bestaande component in `/config/backups`, vervangt de
component, voert `ha core check` uit en vraagt daarna een HA-herstart aan.
Als de configuratiecontrole faalt, herstelt het de oorspronkelijke component
en vraagt het geen herstart aan. Download en tijdelijke uitpakmappen worden ook
bij fouten opgeruimd. Configuratie, secrets, automations en inverterinstellingen
worden niet aangepast.

Wil je de herstart zelf uitvoeren, gebruik dan `bash "$autarco_script" --no-restart`
in het bovenstaande blok en controleer/herstart HA daarna handmatig.

### Met het losse installatiepakket

1. Plaats de ZIP en `install_ble_beta.sh` in `/config`.
2. Voer `bash /config/install_ble_beta.sh /config/autarco-local-ble-0.7.0b1.zip` uit.
3. De installer controleert de pakketinhoud, bewaart de vorige component onder
   `/config/backups/autarco_ble_<tijdstip>_<id>/autarco_local`, vervangt uitsluitend
   de component en ruimt de tijdelijke uitpakmap op. De ZIP blijft bewaard.
4. Controleer HA-configuratie en herstart Home Assistant. De integratie haalt de
   benodigde dependencies zelf op; de testvirtualenv is geen HA-dependency.
5. Open **Instellingen → Apparaten & diensten → Autarco Local → ⋮ → Herconfigureren**.
   Kies **Bluetooth LE (beta)**, het Bluetooth-adres, Device ID **1**, timeout
   **5 s**, interval **15 s**, retries **1**. Bij BLE worden IP en poort genegeerd.
   Behoud bij een bestaande entry wel het huidige IP/poort in de ingevulde velden,
   zodat terugschakelen naar TCP eenvoudig blijft.
6. De herconfiguratie leest alleen de temperatuur. Na het opslaan worden de
   permanente runtime- en settings-polls gestart. Open **Autarco Local** en
   herlaad de pagina volledig zodat de nieuwe dashboardmodule wordt geladen.

Voer na de GitHub-deploy dezelfde herconfiguratie uit (stappen 5 en 6 hierboven).

Laat **EMS-meetwaarden en tekens onafhankelijk gecontroleerd** in Configureren
aanvankelijk uit. Het is geen toestemmingsknop voor inverterwrites.
HACS kan de handmatig geïnstalleerde beta later vervangen door een gewone
release; kies tijdens de proef bewust welke versie je wilt draaien.

## Het dashboard

Het dashboard toont bron, meetleeftijd, verbindingsstatus en instellingenstatus.
**Vrijgeven voor Solis-app** sluit de HA-verbinding en pauzeert nieuwe aanvragen.
Na lokale telefoonbediening: verbreek de Solis-appverbinding en klik
**Bluetooth hervatten**. De pauze wordt na HA-herstart niet onthouden.
Datakwaliteit en de pauzeknop zijn ook beschikbaar als gewone HA-entiteiten.

Een ontbrekend register of een mislukte poll wordt niet als 0 W ingevuld.
Een werkelijk ontvangen registerwaarde 0 blijft 0. Bij een mislukte poll blijft
de vorige ruwe snapshot alleen voor diagnose bewaard; de runtime-sensoren worden
direct onbeschikbaar en het dashboard vermeldt **Verouderd**.
Een instellingenfout maakt de runtime-poll niet onbeschikbaar.

**Transportbetrouwbaarheid bevestigt geen registerbetekenis.** De bestaande
batterijspannings-/stroommapping was in de v0.6.6-UI al als onbevestigd aangemerkt.
Deze beta verandert geen tekenconventies of schalen zonder fysieke vergelijking.
De omvormer rapporteert een batterijcluster; onafhankelijke voltages per toren
of module blijven uit de Dyness-/CAN-bron komen.

## Proef op de echte installatie

Controleer eerst vijf opeenvolgende snapshots, daarna minstens een uur in HA:

| Controle | Vergelijking of verwachte uitkomst |
|---|---|
| Temperatuur | BLE en Solis lokaal vrijwel gelijk op hetzelfde meetmoment |
| PV / huis / net | Onder verschillende belastingen naast P1 en Solis leggen; beide tekens voor netvermogen controleren |
| Batterij-SOC / vermogen | Naast Dyness/CAN en Solis vergelijken, tijdens laden, ontladen en rust |
| Instellingen | Minimum-SOC, reserve, netladen, modi, stromen en tijden met Installer UI vergelijken |
| Nulmetingen | Ruw register, timestamp, datakwaliteit en onafhankelijke bron naast elkaar bewaren |
| Pauze en herstel | Solis-app kan na vrijgeven verbinden; na loskoppelen/hervatten komen verse HA-metingen terug |
| Herstart HA | Session opnieuw opgebouwd, bestaande entiteiten beschikbaar, geen blijvende foutieve 0 W |
| Instellingenfout | Runtime blijft werken; de settings-laag toont een eigen fout/status |

De bekende minimum-SOC van 20% en de bestaande inverter-/BMS-grenzen veranderen
niet. De eerste writeproef moet afzonderlijk worden gekozen nadat bovenstaande
gegevens en het daadwerkelijke write/apply-protocol zijn bevestigd.

## EMS-interface

Gebruik de service `autarco_local.get_snapshot` met response-data:

```yaml
action: autarco_local.get_snapshot
data: {}
response_variable: inverter_snapshot
```

Bij meerdere entries geef je `config_entry_id` op. De response bevat
`transport`, `quality`, `sampled_at`, `age_seconds`, `sample_span_ms`, `values`,
`mapping_validated`, `ems_data_ready` en `ems_control_ready`.
Verouderde of ontbrekende waarden zijn `null`, nooit een opgevulde nul.
Het zijn sequentiële registerreads, geen fysiek atomaire energiebalans.

`ems_data_ready` wordt alleen waar bij handmatig bevestigde mapping, complete
en actuele meetwaarden, een verbinding, minstens vijf succesvolle polls en
een runtime-readduur van maximaal 10 seconden. `ems_control_ready` blijft false.
De machinebesturing krijgt later een afzonderlijke, beperkte allowlist van
gevalideerde setpoints, pre-read, read-back, audit en conflict-/herstelafhandeling.
Een permanent open BLE-sessie geeft het EMS geen installerrechten.

## Terug naar TCP

Herconfigureer dezelfde entry terug naar **Modbus TCP**, met het oorspronkelijke
logger-IP, poort en Device ID. Daardoor blijven entiteit-ID's behouden.
Als je ook de vorige componentcode wilt terugzetten, gebruik dan de bewaarde
componentmap nadat HA is gestopt en herstart daarna HA. Verwijder de HA-config
entry niet: daarin zitten de bestaande entiteitregistraties en opties.

## Softwarevalidatie en grenzen

Tests gebruiken de echte vastgelegde temperatuurframes en gesimuleerde BLE-I/O.
Ze controleren fragmentatie, samengevoegde frames, CRC, verkeerde unit/functie/
lengte, timeout/herstel, oude notificaties, geserialiseerde aanvragen, stale data,
echte nulwaarden en de scheiding tussen instellingen en runtime.
Imports en tests draaien tegen Home Assistant 2026.8.1 en Python 3.14.
Dit is geen fysieke duurtest van de nieuwe integratie op de omvormer.

Bronnen voor het ontwerp:

- [HA Bluetooth API](https://developers.home-assistant.io/docs/core/bluetooth/api/)
- [Bleak retry connector](https://bleak-retry-connector.readthedocs.io/en/latest/usage.html)
- [Solis BLE proof of concept](https://github.com/cryptocake/btle-solis)
- Bestaande Autarco Local-registercatalogus en de eerder vastgelegde lokale temperatuurtest.
