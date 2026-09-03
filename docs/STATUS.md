# STATUS

*Snapshot of where the work is right now. Rewrite this file at each close — never append to it. Keep it around ~40 lines and never over ~60. Past-tense content belongs in CHANGELOG.md, not here.*

*Last updated: 2026-09-04*

## Current phase

**v0.2.0 is the public baseline; v0.3.0 (Doctor and Brief modes) is in adversarial verification**

The protocol as audited on 2026-09-02 is on `main` and tagged. Two new modes are drafted on the release scratch area and must pass a second verification round before they get a branch: Doctor, a dependency-free health check that runs the Bootstrap red flags as a script; and Brief, the ritual that turns STATUS's open questions into DECISIONS entries with the rejected alternatives named.

## In flight

| Item | Owner | Target | Notes |
|---|---|---|---|
| Doctor mode (`scripts/docs-doctor.py` + Mode 4 text) | Claude | v0.3.0 | Round 1 found a hang on wide ids, a too-loose block detector, and a false FAIL on the mature installation; fixes under re-verification |
| Brief mode (Mode 5 text + worked example) | Claude | v0.3.0 | Round 1: silence must not count as an answer; options must trace to a real source; the Close-time offer fires only on askable items |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run on the largest retired register | Only one compaction has ever happened; write the procedure from that instance, not from theory |

## Next

1. Land v0.3.0 on a branch once both re-verifications pass; tag after review.
2. Compaction dry run (separate long-running session; prompt written and handed over).
3. Add `scripts/docs-doctor.py` to SKILL.md's file list when it ships.

## Open questions (owner)

*None open.*

*Bootstrap reminder: this is the first file to read each session. Close reminder: rewrite it AFTER the CHANGELOG entry — completed items out, new items in, past tense deleted.*
