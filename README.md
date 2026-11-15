# Nutikad Lahendused / Smart Solutions

Kursusel ühendame ekraaniga mikrokontrolleri **AtomS3R**, kohaliku arvuti ehk **jaama** ja **Dobot MG400** roboti. Esimeses laboris valisime tähe Atomi nupuga. Jaama Pythoni programm teisendas tähe liikumisteeks ja MG400 joonistas selle 3D-prinditud pastakahoidikuga paberile. Teises laboris lisasime **avaliku HTTPS-postkontori**. See on Flaski veebiteenus, kuhu kasutaja jätab lubatud töö ja kust Atom saab tööd küsida ning tulemuse tagastada.

## Kontrollitud tulemused

### Labor 1 · täht Atomi nupult paberile

03.10.2026 joonistas MG400 päris katses meeskonna initsiaalid **D, N ja R**. Pärast lehe ümberkalibreerimist mõõtis Denys tähekõrguseks **20 mm**. Android-telefon avas Atomi Wi-Fi avalehe automaatselt ning telefonist saadetud 128 × 128 pilt ilmus Atomi ekraanile. [Joonistuse mõõtmised](smart-solutions/lab1/docs/letters.md) · [Jaama sündmuslogi](smart-solutions/lab1/data/letter_events.csv) · [Androidi katse](smart-solutions/lab1/docs/atom_page.md).

[![Video eelvaade: Atomi nupult valitud täht jõuab MG400-ni](smart-solutions/lab1/docs/videos/atom-letter-robot-draws.jpg)](smart-solutions/lab1/docs/videos/atom-letter-robot-draws.mp4)

[Video (19 s)](smart-solutions/lab1/docs/videos/atom-letter-robot-draws.mp4) · [Robot ja pastakahoidik](smart-solutions/lab1/docs/images/robot-drawing-letters.jpg) · [Tähed joonlaua kõrval](smart-solutions/lab1/docs/images/robot-drawing-letters-ruler.jpg) · [Lähivaade](smart-solutions/lab1/docs/images/robot-drawing-letters-closeup.jpg).

### Labor 2 · avalik postkontor, Atom, robot ja kaamerad

| Katse | Tulemus ja tõend |
| --- | --- |
| Avalik postkontor, 20.10.2026 | Nikita Teterev kontrollis HTTPS-i (`/health` vastas HTTP 200) ja sisselogimist telefoni 5G ühenduse kaudu. Töö `letter A` aegus ootejärjekorras. SQLite'i kirje säilis teenuse taaskäivitamisel ning Nikita taastas selle varukoopiast eraldi testbaasi. [Paigaldus ja kontrollid](smart-solutions/lab2/deploy/README.md). |
| Atomi BENCH ja HEALTH_ONLY, 23.10.2026 | Asendus-AtomS3R-i BENCH-katses töötas LCD ja avanes kirjutuskaitstud seadistusleht. HEALTH_ONLY katses õnnestusid Wi-Fi ja TLS, kuid päring lõppes teatega `HEALTH ERROR`. Autenditud avaliku pollingu tõend lisandus 15.11. [Katsekanded](smart-solutions/lab2/README.md) · [Püsivara režiimid](smart-solutions/lab2/firmware/README.md). |
| Atomi LCD, 06.11.2026 | Kasutaja kinnitas ühel füüsilisel AtomS3R-il L2-pildi ja rohelise linnukese. Atom küsis töid kohalikult HTTP-testserverilt ja mõlemad sama tüüpi `display_image` tööd lõppesid olekuga `done / local_display`. [Katseraport](smart-solutions/lab2/docs/display_image_evidence.md) · [L2-pildi foto](smart-solutions/lab2/docs/evidence/atoms3r-lab2-logo-2026-11-06.jpg) · [Linnukese foto](smart-solutions/lab2/docs/evidence/atoms3r-lab2-check-2026-11-06.jpg). |
| Atomi võrk ja serveri ligipääs, 13.11.2026 | Atomi `/state` ja `/settings` vastasid telefoni pääsupunkti võrgus. Kohalik testpostkontor sel ajal ei töötanud. Raimo kinnitas oma kontoga SSH-sisselogimist avalikku serverisse. [Arenduspäevik](smart-solutions/lab2/README.md). |
| Avalik tervikahel, 15.11.2026 | MG400 joonistas avalikust postkontorist saadetud `letter A` ning mõlemad `display_image` tööd said tulemuse `done / local_display`. Kolm lubamatut tööd lükati tagasi, aegunud `letter B` robotit ei liigutanud. Atomit näidati viimase päringu järel umbes 10 s pärast `stale` ja 30 s pärast `offline`. Wi-Fi taastudes jõudis kolme lõpetatud tähetöö tulemus serverisse. [15.11 tõendid](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md#praegune-seis-15112026). |
| Kaamerad, viide ja serverikoopia, 15.11.2026 | Jaama lehel töötasid nii Verbatim USB lauakaamera kui ka USB kaudu ühendatud XIAO tööriistakaamera. Postkontori 30 + 30 katse keskmine viide oli 1 s küsimisvahega 4,6 s ja 10 s vahega 6,7 s. Jaama juhtimisviide kahe kaameraga oli 247 ms. Eraldi postkontorikoopia ehitati samal dropletil juhendi järgi uuesti ja kontrolliti 1 min 33 s jooksul. [Mõõtmised](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md#3-kaamerad-ja-atomi-leht) · [Taastamiskatse](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/deploy/README.md#uuesti-ehitamise-märkused-15112026). |

Lab 2 päevik eristab varasemat musta ekraaniga AtomS3R-i ja asendus-AtomS3R-i. LCD-katse raport kirjeldab ühe seadmega tehtud katset. Seadmete praegune püsivara vajab kohapeal kontrollimist. [Varasema seadme diagnostika](smart-solutions/lab2/docs/atom_display_diagnostic.md).

## Laborid 1–4

| Labor ja eesmärk | Füüsiline või väliskeskkonnas kontrollitud tulemus | Tarkvara ja dokumentatsioon | Lahtine töö |
| --- | --- | --- | --- |
| [1 · Kohalik joonistusjaam](smart-solutions/lab1/README.md) | Atomi nupult valitud täht jõudis USB kaudu jaama ja MG400 joonistas selle. Demo on lõpetatud, esitamise tag on `smart-solutions-lab1`. | Täheplaanid, kalibratsiooni kontroll ja jaama kuivkäivitus. | Hilisema füüsilise `source → finished` katse lõppkoordinaadid puuduvad repost. `positions.json` ja `pick_test.csv` pärinevad varasemast ühe punkti tõstekatsest. |
| [2 · Internetipostkontor ja kaks kaamerat](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md) | Avalik HTTPS-ahel MG400 ja Atomi LCD-ni, whitelist, aegumine, ühenduse taastumine, mõlemad kaamerad, viitemõõtmised ja postkontorikoopia. | Flaski järjekord, püsivara ja adapter. Tarkvaraline tervikahel `letter` ja `pick_place` näidistäituritega. | Ülejäänud liikmete ohutuskinnitused ja anduriga ühendatud Lab 2 Atomi rõhunäit. Päris `pick_place` täitja on ootel. |
| [3 · Privaatne VPN, klapp ja UV](smart-solutions/lab3/README.md) | Riistvara- ja VPN-katsed on ootel. | WireGuardi plaan ja võrguühenduseta logianalüüs. Klapi, UV ja alarmi olekumudel ning sündmuste simulatsioon asuvad Lab 2 püsivaraprojektis. | Marsruudid, 48 tunni päris seire ja ühenduse katkemise ohutu käitumine. Klapi ja UV füüsiline juhtimine ning sõltumatu väljalülituse kontroll. |
| [4 · Ühine andmebaas ja töövoo salvestaja](smart-solutions/lab4/README.md) | Lab 4 päriskatsed on ootel. | Koostatud on dokumentatsiooni kavand ja 15 punkti tõendiplaan. | Ühine kirjelepe, rakendus, 500 kirje loendus, katkestused ning jaama vastuvõtukatsed. |

## Süsteemi arhitektuur

```text
Lab 1  Atomi nupp → USB-jadaühendus → jaam → Ethernet → MG400
Lab 2  brauser → avalik HTTPS-postkontor ← Atomi väljaminev HTTPS-polling
       Atom → USB-jadaühendus → kohalik jaam → Ethernet → MG400
       lauakaamera → USB → jaam
       XIAO tööriistakaamera → USB-jadaühendus → jaam (15.11 katse)
Lab 3  telefon ↔ privaatne WireGuard dropleti kaudu ↔ laborivõrk (plaan)
Lab 4  jaama püsipuhver → privaatne WireGuard → MQTT ja failid → ühine SQLite (kavand)
       töövoo salvestaja → operaatorilukk → ühine MG400 lüüs (kavand)
```

Lab 2 tervikahelas küsib Atom postkontorilt korrapäraselt uusi töid (polling) ja saadab tulemuse tagasi. `display_image` kuvab pildi Atomi ekraanil. `letter` liigub jaama kaudu robotile. Avalik postkontor hoiab tööjärjekorda. Lab 2 roboti liikumiskäsud ja kaameravood jäävad kohalikku võrku. Lab 3 WireGuardi plaan lisab volitatud seadmele eraldi ligipääsutee jaamale ja kaameratele. [Lab 1 katseskeem](smart-solutions/lab1/docs/system_03.10.26.svg) ([draw.io](smart-solutions/lab1/docs/system_03.10.26.drawio)) · [Lab 2 skeem](smart-solutions/lab2/docs/system.svg) ([draw.io](smart-solutions/lab2/docs/system.drawio)) · [WireGuardi plaan](smart-solutions/lab3/docs/wireguard/README.md).

Lab 4 kavand lisab privaatsele teele MQTT-põhise salvestuse ja lugemiseks mõeldud MCP liidese. Töövoo salvestaja kasutab olemasolevat jaama ja kavandatud ühist MG400 lüüsi. [Lab 4 arhitektuur](smart-solutions/lab4/docs/architecture.md).

## Kaustad

| Asukoht | Sisu |
| --- | --- |
| [Lab 1 `src/`](smart-solutions/lab1/src/) ja [`firmware/`](smart-solutions/lab1/firmware/) | Pythoni joonistusjaam, USB-sild ja MG400 klient. Atomi PlatformIO projektis on tähevalik, Wi-Fi avaleht, pildikuva ja pumba telemeetria. |
| [Lab 2 `server/`](smart-solutions/lab2/server/) ja [`deploy/`](smart-solutions/lab2/deploy/) | Flaski API ja veebileht, SQLite'i tööjärjekord ning Caddy, Gunicorni ja systemd paigaldusjuhised. |
| [Lab 2 `firmware/`](smart-solutions/lab2/firmware/) ja [`src/`](smart-solutions/lab2/src/) | Atomi polling, LCD ja USB-sild. Jaama adapter võtab USB kaudu töid vastu. Samas `src/` kaustas on näidistäiturid, kaameraserver ja [kaameraallikad](smart-solutions/lab2/src/cameras/). |
| [Lab 2 `firmware-xiao-camera/`](smart-solutions/lab2/firmware-xiao-camera/) | XIAO ESP32S3 Sense tööriistakaamera PlatformIO projekt. |
| [Lab 3 `docs/`](smart-solutions/lab3/docs/), [`data/`](smart-solutions/lab3/data/) ja [`tools/`](smart-solutions/lab3/tools/) | Võrgu- ja mõõteplaan, päiseridadega CSV-mallid ning tunneli logija ja analüüs. |
| [Lab 4 `docs/`](smart-solutions/lab4/docs/architecture.md) ja [`workflows/`](smart-solutions/lab4/workflows/README.md) | Ühine kirje, salvestustee, puhver, töövoo failikuju, operaatorilukk ja MCP lugemisliides. |
| Testid [Lab 1](smart-solutions/lab1/tests/), [Lab 2](smart-solutions/lab2/tests/) ja [Lab 3](smart-solutions/lab3/tests/) | Pythoni testid. Püsivara C++ testid asuvad Lab 2 [Atomi](smart-solutions/lab2/firmware/test/) ja [XIAO](smart-solutions/lab2/firmware-xiao-camera/test/) projektides. |

## Kiirstart ilma riistvarata

Ava terminal repo juurkaustas. Näited on macOS-i ja Linuxi jaoks ning kasutavad Python 3.11 või uuemat. Sõltuvused paigaldatakse ajutisse kausta. Pärast paigaldust töötavad näited ilma Atomi, MG400, kaamerate, päris võtmete ja tootmisserverita.

```sh
demo_dir=$(mktemp -d)
python3 -m venv "$demo_dir/venv"
"$demo_dir/venv/bin/python" -m pip install \
  -r smart-solutions/lab1/src/requirements.txt \
  -r smart-solutions/lab2/server/requirements.txt
```

Käivita samas terminalis. Iga `cd` sulgudes kehtib ainult selle näite käivituse ajal.

```sh
"$demo_dir/venv/bin/python" -B -m unittest discover -s smart-solutions/lab1/tests -p test_station_dry_run.py
(cd smart-solutions/lab2 && "$demo_dir/venv/bin/python" -B -m src.e2e_demo)
(cd smart-solutions/lab3 && "$demo_dir/venv/bin/python" -B -m unittest discover -s tests)
```

Lab 1 test näitab tähe liikumisplaani ja `accepted_dry_run` sündmust. Lab 2 näide loob ajutised SQLite'i andmebaasid ja tagastab mõlemale näidistööle `server_status: done` koos `hardware_used: false`. Lab 3 testid kasutavad sünteetilisi logiridu ja asendatud käsuvastuseid.

## Kaitsmisel

1. **Lab 1.** Näita videost nupuvajutust ja MG400 joonistust. Ava joonlauaga foto ning seo tulemus jaama sündmuslogi ja USB/Etherneti skeemiga.
2. **Lab 2.** Näita avaliku ahela tegelikke tõendeid, LCD-fotosid, mõlemat kaamerat ja Wi-Fi katkestuskatset. Kohalik näidis sobib tööjärjekorra selgitamiseks. [15.11 tõendid](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md#praegune-seis-15112026) · [Tähekatse juhend](smart-solutions/lab2/docs/live_letter_runbook.md) · [Kaameraplaan](smart-solutions/lab2/docs/cameras.md).
3. **Lab 3.** Näita WireGuardi plaanil telefoni ja laborivõrgu teed. Selgita, mida sünteetiliste andmetega testiti ja millised mõõtmised tuleb laboris koguda. [Mõõteplaan](smart-solutions/lab3/docs/measurements.md) · [Klapi ja UV plaan](smart-solutions/lab3/docs/atom_page.md).
4. **Lab 4.** Kasuta [kontrollnimekirja ja kaitsmisplaani](smart-solutions/lab4/README.md), et siduda ühine kirje, katkestuste loendus, töövoog, kahe brauseri lukk ja MCP vastuvõtutõenditega.

## Seotud kursuseprojektid

- MG400 pastakahoidik, tööriistad ja kaamera mehaanika. [3D printimine ja CAD](https://github.com/Dennel04/3d-printing-course).
- Rõhuandur, pumba juhtimine ja mõõteandmete analüüs. [Andmehõive (Data Acquisition)](https://github.com/Dennel04/data-acquisition-course).

## Ohutus ja piirangud

- Päris MG400-ga tööta laboris kohaliku vastutajaga. Hoia tööala vaba ja füüsiline hädastopp käeulatuses. Korraga saadab liikumiskäske üks programm. Veebinupp ja võrguühenduse katkestamine ei asenda hädastoppi. [Lab 2 ohutus](smart-solutions/lab2/docs/safety.md) · [Lab 3 ohutus](smart-solutions/lab3/docs/safety.md).
- Avaliku serveri kaudu käivitatud `letter A` jõudis 15.11 päris MG400-ni. Lab 2 `pick_place` piirdub näidistäituri, simulatsiooni ja eelkontrolliga. Kursuste ühise juhtimisõiguse mudel on tarkvaraprototüüp. Päris töövoog vajab ühist käskude lüüsi. [Pick-and-place’i piirid](smart-solutions/lab2/docs/pick_place_executor.md) · [Juhtimisõiguse prototüüp](smart-solutions/lab2/docs/ownership_gateway.md) · [Lab 4 operaatorilukk](smart-solutions/lab4/docs/operator_lock.md).
- Varasem XIAO USB kaudu loetud JPEG pärineb diagnostikakatsest. 15.11 kasutas jaam kaht päris kaamerat, XIAO voog tuli USB kaudu. Lab 3 VPN-i kaameramõõtmised ja Lab 4 MQTT andmekatkestused on ootel. [Lab 2 kaameramõõtmised](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md#3-kaamerad-ja-atomi-leht) · [Lab 4 puhvri katseplaan](smart-solutions/lab4/docs/buffering.md).
- VPN-i kaugliikumise eeldused on kogu lauda näitav kaamera, kohalik vastutaja ning rakendatud ja kohapeal kontrollitud katkestuskäitumine. UV on ette nähtud ainult kohalikuks kasutuseks läbipaistmatu katte all. Klapi ja UV tarkvaramudelid ootavad väljundite füüsilist kontrolli. [Lab 3 ohutus](smart-solutions/lab3/docs/safety.md).

## Venekeelsed tõlked

Mitteametlikud ülesannete tõlked ja õppemärkmed on kaustas [`study-ru/`](study-ru/README.md).

## English summary

Smart Solutions connects an AtomS3R, a local Python station and a Dobot MG400. Lab 1 demonstrated letter drawing. Lab 2 demonstrated the public HTTPS job chain to the robot, two LCD jobs and two local cameras. The physical Lab 2 `pick_place` executor remains unverified. Lab 3 has a WireGuard plan, offline monitoring tests and actuator models. Lab 4 documents the proposed shared cycle record, upload path and station workflow.
