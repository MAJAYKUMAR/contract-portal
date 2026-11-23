#!/usr/bin/env python3
# Build the decided set for the next run. Relocated from the Nov 23, 2026
# 4pm ET refresh run (hidden_files/sweep4pm/build_decided_set_4pm.py).
# Environment: Python 3. Run-state files live outside the repo; override
# with PORTAL_HIDDEN_FILES, PORTAL_STATE_FILE, PORTAL_SWEEP_LOG, PORTAL_TRIAGE.
"""Build the decided set for the next run: union of this run's triage
decided set (419 tokens, inherited from the 6pm log) + every 8-char hex
token in this log + all portal GUID prefixes. Then append the full set
to the run log."""
import json, os, re

# Run-state files (portal snapshots, sweep logs) live outside the repo in
# the cron worker's hidden_files dir; override with PORTAL_HIDDEN_FILES.
HF = os.environ.get("PORTAL_HIDDEN_FILES",
                    "/home/hatch/workspace/goals/contract-jobs-portal-for-harshitha/hidden_files")
LOG = os.environ.get("PORTAL_SWEEP_LOG",
                     os.path.join(HF, "run-log-2026-11-23-4pm-et-sweep.md"))
PORTAL = os.environ.get("PORTAL_STATE_FILE",
                       os.path.join(HF, "portal-roles-2026-11-23-2pm.md"))
TRIAGE = os.environ.get("PORTAL_TRIAGE",
                        os.path.join(HF, "sweep4pm", "triage.json"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decided_set.txt")

# truncate the log back to before any previously appended set section, if present
lines = open(LOG).read().splitlines(keepends=True)
idxs = [i for i, l in enumerate(lines) if l.startswith("Full decided set for the next run")]
if idxs:
    open(LOG, "w").writelines(lines[:idxs[0]])

decided = set(json.load(open(TRIAGE))["decided_set"])
log_txt = open(LOG).read()
decided |= set(re.findall(r"\b[0-9a-f]{8}\b", log_txt))
portal_txt = open(PORTAL).read()
decided |= {m.group(1).lower()[:8] for m in re.finditer(r"dice\.com/job-detail/([0-9a-f-]{36})", portal_txt)}
decided = sorted(decided)
print("decided set size:", len(decided))
print("new vs triage set (440):", sorted(set(decided) - set(json.load(open(TRIAGE))["decided_set"])))
open(OUT, "w").write(", ".join(decided) + "\n")

with open(LOG, "a") as f:
    f.write("\nFull decided set for the next run (%d tokens - every 8-char hex token\n" % len(decided))
    f.write("in this log + all portal GUID prefixes; the next run's builder takes\n")
    f.write("every 8-char hex token in this log):\n")
    for i in range(0, len(decided), 8):
        f.write(", ".join(decided[i:i+8]) + ",\n")
print("appended to log")
