# ⏱️ Tid per plats — få koll på hur du lägger din tid

Tre sätt att se **hur mycket tid du lagt på varje plats under dagen** — för din egen
överblick och ditt eget lugn. Allt handlar om *din egen* data, och de privata varianterna
håller allt lokalt på din enhet.

> **Viktigt att veta:** iOS lämnar inte ut detaljerad platshistorik (eller wifi-/Bluetooth-loggar)
> till ett script via kabel. Det går alltså inte att "plocka ut gårdagens sekunder" i efterhand.
> Vägarna nedan är de som faktiskt fungerar: färdig historik från en tjänst du redan använder,
> eller en egen logg som börjar samla från och med nu.

---

## Väg 1 — Google Maps Tidslinje (snabbast, ser redan idag)

Om du har Google Maps visar **Tidslinjen** exakt "du var här 1 h 20 min, sen här 40 min",
dag för dag, med karta. Inget att bygga.

1. Öppna **Google Maps** på telefonen → tryck på din profilbild → **Din tidslinje**.
2. Slå på platshistorik om du inte redan gjort det (frågar om lov).
3. Välj **Idag** för att se dagens platser och tider.

> Tidslinjen lagras numera på din egen enhet. Du kan exportera din data via
> [takeout.google.com](https://takeout.google.com) om du vill ha den som fil.

## Väg 2 — Egen privat loggare (Scriptable) — i den här mappen

Ett eget litet verktyg i två delar som kör på din telefon och håller allt **lokalt**:

| Fil | Gör |
|---|---|
| [`logga-plats.js`](logga-plats.js) | Sparar din nuvarande position till en lokal loggfil. |
| [`tid-per-plats.js`](tid-per-plats.js) | Räknar ut hur länge du var på varje plats idag. Tryck på en rad → öppna i Kartor. |

**Så sätter du upp det:**

1. Installera appen **Scriptable** (gratis).
2. Lägg in båda filerna som två script (kopiera in koden).
3. **Logga automatiskt:** öppna **Genvägar → Automation** och skapa personliga automationer
   som kör `logga-plats.js`:
   - *Tid på dagen* (t.ex. varje hel timme), och/eller
   - *Anländer / Lämnar* en plats du bryr dig om.
4. När du vill se dagen: kör **`tid-per-plats.js`**.

Du kan justera känsligheten högst upp i `tid-per-plats.js`:
```js
const RADIUS_M = 120;   // hur nära punkter räknas som samma plats
const MIN_MIN  = 2;     // minsta uppehåll som visas (minuter)
```

> **Caveat:** iOS begränsar bakgrundskörning, så den egna loggaren tar *stickprov* när den
> triggas — inte en obruten spårning. Vill du ha obruten, automatisk loggning är Väg 3 bättre.

## Väg 3 — OwnTracks (mest privat, obruten loggning, du äger datan)

[OwnTracks](https://owntracks.org) är en gratis app med öppen källkod som loggar din position
automatiskt i bakgrunden. Den kan köras helt privat — du bestämmer var datan hamnar.

1. Installera **OwnTracks** från App Store.
2. Välj läge:
   - **Utan server (enklast):** appen loggar lokalt; du kan exportera din data.
   - **Egen server (mest kontroll):** peka appen mot din egen MQTT- eller HTTP-endpoint
     så att bara du har datan. Se [owntracks.org/booklet](https://owntracks.org/booklet/).
3. Appen visar din historik och var du uppehållit dig, automatiskt.

> Vill du att jag hjälper dig sätta upp en **egen OwnTracks-endpoint** (så datan bara är din),
> säg till — då gör vi en liten privat mottagare.

---

## Om wifi / Bluetooth-historik

Det finns **ingen** väg för ett script på iOS att läsa ut en logg över vilka wifi- eller
Bluetooth-enheter telefonen anslutit till. Den datan exponeras inte för appar. (På en **Mac**
kan du se din *egen* wifi-historik i systemet — säg till om du vill ha ett litet Mac-script
för just det.)

---

> **Endast din egen enhet och din egen data.** Verktygen här är till för din egen överblick.
