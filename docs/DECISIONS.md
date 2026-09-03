# DECISIONS

*Append-only log of non-obvious choices with reasoning. Context → Decision → Reasoning → Consequences. Test before logging: can you name the rejected alternative that was actually considered? If not, it's a default, not a decision.*

*Entries numbered sequentially and appended at the bottom, oldest first. Never edit past entries; append corrections or supersessions instead. A correction is a new numbered entry that names its target.*

---

## D-0001 — 2026-09-03 — DECISIONS entries go at the bottom, oldest first

**Context:** The template never stated an order; 14 installs chose oldest-first and 7 newest-first, and a session appending blind to CHANGELOG (newest-first) and DECISIONS gets one wrong.
**Decision:** Bottom, oldest first.
**Reasoning:** Sequential numbering reads naturally in order; the majority of installs already do it; "append" then means the same physical operation for both registers' *growth* even though the files run in opposite directions. Rejected: newest-first to match CHANGELOG — it makes D-0001 sit at the bottom of a numbered list and was the minority practice.
**Consequences:** The README template now says so explicitly and warns that the two files run opposite ways.

## D-0002 — 2026-09-03 — the STATUS red flag is ~60 lines plus a max-line signal, not a byte cap and not a "dated records" signal

**Context:** The literal ~40-line flag fired on 23 of 25 roots and on the template (44 lines), so it discriminated nothing. Three replacements were tested against the population.
**Decision:** Flag at ~60 lines (fires on 16 of 25, 80 on 10) and on any single line over ~1 KB.
**Reasoning:** Rejected a bare 4 KB byte cap: it flags EVA Copilot, the one mature installation that kept discipline, while passing nothing it should. Rejected "no dated session records in STATUS": it fires on only 5 of 25 roots and misses send-more-heroes, Subterra and King of Mini Games, which are 47%, 32% and 22% history by line — their history headings carry no date. The max-line signal fires on 12 of 25 including the one file that folds thirteen sessions into a 36 KB line and would pass any line cap.
**Consequences:** "~40 lines" survives as the target; "never over ~60" is the flag. The template was cut to 37 lines so a one-row fill sits under the target.

## D-0003 — 2026-09-03 — the three design properties outrank project convention; everything else is the project's

**Context:** The protocol had no precedence rule. The largest project inverted the STATUS design property through its own always-loaded CLAUDE.md ("top line") without ever contradicting the protocol's text, and nothing said which file won.
**Decision:** CHANGELOG-before-STATUS, STATUS-rewritten and registers-append-only are the protocol's and are not overridable; paths, id formats and entry shapes belong to the project's block.
**Reasoning:** Rejected "the project file always wins": it re-licenses exactly the inversion that produced a 611 KB STATUS. Rejected "the protocol always wins": it would override legitimate local choices (docs path, `PWC-APP-D-NNN` ids, entry shapes) and give projects a reason to stop wiring the block at all. The three properties are the ones the audit measured as load-bearing; the rest were never the problem.
**Consequences:** The wiring block carries a Precedence bullet. A disagreement on a property is to be logged as a CHANGELOG entry, so it gets resolved rather than inherited.

## D-0004 — 2026-09-03 — concurrency gets one stated assumption and a pointer, not an annex and not a second protocol

**Context:** The protocol has no concurrency model (zero occurrences of parallel, worktree, branch, lock). The one repository that ran 5–37 lanes on a shared tree accreted eleven compensating mechanisms in 24 days.
**Decision:** One operating principle — "one writer at a time" — plus a pointer to worktree-per-agent isolation.
**Reasoning:** Rejected an annex: 19 of 25 roots have one worktree or none and would pay for it; and the measured damage was 0.74% docs-shaped — registers were 23 of 3,091 swept file-changes — so the problem is N agents sharing one git index, which no documentation protocol governs. Rejected a separate multi-writer protocol for now: the only multi-worktree installation (EVA, 9 worktrees) recorded zero collisions using isolation alone, so the cheapest fix has already been demonstrated. Revisit if a second shared-tree project appears.
**Consequences:** Eight of the eleven mechanisms that project invented are git mechanics; SKILL.md already delegates workflow norms to the project README, and that stays true.

## D-0005 — 2026-09-03 — the compaction trigger changes now; the procedure waits for a dry run

**Context:** "Once a quarter, compact" had fired once in 25 projects (EVA, agent-proposed, 70 → 38 lines). Writing a full procedure from theory was the alternative.
**Decision:** Change the trigger to size-based (~60 lines or a red flag) and describe the routing rule; defer the step-by-step procedure until it has been dry-run against the parent PWC STATUS's five archive sections with a lossless check.
**Reasoning:** Rejected writing the procedure now: the only instance that exists was not observed in detail, and the one file it would most apply to has mechanical consumers (a gate that scans every STATUS line) that a naive split would silence. Rejected leaving the trigger as-is: at the observed rate, quarterly permitted ~470 records between compactions.
**Consequences:** Deferred item in STATUS. The procedure, when written, should generalise EVA's instance rather than invent one.
