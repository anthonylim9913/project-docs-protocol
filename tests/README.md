# Executable verification

From the repository root, run either entry point:

```sh
python3 -B -m unittest discover -v
python3 -B tests/run_regression.py
```

Both discover the same `test_*.py` suite and return a nonzero exit on failure. The explicit runner also refuses an empty suite. Tests use Python's standard library (Python 3.9 or newer). Most scratch projects live under ignored `tests/.tmp/`; Git checks, fresh-install checks and the JSON-mode fixtures use system temporary directories for their independent repositories and ancestor-free registers. Test cleanup removes those temporary projects. They need no private files, credentials or network service. The final local verification environment and actual test count are recorded in [the hardening review](../docs/HARDENING-REVIEW.md).

| Suite | What executes | What the result establishes |
|---|---|---|
| `test_skill_registry.py` and `test_registry_routing.py` | Real registry CLI plus an independent `struct.pack('>Q', ...)` v2 oracle and a seeded 2,000-tree comparison | Known-answer vector, legacy framing forgery rejected by v2, strict UTF-8 byte-order paths, non-UTF-8 refusal (skipped if the filesystem refuses the filename), unchanged metadata exclusions, malformed IDs, active/staged legacy refusal without digest disclosure, retired IDs not compared, unreviewed v2 output, and routing/template contracts. |
| `test_release_check.py` and `test_leak_scan.py` | Disposable Git repositories, tiny real unittest suites, invented external regexes and local ref updates | Measured current counts and wrong-count refusal; interpreter repetition, Doctor WARN override and fatal checks; intermediate/merge blobs, metadata, binary skips, private diagnostics, hook ranges and fail-closed errors. New fixtures do not inspect ancestor registers or assume where the system temporary directory lives. |
| `test_doctor.py` | Real Doctor CLI against controlled registers | Specific check levels/exits for malformed headers, IDs and references, numeric aliases, archives, fences, footers, dates, staleness, schema and decision citations; file bytes and paths remain unchanged. |
| `test_doctor_json.py` | Real Doctor CLI in text and `--json` mode on three [fixture projects](fixtures/doctor-json/README.md) copied outside this repository, plus exit-3 runs and an injected crash | Text output still equals the baseline captured before `--json` existed; JSON mode prints one parseable object with the same checks in the same order, matching summary counts, the same exit code and the same stderr, including when the checker cannot run. |
| `test_doctor_markdown.py` | Complete authentic Install blocks in list and code contexts through Doctor | All three wiring checks, exit codes and read-only behavior; expectations compared separately with retained parser tokens. |
| `test_register_selection.py` | Both CLIs select complete or explicit registers and migration applies reviewed plans | Competing-register ownership, explicit pre-install support, preservation of nonselected files and refusal to redirect a plan. |
| `test_installation.py` | Four documents personalized from the shipped templates, authentic AGENTS wiring, and the real Doctor CLI | The minimum's file inventory, README index and local links, personalized fields, empty DECISIONS, real installation entry, install footer and exit 0. This is a deterministic fixture, not an agent installation. |
| `test_migrate.py` | Real migration API and CLI, plus Doctor on generated rows | Review gates, source preservation, stable provenance, allocation, dates, complete twenty-finding write, same/fresh-plan no-ops, table placement, input drift and injected I/O failure/recovery. |
| `test_migrate_semantics.py` and `test_migrate_opaque.py` | Reviewed validation, write and replay for semantic columns, HTML examples, and declaration/CDATA/processing-instruction boundaries | Every explicit gate survives, conflicting or unsupported state requires reconciliation, and example contents stay out of live mappings and ledger write targets. |
| `test_lifecycle.py` | Recorded example edits followed by the real Doctor and a real artifact check | The retained examples preserve their explicit gates, IDs and provenance; Doctor diagnoses intermediate states; actual artifact content/hash checks detect corruption. |
| `test_status_uniqueness.py` | Real Doctor CLI on handwritten dashboards | Repeated canonical peer headings and visible date fields warn with physical locations; hidden examples, custom headings and separate parent scopes do not collide. Read-only snapshots and ancestor-free projects keep unrelated warnings from making a negative test pass. |
| `test_acceptance_manifest.py` and `test_acceptance_gates.py` | Frozen hardening fixture bytes plus the fail-closed acceptance validator under deliberate malformed/failure/skip/substitution/hash faults | A green child must have complete declared case identities, behavioral assertions, exit codes and runtime hashes; nonzero/error/skip/empty/malformed output is rejected. |
| `run_acceptance.py` and `test_mutants.py` | The canonical four-case child runner against the real Doctor and migration CLIs, plus isolated source mutants | The unmutated runtime is accepted; each semantic mutant changes a targeted case and is rejected by the same validator with retained command, hash, stdout and stderr evidence. |

`scenarios.json` is an index linking the eleven original scenario names to executable test methods. Several names share one mixed-answer test; the index is not counted as an additional passing test or as eleven independent agent executions.

Delegation currency and git-unrecorded-commits regressions use the current block
and disposable Git repositories. The hardening Doctor examples and their pinned
hashes include the new clause so the existing visibility mutant still has to
produce a clean positive, not merely a stale-block warning. The acceptance
validator's exhaustive check inventory adds the new SKIP; no expected case or
gate is removed. Doctor JSON tests retain the captured 1.5.0 bytes and checksums,
then derive exact current text expectations for the fourth clause and additional
git SKIP/count. Historical installation captures remain observations, not current
installation templates. Markdown visibility gains a separately recorded oracle
snapshot, leaving earlier observations untouched.

Lifecycle examples are **authored artifact replays**. There is no automatic Install/Brief/Close writer in this skill. The installation tests apply explicit fixture edits to templates; writing those files is not evidence that an arbitrary agent chooses those edits, that archive recovery is automatically idempotent, or that authorization can be inferred from prose. The four [independent skill-use observations](fixtures/forward/README.md) are recorded separately from the deterministic suite. See [lifecycle evidence](fixtures/lifecycle/README.md) for the per-example boundaries. A subsequent Install → Bootstrap → Close observation must retain its separate contexts, prompts and before/after artifacts, and is not counted as an automated test or a general compliance rate.

Scratch projects under `tests/.tmp/` are nested inside this repository's own installed register. Doctor therefore reports the expected `nested-register` advisory; an otherwise-healthy nested fixture exits 1 and must have no other warning/failure. Fresh-install fixtures run outside that ancestry and assert exit 0 directly, as does the repository's own Doctor check. The retained six-document `FreshInstallTests` cases exercise extra scaffold and a pending brand-value warning; `MinimalInstallTests` separately proves D-0017's four-document contract. Recovery after an intervening Close can produce a `decisions-order` advisory. A deliberate reopen still triggers the conservative `ledger-archive-ids` collision check; its row/event identity needs manual verification. Tests assert these diagnostics rather than suppressing them.

Doctor checks CLOSED evidence structure, not truth or the semantic identity of an occupied decision ID. The non-git lifecycle case runs its stated verification command and compares SHA-256 independently, then corrupts the artifact to demonstrate why those checks are necessary.

The [observed installation and next session](fixtures/install-observation/README.md) use two fresh contexts, retained prompts and snapshots. This is one bounded exercise; ordering is agent-reported and final bytes are independently checked. The [Markdown oracle](fixtures/markdown-oracle/README.md) and [hardening evidence](fixtures/hardening-2026-09-11/README.md) retain targeted red/green checks and independent probes, separate from the standard-library suite.

The frozen hardening inventory lives in `fixtures/hardening-2026-09-12/acceptance-cases.json`; `run_acceptance.py` executes its four real CLI cases, while `validate_acceptance.py` and `test_acceptance_gates.py` enforce declared case identities, behavioral assertions, child exits, and runtime hashes. The baseline comparator uses the corrected `edccbc2` source and includes `test_migrate_opaque.py`; its promoted baseline failures/errors are matched by identity rather than by a nonzero exit alone. Retained canonical control and mutant packets live under `fixtures/hardening-2026-09-12/final/acceptance-*.json`.

## Default-bound input census (D-0029, stage 1)

`input_manifest.py` binds every tracked or present file by default, including new
root files, new directories and `.github/workflows/tests.yml`. Its only exclusions
are the live registers `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`,
`docs/LEDGER.md` and `docs/LEDGER-ARCHIVE.md`, the review documents
`docs/HARDENING-REVIEW.md` and `docs/LESSONS-REVIEW.md`, `.git/` directories,
`tests/.tmp/` and files named `.DS_Store`. CHANGELOG and DECISIONS retain their
history-preservation checks; exclusion from the frozen manifest is not permission
to rewrite their history. Bytecode and import hooks are refused, not skipped.

The census walks with a raising error handler, pruning only `.git` and
`tests/.tmp`. Untracked inputs are the in-scope walk minus `git ls-tree -r HEAD`,
not Git's potentially incomplete untracked walk. Any Git failure or stderr output
refuses generation, including an exit-zero warning. Stray inputs are named in
the refusal; unreadable directories report `cannot enumerate: <path>` and the CLI
retains exit 2. `test_input_census.py` covers real permission denial (skipped only
when the executing user can still read mode-zero paths), excluded scratch
directories and injected Git failures/warnings. `test_input_manifest_cli.py`
covers default binding, deletions, omissions, edits and the exact exclusion list.
`acceptance_support.py` computes expected scope independently from committed paths
and a literal restatement of these exclusions, never the generator's scope code.

This is a scope repair pending independent review, not closure of LG-0044.
In-tree validation still cannot establish independent approval of its own run;
the trusted external judge, harness record and pin are stage-2 work under D-0029.
