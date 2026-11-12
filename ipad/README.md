# 📱 iPad / iPhone — dagens inbokade platser

Visa dagens kalenderhändelser **som har en plats**, direkt på iPaden eller iPhonen —
utan dator. Allt läser bara din egen kalender och frågar om lov första gången.

<div align="center">
  <img src="../docs/snabbstart-ipad.gif" alt="Snabbstart steg för steg" width="560">
</div>

Två sätt, välj det du gillar:

## Väg 1 — Genväg (Shortcuts), inget att installera

Öppna appen **Genvägar** → **+** (ny genväg) → lägg till stegen:

1. **Hitta kalenderhändelser**
   - Filter: **Startdatum** → *är idag*
   - Lägg till filter: **Plats** → *har valfritt värde*
   - **Sortera efter** Startdatum, **stigande**
2. **Upprepa med varje** (resultatet ovan)
   - **Text**: `⏰ [Startdatum] – [Titel]\n📌 [Plats]`
     (sätt in variablerna Startdatum/Titel/Plats; formatera Startdatum till bara tid)
   - **Lägg till i variabel** → `lista`
3. **Visa** `lista` (t.ex. *Snabbvy* eller *Visa resultat*)

Döp den till **"Dagens platser"**. Kör den genom att säga *"Hey Siri, Dagens platser"*
eller lägg en ikon på hemskärmen. Första gången: tryck **Tillåt** på kalenderfrågan.

## Väg 2 — Scriptable (riktig kod, klickbara Kartor-länkar)

1. Installera appen **Scriptable** (gratis).
2. Skapa ett nytt script och klistra in [`DagensPlatser.js`](DagensPlatser.js).
3. Kör. Första gången: tillåt kalenderåtkomst.

Du får en lista sorterad på tid; **tryck på en rad för att öppna platsen i Kartor**.
Scriptet kan läggas på hemskärmen eller köras via Siri.

---

> **Endast din egen kalender.** Verktyget läser bara din egen enhets kalender, lokalt,
> och skickar ingenting vidare.
