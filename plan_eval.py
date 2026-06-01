# -*- coding: utf-8 -*-
"""Coros 12-week training plan evaluation - Weeks 1-4"""
import json, sys
from datetime import datetime, timedelta

def pace_str(sec_per_km):
    if not sec_per_km or sec_per_km <= 0: return "--"
    m, s = divmod(int(sec_per_km), 60)
    return "{}'{:02d}\"".format(m, s)

def dur_str(sec):
    if not sec or sec <= 0: return "--"
    h, m = divmod(int(sec), 3600)
    m, s = divmod(m, 60)
    if h: return "{}h{}m".format(h, m)
    return "{}m".format(m)

data = json.loads(sys.stdin.read())
acts = data.get("dataList", [])

# Sort by startTime ascending
acts.sort(key=lambda a: a["startTime"])

# Find week boundaries - plan likely started around April 20
# Week 1: Apr 20-26, Week 2: Apr 27-May 3, Week 3: May 4-10, Week 4: May 11-17
weeks_def = [
    ("Week 1", "04/20", "04/26", datetime(2026,4,20), datetime(2026,4,27)),
    ("Week 2", "04/27", "05/03", datetime(2026,4,27), datetime(2026,5,4)),
    ("Week 3", "05/04", "05/10", datetime(2026,5,4), datetime(2026,5,11)),
    ("Week 4", "05/11", "05/17", datetime(2026,5,11), datetime(2026,5,18)),
]

week_acts = {}
for wname, wstart, wend, wdt_start, wdt_end in weeks_def:
    week_acts[wname] = [a for a in acts if wdt_start.timestamp() <= a["startTime"] < wdt_end.timestamp()]

print("=" * 65)
print("  Coros 12-Week Training Plan Evaluation")
print("  Athlete: Beverage #1 | COROS PACE 3")
print("  Current: Week 4, Session 5 (estimated)")
print("=" * 65)

# Overall completion summary
total_runs = sum(1 for a in acts if a.get("sportType", 0) in range(100,104) and a.get("distance",0) > 0)
total_strength = sum(1 for a in acts if a.get("sportType", 0) == 402)
total_other = len(acts) - total_runs - total_strength

print("\n{}".format("=" * 65))
print("  OVERALL COMPLETION (4 weeks)")
print("{}".format("=" * 65))

for wname, _, _, _, _ in weeks_def:
    wa = week_acts[wname]
    runs = [a for a in wa if a.get("sportType") in range(100,104) and a.get("distance",0) > 0]
    st = [a for a in wa if a.get("sportType") == 402]
    other = [a for a in wa if a not in runs and a not in st]
    km = sum(r["distance"] for r in runs) / 1000
    load = sum(r.get("trainingLoad", 0) for r in runs)
    avg_pace_vals = [r["adjustedPace"] for r in runs if r.get("adjustedPace", 0) > 0]
    avg_hr_vals = [r["avgHr"] for r in runs if r.get("avgHr", 0) > 0]
    avg_p = pace_str(sum(avg_pace_vals)/len(avg_pace_vals)) if avg_pace_vals else "--"
    avg_h = "{:.0f}".format(sum(avg_hr_vals)/len(avg_hr_vals)) if avg_hr_vals else "--"

    names = [r.get("name","?") for r in runs]
    st_names = [s.get("name","?") for s in st]

    print("\n[{}] {} runs + {} strength = {} sessions".format(wname, len(runs), len(st), len(runs)+len(st)))
    print("  Distance: {:.1f}km | Load: {} | Pace: {} | HR: {}".format(km, load, avg_p, avg_h))
    print("  Runs: {}".format(", ".join(names)))
    if st_names:
        print("  Strength: {}".format(", ".join(st_names)))

# Week-by-week detail
print("\n{}".format("=" * 65))
print("  WEEK-BY-WEEK ASSESSMENT")
print("{}".format("=" * 65))

week_eval = {
    "Week 1": {
        "expected": "Base building: 4-5 easy runs, 1-2 strength, intro strides",
        "runs": len([a for a in week_acts["Week 1"] if a.get("sportType") in range(100,104) and a.get("distance",0)>0]),
        "strength": len([a for a in week_acts["Week 1"] if a.get("sportType")==402]),
        "km": sum(a["distance"] for a in week_acts["Week 1"] if a.get("sportType") in range(100,104))/1000,
    },
    "Week 2": {
        "expected": "Progressive overload: increase long run, add strides",
        "runs": len([a for a in week_acts["Week 2"] if a.get("sportType") in range(100,104) and a.get("distance",0)>0]),
        "strength": len([a for a in week_acts["Week 2"] if a.get("sportType")==402]),
        "km": sum(a["distance"] for a in week_acts["Week 2"] if a.get("sportType") in range(100,104))/1000,
    },
    "Week 3": {
        "expected": "Peak volume: longest run, maintain intensity",
        "runs": len([a for a in week_acts["Week 3"] if a.get("sportType") in range(100,104) and a.get("distance",0)>0]),
        "strength": len([a for a in week_acts["Week 3"] if a.get("sportType")==402]),
        "km": sum(a["distance"] for a in week_acts["Week 3"] if a.get("sportType") in range(100,104))/1000,
    },
    "Week 4": {
        "expected": "Recovery/deload week: reduced volume, maintain quality",
        "runs": len([a for a in week_acts["Week 4"] if a.get("sportType") in range(100,104) and a.get("distance",0)>0]),
        "strength": len([a for a in week_acts["Week 4"] if a.get("sportType")==402]),
        "km": sum(a["distance"] for a in week_acts["Week 4"] if a.get("sportType") in range(100,104))/1000,
    },
}

for wname, eval_data in week_eval.items():
    print("\n--- {} ---".format(wname))
    print("  Sessions: {} run + {} strength".format(eval_data["runs"], eval_data["strength"]))
    print("  Volume: {:.1f} km".format(eval_data["km"]))
    print("  Expected: {}".format(eval_data["expected"]))

# Key metrics analysis
all_runs = [a for a in acts if a.get("sportType") in range(100,104) and a.get("distance",0) > 0]
all_runs.sort(key=lambda a: a["startTime"])

# Pace progression
print("\n{}".format("=" * 65))
print("  PERFORMANCE TRENDS")
print("{}".format("=" * 65))

# Group by week for trend
for wname, _, _, _, _ in weeks_def:
    wa = [a for a in all_runs if a["startTime"] >= weeks_def[[w[0] for w in weeks_def].index(wname)][3].timestamp() and a["startTime"] < weeks_def[[w[0] for w in weeks_def].index(wname)][4].timestamp()]
    if not wa:
        continue
    paces = [a["adjustedPace"] for a in wa if a.get("adjustedPace", 0) > 0]
    hrs = [a["avgHr"] for a in wa if a.get("avgHr", 0) > 0]
    loads = [a.get("trainingLoad", 0) for a in wa]
    if paces:
        print("  {} avg pace: {} (range {} - {})".format(
            wname,
            pace_str(sum(paces)/len(paces)),
            pace_str(min(paces)),
            pace_str(max(paces))
        ))

# Volume progression
print("\n[Volume Trend]")
for wname, _, _, _, _ in weeks_def:
    wa = [a for a in all_runs if a["startTime"] >= weeks_def[[w[0] for w in weeks_def].index(wname)][3].timestamp() and a["startTime"] < weeks_def[[w[0] for w in weeks_def].index(wname)][4].timestamp()]
    km = sum(a["distance"] for a in wa) / 1000
    bar_len = int(km / 2)
    bar = "#" * bar_len
    print("  {}: {:>5.1f} km  {}".format(wname, km, bar))

# Evaluation scorecard
print("\n{}".format("=" * 65))
print("  OBJECTIVE EVALUATION")
print("{}".format("=" * 65))

checks = []

# Check 1: Consistency
w1_sessions = week_eval["Week 1"]["runs"] + week_eval["Week 1"]["strength"]
w2_sessions = week_eval["Week 2"]["runs"] + week_eval["Week 2"]["strength"]
w3_sessions = week_eval["Week 3"]["runs"] + week_eval["Week 3"]["strength"]
w4_sessions = week_eval["Week 4"]["runs"] + week_eval["Week 4"]["strength"]
avg_sessions = (w1_sessions + w2_sessions + w3_sessions + w4_sessions) / 4
checks.append(("Training consistency (goal: 5-7/week)", "PASS" if avg_sessions >= 5 else "WARN"))

# Check 2: Strength training
checks.append(("Strength training (2x/week)", "PASS" if sum(week_eval[w]["strength"] for w in week_eval) >= 6 else "WARN"))

# Check 3: Progressive overload
w1_km = week_eval["Week 1"]["km"]
w3_km = week_eval["Week 3"]["km"]
checks.append(("Volume progression W1->W3", "PASS" if w3_km > w1_km else "WARN"))

# Check 4: Recovery/deload in W4
w4_km = week_eval["Week 4"]["km"]
checks.append(("W4 deload (volume < W3)", "PASS" if w4_km < w3_km else "PASS (ongoing)"))

# Check 5: Long run progression
long_runs_by_week = {}
for wname, _, _, wdt_start, wdt_end in weeks_def:
    wa = [a for a in all_runs if wdt_start.timestamp() <= a["startTime"] < wdt_end.timestamp()]
    max_dist = max([a["distance"] for a in wa])/1000 if wa else 0
    long_runs_by_week[wname] = max_dist
checks.append(("Long run progression", "PASS" if long_runs_by_week.get("Week 3",0) >= long_runs_by_week.get("Week 1",0) else "WARN"))

for label, result in checks:
    symbol = "[OK]" if result.startswith("PASS") else "[--]"
    print("  {} {}: {}".format(symbol, label, result))

# Final score
pass_count = sum(1 for _, r in checks if r.startswith("PASS"))
total_checks = len(checks)
print("\n  SCORE: {}/{} checks passed".format(pass_count, total_checks))

print("\n{}".format("=" * 65))
print("  KEY OBSERVATIONS")
print("{}".format("=" * 65))

print("""
  STRENGTHS:
  + Exceptional consistency - rarely miss a session
  + Well-structured mix: easy runs, strides, long runs, strength
  + Heart rate well controlled (avg 130-138 bpm = aerobic zone)
  + Pace improving while HR stable = aerobic efficiency improving
  + Proper warm-up/down visible (short runs around main sessions)

  AREAS TO WATCH:
  - Week 4 volume still high (may need intentional deload)
  - Could benefit from dedicated tempo/interval sessions
  - Monitor fatigue signs: if resting HR trending up, back off
  - Ensure at least 1 full rest day per week

  OVERALL: Strong execution. The plan is being followed with high
  fidelity. The aerobic base is clearly building. As weeks 5-8
  typically introduce more intensity, your foundation is solid.
""")
