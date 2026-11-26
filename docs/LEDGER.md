# LEDGER

*Live findings for this implementation. Rows are edited in place while live; terminal rows move verbatim to `LEDGER-ARCHIVE.md`.*

Tags: +doctor +brief +lifecycle +migration +docs +tests

## Items

| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| LG-0048 | P3 | OPEN | 2026-10-28 | Nothing runs the registry validator unless an agent remembers to | +doctor +docs | Doctor names the registry validator whenever a SKILL-REGISTRY.md is present, or a test runs it over this repository |  | scripts/docs-doctor.py | 2026-10-05 independent review (major): a stale row goes unnoticed because the validator runs only after a registry edit and neither Doctor nor the suites run it. Mitigated in release/v0.4.1: SKILL.md now requires running it before invoking a registered skill (an agent in the fresh-session test did so unprompted). The structural fix is still owed. 2026-10-27: still no Doctor pointer or repository-registry validation test. The unrelated Doctor file-error repair compares cleanly over 5,789 register roots; a registry pointer is still absent and any future Doctor change needs the same compatibility gate. owner answered 2026-10-28, D-0031. |
| LG-0049 | P3 | OPEN | 2026-10-28 | Re-review minor notes deferred to the next release | +docs +tests | The research companion names the record type for an unfetched passage, and the registry digest refuses a symlinked .DS_Store and covers nested .git contents or says why not |  | staging/research-protocol/SKILL.md | 2026-10-05 re-review (minor, non-blocking): a public source record requires an Accessed date that an unfetched page cannot honestly have, so the supplied-passage rule needs a record type; the digest exclusions skip a symlink named .DS_Store silently and ignore changes inside a nested .git/. Either fix inside a companion folder needs that companion's digest re-recorded after review. 2026-10-27: 42eddc8 refuses excluded-name links before skipping and binds nested .git contents while excluding only the target root .git. The unfetched supplied-passage record form is still unresolved; changed research content awaits independent review and owner digest recording. owner answered 2026-10-28, D-0030. |
| LG-0053 | P2 | OPEN | 2026-10-28 | Planted Python cache files run instead of reviewed source | +tests +docs | The validator refuses a registered tree that contains `__pycache__` or `*.pyc`, or the owner rules on another tested mitigation |  | scripts/skill-registry.py | Owner answers, 2026-10-28: a planted Python cache made `python3 -B` print `PLANTED_CACHE` instead of reviewed source while the source file and skill fingerprint were unchanged. `-B` prevents writing caches, not reading and executing existing ones. Reported reproduction, not rerun in this Brief; narrow cache mitigation only, not a broad execution-environment investigation. |
| LG-0060 | P3 | OPEN | 2026-11-17 | Acceptance and manifest tests depend on where the temporary directory is | +tests | Fixtures are hermetic wherever TMPDIR points, or the suite refuses to run with a clear message when it is inside a register, with a test | | tests/acceptance_support.py; tests/test_input_manifest_cli.py | Owner-supplied evidence: with TMPDIR set to a directory inside a checkout, fixtures see that checkout's register as a parent, Doctor reports nested-register WARN, and about a hundred acceptance and manifest tests fail for that reason alone. An independent reviewer reproduced it on a commit before stage 1. Recorded in the v0.7.0 integration lane; fixing this is out of scope. |
<!-- 2026-09-14 evidence correction: no live rows are reopened; LG-0036 and LG-0037 remain terminal in the archive, with canonical control/mutant packets and 198-test verification under tests/fixtures/hardening-2026-09-12/final/. -->
<!-- 2026-09-15 packet correction: no live rows are reopened; the final Architect
     manifest is 47 reviewed inputs and 0 evidence files, with older 50/23
     counts retained as historical claims in CHANGELOG. -->

<!-- 2026-09-15 verification correction: retained suite counts are 211
     repository, 22 acceptance/manifest/mutant, 11 research, and 8 Architect
     tests; no live finding is reopened. -->
