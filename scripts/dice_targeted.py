#!/usr/bin/env python3
# Targeted Dice searches (title + location queries). Relocated from the
# Nov 23, 2026 4pm ET refresh run (hidden_files/sweep4pm/dice_targeted_4pm.py).
# Environment: Python 3 + requests. Edit TARGETED for the next run's queries.
"""Targeted Dice searches — 2pm ET run, Nov 23 2026. Cards tagged with _search."""
import json, os, sys, time
import dice_sweep as d

HERE = os.path.dirname(os.path.abspath(__file__))

TARGETED = [
    ("Supercomputing", 1, None),
    ("Sr. AI Engineer", 1, "Remote"),
    ("AI Data Engineer", 1, "Remote"),
    ("Sr MLOps Engineer", 1, "Remote"),
    ("Lead AI/ML Engineer", 1, "Remote"),
]

out = {"searches": []}
for q, pg, loc in TARGETED:
    jobs, code = None, 0
    for attempt in range(2):
        try:
            jobs, code = d.fetch(q, pg, loc)
            if jobs:
                break
            print(f"  retry {q} (no jobList, attempt {attempt+1})", file=sys.stderr)
            time.sleep(8)
        except Exception as e:
            print(f"  RETRY {q}: {e}", file=sys.stderr)
            time.sleep(8)
            jobs, code = [], 0
    recs = []
    for j in jobs or []:
        recs.append({
            "guid": j.get("guid"), "title": j.get("title"),
            "company": j.get("companyName"),
            "location": (j.get("jobLocation") or {}).get("displayName"),
            "isRemote": j.get("isRemote"), "postedDate": j.get("postedDate"),
            "employmentType": j.get("employmentType"), "salary": j.get("salary"),
            "_search": q + (f" loc={loc}" if loc else ""),
        })
    out["searches"].append({"query": q, "location": loc, "status": code,
                            "count": len(recs), "jobs": recs})
    print(f"{q} loc={loc}: {len(recs)} cards (HTTP {code})")
    time.sleep(2)
with open(os.path.join(HERE, "targeted.json"), "w") as f:
    json.dump(out, f, indent=1)
print("TARGETED TOTAL:", sum(s["count"] for s in out["searches"]))
