# Executable verification

From the repository root, run either entry point:

```sh
python3 -B -m unittest discover -v
python3 -B tests/run_regression.py
```

Both discover the same `test_*.py` suite and return a nonzero exit on failure. The explicit runner also refuses an empty suite. Tests use Python's standard library (Python 3.9 or newer). Most scratch projects live under ignored `tests/.tmp/`; Git checks, fresh-install checks and the JSON-mode fixtures use system temporary directories for their independent repositories and ancestor-free registers. Test cleanup removes those temporary projects. They need no private files, credentials or network service. The final local verification environment and actual test count are recorded in [the hardening review](../docs/HARDENING-REVIEW.md).

| Suite | What executes | What the result establishes |
|---|---|---|
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
| `test_input_manifest_cli.py` | The real manifest generator and validator on disposable committed copies | The bound scope is every file except a pinned exclusion list: a document, root file or directory added later is bound by default, and omitting, deleting or changing one byte of it is rejected; bytecode and import hooks are refused whether committed or not; a `.DS_Store` is skipped by name and nothing else that is ignored is (LG-0044, D-0025). |
| `test_acceptance_harness_binding.py` | The real runner and validator, in-tree and as a trusted checkout judging a separate candidate, after one-byte edits to each judging file, a missing, altered or short record, a wrong pin, and a shadowing package, stdlib-named module or bytecode planted in `tests/` | The in-tree check refuses each of these; an audit of the files the runner and validator open equals `HARNESS_FILES`; the external check accepts an unchanged candidate, rejects a product mutant by behavior, never executes the candidate's judging code and refuses a candidate whose judging files differ; a candidate's `core.fsmonitor` command never runs and a replacement ref cannot make a mutant commit judge as another; every harness Git call goes through `input_manifest.git()` (D-0027). |
| `test_acceptance_guard_removal.py` | Named guards removed in disposable copies, and three mutants of the validator's own checks | Each named regression fails without its guard. `InTreeLimitTests` records the in-tree check's limit: the candidate's own validator approves a forged packet after each mutant, and the external check refuses all three. |
| `run_acceptance.py` and `test_mutants.py` | The canonical four-case child runner against the real Doctor and migration CLIs, plus isolated source mutants | The unmutated runtime is accepted; each semantic mutant changes a targeted case and is rejected by the same validator with retained command, hash, stdout and stderr evidence. |

`scenarios.json` is an index linking the eleven original scenario names to executable test methods. Several names share one mixed-answer test; the index is not counted as an additional passing test or as eleven independent agent executions.

Lifecycle examples are **authored artifact replays**. There is no automatic Install/Brief/Close writer in this skill. The installation tests apply explicit fixture edits to templates; writing those files is not evidence that an arbitrary agent chooses those edits, that archive recovery is automatically idempotent, or that authorization can be inferred from prose. The four [independent skill-use observations](fixtures/forward/README.md) are recorded separately from the deterministic suite. See [lifecycle evidence](fixtures/lifecycle/README.md) for the per-example boundaries. A subsequent Install → Bootstrap → Close observation must retain its separate contexts, prompts and before/after artifacts, and is not counted as an automated test or a general compliance rate.

Scratch projects under `tests/.tmp/` are nested inside this repository's own installed register. Doctor therefore reports the expected `nested-register` advisory; an otherwise-healthy nested fixture exits 1 and must have no other warning/failure. Fresh-install fixtures run outside that ancestry and assert exit 0 directly, as does the repository's own Doctor check. The retained six-document `FreshInstallTests` cases exercise extra scaffold and a pending brand-value warning; `MinimalInstallTests` separately proves D-0017's four-document contract. Recovery after an intervening Close can produce a `decisions-order` advisory. A deliberate reopen still triggers the conservative `ledger-archive-ids` collision check; its row/event identity needs manual verification. Tests assert these diagnostics rather than suppressing them.

Doctor checks CLOSED evidence structure, not truth or the semantic identity of an occupied decision ID. The non-git lifecycle case runs its stated verification command and compares SHA-256 independently, then corrupts the artifact to demonstrate why those checks are necessary.

The [observed installation and next session](fixtures/install-observation/README.md) use two fresh contexts, retained prompts and snapshots. This is one bounded exercise; ordering is agent-reported and final bytes are independently checked. The [Markdown oracle](fixtures/markdown-oracle/README.md) and [hardening evidence](fixtures/hardening-2026-09-11/README.md) retain targeted red/green checks and independent probes, separate from the standard-library suite.

The frozen hardening inventory lives in `fixtures/hardening-2026-09-12/acceptance-cases.json`; `run_acceptance.py` executes its four real CLI cases, while `validate_acceptance.py` and `test_acceptance_gates.py` enforce declared case identities, behavioral assertions, child exits, and runtime hashes. The baseline comparator uses the corrected `edccbc2` source and includes `test_migrate_opaque.py`; its promoted baseline failures/errors are matched by identity rather than by a nonzero exit alone. Retained canonical control and mutant packets live under `fixtures/hardening-2026-09-12/final/acceptance-*.json`.

**What the binding rule and the harness checks establish, and what they do not (D-0025, D-0027).** `tests/input_manifest.py` binds every file in the repository except its `EXCLUDED` list, and refuses bytecode and import hooks anywhere in the tree (remove a `__pycache__/` left by a run without `-B`). `tests/harness.sha256` lists every file the verdict reads (`HARNESS_FILES`) with its SHA-256, in `sha256sum` format. After editing any of them, regenerate it with `python3 -I -B tests/input_manifest.py . --print-harness-record > tests/harness.sha256`. `run_acceptance.py` and `validate_acceptance.py` re-run themselves under `python3 -I -B` and load the harness only from bytes that match the record.

Run inside the tree it judges, that check is a convenience, not a control. It names accidental or partial edits, planted modules and bytecode, and a wrong pin. It cannot catch an edit to the validator that switches off its own checks, even with the pin supplied, because the pin is then checked by the code that was edited (`InTreeLimitTests` keeps three such mutants). Only the external check below closes that gap. The runner never reports acceptance; only the validator does.

**External check (the reviewer's procedure).** `TRUSTED` is a separate clean checkout of a commit whose harness the reviewer has reviewed: the last reviewed `main`, or, for a change to the harness itself, the candidate's reviewed commit checked out again in a different directory. `CANDIDATE` is a fresh `git clone` the reviewer makes from the pull request's remote for this check, never a directory the candidate supplies: a supplied directory brings its own `.git` (config, hooks, replacement refs) with it. Run the check in a throwaway account or container. The trusted harness executes the candidate's `scripts/` as the product under test, with the privileges of the account that runs it, so that code can read or write anything the account can, the trusted checkout included.

```sh
set -eu                                   # every step must exit 0; the first failure stops the check
TRUSTED="/path/to/trusted-checkout"
CANDIDATE="/path/to/new-empty-directory"  # created by the clone below
REMOTE="https://github.com/OWNER/REPO.git"
REF="refs/pull/NUMBER/head"               # or the candidate branch
REVIEWED_PIN="SHA-256 recorded when the harness was reviewed"
OUT="$(mktemp -d)"

git clone --quiet --no-checkout "$REMOTE" "$CANDIDATE"
git -C "$CANDIDATE" fetch --quiet origin "$REF"
git -C "$CANDIDATE" checkout --quiet --detach FETCH_HEAD
cd "$TRUSTED"
test -z "$(git status --porcelain --ignored | grep -v '\.DS_Store$' || true)"   # clean, ignoring Finder metadata
sha256sum -c --quiet tests/harness.sha256  # coreutils, not repository code: every harness file matches
PIN="$(sha256sum tests/harness.sha256 | cut -c1-64)"
test "$PIN" = "$REVIEWED_PIN"
HEAD="$(git -C "$CANDIDATE" rev-parse HEAD)"
python3 -I -B tests/run_acceptance.py --runtime-root "$CANDIDATE" --source-commit "$HEAD" \
    --result "$OUT/acceptance-result.json" --harness-sha256 "$PIN"
python3 -I -B tests/input_manifest.py "$CANDIDATE" --out "$OUT/candidate-inputs.json"
python3 -I -B -c 'import json,sys; json.dump(json.load(open(sys.argv[1]))["files"], open(sys.argv[2], "w"))' \
    "$OUT/candidate-inputs.json" "$OUT/candidate-hashes.json"
sha256sum -c --quiet tests/harness.sha256  # again: the candidate's product ran since the first check
python3 -I -B tests/validate_acceptance.py --harness-sha256 "$PIN" --subject-root "$CANDIDATE" \
    "$OUT/acceptance-result.json" tests/fixtures/hardening-2026-09-12/acceptance-cases.json "$OUT/candidate-hashes.json"
```

The candidate is accepted only if every step exits 0. Any nonzero exit is a rejection, whichever step it comes from. A `REJECT: …` from the runner is final: the validator is not run after it, and nothing is re-run to get a different answer. The second `sha256sum -c` runs after the candidate's product has executed and immediately before the validator, so a product that rewrote a trusted harness file stops the check there. On a macOS without `sha256sum`, use `shasum -a 256` in its place, with the same arguments. The trusted manifest generator computes the candidate's input hashes. A reviewer who wants a list that does not come from repository code at all can build it with `git ls-files` and `sha256sum`, leaving out the `EXCLUDED` paths. The trusted code never imports the candidate's `tests/`. It refuses a candidate whose judging files or record differ from its own, and records the candidate's full input tree digest in the result (`source_provenance.runtime_tree_sha256`). The pin is the SHA-256 of `tests/harness.sha256`, the file that lists every harness file's hash. `python3 -I -B tests/input_manifest.py . --print-harness-digest` prints the same value from repository code.

**What the external check trusts (D-0027).** It trusts the interpreter, Git and the host, and the reviewer's review of `TRUSTED`. Two things in the candidate are not covered by that and are handled separately. *The candidate's `.git`* (its config, hooks and replacement refs) could run code in Git or make a commit appear to hold other content. The fresh clone keeps all three out of the check, and as a second line every Git command the harness runs sets `GIT_NO_REPLACE_OBJECTS=1`, `core.fsmonitor=false` and `core.hooksPath=/dev/null` (`input_manifest.git()`); other Git settings are not neutralised, which is why a supplied directory is never acceptable. *The candidate's product code* runs with the reviewer's privileges: the throwaway account or container bounds what it can reach, and the second `sha256sum -c` catches a rewritten trusted harness file. Neither stops a product that tampers with the host outside the trusted checkout, or with the interpreter or Git themselves.

**Checkout requirements.** The record and the manifest hash bytes, so they assume a checkout with LF line endings and case-preserving paths. An `eol=crlf` or `core.autocrlf=true` checkout, or a case-only rename on a case-insensitive file system, makes the harness check fail closed with `harness files do not match` and a list of files. File modes are not bound: `chmod +x` leaves the manifest unchanged. A nested `.git` directory below the root (for example inside `staging/`) is skipped, with its contents, without a message (see LG-0049).
