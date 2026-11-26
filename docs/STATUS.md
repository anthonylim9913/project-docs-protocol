# STATUS

*Last updated: 2026-11-26*

## Current phase

**v0.7.0 remains the latest public tag; release-tooling repairs are unreleased.**
Doctor remains 1.9.1. Both companions remain 0.2.2 with unchanged registered
`sha256v2:` identities. Five independently reviewed closures remain archived;
their provenance and the v0.7.0 review limits are recorded in CHANGELOG.

The release gate, optional privacy scanner/hook and CI repairs address two
FIX FIRST reviews. D-0045 records scanner scope. CI now targets macos-15 and
current action majors, with a system-interpreter probe and root-safe whitespace.
All local suites, structural gates and release-check pass; counts are in CHANGELOG.
Hosted CI has not run; hosted interpreter availability remains unverified.
No release or network operation.

## In flight

`LEDGER.md` is authoritative: 5 OPEN, 0 VERIFYING; 8 archived rows, no P0/P1.

| Work | Branch | End action |
|---|---|---|
| Delegated release tooling | `chore/release-tooling` | owner decides on merge and hosted CI after review |
| Delegated review repairs | `fix/r1-findings` | supervisor reviews repairs; owner controls integration |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0044 stage 2 | separate follow-up | self-approval gap, D-0029 |
| LG-0049 and LG-0053 | wave B | supplied passages and cache refusal, D-0030 |
| LG-0048 | wave C | registry pointer, D-0031; release registry gate applies |
| LG-0060 | separate test repair | temporary fixtures can inherit parent registers |
| Compaction procedure in Mode 3 | after a dry run | D-0005 |
| Full CommonMark/GFM conformance | separate scope | bounded syntax is intentional |
| External wiring re-sync | each project's next Close | missing current clauses WARN |

## Next

1. Review this unreleased repair and run hosted CI when authorized.
2. LG-0044 stage 2 and LG-0060, followed by waves B and C.
3. Decide whether the Doctor limits in the v0.7.0 entry need ledger rows.

## Open questions (owner)

*No open questions.*
