#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysera-export.py — gå igenom din EGNA TikTok-dataexport, grundligt.

Det här läser filen du själv begärt och laddat ner från TikTok
("Ladda ner dina data", format JSON). Det kontaktar inget nätverk och skickar
ingenting någonstans — allt sker lokalt på din dator.

Vad det gör:
  1. INVENTERING — listar ALLA kategorier av data i exporten med antal och
     datumspann, så inget "osynligt" missas (visningar, sökningar, DM,
     inloggningar, inställningsändringar, m.m. — det som finns i filen).
  2. INLOGGNINGAR — plockar ut inloggningshistoriken med enhet, IP och tid,
     och markerar vilka som är MISSTÄNKTA (okänd enhet).
  3. TIDSKORSNING — för varje händelse på kontot: vilken inloggning var senast
     innan den? Händelser som ligger efter en misstänkt inloggning flaggas som
     sannolikt gjorda av den okända enheten. Du får bevislänken (vilken
     inloggning varje händelse knyts till), så du själv kan bedöma.
  4. EXPORT — skriver allt till CSV + en läsbar rapport, redo att bifoga en
     polisanmälan.

Vad det INTE kan:
  - Återskapa data som inte finns i exporten (t.ex. meddelanden motparten
    raderat hos sig). Finns det inte i filen, finns det inte att läsa.
  - Peka ut en person med namn. En IP ger bara operatör/region; vem det var
    vet bara operatören, och det lämnas bara ut till polis.

Användning:
    python3 analysera-export.py SÖKVÄG [--rapport rapport.txt] [--csv alla.csv]

    SÖKVÄG = din uppackade export-mapp ELLER en enskild .json-fil.
    (Skriptet letar rekursivt efter .json-filer i en mapp.)

KONFIGURERA FÖRST (längst upp i filen):
    MINA_ENHETER    — enhetsmodeller du VET är dina (t.ex. din iPhone).
    MISSTANKTA      — enhetsmodeller du vet är inkräktarens (förifylld med din).

Endast standardbiblioteket.
"""

import argparse
import csv as csvmod
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# KONFIGURATION — fyll i dina egna enheter här
# ---------------------------------------------------------------------------

# Enhetsmodeller du KÄNNER IGEN som dina egna (precis som de står i exporten).
# Exempel: ["iPhone14,5", "iPad13,1"]. Lämna tom om du är osäker.
MINA_ENHETER = []

# Enhetsmodeller du VET inte är dina (inkräktarens). Förifylld från din fråga.
MISSTANKTA = ["25028RN03Y"]

# Om en inloggning ligger längre än så här efter senaste inloggning räknas
# nästa händelse inte automatiskt till den (timmar). Rent informativt.
MAX_SESSION_TIMMAR = 24

# Fält som kan innehålla en tidsstämpel, i prioritetsordning.
TIDSFALT = ["Date", "date", "Time", "time", "Timestamp", "timestamp",
            "CreateTime", "Create Time", "create_time", "DateTime"]


# ---------------------------------------------------------------------------
# Tidstolkning
# ---------------------------------------------------------------------------

def parse_time(value):
    """Tolka TikToks tidsformat → aware datetime (UTC), eller None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # epoch: sekunder eller millisekunder
        v = float(value)
        if v > 1e12:
            v /= 1000.0
        try:
            return datetime.fromtimestamp(v, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if s.isdigit():
            return parse_time(int(s))
        s = s.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def find_timestamp(item):
    """Hitta första användbara tidsstämpeln i en dict → (dt, fältnamn)."""
    if not isinstance(item, dict):
        return None, None
    for key in TIDSFALT:
        if key in item:
            dt = parse_time(item[key])
            if dt:
                return dt, key
    # Sista utväg: valfritt fält vars namn innehåller date/time
    for key, val in item.items():
        if isinstance(key, str) and ("date" in key.lower() or "time" in key.lower()):
            dt = parse_time(val)
            if dt:
                return dt, key
    return None, None


# ---------------------------------------------------------------------------
# Händelse
# ---------------------------------------------------------------------------

class Handelse:
    __slots__ = ("tid", "kategori", "detalj", "ar_inloggning", "enhet", "ip", "_attr")

    def __init__(self, tid, kategori, detalj, ar_inloggning=False, enhet="", ip=""):
        self.tid = tid
        self.kategori = kategori
        self.detalj = detalj
        self.ar_inloggning = ar_inloggning
        self.enhet = enhet
        self.ip = ip
        self._attr = None


def kompakt(item, tidsfalt, maxlen=160):
    """Gör en läsbar rad av en post, utan tidsfältet (visas separat)."""
    bitar = []
    for k, v in item.items():
        if k == tidsfalt:
            continue
        if isinstance(v, (dict, list)):
            continue
        s = str(v).replace("\n", " ").strip()
        if not s:
            continue
        bitar.append(f"{k}={s}")
    rad = " | ".join(bitar)
    return rad[:maxlen] + ("…" if len(rad) > maxlen else "")


def ser_ut_som_inloggning(kategori):
    k = kategori.lower()
    return "login" in k or "inlogg" in k


# ---------------------------------------------------------------------------
# Rekursiv extraktion av alla tidsstämplade poster
# ---------------------------------------------------------------------------

def extrahera(obj, path, ut):
    if isinstance(obj, dict):
        for k, v in obj.items():
            extrahera(v, path + [str(k)], ut)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                dt, tf = find_timestamp(item)
                if dt:
                    kategori = " / ".join(path) or "(okänd)"
                    inlogg = ser_ut_som_inloggning(kategori)
                    enhet = ip = ""
                    if inlogg:
                        enhet = str(item.get("DeviceModel")
                                     or item.get("Device Model")
                                     or item.get("device_model") or "")
                        ip = str(item.get("IP") or item.get("ip") or "")
                    ut.append(Handelse(dt, kategori, kompakt(item, tf),
                                       inlogg, enhet, ip))
                else:
                    extrahera(item, path, ut)
            else:
                # lista av listor e.d.
                extrahera(item, path, ut)


def las_json_filer(root):
    filer = []
    if os.path.isfile(root):
        if root.lower().endswith(".json"):
            filer = [root]
    else:
        for dp, _d, fs in os.walk(root):
            for name in sorted(fs):
                if name.lower().endswith(".json"):
                    filer.append(os.path.join(dp, name))
    return filer


# ---------------------------------------------------------------------------
# Klassning av enhet
# ---------------------------------------------------------------------------

def enhet_status(enhet):
    """→ 'misstänkt' | 'min' | 'okänd'."""
    if not enhet:
        return "okänd"
    if enhet in MISSTANKTA:
        return "misstänkt"
    if MINA_ENHETER and enhet in MINA_ENHETER:
        return "min"
    if MINA_ENHETER and enhet not in MINA_ENHETER:
        return "misstänkt"   # du har listat dina — allt annat är misstänkt
    return "okänd"


# ---------------------------------------------------------------------------
# Analys
# ---------------------------------------------------------------------------

def analysera(handelser):
    handelser.sort(key=lambda h: h.tid)
    inloggningar = [h for h in handelser if h.ar_inloggning]

    # För varje händelse: senaste inloggning <= händelsens tid.
    def senaste_inloggning(t):
        kandidat = None
        for h in inloggningar:
            if h.tid <= t:
                kandidat = h
            else:
                break
        return kandidat

    for h in handelser:
        h._attr = None if h.ar_inloggning else senaste_inloggning(h.tid)
    return inloggningar


def skriv_inventering(handelser, out):
    per_kat = defaultdict(list)
    for h in handelser:
        per_kat[h.kategori].append(h.tid)
    rows = []
    for kat, tider in sorted(per_kat.items(), key=lambda kv: -len(kv[1])):
        rows.append((kat, len(tider), min(tider), max(tider)))

    print("\n" + "=" * 72, file=out)
    print("INVENTERING — all tidsstämplad data i exporten", file=out)
    print("=" * 72, file=out)
    for kat, n, lo, hi in rows:
        print(f"{n:6d}  {kat}", file=out)
        print(f"        {lo.strftime('%Y-%m-%d')} → {hi.strftime('%Y-%m-%d')}",
              file=out)


def skriv_inloggningar(inloggningar, out):
    print("\n" + "=" * 72, file=out)
    print("INLOGGNINGAR", file=out)
    print("=" * 72, file=out)
    if not inloggningar:
        print("Ingen inloggningshistorik hittades i exporten.", file=out)
        return
    for h in inloggningar:
        status = enhet_status(h.enhet)
        flagga = {"misstänkt": "⚠️ MISSTÄNKT", "min": "✅ din",
                  "okänd": "❔ okänd"}[status]
        print(f"{h.tid.strftime('%Y-%m-%d %H:%M:%S')} UTC  {flagga}", file=out)
        print(f"    enhet={h.enhet or '?'}  ip={h.ip or '?'}  {h.detalj}", file=out)


def skriv_misstankt_aktivitet(handelser, out):
    träffar = []
    for h in handelser:
        if h.ar_inloggning:
            continue
        attr = getattr(h, "_attr", None)
        if attr and enhet_status(attr.enhet) == "misstänkt":
            # Bara om inom rimligt sessionsfönster
            delta_h = (h.tid - attr.tid).total_seconds() / 3600.0
            if delta_h <= MAX_SESSION_TIMMAR:
                träffar.append((h, attr, delta_h))

    print("\n" + "=" * 72, file=out)
    print("SANNOLIKT GJORT AV OKÄND ENHET", file=out)
    print("(händelser efter en misstänkt inloggning, inom "
          f"{MAX_SESSION_TIMMAR} h)", file=out)
    print("=" * 72, file=out)
    if not träffar:
        print("Inga händelser kunde knytas till en misstänkt inloggning.", file=out)
        print("(Kontot kan ha varit inloggat sedan tidigare — se hela listan "
              "i CSV:n och jämför själv mot dina egna tider.)", file=out)
        return träffar
    for h, attr, dh in träffar:
        print(f"{h.tid.strftime('%Y-%m-%d %H:%M:%S')} UTC  [{h.kategori}]", file=out)
        print(f"    {h.detalj}", file=out)
        print(f"    ↳ knuten till inloggning {attr.tid.strftime('%Y-%m-%d %H:%M')} "
              f"UTC från {attr.enhet} ({attr.ip}), {dh:.1f} h efter", file=out)
    return träffar


def skriv_csv(handelser, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csvmod.writer(f)
        w.writerow(["tid_utc", "kategori", "ar_inloggning", "enhet",
                    "enhet_status", "ip", "knuten_till_inloggning_utc",
                    "knuten_enhet", "detalj"])
        for h in handelser:
            attr = getattr(h, "_attr", None)
            w.writerow([
                h.tid.strftime("%Y-%m-%d %H:%M:%S"),
                h.kategori,
                "ja" if h.ar_inloggning else "nej",
                h.enhet,
                enhet_status(h.enhet) if h.ar_inloggning else "",
                h.ip,
                attr.tid.strftime("%Y-%m-%d %H:%M:%S") if attr else "",
                attr.enhet if attr else "",
                h.detalj,
            ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Analysera din egen TikTok-dataexport.")
    ap.add_argument("sokvag", help="Export-mapp eller .json-fil")
    ap.add_argument("--rapport", metavar="FIL", help="Skriv läsbar rapport till fil")
    ap.add_argument("--csv", metavar="FIL", help="Skriv alla händelser till CSV")
    args = ap.parse_args(argv)

    if not os.path.exists(args.sokvag):
        print(f"Hittar inte: {args.sokvag}", file=sys.stderr)
        return 2

    filer = las_json_filer(args.sokvag)
    if not filer:
        print("Inga .json-filer hittades. Pekar du på rätt mapp?", file=sys.stderr)
        return 1
    print(f"Läser {len(filer)} JSON-fil(er) …")

    handelser = []
    for fp in filer:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            print(f"  ⚠️  hoppar över {fp}: {e}", file=sys.stderr)
            continue
        extrahera(data, [], handelser)

    if not handelser:
        print("Hittade ingen tidsstämplad data. Är det en JSON-export?", file=sys.stderr)
        return 1

    inloggningar = analysera(handelser)

    skriv_inventering(handelser, sys.stdout)
    skriv_inloggningar(inloggningar, sys.stdout)
    träffar = skriv_misstankt_aktivitet(handelser, sys.stdout)

    print(f"\nTotalt {len(handelser)} händelser, {len(inloggningar)} inloggningar, "
          f"{len(träffar)} knutna till okänd enhet.")

    if args.rapport:
        with open(args.rapport, "w", encoding="utf-8") as f:
            skriv_inventering(handelser, f)
            skriv_inloggningar(inloggningar, f)
            skriv_misstankt_aktivitet(handelser, f)
        print(f"💾 Rapport: {args.rapport}")
    if args.csv:
        skriv_csv(handelser, args.csv)
        print(f"💾 CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
