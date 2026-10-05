## 2026-10-05 — v0.4.1 released: re-review passed, reviewed digests recorded, README rewritten as a continuity system

The narrow independent re-review of `release/v0.4.1` passed every check: the fail-open fix (an unreadable record folder now fails in both the research checker and the index reader), the digest exclusions (clean trees keep their digests), the new wording, and the research and registry suites (118 and 12 tests). On the owner's instruction, both companions' reviewed digests are recorded in `docs/SKILL-REGISTRY.md` at version 0.2.1, and the registry validates again. Three passages the re-review found still describing the old rule now say to run the registry validator before invoking a registered skill (`SKILL.md`, `templates/README.md`, `docs/SKILL-REGISTRY.md`).

The README now presents the project as what it is — a continuity system: registers with one rule each, session rituals, a write order that survives interruption, automated checks, and extensions adopted when needed — with a diagram, the evidence, and the honest limit that measurement so far covers Claude Code and Codex. From this release the LICENSE names the copyright holder by the GitHub handle; earlier releases are left as published, at the owner's choice. The re-review's remaining minor notes are deferred to the next release (LG-0049).

## 2026-10-05 — v0.4.1 candidate: the review's confirmed defects and the fresh-session findings, fixed on a branch

An independent review of v0.4.0 and of the index-reader fix reported back; its two code findings and its privacy finding were reproduced here before any change. **The index-reader fix failed open:** moving the companion-signature probe into `research_paths.py` widened it to catch every OS error, so an unreadable record folder that the published checker FAILs became a SKIP. The reviewer's own one-line fix is applied (`except UnsafePath`), with two tests that fail on the pre-fix code. **A desktop `.DS_Store` file, or a `.git` folder, changed a skill's digest,** so an untouched vendored skill looked changed since review; the registry digest now ignores Python caches, `.git` and desktop metadata, and the registry template says to compute digests on files exactly as committed. **Nothing ran the registry validator unless an agent remembered to:** `SKILL.md` now requires running it before invoking a registered skill — the check one fresh-session test made unprompted (LG-0048 keeps the structural fix owed).

The fresh-session tests (LG-0046, closed) also produced three text fixes: the research companion says to ignore its writer's lock files in `.gitignore`, and that a digest taken over a supplied passage must never be presented as the page's; the Architect protocol says what an independent Reviewer is — one that starts from the frozen packet alone, never one sharing the Developer's context — and to scale stages and reviewers to the stakes. LG-0045 closes on the review's 65 fingerprinted runs. LG-0044 stays open on two gaps the review found in the acceptance harness: a fixed list of bound documents, and a validator that a one-byte edit can make approve itself. About sixty minor wording findings in the private review report are not addressed in this release.

Both companions' registry rows are stale on this branch by design: their files changed, so their digests are re-recorded only after a narrow independent re-review passes. Nothing is pushed until then.

## 2026-10-02 — published; LG-0046 made testable; an index-reader fix awaits review

The cleaned history is public: `main` and tags v0.1.0–v0.4.0 were force-pushed, and a fresh clone scans clean. Commits that are no longer referenced still open on GitHub by their exact ID; the owner has sent GitHub Support a purge request naming them.

`research-index.py` still treated any folder named `research/` as the research companion, the defect already fixed in `research-doctor.py`. The fix — one shared signature test in `research_paths.py`, called by both tools — is on the unpushed branch `fix/research-index-scope` with four tests, three of which fail on the published reader. Under D-0021 the research-protocol registry row stays at its reviewed digest until an independent review passes and the owner records the new one, so the branch's registry check reports it stale by design (LG-0047).

LG-0046 was blocked on a safe way to watch a fresh session. The boundary now exists outside this repository: a throwaway project wired like a real installation, with one active and one staged vendored skill, run in its own git worktree with no remote, with permission prompts left on and a read-only scorer. Three scenarios are ready — routing to the active skill, restraint with the staged one, and a skill edited after review. An independent review of v0.4.0 (LG-0044, LG-0045) and of the branch is queued for its own session.

## 2026-10-02 — the research and Architect companions and the skill registry, made coherent and made private-safe for release

The owner asked for the Architect protocol, the research companion, the skill registry, the ninth install question, the wiring-block change and the Doctor changes to ship together, checked as one system, and for nothing in the repository to expose the owner's machine or private work. Three independent reviews ran first: how the pieces combine (verdict: coherent after fixes), what the changes do to 31 real installations, and a tested privacy scrub.

**Combining.** The two companions now have one stated contract in `SKILL.md` (*Optional companions*): each is vendored into a project and registered there, owns only its folder, and never writes the core registers out of order. A frozen Architect review declares the register files as reporting paths, so closing as you go cannot change a frozen subject; the CHANGELOG entry precedes any stage advance; handoff owner decisions reach STATUS so a Brief can see them; contract findings are LG rows. The research Brief hook now follows the core Brief rules instead of writing every pick to DECISIONS, and its index read is bounded and placed as Bootstrap step 7. The registry records authority instead of implying it (D-0021), and the generic routing bullet left the always-loaded wiring block for a conditional *Project skills* line (D-0020). One table names each checker, when to run it and its exit codes.

**Defects found on real projects and fixed.** Doctor's rewritten `Last updated` parser accepted the field only at the start of a line: on one project it raised a false warning, on another it hid a real 49-day lag behind "no line found". A field now counts anywhere on the line when its date follows it, and prose that merely mentions the field never counts as a second one; three regression tests fail on the earlier parser. The research doctor judged any folder named `research/` as its companion, failing 13 of 31 real projects that keep ordinary research notes; it now requires the companion's signature and otherwise skips. The registry validator printed the exact digest an edited skill needed to pass, which let an agent re-approve unreviewed work; it no longer does. The research writer accepted any path with a `research` ancestor; it is confined to the project's own `research/`. Doctor is version 1.5.0.

**Privacy.** The repository's own release-readiness packet (106 files), its research working notes (14) and its hardening evidence records carried a private project's name 15 times and hundreds of absolute paths from the owner's machine, and bound commit IDs that a history rewrite removes. They stay private (D-0022): the full record is kept outside this repository. The acceptance harness that hashed them as inputs now binds the public normative documents, with its omission, deletion and dirty-change tests retargeted; the oracle recorder no longer writes the local interpreter or working directory. Every remaining path is a placeholder. Earlier entries below cite files and commit IDs that are no longer in the public repository; they are left as written, because this log is append-only.

Both companions' rows in this repository's registry are re-recorded at 0.2.0 with the digests of the trees reviewed here; the Markdown oracle test again compares against the parser recording made on exactly the current wiring-block text.

Verification: 335 root, 112 research and 113 Architect tests pass on a tree with no history; Doctor exits 0 on this repository and the registry validates; a read-only sweep of 31 real installations against the previous public Doctor shows no exit-code change, with differences only in the new headings check and three cross-register decision citations reported as information. LG-0046 stays blocked: no fresh agent session has yet been observed using the registry.

## 2026-09-22 — retain the reviewed E blocker and concrete release preparation

Actual Reviewer and Architect accept the prevention packet's bounded recorded evidence while holding E-03/E-09 and full E verification incomplete: native nested-sandbox exit71 and zero completed generated mount controls provide no accepted authenticated route. Retain their exact receipts, timeout-duration qualification and earlier metadata/companion adjudications; stop repeated platform attempts without waiving equality. Independent disposable proposal16e3015 supplies three inspection archives, identical two-runtime builds,49 Git-bound payloads,7 CLI help calls and selected392-file local recovery; none closes F/G. Preserve public-history dispositions and explicit unexecuted obligations in the blocked handoff. Candidate code and earlier failures remain unchanged; bounded reporting/preparation review and actual Architect return follow.

## 2026-09-22 — retain actual bounded Stage E review decisions

The actual Reviewer and Architect accept E-SMOKE-01 at c240a45 and the synthetic greeting repair 266b6ab (E-07/E-08); preserve both original FAIL receipts. Reviewer independently accepts bounded companion E-04/E-05/E-06 observations at 54bc921, with actual source retrieval, policy preservation, ordered Close and final reread. Complete context and Stage E remain verification incomplete: both earlier Install config deltas are unattributed, and the companion recorded a real project-trust change. Retain exact scoped receipts and requirement matrices without manufacturing a full-E verdict. Architect authorizes only credential-free prevention preparation; generated-file host OS barrier checks precede any possible new context. F preparation continues independently, while F/G acceptance and all release decisions remain open.

## 2026-09-22 — repair complete-entry reading in the owner CLI smoke

The independent Reviewer and Architect confirmed E-SMOKE-01 on 8ce6419: raw dated-heading matches truncated one real CHANGELOG entry inside its fenced example. Valid-first controls reproduce that truncation; the shipped snippet now uses Doctor's existing bounded visibility rules and emits original bytes through the next real entry boundary. Four focused methods pass on Python 3.14.4 and 3.9.25, including ordinary entries, two fence forms, comments and an effective visibility-guard mutation; immutable re-review remains pending. The actual greeting repair is separately frozen at 266b6ab for independent re-review; its context had stable captured identities and observed Close/reread. The distinct companion context completed its work but retains an incomplete global-identity result for one newly observed disposable-project trust entry; role verdicts and final E acceptance remain pending.

## 2026-09-22 — implement conditional registry routing for fresh-context verification

The actual Reviewer and Architect accepted the frozen E design at efa56ce; implementation acceptance remains pending. Install, Bootstrap, copied wiring, templates and protocol map now use an explicit twelve-column registry with workflow stages separate from lifecycle, authorization boundaries and required/optional fallbacks. Preserve the old Markdown oracle and record a separately named 29-wrapper observation with unchanged visibility expectations; correct the owner copied-doc exercise to CLI smoke. The pre-routing actual Install completed its five witnessed writes and Doctor17 pass, but the runner retained an unresolved concurrent global-config hash difference; no E acceptance or unchanged-config claim is made from it. Fresh candidate contexts and the actual FAIL/repair/re-review/Architect exercise follow.

## 2026-09-22 — accept bounded Stage D and freeze the Stage E contract

Actual Reviewer and Architect PASS exact 96bc0a61e96dbae8697819693cf8809667f558cd, closing R2/R3 and Architect-side R4; retain D-1/D-2 FAIL, D-3 PASS and original scopes unchanged. Retain the Reviewer's coverage clarification: independent exit-7 direct repair/handoff ran on Python3.14, accepted-J and malformed-digest checks on both; separate 113-method candidate suites ran on both. Developer core317 and Reviewer13 affected commands remain separately attributed. Archive LG-0039/LG-0040/LG-0041 with current evidence. Stage E's bounded contract precedes routing implementation and actual contexts; R7/R8/R9 and final component acceptance remain open. The formal D-2 acknowledgment became the eighth D-3 scope dependency, superseding the earlier seven-dependency preparation count.

## 2026-09-22 — retain formal D-2 FAIL before freezing D-3

Retained the actual D-2 FAIL receipt and original contract/input/evidence artifacts byte-for-byte. Its sole blocking product finding is ARCH-D2-NATIVE-FAIL-01, addressed by the local narrow correction. Added an isolated B-only preservation guard control to close an explicitly inconclusive historical harness observation; nine development methods now pass without changing the production history rule. D-3 declares new reporting paths and seven explicit input dependencies. Reviewer evidence limits and its postdelivery field-count harness correction remain attributed and preserved. The next immutable review must supersede D-2; E/F/G and component acceptance remain open.

## 2026-09-22 — preserve real failed-command evidence in Architect repair history

Frozen D-2 `2359a7b` completed its exact-subject Developer verification (core317, Architect104 on Python3.14.4 and3.9.25, scope28 on3.9.25, canonical4 and structural checks; overlapping counts). Subsequent Architect and accountable Reviewer root probes independently confirmed ARCH-D2-NATIVE-FAIL-01: actual failed-command observations were rejected even with honest FAIL receipts. Retain the original subject and evidence. A narrow local correction distinguishes complete evidence from expected outcomes, preserving strict PASS checks; eight new valid-first development methods pass, including accepted-chain and effective guard-removal coverage. Formal D-2 FAIL is being finalized before the next freeze. Repeated helper service failures were bypassed only through authorized sequential root assessment, without retries or invented PASS. E/F/G and component acceptance remain gated.

## 2026-09-22 — retain independent Stage D FAIL and consolidate its repair

Reviewer rejected exact `5bd249f` for earlier native binding, malformed prior v2 receipts, unchanged PASS→FAIL→PASS import and deletion of committed attempts. Retained its original receipt and evidence byte-for-byte plus actual Architect design/platform dispositions. Native per-attempt triples, full prior receipt checks and bounded same-contract history now implement the repair; 21 focused development methods pass, while the final subject and independent re-review remain pending. Additional read-only edge probes informed schema/pending-history and original-stage checks. R2/R3/R4 stay OPEN; E waits for actual Reviewer PASS and Architect cross-check. No component release acceptance exists. Correction to the immediately preceding interrupted Close layout: the C PASS prose following the D implementation paragraph belongs to the earlier “retain independent Stage C PASS” heading; both original entries remain unchanged.

## 2026-09-22 — retain independent Stage C PASS

## 2026-09-22 — implement explicit Architect lifecycle and exact packet binding

Schema 2 now distinguishes honest intermediate work, current review, awaiting Architect and accepted prior reporting packets. Complete Git input/mode checks, exact reporting deltas and immutable prior-packet validation close the reproduced Developer controls for R2/R3; valid-first CLI and nine effective guard-removal experiments address Architect-side R4. Original A/B/C receipts and manifests retain their bytes, subjects and scopes; the old root STATE is preserved as history, with live STATE reporting Stage D implementation. Correct the earlier Reviewer assertion that the old Doctor verified contract/manifest hashes: that assertion did not hold for its original implementation. Development observations are detailed in STAGE-D-IMPLEMENTATION.md; exact-subject verification and independent D review remain pending, and E/F/G remain open.

Reviewer passed exact `14ad1bddf9a28d7712cfd57a237be14ed2f6bbc2`, closing C-01–C-06 and applicable R5/R6 helper obligations. Retained the formal receipt byte-for-byte and verified its announced hashes. Independent current core315, research97 each on Python3.14.4/3.9.25, canonical4 and additional filesystem, transaction, provenance and19 guard checks support that subject; coverage units overlap. Archive LG-0042/LG-0043 with actual closure evidence. Actual agent source handling remains Stage E, extracted/platform work F and final Architect component acceptance G. The actual physical-cwd trust limit is explicit; the original FAIL and its evidence remain unchanged.

## 2026-09-22 — repair six findings from independent Stage C FAIL

The independent Reviewer returned FAIL for `d475cce088193cc07fb8ad3c7f329592e513984b`: newline sidecars, special permission bits, exact-ID suffix collisions, nested-root ambiguity, hidden records and multiple-record provenance. Retained the original receipt and actual Architect adjudications. Valid-first controls reproduced each finding; shared name/declaration rules, lexical root selection and post-flush mode verification implement the consolidated repair. Current development research discovery passes 97 methods on Python 3.14.4 and 3.9.25, including 19 guard experiments. Corrected contaminated draft cases and the legacy wrong-index fixture rather than counting unrelated rejection. The earlier mode/hidden-support prose was an overstated implementation claim for d475cce; its green tests did not close these cases. R5/R6 remain OPEN pending a new immutable independent review; Stage D stays gated.

## 2026-09-22 — release research locks even when cleanup itself fails

A valid-first injected cleanup failure exposed a retained cooperative lock in the Stage C draft. Nested finalizers now close target and lock descriptors even when deleting the owned temp fails; the focused control verifies nonblocking reacquisition and safe retry. Current research discovery passes 72 methods on Python 3.14.4, including eight guard experiments. Immutable-subject verification and independent review remain the Stage C gate; the earlier 71-method observations are retained for their development state.

## 2026-09-22 — complete Stage C implementation for independent review

Research helpers now share descriptor-based path checks and same-line provenance. The writer retains a stable lock, uses exclusive unique temps, preserves target modes and cleans only its own inode. Added public/private/unavailable controls, deterministic real-lock overlap and phase-specific interruption/retry tests, plus eight effective disposable guard mutations. A bounded analyst found duplicate headings, reserved-sidecar writes and malformed supersession siblings; valid-first tests reproduced them before repair. Development research discovery passed 71 methods on Python 3.14.4; exact-subject verification and independent Stage C review follow. The staged registry identity is refreshed without activation; source truth and actual agent compliance remain distinct later obligations.

## 2026-09-22 — accept Stage B and begin research containment repairs

Independent Reviewer passed `5ac2624c4bbc545e645509eed3d3bb5a08029c85`, closing B-01–B-05 and R1. Its current affected suites passed 114 methods on Python 3.14.4 and 3.9.25; prior full 312-method results remain evidence for b68e09f only. Retained exact PASS receipts; archive LG-0038 while R4/R7 keep their D/G obligations. Stage C now implements the reviewed research boundary contract: shared safe reads, stable lock, unique owned temp and explicit same-line provenance exceptions. Generated valid-first cases reproduced the original hazards and two adjacent cases before repair. Concurrency/interruption tests pass in development; no Stage C verdict is claimed.

## 2026-09-22 — preserve valid Doctor descriptions containing summary words

Independent Reviewer returned FAIL for `b68e09ff863d8cd62ff2400659808775a200b55b`: B-01–B-03 and B-05 passed, but B-04 retained a false rejection when an INFO description contained `checks:`. The Architect independently confirmed that this prose is permitted. Two valid-first controls reproduced the rejection before the one-line selector repair; a targeted mutant restores that exact defect. Numeric summary counts, duplicate-summary rejection and exhaustive line accounting remain enforced. Retained the exact FAIL receipt; Stage B awaits independent re-review and Stage C remains gated. The earlier 312-method runs belong to b68e09f.

## 2026-09-22 — close remaining Doctor-line and journal-target schema gaps

Independent re-review of `50844323306b3b584f36227b8c028c647edb745f` closed B-01–B-03 but returned FAIL for remaining B-04/B-05 siblings: unmatched Doctor diagnostic lines were ignored and a journal target could carry fields the actual writer refuses. The Architect corroborated both. Added exhaustive nonblank Doctor line accounting, preserving its scope notice and variable measurement prose, and exact journal target keys without changing the writer. Valid-first regressions reproduced both defects before repair; the new checks have targeted guard-removal controls. Retained both FAIL receipts; Stage B remains pending re-review, with compound R4/R7 and stages C–G still open. Host-exit timeouts and successful recovery retries remain separate evidence.

## 2026-09-22 — repair independently reproduced Stage B review findings

Independent Reviewer returned FAIL for `84f7cd018dab03a23320bc2f85f0154f5286144d` with B-01–B-05: index flags concealed changed behavior bytes, delegated authority was omitted, manifest output could alias source, Doctor reports could be incomplete, and migration observations could contradict preserved history or row state. The Architect separately confirmed the Doctor sibling. Reproduced seven acceptance and four scope controls as expected red before repair. Direct Git-blob comparison, normative dependency closure, safe external output, complete Doctor observations and migration state/history checks now address these findings; fresh immutable-subject verification and independent re-review remain pending. Retained the actual FAIL receipt without revising its verdict or the earlier Stage A PASS.

## 2026-09-22 — implement Stage B canonical evidence and input-scope repairs

Schema 2 validates real control identities, structured commands, exact stages and diagnostics, complete snapshots, fixture-bound migration observations and recomputed tree digests. The four historical fixtures remain unchanged; genuine contiguous-delimiter controls now accompany the correctly named generic twenty-row write control. Replaced misleading strict tests built from invalid fixtures with passing complete Git subjects, precise CLI corruptions and six guard-removal checks. A bounded independent analyst found five additional raw-evidence contradictions; all now have targeted regressions. Current Python 3.14 development discovery passed 278 methods, while exact-subject verification and the accountable Stage B Reviewer gate follow the scoped commit. This is implementation evidence, not release or Architect acceptance; R1–R9 remain live until their independent closure gates.

## 2026-09-21 — resume Stage B after independently accepted baseline

Stage A independently passed packet `4adf22dfae3eff04ec3fe62e3f6f0af50312a9e2` against lessons baseline `47cf2b29fb31d66e9fda56c822d12b4f9c7d0e70`; retained Reviewer receipts and stage register identify the exact evidence. Correct the stale dashboard after the September 17 interruption: R1–R9 remain open, while Stage B acceptance repairs may proceed. The isolated Python 3.9.25 baseline run passed the same 223 discovery tests before interruption; final candidate runtime verification remains required.

## 2026-09-17 — begin release-readiness closure after lessons subject

Created an isolated `release/readiness-20260916` worktree from the lessons
subject and retained a local recovery bundle plus a mechanically enumerated
input manifest. Stage A reproductions preserve the valid controls while
recording independent R1–R9 counterexamples; the release audit remains open
pending the separate Reviewer gate. Python 3.9, Windows, portable package
exercises and Architect adjudication remain unexecuted owner-facing gates.

## 2026-09-16 — narrow dashboard diagnostics and Close guidance from a project handoff

Added advisory diagnostics for repeated canonical peer headings and Last-updated fields, with physical locations and no silent date selection; focused CLI regressions cover formatting, hidden examples, lazy quotes, dated titles and legitimate nesting. Rechecked existing rules before adding one bounded Close reread, material-claim provenance, execution/hub ownership and interruption/withdrawal examples; the four-document minimum, ordered writes, append-only history and single writer remain intact. Exact-byte historical integrity remains optional and deferred; scope, verification and semantic limits are recorded in `docs/LESSONS-REVIEW.md`, and the earlier release packet does not certify this descendant or close the separate release audit.

## 2026-09-15 — freeze next-phase subject and retain independent review

Froze reviewed next-phase subject `edb8449`, retained sanitized acceptance, research and usability critic packets, and wrote the detailed evidence packet, Claude read-only review prompt, and originating-review report. The subject remains local and unactivated; evidence is a later reporting commit.

## 2026-09-15 — close usability critic findings

Scoped research writes to existing non-symlink targets under `research/`, rejected five-or-more digit IDs, accepted both inline and Markdown index links, and documented incomplete temporary files plus the cooperative-lock race boundary. Candidate tests cover the new path and wide-ID refusals.

## 2026-09-15 — close research critic findings

Aligned the companion example and proposal to four-digit IDs, made malformed IDs and provenance digests fail closed, required resolvable index links and distinct supersession targets, and added a cooperative lock around expected-hash writes. The candidate suite now includes these counterexamples; remaining private-source and prompt-injection guarantees are documented conventions rather than content execution.

## 2026-09-15 — require source version or content hash in companion records

The staged research Doctor now requires each source record to carry a nonempty version or content hash alongside URL, access date, exact passage and status, so changed-source limitations remain explicit. Candidate tests and the conflicting-evidence example cover the provenance field.

## 2026-09-15 — stage bounded next-phase companion research skill

Added the isolated `project-research-protocol` candidate under `staging/` with stable source/claim IDs, index retrieval, provenance checks, correction/supersession guidance, prompt-injection boundaries, and write-time expected-hash protection. Added five executable candidate tests and documented the small Bootstrap/Brief/Close hooks; the candidate remains uninstalled and owner-gated durability choices stay open.

## 2026-09-14 — correction: final manifest packet count

The final manifest now covers **50 reviewed inputs** and **23 retained evidence files**, including the canonical runner, plan, acceptance packets, aggregator negative-control packet and refreshed critics. The earlier 46-input count describes the pre-runner intermediate manifest and remains historical.

## 2026-09-14 — correction: canonical acceptance runner kills both semantic mutants

Replaced the direct Doctor and migration mutant probes with `tests/run_acceptance.py`, which executes the frozen four-case manifest against the real command-line tools and sends the structured child result through `validate_acceptance.py`. The unmutated runtime is accepted; the Doctor list-boundary mutant produces an unexpected wiring PASS and the migration newline-join mutant changes the opaque inventory, so both top-level commands exit nonzero and the validator rejects them. Retained machine-readable control and mutant packets under `tests/fixtures/hardening-2026-09-12/final/acceptance-*.json` include source commit, runtime hashes, commands, exits, stdout, stderr, targeted cases and validator results.

## 2026-09-14 — correction: final count, module and manifest scope

The final local suite now runs **198 tests** with zero failures, errors, skips or expected-failure markers. The baseline comparison covers **five** bounded regression modules, and the final hash manifest covers 46 reviewed inputs; earlier 193-test/41-input and four-module wording remains historical intermediate evidence and is superseded by this correction.

## 2026-09-14 — correction: duplicate September 14 repair entry retained as history

The earlier `repair mixed-list visibility, physical opaque delimiters and acceptance gates` entry appears twice in this append-only file because the correction was carried forward during the evidence close. Both historical copies remain byte-preserved; the first occurrence is the canonical summary, and this entry makes the duplication explicit for future reviewers.

## 2026-09-14 — correction: canonical acceptance green control adds one test

The frozen manifest adapter now has an executable canonical-path green control. Final discovery and the explicit regression runner each execute **194 tests**, with zero failures, errors, skips or expected-failure markers; prior 193-test outputs remain retained as intermediate evidence.

## 2026-09-14 — correction: final critic controls and gate schema

The fresh Doctor critic reran the corrected positive fixtures as PASS/PASS/PASS with exit 0, and the migration critic reran split/contiguous and hidden-ledger refusal controls against the current hashes. The acceptance validator now requires a nonempty expected case set, typed discovery count and explicit expected-failure list; its new fault injections reject omitted fields and empty manifests. Final critic packets are retained under `tests/fixtures/hardening-2026-09-12/final/`.

## 2026-09-14 — correction: final counts and reviewer hash boundary

The repaired tree contains 193 discovered tests with zero failures, errors, skips or expected failures, and 33 tracked Python files compile successfully. Earlier September 12 references to 177 tests and 28 Python files remain historical intermediate evidence. The final hash manifest covers 41 reviewed runtime, test, oracle, fixture, template, skill and instruction inputs and excludes itself; the current-hash critic packets supersede the earlier pre-repair summaries.

## 2026-09-14 — repair mixed-list visibility, physical opaque delimiters and acceptance gates

Implementation commit `bf848b27627661bf8429821c81fab7ba24eda40a` repairs the two remaining Doctor false-PASS families: a bullet-to-ordered transition now closes the prior list before the next marker, and an empty list item followed by a blank no longer absorbs top-level indented code. The same commit makes CDATA and processing-instruction terminators contiguous physical delimiters, keeps split fragments opaque, preserves bounded declaration handling, and refuses hidden ledger targets before journal creation. The corrected opaque tests cover hidden headings/findings, refusal without mutation, contiguous positive controls, incomplete EOF and declaration behavior.

The acceptance bundle now compares the identical focused tests against immutable `edccbc2b552fd5de0f2449930fdff7e9854e3ff4` and the repaired tree, freezes exact fixture bytes and hand-authored expectations, records the CommonMark development oracle metadata, and adds a fail-closed result validator with fault-injection tests. The baseline has 52 methods with 21 nominated behavioral failures and one explicitly expected reconciliation error; the repaired tree has 52 methods with zero failures, errors or skips. Historical September 11 evidence remains unchanged; this entry corrects the prior September 12 completion claim and opens the register closure recorded below.

## 2026-09-12 — correction: migration evidence reflects the final boundary review

The retained migration-builder README now records the final seven focused opaque-boundary tests, 77 migration/semantic tests together, 177 total methods, and the post-review `docs-migrate.py` hash. This corrects its intermediate four-test/174-test/hash description without changing historical evidence files.

## 2026-09-12 — correction: final suite count is 177 methods

The final hardening suite includes the split-terminator regression added after independent migration review. The recorded final count is 177 methods with zero skips for both unittest discovery and the explicit regression runner; the earlier 176-method sentence in this day's entry is superseded by this correction.

## 2026-09-12 — final hardening closes nested-fence and opaque-migration leaks

Reproduced the two P2 regressions from `edccbc2`: Doctor now resolves multiple same-line list containers before fence classification and keeps marker-line indented code hidden; migration now treats CDATA, declarations and processing instructions as opaque records through complete, incomplete and split terminators, so hidden examples cannot become live rows or ledger write targets. Added the final acceptance matrix, red/green reproductions, CLI regressions and an exact CDATA status/ledger refusal check. Standard discovery now passes 176 methods with zero skips; the isolated 42-method baseline comparison remains 74 failures at `328105f` versus zero on the repaired runtime. Two independent final critics completed bounded held-out reviews on the final runtime hashes with no confirmed in-scope findings. Publication and protected-ref changes remain owner decisions.

## 2026-09-11 — close the remaining hardening with retained independent evidence

Implementation commit `80fb78687ed8408b7d4d230bb2632c191ba2994b` repairs the eight continuation requirements and the two containment defects caught during this repair. Standard discovery passes 169 tests with no skips; the same 41 new test methods produce 72 assertion/subtest failures, zero errors and zero skips on `328105f`, and pass on the repaired code. Completed independent reviews cover the exact final Doctor, migration and shared-discovery hashes, including the 1,098-wrapper/15-CLI Doctor checks, 11-case selection/replay matrix and 13 actual HTML write/hidden-target probes. These are bounded fixtures, not a population regression claim.

Close LG-0022–LG-0031 using the committed implementation, retained tests and observed outputs: write terminal archive rows, verify every cell, remove live rows, then derive STATUS from zero live repair findings. The four-document installation has separate required AGENTS wiring and one observed two-context Install → Bootstrap/change/Close exercise; snapshots establish final bytes and the write order remains agent-reported. `HARDENING-REVIEW.md` and `tests/fixtures/hardening-2026-09-11/verification.json` record the acceptance commands and limits. D-0005 remains deferred; publication, release refs and other projects remain outside this local completion.

## 2026-09-11 — review finds an HTML comment escape in the new example boundary

Independent migration review found that the newly introduced paired-tag counter treats a closing tag inside an HTML comment as a real boundary, exposing the following example table as live input. Track the repair as LG-0031; its affected pre-fix state is this session's intermediate implementation, not the starting commit. The Doctor ordered-sibling repair now passes both independently reproduced CLI cases and the critic's full 1,098-wrapper visibility comparison; those are bounded parser checks, not a conformance or population claim. Two fresh agent contexts completed Install then Bootstrap/change/Close, with before/after artifacts, prompts and condensed reports retained under `tests/fixtures/install-observation`; primary independently verified the final output, preserved historical entry and unchanged DECISIONS. Write order remains agent-reported rather than timing-traced.

## 2026-09-11 — independent review extends the nested-list repair

The first integrated run passes 161 tests with no skips. That result is not closure: an independent critic's 1,098-wrapper parser comparison found an ordered-list sibling indentation variant absent from the authored cases. Primary reproduced both full CLI failures: `1. Outer` followed by a two-space-indented `2. Inner` exposes a four-space code block as wiring and hides a seven-space live block. Track this as LG-0030 until repaired and independently rechecked. The fresh-context Install observation creates exactly four documentation files plus AGENTS and exits Doctor 0; the separate subsequent-session observation remains in progress. LG-0022–LG-0029 remain open or verifying until final code review, evidence and durable commits are complete.

## 2026-09-11 — reopen remaining hardening and correct the population-evidence claim

Bootstrap verified the active Codex symlink resolves to this checkout at `328105fcbeada838284096bb883efb44907570a9` on the authorized repair branch. The current review owns eight bounded requirements, LG-0022–LG-0029: nested-list visibility, marker-line code, duplicate semantic columns, formatted state, HTML examples, register discovery, minimal-install evidence, and retained-evidence accuracy. Primary alone writes these registers; implementation agents own disjoint source/test areas. The explicit continuation request supplies the current focus despite the preceding dashboard's readiness claim. D-0005 remains deferred.

Correction to “four defects from the second independent review, closed with regressions”: the detailed 28-register comparison manifest, script revision, fingerprints and normalized outputs were not retained in the inspected tracked repository. Its zero-differing-lines result is an unverified historical report, not current acceptance evidence; even a retained dated sample would not establish “regresses no real project.” No unrelated private projects are being rescanned. Local probes confirm migration loses second state/gate aliases, proposes formatted BLOCKED as OPEN, treats a preformatted example as live, and selects a partial docs register over a complete root. Installation/template and parser regressions are being independently exercised. Closure requires retained reproductions, exact-state review and final checks.

## 2026-09-11 — four defects from the second independent review, closed with regressions

An independent reviewer reported four P2 defects at `88b90b4`; all four were reproduced here before any was acted on, so none is recorded on the reviewer's word alone. **Migration** recognised a STATUS table header only when every column label was on a whitelist, so one ordinary extra column (`Severity`) disabled extraction of the `Status` and `Blocked on` columns beside it: an explicitly BLOCKED, explicitly gated row became an ungated OPEN ledger row, and the header row itself became a finding. Headers are now recognised the way GFM defines them — a row whose next visible line is a delimiter row of equal width — and the recognised columns are read by name, so an unfamiliar column is ignored rather than fatal; the template's own `Item · Blocked by · Unblocks when` layout is now read correctly, and header and delimiter rows never become records. Migration also chose `<project>/docs` whenever that directory merely existed, so a valid root-level register beside an empty `docs/` was unreachable; discovery now mirrors Doctor's `find_register`. **Doctor** treated a CommonMark indented code block as live text, so an example of the wiring block indented four spaces was certified as active instructions; `visible_lines()` now consumes indented code using the real rule — code only where no paragraph is in progress, with the four columns measured from the container's content baseline, so nested bullets and indented continuation paragraphs stay visible. Doctor also accepted any separator-shaped line as a table delimiter, so a ten-column ledger header over `|---|---|` passed as a valid table; the delimiter's cell count must now equal the header's, as GFM requires.

A fifth case was found while attacking the repair and fixed with it: a table whose column labels are *all* unrecognised still mapped its rows, so a cell reading `BLOCKED` in a bespoke layout landed as an OPEN row. Such a row is now left unresolved for a human, which is the reviewer's "leave ambiguous tables unresolved" applied to the case the first repair missed. The two coverage gaps the reviewer named are closed too: the git-dependent checks and a fresh install built from `templates/` now have executable tests rather than none.

Evidence: 128 tests pass (89 before this round), and the new regressions were confirmed to fail against the `88b90b4` scripts and pass against these. Doctor run read-only over all 28 qualifying registers on this machine, old script versus new, produced **zero differing check lines** — the indented-code rule regresses no real project. Doctor exits 0 on this repository. Migration preview over a real register left it byte-identical.

## 2026-09-11 — the installation contract said three different things

The README called a roadmap, a glossary, a brand sheet and a spec template "optional scaffolding seeded only when a project needs it", while its own Files section listed `ROADMAP.md` and `GLOSSARY.md` among the starter files copied into every new project, and Install's file tree implied the same. The code settles it: `docs-doctor.py` requires exactly `STATUS.md`, `CHANGELOG.md` and `DECISIONS.md` to see a register at all, reads `README.md` for the install footer, and references `ROADMAP.md`, `GLOSSARY.md` and `SPEC_TEMPLATE.md` zero times. The minimal installation — four files — is now stated in Install and matched in the README (D-0017). This skill's own register has run on those four since install day, which is the working proof.

## 2026-09-10 — verified hardening ready for local human review

Implementation commit `16a1bb9ebcaa3cebd5dd624b748aaf321f3eec28` resolves the twelve confirmed cross-check requirements and four additional migration review findings, including the indented-table variant. Generic discovery passes 89 tests (43 Doctor, 37 migration, 9 authored lifecycle replays); the repository Doctor exits 0 with no warnings/failures, the skill validator passes, and independent code/evidence review reports no confirmed blockers. Close LG-0001–LG-0021 with the committed implementation and per-row checks, copy each terminal row to the archive, verify every cell before removing the live row, then derive STATUS from zero live repair findings; D-0005 compaction remains deferred, and the report distinguishes deterministic execution from the one-agent/four-case forward exercise and manual semantic checks.

## 2026-09-10 — independent verification extends the migration repair

The first integrated run executes 78 discoverable tests, including a real twenty-finding write; the eleven scenario names now point to executable methods and are not counted as tests themselves. Independent code review reproduced migration omissions after fenced HTML, writes into hidden tables, a malformed-journal traceback and loss of structured blocker information; these are LG-0018–LG-0021 and remain open for repair. A separate four-case skill-use exercise preserves partial/unanswered gates, recovers the exact reserved decisions and stops without edits on a semantic conflict; retained before/after observations are separate from authored lifecycle replay and do not establish an agent compliance rate.

## 2026-09-10 — reopen hardening after adversarial cross-check

The clean syntax check at `5621f03` did not establish lifecycle completeness: generic discovery runs zero tests, and the previous runner executes ten Doctor cases and one migration preview while merely checking eleven scenario descriptions. The twelve confirmed requirements map as follows: C1→LG-0008, C2→LG-0009, C3→LG-0007, C4→LG-0010, C5→LG-0011, C6→LG-0006, C7→LG-0012, C8→LG-0013, C9→LG-0014, C10→LG-0015, C11→LG-0016, C12→LG-0017; C-numbers follow the latest cross-check's ordered list. Bootstrap confirms the existing installation at `docs/`; this session repairs it in place, with one register writer, repository-contained fixtures, and no remote changes.

## 2026-09-10 — reconciled review findings into the live ledger

Before migration, STATUS carried 7 live implementation findings; after migration, `docs/LEDGER.md` carries 7 live rows (`LG-0001`–`LG-0007`). The source→ledger mapping is F1/F2→LG-0001, F3→LG-0002, F4→LG-0003, F5→LG-0004, F6→LG-0005, F7→LG-0006, and F8→LG-0007; no item required manual review.

## 2026-09-10 — correction: public regression evidence boundary

The earlier candidate entry cited 67 private fixtures and a 26-root sweep as verification. Those figures remain historical review notes; acceptance now rests on the tracked anonymised Python runner and scenario manifest in `tests/`, while private review paths are excluded from public claims.

## 2026-09-10 — harden ledger lifecycle, Brief provenance, and Doctor diagnostics

Implemented the confirmed follow-up fixes for fence/footer parsing, ledger dates and schema invariants, archive ID collisions, and exact decision citations. The remaining documentation and regression fixtures are being added in this close.

# CHANGELOG

## 2026-09-15 — scope Git cleanliness to reviewed runtime inputs

Canonical provenance ignores unrelated untracked task notes outside the
declared `scripts/`, `templates/` and `tests/` runtime scope, while any change
inside that scope still makes provenance unverified and is independently caught
by content hashes. This keeps the clean-subject gate tied to reviewed inputs.

## 2026-09-15 — close independent provenance and input-binding counterexamples

The strict acceptance validator now independently rehashes every declared
harness, validator, manifest and fixture input, requires a clean verified
runtime Git identity, and rejects `verified: false` or arbitrary 40-hex source
commit values. Focused counterexamples cover unverified provenance, arbitrary
commit substitution and incomplete input manifests; the disposable mutant
harness now gives clean controls their own Git commit.

## 2026-09-15 — close independent provenance and input-binding counterexamples

The strict acceptance validator now independently rehashes every declared
harness, validator, manifest and fixture input, requires a clean verified
runtime Git identity, and rejects `verified: false` or arbitrary 40-hex source
commit values. Focused counterexamples cover unverified provenance, arbitrary
commit substitution and incomplete input manifests; the disposable mutant
harness now gives clean controls their own Git commit.

## 2026-09-15 — independently recompute canonical runtime hashes

The acceptance validator now recomputes the three runtime script hashes from
the declared `runtime_root` for strict canonical results, and requires a
40-character source commit plus derived runtime-tree hash. Symbolic hashes in
legacy unit-only controls remain supported; canonical bundles cannot pass by
reporting a self-generated digest map.

## 2026-09-14 — harden acceptance result truth, protected-state and provenance gates

The canonical acceptance runner now distinguishes harness/setup failure from
expected semantic refusal: failed child state carries a diagnostic and a
nonzero process exit, while a valid four-case result remains aggregate-successful.
Each case records stage exits/diagnostics, exact protected-register hashes,
unauthorized-file observations and an executable positive control. The frozen
manifest is verified before execution; runtime hashes include `register_paths.py`,
the runner/validator and every declared fixture. Acceptance gate tests now cover
false-green failure state and deliberate mutation-before-refusal. A foreign
prefixed CHANGELOG citation is informational when its series is absent locally,
while missing unprefixed local D-series citations still warn.

*Append-only history of what happened and why. Reverse chronological — newest on top. Never edit past entries; append corrections instead. Entry and correction formats: see the templates' README.md.*

---

## 2026-09-14 — bind census appendix to final aggregate run

Corrected the appendix's anonymized run token after the final script/privacy rerun; the method, population, and classifications are unchanged.

## 2026-09-14 — research report adds operational storage guidance

Added a primary research-data-management citation and marked the exact 3-2-1 attribution unverified because a reliable primary passage was not established during the bounded fetches. No protocol behavior or owner decision changed.

## 2026-09-14 — research settling criteria made explicit

Added pre-collection evidence tests for each research question so that unresolved portability, causation, owner acceptance, and lifecycle claims remain visible rather than being inferred from the census. The follow-up is documentation-only and leaves the candidate behavior uninstalled.

## 2026-09-14 — bounded durability census and next-phase research design

The read-only depth-six census separates filename roots from marker-positive installations, deduplicates physical aliases, and classifies Git history, register-file state, remotes, upstreams, generated copies, and machine-wide backup/sync indicators without storing identifying paths or URLs. The research report, proposal table, owner-gated Brief, and optional Markdown-first companion-skill design are under `docs/research/` and `.research-report.md`; Karpathy's `autoresearch` README was verified as an observed workflow, while attribution of this protocol remains unverified.

## 2026-09-06 — v0.4.0 candidate: LEDGER, an item-keyed tracker for findings lists that outgrow STATUS (local branch, for review)

Designed from a measured 1,108-row tracker that had grown one sheet per audit wave: 28 header shapes across 79 sheets, 142 free-text status strings (129 distinct), 321 of 451 closes unverifiable as written, 451 closed rows interleaved with 507 open ones, five side trackers and a 178-line Known-issues section in STATUS. Each of those six mechanisms has a named answer. `templates/LEDGER.md` (60 lines): one fixed ten-column table — ID · P · Status · Date · Title · Tags · Closes-when · Blocked-on · Touches · Evidence — with mint-once `LG-NNNN` ids, a six-token status enum, a Tags vocabulary declared once in the banner (at most twelve), Closes-when written when the row opens, three-part closing evidence enforced by Close, and terminal rows moved to `LEDGER-ARCHIVE.md` in the same edit so the live file is the open set; findings that are terminal at birth go to CHANGELOG, sub-items cite `from LG-NNNN`, and grouping is a grep, never a sorted copy. Opt-in at Install question 8 when a project carries about fifteen live items (tested: 23 of 25 roots sit at 0–10, the two above at 28 and 52); Bootstrap step 5 reads live rows only and never the archive; Close step 2 edits rows before the STATUS rewrite; Brief reads and edits a row its question cites; DECISIONS gains the `extends D-XXXX` title form. Doctor 1.4.0 adds ten checks (`ledger-header` … `ledger-live-size`, `decisions-tags`) that read only the live file and print one `SKIP ledger` line where no ledger exists; exit codes unchanged. Verified by three adversarial rounds on the design (22, then 5, then 47 findings closed), a fourth on the integration, 67 ledger fixtures, and the full regression set (both earlier suites, the reviewer's 11, the original 36, the 26-root sweep unchanged at 2 / 7 / 17 with one SKIP line each). Not merged, not pushed: the owner reads `git diff main..v0.4.0` first.

## 2026-09-06 — v0.3.0 released: Doctor 1.3.0 and Brief hardened after an independent review

A second model reviewed the v0.3.0 branch read-only and returned eight P1 and nine P2 findings; every one was reproduced before it was acted on, and three were re-graded (the "real-name" hits were the copyright holder and the model trailer; the 26-root exit-1 sweep was WARN-by-contract; the "stacked lines left in place" is the compaction decision D-0005). Brief: the recording order is now stated as CHANGELOG → DECISIONS → STATUS with its reason (D-0011); Reasoning carries only reasons the owner gave, with a liveness question over every presented alternative and "presented, not chosen — agent's assessment" for the rest (D-0012); one-option notices are ordinary work, never "unless you object"; declined and revisit markers are durable; the worked example moves its settled item to the preamble and no longer attributes reasons to the owner. Doctor 1.3.0: quoted, fenced and commented text is dropped before any wiring search; clauses count only inside the block's own span; the block's docs path is checked against the register (`wiring-path`); a negated or mid-sentence footer is not a footer; CommonMark's indented headings count; a heading carrying a real id is never template residue; ids at `####` or deeper are a WARN; STATUS checks read visible lines only, an inline comment no longer hides its line; a future STATUS date is a WARN; `status-template-residue` catches the shipped placeholder rows; `changelog-decision-refs` catches a brief that died between CHANGELOG and DECISIONS; exit codes are now 0 / 1 WARN-only / 2 FAIL / 3 cannot run (D-0013). Templates and README: placeholder rows say to delete themselves, Install replaces every date and names which rows to remove, SPEC's per-spec log says oldest-first, the public README says five modes and softens "the block was the difference" to the instruction being the difference, the precedence clause names its three properties. Verified by three fresh reviewers, 46 new fixtures plus the earlier 36 and the reviewer's 11, and a 26-root sweep (2 exit 0, 7 exit 1, 17 exit 2). Merged to `main` and tagged.

## 2026-09-06 — correction to "v0.2.0, first public release"

The earlier entry said no commit message or file names a project, product or person. Re-read now: the copyright holder's name is in LICENSE and the model's name is in the commit co-author trailers, both intended. The claim that holds, on every tracked file and commit through this release, is that no project, product, client or third person is named.

## 2026-09-04 — v0.3.0 candidate: Doctor and Brief modes, on their own branch for review

Mode 4, Doctor: `scripts/docs-doctor.py`, a standard-library, read-only health check that runs the Bootstrap red flags as a script — wiring block present and carrying the three current clauses, STATUS size and longest line, stacked session records, last-updated lag, dormancy, heading format, duplicate and mis-levelled decision ids, template residue, brand placeholders, nested and sibling registers, and STATUS churn where git exists. Built against the 25-root census and a 36-fixture break suite across two adversarial rounds; the first round found a hang on wide ids and a false FAIL on the one mature installation, both closed and confirmed by re-running, not by reading the diff. Mode 5, Brief: the ritual that turns STATUS's open questions into DECISIONS entries — fixed presentation shape, options that must trace to a source, an explicit-pick rule so silence is never recorded as consent, one CHANGELOG entry per brief, offered at Close only when something is askable. Templates: STATUS's open-questions section gains a line shape with a proposed option and a since-date; README names the third ritual and the brief entry format. A worked brief ships as `docs/BRIEF-EXAMPLE.md`. The skill's own docs README gained the install footer so Doctor passes on this repository with exit 0. A sixth wired project found by Doctor with a stale July block was re-synced.

## 2026-09-04 — v0.2.0, first public release

README rewritten to lead with the design property and the population evidence; `docs/EVIDENCE.md` added with the audit's anonymised findings; repository description and topics set; visibility flipped to public. Every change on the audit branch is squashed into two clean commits on `main` so that no commit message or file names a project, product or person. Tag `v0.1.0` remains the pre-audit baseline.

## 2026-09-04 — trigger narrowed: three filenames are no longer the signature

The skill fired on any folder holding STATUS.md, CHANGELOG.md and DECISIONS.md. On this machine nine of the twenty-five matching folders had never run Install — registers that predate the skill, or that other tooling scaffolded in a different dialect — and elsewhere a Keep-a-Changelog file plus an ADR folder would produce the same three names. The signature is now the three files **and** either the wiring block in CLAUDE.md/AGENTS.md or the install footer in the docs README. Bootstrap on a non-installation now offers Install (wire and reconcile) instead of adopting a register it did not create.

## 2026-09-04 — five owner decisions taken; the four affected registers on this machine updated

The owner answered the five open questions from the audit (release, writer instruction, compaction, id collisions, provenance). Recorded as D-0006 to D-0008 below; two were operational and needed no decision entry. Outside this repository: the two live prompt templates in the largest project now say "replace STATUS line 1" instead of "prepend", and the two pre-skill registers carry a provenance line saying they are not installations.

## 2026-09-03 — templates: STATUS cut to 37 lines with Next and Open-questions sections; DECISIONS order fixed; README trimmed and given a correction form

STATUS template dropped five horizontal rules and the note-plus-table duplication in Blocked (35 of 44 lines were chrome; a one-row fill exceeded the protocol's own 40-line rule) and gained `## Next` and `## Open questions (owner)`, which 6 and 7 of 24 installs had invented independently under other names. DECISIONS template now states entry order (bottom, oldest first; installs had split 14/7) and forbids reusing a number with a qualifier. README template: CHANGELOG corrections address by summary or token instead of date (the date form was used 0 times across 25 roots and is ambiguous for 90–98% of entries); a DECISIONS correction form added (the protocol mandated corrections in three places and formatted none); the Commits and External-comms subsections deleted (16 of 16 installs that kept the section had deleted both). Report recs 3, 5, 7.

## 2026-09-03 — SKILL.md: how STATUS is edited, precedence, a bounded bootstrap read, red flags that discriminate, single-writer assumption, nested-register question

The Step-2 wiring block now says STATUS is rewritten rather than appended and that the three design properties (CHANGELOG first, STATUS rewritten, registers append-only) are not overridable by project convention — measured across every install, the presence and wording of that block predicted STATUS churn (0.67–0.83 with it, 0.01–0.16 without or with a "top line" variant). Bootstrap step 1 reads STATUS in full only under ~60 lines (the full read cost ~153,000 tokens on the largest file). Red flags: threshold moved to ~60 lines (the literal 40 fired on 23 of 25 roots and on the template itself), a max-line signal added (one STATUS carried a 36 KB single line), stacked session records named, dormancy-on-return added. Mode 3: step 2 says rewrite; step 3 says corrections take a new number; the compaction trigger is size-based instead of quarterly (quarterly had fired once in 25 projects). Operating principles gain "one writer at a time". Install interview gains the BRAND value gate (8 of 14 BRAND files were never touched) and a nested-register question. Report recs 1, 2, 3, 4 (trigger only), 6, 8.

## 2026-09-03 — baseline tagged v0.1.0; work branch opened; an older distribution bundle's installer guarded

Tagged the pre-audit state as `v0.1.0` (first tag; the repo had two commits and no version). Opened `audit-2026-09-02` so `main` stays at the baseline until reviewed. Patched the installer of a separate, older distribution bundle (outside this repository) to refuse a symlink or git-clone target and to back up rather than delete — its default mode would have replaced the live skill directory with a July snapshot, and its other mode would have deleted this clone.

## 2026-09-03 — initialized project documentation system

Installed the project-docs-protocol on itself at `docs/`, seeded from the 2026-09-02 audit (not approximate: the in-flight items are this session's own work). BRAND.md omitted; no brand dimension. SPEC_TEMPLATE.md omitted; not spec-driven. GLOSSARY and ROADMAP omitted for now — the protocol's own terms are defined in SKILL.md and its roadmap is the audit report's ranked list.
## 2026-09-14 — repair mixed-list visibility, physical opaque delimiters and acceptance gates

Implementation commit `bf848b27627661bf8429821c81fab7ba24eda40a` repairs the two remaining Doctor false-PASS families: a bullet-to-ordered transition now closes the prior list before the next marker, and an empty list item followed by a blank no longer absorbs top-level indented code. The same commit makes CDATA and processing-instruction terminators contiguous physical delimiters, keeps split fragments opaque, preserves bounded declaration handling, and refuses hidden ledger targets before journal creation. The corrected opaque tests cover hidden headings/findings, refusal without mutation, contiguous positive controls, incomplete EOF and declaration behavior.

The acceptance bundle now compares the identical focused tests against immutable `edccbc2b552fd5de0f2449930fdff7e9854e3ff4` and the repaired tree, freezes exact fixture bytes and hand-authored expectations, records the CommonMark development oracle metadata, and adds a fail-closed result validator with fault-injection tests. The baseline has 52 methods with 21 nominated behavioral failures and one explicitly expected reconciliation error; the repaired tree has 52 methods with zero failures, errors or skips. Historical September 11 evidence remains unchanged; this entry corrects the prior September 12 completion claim and opens the register closure recorded below.
## 2026-09-15 — retain fresh-context candidate exercise

Recorded a disposable-process exercise for the staged companion: optional research present and absent, Bootstrap/Close ordering traces, and an intervening-edit stale-write rejection with unchanged bytes. The observation is explicitly bounded and does not claim autonomous-agent compliance or replace the lifecycle replay evidence.
## 2026-09-15 — establish Architect stage contract and close boundary findings

Recorded the staged developer/reviewer contract and frozen acceptance matrix in
`docs/architect/`, added fail-closed canonical evidence and unauthorized-file
checks, enforced the census device boundary and empty-upstream parsing, and
expanded the staged research Doctor's identity, link, symlink, and lifecycle
checks. The optional Architect protocol and project skill registry remain in
their independent implementation stages.
## 2026-09-15 — complete staged Architect and registry packets for review

Added the optional `project-architect-protocol` candidate with a read-only
Doctor, exact lifecycle state, minimal example, and focused tests. Integrated
the optional project skill registry into Install, Bootstrap, templates, and
the repository inventory. Both candidates remain staged and owner-gated.
## 2026-09-15 — independent review passes final implementation packet

The independent Reviewer reproduced the implementation, evidence, registry,
Architect packet, and staged research checks from clean detached state. The
review returned `PASS`; the reviewed implementation is `253f967`, with evidence
packet `9b9d573` and Architect metadata alignment `2896617`. Residual risks are
recorded in the handoff packet.
## 2026-09-15 — repair Architect handoff identity and evidence scope

Rebased the handoff on immutable behavior subject `5af546cd0e91a71161738575a1eb1c4be404c2ca`, retained the independent Reviewer packet under `docs/architect/reviews/`, and narrowed the machine manifest to a complete executable-input scope. The canonical acceptance gate now requires trusted strict invocation and its independently derived hash set. Companion names are `research-protocol` and `architect-protocol`; the registry records lifecycle, evidence, reviewer, and missing-capability behavior.
## 2026-09-15 — correct final Doctor count and retained handoff scope

The Git-enabled Docs Doctor reports 38 checks (33 pass, 5 info, zero warn/fail); the no-Git diagnostic reports 37 checks with one skipped Git check. The final handoff now names both results explicitly and binds the retained review packet to behavior subject `b07dc302da6088ff88dc92485c9cbc15325f18b6`.
## 2026-09-15 — correction: freeze the final Architect packet scope and identity

The final machine manifest is explicitly bounded to **47 reviewed inputs** and
**0 evidence files**; older claims of 50 reviewed inputs and 23 retained
evidence files are historical and superseded. The retained handoff and review
packet now bind the behavior subject and evidence-generation commit to the full
40-hex commit `2c08856d5f558ffc3d993912ab73c95cb9aab22d`. The manifest digest
in `docs/architect/reviews/REVIEW-PASS.json` is recomputed from the current
`tests/fixtures/hardening-2026-09-12/final/hashes.json`.

## 2026-09-15 — correction: align retained verification counts

The final verification rerun discovers 211 repository tests, 22 focused
acceptance/manifest/mutant tests, 11 research tests, and 8 Architect tests.
The STATUS scope note is compacted below the Doctor size threshold so the
Git-enabled Doctor reports 38 checks (33 pass, 5 info, 0 warn/fail) and the
no-Git diagnostic reports 37 checks (32 pass, 4 info, 1 skipped Git check).
