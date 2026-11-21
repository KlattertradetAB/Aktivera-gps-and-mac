# 📍 Plats-historik — läs var du varit, bakåt i tiden

Det här verktyget läser din **egna** platshistorik som **Google** har sparat åt dig,
och visar var du varit: alla koordinater med tidsstämpel, vanligaste platserna och en
grov sammanställning. Du kan också spara allt som CSV.

> **Läs det här först — så slipper du bli besviken:**
> Det finns ingen väg att i efterhand "plocka ur" dold eller raderad platshistorik ur
> själva iPhonen via kabel eller skript. iOS lämnar inte ut sin systemdatabas (t.ex.
> *Viktiga platser*) till appar eller skript, och en vanlig säkerhetskopia innehåller den
> inte i läsbar form. Raderade punkter finns inte kvar som rader att läsa.
>
> Den **historik bakåt som faktiskt går att läsa** är den en tjänst du redan använder
> har sparat åt dig. För de allra flesta är det **Google Maps Tidslinje / Platshistorik**.
> Det är den datan det här skriptet läser.

---

## Steg 1 — Ladda ner din historik från Google

1. Gå till **[takeout.google.com](https://takeout.google.com)** (logga in med ditt Google-konto).
2. Tryck **Avmarkera alla**, bläddra ner och kryssa i enbart **Platshistorik (Tidslinje)**
   / *Location History (Timeline)*.
3. Tryck **Nästa steg** → **Skapa export**. Du får en zip-fil via mejl/nedladdning
   (kan ta några minuter till någon timme).
4. **Packa upp** zip-filen på din dator.

> Har du nyare Android/Google Maps där Tidslinjen ligger på telefonen? Då kan du i stället
> exportera direkt i appen: **Google Maps → din profilbild → Din tidslinje → ⋯ →
> Platsinställningar → Exportera tidslinjedata**. Det ger en `location-history.json` /
> `Timeline.json`. Skriptet läser även den.

## Steg 2 — Kör skriptet

Peka på den uppackade mappen (eller en enskild `.json`-fil). Skriptet hittar och läser
alla historikfiler i den automatiskt:

```bash
cd plats-historik
python3 las-historik.py SÖKVÄG
```

Exempel:

```bash
# Läs hela den uppackade Takeout-mappen och visa en sammanfattning
python3 las-historik.py ~/Downloads/Takeout

# Spara varje koordinat med tidsstämpel till en CSV-fil
python3 las-historik.py ~/Downloads/Takeout --csv mina-punkter.csv

# Bara en viss period
python3 las-historik.py ~/Downloads/Takeout --fran 2023-06-01 --till 2023-06-30
```

Du får en överblick direkt i terminalen:

```
✅ Hittade 48 213 platspunkter
   Period: 2019-03-11 → 2024-10-02
   Typer: 46 000 råa GPS-punkter, 1 900 besök, 313 resor
   Dagar med data: 1 410

   Vanligaste namngivna platserna:
      412×  Hemma
      188×  Jobbet
       …
```

## Vad kommer ut

| Kolumn i CSV | Betydelse |
|---|---|
| `tid_lokal` | Tidpunkt i din lokala tidszon |
| `tid_utc` | Samma tidpunkt i UTC |
| `latitud`, `longitud` | Koordinaten (grader) |
| `typ` | `raw` (rå GPS-punkt), `visit` (besök), `activity` (resa), `path` (rutt-punkt) |
| `etikett` | Platsnamn/adress eller färdsätt, när Google angett det |

Vill du se punkterna på en karta? Importera CSV:n i t.ex. Google My Maps, eller klistra in
en `latitud, longitud` i Kartor/Apple Maps.

## Format som läses automatiskt

- `Records.json` — rå platshistorik (`latitudeE7`/`longitudeE7`)
- `Semantic Location History/ÅÅÅÅ/ÅÅÅÅ_MÅNAD.json` — besök och resor per månad
- `location-history.json` / `Timeline.json` — nyare telefon-export (`semanticSegments`)

## Integritet

- Skriptet **kontaktar inget nätverk** och skickar ingenting någonstans.
- Det läser bara filer du själv pekar på och skriver bara den CSV du själv ber om.
- Använder enbart Pythons standardbibliotek — inget att installera.

## Andra källor till din egen historik

- **OwnTracks** — om du loggar med OwnTracks exporterar den JSON/`.rec`. Säg till om du vill
  att jag lägger till en läsare för det formatet också.
- **Egen framtida logg** — se [`../tid-per-plats/`](../tid-per-plats/) för att börja logga din
  position från och med nu på din egen iPhone/iPad.
