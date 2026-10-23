# STATUS

*Last updated: 2026-10-23*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` approved by the owner for merge to `main` via pull request #1.**

The JSON mode gives dashboards one object per run with the text report's checks, summary, exit code, a `schema` version and the exit-3 `error` (D-0023, D-0024); text output is unchanged apart from the version number. No tag is made for 1.6.0. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 5 live rows as of 2026-10-23, no P0/P1 (LG-0044, LG-0048, LG-0049 and LG-0050 open; LG-0051 verifying).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Merge pull request #1 (`feat/doctor-json`) to `main` | owner's orchestrating session | 2026-10-23 | Approved in the brief of 2026-10-23; no tag |
| Independently review the LG-0051 fix (draft PR, `fix/lg-0051-htmlparser-feed`) | independent reviewer | 2026-10-23 | Migration parses each HTML line immediately; CPython gh-153030 buffering broke `HtmlBoundary` on 3.10.21+/3.11.16+/3.12.14+/3.13.15+/3.14.7+ |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Close the acceptance-harness gaps (LG-0044) and give Doctor a pointer to the registry validator (LG-0048).
2. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
3. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
