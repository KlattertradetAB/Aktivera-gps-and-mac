#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
las-historik.py — läs din EGNA platshistorik från Google och se var du varit.

Det här skriptet läser en historik du själv laddat ner från Google (Takeout
eller Tidslinje-exporten från telefonen). Det hämtar INGENTING från din telefon
och kontaktar ingen tjänst — det läser bara en fil du redan har på disken.
All data stannar lokalt.

Google sparar historiken i några olika format genom åren. Skriptet känner igen
alla de vanliga automatiskt:

  1. Records.json            — rå platshistorik (latitudeE7/longitudeE7)
  2. Semantic Location History/YYYY/YYYY_MÅNAD.json — besök + resor per månad
  3. location-history.json / Timeline.json — nyare export från telefonen
     (semanticSegments med "latLng"-strängar)

Användning:
    python3 las-historik.py SÖKVÄG [--csv ut.csv] [--fran 2024-01-01] [--till 2024-12-31]

    SÖKVÄG kan vara en enskild .json-fil ELLER en mapp (t.ex. hela Takeout-
    mappen) — då söks alla .json-filer igenom rekursivt.

Exempel:
    python3 las-historik.py Takeout/                  # läs allt, skriv sammanfattning
    python3 las-historik.py Records.json --csv mina-punkter.csv
    python3 las-historik.py Takeout/ --fran 2023-06-01 --till 2023-06-30

Endast Pythons standardbibliotek används.
"""

import argparse
import csv as csvmod
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Tidsstämpel-tolkning
# ---------------------------------------------------------------------------

def parse_time(value):
    """Tolka Googles olika tidsformat → aware datetime (UTC), eller None."""
    if value is None:
        return None
    # Millisekunder sedan epoch (sträng eller int), t.ex. "1609459200000"
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        try:
            return datetime.fromtimestamp(int(value) / 1000.0, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    # ISO 8601, t.ex. "2021-01-01T00:00:00Z" eller med offset
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def parse_latlng_string(s):
    """'59.3293°, 18.0686°' eller '59.3293, 18.0686' → (lat, lng) eller None."""
    if not isinstance(s, str):
        return None
    cleaned = s.replace("°", "").replace("geo:", "")
    parts = cleaned.split(",")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None


def e7(value):
    """latitudeE7/longitudeE7 (heltal × 1e7) → grader, eller None."""
    if value is None:
        return None
    try:
        return int(value) / 1e7
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# En punkt = (tid, lat, lng, källa, etikett)
# ---------------------------------------------------------------------------

class Point:
    __slots__ = ("time", "lat", "lng", "kind", "label")

    def __init__(self, time, lat, lng, kind, label=""):
        self.time = time
        self.lat = lat
        self.lng = lng
        self.kind = kind      # "raw", "visit", "activity", "path"
        self.label = label    # ev. platsnamn/adress


# ---------------------------------------------------------------------------
# Format-igenkännare. Var och en tar inläst JSON (dict) → yield Point.
# ---------------------------------------------------------------------------

def from_records(data):
    """Records.json: {"locations": [{latitudeE7, longitudeE7, timestamp...}]}"""
    locs = data.get("locations")
    if not isinstance(locs, list):
        return
    for item in locs:
        if not isinstance(item, dict):
            continue
        lat = e7(item.get("latitudeE7"))
        lng = e7(item.get("longitudeE7"))
        if lat is None or lng is None:
            continue
        t = parse_time(item.get("timestamp") or item.get("timestampMs"))
        yield Point(t, lat, lng, "raw")


def _semantic_point_from_place(place):
    """Plocka lat/lng + namn ur en placeVisit.location."""
    if not isinstance(place, dict):
        return None, None, ""
    lat = e7(place.get("latitudeE7"))
    lng = e7(place.get("longitudeE7"))
    name = place.get("name") or place.get("address") or ""
    return lat, lng, (name or "").replace("\n", " ")


def from_semantic(data):
    """Semantic Location History: {"timelineObjects": [{placeVisit|activitySegment}]}"""
    objs = data.get("timelineObjects")
    if not isinstance(objs, list):
        return
    for obj in objs:
        if not isinstance(obj, dict):
            continue
        if "placeVisit" in obj:
            pv = obj["placeVisit"]
            loc = pv.get("location", {}) if isinstance(pv, dict) else {}
            lat, lng, name = _semantic_point_from_place(loc)
            dur = pv.get("duration", {}) if isinstance(pv, dict) else {}
            t = parse_time(dur.get("startTimestamp") or dur.get("startTimestampMs"))
            if lat is not None and lng is not None:
                yield Point(t, lat, lng, "visit", name)
        elif "activitySegment" in obj:
            seg = obj["activitySegment"]
            if not isinstance(seg, dict):
                continue
            dur = seg.get("duration", {})
            for key, kind in (("startLocation", "activity"), ("endLocation", "activity")):
                loc = seg.get(key, {})
                lat = e7(loc.get("latitudeE7")) if isinstance(loc, dict) else None
                lng = e7(loc.get("longitudeE7")) if isinstance(loc, dict) else None
                if lat is not None and lng is not None:
                    t = parse_time(dur.get("startTimestamp") or dur.get("startTimestampMs"))
                    yield Point(t, lat, lng, "activity", seg.get("activityType", ""))


def from_semantic_segments(data):
    """Nyare telefon-export: {"semanticSegments": [...]} med latLng-strängar."""
    segs = data.get("semanticSegments")
    if not isinstance(segs, list):
        return
    for seg in segs:
        if not isinstance(seg, dict):
            continue
        start_t = parse_time(seg.get("startTime"))
        # Enskilt besök
        visit = seg.get("visit")
        if isinstance(visit, dict):
            tl = visit.get("topCandidate", {})
            pll = tl.get("placeLocation", {}) if isinstance(tl, dict) else {}
            ll = parse_latlng_string(pll.get("latLng") if isinstance(pll, dict) else None)
            if ll:
                yield Point(start_t, ll[0], ll[1], "visit",
                            (tl.get("semanticType") or "") if isinstance(tl, dict) else "")
        # Rutt (en rad punkter med tid)
        path = seg.get("timelinePath")
        if isinstance(path, list):
            for p in path:
                if not isinstance(p, dict):
                    continue
                ll = parse_latlng_string(p.get("point"))
                if ll:
                    t = parse_time(p.get("time")) or start_t
                    yield Point(t, ll[0], ll[1], "path")
        # Resa mellan två punkter
        activity = seg.get("activity")
        if isinstance(activity, dict):
            for key in ("start", "end"):
                node = activity.get(key, {})
                ll = parse_latlng_string(node.get("latLng") if isinstance(node, dict) else None)
                if ll:
                    yield Point(start_t, ll[0], ll[1], "activity",
                                activity.get("topCandidate", {}).get("type", "")
                                if isinstance(activity.get("topCandidate"), dict) else "")


def from_toplevel_list(data):
    """Vissa telefon-exporter är en ren lista på toppnivå med 'startTime'/'visit'."""
    # Hanteras genom att vi wrappar den i semanticSegments i load_json_points.
    return
    yield  # pragma: no cover


RECOGNIZERS = (from_records, from_semantic, from_semantic_segments)


def load_json_points(path):
    """Läs en .json-fil och ge alla punkter vi hittar, oavsett format."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        print(f"  ⚠️  hoppar över {path}: {exc}", file=sys.stderr)
        return

    # Toppnivå-lista (nyare telefon-format) → behandla som semanticSegments.
    if isinstance(data, list):
        data = {"semanticSegments": data}

    if not isinstance(data, dict):
        return

    found = False
    for rec in RECOGNIZERS:
        for pt in rec(data):
            found = True
            yield pt
    if not found:
        # Tyst — många filer i en Takeout-mapp är inte platsdata.
        pass


def iter_json_files(root):
    """Ge alla .json-filer under root (fil eller mapp)."""
    if os.path.isfile(root):
        if root.lower().endswith(".json"):
            yield root
        return
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            if name.lower().endswith(".json"):
                yield os.path.join(dirpath, name)


# ---------------------------------------------------------------------------
# Sammanställning
# ---------------------------------------------------------------------------

def haversine_m(a_lat, a_lng, b_lat, b_lng):
    """Avstånd i meter mellan två koordinater."""
    r = 6371000.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dlmb = math.radians(b_lng - a_lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def summarize(points):
    """Skriv en kort överblick till terminalen."""
    if not points:
        print("\nHittade inga platspunkter i det du pekade på.")
        print("Kontrollera att du laddat ner 'Platshistorik' / 'Location History'")
        print("från takeout.google.com och packat upp zip-filen.")
        return

    timed = [p for p in points if p.time is not None]
    print(f"\n✅ Hittade {len(points):,} platspunkter".replace(",", " "))
    if timed:
        timed.sort(key=lambda p: p.time)
        first = timed[0].time.astimezone().strftime("%Y-%m-%d")
        last = timed[-1].time.astimezone().strftime("%Y-%m-%d")
        print(f"   Period: {first} → {last}")

    by_kind = defaultdict(int)
    for p in points:
        by_kind[p.kind] += 1
    namn = {"raw": "råa GPS-punkter", "visit": "besök",
            "activity": "resor", "path": "rutt-punkter"}
    print("   Typer:", ", ".join(f"{by_kind[k]} {namn.get(k, k)}"
                                  for k in sorted(by_kind)))

    # Dagar med data
    days = sorted({p.time.astimezone().date() for p in timed})
    if days:
        print(f"   Dagar med data: {len(days)}")

    # Namngivna besök — vanligaste platserna
    named = defaultdict(int)
    for p in points:
        if p.kind == "visit" and p.label:
            named[p.label] += 1
    if named:
        print("\n   Vanligaste namngivna platserna:")
        for label, n in sorted(named.items(), key=lambda kv: -kv[1])[:10]:
            print(f"     {n:3d}×  {label}")

    # Grov uppskattad total sträcka från råa/rutt-punkter
    seq = [p for p in timed if p.kind in ("raw", "path")]
    if len(seq) > 1:
        dist = 0.0
        for a, b in zip(seq, seq[1:]):
            d = haversine_m(a.lat, a.lng, b.lat, b.lng)
            if d < 200000:  # hoppa orimliga hopp (>200 km mellan två punkter)
                dist += d
        print(f"\n   Grovt uppskattad total rörelse: {dist/1000:,.0f} km"
              .replace(",", " "))


def write_csv(points, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csvmod.writer(f)
        w.writerow(["tid_lokal", "tid_utc", "latitud", "longitud", "typ", "etikett"])
        for p in sorted(points, key=lambda p: (p.time or datetime.min.replace(tzinfo=timezone.utc))):
            if p.time:
                lokal = p.time.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                utc = p.time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                lokal = utc = ""
            w.writerow([lokal, utc, f"{p.lat:.6f}", f"{p.lng:.6f}", p.kind, p.label])
    print(f"\n💾 Skrev {len(points)} punkter till {path}")
    print("   Öppna i t.ex. Excel/Numbers, eller importera till en karttjänst.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Läs din egen nedladdade Google-platshistorik.")
    ap.add_argument("sokvag", help="Fil eller mapp med din nedladdade historik")
    ap.add_argument("--csv", metavar="FIL", help="Skriv alla punkter till en CSV-fil")
    ap.add_argument("--fran", metavar="ÅÅÅÅ-MM-DD", help="Ta bara med från detta datum")
    ap.add_argument("--till", metavar="ÅÅÅÅ-MM-DD", help="Ta bara med till detta datum")
    args = ap.parse_args(argv)

    if not os.path.exists(args.sokvag):
        print(f"Hittar inte: {args.sokvag}", file=sys.stderr)
        return 2

    def bound(s):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Felaktigt datum: {s} (använd ÅÅÅÅ-MM-DD)", file=sys.stderr)
            sys.exit(2)

    fran, till = bound(args.fran), bound(args.till)
    if till:
        till = till.replace(hour=23, minute=59, second=59)

    files = list(iter_json_files(args.sokvag))
    if not files:
        print("Inga .json-filer hittades. Pekar du på rätt mapp?", file=sys.stderr)
        return 1
    print(f"Läser {len(files)} JSON-fil(er) …")

    points = []
    for fp in files:
        for p in load_json_points(fp):
            if fran and (p.time is None or p.time < fran):
                continue
            if till and (p.time is None or p.time > till):
                continue
            points.append(p)

    summarize(points)
    if args.csv:
        write_csv(points, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
