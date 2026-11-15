# Lab 2 ohutuskokkuleppe mustand

> See dokument on kokkuleppe mustand. See ei tõenda, et meeskonnaliikmed on
> selle läbi lugenud või et katkestus- ja riistvarakatsed on tehtud.

## Mõisted

- **Postkontor** — dropletis töötav avalik Flask/SQLite server
  (`narva2.roboarena.org`). Sinna saab jätta whitelist'i töö ja vaadata
  tulemust. Postkontor ei ühendu ise robotiga, jaamaga ega Atomiga; Atom käib
  seal ise töid küsimas.
- **Kaugtöö** — internetist postkontorisse saadetud whitelist'i kõrgtaseme töö
  (`letter` või `pick_place`, vt [`server_api.md`](server_api.md#whitelist)).
  Atom võtab töö postkontorist ise vastu ja jaam täidab selle lokaalselt.
- **Vastutaja** — ruumis olev nimetatud meeskonnaliige, kes näeb kogu tööala,
  ulatub füüsilise hädastopini ja lubab roboti lokaalselt.
- **Üldkaamera** — laua üldvaatekaamera, mis näitab kogu robotit ja tööala.
- **Tööriistakaamera** — XIAO kaamera tööriista juures. See näitab ainult
  otsikut ja selle all olevat detaili.
- **Hädastopp** — MG400 aluse füüsiline hädastopi nupp.
- **Lokaalne esmakontroll** — uue tööjada esimene jooks ruumis olles: 20%
  kiirusel, tööriist vähemalt 20 mm tööpinnast kõrgemal, ilma proovitükita.

## Kohustuslikud reeglid

### Kes ja millal tohib kaugtööd käivitada

1. Kaugtööd tohib postkontorisse jätta ainult isikliku autentitud ligipääsuga
   meeskonnaliige ja ainult pärast vastutaja selgesõnalist nõusolekut.
2. Vastutaja on ruumis kogu kaugtöö ajal, näeb kogu tööala ja ulatub
   hädastopini.
3. Kui üldkaamera pilti ei ole või see ei näita kogu tööala, kaugtööd ei
   käivitata. Tööriistakaamera üksi ei ole piisav.
4. Kui ruum on tühi, on robot voolust välja lülitatud. Ainult tarkvaras
   disabled-olek ei ole piisav.

### Roboti lubamine ja peatamine

5. Vastutaja kontrollib tööala ja lubab roboti lokaalselt. Roboti kaugelt
   lubamine (remote enable) on keelatud ja seda funktsiooni ei lisata.
6. Füüsiline hädastopp on ainus usaldatud stop. Veebilehe stop-nupp on ainult
   mugavusfunktsioon.
7. Kui MG400 aluse kaitselüliti rakendub, ei proovita robotit kaugelt uuesti
   käivitada. Vastutaja kontrollib olukorra kohapeal.
8. Robotile saadab liikumiskäske korraga ainult üks programm.

### Mida postkontor vastu võtab

9. Postkontor võtab vastu ainult whitelist'i kõrgtaseme töid. Koordinaate,
   trajektoore, DO käske ja otseseid MG400 käske internetist vastu ei võeta.
10. Töö, mis on aegunud (TTL möödas), tundmatu, vigane või whitelist'i
    mittekuuluv, ei liiguta midagi.

### Uus tööjada

11. Iga uus tööjada läbib enne kaugkasutust lokaalse esmakontrolli.

### Internetikatkestus

12. Kui internet katkeb pärast seda, kui Atom on töö postkontorist vastu võtnud
    ja jaam on selle lokaalselt aktsepteerinud, ei katkestata selle tõttu roboti
    jada:
    - jaam lõpetab juba vastu võetud töö oma kohalike ohutusväravate järgi;
    - Atom säilitab tulemuse ja saadab selle postkontorisse pärast ühenduse
      taastumist.
13. Reegli 12 käitumist kontrollitakse laboris kolm korda enne, kui internetist
    võetakse vastu päris töid.

### Labori 1 reeglid kehtivad edasi

14. Labori 1 MG400 ohutusreeglid kehtivad edasi:
    - käed ei ole 440 mm ulatuses, kuni käsk on ootel;
    - enne iga liikumist öeldakse „liigub“;
    - uus jada käivitatakse esimest korda aeglaselt (vt reegel 11);
    - 24 V pumbakasti DO juhtmeid ühendatakse ainult siis, kui robot on
      disabled ja pumbakast vooluta.

## Võrgu- ja infoturve

- Dropleti postkontori veebiliides kasutab HTTPS-i ja parooli või tugevamat
  autentimist.
- Dropleti tulemüüris on avatud ainult minimaalselt vajalikud pordid ning iga
  pordi otstarve on dokumenteeritud.
- Dropletil puudub võrguühendus robotisse, jaama või Atomisse. Ühendust
  algatab ainult Atom: see teeb postkontori suunas väljaminevaid
  HTTPS-päringuid.
- Kogu välissisendit käsitletakse vaenuliku sisendina: skeem, tüüp, pikkus,
  lubatud märgid ja väärtusvahemik kontrollitakse enne kasutamist.
- Kaameravood jäävad kohalikku võrku. Need ei lähe dropleti postkontorisse,
  postkontor ei proxy neid ja kaamera enda aadress ei ole internetist avatud.
- Atomi autentimisvõtit ei lisata reposse, näidiskonfiguratsiooni ega logisse.
- SSH privaatvõtmeid ei lisata reposse, vestlusse ega e-kirja. Igal arvutil on
  eraldi SSH võti; jagatakse ainult avalikku võtit.
- Atomi vaikimisi Wi-Fi parool vahetatakse enne seadme laborist väljaviimist.

## Kontrollnimekirjad

### Üks kord, enne esimest kaugtööd

- [x] Kolm päriskatset kinnitavad, et internetikatkestus ei katkesta juba
  vastu võetud lokaalset tööd ja puhverdatud tulemus saadetakse hiljem
  (reeglid 12–13). 15.11.26: tähed C, D ja E.
- [ ] Kõik meeskonnaliikmed on kokkuleppe läbi lugenud ja kinnitanud (vt
  allpool).

### Iga uue tööjada eel

- [ ] Uus jada on lokaalse esmakontrolliga ohutult läbi tehtud (reegel 11).

### Iga kaugkäivituse eel

- [ ] Vastutaja on nimetatud ja on hädastopi juures.
- [ ] Vastutaja on roboti lokaalselt lubanud.
- [ ] Kogu robot ja tööala on üldkaameras nähtav.
- [ ] Töö ID, whitelist'i tüüp, argument ja TTL on kontrollitud.
- [ ] Jaama ohutusvärav (safety gate) kinnitab, et robot on ühendatud, lubatud,
  veata ja ei täida teist tööd.
- [ ] Sama töö ID ei ole juba täitmisel ega lõpetatud.

## Meeskonna kinnitus

Iga liige lisab oma kinnituse ise pärast kokkuleppe päriselt läbilugemist.

| Nimi | Kuupäev | Kinnitus |
| :--- | :--- | :--- |
| Nikita | TODO | TODO — kinnitab isiklikult pärast läbilugemist |
| Denys | 15.11.26 | Läbi loetud ja kinnitatud |
| Raimo | TODO | TODO — kinnitab isiklikult pärast läbilugemist |
| Maksim | TODO | TODO — kinnitab isiklikult pärast läbilugemist |
