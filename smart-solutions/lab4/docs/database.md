# Ühine katseandmebaas

**Kavand.** Üks SQLite'i andmebaas dropletil kõigi meeskondade tsüklitele. SQLite'i fail kuulub ühele kirjutajateenusele. See teenus võtab kirjeid vastu Mosquitto kaudu. Volitatud lugejad kasutavad privaatset lugemisteenust VPN-is. SQLite'i failil puudub võrguliides. Avalik Lab 2 postkontor kasutab eraldi baasi, protsessiõigusi ja varukoopiaid.

## Andmed ja indeksid

- `cycles` hoiab ühe rea tsükli kohta. Primaarvõti on muutumatu `(team, station_id, cycle)`. [Andmehõive 27 välja](record.md) jäävad ekspordis samasse järjekorda. Algkirje võrdlemiseks säilita selle kanooniline kuju ja kontrollsumma.
- Piiratud väärtustega rühmitussildid on `team` ja `label`. SQLite'is on need veerud. Vali indeksid päringute järgi, näiteks meeskonna ja tsükliaja vahemik. `cycle`, `station_id`, `run_id`, `cad_config_id`, `workflow_version` ja failiteed jäävad tavaväljadeks või relatsioonilisteks võtmeteks. Aegridade hoidlasse eksportimisel väldi nende automaatset lisamist siltideks.
- Eraldi metaandmetes on esimese vastuvõtu UTC-aeg, salvestamise UTC-aeg, failide pikkused ja SHA-256 ning tarnekatsete ja konfliktide jälg. Salvestamise aeg märgitakse salvestustehingus. Mõlemad ajad erinevad mõistelt väljale `t` kuuluvast tsükli algusajast. Kordus säilitab algsed ajad. Analüüs ja CAD seos lähtuvad tsükli ajast ja võtmest.
- Fotod ja kõverad jäävad failideks, et eksporti ja algmaterjali saaks eraldi kasutada. Volitatud lugeja lahendab suhtelise tee kokkulepitud `data/` juure kaudu. Juurdepääs käib meeskonna ja kokkulepitud rolli järgi.

## Salvestamine ja kinnitus

1. Kirjutaja valideerib skeemi, võtme, teema ja kirjutusõiguse. Sisu võrdlemise reegel fikseeritakse ühiselt, sh arvud, JSON-i `null` ja failiteed.
2. Failiteenus kontrollib lubatud suhtelist teed ja omanikku, pikkust ning SHA-256. Ajutise faili järel avaldab ta kontrollitud faili püsivalt samal failisüsteemil. Sama viite ja räsi kordus on lubatud. Sama tee eri sisuga läheb konflikti. Manifesti korral kontrolli ka selle kaudu viidatavaid nõutud faile. Juba kinnitatud failid on muutumatud.
3. Ühe kirjutaja tehing lisab uue rea ja püsivad failide metaandmed. Kokkulepitud talletusrežiim peab üle elama protsessi ja hosti katkestuse. Lähtevariant on WAL ja `synchronous=FULL` sobival lokaalsel failisüsteemil. [SQLite'i sünkroonimine](https://www.sqlite.org/pragma.html#pragma_synchronous)
4. Sama võtme ja kanoonilise sisuga kordus kontrollib failide olemasolu ja terviklust ning tagastab kinnituse ühele olemasolevale reale. Eri sisu või failiräsi fikseerib kirjutaja eraldi konfliktina. Algne rida jääb puutumata. Rakenduse `stored` kinnitus järgneb kestvale tehingule ja failide kontrollile. Eksporti jõuab ainult salvestatud kirje.
5. Katkestuse järel võib fail olla olemas enne kirjet või kirje enne kinnituse saatmist. Sama sisuga kordus kasutab kontrollitud failid uuesti ja kinnitab olemasoleva rea. Lõpetamata üleslaadimiste koristus arvestab aktiivseid ülekandeid ning kinnitatud ja ootel viiteid. Hilisem mõõteparandus käib versioonitud tõendikandena pärast meeskondade kokkulepet. [Kordussaatmine](buffering.md)

Varunda andmebaasi kooskõlaline tõmmis koos selle failide manifesti ja viidatud algfailidega. Kontrolli taastatud võtmeid ja räsisid isoleeritud keskkonnas. Kuni taastamis- ja säilitusreegel on kokku leppimata, hoia jaama kinnitatud koopiad eraldi arhiivis. Taastamisel võrdle seda arhiivi taastatud baasi ja failidega ning taasta puuduvad kinnitatud kirjed sama võtme ja sisuga. [Mahuarvestus](bom.md)
