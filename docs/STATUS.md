# STATUS

*Last updated: 2026-11-26*

## Current phase

**v0.7.0 is the latest public tag. Release tooling is on `main`, untagged;
Doctor 1.10.0 is unreleased branch work.** Both companions remain 0.2.2 with unchanged
registered `sha256v2:` identities.

The delegation candidate adds a paste-ready task brief, owner-assigned ids,
and advisory local-branch and owed-fragment checks (D-0046). An independent
review found two defects in the branch check; both are repaired (newest
CHANGELOG entry). Its evidence supports closing LG-0062; LG-0061 waits for an
independent review of the repairs.

Release tooling (release check, optional privacy scan, pinned CI) merged after
hosted CI passed on all four jobs. Hosted CI has not run on this branch.

## In flight

`LEDGER.md` is authoritative: 5 OPEN, 2 VERIFYING; 8 archived rows, no P0/P1.

| Work | Branch | End action |
|---|---|---|
| Delegation brief and stranded-work advisories | `feat/r3-stranded-work` | review of the branch-check repairs, then owner decides merge |

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

1. Independently review the branch-check repairs, then close LG-0061 and LG-0062.
2. Run hosted CI on this branch, then merge when the owner agrees.
3. LG-0044 stage 2 and LG-0060, followed by waves B and C.
4. Decide whether the Doctor limits in the v0.7.0 entry need ledger rows.

## Open questions (owner)

*No open questions.*
