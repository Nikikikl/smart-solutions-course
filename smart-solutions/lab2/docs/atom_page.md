# AtomS3 lehe Lab 2 laiendus

Lab 2 PlatformIO projektis on nüüd minimaalne `Settings & tests` veebileht,
postkontori klient, rõhuanduri seadete/testi tarkvaraalus ja lokaalse kanali
piir. Labori 1 pildi saatmise, pumba ning täieliku captive-portali lehe
ühendamine on veel TODO; Lab 1 püsivara ei ole tervikuna kopeeritud.

AtomS3 püsivara kohustuslik projektitöövoog on PlatformIO: reprodutseeritav
`platformio.ini`, lähtekoodipuu ja sõltuvused ning build/upload PlatformIO
kaudu. Arduino IDE ei ole selle repo peamine firmware-töövoog. XIAO ESP32S3
Sense püsivara asub eraldi PlatformIO projektis `../firmware-xiao-camera/`.
AtomS3 ja XIAO buildid on tarkvaraliselt kontrollitud. 06.11.2026 laaditi
uude AtomS3R-i NORMAL-püsivara ning kontrolliti kohalikku seadete lehte ja
autenditud HTTP pollingut. 14.11.2026 säilisid Atomi seaded pärast
NORMAL-püsivara laadimist ja kontrolliti avalikku HTTPS-pollingut.
Rõhukalibratsiooni püsivuse ja võrgu taastumise katsed on ootel.
[Atomi LCD-katseraport](display_image_evidence.md) · [Arenduspäevik](../README.md#arenduspäevik).

> Siin eristatakse teostatud tarkvaraalust ja kontrollimata riistvaratööd.
> Allolev rõhuanduri osa on software-only. See ei tõenda päris sensor/op-amp
> ahela, kalibratsiooni, station'i ega MG400 integratsiooni.

## Seaded ja testid Atomi lehel

Kõik allolev on samal Atomi lehel (`/`); eraldi lehte ei ole.

| Plokk | Väli või nupp | Mida teeb |
| :--- | :--- | :--- |
| Postkontor | `Wi-Fi SSID`, `Wi-Fi password` | Wi-Fi võrk, kuhu Atom ühendub |
| Postkontor | `Post-office URL` | serveri aadress |
| Postkontor | `Atom API key` | Atomi võti; lehel ei näidata, tühi väli jätab salvestatud võtme alles |
| Postkontor | `Polling interval (ms)` | küsimisvahe, 250–60 000 ms |
| Postkontor | `Allow HTTP for local development only` | lubab `http://` ainult kohalikuks arenduseks |
| Postkontor | `SAVE SETTINGS` | salvestab ülaltoodu NVS-i |
| Postkontor | `TEST SERVER HEALTH` | teeb ühe `GET /health` kõne ja näitab tulemust, HTTP koodi ja serveri vastust |
| Rõhuandur | `Calibration verified and enabled` | lülitab V ja kPa arvutuse sisse |
| Rõhuandur | `Andur on ühendatud ja juhtmestik kontrollitud` | kohalik kinnitus, ainult RAM-is kuni taaskäivituseni |
| Rõhuandur | `ADC voltage scale (V/count)`, `ADC voltage offset (V)` | ADC koodi teisendus G5 pingeks |
| Rõhuandur | `Pressure scale (kPa/V)`, `Pressure offset (kPa)` | G5 pinge teisendus absoluutrõhuks |
| Rõhuandur | `SAVE PRESSURE SETTINGS` | salvestab neli konstanti NVS-i |
| Rõhuandur | `FILL DA LAB 2 DEFAULTS` | täidab väljad Andmehõive Lab 2 vaikeväärtustega; salvestamiseks vajutada `SAVE PRESSURE SETTINGS` |
| Rõhuandur | `TEST PRESSURE SENSOR` | näitab ühe proovi toorest ADC lugemit, pinget ja kPa kõrvuti |

## Uued postkontori seaded

| Väli | Eesmärk | Salvestamine ja turve |
| :--- | :--- | :--- |
| `Post-office server address` | production HTTPS baasaadress | seadmes; valideerida skeem ja pikkus |
| `Atom authentication key` | Atomi API autentimine | seadmes; UI ei loe olemasolevat võtit tagasi ega logi seda |
| `Polling interval` | tööde küsimise intervall millisekundites | seadmes; tarkvarapiir 250–60 000 ms, lõplik väärtus vajab võrgukatset |
| `Allow local HTTP development` | lubab teadlikult ainult lokaalse `http://` arenduse | production'is väljas; HTTPS vajab päris hosti CA-d |

Serveri aadress ei ole sama mis Labori 1 lokaalse jaama aadress. Atom pollib
dropletit väljamineva HTTPS-ühendusega ja edastab saadud kõrgtaseme töö
Labori 1 lokaalsesse kanalisse.

Salvestusvastus ei tohi sisaldada autentimisvõtit. Tühi võtmeväli tähendab
„jäta olemasolev võti muutmata“, kui serveri aadressi/seadme identiteeti ei
muudeta. Võtme teadlikuks eemaldamiseks peab olema eraldi kinnitatav tegevus.

## Postkontori test

Lehel on nupp `TEST SERVER HEALTH`, mis teeb ühe `GET /health` testpäringu ilma
polli või claim'ita. Firmware lisab seadistatud bearer-päise, kuid praeguse
serveri `/health` endpoint on avalik ega valideeri Atomi võtit. Seega kontrollib
nupp aadressi, TLS-i ja HTTP tervisevastust; Atomi autentimist kontrollivad
poll/result päringud. Round-trip aja ning viimase õnnestunud polli kuvamine on
veel TODO.

Pärast kõnet näitab leht ühel real:

- tulemust (`health_ok`, `health_http_<kood>` või transpordiviga, nt TLS);
- HTTP koodi (`—`, kui serverilt vastust ei tulnud);
- serveri vastust: kuni 200 esimest prinditavat märki vastuse kehast. Praegune
  server vastab `{"ok":true,"service":"lab2-post-office"}`.

Endpoint `/test/post-office` tagastab samad väljad JSON-ina: `result`,
`http_status` ja `server_response`. Atomi võtit ega autoriseerimispäist ei
näidata.

14.11.2026 andis `TEST SERVER HEALTH` avaliku HTTPS-i kaudu `health_ok`.
Autentitud pollingu eraldi kontrollis muutus `poll_http_403` õige võtme
sisestamise järel olekuks `poll_ok_no_job`. Intervall oli `1000 ms` ning
kohaliku HTTP arendusrežiim oli väljas. Avalikul lehel uuenes `last_seen`
ja olek oli `online`. [Katsekanne](../README.md#arenduspäevik).

Testnupp ei loo ega claim'i `letter`/`pick_place` tööd ja ei käivita MG400 rada.

## Rõhuanduri seaded

Andmehõive Lab 2 ühendas Atomi G5 sisendiga MPX5700AP rõhuanduri ja LM358N
astme. Lehel on neli lineaarse teisenduse konstanti. Firmware arvutab samast
raw proovist:

```text
voltage_v = raw_adc × volts_per_count + voltage_offset_v
pressure_kpa = voltage_v × kpa_per_volt + pressure_offset_kpa
```

Vaikeväärtused tulevad Andmehõive Lab 2 mõõteahelast:

| Väli | Ühik | Vaikeväärtus | Arvutus |
| :--- | :--- | :--- | :--- |
| `volts_per_count` | V / ADC kood | `0.00090354` | `3,70 V / 4095` |
| `voltage_offset_v` | V | `0` | — |
| `kpa_per_volt` | kPa / V | `131.24` | `1 / (A · 5,0 V · 0,0012858)` |
| `pressure_offset_kpa` | kPa | `−14.34` | `((A − 1) · Vref / A − 5,0 V · 0,04) / (5,0 V · 0,0012858)` |

Lähteandmed ([Andmehõive repo](https://github.com/Dennel04/data-acquisition-course)):

| Suurus | Väärtus | Allikas |
| :--- | :--- | :--- |
| ADC tegur, 12 bitti, `ADC_11db` | `3,70 V / 4095`; 15.11.2026 G5 multimeetriga `0,865 V`, Atom `0,859 V` | `data-acquisition/lab2/docs/opamp_rebuild_2026-11-14.md`, punkt 7 |
| Astme võimendus `A` | `1 + 10 kΩ / 54 kΩ = 1,185` (`Rref` mõõdetud ~54 kΩ) | sama, punkt 7 |
| Viitepinge `Vref` | `0,69 V`, arvutatud 15.11 multimeetri näitudest (andur `0,837 V`, G5 `0,865 V`) | sama, punkt 7 |
| Anduri ülekandefunktsioon | `Vin = 5,0 V · (0,0012858 · P + 0,04)`, P absoluutrõhk kPa | `data-acquisition/lab1/src/firmware/include/sensor.h` (MPX5700AP andmeleht) |
| Anduri toide | `5 V`, mõõdetud 15.11 | `data-acquisition/lab2/docs/opamp_rebuild_2026-11-14.md`, punkt 7 |

Tulemus on absoluutrõhk. Näiteks G5 `0,865 V` annab `99,2 kPa`. Suhtelise rõhu
jaoks tuleb `pressure_offset_kpa` väärtusest lahutada atmosfäärirõhk.
Konstandid on arvutatud skeemi, mõõdetud tööpunkti ja andmelehe põhjal;
referentsrõhuga kalibratsiooni Andmehõive Lab 2 tulemustes veel ei ole.

Kui `pressure` NVS namespace'is ei ole salvestatud seadeid, kasutab firmware
neid vaikeväärtusi. Pärast `SAVE PRESSURE SETTINGS` kasutatakse salvestatud
väärtusi; salvestatud väljalülitatud olek jääb väljalülitatuks. `GET
/pressure/settings` näitab välja `source` (`saved` või
`data_acquisition_lab2_default`) ja vaikeväärtusi objektis `defaults`.

Nii saab hilisema referentskalibratsiooni koefitsiendid sisestada ilma
püsivara ümber kirjutamata. Kõik neli välja peavad olema lõplikud
arvud ja moodustama piiratud teisendusvahemiku. Nulline skaleerimistegur,
`NaN`, lõpmatus, tekstijääk ning vahemikust väljas teisendus lükatakse tagasi;
vigase sisendi korral jääb eelmine kehtiv NVS seadistus alles.

Kalibratsioon asub eraldi Preferences namespace'is `pressure`. Laadimisel
valideeritakse koefitsiendid uuesti. Puuduv, osaliselt kirjutatud või vigane
NVS konfiguratsioon muutub fail-closed `uncalibrated` olekuks. See tarkvaraline
püsivusmudel on builditud; reboot-püsivus tuleb veel päris Atomil kontrollida.

Normaalrežiimi samal lehel on märkeruut kontrollitud anduriühenduse
kinnitamiseks (`sensor_confirmed=1`; kinnitamata `0`). Kinnitus jääb ainult
RAM-i ja kaob taaskäivitamisel. Puuduv väli vanas kliendis tähendab
kinnitamata ühendust; muu väärtus annab HTTP 400. Kalibratsioonikoefitsiendid
üksi ei kinnita anduri olemasolu. Enne märkimist kontrollib kasutaja wiring'ut
ja G5 lubatud sisendpinget.

## Rõhu test

Nupp `TEST PRESSURE SENSOR` kuvab ühe ja sama proovi kohta korraga:

| Raw ADC | Voltage (V) | Pressure (kPa) |
| :--- | :--- | :--- |
| TODO — real measurement required | TODO — real measurement required | TODO — real measurement required |

Kolm väärtust peavad pärinema samast proovist, et eristada ADC-/ühendusviga
teisendusvalemi või kalibratsiooni veast. Leht ei tohi näidata arvutatud kPa-d
kehtiva kalibratsiooni või kinnitatud anduriühenduse puudumisel.
Normaalrežiimi endpoint keskmistab kaheksa G5 raw ADC lugemit. Kinnitamata
ühendusega tagastab ta `status: sensor_not_confirmed`, `sensor_confirmed:false`,
raw väärtuse ning `null` pinge/kPa, ka varem salvestatud koefitsientidega.
Kinnitatud ühenduse, kuid puuduva kalibratsiooniga jääb olekuks
`not_calibrated`. Kehtiva kalibratsiooni ja kinnitusega arvutatakse pinge ja kPa sama keskmistatud
raw väärtuse põhjal. Vahemikuviga annab error-vastuse, mitte arvulise rõhu.
ADC rail-koodid `0` ja `4095` käsitletakse samuti veana, sest need võivad
tähendada saturatsiooni, lühist või kasutuskõlbmatut tööpunkti.

Test on täielikult kohalik: see ei pöördu dropleti poole, ei polli töid, ei
kutsu station'it ega saa käivitada MG400-t või pumpa. Tarkvara ei saa ujuva
või valesti ühendatud analoogsisendi põhjal kindlalt tuvastada, kas füüsiline
andur on olemas; seetõttu ei tõenda edukas HTTP vastus sensor chain'i korrasolekut.

## Tarkvaraline kontroll enne laborit

- [x] Serveri aadressi skeem ja pikkus valideeritakse.
- [x] Polling-intervalli tüüp ja piirid valideeritakse.
- [x] Võtit ei tagastata seadete GET-vastuses ega logita.
- [x] Testpäring ei polli/claim'i tööd ega kutsu jaama/MG400 täitmisrada.
- [x] Rõhukonstandid salvestatakse ainult täieliku valideerimise järel.
- [x] Puuduv või vigane kalibratsioon ei tekita arvulist kPa tulemust.
- [x] Rõhutest arvutab raw ADC, V ja kPa samast keskmistatud proovist.
- [x] Native-testid katavad kalibreerimata oleku, korrektse teisenduse,
  vigased koefitsiendid, vigase raw ADC ja malformed seadete keeldumise.
- [x] Salvestamata NVS-i korral kasutatakse Andmehõive Lab 2 vaikekonstante;
  need läbivad sama valideerimise.
- [x] `TEST SERVER HEALTH` näitab tulemust, HTTP koodi ja serveri vastust.

## Riistvarakontroll

- [x] Päris Atom pollib avalikku HTTPS-postkontorit oma API võtmega (14.11.2026).
- [x] `TEST SERVER HEALTH` näitab päris Atomil `HTTP 200` ja serveri vastust
  (15.11.2026, telefonist Atomi lehel).
- [x] Kiire polling 1 s on päriselt kasutusel; aeglane 10 s latentsusmõõtmisel
  (vt `docs/latency_poll_*.csv`).
- [x] Kinnitamata anduriga vastab `TEST PRESSURE SENSOR` „sensor not confirmed“
  ja ei näita kPa väärtust (15.11.2026).
- [ ] Anduriga Atomil näidatakse raw ADC, V ja kPa korraga; atmosfääril
  ligikaudu atmosfäärirõhk vaikekonstantidega.

## Labori kontrolliplaan

1. Ühendada Andmehõive Lab 2 päris sensor/op-amp chain ainult kontrollitud
   wiring'u järgi ning kinnitada, et väljund läheb Atomi G5 ADC sisendisse ja
   jääb lubatud pingevahemikku.
2. Salvestada testnupu raw ADC lugemid enne andurikinnitust; pinge ja kPa
   peavad sellel etapil jääma `null`.
3. Mõõta sama tööpunkti op-amp väljundpinge multimeetriga ning võrrelda seda
   raw ADC ja Andmehõive mõõteahelaga.
4. Kontrollida, et väljadel on Andmehõive Lab 2 vaikeväärtused või hilisema
   referentskalibratsiooni `volts_per_count`, `voltage_offset_v`,
   `kpa_per_volt` ja `pressure_offset_kpa`.
5. Kontrollida mitut referentsrõhu punkti kogu kasutatavas vahemikus: raw ADC,
   multimeetri pinge, software voltage ja software kPa dokumenteeritakse sama
   proovi kohta.
6. Võrrelda software kPa tulemust referentsiga ning mitte märkida kriteeriumi
   tehtuks, kuni mõõteviga ja kasutatav vahemik on kinnitatud.
7. Taaskäivitada Atom, avada sama leht ja kontrollida NVS kalibratsiooni
   püsivust ilma koefitsiente uuesti sisestamata. Andurikinnitus peab olema
   lähtestatud: enne uut kohalikku kinnitamist jäävad pinge ja kPa `null`.
8. Korrata `TEST PRESSURE SENSOR` nuppu ning kinnitada, et raw ADC, voltage ja
   kPa kuvatakse koos; ühendus-/vahemikuviga peab olema error, mitte usutav
   võltsrõhk.
