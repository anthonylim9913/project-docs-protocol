# STATUS

*Last updated: 2026-10-25*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` and the LG-0051 migration fix are on `main` (pull requests #1 and #3, merged), untagged; LG-0044 is fixed again on `fix/lg-0044-acceptance-binding-alt` after a further independent review, and awaits an independent re-check.**

The closing control for LG-0044 is external. A trusted checkout's runner and validator judge a fresh clone of the candidate, load their own code only from verified bytes under `python3 -I -B`, and refuse bytecode anywhere. Every Git command they run is hardened against the candidate's `.git`. The reviewer's procedure in `tests/README.md` requires a throwaway account or container, every step to exit 0, and a second `sha256sum -c` before the validator (D-0025, D-0027). Harness pin: `fb17b7f7da9e7c043de69556231b28972bdc30ea063dd50b4f25c107f34c6277`. Suites (621 tests) pass on Linux with Python 3.9 to 3.14. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 5 live rows as of 2026-10-25, no P0/P1 (LG-0044 and LG-0051 verifying; LG-0048, LG-0049 and LG-0050 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Independent re-check of LG-0044 (`fix/lg-0044-acceptance-binding-alt`) | owner's orchestrating session | next review | Run the external check exactly as `tests/README.md` states, with the pin above; not to be merged before it passes |
| Run the suites on the owner's Mac (Python 3.9.6, default `TMPDIR`) | owner | next review | The macOS and 3.9 fixes were checked only on Linux; the 3.9.6 bytecode-test cause is unconfirmed (CHANGELOG 2026-10-25) |
| Close LG-0051 | owner's orchestrating session | this session | Pull request #3 merged as `66c11c3` on 2026-10-25 |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Re-check LG-0044 independently: the external check from a trusted checkout of the reviewed commit against a fresh clone of the candidate, exactly as `tests/README.md` states; then give Doctor a pointer to the registry validator (LG-0048).
2. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
3. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
2. **Which checkout is "trusted" for a harness change?** — proposed: the reviewed commit, checked out again in a separate directory, with the pin from `sha256sum tests/harness.sha256` published in the review — since 2026-10-23
