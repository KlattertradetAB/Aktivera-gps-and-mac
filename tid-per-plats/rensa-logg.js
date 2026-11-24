// rensa-logg.js — töm din egna lokala platslogg (Scriptable, iPhone/iPad)
//
// Raderar punkterna som logga-plats.js sparat i "platslogg.jsonl" på DENNA
// enhet. Det är din egen lokala fil — inget moln, inget systemdata.
//
// VIKTIGT: Det här rensar BARA projektets egen loggfil. Det kan INTE röra
// iOS egen platshistorik (Viktiga platser), Google Maps Tidslinje eller
// någon annan apps data — iOS släpper inte in skript där. Hur du rensar
// det öppet i Inställningar står i README.
//
// Säkerhet: frågar först, och kan spara en backup innan den tömmer.

const fm = FileManager.local();
const path = fm.joinPath(fm.documentsDirectory(), "platslogg.jsonl");

if (!fm.fileExists(path)) {
  const a = new Alert();
  a.title = "Inget att rensa";
  a.message = "Hittar ingen platslogg.jsonl på den här enheten.";
  a.addCancelAction("OK");
  await a.present();
  return;
}

// Hur många punkter finns?
const innehall = fm.readString(path);
const antal = innehall.split("\n").filter(r => r.trim() !== "").length;

const fraga = new Alert();
fraga.title = "Töm platsloggen?";
fraga.message = `Loggen innehåller ${antal} punkter.\n\nVälj hur du vill göra. Detta går inte att ångra.`;
fraga.addAction("Spara backup och töm");      // index 0
fraga.addDestructiveAction("Töm utan backup"); // index 1
fraga.addCancelAction("Avbryt");               // index -1
const svar = await fraga.present();

if (svar === -1) {
  return; // avbröt
}

if (svar === 0) {
  // Spara en tidsstämplad backup bredvid originalet
  const d = new Date();
  const stamp = d.toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const backupPath = fm.joinPath(fm.documentsDirectory(), `platslogg-backup-${stamp}.jsonl`);
  fm.writeString(backupPath, innehall);
  console.log("Backup sparad: " + backupPath);
}

// Töm filen (skriv tom sträng — behåller filen men utan punkter)
fm.writeString(path, "");

const klar = new Alert();
klar.title = "Klart";
klar.message = `Platsloggen är tömd (${antal} punkter borttagna).` +
  (svar === 0 ? "\nEn backup sparades i Scriptable-mappen." : "");
klar.addCancelAction("OK");
await klar.present();
