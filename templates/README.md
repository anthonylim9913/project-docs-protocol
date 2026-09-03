# [PROJECT NAME] — Project Docs

[One or two sentences on what the project is and its current phase. Keep it to what a reader needs in order to orient — not marketing.]

**Primary reader:** [who re-reads these docs most often — default: the owner + future agent sessions]. [Any occasional reviewers noted here.] Docs should be formal enough not to embarrass in a review, but the primary reader is always future-self or future-agent.

---

## How to use these docs

This project runs on a lightweight documentation protocol: a small set of files, each with a single job, and three rituals — bootstrap at session start, close after each meaningful unit of work, and a brief, on demand or offered at close when STATUS carries a question or owner-gated blocker that is not postponed, which turns those questions into DECISIONS entries. The session-start and logging triggers also live in the project's agent-instructions file (`CLAUDE.md` / `AGENTS.md`) so they fire automatically.

### Session bootstrap — do this FIRST, every time

Before proposing work or writing content, read in this order:

1. `STATUS.md` — in full if it is under ~60 lines; otherwise its top line, its headings, and the current-state sections. Current state, in-flight items, blockers, deferred work, next.
2. The last 3–5 entries of `CHANGELOG.md` (most recent first) — what just happened.
3. `DECISIONS.md` — skim for anything touching the area you're about to work on.
4. `GLOSSARY.md` if a term is unfamiliar. Check here before guessing or asking.
5. `SPEC_TEMPLATE.md` if writing or reviewing a spec (only present in spec-driven projects).
6. Confirm current state before substantive work. STATUS can lag by a session.

### Close — do this after each meaningful unit of work

Log as you go; don't wait for the session to end (the end is often never signaled). Order matters — if the session dies mid-update, the append-only log survives:

1. **Write the CHANGELOG entry first.** Append to the top; formats below. Never edit old entries — append a correction instead.
2. **Update STATUS.md second, by rewriting it.** Move completed items out of in-flight. Add new items. Update blockers. Replace the top line — never prepend a session record. Keep it around ~40 lines and never over ~60.
3. **Add a DECISIONS.md entry only if a non-obvious choice was made.** If you can't name the rejected alternative, it's a default — don't log it.
4. `ROADMAP.md`, `BRAND.md`, `GLOSSARY.md`, and this `README.md` only update when the session's work specifically required it.

---

## Entry formats

**CHANGELOG entry** (append to top, newest first):

```
## YYYY-MM-DD — short summary of what happened

Paragraph of 1–3 sentences on what changed and why. Link to relevant spec
or decision IDs. If an entry needs more than three sentences, it's probably
two entries or a DECISIONS entry in disguise.
```

**CHANGELOG correction** (when an earlier entry was wrong — never edit it). Name the target by its summary or a stable token, not by its date alone — most days carry several entries:

```
## YYYY-MM-DD — correction to "<the earlier entry's summary or token>"

The earlier entry said X [unit, scope]. Re-measured now: Y [same unit, same scope]. [Why the discrepancy.]
```

**CHANGELOG brief entry** (one per brief, never one per question; omit the D-range when no entry was logged):

```
## YYYY-MM-DD — brief: N of M questions answered; D-XXXX–D-YYYY logged

Qn <question> → <answer> (D-XXXX | stands with D-XXXX | default, no decision entry), or "Qn — not answered". One line per question. What the answers unlock next, in one sentence.
```

**DECISIONS entry** (numbered sequentially — check the highest existing D-number):

```
## D-NNNN — YYYY-MM-DD — short decision title

**Context:** what situation prompted the decision.
**Decision:** what was chosen.
**Reasoning:** why this over the alternatives. Name them explicitly.
**Consequences:** what this commits to, or forecloses.
```

**DECISIONS correction** (when a past decision's *record* was wrong but the decision stands): a new numbered entry titled `D-NNNN — YYYY-MM-DD — corrects D-XXXX`, saying what was wrong. Never reuse D-XXXX's number with a qualifier — two entries at one address is how a register ends up contradicting itself.

**DECISIONS supersession** (when a past decision is overturned): same format, titled `D-NNNN — YYYY-MM-DD — supersedes D-XXXX`. Never delete the superseded entry — the historical record matters.

New DECISIONS entries go at the **bottom** (oldest first, so numbers read in order). New CHANGELOG entries go at the **top** (newest first). The two files run in opposite directions on purpose; a session appending blind to both gets one wrong.

---

## Working preferences

These are constants. Pattern-match to them — don't re-derive each session.

**Tone.** [Populate with project-specific tone. Example default: positive framing, factual, analytical. Avoid inherently negative words when a neutral alternative works.]

**Format.** [Populate — e.g., "prose over bullets unless structure genuinely earns its place. Tables are fine for genuinely table-shaped data."]

**Pushback.** Substantive disagreement is welcome. Hedging is worse than a clear "I think you're wrong here, because X."

**Options.** When presenting alternatives, label each by what it prioritizes and trades off — "Ship fast, accept debt" vs. "Ship slow, compound maintainability" — not "Option A" vs. "Option B." Recommend one, then let the owner decide.

**Decisions.** [Populate — who is the decider? Default: the project owner.] Don't paper over ambiguity with a default; surface the choice. Open choices go in STATUS under Open questions (owner) and are resolved by a brief, not in passing. An answer is an explicit pick; a question the owner did not address stays open.

**Session hygiene.** For tasks estimated over ~2 hours, prefer a fresh session plus the bootstrap ritual over continuing a long one — long sessions accumulate context that quietly degrades quality. Dispatch subagents only for genuinely independent units of work, not sequential work; integration cost outweighs fake parallelism.

**What doesn't need to be asked.** Assume: concise over long, direct answers before caveats, strongest argument before hedged version, the actual artifact created rather than a description of what it would contain.

---

## File index

- **`README.md`** (this file) — the map. Bootstrap, close, formats, preferences.
- **`STATUS.md`** — living dashboard of current state. Updated every session.
- **`ROADMAP.md`** — the plan. Detailed near-term, sketched long-term.
- **`CHANGELOG.md`** — append-only history of what happened and why.
- **`DECISIONS.md`** — append-only log of non-obvious choices with reasoning.
- **`GLOSSARY.md`** — project term definitions, sectioned by domain.
- **`BRAND.md`** — brand anchors, voice guide, design constants. [Delete this line if not installed.]
- **`SPEC_TEMPLATE.md`** — the template project specs follow. [Delete this line if not installed.]

---

*Installed via the `project-docs-protocol` skill. The protocol is portable — designed to work for any project.*
