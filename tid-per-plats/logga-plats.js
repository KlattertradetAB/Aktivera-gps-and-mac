// logga-plats.js — logga din egen position (Scriptable, iPhone/iPad)
//
// Sparar din NUVARANDE position till en lokal loggfil (platslogg.jsonl).
// Kör den när du vill ta en punkt, eller låt en Genväg-automation köra den
// med jämna mellanrum / när du anländer eller lämnar en plats.
//
// Allt sparas LOKALT på enheten — inget skickas någonstans.
// Summeringen "hur länge var jag var" gör du med tid-per-plats.js.

Location.setAccuracyToHundredMeters(); // batterisnällt; räcker för uppehållstid

let loc = await Location.current();

const fm = FileManager.local();
const path = fm.joinPath(fm.documentsDirectory(), "platslogg.jsonl");

const rec = {
  t: Date.now(),
  lat: loc.latitude,
  lon: loc.longitude,
  acc: loc.horizontalAccuracy
};

const prev = fm.fileExists(path) ? fm.readString(path) : "";
fm.writeString(path, prev + JSON.stringify(rec) + "\n");

// Liten tyst bekräftelse (syns om du kör manuellt, stör inte automationer)
console.log("Loggade: " + rec.lat.toFixed(5) + ", " + rec.lon.toFixed(5));
