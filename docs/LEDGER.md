# LEDGER

*Live findings for this implementation. Rows are edited in place while live; terminal rows move verbatim to `LEDGER-ARCHIVE.md`.*

Tags: +doctor +brief +lifecycle +migration +docs +tests

## Items

| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| LG-0048 | P3 | OPEN | 2026-10-05 | Nothing runs the registry validator unless an agent remembers to | +doctor +docs | Doctor names the registry validator whenever a SKILL-REGISTRY.md is present, or a test runs it over this repository |  | scripts/docs-doctor.py | 2026-10-05 independent review (major): a stale row goes unnoticed because the validator runs only after a registry edit and neither Doctor nor the suites run it. Mitigated in release/v0.4.1: SKILL.md now requires running it before invoking a registered skill (an agent in the fresh-session test did so unprompted). The structural fix is still owed. |
| LG-0049 | P3 | OPEN | 2026-10-05 | Re-review minor notes deferred to the next release | +docs +tests | The research companion names the record type for an unfetched passage, and the registry digest refuses a symlinked .DS_Store and covers nested .git contents or says why not |  | staging/research-protocol/SKILL.md | 2026-10-05 re-review (minor, non-blocking): a public source record requires an Accessed date that an unfetched page cannot honestly have, so the supplied-passage rule needs a record type; the digest exclusions skip a symlink named .DS_Store silently and ignore changes inside a nested .git/. Either fix inside a companion folder needs that companion's digest re-recorded after review. |
| LG-0050 | P3 | OPEN | 2026-10-23 | A command-line usage error exits 2, the code for a FAIL | +doctor +docs | Doctor exits 3 on a usage error, or the owner rules that 2 stays and SKILL.md's exit-code list says so |  | scripts/docs-doctor.py | 2026-10-23, found while adding --json: with no project root or an unknown flag, argparse prints usage to stderr and exits 2, which D-0013 assigns to at least one FAIL; 3 is the checker could not run. Pre-existing and identical in both modes; left unchanged because the exit codes were to stay exactly as they are. JSON consumers tell it apart by the missing object (README). 2026-10-23 owner brief: postponed — leave exit 2 as is for now (CHANGELOG brief, 2026-10-23). |
| LG-0052 | P2 | OPEN | 2026-10-26 | The external check does not isolate the judged product from the trusted checkout | +tests +docs | An independent review shows product commands run under an identity that cannot write the trusted checkout, the output or the interpreter, with all of that identity's processes ended before the re-check and the validator, and a long-running hostile product is rejected |  | tests/README.md | from LG-0044: F2 of the 2026-10-25 independent re-check on the owner's Mac (CHANGELOG 2026-10-26). Candidate product code runs as the user who owns the trusted checkout, and nothing ends its processes before the re-check, so a change made after the second check_harness can be accepted in some runs. The README procedure now states the isolation requirement (D-0028): product commands under an identity that cannot write TRUSTED, OUT or the interpreter; every process of that identity ended before the second check_harness; the trusted runner's setup, both check_harness runs and the validator outside it. Nothing in the harness enforces it yet. Context, F3: macOS 27's /sbin/sha256sum -c exits 0 on an empty record (even with --strict) and on an all-malformed record without --strict, so check_harness also tests the record's line count; whatever runs the product in isolation must keep that test. |
<!-- 2026-09-14 evidence correction: no live rows are reopened; LG-0036 and LG-0037 remain terminal in the archive, with canonical control/mutant packets and 198-test verification under tests/fixtures/hardening-2026-09-12/final/. -->
<!-- 2026-09-15 packet correction: no live rows are reopened; the final Architect
     manifest is 47 reviewed inputs and 0 evidence files, with older 50/23
     counts retained as historical claims in CHANGELOG. -->

<!-- 2026-09-15 verification correction: retained suite counts are 211
     repository, 22 acceptance/manifest/mutant, 11 research, and 8 Architect
     tests; no live finding is reopened. -->
