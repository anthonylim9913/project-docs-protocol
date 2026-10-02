# LEDGER

*Live findings for this implementation. Rows are edited in place while live; terminal rows move verbatim to `LEDGER-ARCHIVE.md`.*

Tags: +doctor +brief +lifecycle +migration +docs +tests

## Items

| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| LG-0044 | P2 | OPEN | 2026-10-02 | Release evidence must cover complete reviewed scope | +tests +docs | An independent review confirms the acceptance harness binds every normative public input and rejects an omitted, deleted or changed one |  | tests/input_manifest.py | from LG-0037; audit R7. 2026-10-02: the release-readiness contract and its evidence are retained privately; the public harness now binds the public normative documents (docs/README, MIGRATION, PROTOCOLS, SKILL-REGISTRY, BRIEF-EXAMPLE, EVIDENCE), with omission, deletion and dirty-change tests retargeted to them. Not yet independently reviewed. |
| LG-0045 | P2 | OPEN | 2026-10-02 | Owner verification must not mutate reviewed source | +tests +docs | An independent review confirms every owner-facing verification command leaves the reviewed tree byte-identical |  | tests/ | from LG-0035; audit R8; baseline reproduced. 2026-10-02: the owner integration packet that carried these commands is retained privately; the public suites assert byte-identical inputs per test, which is not yet an independent review of owner commands. |
| LG-0046 | P2 | BLOCKED | 2026-10-02 | Fresh sessions must discover and route project skills | +tests +docs | An independent reviewer observes a fresh agent session in a project with a SKILL-REGISTRY.md read the registry at Bootstrap and keep to its authority rules | external gate: a safe sandbox for observing an authenticated fresh session | SKILL.md | from LG-0028; audit R9. Design, greeting and companion-content checks passed; the end-to-end fresh-session observation never ran because the sandbox it needs could not be built. 2026-10-02: the generic routing bullet moved out of the wiring block into a conditional Project skills line; the observation is still owed. |
<!-- 2026-09-14 evidence correction: no live rows are reopened; LG-0036 and LG-0037 remain terminal in the archive, with canonical control/mutant packets and 198-test verification under tests/fixtures/hardening-2026-09-12/final/. -->
<!-- 2026-09-15 packet correction: no live rows are reopened; the final Architect
     manifest is 47 reviewed inputs and 0 evidence files, with older 50/23
     counts retained as historical claims in CHANGELOG. -->

<!-- 2026-09-15 verification correction: retained suite counts are 211
     repository, 22 acceptance/manifest/mutant, 11 research, and 8 Architect
     tests; no live finding is reopened. -->
