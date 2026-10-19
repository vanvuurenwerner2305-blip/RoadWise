"""RoadWise test: does TomTom predict holiday traffic, or just a typical weekday?

Run on Windows:  py roadwise_test.py
It asks for your TomTom API key (or reads it from key.txt next to this file).
Results are printed and saved to roadwise_test_results.csv.
"""
import csv, json, os, sys, time, urllib.request, urllib.error

PLACES = {
    "Pretoria": (-25.7479, 28.2293),
    "Polokwane": (-23.9045, 29.4689),
    "Beaufort West": (-32.3567, 22.5829),
}
# (from, to, date, note) - every trip departs at 08:00
TESTS = [
    ("Pretoria", "Polokwane", "2026-11-10", "normal Tuesday"),
    ("Pretoria", "Polokwane", "2026-11-13", "normal Friday"),
    ("Pretoria", "Polokwane", "2026-12-11", "Friday after schools close"),
    ("Pretoria", "Polokwane", "2026-12-18", "Friday before Christmas"),
    ("Pretoria", "Polokwane", "2026-12-25", "Christmas Day"),
    ("Pretoria", "Beaufort West", "2026-11-10", "normal Tuesday"),
    ("Pretoria", "Beaufort West", "2026-11-13", "normal Friday"),
    ("Pretoria", "Beaufort West", "2026-12-11", "Friday after schools close"),
    ("Pretoria", "Beaufort West", "2026-12-18", "Friday before Christmas"),
    ("Pretoria", "Beaufort West", "2026-12-25", "Christmas Day"),
    ("Beaufort West", "Pretoria", "2027-01-03", "New Year return Sunday"),
    ("Beaufort West", "Pretoria", "2027-01-17", "normal Sunday"),
]
TIME = "08:00:00"

def get_key():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "key.txt")
    if os.path.exists(path):
        return open(path).read().strip()
    return input("Paste your TomTom API key: ").strip()

def route(key, a, b, date):
    (la, lo), (lb, lob) = PLACES[a], PLACES[b]
    url = (f"https://api.tomtom.com/routing/1/calculateRoute/{la},{lo}:{lb},{lob}/json"
           f"?key={key}&departAt={date}T{TIME}&traffic=true&computeTravelTimeFor=all&routeType=fastest")
    with urllib.request.urlopen(url, timeout=30) as r:
        s = json.load(r)["routes"][0]["summary"]
    return s

def mins(sec):
    return round(sec / 60) if sec is not None else None

def main():
    key = get_key()
    rows = []
    print(f"{'Trip':32} {'Date':11} {'Note':28} {'Predicted':>9} {'No traffic':>10} {'Extra':>6}")
    for a, b, date, note in TESTS:
        try:
            s = route(key, a, b, date)
        except urllib.error.HTTPError as e:
            print(f"{a} -> {b} {date}: HTTP {e.code} {e.read()[:200]!r}")
            if e.code in (401, 403):
                print("The key was refused. Check it in your TomTom dashboard.")
                return
            continue
        except Exception as e:
            print(f"{a} -> {b} {date}: {e}")
            continue
        pred = mins(s.get("travelTimeInSeconds"))
        free = mins(s.get("noTrafficTravelTimeInSeconds"))
        hist = mins(s.get("historicTrafficTravelTimeInSeconds"))
        extra = pred - free if pred is not None and free is not None else None
        trip = f"{a} -> {b}"
        print(f"{trip:32} {date:11} {note:28} {pred:>8}m {free:>9}m {extra:>5}m")
        rows.append({"from": a, "to": b, "date": date, "depart": TIME, "note": note,
                     "predicted_min": pred, "no_traffic_min": free, "historic_min": hist,
                     "extra_min": extra, "length_km": round(s.get("lengthInMeters", 0) / 1000)})
        time.sleep(0.3)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roadwise_test_results.csv")
    if rows:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"\nSaved {len(rows)} results to {out}")

if __name__ == "__main__":
    main()
    if sys.platform.startswith("win"):
        input("\nPress Enter to close")
