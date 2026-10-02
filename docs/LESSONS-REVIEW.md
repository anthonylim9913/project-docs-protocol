# Dashboard and Close lessons — bounded review, 2026-09-16

This patch implements the owner's local project-handoff recommendations in an
isolated protocol worktree based on `278786e5f9f1a885047a4832a2e259dd21184a64`.
The source planning documents were read locally; no project implementation or
review checkout was edited. Tests use synthetic Markdown, not project paths,
screenshots or logs. This note is development evidence, not an installation file.

## Existing rules and narrow changes

The four-document minimum plus agent wiring, CHANGELOG-before-LEDGER-before-STATUS,
rewritten STATUS, append-only corrections, one writer, register discovery and
interrupted Brief recovery already existed. These are not newly invented rules.

- `status-headings` warns with physical line numbers for repeated canonical
  headings at the same level and parent scope. Custom headings and dated
  subsections remain outside the detector; a dated document title is not an
  exemption. The check cannot choose an authoritative section.
- `status-last-updated` counts visible metadata fields, including ordinary
  emphasis, case, hyphen and list formatting. Duplicates warn without selecting
  one date. Supported fences, comments, quotes, lazy quote continuations and
  indented code do not supply metadata. Markdown support remains bounded.
- Close adds one semantic reread, separate result/provenance labels and short
  inherited-evidence, withdrawal, interrupted-write and unchanged-blocker examples.
  Bootstrap and the README template clarify execution versus planning-hub ownership.
- Doctor's output and help explicitly separate structural health from truth,
  independent verification, product acceptance, historical integrity and write order.

No fifth required file, stage machine, new dependency, blanket hashing or user
approval ceremony is introduced. Shared Markdown visibility and migration code,
the canonical wiring block, frozen acceptance fixtures and staged companions are
unchanged. The prior Architect review remains evidence for its original subject,
not acceptance of this descendant or resolution of the separate release audit.

## Verification and its limits

Direct local runs on macOS arm64 with Python 3.14.4:

| Check | Observed result |
|---|---|
| Baseline repository discovery before edits | 211 tests passed |
| `python3 -B -m unittest tests.test_status_uniqueness -q` | 12 focused methods passed |
| `python3 -B -m unittest discover -q` | 223 tests passed |
| `python3 -B tests/run_regression.py` | The same 223 tests passed; not additional independent coverage |
| `python3 -B scripts/docs-doctor.py . --today 2026-09-16 --no-git` after Close | Exit 0: 38 checks, 33 pass, 4 info, 1 explicit Git skip, no warnings/failures |
| Python compilation, skill frontmatter validation, `git diff --check` | Passed; skill validation used temporary PyYAML, not a runtime dependency |
| Old CHANGELOG bytes against the starting commit, after removing only the new prefix | Identical; DECISIONS and both ledger files unchanged |

Focused tests run the real CLI, assert diagnostic identity/locations and exit
codes, and compare input file bytes before/after. Their temporary projects have
no ancestor register, so an unrelated nested-register warning cannot make a
negative case pass. Positive controls cover valid nesting, formatted dates and
paragraph boundaries. New negative cases failed before their fixes; independent
review found list-formatted metadata misses, lazy-quote false positives and a
dated-title exemption. Each received a regression. The final independent focused
rereview returned PASS, not a claim of full Markdown conformance or release readiness.

Two separate synthetic Close exercises used the baseline and candidate
instructions. Both proposed correct ownership, provenance, withdrawal and
interruption handling. They proposed artifacts from supplied facts; they did not
execute a project Close or validate real evidence. They demonstrate compatibility
with the intended guidance, not a causal improvement or agent compliance rate.

## Deferred work and human duties

Exact-byte historical integrity remains an optional separate design. The existing
Git check measures STATUS churn; `read_text` normalizes bytes. A sound opt-in
checker needs an explicit immutable base, insertion direction, supported entry
format and byte-preserving comparison of old entries, preambles and separators.
This patch does not select a base or provide an integrity PASS.

Humans and the writing agent must still establish that evidence is genuine and
current, the correct actor/attempt/artifact is named, an unchanged blocker remains
blocked, independent review actually occurred, and acceptance is authorized.
Neither a green Doctor, a link/hash nor a final diff establishes those facts or
the actual order of writes. Full Markdown conformance, older-runtime verification
and the separate public-release audit remain outside this patch.
