# 🔎 Konto-granskning — gå igenom din egna TikTok-export, grundligt

Verktyg för att analysera din **egna** nedladdade TikTok-data när någon okänd
loggat in på ditt konto. Det gör den "osynliga" datan synlig: inventerar allt
som finns i exporten, markerar misstänkta inloggningar, och knyter aktivitet
till rätt enhet via tidskorsning.

> **Allt sker lokalt.** Skriptet kontaktar inget nätverk och skickar ingenting.
> Det läser bara filen du själv laddat ner och skriver bara de filer du ber om.

---

## Vad det kan — och inte kan

**Kan:**
- Lista **alla** datakategorier i exporten (visningar, sökningar, DM, likes,
  inloggningar, inställningar …) med antal och datumspann — så inget missas.
- Plocka ut **inloggningshistoriken** och flagga misstänkta enheter.
- **Tidskorsa:** knyta varje handling till den inloggning som var senast innan,
  och lista allt som sannolikt gjorts av den okända enheten — med bevislänk.
- Skriva en läsbar **rapport** + **CSV**, färdigt att bifoga en polisanmälan.

**Kan inte** (var ärlig mot dig själv här):
- Återskapa sådant som **inte finns i exporten** — t.ex. meddelanden motparten
  raderat hos sig, eller handlingar TikTok inte loggar. Finns det inte i filen,
  finns det inte att läsa.
- Peka ut en **person med namn**. En IP ger operatör/region; vem som satt bakom
  den vet bara operatören, och det lämnas bara ut till polis.

## Steg 1 — Ladda ner din data från TikTok

Appen: **Profil → ☰ → Inställningar och integritet → Konto → Ladda ner dina data**.
Under **Begär data**: välj **Alla data** och format **JSON**, tryck **Begär data**.
Filen är klar efter några timmar (ibland upp till ett par dygn) under fliken
**Ladda ner data** — ladda ner zip-filen och packa upp den.

## Steg 2 — Säg vilka enheter som är dina

Öppna `analysera-export.py` och fyll i längst upp:

```python
MINA_ENHETER = ["iPhone14,5", "iPad13,1"]   # enheter du känner igen som dina
MISSTANKTA   = ["25028RN03Y"]               # enheter du vet inte är dina
```

När du listat dina egna enheter i `MINA_ENHETER` markeras allt annat automatiskt
som misstänkt — och din egen inloggning visas grön i stället för "okänd".

## Steg 3 — Kör

```bash
cd konto-granskning
python3 analysera-export.py ~/Downloads/TikTok_Data --rapport rapport.txt --csv alla.csv
```

`SÖKVÄG` kan vara den uppackade mappen eller en enskild `.json`-fil.

Du får tre delar: **inventering**, **inloggningar** (med ⚠️ för misstänkta), och
**"sannolikt gjort av okänd enhet"** — plus `rapport.txt` och `alla.csv`.

## Så funkar tidskorsningen (och dess gräns)

TikTok loggar *när* varje enhet loggade in, men märker **inte** varje handling
med enhet. Skriptet knyter därför varje handling till den **senaste inloggningen
innan** den. Ligger den efter en misstänkt inloggning (inom `MAX_SESSION_TIMMAR`,
standard 24 h) flaggas den som sannolikt inkräktarens.

Det är en **slutledning**, inte ett enhets-ID från TikTok — därför visas alltid
*vilken* inloggning varje handling knutits till, så du själv kan bedöma. Var kontot
redan inloggat sedan tidigare kan en handling sakna föregående inloggning; den
hamnar då i CSV:n utan koppling, och du jämför mot dina egna kända tider.

## Kolumner i `alla.csv`

| Kolumn | Betydelse |
|---|---|
| `tid_utc` | När händelsen skedde (UTC) |
| `kategori` | Var i exporten den kom ifrån |
| `ar_inloggning` | `ja` för en inloggningspost |
| `enhet`, `ip` | Enhet/IP (för inloggningar) |
| `enhet_status` | `min` / `misstänkt` / `okänd` |
| `knuten_till_inloggning_utc`, `knuten_enhet` | Vilken inloggning händelsen knutits till |
| `detalj` | Innehållet (länk, sökord, meddelande …) |

## Integritet

- Inget nätverk, inga beroenden utöver Pythons standardbibliotek.
- Din export kan innehålla privata meddelanden — förvara filen och rapporterna
  på en plats bara du kommer åt.
