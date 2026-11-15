# Jaama püsipuhver ja Atomi välkmälu

## Jaam

1. Enne liikumist reserveerib jaam ruumi tsükli suurima lubatud kirje ja failide jaoks. Ta kirjutab võtme, UTC algusaja ja algseadistuse püsivalt tsüklipäevikusse ning eraldab järgmise numbri samas tehingus.
2. Jaam seob Atomi tulemuse ja mõõtefailid võtmega. Ta kinnitab Atomile sündmuse alles pärast duplikaadikindlat püsisalvestust. Pärast mõõtmiste ja tõendite sidumist lõpetab jaam kirje ning jätab selle koos failiviidete ja kontrollsummadega püsivasse saatmisjärjekorda (`outbox`). Avaldamisvalmis sisu külmutatakse. Taaskäivitus taastab saatmisjärjekorra ja uurib lõpetamata tsüklit. Kahtlase seisuga töö peatub ning läheb kohaliku kontrolli järel sama võtmega `aborted` kirjena edasi, saadaolevad tõendid kaasas. Varem kinnitatud tulemuse põhjal saab lõpetada ainult siis, kui protokolli lõpptingimused on tõendatud.
3. Ühenduse taastumisel jätkab saatja ootel võtmetega, piiratud paralleelsuse ja kasvava kordusvahega. Lae viidatud failid üles enne kirje avaldamist. Samaaegne kordus või kadunud kinnitus ei tekita teist andmebaasirida. Kustuta saatmisjärjekorra kanne alles võtme ja sisuräsiga sobiva rakenduskinnituse järel püsivas tehingus. Hoia kinnitatud andmete jaama arhiivi [taastamisreegli](database.md) järgi.
4. Arvesta mahtu nii baitides kui tsüklites. Hinda piloodis suurim kavandatud tsüklisagedus `R` (tsüklit/min) ja suurim lubatud kirje, pildi ning kõvera kogumaht. Varu vähemalt `ceil(10 × R)` tsüklile ruum, lisaks poolelioleva tsükli ja failisüsteemi varu. Tegelik maht, hoiatuslävi ja katkestuse ajal lubatud töö kinnita pärast inventuuri. Täis puhver või tõendite salvestustõrge blokeerib uue tsükli. Pooleliolev töö läheb kohaliku ohutuskorra järgi seisma, jätab püsiva jälje ja teavitab operaatorit. Vanad kinnitamata kirjed jäävad alles. Edastus võib võrgu taastumisel jätkuda. Liikumine vajab uut luba. [Salvestuskinnitus](mqtt.md#salvestuskinnitus) · [Ohutus](safety.md)

## Atom

- Planeeri Lab 2 AtomS3R-i püsivara olemasolevale välkmälule väike püsiv sündmusjärjekord. `default_8MB.csv` ja LittleFS on olemasoleva projekti lähtepunktid. Kinnita vaba maht, kirjutuskindlus, kulumine ning toitekatkestusest taastumine. [PlatformIO projekt](../../lab2/firmware/platformio.ini)
- Jaam edastab tsüklivõtme enne tsükli algust. Atom seob lõpetava sündmuse võtme ja sündmuse tunnusega. Sündmus on tagatud alates edukast püsikirjutusest ja terviklikkuse kontrollist, mis peab üle elama toitekao. Poolik kirjutus ei kõlba saatmiseks. Atom kirjutab enne saatmist, saadab taaskäivitusest taastunud sündmuse uuesti ja vabastab ruumi pärast jaama püsisalvestuse kinnitust. Taaskäivitunud Atom ei korda füüsilist doseerimist. Jaam eristab seda kinnitust Lab 2 töö vastuvõtukviitungist `station_ack`.
- Kui vool kaob enne püsikirjutust, võivad Atomi RAM-i sündmus ja salvestamata proovid või ajastus kaduda. Jaama eelkande järgi on tsükkel sellegipoolest leitav. Fikseeri katkestus ja puuduva tõendi põhjus, tundmatu mõõtmine jääb tühjaks. Atom annab täitumisest või rikutud kirjest märku. Uus tsükkel vajab enne starti vaba ruumi ka Atomi lõpusündmusele.

## 500 kirje kontroll

Tee eraldi katsekeskkonnas 500 eri võtme ja kontrollsummaga kirje lähtefail. Võimalda vähemalt ühel osal korduda, näiteks katkesta salvestuskinnituse tee pärast tehingut. Hoia sama võtme muudetud sisuga teadlik konflikt eraldi kontrollkatsena ning näita, et algne rida ja failid säilisid. Säilita saatmise, salvestaja ja faili kontrolli logid ilma saladusteta. Katseandmestikus märgi, kas andmed olid sünteetilised või füüsilised. Andmehõive 300 tõendatud päristsüklit on eraldi nõue.

| Näit | Kuidas loendada | Tulemus |
| --- | --- | --- |
| Lähte- ja saadetud võtmed, saatmiskatsed | Võrdle 500 eelregistreeritud võtme loendit avaldatud võtmetega. Loenda kõik avaldamiskatsed eraldi, sh kordused. | TODO |
| Kohale jõudnud ja salvestatud | Loenda kirjutaja vastuvõtud ja andmebaasi eri võtmed. Arvesta faili olemasolu ja räsi. Ootus on 500 algset võtit ning sobiv sisu. | TODO |
| Kaod ja liigsed read | Leia lähte võtmed, millel puudub sobiv püsiv rida või fail. Leia ka võõrad võtmed ja salvestatud kordusread. Ootus on 0 igas kategoorias. | TODO |
| Kordustarned ja konfliktid | Loenda kirjutaja sama võtme ja sisuga kordusvastuvõtud, sama võtme eri sisuga saabumised ning kontrollkatse konfliktid eraldi. | TODO |

## Taastumiskatsed

- **Tunnel 10 minutit maas jooksu ajal.** Lepi ohutu kohalik katseseis kokku ja katkesta tunnel. Pärast taastumist võrdle olekut, ootel ja saadetud võtmeid, korduskatseid, kinnitatud ridu, kadusid ning failiräsisid. Kaasatud liikumine allub kohaliku töövoo ohutusele. Kaugliikumise fail-safe ei kuulu selle andmekatse tõendisse.
- **Atom vooluta tsükli ajal.** Tee ohutus katseseisus eraldi katkestus enne Atomi kirjutust ja pärast edukat kirjutust enne jaama kinnitust. Esimesel juhul oota katkestuskannet koos puuduva tõendiga, teisel sama sündmuse taastumist. Kontrolli võtmeid, ootel/kohale jõudnud kirjeid, kordusvastuvõtte ja andmebaasi duplikaate ning seda, et liigutust ei korratud.
- **Täis puhver ja serveritõrge.** Täida testjärjekord piirini ja kontrolli uue tsükli keeldu ning algsete andmete püsimist. Simuleeri katkestust pärast faili avaldamist ja pärast DB commit'i. Kontrolli kummalgi juhul taastumist ilma teise insert'ita.

Tulemused on TODO. Iga katse juurde lisa kuupäev, katkestushetk, meetod, ootel ja saabunud kirjete ning korduste arv, puuduva sündmuse põhjus ja tõendiviide.
