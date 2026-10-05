# LEDGER

*Live findings for this implementation. Rows are edited in place while live; terminal rows move verbatim to `LEDGER-ARCHIVE.md`.*

Tags: +doctor +brief +lifecycle +migration +docs +tests

## Items

| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| LG-0044 | P2 | OPEN | 2026-10-05 | Release evidence must cover complete reviewed scope | +tests +docs | An independent review confirms the acceptance harness binds every normative public input and rejects an omitted, deleted or changed one |  | tests/input_manifest.py | from LG-0037; audit R7. 2026-10-05 independent review: PARTIAL — all 543 omission, deletion and one-byte mutations of the 181 bound files were rejected, but the bound document list is a fixed allowlist (tests/input_manifest.py:17-19), so a normative document added later is unbound, and a one-byte change to tests/validate_acceptance.py:73 lets the validator approve its own run. Both open. |
| LG-0048 | P3 | OPEN | 2026-10-05 | Nothing runs the registry validator unless an agent remembers to | +doctor +docs | Doctor names the registry validator whenever a SKILL-REGISTRY.md is present, or a test runs it over this repository |  | scripts/docs-doctor.py | 2026-10-05 independent review (major): a stale row goes unnoticed because the validator runs only after a registry edit and neither Doctor nor the suites run it. Mitigated in release/v0.4.1: SKILL.md now requires running it before invoking a registered skill (an agent in the fresh-session test did so unprompted). The structural fix is still owed. |
| LG-0049 | P3 | OPEN | 2026-10-05 | Re-review minor notes deferred to the next release | +docs +tests | The research companion names the record type for an unfetched passage, and the registry digest refuses a symlinked .DS_Store and covers nested .git contents or says why not |  | staging/research-protocol/SKILL.md | 2026-10-05 re-review (minor, non-blocking): a public source record requires an Accessed date that an unfetched page cannot honestly have, so the supplied-passage rule needs a record type; the digest exclusions skip a symlink named .DS_Store silently and ignore changes inside a nested .git/. Either fix inside a companion folder needs that companion's digest re-recorded after review. |
<!-- 2026-09-14 evidence correction: no live rows are reopened; LG-0036 and LG-0037 remain terminal in the archive, with canonical control/mutant packets and 198-test verification under tests/fixtures/hardening-2026-09-12/final/. -->
<!-- 2026-09-15 packet correction: no live rows are reopened; the final Architect
     manifest is 47 reviewed inputs and 0 evidence files, with older 50/23
     counts retained as historical claims in CHANGELOG. -->

<!-- 2026-09-15 verification correction: retained suite counts are 211
     repository, 22 acceptance/manifest/mutant, 11 research, and 8 Architect
     tests; no live finding is reopened. -->
