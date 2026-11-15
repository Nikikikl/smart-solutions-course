# Lab 2 postkontori API leping

> **Olek 20.10.2026:** API on Flask-serveris teostatud ja automaattestidega
> kontrollitud. Päris dropletil on kontrollitud avalik HTTPS, kasutaja
> autentimine, `letter A` loomine/aegumine ning kirje püsimine teenuse restardi
> järel. Päris Atomi production polling ning jaama/MG400 integratsioon on TODO.

## Piirid ja usaldusmudel

```text
kasutaja/brauser
      |
   HTTPS + kasutaja autentimine
      v
dropleti postkontor
      ^
      | HTTPS polling + Atomi autentimisvõti
      v
    Atom
      |
   Labori 1 lokaalne kanal
      v
    jaam
      |
   MG400 lokaalne API
```

Põhireeglid:

- droplet ei algata ühendust Atomi, jaama ega MG400-ga;
- droplet ei ole jaama lehe relay/proxy ning Lab 2 arhitektuuris ei ole VPN-i
  ega tunnelit dropleti ja jaama vahel; otsene kaugjuurdepääs jaamale kuulub
  Lab 3 ulatusse;
- Atom algatab kõik postkontori polling- ja tulemuspäringud väljapoole;
- postkontor võtab vastu ainult whitelist'is olevaid kõrgtaseme töid, mitte
  koordinaate, trajektoore, DO väärtusi ega otseseid liikumiskäske;
- jaam teeb kohaliku valideerimise ja on ainus komponent, mis tohib MG400-le
  liikumiskäske saata;
- kaameravood ei lähe postkontorisse; need jäävad kohalikku võrku ja neid
  vahendab eraldi station'i kaameraprotsess; selle lokaalsed route'id on
  kirjeldatud failis [`cameras.md`](cameras.md) ega kuulu sellesse API-sse;
- kasutajaleht ja Atomi API on loogiliselt eraldi marsruutide, autentimise ja
  õigustega;
- Atomi autentimisvõti salvestatakse Atomis, mitte lähtekoodis ega repos;
- kasutajaleht nõuab autentimist;
- production-transpordi siht on HTTPS; HTTP sobib ainult lokaalseks
  arenduseks ilma päris saladuste või robotitäitmiseta.

## Production HTTP piir

Production-ahel on `Internet -> HTTPS Caddy -> Gunicorn/Flask ->
SQLite`. Caddy on ainus avalik HTTP(S) endpoint ning Gunicorn kuulab ainult
`127.0.0.1:5001`; rakenduse porti ei avata tulemüüris. WSGI entrypoint on
`server.wsgi:app`. Kõik runtime väärtused tulevad kaitstud systemd
EnvironmentFile'ist, mitte lähtekoodi või Git-i salvestatud saladustest.

AtomS3 server URL on kujul `https://<TEAM_HOSTNAME>` ja kasutab sama Caddy
HTTPS piiri väljaminevaks pollinguks. Postkontorisse ei lisata station'i,
MG400, kaamera, stream'i, VPN-i ega tunneli endpoint'e. `/health` on minimaalne
avalik tervisekontroll; ülejäänud marsruutide autentimine jääb allpool
kirjeldatud Basic/bearer piiridesse.

Systemd, Caddy, env, install/update/backup/verify mallid ning värske Ubuntu
taastamisjuhend on failis [`../deploy/README.md`](../deploy/README.md).
Nikita kontrollis 20.10.2026 päris dropleti avalikku HTTPS-i domeenil
`narva2.roboarena.org`: Maci väline curl sai `/health` päringule HTTP/2 200
korrektse TLS-iga, Safari Macis ja Chrome telefonis 5G kaudu avasid autentitud
kasutajalehe. DNS ja avalik HTTPS on kontrollitud 20.10.2026.

Maci OpenSSL kontrollitud TLS-ahelas olid Let's Encrypt YE2, Root YE ja
ISRG Root X2; tulemus oli `Verify return code: 0 (ok)`. Atomi jaoks on ISRG
Root X2 CA-ga lokaalne build ette valmistatud, nagu kirjeldab
[firmware README](../firmware/README.md#production-tls-ettevalmistus--20102026).
CA olemasolu binaaris ei tõenda päris Atomi TLS-ühendust ega bearer-pollingut:
need on endiselt TODO. Täielik taaste puhtale hostile ja kogu dropleti reboot
on samuti kontrollimata.

## Whitelist

| `job` | Lubatud `arg` | Olek |
| :--- | :--- | :--- |
| `letter` | objekt väljaga `letter`, üks suurtäht `A`–`Z` | serveris lubatud ja testitud; hardware integration TODO |
| `pick_place` | täpselt `{"routine":"source_to_finished"}` | software-only ahelas lubatud ja testitud; MG400/pump TODO |
| `display_image` | täpselt `{"image_id":"lab2_logo"}` või `{"image_id":"lab2_check"}` | mõlemad pildid kinnitatud Atomi LCD-l kohaliku HTTP kaudu |

`pick_place` ei tohi sisaldada kasutaja antud X/Y/Z/R koordinaate, kiirust,
pumba-/DO-käske, korduste arvu, trajektoori või skripti. Avalik argument valib
ainult ühe eelmääratud local routine'i. Tulevane päris station executor peab
routine'i ise lokaalseteks, eelnevalt õpetatud ja kontrollitud positsioonideks
ning toiminguteks teisendama. Seda executor'it ei ole veel realiseeritud.

Server lubab kolme kõrgtaseme tööd. Kaitsmise teiseks päris tööks on valitud
`display_image`: Atom näitab üht kahest püsivarasse ehitatud RGB565 pildist.
URL, failitee, koordinaadid ja lisaväljad ei ole lubatud. See töö ei kasuta
StationAdapter'it, USB dispatch'i ega MG400/pumpa. `pick_place` jääb senisele
software-only mock/preflight rajale. `unknown`, test-, status- ja poll-päringud
ei ole teostatud tööd. `display_image` kohalik katse on tehtud. Päris
`letter` ja Atomi avalik HTTPS ahel vajavad veel kontrolli.
[Atomi katseraport](display_image_evidence.md)

Whitelist'i mittekuuluv `job`, tundmatu argument, lisaväli, liiga pikk tekst,
vale tüüp või lubamatu väärtus lükatakse tagasi. Vaikimisi lubamist ei ole.

## Töö kirje

| Väli | Tüüp | Tähendus |
| :--- | :--- | :--- |
| `id` | läbipaistmatu string | serveri loodud püsiv sõnumi/töö ID |
| `job` | string | whitelist'i töö nimi |
| `arg` | objekt | töö tüübile vastav rangelt valideeritav argument |
| `created_at` | UTC ajatempel | serveris loomise aeg |
| `expires_at` | UTC ajatempel | viimane hetk, millal tööd võib claim'ida |
| `status` | enum | üks allpool määratud olek |
| `result` | objekt või `null` | eduka täitmise tulemus ilma saladusteta |
| `reason` | string või `null` | keeldumise/aegumise/vea masinloetav põhjus |

Ajatemplid on UTC ISO 8601 kujul. Server määrab `id`, `created_at` ja
`expires_at`; kliendi kell ei otsusta TTL-i.

## Elutsükkel

```text
queued --Atom claim--> claimed --lokaalne töö õnnestub--> done
   |                      |
   +-- TTL möödub ------> expired
                          +-- lokaalne station keeldub --> refused
```

| Olek | Tähendus |
| :--- | :--- |
| `queued` | valideeritud töö ootab Atomi polli |
| `claimed` | üks Atom on töö püsiva ID-ga vastu võtnud, kuid jaam ei ole täitmist kinnitanud |
| `done` | jaam lõpetas töö edukalt |
| `refused` | töö ei käivitunud või peatati selge ohutus-/valideerimispõhjusega |
| `expired` | TTL möödus enne täitmise algust; töö ei tohi midagi liigutada |

Terminalolekud on `done`, `refused` ja `expired`. Neist ei minda tagasi
`queued` olekusse. Uus katse vajab uut töö kirjet ja uut kasutaja otsust.

### TTL ja aegumine

- server kontrollib TTL-i nii polli kui claim'i ajal;
- `expires_at <= server_now` muudab veel alustamata töö olekuks `expired`;
- Atom kontrollib saadud `expires_at` väärtust uuesti enne töö edastamist
  station'ile, kuid serveri otsus on autoriteetne;
- praegune station-adapter ei saa eraldi TTL-i kontrollida, sest selle lokaalne
  serial-sõnum ei sisalda `expires_at` välja;
- aegunud töö kohta võib saata ACK/result'i, kuid mitte liikumiskäsku;
- juba `claimed` töö TTL ei ole kaugjuhitav stoppsignaal. Kui Atom on töö enne
  aegumist vastu võtnud ja station on selle lokaalselt aktsepteerinud, lõpetab
  station tervikliku töö ka internetikatkestuse korral.

## Teostatud REST endpoint'id

### Kasutaja API

Kasutajaliides ja `/api/jobs*` endpoint'id nõuavad HTTP Basic autentimist.
Parool tuleb keskkonnamuutujast. Production'is peab nende ees olema HTTPS.

| Meetod ja tee | Otstarve |
| :--- | :--- |
| `GET /` | minimaalne kasutajaleht: Atom status, töö loomine ja tööde ajalugu |
| `POST /jobs` | HTML-vormi `letter`, eelmääratud `pick_place` või `display_image` töö loomine |
| `POST /api/jobs` | valideeri whitelist'i töö ja lisa see järjekorda |
| `GET /api/jobs/{id}` | kuva ühe töö olek ja tulemus |
| `GET /api/jobs` | kuva hiljutised tööd ja Atomi olek |
| `GET /api/status` | kuva Atomi `last_seen`, online/stale/offline ja serveri aeg |

### Atomi API

Kõik `/api/atom/*` endpoint'id nõuavad päist
`Authorization: Bearer <ATOM_API_KEY>`. Võtit ei saadeta query-stringis ega
logita. Production'is kasutatakse HTTPS-i.

| Meetod ja tee | Otstarve |
| :--- | :--- |
| `POST /api/atom/poll` | heartbeat/status ja järgmise töö atomaarne claim |
| `POST /api/atom/result` | raporteeri idempotentselt `done` või `refused` |
| `GET /api/atom/jobs/{id}` | loe sama töö autoriteetne serveriolek pärast katkestust |

Poll on korraga heartbeat ja töö küsimine. Kui tööd ei ole, vastab server
edukalt `job: null`; see ei ole viga.

## Example: töö loomine

```http
POST /api/jobs
Content-Type: application/json
```

```json
{
  "job": "letter",
  "arg": {"letter": "A"},
  "ttl_seconds": 60
}
```

Example-vastus:

```json
{
  "id": "example-job-id",
  "job": "letter",
  "arg": {"letter": "A"},
  "created_at": "2030-01-01T12:00:00Z",
  "expires_at": "2030-01-01T12:01:00Z",
  "status": "queued",
  "result": null,
  "reason": null
}
```

Kuupäevad ja ID on ainult formaadinäited, mitte mõõtmised ega production-andmed.

`pick_place` loomise näide erineb ainult high-level töö ja argumendi poolest:

```json
{
  "job": "pick_place",
  "arg": {"routine": "source_to_finished"},
  "ttl_seconds": 60
}
```

Kasutaja ei anna selle tööga robotipositsioone ega actuator-käske.

## Example: Atomi poll ja heartbeat

```json
{
  "device_id": "example-atom-id",
  "poll_interval_ms": 1000,
  "atom_uptime_ms": 123456,
  "station": {
    "reachable": true,
    "robot_state": "locally_enabled"
  }
}
```

Example-vastus töö olemasolul:

```json
{
  "server_time": "2030-01-01T12:00:10Z",
  "job": {
    "id": "example-job-id",
    "job": "letter",
    "arg": {"letter": "A"},
    "created_at": "2030-01-01T12:00:00Z",
    "expires_at": "2030-01-01T12:01:00Z",
    "status": "claimed"
  }
}
```

`poll_interval_ms` on Atomi tegelik kasutatud väärtus ja salvestatakse
heartbeat'i juurde. Mõõtmistes kirjutatakse tegelik intervall iga rea juurde.
Production-vaikeväärtus on TODO — real test required.

## Example: Atomi tulemus

```http
POST /api/atom/result
Authorization: Bearer <ATOM_API_KEY>
Content-Type: application/json
```

Eduka station-tulemuse päring:

```json
{
  "id": "example-job-id",
  "status": "done",
  "result": {"source": "local_station"}
}
```

Server vastab salvestatud tööga ja märgib, kas täpselt sama terminaltulemus
oli duplikaat:

```json
{
  "job": {
    "id": "example-job-id",
    "job": "letter",
    "arg": {"letter": "A"},
    "status": "done",
    "result": {"source": "local_station"},
    "reason": null
  },
  "duplicate": false
}
```

`refused` päringus on `reason` kohustuslik. Tundmatu ID annab `404`, muu kui
`claimed` olek või vastuoluline terminaltulemus `409`; täpselt sama `done` või
`refused` kordus tagastab `200` ja `duplicate: true`. Näite ID ja andmed on
formaadinäited, mitte päris täitmise tulemus.

`display_image` loomine kasutab sama `POST /api/jobs` ja pollingut:

```json
{"job":"display_image","arg":{"image_id":"lab2_logo"},"ttl_seconds":60}
```

Atom salvestab claim'i enne põhiloopi LCD-päringut. Alles pärast renderer'i
lõppu ja terminaltulemuse NVS commit'i saadab ta sama `/api/atom/result` kaudu
`{"id":"example-image-id","status":"done","result":{"source":"local_display"}}`.
`local_station` jääb `letter`/`pick_place` tulemuse allikaks. Source säilib
NVS-is, reboot'il ja HTTPS retry ajal; salvestatud tulemust ei asendata ning
retry ei joonista pilti uuesti. Poolik claim muutub reboot'il
`refused / ambiguous_after_reboot`, mitte uueks kuvamiseks. 06.11.2026
kinnitas kasutaja mõlema pildi nähtavust päris Atomi LCD-l. Kohalikus
testpostkontoris kontrolliti sama ID-ga tulemust `done / local_display`.
Serveri tulemuse API ja autentimine ei muutu.
[Atomi katseraport](display_image_evidence.md#kinnitatud-füüsilised-tulemused)

## Heartbeat, `last_seen` ja roboti olek

- server uuendab autentitud polli vastuvõtmisel Atomi `last_seen` väärtuse;
- online/offline tuletatakse serveri kellast, viimasest nähtud ajast ja
  kokkulepitud polling-intervallist;
- offline-piir peab lubama vähemalt ühe ajutise ebaõnnestumise ja määratakse
  pärast päris võrgu katseid;
- `robot_state` on jaama raporteeritud kirjeldav olek, mitte dropleti käsk;
- minimaalsed kavandatud väärtused: `unknown`, `offline`, `locally_disabled`,
  `locally_enabled`, `busy`, `fault`;
- `locally_enabled` saab tekkida ainult ruumis oleva inimese tegevusest;
  droplet ega Atom ei paku remote-enable käsku.

## Idempotentsus ja kordused

1. Server loob ühe püsiva `id` ja muudab `queued → claimed` atomaarse
   andmebaasioperatsiooniga. Sama tööd ei anta paralleelselt teisele pollile.
2. Atom salvestab aktiivse töö ID enne selle edastamist jaamale. Ta kasutab
   kõigis korduskatsetes muutmata ID-d.
3. AtomS3 lisab Labori 1 serial-JSON sõnumile stabiilse `job_id`. Lab 2
   tarkvaraline jaamaadapter hoiab ID ja `session + seq` olekut SQLite'is.
   Kui ID on juba lokaalselt lõpetatud, tagastab ta salvestatud tulemuse ega
   kutsu executor'it uuesti. Päris MG400 executor integration on TODO.
4. `claimed` tähendab ainult seda, et server andis töö Atomile. Server ei
   näita `executing` olekut, sest praegune API ei saa seda usaldusväärselt teada.
   Kui polli vastus Atomini ei jõudnud, jääb töö `claimed` olekusse ilma
   tulemuseta. Selline töö antakse järgmisel pollil uuesti välja, kui
   `claimed_at` on vanem kui `CLAIM_LEASE_SECONDS` (vaikimisi 3 s) ja TTL ei
   ole läbi. Tööd hoidev Atom ei polli, seega saab töö uuesti ainult Atom,
   kelle käes seda ei ole; Atom ja station tuvastavad korduse `job_id` järgi.
5. Atom salvestab terminaltulemuse enne aktiivse claim'i kustutamist ja saadab
   sama terminaltulemuse sama ID-ga uuesti kuni `POST /api/atom/result` saab
   eduka vastuse. Serveri tulemusuuendus on idempotentne.
6. Server ei muuda vastuolulist terminalolekut vaikides. Konflikt logitakse ja
   tagastatakse veana inimese uurimiseks.

## Atom → station protokoll

Põhitransport on sama põhimõttega nagu Lab 1 laboriarvutis: üks programm omab
AtomS3 USB serial-porti, baud on seadistatav (vaikimisi 115200) ja iga sõnum
on üks reavahetusega lõpetatud JSON objekt. `letter` säilitab Lab 1 formaadi:

```json
{"letter":"A","session":"post-office","seq":1,"atom_sent_ms":1234,"job_id":"example-job-id"}
```

`pick_place` teeb töö tüübi selgeks ja edastab ainult routine'i nime:

```json
{"job":"pick_place","routine":"source_to_finished","session":"post-office","seq":2,"atom_sent_ms":1234,"job_id":"example-pick-id"}
```

| Väli | Reegel |
| :--- | :--- |
| `letter` | täpselt üks suurtäht `A`–`Z`, mida Lab 1 oskab joonistada (`letters.json` või Lab 1 vaikefont `futural`) |
| `job` | `letter` puhul valikuline/legacy-puuduv; teise töö puhul täpselt `pick_place` |
| `routine` | ainult `pick_place` jaoks täpselt `source_to_finished` |
| `session` | mittetühi kuni 64 märgi pikkune Lab 1-ga ühilduv session |
| `seq` | mittenegatiivne täisarv; koos session'iga vana kanali duplicate key |
| `atom_sent_ms` | valikuline mittenegatiivne Atomi uptime; seda ei võrrelda station'i kellaga |
| `job_id` | kohustuslik serveri stabiilne ID, 1–80 märki (`A–Z`, `a–z`, number, `.`, `_`, `-`) |

Lisaväljad lükatakse tagasi. Seega ei võta adapter vastu koordinaate, kiirust,
pumba väärtust, trajektoori ega muud direct-motion käsku.

Kui töö rida on korrektne, vastab station kohe enne täitmist kättesaamise
kinnitusega:

```json
{"station_ack":{"id":"example-job-id"}}
```

Atom saadab töö rea ühe kirjutusega ja kordab seda iga 1,5 s järel, kuni
kinnitus tuleb (kuni 8 korda). Kordamine on ohutu, sest station tuvastab
dubleeritud `job_id` ja ei täida tööd teist korda. Kui kinnitust ei tule,
saadab Atom serverile `refused / station_no_ack`; kui kinnitus tuli, aga
tulemust 300 s jooksul ei tule, `refused / station_result_timeout`. Atom ei jää
ühelgi juhul lõputult ootama.

Station → Atom tulemus kasutab täpselt firmware poolt loetavat envelope'i:

```json
{"post_office_result":{"id":"example-job-id","status":"done"}}
```

või:

```json
{"post_office_result":{"id":"example-job-id","status":"refused","reason":"robot_not_enabled"}}
```

Stabiilsed station'i keeldumispõhjused on `invalid_message`, `invalid_letter`,
`invalid_routine`, `unknown_job`, `duplicate_conflict`, `robot_not_enabled`, `executor_busy`,
`ambiguous_after_restart` ja `execution_failed`. Vigase JSON-i või puuduva
`job_id` puhul ei ole ID-d võimalik kajastada ning adapter vastab tühja `id`
väärtusega; firmware ei käsitle seda aktiivse töö terminaltulemusena.

SQLite'i kirje luuakse olekus `in_progress` enne executor'i väljakutset.
Terminaltulemus püsib restardi üle. Sama `job_id` ja sama payload tagastavad
sama tulemuse; sama ID teise payload'iga või sama `session + seq` teise ID-ga
annab `duplicate_conflict`. Pärast protsessi restarti muutub pooleli olnud
`in_progress` fail-safe olekuks `refused / ambiguous_after_restart` ning seda
ei käivitata automaatselt uuesti.

Praegused `MockLetterExecutor` ja `MockPickPlaceExecutor` ei impordi MG400
klienti, ei loo robotivõrgu ühendust ega juhi pumpa/DO-d. Pick-place mock märgib
selgelt `hardware_used=false`. Adapteri default on lokaalselt keelatud;
`--allow-mock-jobs` lubab ainult kontrollitud mock-täitmise. Tulevane päris executor peab eraldi tõendama
lokaalse enable'i, roboti teadaoleva safe/ready oleku ja ainsa motion-saatja
omandi. Päris `letter` töö on 15.11.26 läbinud kogu ahela avalikust postkontorist Atomi, USB, Lab 1 ja MG400 kaudu.

## Vigased ja keeldutud tööd

- kasutaja API lükkab skeemile mittevastava või whitelist'i mittekuuluva töö
  tagasi enne järjekorda lisamist;
- kui Atom või jaam avastab lisapiirangu rikkumise, raporteerib ta `refused`
  ja masinloetava `reason` väärtuse;
- serveri/Atomi põhjused ja station'i stabiilne nimekiri on eri piiride
  masinloetavad väärtused; station'i väärtused on fikseeritud ülal;
- hostile input'it käsitletakse andmetena: pikkus, tüüp, lubatud märgid,
  struktuur ja vahemikud valideeritakse; seda ei panda shell-käsku, failiteesse
  ega HTML-i ilma turvalise kodeerimiseta;
- tundmatu, vigane või aegunud töö ei liiguta robotit.

## Ühenduse katkemine ja tulemuse retry

- postkontori kadumine ei katkesta juba Atomile edastatud ja station'is
  lokaalselt vastu võetud terviklikku kõrgtaseme tööd;
- station lõpetab juba vastu võetud töö oma kohalike ohutusväravate järgi;
  internetiühendus ei ole otsene motion-control kanal;
- safe-stop direct remote-control ühenduse kadumisel kuulub Lab 3, mitte selle
  postkontori Lab 2 semantikasse;
- Atom säilitab aktiivse töö ID, viimase jaamalt saadud oleku ja saatmata
  terminaltulemuse üle ajutise internetikatkestuse;
- ühenduse taastumisel kordab Atom sama tulemuse saatmist sama ID-ga fikseeritud
  kahe sekundi retry-intervalliga;
- uut tööd ei claim'ita, kuni eelmise töö lõppolek on lahendatud;
- pärast Atom'i restarti ei käivitata ebaselget aktiivset claim'i uuesti. See
  muudetakse `ambiguous_after_reboot` põhjusega saatmata `refused` tulemuseks.

Serveripoolne idempotentsus ning AtomS3 NVS-puhvri tarkvaraalus on teostatud.
Päris seadme katkestuskatse on veel TODO.

## Kohalik teostus ja konfiguratsioon

Server kasutab Flaski ja SQLite'i. SQLite valiti, sest see säilitab töö ID,
claim'i, terminaltulemuse ja `last_seen` väärtuse serveri restardi järel,
kuid ei vaja eraldi production-andmebaasi. Claim toimub ühes
`BEGIN IMMEDIATE` transaktsioonis; lõpetatud tööd ei panda uuesti järjekorda.

Kohalik käivitus nõuab vähemalt:

- `ATOM_API_KEY` — Atomi bearer-võti;
- `POST_OFFICE_PASSWORD` — kasutajaliidese parool;
- `POST_OFFICE_USER` — kasutajanimi, software default `lab-user`;
- `POST_OFFICE_DB` — valikuline SQLite faili tee;
- `JOB_TTL_SECONDS` — software default 60 s;
- `JOB_MAX_TTL_SECONDS` — software default 3600 s;
- `ATOM_STALE_SECONDS` ja `ATOM_OFFLINE_SECONDS` — software default 10 s / 30 s.

Ilma Atomi võtme või kasutaja paroolita server ei käivitu. Need software
default'id ei ole labori lõplikud väärtused: final TTL ja olekupiirid vajavad
reaalset võrguotsust ja katset.

## Logimine ja saladused

Logida võib töö ID, olekumuutuse, aja, seadme ID pseudonüümi ja veakoodi.
Logida ei tohi Atomi võtit, kasutaja parooli, sessiooniküpsist, SSH privaatvõtit
ega täielikke autoriseerimispäiseid.
