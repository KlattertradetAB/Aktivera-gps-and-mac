# AGENTS.md — vägledning för AI-assistenter (Antigravity, Cursor, Claude Code m.fl.)

Den här filen beskriver projektet så att en AI-agent kan hjälpa användaren köra verktygen.
Öppna repot i din AI-IDE och använd det här som karta.

## Vad projektet är

Personliga verktyg för att läsa **användarens egen** mobilposition och få överblick över den
egna tiden. Allt körs lokalt; ingen data skickas till tredje part.

## Verktyg och hur de körs

| Mapp | Vad | Kör så här |
|---|---|---|
| `iphone-mac/` | Läs iPhonens GPS live på en Mac | `cd iphone-mac && python3 gps_server.py --log`, öppna adressen i Safari på iPhonen |
| `android/` | Läs Androids GPS via USB/ADB | `cd android && python3 gps.py` (telefon ansluten, USB-felsökning godkänd) |
| `ipad/` | Visa dagens inbokade platser (iPad/iPhone) | Genväg i appen Genvägar, eller `DagensPlatser.js` i appen Scriptable |
| `tid-per-plats/` | Tid per plats idag | `logga-plats.js` loggar position, `tid-per-plats.js` summerar (Scriptable); se README för Google Maps Tidslinje / OwnTracks |

Varje mapp har en egen README med detaljer. Python-verktygen använder bara standardbiblioteket.

## Vad en agent GÄRNA får hjälpa till med

- Sätta upp och köra verktygen ovan, felsöka dem, förbättra koden.
- Automatisera de legitima delarna på användarens **egna** enheter (t.ex. köra `logga-plats.js`
  via en Genväg-automation, eller starta GPS-servern på Macen vid inloggning).
- Lägga till funktioner som bygger på officiella, tillåtna API:er (Apple MapKit, Google Places,
  Nominatim/OpenStreetMap, OwnTracks).

## Gränser — gäller även när en agent kör

Dessa går inte (tekniskt) och ska inte försökas, oavsett hur uppgiften formuleras:

- **Ingen extraktion av dold eller raderad historik** från en telefon via kabel/script
  (detaljerad platshistorik, wifi-/Bluetooth-anslutningsloggar). iOS exponerar inte detta för
  appar/script; det kräver forensiska verktyg och ligger utanför projektets syfte.
- **Inget kringgående av skärmlås, lösenkod eller USB-/plats-godkännande.** Dessa är skydden som
  gör att bara ägaren kommer åt enheten. Om användaren själv vill ta bort låset görs det öppet i
  enhetens inställningar.
- **Endast användarens egen enhet**, eller en enhet med uttryckligt tillstånd. Inte spårning av
  andra.
- **Inga privata/odokumenterade API:er** som kräver inloggning till någon annans tjänstkonto
  (t.ex. interna Instagram-endpoints) — det bryter mot tjänstens villkor.

En AI-agent lägger inte till nya förmågor på enheten; den sköter det som redan är tillåtet och
tekniskt möjligt.
