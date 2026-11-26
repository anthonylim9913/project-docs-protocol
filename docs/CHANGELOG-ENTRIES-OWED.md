## 2026-11-26 — delegated r4-judge: LG-0044 external trusted judge, pending independent review

Lane `r4-judge` on `fix/lg-0044-external-judge` rebased onto
`feat/r3-stranded-work` at `d41ec26`, then ported the external-judge code and
tests from `89ed3aa..88b46c2` with a three-way application. No alternate
register commits, root README or MIGRATION edits were replayed. The root README
count alone is updated from this lane's own measurements. Stage 1's
strict census, Git-error handling and commit-identity validation remain intact.
No exclusions changed. LG-0044 still requires the independent stage-2 review
specified by D-0029; this author-run evidence cannot close it.

The trusted runner and validator judge a separate candidate whose judging bytes
must match their recorded files. Modules load from verified bytes with isolated
entry points; the record and independently recorded external pin bind the
harness. The manifest adds record/digest output options. All 17 judging files
were re-derived from the trusted file reads: no entries were added or dropped
versus the alternate. Five Python files, the case manifest, six case fixtures,
the contract, two contiguous fixtures, the migration STATUS and LEDGER template
remain the exact set; scripts execute as candidate product code, and test helpers
and regression test files do not decide the acceptance verdict. The record is
bound but does not hash itself. The imported audit test checks the read set.

The owner ruling authorizes fixture-helper changes with byte-identical existing
assertions. `AcceptanceGuardRemovalTests.removal()` now re-records its disposable
mutants before the semantic check. A new regression applies its exact snapshot
guard mutation without re-recording and requires an integrity rejection.
`MutantSensitivityTests.validate()` keeps its body and assertions; its hash
function import now comes directly from `input_manifest` because the isolated
runner initializes its module globals only in main. Shared `copy_subject()`
skips `.DS_Store` when copying fixtures; shared `generate()` retains the strict
stage-1 scope restatement, factored into `reviewed_paths()` for the new external
fixture helper as well. No other existing test helpers were adapted.

A macOS temporary-path alias exposed a defect in the alternate's loaded-module
origin check; normalizing the harness root fixes the imported regression without
changing its assertion. Python 3.9 emits an explicit full-scan limitation and
checks known harness dependency names plus builtins; Python 3.10+ uses the full
stdlib inventory. The limitation warning is emitted at interpreter shutdown so
rejection diagnostics keep their existing prefix; a Python 3.9 guard regression
failed before that repair and now passes unchanged. Missing and linked harness
errors also retain the existing required-input diagnostic wording, preserving
all base assertions while rejecting earlier at the integrity boundary.
D-NEW-1 records the 3.9 implementation choice for the owner.
The test README describes the external review procedure and its assurance
limits, including unsandboxed candidate execution and trusted host/tooling.

Measured direct proofs on the final harness bytes: Python 3.14.4 discovery,
system Python 3.9.6 discovery and `tests/run_regression.py` each ran 542 tests,
OK with one skip. Research ran 123 tests, OK with three skips; Architect ran
118 tests, OK without skips. Measured suites: 542 core, 123 research,
118 Architect; 783 total. All 1,211 existing assertion
expressions are byte-identical to the base, and every base test file remains.
The documented external procedure also passed in disposable committed trusted
and candidate copies, with the four-case verdict, Git-object hash cross-check,
revision/clean-tree checks, external pin comparison and pre/post checksums.
That is author-run verification, not independent approval or OS isolation.

Doctor exits 1 with 43 checks: 34 pass, one owed-fragments WARN, zero FAIL,
eight INFO and zero skipped. The registry validator passes. Whitespace,
protected-register and scripts/staging/templates scope diffs are empty.
The harness checksum passes with strict, quiet shasum verification.
`python3 -B scripts/release-check.py --allow-doctor-warn` ran all three suites
again and exits 1: core 542, research 123 and Architect 118 all PASS; Doctor's
WARN is allowed; registry, working/staged/committed whitespace and all four
root README count claims PASS. Its sole FAIL is the protected newest CHANGELOG
entry's old core count: stated 514, measured 542. This is not waived or reported
as a passing release gate. The owner must fold this real owed entry at Close
and rerun the assembled release gate; the lane has no register-writing duty.
Registers are untouched; `PROGRESS.md` remains untracked. The owner must fold
both owed fragments, update current-state reporting in protocol order and retain
the independent stage-2 review required by D-0029. Hosted CI, independent final
review and candidate execution under a separate OS user or VM were not verified.
