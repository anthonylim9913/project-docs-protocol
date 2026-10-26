# STATUS

*Last updated: 2026-10-26*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` and the LG-0051 migration fix are on `main` (pull requests #1 and #3, merged), untagged. LG-0044's binding is confirmed by the 2026-10-25 independent re-check, and its follow-up fixes are on `fix/lg-0044-acceptance-binding-alt`; isolating the judged product from the trusted checkout is open as LG-0052.**

The closing control for LG-0044 is external. A trusted checkout's runner and validator judge a fresh clone of the candidate, load their own code only from verified bytes under `python3 -I -B`, and refuse bytecode anywhere. Every Git command they run is hardened against the candidate's `.git`. The reviewer's procedure in `tests/README.md` runs `check_harness` (record line count, `sha256sum -c --strict`, record against the reviewer's pin) before the runner and again immediately before the validator, and every step must exit 0. The validator's accepted line names `source_commit` and `runtime_tree_sha256`. The external check does not isolate the judged product from the trusted checkout by itself. The procedure states the identity requirement, but nothing enforces it yet (D-0027, D-0028, LG-0052). Harness pin: `1d9e348035edf1c32cc41aa2414e0330d59a05824e71625c62ec9b3c71153499` (17 record lines). Suites (624 tests) pass on Linux with Python 3.9 to 3.14. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 5 live rows as of 2026-10-26, no P0/P1 (LG-0044 verifying, to be closed by the Close that follows; LG-0048, LG-0049, LG-0050 and LG-0052 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Review of `fix/lg-0044-acceptance-binding-alt` (head after this Close) | owner's orchestrating session | next review | Check the procedure changes, the `.DS_Store` rule, the accepted line and the new pin; not to be merged before that |
| Isolate the judged product from the trusted checkout (LG-0052) | unassigned | after the review above | Product commands under an identity that cannot write the trusted checkout, output or interpreter, all its processes ended before the re-check and validator |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Review this branch's follow-up (procedure, `.DS_Store`, accepted line, pin `1d9e3480…`), then merge it with the owner's go.
2. Design and test product isolation for the external check (LG-0052); then give Doctor a pointer to the registry validator (LG-0048).
3. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
4. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
2. **Which checkout is "trusted" for a harness change?** — proposed: the reviewed commit, checked out again in a separate directory, with the pin from `sha256sum tests/harness.sha256` and the record's line count published in the review — since 2026-10-23
