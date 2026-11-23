#!/usr/bin/env python3
# Dice sweep (general searches). Relocated from the Nov 23, 2026 4pm ET
# refresh run (hidden_files/sweep4pm/dice_sweep_4pm.py).
# Environment: Python 3 + requests. Writes sweep_all.json next to itself.
# Parses Dice search pages via the SSR RSC payload (jobList) — plain curl
# returns a Next.js shell with an empty jobList when filters are present.
"""Dice sweep — 4pm ET run, Nov 23 2026. Rebuilt from the documented method
in run-log-2026-11-22-2pm-et-sweep.md (RSC-decode extraction, largest jobList
chunk, guid field = 36-char hyphenated GUID).
NOTE: /tmp was wiped mid-run, so scripts/outputs live in this durable dir."""
import json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9"}

BASE = "https://www.dice.com/jobs"

def brace_match(s, start):
    assert s[start] == '{'
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
        i += 1
    return None

def extract_jobs(html):
    best = None
    dec = json.JSONDecoder()
    for m in re.finditer(r'self\.__next_f\.push\(\[1,', html):
        j = html.find('"', m.end())
        if j < 0:
            continue
        try:
            chunk, _ = dec.raw_decode(html[j:])
        except Exception:
            continue
        jm = re.search(r'jobList"\s*:', chunk)
        if not jm:
            continue
        ob = chunk.find('{', jm.end())
        if ob < 0:
            continue
        obj = brace_match(chunk, ob)
        if not obj:
            continue
        try:
            data = json.loads(obj)
        except Exception:
            continue
        jobs = data.get("data")
        if isinstance(jobs, list) and (best is None or len(jobs) > len(best)):
            best = jobs
    return best or []

def fetch(query, page=1, location=None):
    params = {"q": query, "countryCode": "US", "radius": "30", "radiusUnit": "mi",
              "page": str(page), "pageSize": "30", "language": "en"}
    if location:
        params["location"] = location
    r = requests.get(BASE, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    jobs = extract_jobs(r.text)
    return jobs, r.status_code

QUERIES = [
    ("ML Engineer", 1, None),
    ("MLOps Engineer", 1, None),
    ("AI Engineer", 1, None),
    ("GenAI Engineer", 1, None),
    ("LLM Engineer", 1, None),
    ("Data Engineer", 1, None),
    ("Data Engineer", 2, None),
    ("Data Scientist", 1, None),
    ("Python Developer", 1, None),
    ("Python Developer", 2, None),
    ("AI Infrastructure Platform Engineer", 1, None),
    ("Sr AI Engineer", 1, "Houston, TX"),
    ("AI Engineer", 1, "Texas"),
    ("ML Engineer", 1, "Remote"),
    ("AI Engineer", 1, "Remote"),
]

def main():
    out = {"searches": []}
    total = 0
    for q, pg, loc in QUERIES:
        jobs, code = [], 0
        for attempt in range(3):
            try:
                jobs, code = fetch(q, pg, loc)
                break
            except Exception as e:
                print(f"  RETRY {q} p{pg} loc={loc}: {e}", file=sys.stderr)
                time.sleep(8 + attempt * 4)
                jobs, code = [], 0
        recs = []
        for j in jobs:
            recs.append({
                "guid": j.get("guid"),
                "title": j.get("title"),
                "company": j.get("companyName"),
                "location": (j.get("jobLocation") or {}).get("displayName"),
                "isRemote": j.get("isRemote"),
                "postedDate": j.get("postedDate"),
                "employmentType": j.get("employmentType"),
                "salary": j.get("salary"),
                "search": q + (f" p{pg}" if pg > 1 else "") + (f" loc={loc}" if loc else ""),
            })
        out["searches"].append({"query": q, "page": pg, "location": loc,
                                "status": code, "count": len(recs), "jobs": recs})
        total += len(recs)
        print(f"{q} p{pg} loc={loc}: {len(recs)} cards (HTTP {code})")
        time.sleep(2)
    out["total_raw"] = total
    with open(os.path.join(HERE, "sweep_all.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"TOTAL RAW: {total}")

if __name__ == "__main__":
    main()
