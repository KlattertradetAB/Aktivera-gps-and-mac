// tid-per-plats.js — hur länge var jag på varje plats idag? (Scriptable)
//
// Läser loggen som logga-plats.js skapat, grupperar punkter som ligger nära
// varandra till "platser", och räknar ut hur länge du var på var och en IDAG.
// Tryck på en rad för att öppna platsen i Kartor.
//
// Allt sker lokalt på enheten.

// --- inställningar du kan ändra ---
const RADIUS_M = 120;   // punkter inom så här många meter = samma plats
const MIN_MIN = 2;      // visa bara uppehåll som är minst så här många minuter
// ----------------------------------

const fm = FileManager.local();
const path = fm.joinPath(fm.documentsDirectory(), "platslogg.jsonl");

function tableWithMessage(msg) {
  const t = new UITable();
  const r = new UITableRow();
  r.addText(msg);
  t.addRow(r);
  return t;
}

if (!fm.fileExists(path)) {
  await tableWithMessage("Ingen logg än. Kör logga-plats.js några gånger först.").present();
  return;
}

// Läs och tolka loggen
let pts = fm.readString(path)
  .trim()
  .split("\n")
  .filter(Boolean)
  .map(l => { try { return JSON.parse(l); } catch (e) { return null; } })
  .filter(Boolean);

// Bara idag, sorterat på tid
const now = new Date();
const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
pts = pts.filter(p => p.t >= startOfDay).sort((a, b) => a.t - b.t);

// Avstånd i meter (haversine)
function dist(a, b) {
  const R = 6371000, toRad = x => x * Math.PI / 180;
  const dLat = toRad(b.lat - a.lat), dLon = toRad(b.lon - a.lon);
  const la1 = toRad(a.lat), la2 = toRad(b.lat);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// Gruppera på varandra följande punkter som ligger nära till "uppehåll"
let stays = [];
let cur = null;
for (const p of pts) {
  if (cur && dist(cur, p) <= RADIUS_M) {
    cur.end = p.t;
    cur.n++;
    cur.lat = (cur.lat * (cur.n - 1) + p.lat) / cur.n; // glidande centroid
    cur.lon = (cur.lon * (cur.n - 1) + p.lon) / cur.n;
  } else {
    if (cur) stays.push(cur);
    cur = { lat: p.lat, lon: p.lon, start: p.t, end: p.t, n: 1 };
  }
}
if (cur) stays.push(cur);

const minutes = ms => ms / 60000;
const result = stays.filter(s => minutes(s.end - s.start) >= MIN_MIN);

function hhmm(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function dur(ms) {
  const m = Math.round(minutes(ms));
  if (m < 60) return m + " min";
  const h = Math.floor(m / 60), r = m % 60;
  return r ? `${h} h ${r} min` : `${h} h`;
}

// Bygg tabell
const table = new UITable();
table.showSeparators = true;

const header = new UITableRow();
header.isHeader = true;
const dstr = now.toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long" });
header.addText("⏱️ Tid per plats idag", dstr);
table.addRow(header);

if (result.length === 0) {
  const r = new UITableRow();
  r.addText("Inga uppehåll ≥ " + MIN_MIN + " min idag.", "Logga fler punkter under dagen.");
  table.addRow(r);
} else {
  // längst tid först
  result.sort((a, b) => (b.end - b.start) - (a.end - a.start));
  let total = 0;
  for (const s of result) {
    total += s.end - s.start;
    const row = new UITableRow();
    row.height = 64;
    const title = `${dur(s.end - s.start)}  ·  ${hhmm(s.start)}–${hhmm(s.end)}`;
    const sub = `📌 ${s.lat.toFixed(5)}, ${s.lon.toFixed(5)}`;
    row.addText(title, sub);
    row.onSelect = () => {
      Safari.open(`http://maps.apple.com/?ll=${s.lat},${s.lon}`);
    };
    table.addRow(row);
  }
  const foot = new UITableRow();
  foot.addText("Summa loggad tid på platser: " + dur(total));
  table.addRow(foot);
}

await table.present();
