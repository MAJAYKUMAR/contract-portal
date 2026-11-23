#!/usr/bin/env python3
# Triage a general sweep vs the portal + decided set. Relocated from the
# Nov 23, 2026 4pm ET refresh run (hidden_files/sweep4pm/triage_4pm.py).
# Environment: Python 3. Run-state files (portal snapshot, sweep log) live
# outside the repo; override with PORTAL_HIDDEN_FILES, PORTAL_STATE_FILE,
# PORTAL_SWEEP_LOG. Window start comes from config/config.json.
"""Triage 4pm sweep vs portal + decided set (from 4pm run log + portal file)."""
import json, os, re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
# Run-state files (portal snapshots, sweep logs) live outside the repo in
# the cron worker's hidden_files dir; override with PORTAL_HIDDEN_FILES.
HF = os.environ.get("PORTAL_HIDDEN_FILES",
                    "/home/hatch/workspace/goals/contract-jobs-portal-for-harshitha/hidden_files")
PORTAL = os.environ.get("PORTAL_STATE_FILE",
                       os.path.join(HF, "portal-roles-2026-11-23-2pm.md"))
LOG6PM = os.environ.get("PORTAL_SWEEP_LOG",
                        os.path.join(HF, "run-log-2026-11-23-2pm-et-sweep.md"))
CONFIG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "config", "config.json")))
WINDOW_START = date.fromisoformat(CONFIG["windowStart"])

portal_guids = set()
with open(PORTAL) as f:
    for m in re.finditer(r"dice\.com/job-detail/([0-9a-f-]{36})", f.read()):
        portal_guids.add(m.group(1).lower())
portal_prefixes = {g[:8] for g in portal_guids}

decided = set()
with open(LOG6PM) as f:
    txt = f.read()
decided |= set(re.findall(r"\b[0-9a-f]{8}\b", txt))
decided |= portal_prefixes

with open(os.path.join(HERE, "sweep_all.json")) as f:
    sweep = json.load(f)

seen = {}
for s in sweep["searches"]:
    for j in s["jobs"]:
        g = (j.get("guid") or "").lower()
        if not g:
            continue
        if g not in seen:
            seen[g] = j
unique = list(seen.values())

def is_contract(j):
    return "contract" in (j.get("employmentType") or "").lower()

def posted_ok(j):
    pd = j.get("postedDate") or ""
    try:
        d = date.fromisoformat(pd[:10])
    except Exception:
        return False
    return d >= WINDOW_START

buckets = {"unique": len(unique), "contract": 0, "in_portal": [], "out_of_window": [],
           "reused": [], "fresh": []}
for j in unique:
    if not is_contract(j):
        continue
    buckets["contract"] += 1
    p = j["guid"][:8]
    if j["guid"] in portal_guids or p in portal_prefixes:
        buckets["in_portal"].append(j)
    elif not posted_ok(j):
        buckets["out_of_window"].append(j)
    elif p in decided:
        buckets["reused"].append(j)
    else:
        buckets["fresh"].append(j)

print(f"raw={sweep['total_raw']} unique={buckets['unique']} contract={buckets['contract']}")
print(f"in_portal={len(buckets['in_portal'])} out_of_window={len(buckets['out_of_window'])} reused={len(buckets['reused'])} fresh={len(buckets['fresh'])}")
print("decided_set_size:", len(decided))
print("\nIN PORTAL prefixes:", sorted(j["guid"][:8] for j in buckets["in_portal"]))
print("\nOUT OF WINDOW:")
for j in sorted(buckets["out_of_window"], key=lambda x: x.get("postedDate") or ""):
    print(f"  {j['guid'][:8]} {j.get('title')} | {j.get('company')} | {j.get('location')} | {j.get('postedDate','')[:10]}")
print("\nREUSED prefixes:", sorted(j["guid"][:8] for j in buckets["reused"]))
print("\nFRESH:")
for j in buckets["fresh"]:
    print(f"  {j['guid']} | {j.get('title')} | {j.get('company')} | {j.get('location')} | remote={j.get('isRemote')} | {j.get('postedDate')} | {j.get('employmentType')} | salary={j.get('salary')}")

with open(os.path.join(HERE, "triage.json"), "w") as f:
    json.dump({"buckets": {k: (v if isinstance(v, int) else [x["guid"] for x in v]) for k, v in buckets.items()},
               "fresh": buckets["fresh"], "out_of_window": buckets["out_of_window"],
               "decided_set": sorted(decided)}, f, indent=1)
