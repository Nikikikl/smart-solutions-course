# Lab 2 postkontori production-paigalduse alus

> **Olek 20.10.2026:** Nikita Teterev kontrollis avalikku HTTPS-i domeenil
> `narva2.roboarena.org`, autentimist Macis ja telefonis 5G kaudu, SSH
> autentimisseadeid, UFW-d, töö loomist/aegumist ning SQLite backup'i
> taastamist eraldi testbaasi. `deploy/verify.sh`: `12 PASS, 0 FAIL, 0 SKIP`.
> Selles katses oli Atom offline. Hilisem autentitud Atomi HTTPS-polling
> on kirjas allpool. Kogu dropleti reboot ja MG400 füüsiline integratsioon
> on kontrollimata.

## Kinnitatud deployment-kontrollid — 20.10.2026

Allpool on Nikita kinnitatud tulemused. 16.10.2026 kontrollid jäävad järgmisse
jaotisse ajaloolise seisuna; uus kontroll ei kirjuta neid üle.

| Kontroll | Tulemus |
| :--- | :--- |
| Ubuntu | 24.04.5 LTS; uuendatud 11 paketti |
| SSH autentimine | `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no` |
| SSH pärast UFW aktiveerimist | Sõltumatu võtmega login õnnestus |
| UFW | `active`; sissetulevad TCP 22, 80, 443 lubatud; default `deny incoming` |
| Swap | 1 GiB swap-fail loodud ja aktiivne, kirje `/etc/fstab` failis |
| Caddy | 2.11.7, `active`, `enabled` |
| Avalik HTTPS | `https://narva2.roboarena.org`; Maci väline curl `/health`: HTTP/2 200, korrektne TLS |
| Kasutajaleht | Autentimine ja UI töötasid Safari Macis ning Chrome telefonis 5G kaudu |
| Töö ja TTL | `letter A` loodud, tulemus `expired`, põhjus `ttl_expired` |
| SQLite püsivus | Töö kirje säilis `smart-solutions-lab2` teenuse restardi järel |
| SQLite backup | 24576 baiti, `root:root`, mode `600` |
| Taastamine eraldi testbaasi | `integrity_check: ok`; töö kirje taastati |
| `deploy/verify.sh` | 12 PASS, 0 FAIL, 0 SKIP |
| `smart-solutions-lab2` | `enabled`, `active` |
| Atom | Avalikus serveris offline; production pollingut ei testitud |

Kogu dropleti reboot ja täielik taastamine puhtale hostile on ootel.
Atomi autentitud HTTPS-polling kinnitati hilisemas 14.11.2026 katses.

## Production UI uuendus — 20.10.2026

Nikita uuendas postkontorit `deploy/update.sh` kaudu commit'ilt `7571582`
commit'ile `7d374915f48e9f4cc7e4357e3a2c82df6191f231`. Enne uuendust loodi
SQLite backup-failid ja Git fast-forward läbis. Kohe pärast
`systemctl restart` käsku ebaõnnestus kontroll: `127.0.0.1:5001` andis
connection refused ning avalik HTTPS `502`. Lühikese aja järel avas Gunicorn
loopback-pordi; täpset käivitusaega ei mõõdetud. Korduv `deploy/verify.sh`
andis `12 PASS, 0 FAIL` ja dropleti Git tööpuu oli puhas.

Nikita kontrollis uut UI-d Safari kaudu Macis ja Chrome'iga Androidis 5G
kaudu. Telefonis töötasid letter/pick-place väljade vahetus ja mobiilikaardid.
SQLite'is säilis varasem `letter A` olekuga `expired`, põhjusega `ttl_expired`.
See on päris UI-uuenduse kontroll; Atomi production pollingut ega MG400
täitmist selle tulemusega tehtuks ei märgita.

## Kinnitatud paigalduskontrollid — 16.10.2026

Nikita kinnitatud tulemused on kirjas ka [Lab 2 arenduspäevikus](../README.md#arenduspäevik).
See tabel kirjeldab 16.10.2026 kontrollihetke, mitte serveri praeguse oleku
uut mõõtmist.

| Kontroll | Tulemus |
| :--- | :--- |
| Ligipääs | Õppejõu antud andmetega võtmega SSH login õnnestus |
| Operatsioonisüsteem | Ubuntu 24.04.5 LTS |
| Repo | `/opt/smart-solutions-lab2/app` |
| Python ja production-paketid | Virtualenv loodud; Python 3.12.3, Flask 3.1.3, Gunicorn 23.0.0 |
| Install | `deploy/install.sh` läbis; systemd teenus `smart-solutions-lab2` loodud |
| Env-fail | `/etc/smart-solutions-lab2/env`, `root:root`, `0600`; nõutud väärtused olemas, placeholder'id puudusid |
| Saladused | Eraldi veebiparool ja Atomi API-võti paroolihalduris; väärtusi siin ei avaldata |
| Teenus ja protsessid | Käsitsi käivitatud, `active (running)`; 2 Gunicorni worker'it ja 1 master |
| Bind | Ainult `127.0.0.1:5001` |
| SQLite | `/var/lib/smart-solutions-lab2/post-office.sqlite3`, 24 KB, omanik `smart-solutions-lab2`, õigused `0600` |
| `GET /health` | HTTP 200, `{"ok":true,"service":"lab2-post-office"}` |
| Autentimata `GET /` | HTTP 401, `WWW-Authenticate: Basic realm="Lab 2 post-office"` |
| Systemd autostart | `disabled` |
| UFW | `inactive`; seadistus ei ole kinnitatud |

Õige veebiparooliga login, tööde loomise ja salvestamise päris HTTP-katsed,
Caddy/avalik HTTPS, SSH hardening ja password-login'i keelamine, täielik
`deploy/verify.sh`, backup/taastamine, telefoni mobiilsidekatse ning AtomS3R
production HTTPS polling on tegemata või kinnitamata. MG400, kaamerate ja
latency füüsilised katsed jäävad samuti TODO-ks. Teenuse hilisemat peatamist
ei ole kinnitatud.

## Arhitektuur ja piir

```text
Internet
   |
   | HTTPS :443
   v
Caddy (avalik TLS-i lõpetamine)
   |
   | HTTP ainult 127.0.0.1:5001
   v
Gunicorn -> Flask postkontor -> SQLite
                                  |
                                  +-- /var/lib/smart-solutions-lab2/

AtomS3 -- väljaminev HTTPS polling --> sama Caddy host
```

Droplet on ainult postkontor. See ei loo ühendust station'i, MG400 ega
kaameratega, ei vahenda kaameravooge ning ei sisalda VPN-i või tunnelit.
Station'i ja kaamerate lokaalne arhitektuur jääb laborivõrku. AtomS3
production server URL on `https://<TEAM_HOSTNAME>` ja ta algatab ühenduse ise.

Gunicorn kuulab ainult `127.0.0.1:5001`. Internetti avatakse Caddy kaudu ainult
HTTP/HTTPS pordid; porti 5001 ei avata tulemüüris. `Caddyfile.example` kasutab
hostinime, mille korral Caddy saab pärast korrektset DNS-i ja portide 80/443
kättesaadavust hallata avalikku HTTPS-sertifikaati.

## Failipaigutus production-hostil

| Tee | Omanik / õigus | Sisu |
| :--- | :--- | :--- |
| `/opt/smart-solutions-lab2/app` | `root:root`, lugemiseks | Git checkout, kogu course repo |
| `/opt/smart-solutions-lab2/venv` | `root:root` | Python virtualenv ja sõltuvused |
| `/etc/smart-solutions-lab2/env` | `root:root`, `0600` | runtime konfiguratsioon ja saladused |
| `/var/lib/smart-solutions-lab2` | service user, `0750` | püsiv SQLite andmebaas |
| `/var/backups/smart-solutions-lab2` | `root:root`, `0700` | kontrollitud SQLite backup'id |
| `/etc/caddy/Caddyfile` | `root:root` | avalik HTTPS reverse proxy |

Teenuse kasutaja `smart-solutions-lab2` on süsteemikonto ilma login-shellita.
Lähtekood ei ole selle kasutaja kirjutatav. Systemd unit annab kirjutusõiguse
ainult püsiva andmebaasi kataloogile.

`deploy/install.sh` ja `deploy/update.sh` paigaldavad ainult postkontori
production-sõltuvused failist `server/requirements.txt`. Kohaliku arenduse,
testide, station-adapteri ja kaamerate sõltuvused on eraldi failis
`server/requirements-dev.txt` ning neid dropletile ei paigaldata.

## Eeltingimused

- puhas toetatud Ubuntu droplet, mille hostinimi/IP on õppejõult saadud;
- iga meeskonnaliikme eraldi SSH võtmepaar ja kontrollitud võtmega login;
- DNS A/AAAA kirje `<TEAM_HOSTNAME>` jaoks;
- `git`, `python3`, `python3.12-venv`, `curl`, Caddy ja `ufw` (`sqlite3` käsk ainult käsitsi kontrolliks);
- `sudo` küsib dropletis parooli; see on paroolihalduris koos veebiparooli ja Atomi võtmega;
- Git checkout on `/opt/smart-solutions-lab2/app`;
- päris väärtused on paroolihalduris, mitte repos ega shelli ajaloos.

Pakette ja Caddyt paigaldatakse nende ametlike Ubuntu juhiste järgi päris
hostil. Repo ei automatiseeri neid samme. 20.10.26 kinnitas Nikita Ubuntu
24.04.5 LTS, 11 paketi uuendamise ning Caddy 2.11.7 `active/enabled` oleku.

## Ligipääs ja avalik HTTPS kontrollitud

Nikita sai ligipääsuandmed ja kontrollis võtmega SSH login'it 16.10.26.
Väärtusi ei salvestata sellesse dokumenti. Runbook'i käsud kasutavad jätkuvalt
placeholder'e:

- `<SSH_USER>`: õppejõu antud SSH kasutajanimi;
- `<DROPLET_IP>`: dropleti avalik aadress;
- `<HOSTNAME>`: õppejõu antud hostinimi/link;

Nikita kontrollis 20.10.26 sõltumatut võtmega login'it pärast UFW
aktiveerimist ning avalikku HTTPS-i domeenil `narva2.roboarena.org`.
13.11.2026 kinnitas Raimo isiklikult oma võtmega SSH-sisselogimist
sudo-õiguseta kontole. Denysi 14.11.2026 jaamaarvuti SSH-kontroll on
[arenduspäevikus](../README.md#arenduspäevik).
Runbook'i `<HOSTNAME>` ja `<TEAM_HOSTNAME>` tähistavad selle
deployment'i puhul `narva2.roboarena.org`.

Repo olemasolevates konfiguratsioonimallides tähistab `<TEAM_HOSTNAME>` sama
õppejõult saadud väärtust, mida selle runbook'i käskudes tähistab `<HOSTNAME>`.

Password-login'i ja keyboard-interactive autentimise keelamine, UFW,
avalik TLS ning telefoni 5G katse on kontrollitud.
14.11.2026 kinnitati füüsilise Atomi autentitud HTTPS-polling tühja
järjekorraga. Avalikul lehel uuenes `last_seen` ja olek oli `online`.
[Atomi katse](../docs/atom_page.md#postkontori-test).

## Kohalik eelkontroll

Privaatvõtit ei avata ega kopeerita. Kontrolli ainult avaliku võtme
fingerprint'i ja privaatse vaste olemasolu:

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub -E sha256
test -f ~/.ssh/id_ed25519 && echo "private counterpart exists"
git -C /path/to/smart-solutions-course status --short --branch
git -C /path/to/smart-solutions-course diff --check
```

Saada õppejõule ainult `id_ed25519.pub` sisu. Kui ligipääs on kinnitatud,
kasuta esimeseks ühenduseks täpselt saadud placeholder'ite väärtusi:

```bash
ssh -i ~/.ssh/id_ed25519 <SSH_USER>@<DROPLET_IP>
```

Hoia esimene sessioon avatuna kuni võtmega teine sessioon, SSH seadistus ja
tulemüür on eraldi kontrollitud.

## Esmane paigaldus

Allolevad käsud on hostil täitmiseks pärast eeltingimuste kontrolli. Asenda
ainult märgitud placeholder'id päris hosti väärtustega. Esmalt tuvasta distro
ja paigalda Ubuntu uuendused ning vajalikud paketid; vaata upgrade'i nimekiri
enne kinnitamist üle:

```bash
cat /etc/os-release
sudo apt update
apt list --upgradable
sudo apt upgrade
sudo apt install -y git python3 python3-venv curl openssl sqlite3 ufw \
  debian-keyring debian-archive-keyring apt-transport-https gnupg
```

Paigalda Caddy tema ametliku Debian/Ubuntu pakivaramu kaudu, mitte tundmatust
binaarist. Enne käivitamist kontrolli allalaaditud võtme ja repo URL-i Caddy
ametliku paigaldusjuhendi vastu:

```bash
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

1. Tee rakenduse kataloog ja klooni repo:

   ```bash
   sudo install -d -o root -g root -m 755 /opt/smart-solutions-lab2
   sudo git clone https://github.com/Dennel04/smart-solutions-course \
     /opt/smart-solutions-lab2/app
   ```

2. Vaata üle checkout'i branch ja commit. Seejärel käivita ettevalmistus:

   ```bash
   cd /opt/smart-solutions-lab2/app/smart-solutions/lab2
   sudo sh deploy/install.sh
   ```

   Skript ei käivita teenust, ei muuda SSH-d/tulemüüri ega paigalda Caddyt.
   Olemasolevat `/etc/smart-solutions-lab2/env` faili see üle ei kirjuta.

3. Loo kolm erinevat väärtust: veebikasutaja nimi, pikk juhuslik veebiparool
   ja eraldi pikk juhuslik Atomi bearer-võti. Ära kasuta näiteid production'is.
   Muuda root'ina `/etc/smart-solutions-lab2/env`, asenda kõik `<...>` väljad
   ja kontrolli õigusi:

   ```bash
   sudoedit /etc/smart-solutions-lab2/env
   sudo chown root:root /etc/smart-solutions-lab2/env
   sudo chmod 600 /etc/smart-solutions-lab2/env
   ```

   `POST_OFFICE_DB` peab jääma välisele püsirajale
   `/var/lib/smart-solutions-lab2/post-office.sqlite3`. Saladusi ei lisata
   Git-i, logisse, issue'sse ega ekraanipilti.

   Genereeri kaks eri saladust käsuga, mille argumendis saladust ennast ei ole;
   salvesta väljund kohe paroolihaldurisse ja puhasta terminali kuva. Käivita
   käsk eraldi veebiparooli ja Atomi bearer-võtme jaoks:

   ```bash
   python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

   `env` faili võtmed on täpselt `POST_OFFICE_USER`,
   `POST_OFFICE_PASSWORD`, `ATOM_API_KEY`, `POST_OFFICE_DB`,
   `JOB_TTL_SECONDS`, `JOB_MAX_TTL_SECONDS`, `ATOM_STALE_SECONDS`,
   `ATOM_OFFLINE_SECONDS` ja `PUBLIC_HOSTNAME`. Sama uus `ATOM_API_KEY` läheb
   hiljem Atomi lokaalse seadistuslehe kaudu Atomisse; seda ei panda käsurea
   argumenti ega Git-i.

4. Kopeeri Caddy näidis, asenda `<TEAM_HOSTNAME>` ja valideeri enne reload'i:

   ```bash
   sudo install -o root -g root -m 644 deploy/Caddyfile.example /etc/caddy/Caddyfile
   sudoedit /etc/caddy/Caddyfile
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```

5. Alles pärast konfiguratsiooni ja DNS-i kontrolli käivita rakendus:

   ```bash
   sudo systemctl enable --now smart-solutions-lab2
   sudo systemctl status smart-solutions-lab2
   sudo journalctl -u smart-solutions-lab2 -n 100 --no-pager
   sudo sh deploy/verify.sh
   ```

`/health` on tahtlikult avalik minimaalne tervisekontroll. Kasutajaliides ja
`/api/jobs*` nõuavad Basic autentimist; `/api/atom/*` nõuab eraldi bearer-võtit.
Rakendus keeldub käivitumast, kui parool või Atomi võti puudub.

## SSH hardening — ohutu järjekord

SSH lukustuse vältimiseks tehakse päris hostil toimingud täpselt sellises
järjekorras. Neid samme ei tee ükski repo skript.

1. Saa õppejõult dropleti aadress, kasutajanimi ja hosti ligipääsureeglid.
2. Tee esimene login õppejõu antud meetodil ning hoia see sessioon avatuna.
3. Lisa igale kasutatavale arvutile selle enda avalik `.pub` võti ja anna
   õppejõule ainult nõutud avalikud võtmed; privaatvõtit ei jagata kunagi.
4. Ava **teine terminal** ja tõesta, et uus võtmega login töötab.
5. Muuda SSH seadistust nii, et parooliga login keelatakse alles nüüd.
6. Valideeri konfiguratsioon käsuga `sudo sshd -t`.
7. Reload'i distro tegelik SSH service (`ssh` või `sshd`), ära tee pimesi
   restarti.
8. Ava veel üks uus võtmega sessioon ja kontrolli seda.
9. Alles pärast õnnestunud kontrolli sulge esialgne sessioon.

Teises lokaalses terminalis kontrolli võtmega login'it nii, et klient ei paku
parooli autentimist:

```bash
ssh -o PasswordAuthentication=no -i ~/.ssh/id_ed25519 \
  <SSH_USER>@<DROPLET_IP>
```

Serveris vaata enne muudatust tegelik effective config ja olemasolevad
drop-in failid üle:

```bash
sudo sshd -T | grep -E '^(passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication) '
sudo find /etc/ssh/sshd_config.d -maxdepth 1 -type f -print
systemctl list-unit-files --type=service | grep -E '^ssh(d)?\.service'
```

Kui password-login ei ole juba keelatud ja hosti omanik lubab muudatust, loo
eraldi drop-in; ära kirjuta distro põhifaili pimesi üle:

```bash
sudo install -d -o root -g root -m 755 /etc/ssh/sshd_config.d
printf '%s\n' \
  'PasswordAuthentication no' \
  'KbdInteractiveAuthentication no' \
  'PubkeyAuthentication yes' \
  | sudo tee /etc/ssh/sshd_config.d/99-smart-solutions-key-only.conf >/dev/null
sudo chmod 644 /etc/ssh/sshd_config.d/99-smart-solutions-key-only.conf
sudo sshd -t
sudo sshd -T | grep -E '^(passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication) '
```

Leia eelmise käsuga tegelik unit (`ssh.service` või `sshd.service`) ja tee
ainult reload, näiteks Ubuntu tavapärase `ssh.service` korral:

```bash
sudo systemctl reload ssh.service
```

Seejärel ava kolmas uus võtmega sessioon. Kui `sshd -t`, reload või uus login
ebaõnnestub, jäta algne sessioon avatuks ja paranda põhjus enne jätkamist.

Root-login, kasutajate loomine ja õppejõu ligipääs kooskõlastatakse hosti
omanikuga; siin ei eeldada nende poliitikat.

## Tulemüür — käskude kontroll-leht

Need on teadlikult dokumenteeritud käsud, mitte automaatne skript. Käivita
need alles pärast võtmega login'i kontrolli ja kinnita enne `enable` käsku,
et kasutatava SSH pordi reegel on olemas.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status verbose
sudo ufw enable
sudo ufw status numbered
sudo ss -lntup
```

Kui host kasutab mittevaikimisi SSH porti, lisa enne tulemüüri aktiveerimist
selle täpne reegel `OpenSSH` profiili asemel. Porti 5001, SQLite'i, station'i,
MG400 või kaamerate jaoks avalikku reeglit ei lisata.

## Uuendamine ja rollback

Uuendamisel vali ja vaata commit/ref enne läbi. Skript nõuab puhast checkout'i,
teeb enne Git muudatust SQLite online-backup'i, lubab ainult fast-forward
merge'i, uuendab Python sõltuvused, restardib teenuse, ootab kohalikku HTTP
valmisolekut ning käivitab muutmata `verify.sh` kontrolli:

```bash
cd /opt/smart-solutions-lab2/app/smart-solutions/lab2
sudo sh deploy/update.sh origin/main
```

`origin/main` on näide teadlikult valitud ref-ist, mitte automaatne soovitus.
Skript ei kasuta force/reset käsku ega kustuta andmebaasi.

Pärast restarti võib systemd näidata teenust aktiivsena enne, kui Gunicorn
kuulamisport on avatud. `update.sh` ootab nüüd
`http://127.0.0.1:5001/health` HTTP 200 vastust: kuni 15 katset, päringu
connection timeout ja kogutimeout kumbki 1 s ning ebaõnnestunud katsete vahel
1 s paus. Maksimaalne ootamine on ligikaudu 30 s (15 päringut ja 14 pausi).
Päring läheb otse loopback-liidesele, proxy-seadeid kasutamata. Kui endpoint
ei saa valmis, lõpetab skript veakoodiga ega kuuluta uuendust edukaks.
Eduka health'i järel peab endiselt läbima täielik `verify.sh`, mille viga
lõpetab samuti skripti veaga. Timeout ei käivita automaatset rollback'i.

See ootamise parandus on lokaalselt mock curl'iga testitav; production'is
20.10.26 nähtud võidujooks tekkis enne paranduse lisamist. Parandatud skripti
production-kontroll on TODO.

Backup'i saab eraldi teha käsuga:

```bash
sudo sh deploy/backup.sh
```

Rollback'i korral peata teenus, säilita praegune DB eraldi, kontrolli valitud
backup'i `PRAGMA quick_check` abil, kopeeri see püsirajale õige omaniku ja
õigustega ning käivita teenus uuesti. Ära kirjuta toimivat DB-d üle enne, kui
backup ja soovitud rakendusversioon on tuvastatud. Rakenduskoodi rollback peab
olema eraldi läbi vaadatud Git ref ja võimalusel fast-forward; skeemimuudatuse
korral on vaja selle versiooni eraldi migratsioonijuhist.

## Taastamine puhtale dropletile

1. Taasta Ubuntu ja turvauuendused vastavalt hosti haldusreeglitele.
2. Lisa meeskonna avalikud SSH võtmed ja tee eespool kirjeldatud teise sessiooni
   kontroll.
3. Paigalda eeltingimused ning Caddy.
4. Taasta DNS ainult pärast uue avaliku IP kinnitamist.
5. Klooni kontrollitud Git ref rajale `/opt/smart-solutions-lab2/app`.
6. Käivita `deploy/install.sh`; see loob service user'i, virtualenv'i ja unit'i.
7. Taasta `/etc/smart-solutions-lab2/env` paroolihaldurist, õigustega `0600`.
8. Taasta kontrollitud SQLite backup rajale `POST_OFFICE_DB`, omanikuks
   `smart-solutions-lab2:smart-solutions-lab2` ja õiguseks `0600`.
9. Paigalda ja valideeri Caddy konfiguratsioon.
10. Sea tulemüür alles pärast SSH ligipääsu kontrolli ning käivita teenused.
11. Käivita `deploy/verify.sh`, kontrolli autentimist ja tee Atomiga päris
    outgoing-polling katse. Dokumenteeri kuupäev ning tegelik tulemus alles siis.

## Uuesti ehitamise märkused 15.11.2026

Serveris töötav commit: vaata `git -C /opt/smart-solutions-lab2/app log --oneline -1`
ja klooni sama ref (`git checkout <commit>`), mitte lihtsalt viimast `main`-i.

Env-faili valikulised võtmed: `CLAIM_LEASE_SECONDS` (vaikimisi 3) ja
`POST_OFFICE_BIND` (vaikimisi `127.0.0.1`).

Käsitsi käivitus ilma systemd-ta (nt testkoopia teises pordis):

```bash
set -a; . /path/to/env; set +a; umask 077
runuser -u smart-solutions-lab2 -- /path/to/venv/bin/gunicorn --workers 2   --bind 127.0.0.1:5099 --access-logfile - --error-logfile - server.wsgi:app
```

Otsast lõpuni kontroll (vaheta port, kasutaja, parool ja Atomi võti):

```bash
B=http://127.0.0.1:5099
curl -s -o /dev/null -w '%{http_code}
' $B/            # 401 ilma paroolita
ID=$(curl -s -u USER:PASS -H 'Content-Type: application/json'   -d '{"job":"letter","arg":{"letter":"A"},"ttl_seconds":120}' $B/api/jobs | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
curl -s -H "Authorization: Bearer ATOM_KEY" -H 'Content-Type: application/json'   -d '{"device_id":"test","poll_interval_ms":1000}' $B/api/atom/poll   # töö tuleb "claimed"
curl -s -H "Authorization: Bearer ATOM_KEY" -H 'Content-Type: application/json'   -d "{\"id\":\"$ID\",\"status\":\"done\",\"result\":{}}" $B/api/atom/result
curl -s -u USER:PASS $B/api/jobs/$ID                    # "status":"done"
```

`install.sh`, `update.sh` ja `verify.sh` kasutavad production'i radu ja porti
5001; testkoopia sammud tehakse käsitsi nagu ülal.

## Kontrollimine ja logid

```bash
sudo sh deploy/verify.sh
sudo systemctl status smart-solutions-lab2 caddy
sudo journalctl -u smart-solutions-lab2 --since today
sudo journalctl -u caddy --since today
```

`verify.sh` kontrollib env-faili õigusi ja placeholder'e, DB kataloogi
omanikku, DB rada ja kirjutatavust service user'ina, systemd/Caddy olekut,
Caddy konfiguratsiooni, localhost health'i, port 5001 loopback-bind'i ning
seadistatud hostinime HTTPS health'i. HTTPS curl ei kasuta `-k` lippu, seega
kontrollib ka sertifikaadi usaldatavust. Mitte-Linux arendusmasinas annab
skript teadlikult `SKIP`, mitte väljamõeldud PASS-i.

Logides võivad olla töö ID, olek, ajatempel ja veakood. Paroole, bearer-võtit,
Authorization päist, SSH privaatvõtit või kogu env-faili ei tohi logida.

### DNS, HTTPS ja välise kliendi kontroll

Enne Caddy reload'i peab õppejõu antud nimi viitama kinnitatud dropletile:

```bash
getent ahostsv4 <HOSTNAME>
getent ahostsv6 <HOSTNAME>
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl --fail --show-error --silent https://<HOSTNAME>/health
```

AAAA kirje tohib olemas olla ainult siis, kui dropleti IPv6 ja UFW on samuti
teadlikult seadistatud. Caddy backend jääb `127.0.0.1:5001`; konfiguratsiooni
ei lisata camera, station'i ega MG400 route'e.

Teisest arvutist kontrolli HTTPS health'i ja kasutajalehte. `curl -u` saab
kasutajanime järel parooli interaktiivselt küsida, nii et parooli ei panda
shelli ajalukku:

```bash
curl --fail --show-error --silent https://<HOSTNAME>/health
curl --fail --show-error --silent --user '<WEB_USERNAME>' \
  https://<HOSTNAME>/api/status
```

Telefonis lülita Wi-Fi välja, ava `https://<HOSTNAME>`, kontrolli brauseri TLS
olekut ja logi sisse. Töö saada ainult siis, kui labori kohalik ohutuskontekst
ja Atom/robot seda päriselt lubavad.

## Atomi production-serverile ümberlülitamine

Alles pärast avaliku HTTPS health'i õnnestumist kontrolli päris hosti
sertifikaadiahelat:

```bash
openssl s_client -connect <HOSTNAME>:443 -servername <HOSTNAME> \
  -verify_return_error </dev/null
```

Võta usaldatud root CA PEM sertifikaadi väljastaja ametlikust allikast ja
pane see lokaalsesse ignoreeritud faili
`firmware/include/post_office_ca_private.h` väärtusena
`POST_OFFICE_ROOT_CA`. Ära vali CA-d oletuse järgi ega kopeeri serveri
leaf-sertifikaati root CA asemele. Seejärel tee PlatformIO build ja upload
eraldi kontrollitud hardware-sammuna. Ilma CA-ta peatab firmware HTTPS
pollingu põhjusega `https_ca_not_configured`.

Pärast CA-ga firmware upload'i:

1. Ava Atomi lokaalne seadistusleht.
2. Sea serveri URL-iks `https://<HOSTNAME>`.
3. Sisesta sama uus `ATOM_API_KEY`, mis on production env-failis.
4. Sea teadlikult valitud polling interval ja käivita üks serveri test.
5. Kontrolli dropletis HTTP 200 pollingut ning lehel `last_seen` uuenemist.
6. Tee reboot ja kinnita seadete püsimine enne katsete jätkamist.

Production firmware kontrollib TLS sertifikaati CA trust store'i või
konfigureeritud CA kaudu; production päringute jaoks ei kasutata
`setInsecure()` käitumist.

## Päris acceptance-testide järjekord

Need on katsejuhised, mitte tehtud tulemused. Iga tulemus märgitakse alles
pärast päris dropleti ja laboririistvaraga katset:

1. Ava leht telefonist mobiilse andmesidega (Wi-Fi väljas) ja kinnita HTTPS.
2. Kinnita Atomi authenticated polling ning `last_seen` uuenemine.
3. Käivita `letter` ainult kohaliku enable'i ja ohutusvaatlejaga.
4. Käivita `pick_place` alles pärast local MG400/pumba implementatsiooni,
   õpetatud positsioonide kontrolli ja 20% esimese jooksu nõude täitmist.
5. Jäta Atom väljalülitatuna töö, oota üle TTL-i ning kinnita, et see aegub ja
   ei põhjusta liikumist.
6. Saada whitelist'i mittekuuluv töö ja kinnita fail-closed refusal.
7. Lülita Atom välja ning mõõda, millal leht muutub stale/offline olekusse.
8. Katkesta ühendus poole lubatud töö ajal; töö peab lokaalselt lõppema ja
   terminaltulemus pärast ühenduse taastumist idempotentselt kohale jõudma.
9. Tee 30 latency katset polling interval A-ga ja 30 interval B-ga, kasutaja
   vajutusest roboti esimese liigutuseni.
10. Täida olemasolevad `docs/latency_poll_fast.csv` ja
    `docs/latency_poll_slow.csv`; ära loo oletuslikke ridu ega dubleeri
    mõõtmistabelit. Arvuta kummagi intervalli keskmine ja maksimum alles
    tegelikest mõõtmistest.

## Päris dropleti päeva TODO

- [x] Nikita sai õppejõult ligipääsuandmed ning kontrollis võtmega SSH login'it
  ja Ubuntu 24.04.5 LTS versiooni 16.10.2026.
- [x] Repo, virtualenv, production-paketid ja systemd teenus on paigaldatud.
- [x] Teenus käivitati käsitsi; Gunicorn kuulas ainult loopback-liidesel,
  `/health` vastas HTTP 200 ja autentimata `/` HTTP 401.
- [x] `smart-solutions-lab2` ja Caddy on `enabled` ning `active` (20.10.2026).
- [ ] Teenuste käivitumine pärast kogu dropleti reboot'i on kontrollitud.
- [x] Raimo kinnitas isiklikult oma võtmega SSH-sisselogimist sudo-õiguseta
  kontole (13.11.2026). [Lab 2 arenduspäevik](../README.md#arenduspäevik)
- [ ] Seni kinnitamata isiklikud SSH-ligipääsud vajavad kontrolli.
- [x] SSH effective config: `pubkeyauthentication yes`,
  `passwordauthentication no`, `kbdinteractiveauthentication no`;
  Nikita sõltumatu login pärast UFW aktiveerimist õnnestus (20.10.2026).
- [x] Domeeni `narva2.roboarena.org` avalik HTTPS ja `/health` vastus on
  välise Maci curl'iga kontrollitud: HTTP/2 200, korrektne TLS (20.10.2026).
- [x] UFW `active`, sissetulevad TCP 22/80/443 lubatud, default `deny incoming`
  (20.10.2026).
- [x] Env-fail on `root:root 0600`, nõutud väärtused on olemas,
  placeholder'id puuduvad ja saladused on repost väljas.
- [x] SQLite fail asub Git checkout'ist väljas püsirajal, õigustega `0600`.
- [x] SQLite backup on loodud (24576 baiti, `root:root 600`) ning taastatud
  eraldi testbaasi: `integrity_check: ok`, töö kirje taastatud (20.10.2026).
- [x] Kasutaja autentimine ja UI töötavad Safari Macis ja Chrome telefonis
  5G kaudu (20.10.2026).
- [x] Päris Atom pollis avalikku postkontorit väljamineva HTTPS-ühendusega
  ja sai oma võtmega vastuse `poll_ok_no_job` (14.11.2026).
- [x] `letter A` loomine, aegumine (`ttl_expired`) ning kirje säilimine teenuse
  restardi järel on päris hostil kontrollitud (20.10.2026).
- [x] Täielik `deploy/verify.sh`: `12 PASS, 0 FAIL, 0 SKIP` (20.10.2026).
- [ ] Station'i, MG400 ja kaamerate poole ei ole dropletil route'i/proxy't.
- [ ] Taasteprotseduur on päriselt läbi proovitud ja tulemus kuupäevaga kirjas.
