// Dagens inbokade platser — för Scriptable (iPad/iPhone)
//
// Visar dagens kalenderhändelser som har en plats, sorterade på tid.
// Tryck på en rad för att öppna platsen i Kartor.
//
// Så här: installera appen "Scriptable", skapa ett nytt script, klistra in
// detta och kör. Första gången frågar iPaden om kalenderåtkomst -> Tillåt.
// Lägg till på hemskärmen eller kör via Siri om du vill ("kör script ...").

// Hämta dagens händelser från ALLA kalendrar
let events = await CalendarEvent.today([]);

// Behåll bara de med en plats, sortera på starttid
let withLoc = events
  .filter(e => e.location && e.location.trim() !== "")
  .sort((a, b) => a.startDate - b.startDate);

function hhmm(d) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Bygg en enkel tabell
let table = new UITable();
table.showSeparators = true;

let header = new UITableRow();
header.isHeader = true;
let today = new Date().toLocaleDateString("sv-SE", {
  weekday: "long", day: "numeric", month: "long"
});
header.addText("📍 Dagens platser", today);
table.addRow(header);

if (withLoc.length === 0) {
  let row = new UITableRow();
  row.addText("Inga händelser med plats idag.");
  table.addRow(row);
} else {
  for (let e of withLoc) {
    let row = new UITableRow();
    row.height = 64;
    row.addText(`${hhmm(e.startDate)}  ${e.title}`, `📌 ${e.location}`);
    // Tryck på raden -> öppna i Kartor
    row.onSelect = () => {
      let q = encodeURIComponent(e.location);
      Safari.open(`http://maps.apple.com/?q=${q}`);
    };
    table.addRow(row);
  }
}

await table.present();
