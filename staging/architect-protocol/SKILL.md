---
name: architect-protocol
description: Use when a project that has adopted it needs staged architectural planning with an exact subject, independent read-only review, repair cycles, and an evidence-backed handoff.
---

# architect-protocol (optional)

Use this skill for work that needs an Architect to own scope and acceptance
while a Developer implements and a separate Reviewer adjudicates each stage.
It is a project-local protocol: it does not install itself, change global
skills, push, merge, tag, or create a second STATUS. It uses the owning
register's STATUS (usually `docs/STATUS.md`), as the project docs protocol does.

## Contract

Keep the Architect packet in the owning register's `architect/` folder (usually
`docs/architect/`, selectable with the doctor's `--packet-dir`):

```text
docs/architect/PLAN.md
docs/architect/STAGES.md
docs/architect/ACCEPTANCE-MATRIX.md
docs/architect/STATE.json
```

`STATE.json` uses schema 2 and separates the six lifecycle names (`scope`,
`baseline`, `implement`, `review`, `repair`, `handoff`) from project-specific
review gates. Read [SCHEMA.md](SCHEMA.md) when authoring a packet or interpreting
Doctor output. The JSON selects the active gate and effective attempt; STAGES.md
preserves narrative and historical observations. It never replaces STATUS.
Packet artifacts are work and are logged like any work: the CHANGELOG entry
precedes any `STATE.json` stage advance, then LEDGER (when adopted) and STATUS
follow the docs protocol's order. STATUS cites the packet path, active stage and
as-of date. Handoff owner decisions also appear under STATUS "Open questions
(owner)"; with LEDGER adopted, each contract finding is an LG row the packet
cites. Every contract declares the register files as reporting paths (SCHEMA.md),
so closing as you go never changes a frozen subject.

Start unfrozen scope with null artifact references. Freeze an immutable behavior
subject before review; record labels separately. Honest pending and failed review
states remain valid intermediate work. They are not acceptance. Earlier PASS
receipts certify their original subject and scope only. Preserve failed attempts
and explicit repair supersession; never overwrite history or downgrade a current
receipt to a legacy format to get a pass.

Each completed native attempt retains its own original contract/input/evidence
reference triple and output paths. A new attempt uses new paths. Doctor validates
each against its own immutable subject and scope, then preserves declared
attempt history within the current frozen contract's B-through-HEAD ancestry.
It refuses reporting merges. This bounded check cannot recover unrecorded or
rewritten history or prove completeness across a new contract boundary; the
independent Reviewer and actual Architect must cross-check those transitions.

Retain complete actual failed-command observations in failed attempts. A validated
FAIL or verification-incomplete receipt can preserve a nonmatching exit without
pretending it succeeded. Every PASS still meets its own frozen expected exits;
all attempts retain complete identity, scope, hash and output checks. An unresolved
effective failure still blocks advancement. Missing or unrun evidence is not
covered by this rule.

For every stage, freeze the scope and subject commit, list every input and its
hash, implement in an isolated branch/worktree, and produce durable commands,
outputs, and expected results. A fresh independent reviewer checks
the exact subject and input manifest, runs positive, negative, holdout, and
mutation controls where relevant, and returns only `PASS`, `FAIL`, or
`FAIL — verification incomplete`. A child report is evidence for handoff, not
stage adjudication. Repair the finding and repeat the same stage when review
fails; never lower the acceptance bar to make an infrastructure failure pass.

At handoff, report the clean subject identity, complete evidence manifest,
reviewer verdicts, residual risks, and deferred owner decisions. Run the
read-only doctor before claiming the packet is structurally complete:

```bash
python3 -B scripts/architect-doctor.py /path/to/project
```

The doctor validates the packet only; it does not infer behavioral correctness
or approve a merge.

Use the exact all-tracked-minus-reporting scope in SCHEMA.md; account for new
files, deletions, file modes and index-hidden working edits. Select only exact
reporting paths in the frozen contract, without blanket directory exclusions.
Inputs and later evidence are separate to avoid self-reference. Use a clean
checkout with bytecode disabled for strict review; do not remove evidence
bindings merely because they are inconvenient.

A complete Reviewer packet first says **awaiting Architect**. Send the immutable
behavior and reporting commits, evidence and role identities to the actual
Architect task through authorized task messaging and verify successful delivery.
Only an actual Architect response permits recording accepted, and that response
binds the prior reporting commit. Doctor verifies these byte relationships, not
actor authenticity. A later commit does not accept itself.

The included minimal example is unfrozen and requires `--structural-example`;
its STRUCTURAL result cannot certify a final handoff. Production validation
requires Git and safe POSIX descriptor operations; unsupported capabilities are
refused. Never turn infrastructure failure or missing required evidence into
PASS. No registry entry or source passage grants activation or external-write
permission.
