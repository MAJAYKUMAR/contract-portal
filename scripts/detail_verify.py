#!/usr/bin/env python3
# Detail-verify fresh Dice candidates (live check + pay/flags from the
# JobPosting description). Relocated from the Nov 23, 2026 4pm ET refresh
# run (hidden_files/sweep4pm/detail_verify_4pm.py).
# Environment: Python 3 + requests. PER-RUN SCRIPT: replace the GUIDS list
# with the next run's fresh candidates before running.
"""Detail-verify fresh Dice candidates — 2pm ET run, Nov 23 2026.
Rules from run-log-2026-11-22-6pm-et-sweep.md:
- Hard HTTP 410 = dead even if JobPosting JSON-LD served.
- HTTP 200 + "Job Not Found" title + NEXT_HTTP_ERROR_FALLBACK;404 + no JSON-LD = dead (soft-404).
- JSON-LD regex <script[^>]*application/ld\\+json[^>]*>; fallback: decode RSC chunks,
  brace-match object containing "@type": "JobPosting".
- baseSalary: read baseSalary.value or baseSalary; single NUMBER value = pay figure
  (presumed $/hr); "DOE"/"Depends on Experience" = pay not stated; annual figure is NOT
  hourly — check description text first; description range overrides single JSON-LD number.
- Flags (C2C/1099/USC-GC/H-1B) re-checked against JobPosting DESCRIPTION text only.
"""
import json, re, sys
import requests
from dice_sweep import UA, brace_match

GUIDS = [
    "80d6700e-e592-4325-b5c5-ed0ee18ca22c",  # Sr. AI Engineer (GenAI / LLM, Vertex AI), USG, Inc., Columbus OH, 2026-11-23, DOE
    "f50f9cf9-2c08-459e-8dbe-d14238376862",  # Data Engineer - Java--(only W2), Analytics Solutions, McLean VA, 2026-11-23, salary 40-60 card
    "f0ce4d1a-1413-4cb5-8923-9caad07a8e38",  # Python Developer, Cyma Systems Inc, Washington DC, 2026-11-23, DOE
    "51468c4c-ee5a-44d8-b329-9338f782a46c",  # Senior Python Developer, Raas Infotek LLC, Richmond VA, 2026-11-23, DOE
]

def extract_jobposting(html):
    m = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                return data
            if isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and d.get("@type") == "JobPosting":
                        return d
        except Exception:
            pass
    # fallback: RSC chunks
    dec = json.JSONDecoder()
    for mm in re.finditer(r'self\.__next_f\.push\(\[1,', html):
        j = html.find('"', mm.end())
        if j < 0:
            continue
        try:
            chunk, _ = dec.raw_decode(html[j:])
        except Exception:
            continue
        if '"@type": "JobPosting"' not in chunk and '"@type":"JobPosting"' not in chunk:
            continue
        idx = chunk.find('"@type"')
        ob = chunk.rfind('{', 0, idx)
        if ob < 0:
            continue
        obj = brace_match(chunk, ob)
        if not obj:
            continue
        try:
            data = json.loads(obj)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None

def clean_text(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def pay_from(job):
    bs = (job or {}).get("baseSalary") or {}
    val = bs.get("value") if isinstance(bs, dict) else bs
    if isinstance(val, dict):
        mn, mx = val.get("minValue"), val.get("maxValue")
        if mn is not None or mx is not None:
            return f"{mn}-{mx} (unit: {val.get('unitText') or bs.get('unitText') or '?'})"
        return None
    if isinstance(val, (int, float)):
        return f"{val} (single number, presumed $/hr)"
    if isinstance(val, str):
        return f"'{val}'"
    # FIX (12pm run): minValue/maxValue can sit DIRECTLY on baseSalary
    if isinstance(bs, dict):
        mn, mx = bs.get("minValue"), bs.get("maxValue")
        if mn is not None or mx is not None:
            return f"{mn}-{mx} (unit: {bs.get('unitText') or '?'})"
    return None

for g in GUIDS:
    url = f"https://www.dice.com/job-detail/{g}"
    print("=" * 100)
    print(url)
    try:
        r = requests.get(url, headers=UA, timeout=30)
    except Exception as e:
        print("FETCH ERROR:", e)
        continue
    print("HTTP:", r.status_code)
    html = r.text
    title_m = re.search(r'<title>(.*?)</title>', html, re.S)
    print("TITLE:", clean_text(title_m.group(1)) if title_m else "?")
    print("NEXT_HTTP_ERROR_FALLBACK;404 present:", "NEXT_HTTP_ERROR_FALLBACK;404" in html)
    job = extract_jobposting(html)
    print("JobPosting JSON-LD found:", bool(job))
    if job:
        print("job title:", job.get("title"))
        print("hiringOrg:", (job.get("hiringOrganization") or {}).get("name"))
        print("employmentType:", job.get("employmentType"))
        print("datePosted:", job.get("datePosted"))
        print("validThrough:", job.get("validThrough"))
        loc = job.get("jobLocation") or {}
        addr = loc.get("address") or {}
        print("location:", loc.get("name") or addr)
        print("baseSalary raw:", json.dumps(job.get("baseSalary"))[:300])
        print("pay parsed:", pay_from(job))
        desc = clean_text(job.get("description") or "")
        print("desc len:", len(desc))
        # description pay range
        for pm in re.finditer(r'\$[\d,]+(?:\.\d+)?\s*(?:-|to)\s*\$?[\d,]+(?:\.\d+)?\s*(?:per hour|/hr|hourly)', desc, re.I):
            print("DESC PAY RANGE:", pm.group(0))
        for pm in re.finditer(r'\$[\d,]+(?:\.\d+)?\s*(?:per year|/year|annually|per annum)', desc, re.I):
            print("DESC ANNUAL PAY:", pm.group(0))
        low = desc.lower()
        for flag, pats in [
            ("C2C", ["c2c", "corp-to-corp", "corp to corp"]),
            ("1099", ["1099"]),
            ("W2", ["w2", "w-2"]),
            ("USC/GC", ["us citizen", "u.s. citizen", "green card", "gc only", "usc only", "citizenship required", "must be a us citizen"]),
            ("H-1B", ["h-1b", "h1b", "h1-b"]),
            ("sponsorship", ["sponsorship", "no sponsorship", "will not sponsor", "unable to sponsor"]),
            ("duration", []),
        ]:
            hits = [p for p in pats if p in low]
            if hits:
                # show context snippets
                snips = []
                for p in hits[:3]:
                    i = low.find(p)
                    snips.append(desc[max(0, i-60):i+80].replace("\n", " "))
                print(f"FLAG {flag}: {hits} :: {' | '.join(snips)}")
        # duration hints
        for pm in re.finditer(r'\b(\d+\s*(?:months?|years?)\s*(?:\+)?\s*(?:extension|contract|duration)?)\b', desc, re.I):
            print("DURATION HINT:", pm.group(0))
        print("DESCRIPTION (first 2500 chars):")
        print(desc[:2500])
    else:
        print("No JobPosting — page body excerpt:")
        print(clean_text(html)[:1500])
