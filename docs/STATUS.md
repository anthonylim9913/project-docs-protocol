# STATUS

*Last updated: 2026-10-02*

## Current phase

**Companions and skill registry integrated and made private-safe; awaiting the owner's go-ahead on the public history rewrite.**

The research and Architect companions, the skill registry, Install question 9 and Doctor 1.5.0 are integrated, checked as one system (`SKILL.md`, *Optional companions*) and verified by three suites. The release-readiness process evidence is retained privately (D-0022).

## In flight

`LEDGER.md` is authoritative: 3 live rows as of 2026-10-02, no P0/P1. LG-0044 and LG-0045 are open against public conditions; LG-0046 is blocked.

| Item | Owner | Target | Notes |
|---|---|---|---|
| Publish the cleaned history and tag `v0.4.0` | owner | next session | Needs an explicit choice: force-push rewritten history, or delete and recreate the repository so old commits stop resolving |

## Blocked

LG-0046 (fresh sessions discover and route project skills) — blocked on a safe sandbox for observing an authenticated fresh session.

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | The generic block did not change in a way any check requires |

## Next

1. Owner chooses how the cleaned history is published.
2. Independent review of the public acceptance harness (LG-0044) and owner verification commands (LG-0045).
3. Observe a fresh session using a registry once a safe sandbox exists (LG-0046).

## Open questions (owner)

1. **Publish the cleaned history by force-push, or by deleting and recreating the repository?** — proposed: recreate — since 2026-10-02
