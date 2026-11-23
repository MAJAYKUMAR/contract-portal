# Architecture

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Presentation  src/template.html + src/styles.css + src/app.js│
│               (rendering, filters, sort, tabs, sync)        │
├─────────────────────────────────────────────────────────────┤
│ Data          data/roles.json (jobs, expired stamps,        │
│               snapshot, totals) — the single source of truth│
├─────────────────────────────────────────────────────────────┤
│ Automation    scripts/dice_sweep.py, dice_targeted.py,      │
│               triage.py, detail_verify.py,                  │
│               build_decided_set.py, build.py                │
├─────────────────────────────────────────────────────────────┤
│ Config        config/config.json (pay floor, sources,       │
│               window, cadence, exclusions)                  │
└─────────────────────────────────────────────────────────────┘
```

`index.html` at the repo root is a **generated** artifact, not source. It is
assembled by `scripts/build.py` from `src/` + `data/roles.json` and is what
Vercel serves. Never hand-edit it.

## Data flow

```
Dice / LinkedIn
  → scripts/dice_sweep.py + dice_targeted.py   (fetch search pages)
  → scripts/triage.py / targeted_triage.py     (dedupe vs portal + decided set)
  → scripts/detail_verify.py                  (live-check each fresh candidate)
  → data/roles.json                           (append jobs, update expired, bump snapshot)
  → python3 scripts/build.py                  (validate + assemble index.html)
  → git push main                             (Vercel auto-deploys)
```

## Refresh pipeline

- Every 2 hours, 8am–6pm ET (`refreshCadenceHours: 2`,
  `refreshWindowET: "08:00-18:00"`). Runs outside the window do nothing.
- 14-day window (`windowDays: 14`, `windowStart` in `config/config.json` —
  currently `2026-11-11`; it rolls forward as the portal ages).
- Sources: Dice + LinkedIn only. A role is added only with an exact direct
  job link (never a search-page URL), verified live on its own page.
- Pay floor $50/hr: stated pay under $50/hr is excluded; pay-not-stated
  roles are included flagged "confirm $50+/hr with vendor".
- Excluded: no-sponsorship / USC-GC-only / citizenship-required roles and
  confirmed-1099-only roles. 1099-labelled roles may be listed only with
  the 1099 flag (1099 generally cannot support an H-1B transfer).
- C2C is "confirmed" only when the posting itself states C2C / Corp-to-Corp
  / W2-or-C2C; otherwise the role is "C2C-unsure".

## Verification rules (learned the hard way)

- **Dice stale-cache lesson:** a fetched Dice page can be a stale cached
  copy showing full content for a dead URL. Live `curl` HTTP 200/410 is
  the truth; never trust a cached page alone for live status.
- **Expiry is page-confirmed only:** Dice HTTP 410 or "no longer
  available"; LinkedIn "no longer accepting applications" or 404.
- **HTTP 429 / 502 is NOT expiry.** A rate limit or transient fetch failure
  leaves the role where it is; retry next run.
- **Truncated URLs 404 for any invalid id** — expired checks must use full
  36-char Dice GUIDs.
- **Description evidence governs:** if a posting's description anchors a
  city with no remote wording, it is not remote even if structured data
  says TELECOMMUTE. Snippet locations are untrusted; the detail page decides.
- **Never delete a role.** Dead roles move to the Expired tab with a
  date+time stamp ("Expired Nov 23, 2026, 3:04pm CT — posting removed").
  If an expired role is live again, its stamp is removed and it returns to
  All Jobs.
- **Every role needs `postedISO`** (real posting date, `YYYY-MM-DD`). The
  Posted-date filter compares it against the visitor's current date; a
  role without it can only show under "All dates". Never guess the date.
- **Most-recent sort** uses a `dateOrd` lookup in `src/app.js` keyed by the
  `posted` string — a refresh adding a role posted on a new date must add
  that date to `dateOrd` or the newest role sorts last.

## Sync (applied / starred marks)

- Firebase Realtime Database, project `contract-portal-9ea01`, keyless:
  the page polls `/applied.json` and `/starred.json` every 4s and writes
  via PUT/DELETE. Database rules allow read/write on `applied`/`starred`
  only; everything else is denied. No API key is used or stored anywhere.
- `localStorage` fallback (`contract-portal-applied-v1`,
  `contract-portal-starred-v1`) with a one-time migration of local marks
  to the cloud. Marking Applied never submits an application — it only
  tracks the mark.

## Deploy

Push to `main` → Vercel auto-deploys. Vercel Web Analytics is
enabled (free Hobby tier); its script is inlined into the single-file
build by `scripts/build.py` from `src/analytics.html`, byte-for-byte.

## How to run the build

```bash
python3 scripts/build.py   # from the repo root; writes index.html
```

Python 3, standard library only. The build validates `data/roles.json`
(totals match the data, no duplicate ids, every expired entry has a
matching job, every job has `id`, `title`, `company`, `url`,
`postedISO`) and fails before writing anything if the data is inconsistent.
Output is deterministic.

## How a refresh updates the portal

1. Run the sweep scripts, triage, and detail verification.
2. Edit `data/roles.json`: append new jobs with the next free id, add or
   remove `expired` entries with the run's actual America/Chicago
   date+time stamp, bump `snapshot` and let the build recompute `totals`
   (the build fails if the stored totals disagree).
3. Run `python3 scripts/build.py`, verify the counts in the output,
   commit, and push.
