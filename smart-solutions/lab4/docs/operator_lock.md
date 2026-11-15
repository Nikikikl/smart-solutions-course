# Operaatorilukk ja ühine MG400 lüüs

**Kavand.** Jaam kuvab aktiivset operaatorit ja töö olekut. Üks autenditud operaator saab juhtimisseansi, teised on vaatlejad. Lukk kehtib jaamas serveripoolselt kõigil käsuradadel ning lüüsis vahetult enne füüsilise käsu saatmist. [Lab 2 omanikumudel](../../lab2/docs/ownership_gateway.md) · [Olemasolevate liideste võrdlus](integration.md#juhtimisliideste-võrdlus)

## Seanss, tööluba ja taastumine

| Kiht | Reegel |
| --- | --- |
| Kasutajaliidese lease | „Võtan juhtimise“ taotleb atomaarset õigust isiklikule sessioonile. Aktiivne leht uuendab lease'i aegunud sessiooni ülevõtuta. Esialgne katseseadistus on 30 s, uuendus iga 5 s, et lühike võrguviivitus ei vahetaks omanikku. Kinnita väärtused laboris. Lease mõõdab seansi elusolekut. Jog-jätkuteatel ja töö lõpetamisel on eraldi ohutuse ajapiirid. |
| Füüsilise töö luba | Kohalikult kinnitatud lüüs seob operaatori, sessiooni, tervikliku töö, plaani ja kehtiva fencing-tunnuse. Üks serialiseeritud kirjutaja hoiab luba tervikjada lõpuni ning kontrollib iga sammu eel omanikku, kehtivust, plaani ja värsket tagasisidet. |
| Recovery | Lease'i aegumine või „Loobun“ tühistab uued käsud. Liikumise ajal või teadmata olekus viib lüüs süsteemi `UNCERTAIN` olekusse ja eemaldab saatmata vana järjekorra. Ainult kohalik kontroll saab kinnitada seisaku, tühja käsujärjekorra, ohutu väljundite seisu ja vigade puudumise. Seejärel vabastab operaator luku ning järgmine töö vajab uut luba. |

Võta prototüübist üle olekud `BLOCKED → FREE → RESERVED → ACTIVE` ja `UNCERTAIN`, püsiv fencing/epoch, sammu eelregistreerimine ning lõpetamise tõendid. Aktiivse rikke järel jõuab süsteem `FREE` olekusse ainult kontrollitud taastamise kaudu. Prototüüp kasutab sünteetilisi kinnitusi, `physical_execution_allowed=False` ja SQLite'i. Seda tuleb täiendada päris tagasiside, autentimise, OS-i ühe protsessi kaitse ja sõltumatu watchdog'iga. Taaskäivitus blokeerib juhtimise. Lingi taastumine tühistatud tööd ei jätka. Juba kontrollerile saadetud käsk võib jätkuda, mistõttu tokeni vahetus üksi ei tõenda seisakut. [Lab 3 katkestusreegel](../../lab3/docs/safety.md#vpn-i-kadumine-liikumisel)

## Üks ühenduse omanik

Lähtevariant on olemasoleva mg400-base'i kohaliku ühenduse omaniku laiendamine üheks lüüsiks pärast tehnilist ülevaatust. Lab 1 klient, Lab 2 adapteri töö, CAD Hubi Jog ja Picker, mg400-base'i UI/CLI ning töövoog läbivad sama käsujärjekorra. CAD-i Real-backend vajab lüüsi klienti. Simulatsiooni võib hoida eraldi. Real-režiim võib taastuda Hubi salvestatud seadest ja proovida kohe robotiga ühendust. Keela sõltumatud Real-protsessid enne päris töö alustamist. Hubi Motion Lock jääb kohalikuks lisaväravaks.

Kontrolli kõiki olekut muutvaid radasid, sh jog, move, teach/salvesta, recall, töövoo käivitus, pumba- ja DO-käsud, Atomile minevad täiturikäsud, kiirus, ühendamine, enable/disable ja veast taastumine. Avalikust postkontorist pärit lubatud Lab 2 töö liigub kohaliku loa kontrolli. Sündmuste edastus ja vaatlus käivad eraldi. Tarkvaralisel Stopil on ohutuskorras määratud eelisjärjekord. Füüsiline hädastopp jääb töö ajal käeulatusse.

Piira roboti juhtimisvõrgu ligipääs lüüsi hostile ja selle hosti juhtimisõigus lüüsi teenusele. OS-i eluealukk peab toimima enne TCP ühenduste või adapteri tööandmebaasi avamist. Kaitse kehtib alles siis, kui katsed kinnitavad otseühenduse kõrvalteede tõkestamist, vana epoch’i kehtetust, ohutut taaskäivitust ja kõigi käsuradade kontrolli. [Ühe lüüsi lähteplaan](../../lab2/docs/ownership_gateway.md#üks-päris-gateway-vajalikud-muudatused-mitte-praegune-kaitse)

## Vastuvõtukatsed

Kahe brauseriga taotle luba korraga. Teine näeb olekut, käsud keelduvad ka otse serveri marsruudil. Proovi puhkeolekus vabastamist, aktiivse töö katkestust, lease'i aegumist, hilinenud käsku ja võrgu taastumist. Kontrolli enne luba kohalikku recovery't. Lisa ka CAD Hubi, Lab 1/2 ja CLI paralleelse käsutee tõkestus, logi sessioon, töö, otsus ning põhjus. Katseta esmalt asendatud täituriga. Päriskatse ja tulemused on TODO.
