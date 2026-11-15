# MCP lugemisliides

**Kavand.** Jaam pakub nelja tööriista. MCP protsessil on ligipääs ainult lubatud jaama lugemisvaadetele. See protsess ei saa lüüsi, Atomi täitureid, robotiühendust, MQTT kirjutajat ega failisüsteemi üldliidest kasutada.

## Protokoll

Rakenduse lähteversioon on MCP `2025-11-25`, JSON-RPC 2.0 ja Streamable HTTP ühel Flaski aadressil. Enne teostust kinnita selle versiooni tugi valitud kliendis ning vaata selle versiooni spetsifikatsioon uuesti üle. [Elutsükkel](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) · [Transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [Tööriistad](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

1. Klient saadab `initialize` koos `protocolVersion`, `capabilities` ja `clientInfo` väljadega. Jaam vastab sama päringu ID-ga, lepitud versiooni, `serverInfo` ja `tools` võimekusega. Sobimatu versiooni puhul ei jätkata tööriistakutsetega.
2. Klient saadab `notifications/initialized` teate ilma ID-ta. Eduka teate HTTP vastus on 202 tühja sisuga. Edasised päringud kannavad kokkulepitud `MCP-Protocol-Version` päist. Kui server annab `Mcp-Session-Id`, peab klient seda edasi kandma ja server seob selle sama lingi elueaga.
3. Klient leiab tööriistad `tools/list` kaudu koos `inputSchema` kirjeldustega ja kasutab `tools/call` päringut. Jaam kontrollib sisendit ning tagastab sama ID-ga `result.content` või nõuetekohase JSON-RPC protokollivea. POST kliendi `Accept` lubab JSON-i ja SSE-d. Esimene variant vastab päringule `application/json` vormingus. GET tagastab 405, kui eraldi SSE voogu ei pakuta.

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {"name": "look", "arguments": {"camera": "table"}}
}
```

## Tööriistad ja lubatud lugemisrajad

| Tööriist | Sisend ja väljund |
| --- | --- |
| `guide()` | Tühi objekt. Tagastab alloleva juhise ja lubatud lugemisteed. |
| `status()` | Tühi objekt. Roboti side ja oleku värskus, aktiivne operaator, tänaste salvestatud tsüklite arv, sh katkestatud tsüklite osakaal, ning `blocked` märgendite arv, viimane salvestatud kirje koos tsükli ja vastuvõtu ajaga ning ligipääsu järelejäänud aeg. Jaama kalender kasutab Europe/Tallinn ajavööndit, kirje säilitab UTC. |
| `look(camera)` | Ainult `table` või `tool`. Üks lubatud värske JPEG-kaader vastuses `type: image`, base64 `data` ja `mimeType: image/jpeg`. Puuduva või aegunud pildi korral tagasta selgitus. |
| `api(path)` | Üks täpne lubatud tee. Ainult sisemine GET ja filtreeritud vastus, isegi kui mõnel muul marsruudil oleks samuti GET. |

`api` lubatud teede ettepanek on jaama `/health` ja kaameraserveri `/api/cameras`, pärast vastuseväljade ülevaatust. `look` kasutab jaama kaameraserveri `/snapshot/<name>.jpg` sisemist fikseeritud vastendust. Täpsed vastendused kinnitatakse tarkvarakatses. Jäta vastusest välja aadressid, failiteed, võtmed ja toorlogid. Tõkesta päringuparameetrid, täielikud URL-id, ümbersuunamised ja kõik lubatud loendist kõrvalekalduvad teed. Kasuta olemasolevaid lugemiskäsitlejaid läbi kontrollitud sisemise vastenduse. [Jaama marsruudid](../../lab1/src/station.py) · [Kaameraserver](../../lab2/src/camera_server.py)

`guide()` tekst:

> Alusta tööriistast status. Küsi kaamerakaadrit tööriistaga look ning vali table või tool. Tööriist api loeb ainult juhises loetletud jaama teid. Kasuta kuvatud aega ja värskust ning ütle, kui pildil või seisus pole vastuse jaoks piisavalt infot. Selle lingiga saab jaama ainult vaadelda.

## Ligipääs ja keeldumine

Vaikimisi on ligipääs kinni. Kohalik operaator avab jaama lehel ühe raskesti äraarvatava ajutise HTTPS-lingi ainult VPN-is. Link on võtmena käsitletav saladus. Uue lingi loomine või sulgemine tühistab vana lingi ja seansid kohe. Katseseadistuseks kavanda 5 minutit tegevusetust ja 15 minuti absoluutpiir. Kinnita väärtused ja sobivus kliendiga. Kontrolli `Origin` päist, piira päringute arvu, suurust ja kestust ning rakenda õiguse kontroll igal kutsel. Jäta link ja tunnus puhverserveri ning rakenduse logidest välja. Ära lisa linki reposse ega vestlusse.

Kinnise või aegunud lingi MCP päring saab kliendile loetava lause „MCP ligipääs on suletud. Palu jaama kohalikul operaatoril avada uus link.“ `initialize` puhul lisa lause JSON-RPC veateatesse. Kinnises olekus ei avalda server tööriistaloendit ega jaama andmeid. Keelatud argument või marsruut `tools/call` päringus annab tööriista tulemuse `isError: true` ja lause „Seda teed ei saa MCP kaudu lugeda. Kasuta juhises lubatud vaateid.“ Tundmatu tööriista ja vigase protokollisõnumi korral kasuta JSON-RPC veavormingut koos arusaadava tekstiga.

Logi UTC aeg, tööriista nimi, piiratud ja puhastatud argumendid, tulemus ja keeldumise põhjus. Hoia pildid, URL-i saladus ja isikuandmed logidest väljas. Lepi kokku kaamerate lubatud vaateväli ja ligipääsu logi säilitusaeg. [Ohutus](safety.md)

## Vastuvõtukatse

Anna valitud agendile ainult ajutine link. Küsi:

1. Mitu tsüklit tehti täna ja mitu neist olid `blocked`?
2. Kas sisendhoidikus on klaas?
3. Mis kell tuli viimane kirje?

Võrdle vastuseid andmebaasi päringu ja kaadri sõltumatu vaatlusega. Lisa iga küsimuse juurde oodatud ja saadud vastus, tõend ning tööriistakutsete arv. Katseta ligipääsu kinni, aegunud ja pööratud lingiga, keelatud kirjutusrada, tundmatut tööriista ja piiramata URL-i. Kontrolli, et ükski kutse ei muutnud seadme olekut, töövoogu ega katseandmeid. Vastused, kutseloendus ja logitõend on TODO.
