# Nutikad Lahendused · Labor 4 — Ühine andmebaas ja töövoo salvestaja

**Tellimine** 27.11.2026 · **Esimene kaitsmine** 10.12.2026 veebis

Jaam saadab ühe kirje tsükli kohta kõigi meeskondade ühisesse andmebaasi. Operaator õpetab jaama lehel poosid ja tegevused, salvestab töövoo JSON-i ja saab selle sama jaama kaudu uuesti läbi mängida. Üks operaator juhib robotit. Vaatlejad ja MCP klient saavad ainult lugeda.

[Õppejõu täielik ülesanne](https://github.com/KKallas/Narva-subjects/blob/main/EST/2026-27/Smart%20Solutions/Smart%20Solutions%20%5BLab%204%5D%20EST.md) · [Ametlik kokkuvõte](https://github.com/KKallas/Narva-subjects/blob/main/EST/2026-27/Smart%20Solutions/Smart%20Solutions%20%5BLabor%204%20kokkuv%C3%B5te%5D%20EST.md)

## Seis 15.11.2026

Valmis on dokumentatsiooni kavand. [Andmehõive 27-väljaline kirje](docs/record.md) on **PROPOSED**. [CAD-i kandidaat ja vahetuslogi](docs/integration.md#cad-i-vahetus) on ettepanekud. Lab 4 teenuste, püsivara ja töövoo rakendus ning kõik Lab 4 vastuvõtukatsed on ootel.

Lab 2 tõend näitab avalikku `letter A` ahelat, mõlemat `display_image` tööd, tõrjutud käske ja aegunud tööd, Atomi `stale/offline` olekut, kolme Wi-Fi taastumist ning mõlemat kohalikku kaamerat. Lab 3 WireGuardi, fail-safe'i, UV ja klapi katsed ning Lab 4 MQTT katsed on lahtised. [Lab 2 tõendid 15.11](https://github.com/Dennel04/smart-solutions-course/blob/3d3743326901ca48b8f9d1868fce8b4ed3d90f69/smart-solutions/lab2/README.md#praegune-seis-15112026) · [Lab 3](../lab3/README.md)

## Kontrollnimekiri

Punktid on õppejõu täisteksti järjekorras. Lisa täidetud punkti juurde kuupäev, arvud ühikutega ja tõendiviide.

| Nr | Nõue | Seis ja tõend või TODO |
| --- | --- | --- |
| 1 | Andmehõive ja kõik meeskonnad kinnitavad kirje kuju, välja ühiku ja päritolu. | [27 välja](docs/record.md) on kirjas. Ühine kinnitus ja versioon on TODO. |
| 2 | Ühine dropleti andmebaas ainult tunnelis, meeskonnal oma konto ja õigus ainult oma kirjetele. | [MQTT kontod ja ACL](docs/mqtt.md) ning [andmebaas](docs/database.md) on kavandatud. Paigaldus, tunnel ja õiguste katse on TODO. |
| 3 | Jaam saadab iga tsükli ja droplet salvestab selle õige meeskonnatunnusega. | [Andmetee ja salvestuskinnitus](docs/mqtt.md#salvestuskinnitus). Rakendus ja otsast lõpuni tõend on TODO. |
| 4 | 500 kirje puhul on teada saadetud, saabunud ja topelt kirjete arv. Kaod 0. | [Loendusmeetod](docs/buffering.md#500-kirje-kontroll). Mõõtearvud ja logid on TODO. |
| 5 | Jooksu keskel katkeb tunnel ja teises katses Atomi toide. Ootel kirjed saabuvad ilma topeltreata. | [10 minuti ja Atomi toite katsed](docs/buffering.md#taastumiskatsed). Püsipuhvrite rakendus ja katsed on TODO. |
| 6 | Jaama lehel saab õpetada punkti ja tegevust, salvestada ning mängida. Töövoog on repo JSON. | [Failikuju](docs/workflow.md) ja [töövoofailide kaust](workflows/README.md). Salvestaja ja õpetatud fail on TODO. |
| 7 | Sama töövoog mängib 20 korda järjest sama tulemusega. | [Katseplaan](docs/workflow.md#töövoo-katsed). 20 kordust ja kõrvalekalded on TODO. |
| 8 | Üks kasutaja juhib, teine vaatleb. Luku vabastamise kord on kirjas ja katsetatud. | [Reeglid ja kahe brauseri katse](docs/operator_lock.md). Lüüs ja katsed on TODO. |
| 9 | Jaamas on neli lugemistööriista, vaikimisi kinni, salajase lingi ja automaatsulgemisega. Kutsed logis. | [MCP kavand](docs/mcp.md). Klienditugi, rakendus ja logitõendid on TODO. |
| 10 | Keelatud kutse ja kinnine ligipääs vastavad arusaadava lausega. | [Vastusetekst ja kontroll](docs/mcp.md#ligipääs-ja-keeldumine). Mõlemad katsed on TODO. |
| 11 | Agent vastab ainult lingi kaudu kolmele küsimusele. Vastused ja kutseloendus on kirjas. | [Küsimused ja võrdlus](docs/mcp.md#vastuvõtukatse). Vastused ja kutsete arv on TODO. |
| 12 | Teine meeskond salvestab ja mängib töövoo läbi alla 5 minuti, kõrvalise abita. | [Ajavõtt ja märkmed](docs/workflow.md#töövoo-katsed). Meeskond, aeg ja tagasiside on TODO. |
| 13 | Lab 3 ohutuskokkulepe täpsustab, kes tohib töövoogu kaugelt käivitada. | [Lab 4 täiendus](docs/safety.md) on kirjas. Isiklikud kinnitused ja kaugkäivituse eeltingimused on TODO. |
| 14 | 27.11 tellimus on `docs/bom.md`-s. | [Inventuur ja tellimuse tööleht](docs/bom.md). Riiuli- ja serverikontroll ning tellimus või nullvajaduse kinnitus on TODO. |
| 15 | Repo, arenduspäevik ja tag `smart-solutions-lab4`. | Dokumentatsioon ja päeviku jaotis on olemas. Meeskonna töökanded, rakendus, tõendid ja esitamise tag on TODO. |

## Tööfailid

- [Arhitektuur ja skeem](docs/architecture.md) · [Kursuste integratsioon ja lähterevisjonid](docs/integration.md)
- [Kirje](docs/record.md) · [MQTT](docs/mqtt.md) · [Andmebaas](docs/database.md) · [Püsipuhver ja kaoloendus](docs/buffering.md)
- [Töövoo JSON ja valideerimine](docs/workflow.md) · [Töövoofailide kaust](workflows/README.md) · [Operaatorilukk](docs/operator_lock.md)
- [Lugemiseks mõeldud MCP](docs/mcp.md) · [Ohutuskokkulepe](docs/safety.md) · [Inventuur ja tellimus](docs/bom.md)

## Tööjärjekord

1. **Kodus.** Kinnita ühine kirje, failitõendid, MQTT kinnitus, CAD-i sidumine ja töövoo piirid. Vaata üle üks lüüs ja MCP kliendi protokolliversioon. Järgmises etapis teosta ning katseta isoleeritult salvestust, kordusi, täis puhvrit, käsuõigust ja lugemisliidest.
2. **Laboris.** Tee inventuur ja vormista 27.11 tellimus. Kontrolli Lab 3 võrku ja ohutust, jaama ühendusi, flashi, kalibratsiooni ja viie klaasi paigutust. Käivita uus töövoog esmalt lokaalsel 20% kuivkäigul. Kogu 500 kirje loendus, kaks katkestuskatset, 20 kordust, luku-, MCP- ja teise meeskonna katse. Kaugkäivitus eeldab [ohutuskokkuleppe](docs/safety.md) kinnitamist ja kohalikke tõendeid.
3. **Esitamisel.** Seo tulemused kontrollnimekirjaga. Lisa kuupäevad, tegelikult kasutatud vahendid, tõendid ja lahtise töö põhjused. Tee esitamise tag, kui repo ja päevik on valmis.

## Kaitsmise ettevalmistus

Planeeri 15 minutit. Näita skeemil avaliku postkontori ja privaatse salvestustee piiri. Lase õppejõul töövoog ise salvestada ja läbi mängida. Näita ohutus katseseisus tunneli katkestust ning võtmete ja loenduse vastavust pärast taastumist. Proovi operaatorilukku kahes brauseris. Ava ajutine MCP link ja lase agendil vastata õppejõu küsimusele. Hoia käepärast 20 korduse logi, teise meeskonna ajavõtt, ohutuskinnitused ja arenduspäevik.

Esitamiseks lisa Git-repo link ja tag `smart-solutions-lab4`. Pane valmis töötavad lähtefailid ja püsivara, paroolideta teenuseseadistuse kirjeldus, JSON-töövood ning katsetõendid. Dokumentatsioonis on praegu ainult nende alus.

## Arenduspäevik

Lisa pärast iga töösessiooni uus kanne. Meeskond märgib kuupäeva, osalejad, tegevuse, tõendid koos mõõtarvude ja ühikutega ning lahtise järgmise sammu.

**15.11.2026 · dokumentatsiooni ettevalmistus**

Codex võrdles õppejõu 15 kontrollpunkti kolme kursuse repodega ja sidus Lab 4 kavandi Andmehõive kirje ning CAD-i vahetuslogiga. Meeskonna kinnitused, rakendus ja mõõteread lisanduvad pärast asjaomaseid töid ja katseid.
