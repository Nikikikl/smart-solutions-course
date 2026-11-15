# Töövoo salvestaja

**Kavand.** Jaama lehel võtab operaator juhtimise, avab tööriistakaamera, liigutab Jogiga ja salvestab lüüsist loetud värske poosi nimega. Ta lisab sammud, salvestab nime ja versiooniga JSON-i ning vaatab sammud ja ühikud enne „Mängi“ käsku üle. Kasuta Lab 1 punktide õpetamise ja CAD Hubi Jog/Pickeri liideseid [ühise lüüsi kaudu](operator_lock.md). Salvesta fail uue versioonina, sh koordinaadiraam, paigutuse ja kalibratsiooni viited. [Töövoofailide kaust](../workflows/README.md)

## Faili kuju

Järgnev JSON on süntaktiline näide. `example-*` viited on sünteetilised ja pärisjaamas tundmatud. `poses` väärtuste järjekord on `[X, Y, Z, R]`, kolm esimest millimeetrites ja `R` kraadides. Raam ning tööriist määravad, mida väärtused tähendavad. Iga samm teeb ühe tegevuse. `move` viib nimega poosi, protsessitoiming nõuab sobivas poosis kinnitatud seisakut.

```json
{
  "name": "example",
  "version": "1",
  "speed_pct": 20,
  "frame_id": "example-frame",
  "layout_ref": "example-layout",
  "cad_config_id": "example-cad",
  "calibration_id": "example-calibration",
  "poses": {
    "example-safe": [0, 0, 0, 0]
  },
  "steps": [
    {"action": "move", "pose": "example-safe"},
    {"action": "suction_on"},
    {"action": "suction_off"},
    {"action": "dispense", "ms": 1},
    {"action": "cure", "s": 1},
    {"action": "blow"},
    {"action": "wait", "ms": 1}
  ]
}
```

`move` kasutab olemasoleva poosi nime. `suction_on`, `suction_off` ja `blow` kutsuvad esile eraldi lubatud täituritoimingu. `dispense` ja `wait` võtavad positiivse `ms` väärtuse, `cure` positiivse `s` väärtuse. Puhumise ning vaakumi kasutuse piirid tulevad kohalikust kinnitatud täituriprofiilist. Kirjesse läheb `workflow_version`. Jaam seob selle konkreetse nime ja muutumatu versiooni või commit'iga.

## Valideerimine enne käivitust ja sammu ajal

- Kontrolli võtmeid, tüüpe, sammude arvu, lubatud tegevusi, aega ja kiiruspiire. Tagasi lükatakse tundmatu või topelt võti, määramata poos, vigane ühik või mittemõõdetav piir. Kasuta Andmehõive kinnitatud doosi- ja UV-piire. Puuduva kokkuleppe puhul on vastav toiming blokeeritud.
- Kontrolli versioone, kalibratsiooni kehtivust, tööriista nihkeid, liigesepiire, tööala ja kogu trajektoori, sh lähenemist ning taganemist. Vale kõrgus, kokkupõrke kahtlus või sobimatu tegevuspoos peatab töö enne esimest sammu. Mudeli eelkontrollile järgneb kohalik kuivkäik.
- Kinnita täitmise ajal värske päris tagasiside, sh haare, vabastus ja seisak seal, kus protokoll neid eeldab. Ebaselge samm peatab jada. Uuesti saatmine ei korda füüsilist toimingut.
- `cure` vajab kohalikku käivitust ja UV-luba. Kogu `cure` sammuga töövoog on kohalik. UV puhul kontrolli 405 nm kaitseprille, läbipaistmatut katet ja sõltumatut Atomi taimerit. Uue versiooni esimene käik on kohalik 20% kuivkäik tööriistaga vähemalt 20 mm üle pinna, ilma proovitükita ja inimesega füüsilise hädastopi juures. [Ohutus](safety.md)

## Andmehõive viie klaasi ringlus

Andmehõive mõõtetsüklis doseeritakse tilgaplaadile, tehakse pilt ja mõõdetakse, seejärel liigub üks klaas ilma liimita sisendist väljundisse. Pärast viie klaasi ülekandmist vahetab jaam hoidikute loogilised rollid. Kontrolli mõlema suuna poose ja tegelikku viiendat kohta koos CAD-iga. Senine nelja pesa paigutus on lähtepunkt. Jaam hoiab rollid ja hõivatuse seansi olekus, kinnitab ülekande enne loenduri või rolli muutmist ning peatub pärast katkenud või ebaselget haaret kuni kohapeal üle loetakse. Võtme, failide ja mõõtmiste sidumine jääb püsivaks ka katkestuse korral. [Andmehõive tsükkel](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/docs/experiment_plan.md#automaatne-tsükkel) · [CAD sidumine](integration.md#cad-i-vahetus)

## Töövoo katsed

- Sama kinnitatud versioon 20 korda järjest. Fikseeri eelnevalt oodatud lõpptulemus ja tolerantsid. Talleta iga tsükli võti, kestus, tegelik lõppolek, kõrvalekalded ning esimese jooksu tõrked. Võrdle lähteseisusid ja CAD konfiguratsiooni. Tulemused on TODO.
- Teine meeskond õpetab ilma meie selgituste või abita klaasi viimise teise hoidikusse, salvestab ja mängib töövoo läbi. Mõõda aeg esimesest tegevusest eduka esituseni, siht on alla 5 minuti. Kohalik ohutusvastutaja jääb hädastopi juurde ja võib katse katkestada. Pane kirja meeskond, aeg, takerdumised ja parandused enne järgmist kordust. Tulemused on TODO.
