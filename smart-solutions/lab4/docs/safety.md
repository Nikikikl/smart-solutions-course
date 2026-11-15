# Lab 4 töövoo ohutuskokkuleppe kavand

Kehtib kogu [Lab 3 ohutuskokkulepe](../../lab3/docs/safety.md). Lab 4 lisab allolevad töövoo tingimused. Meeskonnaliikmed kinnitavad lepingu isiklikult enne esimest kaugkäivitust. Isikute volitused, kohalikud kinnitused ja katsed on TODO.

## Kes võib töövoo käivitada

- **Kohalik operaator** kontrollib vaba tööala, hädastoppi, tööriista, kalibratsiooni ja roboti olekut. Tema lubab roboti kohapeal. Uue või muudetud jada esimene jooks on kohalik kuivkäik 20% kiirusel, tööriist vähemalt 20 mm pinnast kõrgemal ja ilma proovitükita. Käed jäävad 440 mm tööalast välja, enne käiku ütle „liigub“. Tühjas ruumis on robot voolust väljas.
- **Kaugoperaator** peab olema isiklikult volitatud, sisse logitud VPN-i kaudu ja aktiivse juhtimisseansiga. Ta võib käivitada ainult kohapeal kontrollitud töövooversiooni ilma UV-kõvenduseta. Iga käivitus vajab kohaliku vastutaja selgesõnalist luba ja toimivat kogu tööala ning robotit katvat lauakaamerat. Kohalik vastutaja viibib kogu töö ajal ruumis ja ulatub füüsilise hädastopini. Tööriistakaamera üksi ei anna kaugkäivituseks luba.
- **Vaatlejad, avalik postkontor ja MCP** ei käivita Lab 4 töövoogu. Lab 2 whitelist jääb kõrgtaseme tööde piiriks ja läbib ühise lüüsi kohaliku loa kontrolli. Värskenda õigused ja käsurajad [operaatoriluku plaani](operator_lock.md) järgi.

## UV, klapp ja katkestused

- `cure` sammuga töövoo käivitab ainult kohalik operaator lokaalse UV-loaga. Läbipaistmatu kate piirab UV-valguse tööalale, lamp on suunatud alla ning operaatoril ja tööala juures viibijatel on 405 nm kaitseprillid. Hoia nahk katte alt eemal. Atomi sõltumatu taimer peab LED-i välja lülitama ka brauseri või võrgu kadumisel. Ülempiir, lokaalne tõke ja väljalülitus vajavad füüsilist kinnitust.
- Lab 3 pneumaatikas läheb pumba Y-haru otse iminapale, klapp juhib süstlaharu. Vooluta on pump süstlast lahutatud ja süstal atmosfäärile avatud. Kontrolli seda päriselt enne doseerimist. Vabasta ja kontrolli süstla rõhk enne eemaldamist. 24 V pumbakasti DO-juhtmed ühendatakse keelatud roboti ja vooluta kastiga.
- Enne päris kaugliikumist rakenda ning katseta füüsilise hädastopiga VPN-i kadumise ohutu toimimine. Lepi kokku roboti, pumba, klapi ja UV olek ning aja piirid. Kaamera või side kadumine peatab uute kaugkäskude vastuvõtu ja käivitab kontrollitud katkestuskorra. Väldi pumba automaatset vabastust, kui see võib detaili kukutada. Side, seansi ja andmeedastuse taastumine ei taasta liikumisluba. Ruumis olev inimene kontrollib seisakut, tühja käsujärjekorda ja väljundeid ning lubab uue töö. Kaitsemehhanismi rakendumine või tundmatu olek vajab kohapealset taastamist.
- Käskude ainuõigus on ühel MG400 lüüsil. Füüsiline hädastopp on ainus usaldatud stop. 15.11 Lab 2 Wi-Fi katse käsitles varem vastu võetud HTTPS-tööd. VPN-i fail-safe, UV, klapp ja Lab 4 katkestustega edastus ootavad eraldi tõendeid.

Enne kaitsmist lisa kinnitajad, lubatud töövooversioon, taastamiskatse ja kokkulepitud kaameravaate piirid. Käsitle VPN-i võtmeid, kasutajatunnuseid ja MCP linki Lab 3 ligipääsureeglite järgi. [Lab 3 VPN-i tööplaan](../../lab3/docs/wireguard/README.md) · [MCP ligipääs](mcp.md#ligipääs-ja-keeldumine)
