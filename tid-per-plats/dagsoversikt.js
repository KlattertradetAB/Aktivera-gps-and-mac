// dagsoversikt.js — allt om din dag på ett ställe (Scriptable, iPhone/iPad)
//
// Samlar i EN vy:
//   📍 var du är just nu
//   🗓️ dagens inbokade platser (din kalender)
//   ⏱️ tid per plats hittills idag (din egen logg från logga-plats.js)
//
// Tryck på en rad för att öppna platsen i Kartor.
// Allt sker lokalt på enheten — bara din egen data, inget skickas iväg.

// --- inställningar ---
const RADIUS_M = 120;   // punkter inom så här många meter = samma plats
const MIN_MIN = 2;      // minsta uppehåll som visas (minuter)
// ---------------------

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

const now = new Date();
const table = new UITable();
table.showSeparators = true;

const header = new UITableRow();
header.isHeader = true;
const dstr = now.toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long" });
header.addText("📅 Din dag", dstr);
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

// 1) Var du är just nu
section("📍 Just nu");
try {
  Location.setAccuracyToHundredMeters();
  const loc = await Location.current();
  place(
    `${loc.latitude.toFixed(5)}, ${loc.longitude.toFixed(5)}`,
    "Tryck för karta",
    () => Safari.open(`http://maps.apple.com/?ll=${loc.latitude},${loc.longitude}`)
  );
} catch (e) {
  note("Kunde inte hämta plats just nu.", "Tillåt platsåtkomst och försök igen.");
}

// 2) Dagens inbokade platser (kalender)
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

// 3) Tid per plats hittills idag (egen logg)
section("⏱️ Tid per plats (loggat)");
const fm = FileManager.local();
const path = fm.joinPath(fm.documentsDirectory(), "platslogg.jsonl");
if (!fm.fileExists(path)) {
  note("Ingen logg än.", "Kör logga-plats.js för att börja samla.");
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
    note("Inga uppehåll ≥ " + MIN_MIN + " min idag än.");
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
