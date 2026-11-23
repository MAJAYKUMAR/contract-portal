# data/

`roles.json` is the source of truth for every role on the portal.
`index.html` is generated from it by `scripts/build.py` — never hand-edit
`index.html`; edit this file, then rebuild.

## Format

```json
{
  "snapshot": "Nov 23, 2026, 4pm ET",
  "totals": {"live": 99, "expired": 156, "total": 255},
  "jobs": [ { "id": 1, "title": "...", "postedISO": "2026-10-29", ... } ],
  "expired": { "3": "Nov 10, 2026, 2:08pm CT", ... }
}
```

- `jobs` — every role ever listed, in id order. Never delete a role; a dead
  role stays in `jobs` and gains an entry in `expired` instead.
- `expired` — role id → the date AND time it was found dead
  ("`<Mon D, YYYY, h:MMam/pm CT>`"). A role with an entry here renders in
  the Expired tab with the note "Expired <stamp> — posting removed".
  If a role in `expired` is live again, remove its entry here.
- `totals` — live = jobs not in `expired`; total = len(jobs). The build
  recomputes these and fails if they disagree with the file.
- `snapshot` — the refresh run that produced this file, e.g.
  "Nov 23, 2026, 4pm ET".

Known quirk: job 122 has `postedISO: "2026-11-12T17:34:58.000Z"` — a full
ISO timestamp, not `YYYY-MM-DD`. It is kept verbatim from the original
portal; do not "fix" it by hand — the date filter treats it as unparseable
and the role only shows under "All dates".

## How a refresh updates this file

1. Sweep Dice + LinkedIn for new contract roles (see `scripts/`).
2. Verify each candidate live on its own job page before adding it.
3. Re-check every live role and every expired role (Dice HTTP 410 or
   "no longer available" = dead; LinkedIn "no longer accepting
   applications" or 404 = dead; HTTP 429 / 502 is NOT expiry — retry
   next run).
4. Append new roles to `jobs` with the next free id, add/remove
   `expired` entries with the run's actual America/Chicago time stamp,
   bump `snapshot`, then run `python3 scripts/build.py`.

## Rules carried over from the original single-file portal (verbatim)

/* DATA — IMPORTANT FOR FUTURE ROLES: Every future role added to the JOBS
   list MUST include a postedISO field with its real posting date in
   YYYY-MM-DD format (e.g. postedISO:"2026-11-10"). The Posted date
   filter compares postedISO against the visitor's current date, so a
   role without a correct postedISO cannot be placed in Today /
   Last 2 days / Last 7 days / Older than 7 days and will only show
   under "All dates". Do not omit it and do not guess the date. */

/* Roles verified dead live on Nov 10, 2026 (Dice 410 / "Sorry this job
   is no longer available", or LinkedIn closed/404). They are not deleted:
   they move out of All Jobs into the Expired tab, greyed out with an
   "Expired" badge, and their job links stay visible.
   STANDING RULE: EXPIRED maps each role ID to the date AND time it was
   found dead, as a stamp string "<Mon D, YYYY, h:MMam/pm CT>". Every
   role moved to Expired in the future MUST be added here with its own
   stamp, set to the date and time it was found dead at that check. The
   card note renders as "Expired <stamp> — posting removed" next to the
   Expired badge. 19 roles remain from the batch found expired on
   Nov 10, 2026 at 2:08pm CT; 8 more were found
   expired on Nov 11, 2026 at 11:05am CT, and id 28 was found expired
   on Nov 11, 2026 at 1:05pm CT. Id 22 is genuinely expired — its
   operative stamp is Nov 11, 2026, 3:04pm CT. Id 1 was found expired on
   Nov 12, 2026 at 7:08am CT (Dice returned HTTP 410). Ids 72 and 88
   were found expired on Nov 12, 2026 at 9:09am CT, and ids 60, 70, 95
   and 112 were found expired on Nov 12, 2026 at 11:11am CT (Dice
   HTTP 410, "no longer available"). Id 89 was found expired on
   Nov 12, 2026 at 1:09pm CT (Dice HTTP 410, "no longer available",
   confirmed on three fetches). Id 118 was found expired on
   Nov 12, 2026 at 3:09pm CT (Dice HTTP 410, "no longer available").
   Id 92 was found expired on Nov 12, 2026 at 5:12pm CT (Dice
   HTTP 410, "no longer available", confirmed on three fetches).
   Ids 31, 101 and 114 were found expired on Nov 13, 2026 at
   9:03am, 9:05am and 9:06am CT respectively (Dice HTTP 410).
   Id 85 was found expired on Nov 13, 2026 at 3:03pm CT (Dice
   HTTP 410, "no longer available"). Id 120's operative expired
   stamp is Nov 20, 2026, 1:07pm CT. Id 125 was found expired on
   Nov 13, 2026 at 5:06pm CT (Dice HTTP 410, "no longer
   available"). Id 113 was found expired on Nov 16, 2026 at
   3:08pm CT, and id 149 on Nov 16, 2026 at 3:10pm CT
   (postings removed). Id 123 was found expired on
   Nov 17, 2026 at 11:08am CT, and id 172 on Nov 17, 2026
   at 11:10am CT (Dice HTTP 410, postings removed). Id 159 was
   found expired on Nov 17, 2026 at 1:09pm CT, id 178 on
   Nov 17, 2026 at 1:10pm CT, and id 4 on Nov 17, 2026 at
   1:13pm CT (postings removed). Id 81 was found expired on
   Nov 17, 2026 at 3:08pm CT, and id 183 on Nov 17, 2026 at
   3:13pm CT (postings removed). Id 129 was found expired on
   Nov 17, 2026 at 5:11pm CT, and id 180 on Nov 17, 2026 at
   5:13pm CT (postings removed). Id 52 was found expired on
   Nov 18, 2026 at 7:08am CT (Dice HTTP 410, "no longer
   available"). Id 43 was found expired on Nov 18, 2026 at
   9:09am CT, id 86 at 9:11am CT, id 126 at 9:13am CT,
   ids 167, 168 and 170 at 9:14am CT, and ids 179 and 191
   at 9:15am CT (postings removed). Id 172 was restored to
   All Jobs on Nov 18, 2026 — its posting is live again, so
   its Nov 17, 2026, 11:10am CT stamp was removed. Id 6 was
   found expired on Nov 18, 2026 at 11:05am CT, id 141 at
   11:10am CT, and id 175 at 11:11am CT (Dice HTTP 410,
   postings removed). Id 2 was found expired on Nov 18, 2026 at 1:00pm CT, and ids 148 and 154 on Nov 18, 2026 at 1:05pm CT (postings removed). Ids 104 and 145 were found expired on Nov 18, 2026 at 5:12pm CT, and ids 164, 184, 185, 195 and 197 on Nov 18, 2026 at 5:13pm CT (Dice HTTP 410, postings removed). Id 160 stays in the Expired tab — re-verified dead (HTTP 410) on Nov 18, 2026 despite a search snippet claiming it live. Ids 162, 166 and 202 were found expired on Nov 19, 2026 at 7:08am CT (Dice HTTP 410, postings removed). Ids 193 and 207 were found expired on Nov 19, 2026 at 9:07am CT (Dice HTTP 410, "no longer available"). Ids 21, 50, 53, 58, 173 and 204 were found expired on Nov 19, 2026 at 11:01am, 11:03am, 11:17am, 11:03am, 11:05am and 11:06am CT respectively (postings removed). Ids 213 and 215 were found expired on Nov 19, 2026 at 1:08pm CT (Dice HTTP 410, postings removed). Ids 187, 190 and 196 were found expired on Nov 19, 2026 at 3:06pm CT (Dice HTTP 410, postings removed). Id 84 was found expired on Nov 19, 2026 at 5:05pm CT, id 117 at 5:06pm CT, and ids 169, 206 and 220 at 5:07pm CT (Dice HTTP 410, "no longer available"). Ids 135 and 146 were found expired on Nov 20, 2026 at 9:07am CT, and ids 172, 210 and 212 on Nov 20, 2026 at 9:08am CT (Dice HTTP 410, postings removed). Id 172 expires again after its Nov 18, 2026 restoration. Id 15 was found expired on Nov 20, 2026 at 5:02pm CT, and ids 217 and 223 on Nov 20, 2026 at 5:07pm CT (postings removed). Id 192 was found expired on Nov 21, 2026 at 9:05am CT (Dice HTTP 410, posting removed). Id 44 was found expired on Nov 23, 2026 at 9:06am CT, and id 199 on Nov 23, 2026 at 9:09am CT (postings removed). Id 171 was found expired on Nov 23, 2026 at 11:05am CT, ids 194 and 234 at 11:06am CT, and id 244 at 11:07am CT (Dice HTTP 410, postings removed). Ids 211 and 228 were found expired on Nov 23, 2026 at 1:06pm CT (Dice HTTP 410, postings removed). Ids 103, 105 and 131 were found expired on Nov 23, 2026 at 3:04pm CT, and id 248 at 3:06pm CT (Dice HTTP 410, postings removed). */
