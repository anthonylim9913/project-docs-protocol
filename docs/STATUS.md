# STATUS

*Last updated: 2026-11-27*

## Current phase

**v0.7.0 is the latest public tag. Release tooling is on `main`, untagged.
Doctor 1.10.0 and the external trusted judge are reviewed branch work, not
yet merged.** Both companions remain 0.2.2 with unchanged registered
`sha256v2:` identities.

The branch adds a paste-ready delegation brief, owner-assigned ids, two
advisory Doctor checks for stranded work (`git-unlisted-branches`,
`owed-fragments`; D-0046, D-0047, D-0049) and LG-0044 stage 2, the external
trusted judge (D-0029, D-0048). Independent reviews support all three
closures recorded on 2026-11-27: LG-0044, LG-0061 and LG-0062 are CLOSED in
the archive with the reviewers' readings and stated limits.

Hosted CI has not run on this branch. The local release check passed on
Python 3.14.4 and 3.9.6 before the last small repair; rerun it before merging.

## In flight

`LEDGER.md` is authoritative: 4 OPEN, 0 VERIFYING; 11 archived rows, no P0/P1.

| Work | Branch | End action |
|---|---|---|
| Delegation brief, stranded-work checks and LG-0044 stage 2 | `fix/lg-0044-external-judge` | hosted CI as a pull request, then owner decides merge |

`feat/r3-stranded-work` is an older subset of that branch.

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0049 and LG-0053 | wave B | supplied passages and cache refusal, D-0030 |
| LG-0048 | wave C | registry pointer, D-0031; release registry gate applies |
| LG-0060 | separate test repair | temporary fixtures can inherit parent registers |
| Compaction procedure in Mode 3 | after a dry run | D-0005 |
| Full CommonMark/GFM conformance | separate scope | bounded syntax is intentional |
| External wiring re-sync | each project's next Close | missing current clauses WARN |

## Next

1. Run hosted CI on the branch, then merge when the owner agrees.
2. LG-0060, then waves B and C (LG-0049, LG-0053, LG-0048).
3. Decide whether the Doctor limits in the v0.7.0 entry need ledger rows.

## Open questions (owner)

*No open questions.*
