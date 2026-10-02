# Maple Check — Project Docs

Maple Check is an initial Python utility. Its current `../check.py` entry point prints “Maple Check describes local record checks.” Maintenance is its only planned scope.

**Primary reader:** the owner and future Codex sessions. Docs should be formal enough not to embarrass in a review, but the primary reader is always future-self or future-agent.

---

## How to use these docs

This project runs on a lightweight documentation protocol: a small set of files, each with a single job, and three rituals — bootstrap at session start, close after each meaningful unit of work, and a brief, on demand or offered at close when STATUS carries a question or owner-gated blocker that is not postponed (or whose revisit condition has arrived), which records each answer — a DECISIONS entry when a real alternative was rejected, otherwise the brief's CHANGELOG line. The session-start and logging triggers also live in the project's agent-instructions file (`../AGENTS.md`) so they fire automatically.

### Session bootstrap — do this FIRST, every time

Before proposing work or writing content, read in this order:

1. `STATUS.md` — in full if it is under ~60 lines; otherwise its top line, its headings, and the current-state sections. Current state, in-flight items, blockers, deferred work, next.
2. The last 3–5 entries of `CHANGELOG.md` (most recent first) — what just happened.
3. `DECISIONS.md` — skim for anything touching the area you're about to work on.
4. `GLOSSARY.md` if installed and a term is unfamiliar. Check here before guessing or asking.
5. `LEDGER.md` if installed — the live rows only; never `LEDGER-ARCHIVE.md`. On first adoption, reconcile every live STATUS finding and known-issues item into the ledger before treating it as authoritative: record before/after counts, a source→LG mapping, and a review list for anything that cannot be mapped.
6. `SPEC_TEMPLATE.md` if writing or reviewing a spec (only present in spec-driven projects).
7. Confirm current state before substantive work. STATUS can lag by a session.

### Close — do this after each meaningful unit of work

Log as you go; don't wait for the session to end (the end is often never signaled). Order matters — if the session dies mid-update, the append-only log survives:

1. **Write the CHANGELOG entry first.** Append to the top; formats below. Never edit old entries — append a correction instead.
2. **Edit `LEDGER.md` second** (if installed) — rows in place, new ids at the bottom, terminal rows written and verified in the archive before live removal; CHANGELOG remains first. STATUS derives from it. LEDGER is mutable while live; terminal rows leave for `LEDGER-ARCHIVE.md` and IDs remain reserved forever.
3. **Update STATUS.md third, by rewriting it.** Move completed items out of in-flight. Add new items. Update blockers. Replace the top line — never prepend a session record. Keep it around ~40 lines and never over ~60.
4. **Add a DECISIONS.md entry only if a non-obvious choice was made.** If you can't name the rejected alternative, it's a default — don't log it.
5. Update this `README.md` when working preferences or conventions change. Update `ROADMAP.md`, `BRAND.md`, and `GLOSSARY.md` only if installed and the session's work requires it; add one later when real content warrants it.

---

## Entry formats

The examples below use the installation date; use the actual date for each new entry.

**CHANGELOG entry** (append to top, newest first):

```
## 2026-09-11 — short summary of what happened

Paragraph of 1–3 sentences on what changed and why. Link to relevant spec
or decision IDs. If an entry needs more than three sentences, it's probably
two entries or a DECISIONS entry in disguise.
```

**CHANGELOG correction** (when an earlier entry was wrong — never edit it). Name the target by its summary or a stable token, not by its date alone — most days carry several entries:

```
## 2026-09-11 — correction to "<the earlier entry's summary or token>"

The earlier entry said X [unit, scope]. Re-measured now: Y [same unit, same scope]. [Why the discrepancy.]
```

**CHANGELOG brief entry** (one per brief, never one per question; recorded CHANGELOG, then reserved DECISIONS entries, LEDGER updates, then STATUS — the entry must exist before the STATUS rewrite removes the question; omit the D-range when no entry was logged):

```
## 2026-09-11 — brief: N of M questions answered; D-XXXX–D-YYYY logged

Qn <question> → <answer> (D-XXXX | stands with D-XXXX | default, no decision entry), or "Qn — not answered". One line per question. What the answers unlock next, in one sentence.
```

If a ledger is installed later, each row’s Evidence cites the real provenance: a D-ID, an existing
decision, the Brief CHANGELOG line for a documented default, or the owner
answer recorded there. Clear only the resolved blocker; retain every other
`Blocked-on` gate. A terminal ruling moves the exact row to `LEDGER-ARCHIVE.md`
after archive verification, and a replay never reuses its ID.

**DECISIONS entry** (reconcile pending Briefs first; allocate above existing IDs and all CHANGELOG/decision-archive reservations, never reuse a reserved number):

```
## D-NNNN — 2026-09-11 — short decision title

**Context:** what situation prompted the decision.
**Decision:** what was chosen.
**Reasoning:** why this over the alternatives. Name them explicitly.
**Consequences:** what this commits to, or forecloses.
```

**DECISIONS correction** (when a past decision's *record* was wrong but the decision stands): a new numbered entry titled `D-NNNN — 2026-09-11 — corrects D-XXXX`, saying what was wrong. Never reuse D-XXXX's number with a qualifier — two entries at one address is how a register ends up contradicting itself.

**DECISIONS supersession** (when a past decision is overturned): same format, titled `D-NNNN — 2026-09-11 — supersedes D-XXXX`. Never delete the superseded entry — the historical record matters.

**DECISIONS extension** (when an earlier rule stands, narrowed or added to): same format, titled `D-NNNN — 2026-09-11 — extends D-XXXX — title`. A cited id without a verb is a citation, not lineage; back-links and the head of a chain are derived by grep on the id. When a chain has been extended more than three times, restate the whole rule once as a supersession naming every id it replaces — the head lives in DECISIONS, never as a rewritten copy in README, the instructions file or STATUS. `+tags` may end a title only when `LEDGER.md` exists and its `Tags:` line declares them (Doctor `decisions-tags`).

New DECISIONS entries go at the **bottom** (oldest first, so numbers read in order). New CHANGELOG entries go at the **top** (newest first). The two files run in opposite directions on purpose; a session appending blind to both gets one wrong.

---

## Working preferences

**Register ownership.** This `docs/` register owns Maple Check. No parent register owns this temporary project.

**Utility verification.** Run `python3 check.py` from the project root to exercise the current entry point; its expected output is `Maple Check describes local record checks.` This verifies its current description output, not record-checking behavior.

**Register writes.** One session writes the registers at a time.

These are constants. Pattern-match to them — don't re-derive each session.

**Tone.** Factual, concise, and direct. Describe observed behavior and distinguish it from intended behavior.

**Format.** Prefer short paragraphs. Use lists for steps and tables when the information has consistent fields.

**Pushback.** Substantive disagreement is welcome. Hedging is worse than a clear "I think you're wrong here, because X."

**Options.** When presenting alternatives, label each by what it prioritizes and trades off — "Ship fast, accept debt" vs. "Ship slow, compound maintainability" — not "Option A" vs. "Option B." Recommend one, then let the owner decide.

**Decisions.** The project owner decides non-obvious scope and tradeoff choices; agents handle routine implementation details within the authorized task. Don't paper over ambiguity with a default; surface the choice. Open choices go in STATUS under Open questions (owner) and are resolved by a brief, not in passing. An answer is an explicit pick; a question the owner did not address stays open.

**Session hygiene.** For tasks estimated over ~2 hours, prefer a fresh session plus the bootstrap ritual over continuing a long one — long sessions accumulate context that quietly degrades quality. Dispatch subagents only for genuinely independent units of work, not sequential work; integration cost outweighs fake parallelism.

**What doesn't need to be asked.** Assume: concise over long, direct answers before caveats, strongest argument before hedged version, the actual artifact created rather than a description of what it would contain.

---

## File index

The minimum is four documentation files: README, STATUS, CHANGELOG and DECISIONS. The project-level agent-instructions file supplies the required wiring separately. Other documents are added when there is real content to seed.

- **`README.md`** (this file) — the map. Bootstrap, close, formats, preferences.
- **`STATUS.md`** — living dashboard of current state. Updated every session.
- **`CHANGELOG.md`** — append-only history of what happened and why.
- **`DECISIONS.md`** — append-only log of non-obvious choices with reasoning.

---

*Installed via the `project-docs-protocol` skill. The protocol is portable — designed to work for any project.*
