# Nutikad Lahendused: Labor 2 — internetipostkontor ja kaks kaamerat

**Töömaht:** 28 tundi | **Hindamine:** 20 punkti | **Meeskond:** 3 tudengit

**Välja antud:** 07.10.26 | **Tellimise kuupäev:** 16.10.26 | **Esimene kaitsmine:** 29.10.26, veebis

[Õppejõu ülesanne ja hindamiskriteeriumid](https://github.com/KKallas/Narva-subjects/blob/main/EST/2026-27/Smart%20Solutions/Smart%20Solutions%20%5BLab%202%5D%20EST.md).

[Praegune seis](#praegune-seis-15112026) · [Arhitektuur](#süsteemi-arhitektuur) ·
[1. Droplet](#1-droplet) · [2. Postkontor](#2-postkontor) ·
[3. Kaamerad ja Atomi leht](#3-kaamerad-ja-atomi-leht) ·
[Kontrollnimekiri](#kontrollnimekiri) · [Tööfailid](#tööfailid) ·
[Arenduspäevik](#arenduspäevik).

## Ülevaade

Laboris 1 valiti täht Atomi nupuga ja kohalik jaam edastas töö Dobot
MG400-le. Labor 2 lisab **avaliku HTTPS-postkontori**: kasutaja jätab sinna
lubatud töö ja näeb hiljem tulemust. **AtomS3R** küsib ise korrapäraselt uusi
töid (polling) ja annab töö USB kaudu **jaamale** (laboriarvuti), mis juhib
robotit ja näitab kohalikke kaamerapilte. Töö kehtib kuni kehtivusaja (TTL)
lõpuni.

| Töö | Mida kasutaja tellib | Seis |
| --- | --- | --- |
| `letter` | Ühe tähe A–Z joonistamine Labori 1 jaama kaudu. | 15.11.26: avalik postkontor → Atom → USB → jaam → MG400, täht A paberil, olek `done`. |
| `display_image` | Püsivarasse ehitatud pilt Atomi LCD-l: `lab2_logo` või `lab2_check`. | 15.11.26 avaliku postkontori kaudu mõlemad `done / local_display`. [LCD-raport](docs/display_image_evidence.md). |
| `pick_place` | Eelmääratud tööjada `source_to_finished`. | Ainult tarkvaraliselt (näidistäitur); päris robotiga ei kasutata. [Täitja piirid](docs/pick_place_executor.md). |

<a name="praegune-seis-13112026"></a>
<a name="praegune-seis-14112026"></a>

## Praegune seis (15.11.2026)

- **Avalik postkontor.** `https://narva2.roboarena.org` uuendati
  15.11 commit'ile `ea423b6` (`deploy/update.sh`); `deploy/verify.sh` kõik
  PASS. Kasutajaleht on HTTP Basic parooli taga, paroolid on repost väljas.
- **Tööd avalikus ahelas.** `letter A` joonistati MG400-ga paberile
  (`done`). `display_image` `lab2_logo` ja `lab2_check`: mõlemad
  `done / local_display`.
- **Lubamatu ja aegunud töö.** Kolm lubamatut tööd said HTTP 400, robot ei
  liikunud. Aegunud `letter B` ei pannud robotit liikuma, kui Atom tagasi tuli.
- **Atom on vait.** Leht näitab `stale` ~10 s ja `offline` ~30 s pärast
  viimast postil käiku.
- **Ühendus katkes keset tööd (3 korda).** Robot joonistas tähe lõpuni ja
  vastus jõudis serverisse pärast Wi-Fi taastumist.
- **Kaamerad.** Mõlemad pildid on jaama kohalikul kaameralehel; lauakaamera
  näeb kogu lauda ja robotit, tööriistakaamera pliiatsi otsa ja tähti.
- **Lahti.** Latentsus 2 × 30 sõnumit (käib), mõlema kaamera mõõdikud koos
  XIAO-ga ja juhtimislatentsus kahe kaameraga, rõhuanduri seaded ja test
  Atomi lehel, telefoni ekraanipilt WiFi väljas, teiste liikmete
  ohutuskinnitused, tag `smart-solutions-lab2`.

## Süsteemi arhitektuur

```text
Brauser (telefon) → HTTPS → avalik postkontor ← väljaminev HTTPS-polling ← AtomS3R
AtomS3R → sisseehitatud pilt → LCD
AtomS3R → USB serial → jaama adapter → Labori 1 jaam → Ethernet → MG400
Verbatim lauakaamera → USB (OpenCV) → jaama kaameraleht
XIAO tööriistakaamera → USB serial → jaama kaameraleht
```

- **Avalik pool.** Caddy teenindab HTTPS-i, Gunicorn/Flask kuulab ainult
  `127.0.0.1:5001`, SQLite hoiab järjekorda, tulemusi ja Atomi `last_seen`
  aega. Postkontor ei loo kunagi ühendust Atomi, jaama ega robotiga; Atom
  tuleb ise. [Paigaldus](deploy/README.md) · [API](docs/server_api.md).
- **Kohalik pool.** Pilditöö lõpetab Atom oma LCD-l. Robotitöö läheb USB
  kaudu jaama adapterisse ja Labori 1 jaama, mis ainsana saadab MG400-le
  käske. Atom ootab jaamalt kviitungit `station_ack` (kordus iga 1,5 s kuni
  8 korda) ja tulemust 300 s jooksul; muidu vastus `station_no_ack` /
  `station_result_timeout`. [Adapter](src/station_adapter.py).
- **Kaamerad.** Kaameraleht (`src/camera_server.py`) kuulab ainult
  `127.0.0.1:5002`; kaamerapilte postkontorisse ei saadeta.
  [Kaamerad](docs/cameras.md).

![Lab 2 süsteemiarhitektuur](docs/system.svg)

[Muudetav draw.io skeem](docs/system.drawio).

## Vastused (Kirjuta üles)

### 1. Droplet

| Küsimus | Vastus |
| :--- | :--- |
| Dropleti aadress ja link | `narva2.roboarena.org`, [https://narva2.roboarena.org](https://narva2.roboarena.org) |
| Kelle võtmed on sees ja millal | Nikita 16.10.26; Raimo 13.11.26 (konto `raimo`, ilma sudo-ta); Denys jaamaarvutist 14.11.26 (konto `denys`); 15.11.26 on iga liikme võti tema oma arvutist dropletis. Privaatvõtmed jäävad arvutitesse. |
| Lahti olevad pordid | UFW `active`, default `deny incoming`: TCP 22 — SSH; TCP 80 ja 443 — Caddy (HTTPS). Gunicorn ainult `127.0.0.1:5001` (20.10.26). |
| Kuidas sisse saab | `ssh <kasutaja>@narva2.roboarena.org` oma võtmega; `passwordauthentication no`, `kbdinteractiveauthentication no` (20.10.26). |
| Uuesti ehitamine | Ei ole veel tehtud. Juhend: [taastamine puhtale dropletile](deploy/README.md#taastamine-puhtale-dropletile). |

Paigaldus ja uuendus: `deploy/install.sh`, `deploy/update.sh`, kontroll
`deploy/verify.sh` (20.10.26: 12 PASS, 0 FAIL; 15.11.26 pärast uuendust
commit'ile `ea423b6`: kõik PASS). [Paigaldusjuhend](deploy/README.md).

### 2. Postkontor

**Lehe aadress:** [https://narva2.roboarena.org](https://narva2.roboarena.org)
(HTTP Basic parool; paroolid ja Atomi võti on repost väljas).
**Kes mida saadab:** [`docs/server_api.md`](docs/server_api.md).

**Lubatud tööd** ([whitelist](docs/server_api.md#whitelist)):

| `job` | Lubatud argument |
| :--- | :--- |
| `letter` | üks suurtäht `A`–`Z` |
| `display_image` | `lab2_logo` või `lab2_check` |
| `pick_place` | ainult `source_to_finished` (päris robotiga ei kasutata) |

Muu töö, lisaväli või vale väärtus saab HTTP 400 koos põhjusega ega lähe
järjekorda. 15.11.26 proovitud: `move` koordinaatidega → `unknown_job`,
`letter` lisaväljaga `x` → `unexpected_field`, täht „Ж“ → `invalid_letter`;
järjekorda ei läinud midagi, robot ei liikunud.

**Aegumine.** Igal tööl on TTL (serveri vaikeväärtus 60 s, kõige rohkem
3600 s). Aegunud töö saab oleku `expired / ttl_expired` ja Atomile seda ei
anta. 15.11.26: `letter B` TTL-iga 15 s jäeti, kui Atom oli vooluta; töö
aegus ja Atomi sisselülitamisel robot ei liikunud. (Ka 20.10.26: `letter A`
aegus päris serveris.)

**Telefon WiFi väljas.** Ekraanipilt: TODO. 20.10.26 avati leht ja logiti
sisse Chrome'iga telefonis 5G kaudu.

**Latentsus** (kasutaja vajutus → roboti esimene liigutus, 30 sõnumit):

| Küsimisvahe | Keskmine | Maksimum | Postil käike tunnis | Fail |
| :--- | :--- | :--- | :--- | :--- |
| 1 s | TODO (mõõtmine käib) | TODO | 3600 | [latency_poll_fast.csv](docs/latency_poll_fast.csv) |
| aeglane | TODO | TODO | TODO | [latency_poll_slow.csv](docs/latency_poll_slow.csv) |
| Labor 1, täht otse Atomi nupult | Atom → jaam 4,4 ms, jaam → esimene robotikäsk 494 ms (5 vajutust) | 12,2 ms / 592 ms | — | [Lab 1](../lab1/README.md) |

**Ühendus katkes keset tööd.** 15.11.26, 3 korda (tähed C, D, E): telefoni
hotspot (Atomi Wi-Fi) lülitati välja, kui robot joonistas. Robot joonistas
tähe lõpuni, Atom hoidis tulemust (`result_retry_wait`) ja saatis selle pärast
Wi-Fi taastumist; server: `done` kell 11:29:08, 11:33:57 ja 11:34:54 UTC.
[Video, täht C](docs/evidence/connection-loss-letter-c-2026-11-15.mp4)
(19,6 s): töö jäetakse telefonist, hotspot lülitatakse välja, robot lõpetab
tähe C paberil.

**Atom on vait.** Leht ja API näitavad iga Atomi viimast postil käiku
(`last_seen`). 15.11.26 Atom vooluta: `last_seen` jäi 11:17:01 UTC peale,
olek `stale` ~10 s ja `offline` ~30 s pärast seda (`ATOM_STALE_SECONDS=10`,
`ATOM_OFFLINE_SECONDS=30`).

### 3. Kaamerad ja Atomi leht

**Üks pilt kummastki kaamerast samal hetkel:** TODO.

| Kaamera | Lahutus | Viide | FPS | Ribalaius | Fail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Laud, Verbatim AWC-03, 1280 × 720 (jaama lehel) | 1280 × 720 | keskm. 306 ms, max 371 ms | 9,95 | 8,75 Mbit/s | [camera_metrics.csv](docs/camera_metrics.csv) |
| Laud, 3840 × 2160 → 1280 × 720 | 3840 × 2160 | keskm. 437 ms, max 494 ms | 9,94 | 8,38 Mbit/s | sama |
| Laud, 1920 × 1080 → 1280 × 720 | 1920 × 1080 | keskm. 501 ms, max 590 ms | 5,00 | 4,36 Mbit/s | sama |
| Tööriist, XIAO ESP32S3 Sense (OV3660) | 800 × 600 (SVGA JPEG) | TODO | 12,8 (USB, 14.11.26) | TODO | — |

Lauakaamera mõõdeti 14.11.26, 12 katset iga lahutuse kohta (monitori
muutus → pilt jaama kliendis). Jaama lehel on 1280 × 720: sama FPS ja
väikseim viide.

**Juhtimise latentsus** (jaam saadab MG400-le `MovL` Z ±3 mm → esimene
liigutus tagasisidepordis 30004; [control_latency_cameras.csv](docs/control_latency_cameras.csv)):

| Kaameraid töös | Keskmine | Maksimum | n |
| :--- | :--- | :--- | :--- |
| 0 | 260 ms | 267 ms | 10 |
| 1 (Verbatim 1280 × 720, 10 FPS) | 263 ms | 271 ms | 10 |
| 2 | TODO | TODO | — |

**Kuidas tööriista kaamera pilt jaamani jõuab.** Jaamaarvutil ei ole Wi-Fi-d,
seega tuleb XIAO pilt USB serial'i kaudu: `python -m src.camera_server
--xiao-port COM5`. Lauakaamera käib USB kaudu OpenCV-ga. Leht
`http://127.0.0.1:5002` kuulab ainult jaamaarvutis.

**Vaateväli (15.11.26).** Lauakaamera näeb kogu lauda ja robotit.
Tööriistakaamera näeb pliiatsi otsa ja joonistatud tähti.

**Atomi leht:** seadete ja testide nimekiri on failis
[`docs/atom_page.md`](docs/atom_page.md) (serveri aadress, Atomi võti,
küsimisvahe, postkontori test). Rõhuanduri seaded ja testnupp (ADC, pinge,
kPa): TODO, Andmehõive Lab 2 kalibratsioon on vaja.

## Kontrollnimekiri

Õppejõu 20 punkti. Iga tehtud punkti juures kuupäev ja tõend.

- [x] Iga arvuti kohta oma SSH võti; dropleti aadress ja link saadud.
  Iga liikme võti oma arvutist on dropletis (15.11.26). [Droplet](#1-droplet).
- [x] Droplet töötab, igast arvutist saab oma võtmega sisse, paroolisisselogimine
  keelatud, tulemüür lahti ainult kasutatud portidel (20.10.26, 15.11.26).
- [x] Leht käib õppejõu lingi peal HTTPS-iga (20.10.26).
- [x] Kasutaja leht avaneb telefonist mobiilse andmesidega (20.10.26, 5G).
  Ekraanipilt WiFi väljas: TODO.
- [x] Atom käib postil oma võtmega: saadab oleku ja küsib sõnumeid (14.11.26).
- [x] Kasutaja jätab sõnumi, robot teeb töö, leht näitab vastust; kaks eri tööd,
  üks neist Labori 1 täht: `letter A` ja `display_image` (15.11.26).
- [x] Lubatud tööde nimekiri kirjas; muu sõnum ei liiguta midagi (15.11.26).
  [Postkontor](#2-postkontor).
- [x] Sõnum aegub, vana sõnum ei liiguta robotit; läbi proovitud (15.11.26).
- [ ] Latentsus: 30 sõnumit kahe küsimisvahega. Mõõtmine käib.
- [x] Ühendus katkestatud keset tööd: robot lõpetas, vastus jõudis kohale
  (15.11.26, 3 korda). [Video](docs/evidence/connection-loss-letter-c-2026-11-15.mp4).
- [x] Atom vait: leht näitab viimast postil käiku; proovitud vooluta Atomiga (15.11.26).
- [x] Kes mida saadab: [`docs/server_api.md`](docs/server_api.md).
- [ ] Ohutuskokkulepe kirjas ja kõigil loetud. [`docs/safety.md`](docs/safety.md):
  Denys 15.11.26; teised liikmed kinnitavad ise.
- [x] Lauakaamera näitab kogu lauda ja robotit (15.11.26).
- [x] Tööriistakaamera näitab otsikut ja detaili selle all (15.11.26).
- [x] Mõlemad pildid on jaama lehel, labori võrgus (15.11.26).
- [ ] Mõlema kaamera viide, FPS ja ribalaius; juhtimislatentsus mõlema
  kaameraga. Verbatim ning 0 ja 1 kaameraga tehtud 14.11.26; XIAO ja 2 kaamerat TODO.
- [ ] Rõhuanduri seaded ja testnupp Atomi lehel, `docs/atom_page.md` uuendatud.
- [x] Tellimus 16.10: selle labori jaoks ei tellitud midagi ([`docs/bom.md`](docs/bom.md)).
- [ ] Repo ja arenduspäevik täidetud, tag `smart-solutions-lab2`.

## Tööfailid

| Osa | Kaust / fail |
| :--- | :--- |
| Postkontor (Flask + SQLite) | [`server/`](server/app.py) |
| Dropleti paigaldus ja kontroll | [`deploy/`](deploy/README.md) |
| AtomS3R püsivara (PlatformIO, `atoms3r_normal`) | [`firmware/`](firmware/README.md) |
| XIAO tööriistakaamera püsivara (PlatformIO) | [`firmware-xiao-camera/`](firmware-xiao-camera/README.md) |
| Jaama adapter ja kaameraleht | [`src/station_adapter.py`](src/station_adapter.py), [`src/camera_server.py`](src/camera_server.py) |
| Testid | [`tests/`](tests/), kogu kontroll `smart-solutions/lab2/check.sh` |
| Dokumendid | [`docs/server_api.md`](docs/server_api.md), [`docs/atom_page.md`](docs/atom_page.md), [`docs/safety.md`](docs/safety.md), [`docs/bom.md`](docs/bom.md), [`docs/cameras.md`](docs/cameras.md) |

Mõlemad püsivarad ehitatakse ja laaditakse PlatformIO-ga (`platformio.ini`,
lähtekood ja sõltuvused repos). Saladused (Wi-Fi, Atomi võti, CA header) on
ignoreeritud failides, mitte repos.

### Kiirstart ilma riistvarata

Lab 2 kaustas, Python 3.11+:

```sh
cd smart-solutions/lab2
python3 -m venv .venv && . .venv/bin/activate
pip install -r server/requirements.txt 'requests>=2.32,<3'

# kohalik postkontor (ajutine baas, näidisparoolid)
env POST_OFFICE_BIND=127.0.0.1 POST_OFFICE_DB=/tmp/lab2-demo.sqlite3 \
  POST_OFFICE_USER=demo-user POST_OFFICE_PASSWORD=demo-password \
  ATOM_API_KEY=demo-atom-key python -B -m server.app      # http://127.0.0.1:5001

# tarkvaraline tervikahel: postkontor → simuleeritud Atom → jaama adapter → tulemus
python -B -m src.e2e_demo

# kahe kaamera leht sünteetiliste piltidega
python -B -m src.camera_server --mock --host 127.0.0.1 --port 5002
```

## Arenduspäevik

**KAARDISTA ISE — päevik.** Üks sissekanne iga töösessiooni kohta, kirjutatud
nii, et inimene, kes kohal ei olnud, saab aru. Sissekandeid lisatakse, mitte
ei muudeta.

**PP.KK.AA — kes olid kohal**

* Tegime:
* Juhtus (numbrid):
* Otsustasime, ja miks:
* Lahti järgmiseks korraks:

**11.10.26 — Nikita**

* Tegime: Valmistasin ette ja viisin software-foundation'i tasemele Flaski +
  SQLite'i postkontori, autentitud Atomi polling/result API, TTL/expiry ja
  idempotentsuse, AtomS3R PlatformIO polling-püsivara aluse, station'i
  job-adapteri ja kaamerakihi, XIAO ESP32S3 Sense PlatformIO kaamerapüsivara
  aluse ning Gunicorni, systemd ja Caddy näidetega dropleti paigaldusaluse.
  Lisasin regressioonitestid ja software-only E2E kontrolli. Füüsilist
  riistvara ega päris dropletit selles töös ei kasutatud.
* Juhtus (numbrid): Python: `63 passed`; deployment-testid: `7/7`; Atomi
  native-testid: `12/12`; XIAO native-testid: `6/6`; mõlemad PlatformIO buildid:
  `SUCCESS`; software E2E: `server_status=done`, `hardware_used=false`.
* Otsustasime, ja miks: Atom algatab dropleti suunas väljamineva pollingu ning
  droplet ei loo otseühendust station'i ega MG400-ga. Internetist võetakse vastu
  ainult kõrgtaseme töid, kaamerad jäävad lokaalsesse võrku ning direct
  control/VPN kuulub Lab 3-sse. Atom ja XIAO kasutavad kohustuslikult
  PlatformIO-d, saladused jäävad repost välja ning ebaselge või korduv töö
  lõpetatakse fail-safe keeldumisega, mitte robotiliikumise kordamisega.
* Lahti järgmiseks korraks: AtomS3R-i päris upload ja lokaalne polling-katse,
  päris droplet, MG400 integratsioon, teine kõrgtaseme töö, füüsilised kaamerad
  ning Andmehõive Lab 2 rõhukalibratsioon.

**12.10.26 — Nikita**

* Tegime: Viisin Lab 2 README Lab 1-ga samasse struktuuri ja stiili ning
  kontrollisin kõigi kolme kursuse Lab 2 README vormingute kooskõla. Tegin Smart
  Solutions pre-hardware auditi: kontrollisin faile `docs/server_api.md`,
  `docs/atom_page.md`, `docs/safety.md`, `docs/bom.md`, mõõtmiste CSV-malle ja
  juurfaili `AGENTS.md`. Lisasin süsteemiarhitektuuri failid
  `docs/system.drawio` ja `docs/system.svg`, dokumenteerisin Andmehõive ja 3D
  Printing sõltuvused ning märkisin puuduva teise kõrgtaseme töö selgeks
  blocker'iks.
* Juhtus (numbrid): `git diff --check` läbis; `4` measurement CSV-malli
  sisaldavad ainult päiseid; lubatud kõrgtaseme robotitöid on `1` (`letter`);
  teine töö on `TODO`; loodud süsteemiskeemi faile on `2` (`system.drawio` ja
  `system.svg`). Need arvud on dokumentatsiooni- ja tarkvarafaktid, mitte
  füüsilised mõõtmistulemused.
* Otsustasime, ja miks: Lab 2 dokumentatsioon järgib Lab 1 vormingut ning
  füüsilised tulemused jäävad TODO-ks kuni päris mõõtmiseni. Rõhukalibratsioon
  tuleb Andmehõive Lab 2-st ning kaamerate füüsiline kinnitus ja FOV sõltuvad 3D
  Printing Lab 2-st. `pick_place` ei ole teostatud töö enne tegelikku lubamist
  ja kontrolli; tag luuakse alles pärast täielikku lõppkontrolli.
* Lahti järgmiseks korraks: ühendada päris AtomS3R, laadida Lab 2 püsivara
  PlatformIO-ga, kontrollida serial boot'i ja Atomi web/settings lehte, testida
  lokaalset postkontori pollingut ning hiljem teostada ja kontrollida teine
  kõrgtaseme töö.

**12.10.26 — Nikita (AtomS3R hardware test)**

* Tegime: Ehitasin Lab 2 `atoms3r` environment'i, tuvastasin ühendatud seadme
  PlatformIO abil ning laadisin püsivara füüsilisse AtomS3R-i. Vaatasin serial
  logi 115200 baudiga, käivitasin lokaalse Flask post-office'i development-only
  saladustega ja kontrollisin `/health` kättesaadavust nii loopback- kui ka
  sülearvuti LAN-aadressil. Peatasin katse enne Atomile Wi-Fi või API võtme
  sisestamist, sest server ei olnud LAN-ist kättesaadav.
* Juhtus (numbrid): Port oli `/dev/cu.usbmodem101` (USB VID:PID `303A:1001`).
  `pio run -e atoms3r` oli `SUCCESS` ajaga 4,36 s; RAM 50 168 / 327 680 baiti
  (15,3%) ja flash 1 122 541 / 3 342 336 baiti (33,6%). Upload oli `SUCCESS`
  ajaga 22,22 s ning kirjutatud image'i hash kontrolliti. Serialis ei nähtud
  panic'ut ega boot loop'i ja firmware jõudis pollingutsüklisse, kuid logis
  kordus `[E][Preferences.cpp] ... activeId NOT_FOUND` ligikaudu iga 9 ms ning
  `POST poll_failed` ligikaudu kord sekundis; seetõttu ei loetud boot-kontrolli
  puhtalt läbituks. Sülearvuti LAN IP oli `192.168.50.249`. Serveri
  `http://127.0.0.1:5001/health` vastas HTTP 200, kuid
  `http://192.168.50.249:5001/health` ei olnud kättesaadav.
* Otsustasime, ja miks: Praegust production'i localhost-piiri ei muudeta
  varjatult. Füüsilise Atomi lokaalseks arendustestiks on vaja eraldi selgelt
  lubatavat development-bind'i LAN-liidesele, säilitades production'i
  `127.0.0.1` vaikeväärtuse. Enne jätkamist tuleb eemaldada ka puuduva
  `activeId` võtme tekitatud NVS log storm. Web/settings lehte, server-test'i,
  pollingut/`last_seen` väärtust, persistence'it ega Wi-Fi reconnect'i selles
  katses läbituks ei märgitud.
* Lahti järgmiseks korraks: Lisada ja dokumenteerida minimaalne development-only
  LAN-bind, parandada puuduva `activeId` lugemine, korrata puhast serial boot'i,
  avada Atomi setup-AP/web settings, kasutada ainult lokaalset development
  võtit, testida `/health`, päris pollingut ja `last_seen` väärtust ning alles
  seejärel teha reboot persistence ja Wi-Fi reconnect kontrollid. MG400,
  droplet, XIAO, kaamerad ja ametlikud latentsusmõõtmised jäävad sellest katsest
  välja.

**12.10.26 — Nikita (AtomS3R hardware test, jätk)**

* Tegime: Leidsin LAN blocker'i põhjuse funktsioonist `server.app.main`, kus
  development-server kasutas alati `127.0.0.1`. Lisasin piiratud
  `POST_OFFICE_BIND` opt-in'i: default on endiselt loopback ning `0.0.0.0` on
  lubatud ainult teadlikuks development LAN testiks. Production'i Gunicorn ja
  Caddy jäid loopback-piirile. Leidsin NVS flood'i põhjuse funktsioonist
  `PersistentState::activeJobId()`: värskel seadmel normaalset puuduvat
  `activeId` võtit loeti igas võrgutsüklis `getString()` abil. Lisasin enne
  lugemist `isKey()` kontrolli, testisin tarkvara, ehitasin ja laadisin firmware
  uuesti ning kordasin serial- ja LAN-kontrolli.
* Juhtus (numbrid): Python suite: `66 passed`; Atom native-testid: `13/13`;
  Atom build: `SUCCESS` 7,82 s, RAM 50 168 / 327 680 baiti (15,3%), flash
  1 123 057 / 3 342 336 baiti (33,6%). Re-upload pordile
  `/dev/cu.usbmodem101` oli `SUCCESS` 16,25 s ja image'i hash kontrolliti.
  Mitmesekundilises serial-vaatluses ei olnud panic'ut ega reboot loop'i ning
  `activeId NOT_FOUND` log storm kadus täielikult; seadistamata ühenduse
  `POST poll_failed` jäi ligikaudu 1000 ms intervallile. Sülearvuti tegelik LAN
  IP oli endiselt `192.168.50.249`. Explicit `POST_OFFICE_BIND=0.0.0.0` korral
  vastasid nii `http://127.0.0.1:5001/health` kui ka
  `http://192.168.50.249:5001/health` HTTP 200.
* Otsustasime, ja miks: Kaht algset parandust ei laiendatud arhitektuuri
  refactor'iks ega production'i avalikuks bind'iks. Atom ei ilmunud praeguse
  LAN-i ARP-tabelisse ning `Lab2AtomSetup` AP-d ei leitud ka pärast normaalset
  restarti. Tõenäoline põhjus on varasem `wifi` NVS SSID, mille olemasolul
  firmware jääb STA connecting olekusse ega tee setup-AP fallback'i. Salvestatud
  Wi-Fi andmeid ei loetud ega kustutatud ilma eraldi kinnitamiseta. Seetõttu ei
  märgitud settings-lehte, server-test'i, autentitud pollingut, `last_seen`
  väärtust, persistence'it ega reconnect'i läbituks.
* Lahti järgmiseks korraks: Kinnitada turvaline Wi-Fi taastamisviis — kasutada
  teadaolevat salvestatud võrku, kustutada kasutaja loal ainult vana Wi-Fi NVS
  seadistus või lisada eraldi kontrollitud setup-AP fallback. Seejärel avada
  settings-leht, sisestada lokaalne development URL ja võti, kontrollida
  `/health`, autentitud pollingut ja tegelikku intervalli, `last_seen` väärtust,
  reboot persistence'it ning Wi-Fi reconnect'i. MG400, droplet, XIAO, kaamerad
  ja ametlik mid-job disconnect test jäävad endiselt välja.

**13.10.26 — Nikita (AtomS3R Wi-Fi reconnect test)**

* Tegime: Lisasin olemasolevale setup-AP fallback'ile piiratud AP+STA recovery:
  seadistus-AP jääb võrgu taastumise ootamise ajal aktiivseks, salvestatud
  STA-seadistust proovitakse perioodiliselt uuesti ning eduka ühenduse järel
  peatatakse retry ja setup-AP. Ehitasin ja laadisin püsivara päris AtomS3R-i,
  kontrollisin autentitud lokaalset pollingut ja reboot-järgset persistence'it
  ning tegin reaalse 2,4 GHz katkestus- ja taastamiskatse ilma Atomi reboot'ita.
* Juhtus (numbrid): Native-testid läbisid `21/21`; Atom build oli `SUCCESS`,
  RAM 50 176 / 327 680 baiti (15,3%) ja flash 1 127 693 / 3 342 336 baiti
  (33,7%); upload pordile `/dev/cu.usbmodem1101` oli `SUCCESS`. Enne katkestust
  vastas `POST /api/atom/poll` HTTP 200 ligikaudu `1000 ms` intervalliga ning
  `last_seen` uuenes. 2,4 GHz kadumisel lõppes polling, serial näitas esmalt
  reason `51` (`INVALID_FTE`) ja seejärel reason `201` (`NO_AP_FOUND`);
  `15 s` järel oli lõppolek `WL_NO_SSID_AVAIL` ja käivitus `Lab2AtomSetup`.
  Recovery retry intervall oli `20 s` ning ühe STA-katse timeout `15 s`.
  Võrgu taastumise järel assotsieerus Atom järgmisel retry-katsel, sai uuesti
  aadressi `192.168.50.19` ja polling jätkus automaatselt HTTP 200-ga;
  `last_seen` uuenes väärtuselt `2026-10-12T22:16:20.330494Z` väärtusele
  `2026-10-12T22:16:24.333387Z`. Käsitsi raadio sisselülitamise hetke ei
  timestamp'itud Atomiga samast kellast, seega täpset taastumisaega sekundites
  ei esitata. Panic'ut, reboot loop'i ega NVS log storm'i ei olnud.
* Otsustasime, ja miks: Fallback kasutab AP+STA režiimi, et setup-leht jääks
  kättesaadavaks, kuid retry ei muutuks tight loop'iks. SSID-d, Wi-Fi parooli,
  serveri URL-i, Atomi võtit ega pollinguseadeid katkestuse ajal ei kustutata.
  Edukas STA taastumine lõpetab recovery-oleku ja tavapolling jätkub ilma
  reboot'ita. Development-võtit ega muid saladusi päevikusse ei lisata.
* Lahti järgmiseks korraks: Ametlik mid-job katkestuskriteerium koos aktiivse
  töö ja saatmata tulemuse NVS retry-ga, production droplet/HTTPS, päris MG400,
  kaamerad, latentsusmõõtmised ja Andmehõive rõhukalibratsioon jäävad TODO-ks.

**16.10.2026 — Nikita Teterev**

* Tegime: Sain õppejõult serveri ligipääsuandmed ja logisin SSH võtmega
  DigitalOcean Dropletisse. Kloonisin repo kataloogi
  `/opt/smart-solutions-lab2/app`, lõin Python virtualenv'i ja paigaldasin
  production-sõltuvused. Käivitasin `deploy/install.sh`, mis lõi systemd
  teenuse `smart-solutions-lab2`. Täitsin kaitstud
  `/etc/smart-solutions-lab2/env` faili, kontrollisin nõutud väärtuste
  olemasolu ja placeholder'ite puudumist ning käivitasin teenuse käsitsi.
  Kontrollisin teenuse olekut, kuulamisaadressi, SQLite faili ning kohalikke
  HTTP vastuseid.
* Juhtus (numbrid): Ubuntu `24.04.5 LTS`, Python `3.12.3`, Flask `3.1.3` ja
  Gunicorn `23.0.0`. Install läbis; teenus oli `active (running)`, Gunicorn
  kuulas ainult `127.0.0.1:5001` ning töötasid `2` worker'it ja `1` master.
  Env-faili omanik oli `root:root`, õigused `0600`. Andmebaas
  `/var/lib/smart-solutions-lab2/post-office.sqlite3` oli `24 KB`, omanik
  `smart-solutions-lab2`, õigused `0600`. `GET /health` vastas HTTP `200` ja
  JSON-iga `{"ok":true,"service":"lab2-post-office"}`. Autentimata `GET /`
  vastas HTTP `401` päisega
  `WWW-Authenticate: Basic realm="Lab 2 post-office"`. Systemd autostart oli
  kontrolli ajal `disabled`, UFW `inactive`. Teenuse hilisemat peatamist
  ei ole kinnitatud.
* Otsustasime, ja miks: Hoidsin veebiparooli ja Atomi API-võtme eraldi
  paroolihalduris; saladusi ega env-faili sisu reposse ei lisanud. Jätsin
  Gunicorni loopback-liidesele ja SQLite faili lähtekoodipuust välja.
  Märkisin tehtuks esmase paigalduse, health'i ja autentimata ligipääsu
  keeldumise kontrolli. HTTP 401 ei kinnita õige parooliga login'it ning
  loopback HTTP ei kinnita avalikku HTTPS-i ega Atomi production-pollingut.
* Lahti järgmiseks korraks: Kontrollida login'it õige veebiparooliga ning
  tööde loomist ja salvestamist päris HTTP kaudu. Seadistada ja kontrollida
  Caddy/avalik HTTPS, UFW ning SSH hardening koos password-login'i
  keelamisega; läbida täielik `deploy/verify.sh`, backup ja taastamine.
  Lubada ja kontrollida teenuse autostart. Teha telefoni mobiilsidekatse ja
  AtomS3R production HTTPS polling. MG400, päris kaamerad ja latency
  mõõtmised jäävad TODO-ks.

**20.10.2026 — Nikita Teterev**

* Tegime: Uuendasin Ubuntu 24.04.5 LTS serverit, kontrollisin SSH
  autentimisseadeid ja sõltumatut võtmega login'it pärast UFW aktiveerimist.
  Lõin ja aktiveerisin swap-faili ning lisasin kirje `/etc/fstab` faili.
  Seadistasin Caddy avaliku postkontori jaoks domeenil `narva2.roboarena.org`.
  Kontrollisin HTTPS-i välise curl'iga Macist ning autentimist ja UI-d Safari
  kaudu Macis ja Chrome'iga telefonis 5G kaudu. Lõin töö `letter A`,
  kontrollisin aegumist ja SQLite kirje säilimist teenuse restardi järel.
  Tegin SQLite backup'i, taastasin selle eraldi testbaasi ja käivitasin
  `deploy/verify.sh`.
* Juhtus (numbrid): Ubuntu `24.04.5 LTS`, uuendatud `11` paketti.
  SSH effective config: `pubkeyauthentication yes`, `passwordauthentication no`,
  `kbdinteractiveauthentication no`. UFW `active`, sissetulevad TCP
  `22`, `80`, `443` lubatud, default `deny incoming`; uus sõltumatu SSH login
  õnnestus. Aktiivne swap-fail `1 GiB`, kirje `/etc/fstab` failis.
  Caddy `2.11.7`, `active`, `enabled`; `smart-solutions-lab2` samuti `active`
  ja `enabled`. Väline `/health` curl: `HTTP/2 200`, korrektne TLS.
  Mõlema brauseri autentimine ja UI töötasid. Töö `letter A` sai oleku
  `expired`, põhjus `ttl_expired`; kirje säilis teenuse restardi järel.
  SQLite backup: `24576` baiti, `root:root`, mode `600`. Eraldi testbaasis
  `integrity_check: ok` ja töö kirje taastati. `deploy/verify.sh`:
  `12 PASS, 0 FAIL, 0 SKIP`. Atom oli avalikus serveris offline.
* Otsustasime, ja miks: Eristan teenuse restarti kogu dropleti reboot'ist:
  kirje püsimine on kontrollitud teenuse restardiga, kuid hosti reboot ja
  teenuste käivitumine pärast seda pole kontrollitud. Taastasin backup'i
  eraldi SQLite baasi, et kontrollida terviklikkust ja töö kirjet toimivat
  baasi üle kirjutamata. Aegunud töö kinnitab TTL-rada; offline Atomiga ei
  kinnita see production pollingut ega roboti täitmisrada.
* Lahti järgmiseks korraks: Kontrollida kogu dropleti reboot'i ja teenuste
  automaatset taastumist, Atomi production HTTPS pollingut ning füüsilist
  Lab 2 end-to-end ahelat. Täielik taastamine puhtale hostile, MG400
  integratsioon, päris kaamerad, rõhuandur/Andmehõive kalibratsioon,
  latency/metrics, ametlik mid-job katkestuskatse ja ohutuskinnitused jäävad
  lahti.

**20.10.2026 — Nikita Teterev (production TLS ettevalmistus, jätk)**

* Tegime: Kontrollisin Macis `https://narva2.roboarena.org` TLS-ahelat
  OpenSSL-iga. Laadisin Let's Encrypti ametlikult veebilehelt ISRG Root X2
  juursertifikaadi ja kontrollisin SHA-256 fingerprint'i. Lõin lokaalse
  `firmware/include/post_office_ca_private.h` faili ning kontrollisin
  `git check-ignore` abil, et see jääb Git'ist välja. Ehitasin `atoms3r`
  püsivara, kontrollisin PEM-sertifikaadi olemasolu `firmware.bin` failis
  ning käivitasin `bash smart-solutions/lab2/check.sh`.
* Juhtus (numbrid): Kontrollitud TLS-ahelas olid Let's Encrypt YE2,
  Root YE ja ISRG Root X2. OpenSSL: `Verify return code: 0 (ok)`.
  ISRG Root X2 SHA-256 fingerprint:
  `69729b8e15a86efc177a57afb7171dfc64add28c2fca8cf1507e34453ccb1470`.
  `pio run -e atoms3r`: `SUCCESS`, RAM `15,4%`, flash `34,5%`, aeg `20,98 s`.
  Eraldi binaarikontroll leidis ISRG Root X2 PEM-sertifikaadi.
  Regressiooniskript lõpetas teatega
  `All software-only regression checks passed.`
* Otsustasime, ja miks: Hoian CA header'i ja build-artifact'id lokaalselt;
  dokumentatsiooni läheb sertifikaadi nimi ja fingerprint, mitte PEM ega
  binaar. Maci TLS-kontroll ja CA olemasolu build'is annavad aluse järgmisele
  seadmekatsele, kuid ei kinnita Atomi production HTTPS ühendust.
* Lahti järgmiseks korraks: Taastada projektipüsivara päris AtomS3R-i,
  kontrollida seadeid ja production HTTPS pollingut ning `last_seen`
  uuenemist. Päris MG400/jaama integratsioon, rõhuanduri ja kaamerate katsed,
  latency ning ametlik mid-job katkestuskatse jäävad TODO-ks.

**20.10.2026 — Nikita Teterev (production UI uuendus, jätk)**

* Tegime: Uuendasin `narva2.roboarena.org` postkontorit `deploy/update.sh`
  kaudu commit'ilt `7571582` commit'ile
  `7d374915f48e9f4cc7e4357e3a2c82df6191f231`. Enne uuendust loodi SQLite
  backup-failid ning Git fast-forward läbis. Kontrollisin pärast teenuse
  restarti käivitumist, kordasin `deploy/verify.sh` kontrolli ja vaatasin uut
  liidest Safari kaudu Macis ning Chrome'iga Androidis 5G kaudu.
* Juhtus (numbrid): Kohe pärast `systemctl restart` käsku sai kontroll
  `127.0.0.1:5001` aadressilt connection refused ja avalikult HTTPS-ilt `502`.
  Lühikese aja järel hakkas Gunicorn kuulama `127.0.0.1:5001`; täpset aega
  ei mõõdetud. Korduv `deploy/verify.sh`: `12 PASS, 0 FAIL`. Dropleti Git
  tööpuu oli puhas. Varasem `letter A` säilis SQLite'is olekuga `expired`,
  põhjusega `ttl_expired`. Telefonis töötasid letter/pick-place väljade
  ümberlülitus ja tööde mobiilikaardid.
* Otsustasime, ja miks: Esimene kontroll ebaõnnestus Gunicorni käivitumise
  ajal; edukas korduskontroll järgnes valmisolekule. `systemctl restart`
  lõpetamine ei kinnita veel avatud HTTP porti. Lisasime repos `update.sh`
  skripti enne muutmata `verify.sh` käivitamist piiratud lokaalse `/health`
  ootamise: kuni 15 päringut, igal päringul 1 s timeout ja katsete vahel 1 s
  paus. Ainult HTTP 200 lubab jätkata, limiidi ületamine lõpetab uuenduse
  veaga. Readiness-parandus on praegu ainult lokaalselt testitud.
* Lahti järgmiseks korraks: Kontrollida parandatud uuendusskripti järgmise
  lubatud production-uuenduse ajal. Atomi production HTTPS polling, füüsiline
  MG400/jaama ahel, rõhuandur ja päris kaamerad, latency/metrics ning kogu
  dropleti reboot jäävad eraldi kontrollideks.

**23.10.2026 — Nikita Teterev (AtomS3R BENCH-katse)**

* Tegime: Asendus-AtomS3R-i Lab 1 täis-flash backup loodi Macis väljaspool
  Git'i; kontrolliti suurust ja SHA-256 ning pärast backup'i töötas endiselt
  Lab 1 ekraan. Laadisime ühe kontrollitud `atoms3r` BENCH_MODE=1 püsivara.
  MacBook ühines kaitstud `Lab2AtomBench` AP-ga ja Safari avas
  `http://192.168.4.1` read-only eestikeelse liidese. Proovisime kohalikku
  G5 ADC testi ilma andurita. USB Serial Monitor ühendas kiirusel 115200;
  Reset'i vajutamisel näitas macOS katkestust ja taasühendumist ning LCD
  naasis `BENCH` / `execution disabled` kuvale. Atom oli kogu katse ajal
  välisest riistvarast lahti ühendatud.
* Juhtus (numbrid): ESP32-S3-PICO-1, flash `8 MB`; backup `8 388 608` baiti,
  SHA-256 kontrollitud, backup'i sisu ei avaldatud. BENCH puhas build
  `SUCCESS`, native `43/43`, Python `480 passed`. Upload `SUCCESS`, esptool
  kinnitas kirjutatud andmete hash'i; `erase_flash` ega `uploadfs` ei kasutatud.
  LCD näitas `BENCH`, `execution disabled`, `Lab2AtomBench`, `192.168.4.1`
  ja ajutist AP parooli (parooli ei dokumenteerita). ADC vastus:
  `status=not_calibrated`, `raw_adc=7`, `calibrated=false`,
  `sensor_connected=not_verified`, `voltage_v=null`, `pressure_kpa=null`.
  `raw_adc=7` on ujuva sisendi vaatlus, mitte füüsiline rõhumõõtmine.
  Save- ja postkontori testinupud olid lehel keelatud. HTTP 423 jõustamist
  kontrollisid software-testid, mitte eraldi päring päris Wi-Fi kaudu.
  Rakenduse diagnostilisi serial-teateid ei salvestatud ega kinnitatud.
* Otsustasime, ja miks: Hoidsime BENCH_MODE'i ja välise riistvara isolatsiooni.
  Kasutaja võttis selle katse jaoks teadlikult vastu ESP-IDF 4.4.7
  panic/coredump'i ja OTA metadata jääkriski: kogu flash'i muutumatust ei
  garanteerita. Kaitstud AP ja veebilehe avanemine ei tõenda production
  HTTPS-i ega pollingut. Reset'i järel nähtav BENCH-ekraan ei tõenda NVS-i
  säilimist ega puhtaid rakenduse serial-logisid. Salvestame ainult kinnitatud
  vaatlused; varasemate sessioonide kandeid ei muudeta.
* Lahti järgmiseks korraks: Püüda rakenduse diagnostilised serial-teated,
  mõõta päris HTTP 423 vastused ning kavandada NVS-i säilimise kontroll.
  Normaalrežiimi, production HTTPS/pollingu ja station-adapteri katsed vajavad
  eraldi luba. MG400, pump, kaamerad, rõhuandur/LM358 ahel, Andmehõive Lab 2
  kalibratsioon, latency-mõõtmised ja ametlik mid-job katkestuskatse jäävad TODO.

**23.10.2026 — Nikita Teterev (BENCH HTTP 423, jätk)**

* Tegime: Saatsin MacBookist curl'iga kaks POST-päringut päris AtomS3R-ile
  kohaliku `Lab2AtomBench` Wi-Fi kaudu. Päringutes ei olnud paroole ega API-võtmeid.
  Atom jäi BENCH_MODE'i; station, MG400, pump ja andurid olid lahti ühendatud.
* Juhtus (numbrid): `POST http://192.168.4.1/settings` andis `HTTP/1.1 423`
  ja `{"error":"bench_read_only"}`. `POST http://192.168.4.1/test/post-office`
  andis samuti `HTTP/1.1 423` ja `{"error":"bench_read_only"}`. Need kaks
  tulemust kinnitavad firmware HTTP-keeldu riistvaral, lisaks software-testidele.
  Esimese sama päeva kande HTTP 423 TODO on nende kahe endpoint'i osas täidetud.
* Otsustasime, ja miks: Kontrollisin keeldu otse HTTP kaudu, sest keelatud
  nupp brauseris üksi ei tõenda serveripoolset kaitset. See katse ei kinnita
  `/pressure/settings` POST-i, NVS-i täielikku säilimist ega production-pollingut.
  Production HTTPS-i/pollingut ei kasutatud; coredump'i jääkrisk jäi samaks.
* Lahti järgmiseks korraks: Kontrollida `/pressure/settings` POST-i päris
  HTTP 423 vastust, püüda rakenduse serial-diagnostika ja kavandada NVS-i
  säilimise kontroll. Production HTTPS, station/MG400, pump, kaamerad ning
  päris rõhuanduri/op-amp ahel ja kalibratsioon jäävad TODO-ks.

**23.10.2026 — Nikita Teterev (BENCH pressure/settings HTTP 423, jätk)**

* Tegime: Saatsin MacBookist curl'iga kohaliku `Lab2AtomBench` Wi-Fi kaudu
  kolmanda safety-päringu päris AtomS3R-ile. Kasutasin käsku
  `curl --noproxy '*' -i --max-time 5 -X POST http://192.168.4.1/pressure/settings`.
* Juhtus (numbrid): Vastus oli `HTTP/1.1 423`,
  `Content-Type: application/json`, keha `{"error":"bench_read_only"}`.
  Koos eelmise jätkukandega on kõik kolm POST-route'i (`/settings`,
  `/test/post-office`, `/pressure/settings`) riistvaral HTTP 423-ga kontrollitud.
* Otsustasime, ja miks: Säilitame BENCH_MODE'i piiratud kontrolli tulemuse.
  Kolm keeldumist kinnitavad nende HTTP-handler'ite kaitset, mitte täielikku
  NVS-i säilimist või kogu flash'i read-only olekut. ESP-IDF coredump'i risk jääb.
* Lahti järgmiseks korraks: Rakenduse serial-diagnostika ja füüsilise NVS-i
  säilimise kontroll. Production HTTPS/polling, station/MG400, pump, kaamerad,
  rõhuandur/op-amp ja kalibratsioon ning ametlikud mõõtmised jäävad TODO-ks.

**23.10.2026 — Nikita Teterev (AtomS3R HEALTH_ONLY, jätk)**

* Tegime: Laadisin asendus-AtomS3R-i eraldi `atoms3r_health` püsivara ja
  kontrollisin ekraani ning USB-helper'iga suhtlust. Lubasin ühe health-katse
  Redmi telefoni Wi-Fi hotspot'i kaudu. Varasemad BENCH-tulemused jäävad
  eraldi katseteks; neid kandeid ei kirjutata ümber.
* Juhtus (numbrid): Päris upload õnnestus. Helper näitas järjest
  `WIFI CONNECTED`, `TLS VERIFIED`, `HEALTH ERROR` ning naasis shell'i.
  Edukat HTTP 200 ega `{"ok":true,"service":"lab2-post-office"}` vastust
  ei kinnitatud. Wi-Fi ja TLS-i tulemus ei ole edukas `/health` end-to-end test.
* Otsustasime, ja miks: Säilitame isoleeritud ühe päringu build'i, USB kaudu
  antava ühekordse loa, RAM-only Wi-Fi seaded ning NVS-guard'id. API-võtit,
  pollingut, claim'i, result retry'd ega station/actuator-käske see katse ei
  vaja. Üldine `HEALTH ERROR` ei erista write/read/timeout'i, HTTP staatust,
  framing'ut ega JSON kontrolli. Dokumenteerisime piiratud diagnostikakoodide
  plaani; neid koode ei ole veel püsivarasse lisatud. Chunked-framing on
  parseris keelatud, kuid selle seost päris veaga ei ole tõendatud.
  ESP-IDF flash-coredump'i ja OTA metadata jääkrisk, Maci UTC usaldamine
  ning CRL/OCSP puudumine jäävad kehtima. Saladusi ega backup'i ei avaldata.
* Lahti järgmiseks korraks: Eristada HTTP etapi viga ilma saladuste või body
  logimiseta ning teha eraldi lubatud `/health` korduskatse. Autentitud
  production-polling, füüsiline station/MG400/pump, kaamerad, Andmehõive
  kalibratsioon, NVS-i säilimine, latency ja ametlik mid-job katse jäävad TODO.

**06.11.2026 — tarkvaraintegratsioon ja füüsilised Atomi LCD-katsed**

* Tegime: Valmistasime tarkvaraliselt ette kontrollitud live-letter raja:
  Lab 1 read-only terminalolek, stabiilne töö identiteet, SQLite safety
  interlock, protsessilukk ja selgesõnalised kohalikud käivitusload
  (`77fa985`; [käivitusjuhend](docs/live_letter_runbook.md)). MG400-ga seda
  veel ei katsetatud. Ühendasime kaks olemasolevat kaameravoogu Lab 1 station'i
  lehele, säilitades loopback-juhtimise ja eraldi worker'id (`19909ca`);
  kontroll kasutas mock-kaameraid, mitte päris kaameramõõtmisi.
  Postkontori server/UI sai `display_image` whitelist'i (`b38c6cc`) ning
  NORMAL-püsivara kohaliku renderer'i ja NVS-i `local_display` allika
  (`957142c`). Uuele AtomS3R-ile loodi privaatne 8 MiB täis-flash backup,
  kontrolliti SHA-256 ja laaditi üks kord `atoms3r_normal`; esptool kinnitas
  kirjutatud andmete hash'i. LCD näitas Setup AP-d ja kasutaja avas Maci
  Safaris kohaliku lehe ning GET `/state` ja `/settings`; algul olid
  active/pending tühjad ning SSID, server ja API-võti seadistamata.
  Seejärel kasutati eraldi test-SQLite'iga Flask-postkontorit ja Xiaomi
  WPA2 / 2,4 GHz hotspot'i. Pärast testivõtme parandamist asendus polling'u
  403 vastus HTTP 200-ga ning `last_seen` hakkas uuenema.
  Kontrollisime ühe päris AtomS3R-iga (MAC `B4:3A:45:BC:CE:84`)
  NORMAL-püsivara kahte sisseehitatud pilti kohaliku Flask/SQLite
  HTTP-testpostkontori kaudu. Kasutaja kinnitas LCD-l L2-pildi ja seejärel
  rohelise linnukese; StationAdapter'it, MG400-t ega production'it ei kasutatud.
* Juhtus (numbrid): Avaldamiseelne tarkvarakontroll: pytest `888 passed,
  1 skipped`, native `72/72`, NORMAL/BENCH/HEALTH_ONLY buildid `SUCCESS`.
  Need on software-only tulemused. Uue Atomi backup oli `8 388 608` baiti;
  privaatset sisu ei avaldatud. NORMAL upload ja rakenduse esimene käivitus
  olid edukad; kohalik seadeleht töötas. Polling-seade oli `1000 ms`.
  Loodi täpselt `2` tööd, üks POST kummagi kohta, TTL
  `120 s`. Mõlema loomine andis HTTP `201`, Atomi poll/result HTTP `200`
  ning terminaltulemus oli `done / local_display`. JSON-id ja test-SQLite
  kinnitavad kahte lõpetatud tööd; ID-d ja tõendite piirid on
  [LCD-katsete raportis](docs/display_image_evidence.md). Visuaalse tulemuse
  kinnitas kasutaja vestluses; fotode lisamine on kirjas 07.11 jätkukandes.
* Otsustasime, ja miks: Eristame füüsilist LCD-kuva mock-tulemustest ja
  kohaliku HTTP katset avalikust HTTPS-ist. Kaks pilti on sama töö tüübi
  kaks argumenti ega täida üksi kahe eri töö nõuet koos Lab 1 tähega.
* Lahti järgmiseks korraks: Aegumine, whitelist-keeldumine, offline-kuva,
  avalik HTTPS ning katkestuse/reboot'i retry. Päris `letter`, kolm mid-job
  katkestuskatset, roboti latentsus,
  kaamerad ja rõhuanduri integratsioon jäävad laborisse. Lab 2 ei ole lõpetatud.

**07.11.2026 — tõendite ja dokumentatsiooni avaldamise ettevalmistus**

* Tegime: Võrdlesime mõlemat privaatset LCD-katse JSON-i test-SQLite'i
  kirjetega ning täiendasime README-d, firmware README-d ja
  [tõendite raportit](docs/display_image_evidence.md). Varasemad päevikukanded
  jäid muutmata. Vaatasime üle kasutaja kaks LCD-fotot ja paigutasime need
  `docs/evidence/` kausta pildibaite muutmata. Uusi riistvarakatseid ega töid
  ei käivitatud.
* Juhtus (numbrid): Kontrollitud baasis oli täpselt `2` lõpetatud
  `display_image` tööd, mõlemad `done / local_display`. Mõlemal on kasutaja
  visuaalne LCD-kinnitus ja nüüd ka foto. Lisati `2` kontrollitud JPEG-i;
  EXIF/XMP ega kommentaariplokke neis ei leitud. Markdowni viited ja
  `git diff --check` läbisid.
* Otsustasime, ja miks: Git'i läheb kontrollitud dokumentatsioon ning ainult
  üle vaadatud fotod. Credentials, SQLite, USB/serverilogid ja flash-backup'id
  jäävad privaatseks. Kohalikku HTTP tõendit ei esitata avaliku HTTPS-i ega
  roboti täieliku integratsiooni tulemusena.
* Lahti järgmiseks korraks: Avaldada kontrollitud dokumentatsioon ja fotod
  ning jätkata raporti koduste ja laboratoorsete TODO-dega.
  Lõplikku Lab 2 tag'i veel ei looda.

**07.11.2026 — rollide täpsustus 06.–07.11 tööde kohta**

* 06.11 aitas Codex tarkvaramuudatusi ette valmistada ja testida. Kasutaja
  ühendas füüsilise AtomS3R-i, kontrollis seadete lehte, seadistas
  testühenduse ning kinnitas mõlemad pildid LCD-l. Codex laadis kasutaja
  loal NORMAL-püsivara ja kontrollis testpostkontori kaudu tööde tulemusi.
* 07.11 esitas kasutaja LCD-fotod. Codex võrdles katsetulemusi, täiendas
  dokumentatsiooni ja avaldas selle koos fotodega kasutaja loal (`7f1aab2`).

**13.11.2026 — Atomi võrgu ja Raimo SSH-ligipääsu kontroll**

* AtomS3R (MAC `B4:3A:45:BC:CE:84`) ühendus Redmi pääsupunktiga. MacBooki
  IP oli `10.117.35.52` ja Atomi IP `10.117.35.65`. Päringud
  `GET /state` ja `GET /settings` õnnestusid. Atomi olek oli
  `sta_connected` ning `active_job_id` ja `pending_result_id` olid tühjad.
  MacBookis ei töötanud kohalik postkontor ja port `5001` ei kuulanud,
  seega oli `poll_failed` ootuspärane.
* Nikita logis SSH kaudu `root`-kasutajana serverisse
  `narva2.roboarena.org`. Dropletis loodi sudo-õiguseta konto `raimo` ja
  lisati Raimo avalik võti faili `/home/raimo/.ssh/authorized_keys`.
  Kataloogi õigused olid `700` ja faili õigused `600`. Kontroll
  `sshd -t` õnnestus. Võtme sõrmejälg oli
  `SHA256:33+xYP4P1FwYsTTgqgxekHIhPoW23xkfmvctZWkHC1I`.
  Raimo kinnitas isiklikult, et sai oma kontoga SSH kaudu sisse logida.
* Lahti jäid ülejäänud liikmete SSH-ligipääs, Atomi production HTTPS
  polling, päris MG400 töö, kaamerad, rõhuandur ja dropleti taaskäivituse katse.

**14.11.2026 — kaamerad, XIAO püsivara, station'i SSH ja juhtimislatentsus**

* Kaamerad laboriarvutis: Verbatim (OpenCV seade 0) andis `3840 × 2160`
  kaadri; XIAO ESP32S3 Sense (USB serial `1C:DB:D4:43:35:DC`) andis JPEG-i
  ka vana 3D Printingu USB-püsivaraga. Verbatimi praeguses asendis ei ole
  Gridfinity ruudustik servast servani kaadris; ruudunimesid kaadris ei
  olnud, loetavuse katse jäi tegemata.
* XIAO-sse laaditi `firmware-xiao-camera` (commit `0e90d98`): OV3660 tuvastati,
  PSRAM 8 MB, SVGA JPEG ~19,6 KB, USB kaudu 20 kaadrit keskmiselt 78 ms
  (12,8 FPS). Lisatud: 3D Printingu USB-protokoll (`c`/`i`), et sama
  püsivara teenindaks ka 3D hubi; `WiFi.setSleep(false)`; OV3660 vflip jäeti
  välja nagu 3D püsivaras. Wi-Fi seaded ignoreeritud `wifi_private.h` failis;
  XIAO ühines telefoni pääsupunktiga ja sai IP `10.200.77.31`.
* Station'i ja XIAO vaheline Wi-Fi rada ei toiminud: laboriarvutil pole
  Wi-Fi adapterit ning MG400 võrgus `192.168.1.x` pole ruuterit. Telefoni
  USB-jagamine andis arvutile IP `10.239.80.157`, kuid päring
  `http://10.200.77.31/status` aegus 10 s jooksul (telefon ei suuna USB- ja
  Wi-Fi-klientide vahel). USB-jagamise ajal oli arvutil kaks võrdse
  meetrikaga vaikemarsruuti ja DNS aegus; jagamine lülitati välja.
  Lahendus vajab Wi-Fi-ga station'i sülearvutit või Etherneti külge
  ruuterit/pääsupunkti.
* Atomi (`B4:3A:45:BC:CE:84`) NVS-is oli server `http://10.117.35.52:5001`
  (MacBooki kohalik postkontor), seega `POST poll_failed`; production URL
  ja CA-ga püsivara on järgmine samm.
* Station PC sai oma ed25519 võtme (sõrmejälg
  `SHA256:scHNEQNcaUa0d/mqWz2wCqyqoikrtnuNpSGUVC9sg0E`); Nikita lisas selle
  kasutajale `denys`. Kontroll: `whoami` = `denys`, `sudo -v` õnnestus,
  ilma võtmeta sisselogimine andis `Permission denied (publickey)`.
* Juhtimislatentsus (`src/latency_bench.py`, uus): station saadab
  MG400 pordile 30003 `MovL` Z ±3 mm, kiirus 2 %, vabas õhus, inimene
  hädastopi juures. Esimene liikumine tuvastatakse tagasisidepordist 30004
  (~8 ms pakett, liigese muutus > 0,05°, `src/motion_watch.py`). Tulemused
  failis `docs/control_latency_cameras.csv`: ilma kaamerata keskmine 260 ms,
  max 267 ms (n = 10); USB kaamera töös (1280 × 720, 10 FPS, 1 klient)
  keskmine 263 ms, max 271 ms (n = 10). Kahe kaamera tingimus jäi tegemata,
  sest XIAO ei jõua station'ini Wi-Fi kaudu.
* Kaamera viite katse kaadrite erinevuse järgi ebaõnnestus: 3 mm liikumine
  2 % kiirusel ei muuda laua kaamera pilti piisavalt (6/10 korral muutust
  ei leitud). Need read jäeti tulemustest välja; kaamera viide mõõdetakse
  taimeriga kaadris.

**14.11.2026 — AtomS3R-i HTTPS-ühendus avaliku postkontoriga**

* AtomS3R-ile (MAC `B4:3A:45:BC:CE:84`) ehitati ja laaditi PlatformIO-ga
  `atoms3r_normal`, mis sisaldas ISRG Root X2 juursertifikaati. Enne
  laadimist kontrolliti 8 MiB flash-varukoopiat ja partitsioonitabeli
  vastavust. Esptool kinnitas kirjutatud andmete kontrollsummad.
  Pärast laadimist olid varasemad NVS-i seaded alles, Wi-Fi olek Redmi
  pääsupunktis oli `sta_connected` ning `active_job_id` ja
  `pending_result_id` olid tühjad.
* Seadistati `https://narva2.roboarena.org` ja pollinguintervalliks
  `1000 ms`. Kohaliku HTTP arendusrežiim oli väljas.
  `TEST SERVER HEALTH` andis `health_ok`. Polling andis algul
  `poll_http_403`. Pärast õige tootmiskeskkonna API võtme sisestamist oli
  vastus `poll_ok_no_job`. Avalik leht näitas olekut `online` ja
  `last_seen` uuenes 14.11.2026.
* Katse hõlmas tühja järjekorda. Avaliku ahela töö täitmine ning
  TTL-i, lubamatute tööde ja `offline`-oleku katsed päris Atomiga on ootel.

**15.11.2026 — Denys**

* Tegime: Uuendasime `https://narva2.roboarena.org` commit'ile `ea423b6`
  (`deploy/update.sh`). Saatsime avalikust postkontorist tööd päris
  ahelasse: postkontor → Atom (HTTPS-polling) → USB → jaama adapter →
  Labori 1 jaam → MG400. Proovisime läbi lubamatud tööd, aegumise, vooluta
  Atomi ja ühenduse katkestuse keset tööd. Panime mõlemad kaamerad jaama
  kaameralehele. Atom ↔ jaam USB-ühendusele lisasime kviitungi
  `station_ack` ja laadisime Atomi püsivara 15.11.
* Juhtus (numbrid): `deploy/verify.sh` kõik PASS. `letter A` joonistati
  paberile (pliiatsi kalibratsioon `lab1/config/robot_calibration_pen.json`,
  leht 239,4 × 150,7 mm, pliiats all Z −113,35 mm), olek `done`.
  `display_image` `lab2_logo` ja `lab2_check`: `done / local_display`.
  `move` koordinaatidega, `letter` väljaga `x` ja „Ж“: HTTP 400
  (`unknown_job`, `unexpected_field`, `invalid_letter`), järjekorda ei
  läinud midagi. `letter B` TTL 15 s vooluta Atomiga: `expired / ttl_expired`,
  Atomi sisselülitamisel robot ei liikunud. Vooluta Atom: `last_seen`
  11:17:01 UTC, `stale` ~10 s, `offline` ~30 s pärast. Hotspot välja keset
  joonistamist 3 korda (C, D, E): robot lõpetas tähe, server `done`
  11:29:08, 11:33:57, 11:34:54 UTC. `station_ack` kordus iga 1,5 s kuni
  8 korda, tulemuse tähtaeg 300 s. Kaamerad: Verbatim AWC-03 1280 × 720
  (OpenCV), XIAO USB serial'i kaudu (`--xiao-port COM5`).
  [Video, täht C](docs/evidence/connection-loss-letter-c-2026-11-15.mp4)
  (19,6 s): töö jäetakse telefonist, hotspot lülitatakse välja, robot
  lõpetab tähe C paberil.
* Otsustasime, ja miks: XIAO pilt tuleb jaama USB kaudu, sest jaamaarvutil
  ei ole Wi-Fi-d; kaameraleht jääb ainult kohalikuks (`127.0.0.1:5002`).
  Atom ootab jaamalt kviitungit ja tulemust tähtajaga, et kadunud USB-sõnum
  lõppeks keeldumisega (`station_no_ack` / `station_result_timeout`), mitte
  ootamisega. Jaama tähekataloog võtab vastu kõik A–Z, mida Labor 1 joonistab.
  BOM: selle labori jaoks ei tellitud midagi.
* Lahti järgmiseks korraks: latentsus 2 × 30 sõnumit, mõlema kaamera
  mõõdikud koos XIAO-ga ja juhtimislatentsus kahe kaameraga, rõhuanduri
  seaded ja test Atomi lehel, telefoni ekraanipilt WiFi väljas, teiste
  liikmete ohutuskinnitused, tag `smart-solutions-lab2`.

## Väljundid ja tulemused

**Väljundid**
* Andmehõive L2: Atomi leht, kus on serveri, võtme ja küsimisvahe seaded ning
  postkontori test; rõhuanduri seaded ja test on TODO.
* 3D printimine L2: lauakaamera pilt kogu lauast ja robotist ning
  tööriistakaamera pilt pliiatsi otsast (15.11.26).
* Nutikad Lahendused L3: töötav avalik postkontor dropletis (HTTPS, SSH
  võtmetega, UFW) ja kaks kohalikku kaamerapilti jaama lehel.

**KAARDISTA ISE, lõpus.**
* Git repo ja tag: TODO — lisada esitamisel.
* Numbrid, mille see labor andis, ühikutega: Atomi `stale`/`offline` 10 s /
  30 s; Atom ↔ jaam kviitung iga 1,5 s kuni 8 korda, tulemuse tähtaeg 300 s;
  lauakaamera 1280 × 720 viide keskm. 306 ms, 9,95 FPS, 8,75 Mbit/s;
  juhtimislatentsus 0 / 1 kaameraga 260 / 263 ms; pollingu latentsus TODO.
* Meeskonna ohutuskinnitused: Denys 15.11.26 ([safety.md](docs/safety.md));
  teised liikmed kinnitavad ise.
* Mida me teeksime teisiti: TODO — täita lõpus.
* Mida järgmine labor peaks enne alustamist teadma: jaamaarvutil ei ole
  Wi-Fi-d, seega XIAO pilt tuleb USB kaudu; TODO — täita lõpus.
