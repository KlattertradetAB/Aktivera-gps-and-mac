// min-dag.js — EN fil för allt (Scriptable, iPhone/iPad)
//
// När du kör den:
//   1) loggar din plats just nu (lokalt)
//   2) visar din dag: plats nu + dagens inbokade platser (kalender) + tid per plats
//
// Klistra in HELA den här filen i ETT nytt Scriptable-script. Allt sker lokalt
// på enheten — bara din egen data, inget skickas iväg.
//
// OBS: första gången frågar appen om plats- och kalenderåtkomst — tryck Tillåt.
// Om plats är nekad: Inställningar → Integritet → Platstjänster → Scriptable → Tillåt.

// --- inställningar du kan ändra ---
const RADIUS_M = 120;   // punkter inom så här många meter = samma plats
const MIN_MIN = 2;      // minsta uppehåll som visas (minuter)
// ----------------------------------

const fm = FileManager.local();
const path = fm.joinPath(fm.documentsDirectory(), "platslogg.jsonl");

function hhmm(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function dur(ms) {
  const m = Math.round(ms / 60000);
  if (m < 60) return m + " min";
  const h = Math.floor(m / 60), r = m % 60;
  return r ? `${h} h ${r} min` : `${h} h`;
}
function dist(a, b) {
  const R = 6371000, toRad = x => x * Math.PI / 180;
  const dLat = toRad(b.lat - a.lat), dLon = toRad(b.lon - a.lon);
  const la1 = toRad(a.lat), la2 = toRad(b.lat);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// --- 1) Logga plats just nu ---
let locNow = null, locErr = null;
try {
  Location.setAccuracyToHundredMeters();
  locNow = await Location.current();
  const rec = { t: Date.now(), lat: locNow.latitude, lon: locNow.longitude, acc: locNow.horizontalAccuracy };
  const prev = fm.fileExists(path) ? fm.readString(path) : "";
  fm.writeString(path, prev + JSON.stringify(rec) + "\n");
} catch (e) {
  locErr = String(e);
}

// --- bygg vyn ---
const now = new Date();
const table = new UITable();
table.showSeparators = true;

const header = new UITableRow();
header.isHeader = true;
const dstr = now.toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long" });
header.addText("📅 Min dag", dstr);
table.addRow(header);

function section(txt) {
  const r = new UITableRow();
  r.isHeader = true;
  r.addText(txt);
  table.addRow(r);
}
function note(txt, sub) {
  const r = new UITableRow();
  r.addText(txt, sub || "");
  table.addRow(r);
}
function place(title, sub, onTap) {
  const r = new UITableRow();
  r.height = 58;
  r.addText(title, sub);
  if (onTap) r.onSelect = onTap;
  table.addRow(r);
}

// Just nu
section("📍 Just nu");
if (locNow) {
  place(
    `${locNow.latitude.toFixed(5)}, ${locNow.longitude.toFixed(5)}`,
    "Loggad · tryck för karta",
    () => Safari.open(`http://maps.apple.com/?ll=${locNow.latitude},${locNow.longitude}`)
  );
} else {
  note("Kunde inte hämta plats.",
       "Inställningar → Platstjänster → Scriptable → Tillåt (+ Exakt plats).");
}

// Dagens inbokade platser
section("🗓️ Inbokade platser idag");
let events = [];
try { events = await CalendarEvent.today([]); } catch (e) {}
const evLoc = events
  .filter(e => e.location && e.location.trim() !== "")
  .sort((a, b) => a.startDate - b.startDate);
if (evLoc.length === 0) {
  note("Inga inbokade platser med adress idag.");
} else {
  for (const e of evLoc) {
    place(
      `${hhmm(e.startDate.getTime())}  ${e.title}`,
      `📌 ${e.location}`,
      () => Safari.open(`http://maps.apple.com/?q=${encodeURIComponent(e.location)}`)
    );
  }
}

// Tid per plats idag
section("⏱️ Tid per plats (loggat)");
if (!fm.fileExists(path)) {
  note("Ingen logg än.", "Kör scriptet några gånger under dagen.");
} else {
  let pts = fm.readString(path).trim().split("\n").filter(Boolean)
    .map(l => { try { return JSON.parse(l); } catch (e) { return null; } })
    .filter(Boolean);
  const sod = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  pts = pts.filter(p => p.t >= sod).sort((a, b) => a.t - b.t);

  let stays = [], cur = null;
  for (const p of pts) {
    if (cur && dist(cur, p) <= RADIUS_M) {
      cur.end = p.t; cur.n++;
      cur.lat = (cur.lat * (cur.n - 1) + p.lat) / cur.n;
      cur.lon = (cur.lon * (cur.n - 1) + p.lon) / cur.n;
    } else {
      if (cur) stays.push(cur);
      cur = { lat: p.lat, lon: p.lon, start: p.t, end: p.t, n: 1 };
    }
  }
  if (cur) stays.push(cur);

  const res = stays.filter(s => (s.end - s.start) / 60000 >= MIN_MIN)
    .sort((a, b) => (b.end - b.start) - (a.end - a.start));

  if (res.length === 0) {
    note("Inga uppehåll ≥ " + MIN_MIN + " min idag än.", "Kör scriptet fler gånger under dagen.");
  } else {
    let total = 0;
    for (const s of res) {
      total += s.end - s.start;
      place(
        `${dur(s.end - s.start)}  ·  ${hhmm(s.start)}–${hhmm(s.end)}`,
        `📌 ${s.lat.toFixed(5)}, ${s.lon.toFixed(5)}`,
        () => Safari.open(`http://maps.apple.com/?ll=${s.lat},${s.lon}`)
      );
    }
    note("Summa loggad tid på platser: " + dur(total));
  }
}

await table.present();
