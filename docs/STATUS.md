# STATUS

*Last updated: 2026-11-26*

## Current phase

**v0.7.0 is the latest public tag. Release tooling is on `main`, untagged.**
Doctor remains 1.9.1 and both companions 0.2.2 with unchanged registered
`sha256v2:` identities.

Since the tag, `main` gained a one-command release check
(`scripts/release-check.py`), an optional privacy scan with a sample pre-push
hook (`scripts/leak-scan.py`, scope in D-0045), and CI on pinned Linux and
macOS images with a weekly run. Two independent reviews asked for repairs
before the merge; hosted CI then passed on all four jobs (CHANGELOG
2026-11-26, four entries).

## In flight

`LEDGER.md` is authoritative: 5 OPEN, 0 VERIFYING; 8 archived rows, no P0/P1.

*No items in flight.*

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

1. LG-0044 stage 2 and LG-0060, followed by waves B and C.
2. Decide whether the Doctor limits in the v0.7.0 entry need ledger rows.

## Open questions (owner)

*No open questions.*
