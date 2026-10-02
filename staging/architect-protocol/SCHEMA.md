# Architect packet schema 2

Read this when creating or changing a production packet. All JSON uses UTF-8,
unique keys, finite values and the exact fields below. Unknown fields fail.
SHA256 values are 64 lowercase hex characters; Git subjects are resolvable full
40-character commits. A reference is `{ "path": "project/relative/file",
"sha256": "..." }`. Paths use `/`, without dot segments, glob syntax, drive
prefixes, backslashes or `.git` components. They are relative to the project
root, including when `--packet-dir 'review packet'` selects another directory.
Artifacts must be ordinary single-link files beneath ordinary directories.

`PLAN.md`, `STAGES.md` and `ACCEPTANCE-MATRIX.md` accompany `STATE.json` in the
packet directory. Markdown explains scope and historical observations; JSON
alone selects the current lifecycle and effective review attempts. A packet
must not contain its own `STATUS.md`. The project dashboard remains authoritative
for current project work. Doctor cannot verify register write order or intent.

## STATE.json

Exact fields: `schema: 2`, `protocol: "architect-protocol"`, `mode`, `stage`,
`active_gate`, `subject_commit`, `subject_label`, `roles`, `contract`,
`input_manifest`, `evidence_manifest`, `stages`, `open_findings`, `handoff`,
`handoff_status`, `external_review`, `architect_acceptance`.

`roles` contains distinct nonempty `developer`, `reviewer`, `architect` task
identities. Labels are descriptive; `subject_commit` alone identifies behavior.
`open_findings` lists unique IDs from the contract. Only in-scope findings gate
this packet; unrelated project LEDGER rows do not imply a release failure.

| Lifecycle | Required interpretation |
| --- | --- |
| `scope` | Unfrozen: null subject, active gate and artifact references; empty stages. Open work is not accepted. |
| `baseline` | Immutable baseline and its frozen contract; active PENDING attempt has the same subject. Evidence may still be null. |
| `implement` | Last known immutable subject, contract and earlier reviews retained; PENDING current attempt. Working changes are expected; no acceptance claim. |
| `review` | Exact subject, frozen contract, complete inputs/evidence, clean reporting descendant, PENDING active attempt with current subject. |
| `repair` | Retained FAIL or FAIL — verification incomplete for the active subject. Working changes permitted; no acceptance claim. |
| `handoff` | Every gate effectively PASS, no open scoped finding, exact inputs/evidence and HANDOFF, with awaiting or accepted status below. |

Outside handoff, handoff and external acceptance fields are null. Supplied
optional artifact references still require valid reference shape. Intermediate
states do not claim current evidence verification unless in `review`.

`mode` is `production` or `structural-example`. Examples require the explicit
`--structural-example` CLI flag, must be unfrozen scope, and print STRUCTURAL,
never production PASS. The flag cannot validate production packets. An absent
optional packet prints SKIP. Missing required artifacts in a present packet fail.

## Frozen contract and complete inputs

The contract has `schema: 2`, `kind: "architect-contract"`,
`scope: "all-tracked-except-reporting"`, unique `stages`, `components`, `findings`,
`reporting_paths`, `evidence_checks` and an object `historical_stages`.
`findings` may be empty. Stages/components/reporting paths/checks are nonempty.
Reporting exclusions are exact project-relative file names, never directories
or prefixes. The contract itself is never reporting. Instructions, tests,
expected outcomes and acceptance contracts are behavior inputs even when
Markdown or JSON. Accountable review must inspect the proposed exclusions.
The owning register's `CHANGELOG.md`, `STATUS.md` and `DECISIONS.md` — and
`LEDGER.md` and `LEDGER-ARCHIVE.md` where adopted — are declared reporting paths,
so the docs protocol's close-as-you-go writes never change a frozen subject. A
`SKILL-REGISTRY.md` change alters which skills an agent invokes: it is a behavior
input and requires a new attempt. architect-doctor does not enforce this list;
the Reviewer checks it.

Each evidence check has exactly `id`, integer `exit`, and unique `outputs`
paths. Required output paths are unique across checks and must be declared
reporting. The input manifest has `schema: 2`, `kind: "architect-inputs"`,
`subject_commit`, `files`, `tree_sha256`. `files` maps every tracked behavior
path to `{ "mode": "100644" or "100755", "sha256": "..." }`. The aggregate is
SHA256 of sorted UTF-8 `path:mode:sha256\n` rows. No self-reference is needed:
input/evidence/STATE/review/handoff files are declared reporting paths before
freezing behavior B. Unlisted new paths, deletions and mode changes are behavior
changes. Symlink/submodule Git inputs are unsupported and refused.

Strict review/handoff compares every behavior byte/mode against B, permits only
exact reporting changes between B and HEAD, and checks all tracked current bytes
against HEAD even when index flags hide edits. Ignored and untracked files also
fail; use a clean checkout and `PYTHONDONTWRITEBYTECODE=1`. A broad cache exclusion
is not a replacement for a clean review subject. The core acceptance runner's
enumerated input manifest is a separate contract and is not reused as this scope.

## Evidence and review attempts

Evidence has `schema: 2`, `kind: "architect-evidence"`, `subject_commit`,
`contract_sha256`, `input_manifest_sha256`, `generation_commits`, `files`,
`commands`. Generation commits must resolve and be B or reporting-only
descendants. `files` maps exactly the contract's outputs to hashes. `commands`
follow the contract checks in order, with exact fields `id`, nonempty ordered
`argv` (nonempty executable, repeated and empty later arguments permitted), `cwd`, `environment` (`python`, `platform`),
integer `exit`, and ordered output references. Retain actual outputs and command
observations; inventing a successful observation is never permitted.

Complete evidence and successful outcomes are separate checks. Current strict
review/readiness and every completed PASS receipt, including earlier attempts,
must match their own frozen expected exits. Only a validated FAIL or
FAIL — verification incomplete receipt that agrees with its attempt may retain
actual integer exits that differ from those expectations. Identity, original
scope, hashes, commands, outputs and generation checks remain mandatory. This
does not permit missing artifacts or unrun-command placeholders. Select this
rule from the validated receipt verdict, never from an evidence flag or the
attempt's position. An intentionally expected nonzero exit can meet a contract;
a semantic review can FAIL even when every command met its expected exit.

STATE stages follow contract order. Each has `id`, `attempts`, `effective`.
Each attempt has `id`, `subject_commit`, `verdict`, `receipt`, `supersedes`,
`bindings`. A completed native attempt's `bindings` contains exactly `contract`,
`input_manifest`, `evidence_manifest` references. Pending attempts may use null
bindings while evidence is being prepared. A collapsed frozen historical import
uses null attempt bindings; its original bindings live in the frozen contract.
Verdicts are PENDING, PASS, FAIL or FAIL — verification incomplete. PENDING has
null receipt. Completed attempts have receipts. The first attempt supersedes
null; later attempts name the previous attempt ID. IDs are unique and `effective`
must name the last attempt. An earlier PASS never overrides a later failure.
Future gates have no attempts and null effective; past gates must effectively
PASS. A repair is an additional explicit attempt, not deletion of a failure.

Current receipts have `schema: 2`, `kind: "architect-review"`, `stage`, `attempt`,
`verdict`, `subject_commit`, `contract_sha256`, `input_manifest_sha256`,
`evidence_manifest_sha256`, `evidence_generation_commits`, `reviewer_task`,
`reviewed_at`, `supersedes`. The final current receipt binds all current artifacts
and generation commits. Earlier receipts retain their own subjects and scopes.
Every completed native receipt is checked against its own retained triple:
original contract bytes at their original path in that receipt's subject,
membership of the reviewed stage in that contract, complete original input
scope/bytes/modes/aggregate, retained outputs and original permitted generation
scope. Historical inputs need not equal today's behavior. Native artifact paths
remain stable; use distinct evidence paths for a later attempt rather than
overwriting an earlier attempt's outputs. The final native triple additionally
equals the current STATE references.
Hashes and task strings do not prove who conducted review: preserve actual task
messages and independent raw observations, and have the accountable Architect
cross-check them. A structural PASS does not grant release authority.

## Frozen historical imports

Only the contract can select compatibility, before B freezes. An import has
exactly `shape`, `receipt`, `subject_commit`, `baseline_commit`, `bindings`,
`prior_receipts`. It fixes one imported effective PASS and preserves selected
prior completed receipts. STATE cannot choose a different receipt or add attempts
to that frozen gate. Neither the active nor final gate may use compatibility.
Current review failure cannot fall back to an older schema.

Supported original shapes:

- `legacy-a`: schema 1 / independent-stage-review; `packet_commit` is the review
  subject, distinct from `baseline_behavior_commit`; original manifest hash is
  `baseline_input_manifest.sha256`.
- `legacy-b`: schema 1 / independent-stage-review, `subject_commit`, and original
  `input_manifest.sha256`; null baseline in the import.
- `legacy-c`: no schema or kind fields, `subject_commit`, and original
  `submitted_manifest_sha256`; null baseline in the import.
- `v2`: original architect-review schema, full binding fields, original attempt,
  timestamp and resolvable generation commits; null baseline. Its supersedes
  chain follows the original attempts in ordered `prior_receipts`, while STATE
  holds one collapsed imported effective attempt.

Every prior v2 receipt retains the exact supported fields, immutable subject,
Reviewer identity, digest types, timestamp and resolvable generation identities.
An original PASS may precede a FAIL and repair PASS; preserve all three receipts
unchanged and in their original supersession order. Historical validation keeps
the original contract's obligations; it does not reinterpret legacy A/B/C as
native v2 approvals or add fields absent from the actual original review.

Bindings map `input_manifest` and, when originally supplied, `contract` and
`evidence_manifest` to references. Preserve raw original digest values. A safely
relocated artifact must still match the digest inside the original receipt,
even if its transport reference and bytes are replaced together. Legacy
`acceptance_contract_hash`, if present, is mandatory; never invent one when
absent. Historical schemas and original scope remain historical: the importer
does not retrospectively claim current scope coverage or re-execute old reviews.

## Bounded preservation of declared attempts

Strict review/handoff also reads the selected STATE path in B and every commit
in B-through-HEAD reporting ancestry for the same exact contract reference.
Reporting merges are explicitly unsupported and refused. Previously declared
attempt IDs and order must remain a prefix of current history; completed attempt
subjects, verdicts, receipts, supersession and binding triples are immutable.
PENDING entries may complete with actual result/evidence without freezing their
mutable pending fields, but may not disappear. Malformed same-contract schema or
attempt fields and disappearance of STATE after declaration fail verification.
Clearly different contracts are not retroactively interpreted as this contract.

Past snapshots are inspected as history, not required to be successful handoffs:
a recorded FAIL must remain visible and may be followed by an explicit repair.
The same check applies to immutable nominated F during accepted B/F/J validation.
It cannot discover never-recorded reviews, unreachable or rewritten history,
unrelated refs or omitted history across a refrozen contract boundary. Those
limits remain accountable Reviewer/Architect duties, not automatic assurances.

## Acyclic handoff and actual Architect response

HANDOFF JSON has `schema: 2`, `kind: "architect-handoff"`, `subject_commit`,
`contract_sha256`, `input_manifest_sha256`, `evidence_manifest_sha256`,
`review_sha256`, `components`, `findings`, `report`, `residual_risks`,
`owner_decisions`. Components exactly map contract components to PASS; findings
map contract findings to CLOSED. The report reference points to human-readable
Markdown identifying B. Risks/decisions are lists, possibly empty.

Freeze behavior B → generate evidence → independent Reviewer receipt → commit
reporting packet F → external review of exact F → actual Architect response.
STATE at F uses `handoff_status: "awaiting-architect"`, with null external review
and acceptance. F does not embed its own commit ID. Send F out of band and verify
message delivery. Awaiting is not accepted and elapsed time is not approval.

A later reporting descendant J may record `handoff_status: "accepted"` with:

- `architect-reporting-review`: schema 2, `behavior_commit`, `reporting_commit`,
  `verdict: "PASS"`, `reviewer_task`, `handoff_sha256`.
- `architect-acceptance`: schema 2, `behavior_commit`, `reporting_commit`,
  `verdict: "PASS"`, exact PASS `components`, `architect_task`,
  `reporting_review_sha256`.

Both identify B and the actual earlier F, not J. Doctor verifies B→F→J,
byte bindings and fully validates F's immutable packet and artifacts through Git
blobs. Restoring valid bytes at J cannot conceal invalid evidence or stages at F.
This does not certify J's own containing commit; externally review J if needed.

## Support and limits

Python 3.9+ and Git are required for production identity validation. Safe local
artifact reads require POSIX directory descriptors, O_NOFOLLOW and O_NONBLOCK;
platforms without these fail explicitly before packet reads. No equivalent
Windows safe-read guarantee is claimed. macOS/Linux runtime matrix observations
are reported separately from definitions of hosted CI that have not run.
The helper is read-only and writes no caches when invoked with `-B`.
Trusted project-root selection is explicit; the operating system resolves that
root. This is not sandboxing against a hostile actor replacing every directory
concurrently, a signature system, a full Markdown parser or semantic verification
of source truth, owner intent, scope sufficiency or review independence.
