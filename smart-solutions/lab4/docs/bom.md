# Inventuur ja 27.11.2026 tellimus

Alusta olemasoleva jaama, võrgu ja mõõtevahenditega. Varasema katse tõend näitab kasutatud seadet, selle praegune olek ja vaba maht vajavad inventuuri. Ühtki uut tellimisrida ega kogust pole kinnitatud.

| Ressurss | Mida inventuuris kontrollida | Millal tekib vajadus |
| --- | --- | --- |
| Droplet ja ruuter | Kontrolli vaba ketast ja RAM-i, olemasoleva teenuse koormust, WireGuardi tuge ja eraldi teenuseõigusi. | Kui kõikide meeskondade failid, andmebaas, logid ja varukoopiad ei mahu, arvuta enne otsust vajalik lisamaht. |
| Laborijaam ja ketas | Mõõda suurim piloodi JPEG-i, kõvera ja kirje maht, jaama vaba ketas ning 10 minuti ootejärjekord koos arhiivivaruga. | Jaamaketta lisamaht vaid mõõdetud puudujäägil. [Puhvri valem](buffering.md#jaam) |
| AtomS3R ja sisemine flash | Lab 2 projekt kasutab 8 MB jaotuse lähtekohta. Tuvasta seadme tegelik partitsioon, vaba ruum, flashi kulumisvaru ja ühilduvus. | Otsusta püsisündmuste tegeliku mahu ja toitekatse järgi. Väldi ostu enne flashi kontrolli. |
| USB toite- ja andmekaablid, Ethernet, adapterid, kaamerad | Mõlemad kaamerad töötasid Lab 2 katses. Kontrolli praegused andmekaablid, pingevaba paigutus, ruuteri ja MG400 võrgukaablid, jaama USB-pordid ning Atomi ja XIAO eraldi ühendused. | Kandidaat on puuduva või vigase andmekaabli või adapteri asendus, kui olemasolevaga tekib mõõdetav tõrge või puudu on port. |
| MG400, rakis, klaasid, täiturid ja kaitsevahendid | Kontrolli ühiselt viie klaasi ja hoidikute olemasolu, mõõteahelat, UV-katet ja prille ning eelmistest laboritest saadud osi. | Puudujäägi kohta lepi kokku üks tellija. [Andmehõive BOM](https://github.com/Dennel04/data-acquisition-course/blob/7f31501d26fd59d19f9f19cb2ba3139d2240951b/data-acquisition/lab4/docs/bom.md) · [CAD BOM](https://github.com/Dennel04/3d-printing-course/blob/65747f15f03cb69d176a021d0ccf328f46e56d20/3d-print/lab4/docs/bom.md) · [Lab 3 BOM](../../lab3/docs/bom.md) |
| Kaitsmise vahendid | Kontrolli, kes annab teise meeskonna, stopperi, testkliendi, kaks brauseriseanssi ja VPN-is oleva MCP kliendi. | Kavanda olemasolevate vahenditega. |

Arvuta dropleti maht kõikide meeskondade kirjete arvu ning piloodis mõõdetud kirje, pildi ja kõvera baitide järgi. Lisa SQLite'i indeksid ja WAL, failide ajutine ruum, logid, kooskõlaline varukoopia ning säilitusvaru. Kontrolli RAM-i pilootkoormuses. Jaama, ruuteri ja olemasoleva dropleti võimekus on praegu TODO.

Enne 27.11.2026 kirjuta siia iga kinnitatud puudujääk, kogus, ühilduvus, kasutus, esitaja ja tellimustabelisse kandmise kuupäev. Kui varu katab töö, kinnita kuupäevaga tellimisvajaduse puudumine. [Ühine Moodle'i tellimistabel](https://moodle.ut.ee/mod/url/view.php?id=1535601)
