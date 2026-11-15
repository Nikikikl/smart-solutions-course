# Ühine tsüklikirje

**PROPOSED.** Alus on Andmehõive 27-väljaline ettepanek. Andmehõive, Nutikad Lahendused ja kõik osalevad meeskonnad kinnitavad kuju enne esimest päristsüklit ning lukustavad kinnitatud versiooni pärast kaitsmist Labori 5 jaoks. [Andmehõive põhileping](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/docs/record.md) · [CSV päis](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/data/cycles.csv)

## Väljad CSV järjekorras

Liik „silt“ tähistab piiratud väärtustega rühmitustunnust. „Väli“ hõlmab siin ka aega, viiteid ja võtmetunnuseid. Säilitamise ja indekseerimise plaan on [andmebaasi kirjelduses](database.md).

| Väli | Tüüp või ühik | Päritolu ja tähendus | Liik |
| --- | --- | --- | --- |
| `cycle` | Positiivne täisarv | Jaam eraldab püsiva järgmise numbri enne käivitust. | Väli, võti |
| `team` | Tunnus | Püsiv meeskonnatunnus, mida server võrdleb saatja õigusega. | Silt, võti |
| `t` | ISO 8601, UTC `Z` | Tsükli algusaeg jaama kellalt. | Väli |
| `tip` | mm | Otsiku nimiläbimõõt tootja märgistusest. Täpne tüüp ja tunnus jäävad seansi logisse. | Väli |
| `pressure_kpa` | kPa atmosfääri suhtes | Kalibreeritud anduri keskmine doseerimiseelse seadehetke kokkulepitud aknas. Seanss fikseerib akna, asukoha, rõhu märgi ja kalibratsiooni. | Väli |
| `pulse_ms` | ms | Atomile antud doseerimisimpulsi käsk. Mähise mõõdetud impulsi tõend jääb eraldi mõõtefaili. | Väli |
| `drop_area_mm2` | mm², mõõtmisvea korral tühi | Kaamerasegmendi pindala seansi mõõtkavas. Null kehtib kontrollitud laiguta kvaliteetse kaadri korral. | Väli |
| `drop_target_mm2` | mm² | Katseplaani sihtpindala, ka püsiretsepti võrdluses. | Väli |
| `label` | `normal`, `blocked`, `empty` | Kinnitatud olukord. Lahtise või katkenud tsükli kinnitamata märgend võib olla tühi. | Silt |
| `label_source` | `human`, `image`, `scale` | Olukorra tuvastamise peamine viis. Tõend ja vastuolud lähevad `label_ref` või `note` väljale. | Väli |
| `syringe_g` | g, kaalumata tsüklil tühi | Süstla mass vahetult pärast tsüklit. Aeg ja fikseeritud koostis on seansi tõendis. | Väli |
| `curve` | Suhteline failitee | Jaama toorproovid ja kehtiva kalibratsiooni korral kalibreeritud rõhk. | Väli |
| `image` | Suhteline failitee | Algne tööriistakaamera fail või kaadri manifest. | Väli |
| `schema_version` | Tunnus | Osapoolte kinnitatud kirjekuju versioon. | Väli |
| `station_id` | Tunnus | Andmeid salvestava jaama püsitunnus. | Väli, võti |
| `run_id` | Tunnus | Seanss, mis seob retsepti, katseplaani ja kalibratsioonid. | Väli |
| `run_cycle` | Positiivne täisarv | Tsükli järjekord seerias. Kaalumissammu määrab katseplaan. | Väli |
| `series` | `pilot`, `dataset`, `comparison`, `recovery`, `verification` | Katseplaani põhiseeria. | Väli |
| `mode` | `recipe`, `feedback`, `model_feedback`, tühi | Aktiivne juhtimisviis. Juhuslikustatud avatud juhtimisel jääb tühjaks ja seaded tulevad katseplaanist. | Väli |
| `pressure_setpoint_kpa` | kPa atmosfääri suhtes | Katseseadistus või juhtimise siht. Mõõdetud väärtus on `pressure_kpa`. | Väli |
| `measurement_status` | `measured`, `no_drop`, `not_measured` | Pilditöötluse tulemus. `no_drop` vajab kasutuskõlblikku kaadrit ja lisakontrolli, `not_measured` põhjust. | Väli |
| `label_ref` | Tõendiviide | Kontrollpilt, vaatlus või kaalumiskanne koos tuvastamise alusega. | Väli |
| `cad_config_id` | Tunnus | Seansi metaandmete viide detailiversioonile, paigutusele, tööriistale, kaamerale ja kalibratsioonile. | Väli |
| `workflow_version` | Tunnus | Nutikate Lahenduste töövoo versioon või commit. | Väli |
| `cycle_status` | `completed`, `aborted` | Jaama lõppseis protokolli järgi. Kavandatud veakatse võib lõppeda kontrollitud väljalülitusega. Katkestus säilitab võtme ja põhjuse. | Väli |
| `duration_s` | s | Kestus algusest lõpuni või katkestuseni jaama monotoonsel kellal. | Väli |
| `note` | Tekst, vajadusel tühi | Puuduva väärtuse põhjus, katkestus, erand või tõendite vastuolu. | Väli |

## Identiteet ja failiviited

- Püsiv võti on ettepanekus `(team, station_id, cycle)`. Jaam salvestab numbri enne käivitust ja jätkab numeratsiooni üle taaskäivituste. Katkestus ja kordussaatmine säilitavad sama võtme. Jaama asendamisel või varukoopia taastamisel kontrolli numeratsiooni või võta kasutusele uus jaamatunnus.
- CSV on UTF-8, komaeraldaja ja punktiga kümnendmärk. CSV tühi väärtus vastab JSON-is `null`-ile. Puuduv mõõtmine jääb tühjaks. `no_drop` ja nullpind eeldavad kvaliteetset kaadrit ning lisakontrolli. Laiguta pilt üksi ei erista ummistust tühjast süstlast.
- `curve` ja `image` on suhtelised `data/` kaustast. Lähtefailide nimemustrid on `curves/<team>/<station_id>/<cycle>.csv` ja `images/<team>/<station_id>/<cycle>.jpg`. Säilita algfailid muutmata ja viita olemasolevale failile või kinnitatud salvestusviitele. Kõveras säilivad proovijärjestus, `t_ms`, ADC kood ning kalibreeritud `p_kpa` või tühi väli. Kehtivad [põhilepingu kvaliteedi- ja failireeglid](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/docs/record.md#identiteet-failid-ja-kvaliteet).
- Jaam jätab iga alustatud tsükli jälje alles. Võimalusel kinnita olukord tõendiga enne avaldamist. Sama võtme kordussaatmine kasutab sama sisu. Pärast avaldamist lisa tõendiga paranduskande viide kokkulepitud korras. [Andmestiku arvestus](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/docs/experiment_plan.md#labori-5-andmeseeria) · [Salvestus ja parandused](database.md)

## Kooskõlastus enne esimest päristsüklit

Kinnita nimed ja järjekord, ühikud ja tühjad väärtused, võti ja UTC, rõhuaken ja märgikonventsioon, tõendid ja failide lugemisõigus, `cad_config_id` ning paranduste, MQTT ja salvestuskinnituse kord. Täpsusta katkestatud tsükli kõigi kättesaamatute andmete `null`-reegel, kui tõend või tegelik kestus puudub. Ühtegi uut kirjevälja pole ette pandud. Kinnitajaid, kuupäeva, versiooni ja lukustamise kuupäeva täidavad osapooled pärast kokkulepet.
