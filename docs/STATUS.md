# STATUS

*Last updated: 2026-10-23*

## Current phase

**v0.4.1 public; Doctor's `--json` mode waits on a draft pull request from `feat/doctor-json`.**

The JSON mode gives dashboards one object per run with the text report's checks, summary and exit code; text output is unchanged. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 4 live rows as of 2026-10-23, no P0/P1 (LG-0044, LG-0048, LG-0049 and LG-0050 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Review the draft pull request for Doctor `--json` | owner | next | Not merged, version not bumped, nothing tagged; D-0023 records the JSON contract |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. The owner reviews `feat/doctor-json`; merging, the version and any tag are the owner's.
2. Close the acceptance-harness gaps (LG-0044) and give Doctor a pointer to the registry validator (LG-0048).
3. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
4. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

1. **Doctor's version for `--json`: still 1.5.0, so a consumer cannot tell from it whether the flag exists. Bump it, and give the object its own schema version?** — proposed: 1.6.0 at merge, no schema field until the shape changes — since 2026-10-23
2. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23
3. **Should the JSON object also carry the exit-3 reason and the Scope disclaimer, now on stderr and in the docs only, and send `--help`/`--version` text to stderr under `--json`?** — proposed: not until a dashboard needs them — since 2026-10-23
