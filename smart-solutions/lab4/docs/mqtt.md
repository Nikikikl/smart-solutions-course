# MQTT andmetee

**Kavand.** Dropletil töötab eraldi Eclipse Mosquitto kuulaja ainult kinnitatud WireGuardi liidese aadressil. Tulemüür lubab ligi volitatud VPN-i osapooled. Luba ainult autentitud ühendus. Igal meeskonnal on oma kasutajakonto, parool ja teemaõigused. Pööra saladused läbi eraldi salajase konfiguratsiooni, millele pääseb ligi vaid vastav teenus. Avalikul postkontoril puuduvad nende teemade, failiteenuse ja katsebaasi õigused. [Mosquitto seadistusvalikud](https://mosquitto.org/man/mosquitto-conf-5.html) · [Lab 3 võrguplaan](../../lab3/docs/network_plan.md)

## Teemad ja õigused

| Teema | Saatja → lugeja | QoS | Põhjus |
| --- | --- | --- | --- |
| `lab4/<team>/<station_id>/cycles` | Jaam → salvestaja | 1 | Lõplik kirje peab jõudma kohale ka kordussaatmise teel. Siia kuuluvad lõpetatud ja katkestatud tsüklid. |
| `lab4/<team>/<station_id>/stored` | Salvestaja → jaam | 1 | Jaam peab saama rakenduse kinnituse. Korduv või hilinenud kinnitus on võimalik. |
| `lab4/<team>/<station_id>/telemetry` | Jaam → lubatud jälgija | 0 | Valikuline otsevaade. Tsükliga seotud toorkõver säilib eraldi failis. |

ACL seob kontod nende enda meeskonna teemadega. Jaamakonto avaldab `cycles` ja `telemetry` alla ning loeb enda `stored` teemat. Ainult salvestaja saab lugeda kõigi meeskondade `cycles` teemasid ja kirjutada `stored` alla. Salvestaja kontrollib teemast saadud meeskonda ja jaama väljade `team` ja `station_id` ning jaamaregistri vastu. Faili üleslaadimisel rakendub sama meeskonnapiir. Teemadel `cycles` ja `stored` on retain väljas. Brokeri püsiseanss võib vähendada korduskatseid, jaama püsipuhver jääb tarne lähtekohaks. [MQTT 5.0 standard](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html)

## Salvestuskinnitus

Jaam laeb püsipuhvris viidatud failid koos kontrollsummadega üles VPN-i eraldi failiteenusesse ja avaldab 27-väljalise kirje. MQTT `PUBACK` näitab, et sõnumi võttis vastu järgmine MQTT osapool. Jaam hoiab kirjet alles kuni rakenduse `stored` kinnituseni. See saabub alles siis, kui salvestaja on kontrollinud kõiki viiteid ja lõpetanud püsiva SQLite'i tehingu. Ümbrise kuju on ettepanek. `record_sha256` arvutatakse kokkulepitud kanoonilisest kirjest ning see kuulub kinnituse metaandmetesse.

```json
{
  "team": "example",
  "station_id": "example-station",
  "cycle": 1,
  "record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "status": "stored"
}
```

See on sünteetiline vorminäide. Sama võtme ja sisuga kordus saab samaväärse `stored` kinnituse. `conflict` ja `invalid` on eraldi tõrketeated võtme ning saadetud kirje kontrollsummaga. Need jätavad algse järjekorrakande alles ja annavad operaatorile märku. Puuduv fail, täis ketas või muu ajutine tõrge jätab kirje korduskatse ootele. Jaam võrdleb kinnitust ootel võtme ja kontrollsummaga. Valeteema või võõra võtmega vastus ei eemalda kirjet.

Rakendusetapis kontrolli lubatud teemad, anonüümse ühenduse ja teise meeskonna teemade keeld, VPN-i väline ligipääs ning brokeri ja kirjutaja taaskäivitamine. [Andmebaasi salvestus](database.md) · [Puhver ja katsed](buffering.md)
