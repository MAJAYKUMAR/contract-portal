#!/usr/bin/env python3
# Triage a targeted sweep vs the portal + decided set. Relocated from the
# Nov 23, 2026 4pm ET refresh run (hidden_files/sweep4pm/targeted_triage_4pm.py).
# Environment: Python 3. Run-state files live outside the repo; override
# with PORTAL_HIDDEN_FILES, PORTAL_STATE_FILE, PORTAL_SWEEP_LOG.
# Window start comes from config/config.json.
"""Targeted triage — 4pm ET run. Same buckets as main triage, per-search."""
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
decided = set(re.findall(r"\b[0-9a-f]{8}\b", open(LOG6PM).read())) | portal_prefixes

with open(os.path.join(HERE, "targeted.json")) as f:
    tgt = json.load(f)

seen = {}
for s in tgt["searches"]:
    for j in s["jobs"]:
        g = (j.get("guid") or "").lower()
        if g and g not in seen:
            seen[g] = j

def is_contract(j):
    return "contract" in (j.get("employmentType") or "").lower()

def posted_ok(j):
    try:
        return date.fromisoformat((j.get("postedDate") or "")[:10]) >= WINDOW_START
    except Exception:
        return False

tot = {"contract": 0, "in_portal": [], "out_of_window": [], "reused": [], "fresh": []}
per_search = {}
for s in tgt["searches"]:
    ps = {"contract": 0, "in_portal": [], "out_of_window": [], "reused": [], "fresh": []}
    for j in s["jobs"]:
        if not is_contract(j):
            continue
        ps["contract"] += 1
        p = j["guid"][:8]
        if j["guid"] in portal_guids or p in portal_prefixes:
            ps["in_portal"].append(j)
        elif not posted_ok(j):
            ps["out_of_window"].append(j)
        elif p in decided:
            ps["reused"].append(j)
        else:
            ps["fresh"].append(j)
    per_search[s["query"] + (f" loc={s['location']}" if s.get("location") else "")] = {
        k: (v if isinstance(v, int) else [x["guid"][:8] for x in v]) for k, v in ps.items()}
    for k in ("in_portal", "out_of_window", "reused", "fresh"):
        tot[k].extend(ps[k])
    tot["contract"] += ps["contract"]

print(f"targeted unique={len(seen)} contract={tot['contract']} in_portal={len(tot['in_portal'])} "
      f"out_of_window={len(tot['out_of_window'])} reused={len(tot['reused'])} fresh={len(tot['fresh'])}")
for name, ps in per_search.items():
    print(f"\n{name}: contract={ps['contract']} in_portal={ps['in_portal']} "
          f"out_of_window={ps['out_of_window']} reused={ps['reused']} fresh={ps['fresh']}")
    # detail lines for the non-portal hits in this search
    for j in tgt["searches"]:
        pass
# print detail lines per search for out-of-window / reused / fresh hits
for s in tgt["searches"]:
    name = s["query"] + (f" loc={s['location']}" if s.get("location") else "")
    print(f"\n--- {name} contract hits ---")
    for j in s["jobs"]:
        if not is_contract(j):
            continue
        p = j["guid"][:8]
        tag = ("PORTAL" if j["guid"] in portal_guids or p in portal_prefixes
               else "OOW" if not posted_ok(j)
               else "DECIDED" if p in decided else "FRESH")
        print(f"  [{tag}] {p} {j.get('title')} | {j.get('company')} | {j.get('location')} | {j.get('postedDate','')[:10]}")

with open(os.path.join(HERE, "targeted_triage.json"), "w") as f:
    json.dump({"per_search": per_search,
               "totals": {k: (v if isinstance(v, int) else [x["guid"] for x in v]) for k, v in tot.items()}},
              f, indent=1)
