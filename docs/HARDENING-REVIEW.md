# Local hardening review — 2026-09-10

**Current acceptance is recorded in the September 11 continuation section at the end.** Earlier sections below are retained history; the continuation corrects their population and installation evidence claims.

This repair addresses the twelve confirmed cross-check requirements and four additional migration defects reproduced during independent review. The implementation stays on `fix/project-docs-protocol-gaps-2026-09-09`. The inspected starting commit was `5621f038e947fc32de3c8aaf8f31ea579e863553`; the released baseline is `bf14c4a01240b1cf04a5358d330e629a9017c7de`.

The completed implementation passes 89 discoverable tests: 43 Doctor cases, 37 migration cases and 9 lifecycle replay cases. Independent review reproduced and rechecked the additional migration defects, including the final indented-table variant, and reports no remaining confirmed blockers. All 21 tracked repair findings are CLOSED in `LEDGER-ARCHIVE.md`; the live ledger has zero repair findings and STATUS is ready for local human review. D-0005 compaction remains deferred.

Implementation commit: `16a1bb9ebcaa3cebd5dd624b748aaf321f3eec28`. The following documentation commit records the final register close and this report; resolve it with `git log -1 --format=%H -- docs/LEDGER-ARCHIVE.md`. The active branch contains both, and `main`, remote-tracking refs and release tags remain at their prior values.

## Requirement-to-evidence map

C-numbers preserve the latest cross-check's ordered list. Commands run from the repository root.

| Requirement | Implementation and local evidence |
|---|---|
| C1 — malformed LEDGER crashes Doctor | `tests.test_doctor.DoctorTests.test_malformed_ledger_headers_do_not_abort_later_checks`: missing/drifted headers produce FAIL and dependent SKIPs, with later checks present. Bad row widths retain diagnostics for valid rows. |
| C2 — oversized referenced IDs crash | `test_oversized_references_in_every_cell`, `test_oversized_blocked_reference_is_not_valid`, and `test_oversized_superseded_successor_is_not_valid`: a shared twelve-digit guard covers primary cells and references; malformed input does not reach unbounded integer conversion. |
| C3 — migration is not idempotent | `tests.test_migrate.MigrationTests.test_same_plan_and_fresh_plan_are_byte_idempotent` and archival source-identity case: same-plan replay and a newly generated plan preserve bytes and do not duplicate source mappings. |
| C4 — allocation ignores archive/reservations | `test_allocates_after_archive_and_reservation_aliases` plus prefix and width cases: all register Markdown contributes reserved IDs; default and family series remain distinct. |
| C5 — placeholder dates and unsafe writes | Real-date, unreviewed-row, blocked-source, input-drift, dropped-mapping and interruption cases in `test_migrate.py`; reviewed JSON plan, journal before writes, CHANGELOG first, atomic per-file replacement and conflict-checked replay. See [MIGRATION.md](MIGRATION.md). |
| C6 — archive aliases compare textually | `test_numeric_aliases_collide_with_live_ids`: `LG-1` and `LG-0001` collide in both directions; family prefixes remain distinct. |
| C7 — lifecycle cases are only declarations | `test_lifecycle.py` replays authored file transitions through the real Doctor and verifies gates, reserved IDs, exact archive rows and real artifact hashes. Four separate [skill-use observations](../tests/fixtures/forward/README.md) retain actual independent agent outputs. Neither is presented as an automated Brief/Close writer. |
| C8 — migration write mode is untested | `test_cli_review_write_and_replay`, the failure/replay cases, generated-ledger Doctor checks, and `test_twenty_findings_review_write_and_fresh_plan_preserve_all_sources` exercise actual writes and preserved STATUS bytes. |
| C9 — workflow summaries disagree | SKILL's install block, both agent instruction files, root/docs/template READMEs and ledger banner agree: ordinary Close is CHANGELOG → LEDGER if installed → STATUS → optional DECISIONS. Brief writes reserved DECISIONS between CHANGELOG and LEDGER. The independent skill-use cases follow these orders in their reported edits. |
| C10 — repository STATUS is stale | The final Close archives LG-0001–LG-0021 with their checks and implementation commit; the dashboard derives from zero live repair findings. Historical claims remain intact; the update is a new CHANGELOG entry. |
| C11 — generic discovery runs zero tests | `tests/__init__.py` and standard `test_*.py` modules make `python3 -B -m unittest discover -v` execute the suite. `tests/run_regression.py` uses the same discovery and refuses an empty suite. |
| C12 — report overstates verification | This report separates CLI/API executions, authored lifecycle replay, observed agent outputs and untested semantic boundaries. The scenario index is not counted as another test. |

## Additional findings from this repair

The original Doctor suite reproduced a normal language fence opener (` ```markdown `) falsely exposing wiring, plus an append-only conflict in the decision-tag repair message. Both have executable regressions and corrections.

Independent migration review reproduced four more cases: a literal HTML comment inside a fence consuming later live findings (LG-0018); hidden ledger example tables receiving new rows (LG-0019); a journal whose `inputs` is a list escaping as a traceback (LG-0020); and structured `BLOCKED`/`owner` table data proposed as an unblocked row (LG-0021). Each was reproduced, covered by executable regressions, repaired and independently rechecked. The hidden-table repair also rejects four-space/tab-indented code tables before creating a journal or changing registers, while preserving support for zero-to-three-space table indentation.

## What the previous report established

At the inspected starting commit, `python3 -B -m unittest discover -v` ran zero tests. The custom runner executed ten Doctor cases and one migration preview. Its twelfth reported PASS checked only that eleven manifest entries had names and invariant text; it did not execute those eleven lifecycles or migration write mode. This corrects the verification claim while preserving the historical CHANGELOG entries.

Before fixes, the new Doctor cases reproduced the unbound check-list crash and oversized-reference crashes. The migration reproduction ran the old bare `--write` twice: it created two rows for one source, allocated below archive/reservation IDs, and saved `YYYY-MM-DD`. Failure injections in the repaired implementation cover interruptions before the log, before the ledger replacement, after the ledger replacement, and conflicting edits during recovery.

## Verification and boundaries

Verified on macOS with Python 3.14.4 on 2026-09-10. Commands run from this repository root:

| Command or inspection | Observed result |
|---|---|
| `python3 -B -m unittest discover -v` | 89 tests passed; 43 Doctor, 37 migration, 9 lifecycle replay. |
| `python3 -B tests/run_regression.py` | The same 89 tests passed after register closure. |
| `python3 -B scripts/docs-doctor.py . --today 2026-09-10` | Exit 0: 38 checks, 32 PASS, 6 INFO, no WARN/FAIL/SKIP both before and after the final register close; the final check sees 21 archived IDs and 0 live rows. |
| Skill Creator `quick_validate.py .` | `Skill is valid!`; PyYAML 6.0.3 was installed only in ignored repository-local scratch for this external validator. |
| Python in-memory compilation | Seven shipped script/test modules compiled successfully. |
| `git diff --check` | No whitespace errors. |
| Register and wiring inspection | AGENTS and CLAUDE are byte-identical; the entire starting CHANGELOG remains an unchanged suffix; DECISIONS bytes match the starting commit. All 21 terminal rows were read back and matched cell for cell before live-row removal. |

The deterministic suite and shipped scripts use only Python's standard library; they require no private fixtures or network service. Test scratch files stay in ignored `tests/.tmp/`. Independent review's preceding full-suite run passed all 86 then-current tests; its final focused recheck confirmed the indented-table repair, and the primary session then ran the full 89-test suite above. A focused review pass is not counted as another full-suite run.

The lifecycle JSON traces are authored examples. Their tests execute Doctor and verify artifact invariants; they do not re-run an agent or implement a hidden writer. The separate forward exercise is one independent agent processing four cases, not four independent reviewers or a compliance estimate. Retained before/after files demonstrate final state; they are not a filesystem timing trace.

Doctor verifies structure. It does not prove the meaning of an occupied decision ID, the truth of CLOSED evidence, or the semantic completeness of a migration inventory. Deliberate reopen retains its ID and triggers a conservative archive-collision diagnostic; the row-specific hashed reopen event must be checked manually. Reservation recovery after an intervening Close may append lower-numbered decisions and legitimately produce an ordering advisory.

Migration uses an explicit reviewed plan and a durable recovery journal with atomic individual file replacements. It is not globally atomic across files and assumes one writer. Its source identity includes source text and section, so intentional edits to those need reconciliation. It inventories supported STATUS sections; other trackers and custom sections still require manual inventory. STATUS remains intact until separately reviewed adoption.

The repository-contained fixtures correctly produce a `nested-register` advisory because the enclosing repository owns this register. Healthy fixture assertions require that to be the only warning. The repository's own Doctor check is the separate exit-0 control.

All source changes and retained artifacts belong to this repository. No private workbook, collateral project, remote ref, release tag or published state is part of this repair. The earlier compaction procedure remains deferred under D-0005 and is outside this task.

## 2026-09-11 — second independent review, and what this round adds

A second independent review of `88b90b4` reported four P2 defects. All four were reproduced here before repair; none is recorded on the reviewer's word. Each is closed with a regression confirmed to fail against the `88b90b4` scripts and pass against these.

| Reported defect | State | Evidence |
|---|---|---|
| Extra column disables Status/Blocked-on extraction | closed | GFM delimiter-based header detection; the defect's own fixture now writes `BLOCKED` with its gate intact |
| Indented code example certified as active wiring | closed | `visible_lines()` consumes CommonMark indented code; the fixture now FAILs `wiring-block` |
| Malformed delimiter accepted as a valid table | closed | delimiter cell count must equal the header's; the fixture now FAILs `ledger-header` |
| Root register unreachable beside an empty `docs/` | closed | discovery mirrors Doctor's `find_register` |
| *(found while attacking the repair)* all-unnamed columns map a state token as OPEN | closed | left unresolved for a human (D-0018) |

Two coverage gaps the reviewer named are closed: the git-dependent checks and a fresh install built from `templates/` now have executable tests. The contract ambiguity he raised about ROADMAP and GLOSSARY is settled in D-0017.

Acceptance evidence for the highest-risk change, the indented-code rule, is a population comparison rather than an argument: Doctor was run read-only over all 28 qualifying registers on this machine under the `88b90b4` script and under this one, and produced **zero differing check lines**. Hiding live instructions would be worse than the defect being fixed, so that comparison, not the unit tests, is what licenses the change. 128 tests pass; Doctor exits 0 on this repository; migration preview over a real register left it byte-identical.

The bounded-evidence statements in the sections above still hold and are not superseded: the lifecycle traces remain authored examples, Doctor still verifies structure rather than meaning, and migration still assumes one writer.

## 2026-09-11 — continuation completed locally with exact-code independent review

Starting commit: `328105fcbeada838284096bb883efb44907570a9`. Implementation and retained evidence commit: `80fb78687ed8408b7d4d230bb2632c191ba2994b`. The following documentation commit records Close and this report; the final local handoff is the branch HEAD. Previous review baseline remains `88b90b4cc74512f701497e2326a12654da547771`; released `main` remains `bf14c4a01240b1cf04a5358d330e629a9017c7de`. The local branch named `v0.4.0` remains `8671e8d03224614290ff5aa3859e349eff587d13`; it is not a tag. No push, merge, publication, release-ref change or unrelated project edit was performed.

The active Codex installation was verified as the existing symlink from `~/.codex/skills/project-docs-protocol` to this repository. It was reused without replacement. Bootstrap read the complete canonical skill, both instruction files, STATUS, recent CHANGELOG, relevant decisions including D-0005/D-0017/D-0018, and the live ledger. The user's explicit continuation request supplied the current focus. Primary alone wrote the register and allocated LG-0022–LG-0031; implementation lanes owned disjoint files or regions. All ten continuation rows are now CLOSED in the archive, with resolving commit and per-row checks. Zero live repair findings remain. D-0005 remains deferred.

### Findings, implementation and retained regressions

| Finding | Repair and evidence |
|---|---|
| LG-0022 — full nested-list wiring hidden | Doctor resolves list containers relative to their content baselines. Complete authentic six-space Install blocks, bullets, numbered items, tabs, blanks and lazy continuations receive all three wiring PASS results. `test_doctor_markdown.py` executes 23 full CLI cases across four methods. |
| LG-0023 — marker-line code certified | Surplus marker padding is checked on the item's first line. The tight `-     ## Project docs protocol` fixture receives FAIL/SKIP/SKIP; the original top-level four-space code exclusion remains covered. |
| LG-0024 — state/gate aliases dropped | Migration retains every gate alias in source order, joined by semicolons, and validates that review removes none. Matching state aliases are accepted; conflicting/invalid state cells remain unresolved. A writes BLOCKED with owner sign-off, B refuses before reconciliation, C retains provider quota and owner approval. Actual validation/write/replay tests cover each. |
| LG-0025 — formatted state becomes OPEN | Whole supported state tokens inside balanced emphasis/code markup are recognized in known columns. Unknown-column formatted or unsupported possible states require reconciliation. Title cells and ordinary prose never invent state semantics; bespoke tables without state tokens remain usable under D-0018. |
| LG-0026 — example content becomes live | HTML is retained as opaque unresolved source; indented unsupported examples also require reconciliation. Inner headings/lists/tables cannot become live mappings or ledger write targets. Multiline source is quoted when logged, preventing synthetic CHANGELOG headings. STATUS remains byte-identical. |
| LG-0027 — register selection diverges | `scripts/register_paths.py` supplies both tools' ownership rule: the unique complete STATUS/CHANGELOG/DECISIONS set wins; partial competitors do not. Two complete sets require explicit selection. Migration's two-file pre-install exception requires both `--pre-install` and `--register-dir`. Plans bind their resolved directory before validation or journal replay. Eight retained methods plus 11 independent selection/recovery cases exercise writes and nonselected-file preservation. |
| LG-0028 — minimum and next-session evidence missing | The skill, root README and template distinguish four docs from separately required agent wiring. Optional files are conditional and omitted index rows are removed. Two genuine four-doc tests verify personalization, empty decisions, real log/footer, exact file inventory and Doctor exit 0. Retained BRAND coverage seeds a real color while testing a deliberate pending-value warning. Two fresh contexts separately observed Install and Bootstrap/change/Close. |
| LG-0029 — acceptance claims exceed artifacts | This report and append-only CHANGELOG corrections mark the 28-register comparison unverified. Tracked scripts, dated hashes, inputs and outputs now support the bounded fixture claims. Test documentation distinguishes system temporary directories from nested scratch, automated fixtures from authored replays, and actual agent observations from both. |
| LG-0030 — ordered-sibling regression introduced during repair | Independent review found four-space code falsely certified and seven-space live wiring hidden after indented ordered siblings. The initial repair incorrectly required identical marker columns; it now matches the first unmatched list container. Both original starting-code controls passed, so retained intermediate source/CLI evidence identifies the affected version honestly. Final independent 1,098-wrapper sweep has zero visibility disagreements. |
| LG-0031 — new HTML boundary releases examples | Independent review and primary probes found tag-shaped comments/attributes, multiline void attributes, adjacent roots, and missing blank separators escaping the first boundary implementation. Standard-library HTML tokenization plus an explicit tag stack now handles lexical completeness; non-raw blocks retain content through blank separation, and raw elements preserve their closing-tag boundary. Twenty-seven semantic tests and 13 independent actual writes/hidden-target pairs cover the repair. Intermediate hashes and red outputs are retained. |

The source/discovery changes keep reviewed plans, archive/reservation allocation, stable provenance, stale-plan refusal, source preservation, journal recovery and same/fresh-plan idempotence. Existing automatic-discovery tests previously used incomplete two-file registers; those fixtures now satisfy the documented three-file premise, while a separate explicit pre-install test preserves the intended two-file workflow. Old plans without a resolved target binding must be regenerated and reviewed. Existing migrated rows are not silently rewritten; source edits or changed interpretation require reconciliation.

### Independent review and rejected candidates

Two separate critics inspected actual diffs and ran independently authored probes. Both completed their assigned reviews and final-code rechecks; neither an incomplete verifier nor a builder report is counted as independent acceptance. Final reviewed SHA-256 values:

| Runtime file | SHA-256 |
|---|---|
| `scripts/docs-doctor.py` | `65d5be94cf6b708f7b2de61a7cb6799adb60569a7ff91c7598e113eeb25bd07f` |
| `scripts/docs-migrate.py` | `dff2647f5e4594abaaff8d38f21791d421add7e1fb64d2247f73bc3e43c92d88` |
| `scripts/register_paths.py` | `f8ee7ba8bacd1404d9475e08108c94a5638befb6ea7d80d44f26d8deef1948b3` |

The Doctor critic independently ran 1,098 generated full-block wrappers for sentence visibility, 15 separately seeded full CLI cases for all three checks/exits, a token-for-token replay of the 23-case parser snapshot, and 11 discovery/replay cases. Migration's critic ran 82 relevant methods, independent A/B/C/all-alias and review/provenance probes, 13 actual HTML CLI writes with corresponding hidden-target refusals, and a four-doc installation artifact check. Final discovery and target-binding logic were reread after the HTML changes. No confirmed in-scope blocker remains at the hashes above.

One proposed expectation was rejected against markdown-it-py 4.0.0: `20.` cannot interrupt an open paragraph to create a nested ordered list. That input remains a code-negative control; a blank line supplies the legitimate numbered-list positive. An independent scratch-path comparison initially disagreed over macOS `/var` versus `/private/var`; canonicalizing the harness path resolved it, and it was not counted as a product defect. Ordinary titles such as “requests blocked by CORS,” a known title cell reading BLOCKED, and bespoke tables without a state token remain positive controls rather than guessed blocked states.

### Exact verification and evidence boundary

Primary execution on 2026-09-11 used macOS on arm64, Python 3.14.4 and Git 2.54.0. Detailed environment, command results and hashes are retained in [verification.json](../tests/fixtures/hardening-2026-09-11/verification.json).

| Check | Actual result |
|---|---|
| `python3 -B -m unittest discover -v` | Exit 0; 169 methods, zero skips, 13.018 seconds. |
| `python3 -B tests/run_regression.py` after Close | Exit 0; the same 169 methods, zero skips, 11.453 seconds. |
| `python3 -B tests/compare_hardening_baseline.py` | Exit 0 for the comparison runner. Same 41 methods: old `328105f` exits 1 with 72 assertion/subtest failures, zero errors/skips; current exits 0 with zero failures/errors/skips. Method count and subtest-failure count are different measures. |
| Doctor with actual date `--today 2026-09-11` after Close | Exit 0; 38 checks: 33 PASS, 5 INFO, zero WARN/FAIL/SKIP. Earlier pre-commit output was 32 PASS/6 INFO; the tenth STATUS commit moves churn from insufficient-data INFO to PASS. |
| Skill Creator `quick_validate.py .` | Exit 0, `Skill is valid!`; PyYAML 6.0.3 lives only in ignored development storage. |
| In-memory Python compilation | All 27 tracked/unignored Python files compile; exit 0. |
| `git diff --check` | Exit 0. |
| Register history and closure | Entire starting CHANGELOG is an unchanged suffix; DECISIONS is byte-identical to start; AGENTS/CLAUDE are identical. Ten terminal rows were verified cell-for-cell in the archive before live removal. |

The 169 methods comprise 74 existing Doctor methods, 4 new Doctor Markdown methods, 45 existing migration methods, 27 new migration-semantic methods, 8 selection methods, 2 minimal-install methods and 9 authored lifecycle methods. Independent sweeps/probes and the two-context observation are separate evidence, not extra unit-test counts. Normal runtime and tests need no third-party dependency; markdown-it-py 4.0.0 serves only as a development oracle. Full CommonMark/GFM conformance was not tested or claimed.

The [observed installation](../tests/fixtures/install-observation/README.md) retains the actual dispatched prompts with normalized paths, complete before/after projects, artifact hashes and explicitly condensed agent reports. The later fresh context received the small change request and relied on installed instructions/registers, not a transcript prescribing edits. Primary verified the requested output, four-doc inventories, clean optional index, unchanged DECISIONS, intact installation entry and Doctor exit 0. This is one sequential exercise. Snapshot bytes prove final state; write order is agent-reported, not an independent timing trace. Authored lifecycle replays likewise do not prove arbitrary agent compliance.

Correction to the earlier “population comparison licenses the change” claim: no detailed 28-register manifest, script revision, input fingerprints or normalized results were retained in the inspected repository, including available non-dependency scratch. The zero-differing-lines result is an unverified historical report, not current acceptance evidence. No unrelated private projects were rescanned. Even a retained dated sample would not establish “regresses no real project.” The stronger historical CHANGELOG sentence remains intact and is corrected by new entries.

A final independent handoff audit also reconciled the report, command counts, artifact hashes, links and register Close without a material mismatch. The implementation is ready for human merge review on the local branch. Remaining limits: conservative HTML may retain more than a renderer exposes; unsupported Markdown needs explicit reconciliation; human review still determines whether dispositions and closing evidence are true; migration assumes one writer and is recoverable across individual atomic files rather than globally atomic. Compaction under D-0005, other projects' migrations/wiring, merge, release tags and publication remain outside this completion.

## 2026-09-12 — final hardening evidence and stopping decision

This round started from clean `edccbc2b552fd5de0f2449930fdff7e9854e3ff4` on `fix/project-docs-protocol-gaps-2026-09-09`; `main` (`bf14c4a01240b1cf04a5358d330e629a9017c7de`) and `v0.4.0` (`8671e8d03224614290ff5aa3859e349eff587d13`) were not changed. The active installation remains the symlink `~/.codex/skills/project-docs-protocol` → `~/.claude/skills/project-docs-protocol`; the existing register was bootstrapped in place and no competing register was created.

Doctor's `visible_lines` now resolves every newly opened list container before checking a fence. The exact `- - ```markdown` authentic Install wrapper is hidden, its unfenced counterpart remains visible, and marker-line surplus padding remains indented code. Migration's `OpaqueBoundary` preserves CDATA, declaration and processing-instruction blocks as one unresolved source record, including incomplete and split terminators; hidden ten-column LEDGER tables are refused before journal creation, while a real table after the closed block remains usable. The runtime stays standard-library-only.

The bounded acceptance matrix is in `tests/fixtures/hardening-2026-09-12/ACCEPTANCE-MATRIX.md`. Red/green migration reproductions and final command output are in `tests/fixtures/hardening-2026-09-12/`; historical 2026-09-11 evidence was restored byte-for-byte after the comparison runner. The development oracle is `markdown-it-py 4.0.0` with the CommonMark preset, installed only in `/tmp/docs-md-oracle-2026-09-12`; it is not a shipped dependency.

Final checks on macOS arm64, Python 3.14.4, Git 2.54.0: `python3 -B -m unittest discover -v` — 176 methods, zero skips, exit 0; `python3 -B tests/run_regression.py` — same 176, zero skips, exit 0; `python3 -B tests/compare_hardening_baseline.py` — isolated 42-method comparison, baseline `328105f` exit 1 with 74 failures and zero errors/skips, current exit 0 with zero failures/errors/skips; Doctor `--today 2026-09-12` — 38 checks, 33 PASS, 5 INFO, zero WARN/FAIL/SKIP, exit 0; skill validation — `Skill is valid!`; in-memory compilation — 27 tracked Python files; `git diff --check` — exit 0. Fresh-install minimum tests pass with four documents, separate AGENTS wiring, personalized content, empty DECISIONS and the real footer/installation log.

Independent critics had no inherited conversation. The Doctor critic ran 32,704 generated marker/fence combinations plus 100 tab cases, 13 held-out API/CLI cases and the full Doctor suite; it found no in-scope issue at `scripts/docs-doctor.py` SHA-256 `a35eaef5c4d90dfe668488460ad89cf02ea694a143d311bfb07eca39338a5159`. The migration critic ran held-out complete/incomplete/split terminators, quoted and delimiter-looking content, adjacent active records, hidden ledger targets, real external tables, and reviewed refusal/replay probes; it reported one valid split-terminator defect during review, which was fixed and added to the regression suite. Final migration review is rerun against the post-fix hash and is recorded with the final handoff.

Runtime hashes at final review: `scripts/docs-doctor.py` `a35eaef5c4d90dfe668488460ad89cf02ea694a143d311bfb07eca39338a5159`; `scripts/docs-migrate.py` `912c6496de0954f2ed54deb5bbbcbf24a980b959b12f2a4c8cc10a03402830bc`; `scripts/register_paths.py` `f8ee7ba8bacd1404d9475e08108c94a5638befb6ea7d80d44f26d8deef1948b3`; `SKILL.md` `2c61f35e1c341b47149940d79711e77cb9c5a233140ab18337d5f6fcc430acc9`; templates README/STATUS/CHANGELOG/DECISIONS hashes are retained in the handoff command output. Documentation changes after runtime review require this final evidence consistency check; no runtime files changed after the critics' final pass.

Stopping decision: implementation completion, tested compatibility, independent review completion and local publication readiness are all satisfied for the declared supported behavior. Remaining limitations are explicit: conservative opaque HTML may retain more than a renderer exposes; unsupported Markdown and ambiguous migration layouts require reconciliation; Doctor and migration do not prove semantic truth or arbitrary agent compliance; migration recovery is file-sequence recoverable rather than globally atomic; D-0005 compaction, other repositories, merge, tags, push and publication remain outside this task. Human merge/release review is still required.

## 2026-09-14 — final repair continuation and truthful local handoff

This continuation supersedes the September 12 completion claim for the three findings promoted by the independent cross-check. Immutable START is `880e8c11a89cb5ca8094799e111da9c001b2d478`; the durable implementation and test/gate repair is `bf848b27627661bf8429821c81fab7ba24eda40a`. No push, merge, tag, publication, reset, D-0005 compaction or unrelated-repository edit was performed. The active installation remains the existing symlink at `~/.codex/skills/project-docs-protocol` resolving to this checkout.

| Finding | Repair and independent expected result | Evidence |
|---|---|---|
| LG-0032 mixed bullet/ordered transition | CommonMark list-container closure is applied before the interruption rule; the complete authentic Install block is one fenced code example. Expected Doctor result is `FAIL/SKIP/SKIP`, exit 2. An unfenced active control remains visible and passes all three wiring checks. | `tests/test_doctor.py` exact CLI regression, `tests/test_doctor_markdown.py` retained case `mixed-list-transition-fenced-authentic`, frozen source under `tests/fixtures/hardening-2026-09-12/cases/doctor-a1.md` |
| LG-0033 empty item plus blank | Empty list items are tracked separately from populated items and close before a top-level four-column code block. Expected result is `FAIL/SKIP/SKIP`, exit 2; a nonempty active control remains visible. | `tests/test_doctor.py` exact CLI regression, retained `empty-item-blank-fenced-authentic`, frozen `doctor-a2.md` |
| LG-0034 split CDATA/PI delimiters | `OpaqueBoundary` preserves physical newlines; only contiguous `]]>` and `?>` close. Declaration subset handling remains bounded. Hidden headings and the only ten-column ledger target remain unresolved and are refused before journal creation. | 12 `tests.test_migrate_opaque` methods, contiguous positive controls, split and EOF controls, hidden-target mutation assertions |
| LG-0035 corrected baseline | The acceptance comparator exports immutable `edccbc2` and runs the same 52 focused methods including `test_migrate_opaque`. Baseline has exactly 21 nominated failures plus one explicitly expected reconciliation error; current has no failures, errors or skips. | `tests/compare_hardening_baseline.py`, `tests/fixtures/hardening-2026-09-12/final/baseline-comparison.json` |
| LG-0036 fail-closed gates | Frozen exact fixture bytes and hashes, independent oracle metadata, and a validator reject incomplete/duplicate/substituted/malformed outputs, failures, errors, skips, expected failures, zero discovery, wrong exits and wrong runtime hashes. | `tests/acceptance_gate.py`, `tests/test_acceptance_gates.py`, `tests/test_acceptance_manifest.py`, `acceptance-cases.json` |
| LG-0037 closure accuracy | Register closure, dynamic manifests and final reports are corrected after implementation. Historical September 11 artifacts remain preserved and are not relabeled. | `docs/CHANGELOG.md`, `docs/LEDGER-ARCHIVE.md`, `docs/STATUS.md`, this continuation |

The independent domain reviews were restarted from compact final-hash packets after implementation: one covered Doctor list/fence transitions and one covered migration opacity, hidden write targets, source preservation and recovery. A separate gate-focused review attempted false greens against the acceptance validator. Their raw commands and outputs are retained under the dated fixture directory; summary-only earlier reports remain historical and are not used as sole acceptance evidence.

Fresh verification on Python 3.14.4: standard discovery and the explicit regression runner are required to pass with zero unexpected failures, errors, skips or expected-failure markers; compilation enumerates all tracked Python files dynamically; Doctor is run with the actual date; baseline and mutation gates use isolated subprocesses and identical test bytes. Python 3.10 evidence is retained from the prior review; Python 3.9 remains unverified because an isolated runtime was unavailable. The runtime remains standard-library-only, while markdown-it-py 4.0.0 is development-only oracle support.

Limitations remain explicit: finite fixtures do not prove zero possible parser errors; Doctor checks wiring structure rather than semantic truth; opaque handling is intentionally conservative; migration recovery is recoverable per file sequence rather than globally atomic; one-writer assumptions remain; and full CommonMark/GFM conformance is outside scope.

### Hash correction for the 2026-09-14 review

The earlier September 12 critic packets and the hash table in the preceding section describe the pre-repair `880e8c1` runtime and remain historical. They are not evidence for this continuation. The current `bf848b2` runtime hashes are `scripts/docs-doctor.py` `5453da1023d979b3d4a1cdede96c5fcaa1e2a8986f325cf6fe0ed4030f3ce94d`, `scripts/docs-migrate.py` `7218fe6303f0e4051912ddd32b9b46c4a2742a485a5db80e16d5a43e1f3aa2d7`, and `scripts/register_paths.py` `f8ee7ba8bacd1404d9475e08108c94a5638befb6ea7d80d44f26d8deef1948b3`. The dated final critic packets named below must be read for the independent final-hash review; no pre-repair summary is promoted.

Final independent packets are `tests/fixtures/hardening-2026-09-12/final/critic-doctor-final.txt`, `critic-migration-final.txt`, and `critic-gate-final.txt`. The migration packet records SHA-256 `a0a1ac0b8ed3645d55e0b87fa3ad8c303255d537f84dfa2a49282be04905c094` and current runtime hashes; the gate packet records the current comparator, validator, malformed-output and mutant checks. The older `critic-doctor.txt` and `critic-migration.txt` remain retained historical reports and are excluded from the final reviewer count because they hash the pre-repair runtime.

### Gate critic correction

The final gate critic initially identified optional `expected_failures` and empty-manifest acceptance as protocol gaps. The validator now requires a nonempty expected case manifest, a typed integer discovery count, and an explicit empty `expected_failures` list; the corresponding fault-injection assertions are included in `tests/test_acceptance_gates.py`. The two frozen Doctor positive fixtures were also corrected to carry the complete bounded-read clause and independently rerun as PASS/PASS/PASS, exit 0.


### Final count correction (historical pre-control record)

After the canonical frozen-manifest green-control regression was added, an
intermediate tree reported 194 tests. That packet remains historical
pre-control evidence; the current tree adds the canonical child runner and
full CLI corruption controls and is reported below.

## 2026-09-14 — canonical acceptance and final evidence correction

The exact runtime source commit for this acceptance repair is
`22fa3b64214403850f73c3695fa5b6795dd32078`. `tests/run_acceptance.py` executes
all four frozen cases against the real Doctor and migration CLIs. The control
packet is accepted by the validator; the isolated Doctor list-boundary mutant
changes a targeted case to an unexpected wiring PASS, and the isolated
migration newline-join mutant changes the split opaque inventory. Both mutant
runner commands exit 1 and their validator commands exit 1 with `REJECT`; no
failure is an import, syntax or fixture-setup error. The exact JSON packets
retain source commit, current or mutant hashes, commands, exits, stdout,
stderr, targeted case IDs and validator results:

- `tests/fixtures/hardening-2026-09-12/final/acceptance-control.json`
- `tests/fixtures/hardening-2026-09-12/final/acceptance-doctor-mutant.json`
- `tests/fixtures/hardening-2026-09-12/final/acceptance-migration-mutant.json`

The final local suite is **198 tests**, with zero failures, errors, skips or
expected-failure markers in both standard discovery and `tests/run_regression.py`.
The focused acceptance command runs 15 tests. The baseline comparator covers
five bounded regression modules and reports baseline 52 methods with 21
nominated failures plus one expected reconciliation error, while the current
tree is clean. The prior 193-test and 194-test packets remain historical
pre-control artifacts and are not counted as final evidence.

The prior `critic-doctor-final.txt`, `critic-migration-final.txt` and
`critic-gate-final.txt` packets cite earlier HEADs and are historical. Fresh
final-head rechecks are retained in the replacement packets after the final
verification run below; their reviewed SHA-256 values are the ones in
`final/hashes.json`. The older packets remain intact for audit history.

The final packet refresh was reviewed at `7f7e3660d673239996a655da648986a422c573b3`
and the final hash manifest records that reviewed HEAD while excluding itself. It
covers the runtime, tests, frozen fixtures, retained control and
mutant packets, review report, documentation registers, templates, skill and
instruction files. The five-module wording in the baseline artifact matches
`tests/compare_hardening_baseline.py`.
