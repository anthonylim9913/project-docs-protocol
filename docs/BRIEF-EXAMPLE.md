# Brief — worked example

The five items the skill's own STATUS carried on 2026-09-04 — four presented as questions in the Mode 5 shape, one already settled and said so in the preamble — then recorded. The project is the protocol skill itself; the evidence comes from a 25-project audit run two days earlier. No other project is named. The D-0006 to D-0008 shown under "The record" are a rendering in the brief's format, written to show how the losers are named and whose words each reason is in; they are not the entries as they stand in the skill's register, which differ in wording.

---

## The brief as presented

**Read:** this session had already bootstrapped, so the read went straight to the questions. STATUS "Open questions (owner)" — five items, none postponed. Blocked — empty. Deferred — one row (compaction procedure), reason still current. Last five CHANGELOG entries — the audit's SKILL and template changes landed; nothing dissolves a question. DECISIONS — a grep for each question's key terms ("publish", "prepend", "compaction", "renumber", "signature") across D-0001 to D-0005 hits once: **D-0005 already settles the compaction-procedure item**, so it goes in the preamble as settled, gets no number and no options, and the four remaining items are Q1 to Q4.

**Settled:** the compaction procedure — settled by D-0005 (chose: defer until the dry run). Not asked. Say so if you want a supersession.

**Notices (one real option, ordinary work, stated as the plan):** none.

### Q1 — Publish the skill now, after hardening, or never?

**Context.** The skill lives in a private git repository with a remote and no clones; the branch carrying the audit's changes is not merged, so `main` still holds the pre-audit text. The pre-audit trigger fires on any folder holding three filenames (STATUS, CHANGELOG, DECISIONS), which on this machine matched nine registers the skill never created — on a stranger's machine it would match a Keep-a-Changelog file plus an ADR folder (architecture decision records, a common convention with the same names). The README opens with the problem, not the design property, and there is no public evidence file. "Hardening" here means: merge the branch, tag a release, narrow the trigger, write an anonymised evidence page.

**Options** (from the STATUS "Next" row, the audit's release finding, and the repository's current state):
- *Publish now — reach first, accept shipping the pre-audit text.* Pro: the remote exists and making it public is one setting; zero further work. Con: the false-trigger risk ships to other people's machines, and the one thing that distinguishes this skill — the measurement — is not in the repository yet.
- *Publish after hardening — correctness first, accept a delay of one or two sessions.* Pro: what strangers clone is the reviewed text with the narrowed trigger and the evidence that justifies it. Con: the delay; and every later commit to `main` becomes an unpinned release to anyone who followed the clone instruction, so tagging discipline starts now.
- *Stay private — zero exposure, forgo the evidence's value.* This is the do-nothing option; it is the state the repository is in today. Pro: no maintenance obligation. Con: the audit is done and the population data is the pitch; keeping it private wastes the work, and the personal-tool framing in the README already sets expectations low.

**Recommendation.** Publish after hardening. The trigger fix alone is reason enough not to publish the current `main`; the rest of the hardening is a day's work already in flight.

**What would change the answer.** If hardening slipped past a couple of sessions, publish with a "pre-release, trigger over-fires" note rather than wait. If another project depended on a public URL today, publish now with the same note.

### Q2 — Fix the "prepend a session line to STATUS" instruction in all 25 files that carry it, or only the 2 live templates?

**Context.** In the largest project, 25 files tell the agent to *prepend* a session record to STATUS — that instruction is what grew one STATUS file to over 1,000 lines and 611 KB, because prepending turns the dashboard into a second log. Two of the 25 are reusable prompt templates that future sessions copy; the other 23 are dated one-shot prompts, register entries and audit snapshots — historical documents. "Append-only" is the protocol's rule that CHANGELOG and DECISIONS are never edited after the fact; the question is whether that rule extends to prompt files that are not registers but function as a record of what was instructed. Two terms used below: the "wiring block" is the short section the skill appends to a project's agent-instructions file so that bootstrap and close fire every session; its "precedence rule" is the sentence in that block saying the protocol's three properties (CHANGELOG first, STATUS rewritten, registers append-only) override any project convention, including an instruction in a prompt.

**Options** (from the audit's writer-instruction finding, which counted the 25 files and separated the two live ones; "fix none" is do-nothing):
- *Fix all 25 — consistency first, accept rewriting history.* Pro: no file anywhere says "prepend"; a reused old prompt cannot reintroduce the habit. Con: 23 of the edits rewrite dated documents to hide what was actually instructed — the same retroactive edit the protocol forbids in registers, applied to their inputs.
- *Fix the 2 live templates — append-only first, accept that stale one-shots still say "prepend".* Pro: stops the inflow at its only live source; touches nothing historical. Con: a session that reuses a dated prompt would still be told to prepend; the precedence rule has to be what overrides it.
- *Fix none — untouched history, accept the growth continuing.* Pro: zero edits. Con: STATUS was growing at roughly five records a day; this is the inflow the audit said to stop first.

**Recommendation.** Fix the two live templates. The precedence rule now in the wiring block already outranks a stale prompt, so the residual risk is covered; the 23 rewrites would buy nothing and cost the record.

**What would change the answer.** If a dated prompt were observed being reused *and* producing a prepend despite the precedence rule, fix that prompt too — one at a time, as observed, not all 23 pre-emptively.

### Q3 — Four decision ids resolve to more than one body: renumber, one correction entry, or leave it?

**Context.** In the largest retired register, four decision ids (the `D-NNN` addresses that other documents cite) each head more than one entry — three head two bodies, one heads four — because amendments and corrections were filed under the original number with a qualifier instead of a new number. Nothing in the register acknowledges this. An "inbound citation" is any place — a CHANGELOG line, a prompt, a status row — that refers to the id and expects one answer.

**Options** (renumbering was the repair the owner raised when the audit reported the collisions; the correction entry is the protocol's own rule in Mode 3, step 3; "leave it" is do-nothing):
- *Renumber — clean addresses, break every inbound citation.* Pro: every id resolves to exactly one body afterwards. Con: it edits an append-only register and silently invalidates every existing reference to the moved ids; the fix creates the failure it is fixing, elsewhere.
- *One correction entry — honesty first, addresses stay ambiguous but documented.* Pro: append-only, one new numbered entry naming all four collisions and stating which body governs at each address; every old citation still resolves, now with a written rule for reading it. Con: the ambiguity remains for anyone who reads the old entry without the correction.
- *Leave it — zero edits, ambiguity undocumented.* Pro: nothing changes. Con: a reader has no way to know which body the project treats as current; an ambiguity that is written down is a different thing from one that is not.

**Recommendation.** One correction entry. It is the only option that respects the register's append-only rule and fixes the reader's problem.

**What would change the answer.** If the register were being migrated to a new format anyway, renumber during the migration with a mapping table — the citations break once, deliberately, with a key.

### Q4 — Does a register that pre-dates the skill count as an installation?

**Context.** The skill's trigger fired on three filenames. Nine of the 25 matching folders on this machine never ran Install: their registers were created by hand or by other tooling before the skill's text existed, and none carries the wiring block (defined under Q2). When the skill adopted such a register it applied rules the register never agreed to, and in the largest case wrote to the wrong one of two registers in the same repository. "Installation" here means: the skill created or wired the register and is entitled to run Bootstrap and Close on it.

**Options** (the current behaviour is do-nothing; the alternative is the audit's provenance finding — no third option was ever proposed, and none is added):
- *Count it — reach first, accept wrong-register writes and rules the owner never chose.* This is what the skill does today. Pro: the skill helps on every register-shaped folder. Con: it is exactly the behaviour the audit measured as harmful.
- *Don't count it — precision first, accept that the skill offers Install on registers an owner considers already theirs.* Pro: the skill acts only where it has the wiring block or its own install footer to point to; on anything else it says so and offers Install as wire-and-reconcile. Con: an owner with a hand-made register gets an offer instead of service until they accept it once.

**Recommendation.** Don't count it. The signature becomes the three files plus the block or footer; Install on a pre-existing register means wiring and reconciling, never overwriting.

**What would change the answer.** If Install-as-reconcile turned out to be heavy in practice — more than one exchange — a lighter way for an owner to bless a hand-made register would be worth designing.

---

## The owner's answers

First reply: "Q1 after hardening. Q2 the two live templates. Q3 one correction entry. Q4 not an installation — that was never really a question; the audit answered it." Nothing on the settled item, which was not asked.

Q1, Q2 and Q3 took the recommendation without saying which alternatives were live, so the agent asked once, in one line, naming every presented alternative: "Q1 — were 'publish now' or 'stay private' live for you? Q2 — 'fix all 25' or 'fix none'? Q3 — 'renumber' or 'leave it'?" Second reply: "Q1 publish now was live — I had the visibility setting open before the audit, and the trigger finding is what stopped me; stay private never was. Q2 all 25 was live — I asked for it before I saw the count, and twenty-three of those are dated documents I don't want rewritten; fix none, never. Q3 renumbering was my first instinct; the broken citations changed my mind. Leaving it, no." Q4 needed no such question: the owner's own words say the alternative was never live.

## The record, in the brief's recording order

The order is CHANGELOG, then DECISIONS, then STATUS (Mode 5, Record). Every numbered question received an explicit pick, so none is carried as "not answered". Had the first reply stopped at Q2, Q3 and Q4 would have stayed in STATUS unchanged, received no DECISIONS entry, and appeared in the CHANGELOG line as "Q3 — not answered" and "Q4 — not answered"; the agent would then have asked, in one line, for those two numbers. Silence is not concurrence, and the recommendation is not an answer.

### 1. CHANGELOG — one entry for the brief

```
## 2026-09-04 — brief: 4 of 4 questions answered; D-0006–D-0008 logged; one settled item noted

Q1 publish → after hardening (D-0006). Q2 "prepend" instruction → the two live templates only (D-0007). Q3 colliding decision ids → one correction entry, no renumber (D-0008). Q4 pre-existing register → not an installation; default, no decision entry — the trigger narrowing is its own entry. Settled, not asked: compaction procedure stands with D-0005; its line leaves Open questions. Unlocks: merge, tag v0.2.0, publish.
```

### 2. DECISIONS — three entries, appended after D-0005 (rendered in the brief's format; see the note at the top)

```
## D-0006 — 2026-09-04 — go public after hardening, not now and not never

**Context:** The repository is private with no clones; `main` holds the pre-audit text, whose trigger fires on three filenames alone; the README leads with the problem and there is no evidence page.
**Decision:** Publish only after the audit branch is merged and tagged `v0.2.0`, the trigger is narrowed, the README leads with the design property, and an anonymised `docs/EVIDENCE.md` exists.
**Reasoning:** Rejected "publish now — reach first", which the owner said was live: "I had the visibility setting open before the audit, and the trigger finding is what stopped me." Presented, not chosen: "stay private — zero exposure" — agent's assessment: the audit is done and unpublished evidence is wasted evidence; the owner said it was never live.
**Consequences:** Every commit to `main` is an unpinned release to anyone who followed the clone instruction; tag before every behavioural change. Would be revisited if hardening slipped more than a couple of sessions.

## D-0007 — 2026-09-04 — the prepend instruction is fixed in live templates only, never in historical prompts

**Context:** Twenty-five files in the largest project instruct "prepend a session line to STATUS". Two are reusable templates; twenty-three are dated one-shot prompts, register entries and audit snapshots.
**Decision:** Fix the two live templates to say "replace STATUS's top line"; leave the twenty-three untouched.
**Reasoning:** Rejected "fix all 25 — consistency first", which the owner said was live: "I asked for it before I saw the count, and twenty-three of those are dated documents I don't want rewritten." Presented, not chosen: "fix none — untouched history" — agent's assessment: STATUS was growing at about five records a day and the templates are the only live source; the owner said it was never live.
**Consequences:** A reused historical prompt still says "prepend"; precedence, not the prompt, decides. If one is observed producing a prepend anyway, fix that prompt then.

## D-0008 — 2026-09-04 — colliding decision ids get one correction entry, not a renumber

**Context:** Four ids in the largest retired register head more than one entry — three head two bodies, one heads four — and nothing acknowledges it.
**Decision:** Append a single correction entry naming every collision and stating which body governs at each address. Do not renumber.
**Reasoning:** Rejected "renumber — clean addresses", which the owner said was live: "renumbering was my first instinct; the broken citations changed my mind." Presented, not chosen: "leave it — zero edits" — agent's assessment: an ambiguity that is written down is a different thing from one that is not; the owner said it was never live.
**Consequences:** The addresses stay ambiguous, knowingly, with a written reading rule. The entry is drafted by the session that reads every colliding body during the compaction dry run, and applied by the owner. Renumbering becomes right only inside a format migration with a mapping table.
```

The settled item gets no entry: it stands with D-0005 and the CHANGELOG line cites it. **Q4** gets no entry: the owner took the recommendation and said the alternative was never live — the DECISIONS test ("name the rejected alternative the owner actually considered") fails, so it is a default. Its effect on the skill's text is a change of work, logged under its own CHANGELOG entry, not a decision. In all three entries the reason for each rejection is the owner's, quoted from the second reply; the assessment of each option the owner never called live is the agent's and is marked as such, so a future reader can tell the two apart.

### 3. STATUS — rewritten

"Open questions (owner)" goes from five numbered lines to: *None open. The four questions of 2026-09-04 are logged as D-0006 to D-0008 and in the brief entry; the compaction-procedure line was already settled by D-0005 and is removed.* No "answered" section. "Next" gains: 1. merge, tag `v0.2.0`, publish; 2. the two-template fix and the correction entry are outside this repository and are queued where they belong. Deferred row for the compaction procedure is unchanged — D-0005 stands.

### 4. Next action

Merge the audit branch and tag `v0.2.0`.

---

## What this example demonstrates

Three record outcomes from one brief: new decision entries whose Reasoning quotes the owner's own words for each alternative they called live, and marks every other presented option as the agent's assessment (Q1, Q2, Q3 — after one liveness question that named every presented alternative, not only the strongest, and not by assumption); an item already settled by an existing entry, listed in the preamble as settled with no number and no options, and removed from STATUS without being asked (the compaction procedure, D-0005); and an answer that is a default and gets no entry, said out loud (Q4, which also shows a two-option question — no third option was invented to fill the list). One CHANGELOG entry carries the four questions and the settled item. The record is written CHANGELOG, then DECISIONS, then STATUS, so the entries exist before the STATUS rewrite removes the questions. STATUS ends with the list empty rather than with an "answered" section — the failure the mode exists to prevent.
