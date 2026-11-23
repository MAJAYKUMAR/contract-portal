# Contract Portal

A live, auto-refreshing board of verified ML / MLOps / AI contract roles — C2C
first, then W2. Every role is checked live on its own Dice or LinkedIn page
before it is listed, and re-checked every 2 hours; dead postings move to the
Expired tab instead of disappearing.

## What it tracks

- ML Engineer / MLOps / AI / Data / Python contract roles, $50/hr floor
  (pay-not-stated roles are listed flagged, pending vendor confirmation)
- Remote US or Texas; C2C first, W2 included, 1099 roles labelled and
  off by default (1099 generally cannot support an H-1B transfer)
- H-1B-transfer notes per role — most postings don't state it, so those say
  "confirm with vendor"

## Features

- Filters: C2C / W2 / check-vendor / 1099 / H-1B-listed / Remote / Texas /
  Applied / Starred; search; sort by priority, pay, or most recent
- Posted-date filter (Today / Last 2 days / Last 7 days / Older) computed
  against the visitor's actual current date
- All Jobs / Applied / Expired tabs — marking a role Applied moves it to the
  Applied tab on every device
- Applied and starred marks sync across devices via Firebase Realtime
  Database (keyless, world read/write on the marks only), with a
  localStorage fallback when the cloud is unreachable
- Expired roles keep their link and a date+time stamp of when they were
  found dead

## How the refresh works

Every 2 hours, 8am–6pm ET, a sweep scans Dice and LinkedIn for new contract
roles posted in the last 14 days, deduplicates against the portal, and
verifies each candidate live on its own job page before adding it. The same
run re-checks every live and expired link. See `docs/ARCHITECTURE.md` for
the pipeline and the verification rules.

## Repo structure

```
index.html          generated page (deployed to Vercel) — do not hand-edit
src/
  template.html     HTML shell with {{...}} placeholders
  styles.css        portal CSS
  app.js            rendering, filters, sort, tabs, Firebase sync
  analytics.html    Vercel Web Analytics scripts (injected byte-for-byte)
data/
  roles.json        source of truth: jobs, expired stamps, snapshot, totals
  README.md         data rules for adding roles
scripts/
  build.py          assembles index.html from src/ + data/roles.json
  dice_sweep.py     Dice general sweep (RSC jobList extraction)
  dice_targeted.py  targeted Dice title/location searches
  triage.py         triage a sweep vs the portal + decided set
  targeted_triage.py
  detail_verify.py  detail-verify fresh candidates (pay/flags from the posting)
  build_decided_set.py
config/
  config.json       pay floor, sources, window, refresh cadence, exclusions
docs/
  ARCHITECTURE.md   layers, data flow, verification rules, deploy
```

## Build

```bash
python3 scripts/build.py   # writes index.html at the repo root
```

Python 3, standard library only. The build is deterministic and validates
`data/roles.json` (totals match the data, no duplicate ids, every expired
entry has a matching job) before writing anything.

## Deploy

Pushing to `main` auto-deploys to Vercel.

## Tech

Vanilla HTML/CSS/JS (single generated page, no framework, no build
dependencies) · Python 3 sweep + verification scripts · Firebase Realtime
Database for cross-device sync · Vercel hosting + Web Analytics.

## License

MIT — see [LICENSE](LICENSE).
