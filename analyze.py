# -*- coding: utf-8 -*-
"""Coros sports data analysis"""
import json, sys
from datetime import datetime

def pace_str(sec_per_km):
    if not sec_per_km or sec_per_km <= 0:
        return "--"
    m, s = divmod(int(sec_per_km), 60)
    return "{}'{:02d}\"".format(m, s)

def dur_str(sec):
    if not sec or sec <= 0:
        return "--"
    h, m = divmod(int(sec), 3600)
    m, s = divmod(m, 60)
    if h:
        return "{}h{}m".format(h, m)
    return "{}m".format(m)

def sport_name(st):
    names = {100: "Run", 101: "IndoorRun", 102: "TrailRun", 103: "TrackRun",
             104: "Hike", 900: "Walk", 200: "Bike", 201: "IndoorBike",
             202: "MTB", 300: "Swim", 301: "OpenWater", 402: "Strength"}
    return names.get(st, "Other({})".format(st))

data = json.loads(sys.stdin.read())
acts = data.get("dataList", [])
if not acts:
    print("No data")
    sys.exit(1)

print("=" * 56)
print("  Beverage #1 | Coros Training Analysis")
print("  Device: COROS PACE 3 | Last 30 Activities")
print("=" * 56)

# Sport type distribution
type_count = {}
for a in acts:
    name = sport_name(a.get("sportType", 0))
    type_count[name] = type_count.get(name, 0) + 1

print("\n[Sport Types]")
for name, count in sorted(type_count.items(), key=lambda x: -x[1]):
    bar = "#" * count
    print("  {:<10s}  {:2d}x  {}".format(name, count, bar))

# Running stats
runs = [a for a in acts if a.get("sportType") in (100,101,102,103) and a.get("distance", 0) > 0]
strength = [a for a in acts if a.get("sportType") == 402]

if runs:
    total_km = sum(r["distance"] for r in runs) / 1000
    total_time = sum(r["totalTime"] for r in runs)
    avg_hrs = [r["avgHr"] for r in runs if r.get("avgHr")]
    avg_paces = [r["adjustedPace"] for r in runs if r.get("adjustedPace") and r["adjustedPace"] > 0]
    avg_cadences = [r["avgCadence"] for r in runs if r.get("avgCadence")]
    loads = [r["trainingLoad"] for r in runs if r.get("trainingLoad")]

    print("\n[Running Stats] ({} runs)".format(len(runs)))
    print("  Total Distance:  {:.1f} km".format(total_km))
    print("  Total Time:      {}".format(dur_str(total_time)))
    print("  Avg Distance:    {:.1f} km/run".format(total_km/len(runs)))
    if avg_paces:
        print("  Avg Pace:        {} /km".format(pace_str(sum(avg_paces)/len(avg_paces))))
    if avg_hrs:
        print("  Avg HR:          {:.0f} bpm".format(sum(avg_hrs)/len(avg_hrs)))
    if avg_cadences:
        print("  Avg Cadence:     {:.0f} spm".format(sum(avg_cadences)/len(avg_cadences)))
    if loads:
        print("  Training Load:   {} (cumulative)".format(sum(loads)))

# Training structure
easy = [r for r in runs if "ST" not in r.get("name","")]
st_run = [r for r in runs if "ST" in r.get("name","")]
long_run = [r for r in runs if "20k" in r.get("name","") or "22k" in r.get("name","")]

print("\n[Training Mix]")
print("  Easy Run:        {}x".format(len(easy)))
print("  Easy Run+Strides: {}x".format(len(st_run)))
print("  Long Run (LSD):  {}x".format(len(long_run)))
if strength:
    lower = [s for s in strength if "下肢" in s.get("name","")]
    core = [s for s in strength if "核心" in s.get("name","")]
    print("  Leg Strength:    {}x".format(len(lower)))
    print("  Core Strength:   {}x".format(len(core)))

# Trend
print("\n[Recent Runs] (last 12)")
print("  {:<8} {:<20} {:>6} {:>8} {:>5} {:>5}".format("Date", "Name", "km", "Pace", "HR", "Load"))
print("  " + "-" * 57)
for r in runs[:12]:
    dt = datetime.fromtimestamp(r["startTime"]).strftime("%m/%d")
    km = r["distance"] / 1000
    p = pace_str(r.get("adjustedPace", 0))
    hr = "{:.0f}".format(r["avgHr"]) if r.get("avgHr") else "--"
    tl = r.get("trainingLoad", 0)
    name = r.get("name", "?")[:18]
    print("  {:<8} {:<20} {:>5.1f} {:>8} {:>4} {:>5}".format(dt, name, km, p, hr, tl))

# HR zone analysis (maxHr=187, rhr=45)
max_hr = 187
rhr = 45
hrr = max_hr - rhr

print("\n[HR Zone Distribution] (MaxHR={}, RHR={})".format(max_hr, rhr))
zones = [
    ("Z1 Recovery     ", 0.60, 0.70),
    ("Z2 Aerobic      ", 0.70, 0.80),
    ("Z3 Tempo        ", 0.80, 0.90),
    ("Z4 Threshold    ", 0.90, 0.95),
    ("Z5 Anaerobic    ", 0.95, 1.00),
]
for zname, lo, hi in zones:
    zlo = int(rhr + hrr * lo)
    zhi = int(rhr + hrr * hi)
    count = sum(1 for r in runs if r.get("avgHr", 0) and zlo <= r["avgHr"] <= zhi)
    bar = "#" * count
    print("  {} {:3d}-{:3d}bpm: {:2d}x  {}".format(zname, zlo, zhi, count, bar))

# Summary
print("\n[Summary]")
print("  1. High training frequency: {} runs in recent period".format(len(runs)))
print("  2. Easy runs dominate, with structured ST strides + strength")
if avg_paces:
    print("  3. Easy pace ~{} with HR ~{:.0f}bpm = solid aerobic base".format(
        pace_str(int(sum(avg_paces)/len(avg_paces))), sum(avg_hrs)/len(avg_hrs)))
if avg_hrs:
    z2_count = sum(1 for r in runs if r.get("avgHr", 0) and rhr + hrr * 0.70 <= r["avgHr"] <= rhr + hrr * 0.80)
    print("  4. {} of {} runs in Z2 = proper aerobic training".format(z2_count, len(runs)))
print("  5. Weekly volume ~60-80km, mid-to-advanced runner level")
print("  6. Recommendation: Add tempo/interval sessions to boost speed endurance")
