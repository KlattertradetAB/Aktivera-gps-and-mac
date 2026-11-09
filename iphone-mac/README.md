# 🍎 iPhone + Mac

**Läs GPS-positionen från din egen iPhone direkt på din Mac.**

[![Plattform](https://img.shields.io/badge/plattform-iPhone%20%2B%20macOS-0a84ff)](#)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Beroenden](https://img.shields.io/badge/beroenden-inga%20(standardbibliotek)-success)](#krav)

iPhonens riktiga position läses via webbläsarens Geolocation-API och visas live på din Mac.
Allt sker lokalt mellan din iPhone och din dator — inget skickas vidare.

## Varför det ser ut så här

Till skillnad från Android finns det **ingen** väg för en dator att läsa iPhonens GPS direkt
via kabeln — Apple tillåter det helt enkelt inte. iOS ger bara platsen till appar, och bara
med din tillåtelse.

Den väg som **fungerar**: Macen startar en liten **webbserver** som du öppnar i **Safari** på
iPhonen. Du trycker på en knapp, Safari frågar om platstillåtelse, och telefonens **riktiga
GPS-position** skickas tillbaka och visas live på Macen — via telefonens egen GPS genom
webbläsarens Geolocation-API.

## Funktioner

- 📡 Live-uppdatering av position, hastighet, höjd och osäkerhet
- 🔌 Fungerar över **kabel** (iPhone-USB-nätverk) eller **wifi**
- 🗺️ Färdig Apple Maps-länk för varje position
- 💾 Valfri loggning till en JSONL-fil (`--log`)
- 🔒 Allt lokalt — inga konton, inga nycklar, inget skickas externt

## Krav

- En **Mac** med **Python 3.8+** och `openssl` (båda finns normalt förinstallerade)
- En **iPhone** med Safari
- Valfritt: en USB-kabel (annars samma wifi-nät)

## Kom igång

### 1. Starta servern på Macen

```bash
cd iphone-mac
python3 gps_server.py
```

Första gången skapas ett självsignerat certifikat (engångs). Servern skriver ut en eller
flera adresser, t.ex.:

```
Öppna EN av dessa adresser i Safari på iPhonen:

    https://172.20.10.1:8443      (iPhone USB-kabel)
    https://192.168.1.42:8443     (nätverk (wifi/ethernet))
```

### 2. Anslut iPhonen och öppna adressen

- **Via kabel:** koppla in iPhonen i Macen. Då skapas ett "iPhone USB"-nätverk, och adressen
  som är märkt **iPhone USB-kabel** fungerar.
- **Via wifi:** se till att iPhone och Mac är på samma nät och använd nätverks­adressen.

Öppna adressen i **Safari** på iPhonen.

### 3. Godkänn certifikatet (en gång)

Safari varnar för "osäker anslutning" (det är det självsignerade certet).
Tryck **Visa detaljer → besök denna webbplats**. Det behövs bara första gången.

### 4. Tryck "Starta GPS" och tillåt plats

Positionen uppdateras live på sidan — och skrivs ut på Macen i terminalen, med en färdig
Apple Maps-länk.

## Användning

```bash
python3 gps_server.py                    # standardport 8443
python3 gps_server.py -p 9000            # annan port
python3 gps_server.py --log              # spara varje position till positioner.jsonl
python3 gps_server.py --log mina.jsonl   # egen loggfil
```

Terminalen visar varje uppdatering:

```
[14:03:21]  59.329301, 18.068599  ±8 m   https://maps.apple.com/?ll=59.329301,18.068599
```

## Felsökning

| Problem | Lösning |
|---|---|
| Safari säger bara "osäker anslutning" | Tryck **Visa detaljer → besök denna webbplats**. Certet är självsignerat, det är väntat. |
| Knappen gör inget / "Du nekade platsåtkomst" | Tillåt plats när Safari frågar. Annars: iPhone → Inställningar → Safari → rensa och försök igen, och kontrollera Inställningar → Integritet → Platstjänster → Safari. |
| iPhonen når inte adressen | Prova den andra adressen (USB vs wifi). Via kabel: använd `172.20.10.x`-adressen. Kontrollera att Macens brandvägg inte blockerar Python. |
| "±stor osäkerhet" / ingen fix | Gå nära ett fönster eller ut. GPS tar några sekunder att få fix. Sidan uppdateras automatiskt när den blir bättre. |
| Positionen uppdateras inte | Lämna skärmen på och Safari i förgrunden — iOS pausar GPS i bakgrunden. |

## Alternativ (utan webbserver)

**iOS Genväg (Shortcut):** skapa en genväg med *Hämta aktuell plats* → *Spara fil* till
iCloud Drive. Macen läser sedan filen från `~/Library/Mobile Documents/...`.

## Och Android?

Mappen [`../android/`](../android/) innehåller motsvarande verktyg för Android, som läser GPS
direkt över USB via ADB.

---

> **Endast för din egen enhet.** Använd verktyget bara på en iPhone du själv äger eller har
> uttrycklig tillåtelse att använda.
