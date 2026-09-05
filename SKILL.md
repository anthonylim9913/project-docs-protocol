---
name: project-docs-protocol
description: "Lightweight documentation protocol for multi-session projects. Use when the user wants to bootstrap project docs, resume work on an existing project, or log completed work. Triggers on: 'set up project docs', 'initialize docs', 'install the project docs protocol', 'cold start', 'coldstart', 'bootstrap this project', 'catch me up on <project>', 'resume work', 'where were we', 'close out the session', 'log this session', 'update the changelog', 'check the docs', 'doctor', 'is the protocol wired', 'brief me', 'what do you need from me', 'what are you waiting on', and whenever a project folder contains STATUS.md + CHANGELOG.md + DECISIONS.md (at the root or under /docs/) AND either its CLAUDE.md/AGENTS.md carries the 'Project docs protocol' block or its docs README says it was installed by this skill — the signature of an installed system. Three matching filenames alone are not the signature: other conventions use them."
---

# Coldstart — project documentation protocol

This skill installs and operates a small-file documentation protocol designed for multi-session, multi-month projects where continuity across sessions is the main cost. The protocol is portable — it works for any project, not a specific one.

## When to use this skill

Invoke automatically, without asking, in any of these situations:

1. **User asks to set up project docs** for a new or existing project. Phrases like "set up the docs folder," "initialize project docs," "install the project-docs-protocol system," "bootstrap this project." → Run **Install**.
2. **User returns to work on a project** that carries the signature of an installed system: `STATUS.md`, `CHANGELOG.md` and `DECISIONS.md` at the root or under `/docs/`, **and** either the `## Project docs protocol` block in `CLAUDE.md`/`AGENTS.md` or the footer *"Installed via the `project-docs-protocol` skill"* in the docs README. Three matching filenames alone are not enough — Keep-a-Changelog plus an ADR folder produces the same three names, and a register that predates this skill is not an installation of it. Always run **Bootstrap** before proposing work.
3. **A meaningful unit of work just completed** on such a project — a spec drafted, a decision made, a blocker resolved, a major refactor landed. Run **Close** immediately; don't wait for the session to end. Session-end phrases ("close out," "log the session," "let's wrap") also trigger Close as a catch-all.
4. **User asks to catch up or resume:** "where were we on X," "catch me up on X," "resume work on X." → Run **Bootstrap**.
5. **User asks whether the install is healthy:** "check the docs," "doctor," "is the protocol wired here." → Run **Doctor**. Also run it, unasked, whenever a Bootstrap red flag fires.
6. **User asks what they need to decide:** "brief me," "what do you need from me," "what are you waiting on." → Run **Brief**. At Close, offer it in one line only when STATUS carries an askable item; otherwise say nothing.

**If a resume-style phrase fires but the signature is absent** — no files, or the three files without the block or footer — don't hunt indefinitely and don't adopt a register you did not install: say the protocol isn't installed here and offer Install instead (which, on pre-existing registers, means wiring and reconciling, not overwriting).

---

## Mode 1 — Install (cold start a new project)

### Pre-install interview

Ask these before creating any files (or confirm from memory/conversation). Keep it to one exchange; don't over-interrogate.

1. **Project name.** The canonical name used in prose, plus any shorthand.
2. **Doc location.** Default: `/docs/` at the repo root. Alternatives: `./` (root) for small projects, `~/<project>/docs/` for non-code projects.
3. **Current phase.** Truly new, or mid-flight? Mid-flight installs seed STATUS with approximate in-flight items (flagged as approximate).
4. **Primary reader.** Default: the user + future agent sessions. Formality target: "wouldn't embarrass in a review." Any additional reviewers?
5. **Does brand matter, and is anything known yet?** Keep BRAND.md only if the project has a brand dimension *and* at least one concrete value can be written today — a font, a colour, a path to a brand system. A BRAND.md with only `[POPULATE]` markers is never filled in later (measured: 8 of 14 were untouched after install day). Otherwise skip it and add it when a value exists.
6. **Spec-driven?** If the project will use written specs, confirm the spec ID prefix (default `PROJ-SPEC-NNNN`) and include SPEC_TEMPLATE.md. Otherwise skip it.
7. **Is there already a register above this folder?** If the repository root or a parent folder has its own STATUS/CHANGELOG/DECISIONS, decide which register owns this work and write the answer into both READMEs. Two registers in one repository with no ownership rule is how a session writes to the wrong one.

### Step 1 — Create the folder and copy templates

Copy from this skill's `templates/` directory into the target location:

```
<docs>/
├── README.md          # the map: bootstrap, close, preferences, entry formats
├── STATUS.md          # living dashboard of current state
├── ROADMAP.md         # the plan — detailed near-term, sketched long-term
├── CHANGELOG.md       # append-only history of what happened and why
├── DECISIONS.md       # append-only log of non-obvious choices with reasoning
├── GLOSSARY.md        # project-specific terms, sectioned by domain
├── BRAND.md           # brand anchors, voice, tokens (only if brand matters)
└── SPEC_TEMPLATE.md   # spec template (only for spec-driven projects)
```

Personalize each template with the project name, reader audience, working preferences, and any initial content you can infer. Replace every `YYYY-MM-DD` with today's date. Delete placeholder rows that have no real content — the Open-questions line, the Next placeholder line, the example table rows. `[POPULATE]` may remain only in BRAND.md, and each one is a WARN the next Doctor prints: leave one only for a value that is genuinely pending.

### Step 2 — Wire up auto-triggering

This is the step that makes the protocol survive. Skill-trigger phrases are unreliable; instructions files are loaded every session. It is also the step that decides whether STATUS stays a dashboard: measured across every install, projects whose instructions file carries this block rewrite STATUS each close, and projects without it — or with a project-authored block that names a "top line" — accrete history there until the file is unreadable. Append this block (adjusted for the actual docs path) to the project's agent-instructions file — `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex and other agents. Update whichever exist; if neither exists, create the one(s) matching the tools the user works with — when in doubt, create both with identical content:

```markdown
## Project docs protocol

This project uses the project-docs-protocol (docs in `<docs-path>/`).

- **Session start:** before proposing or doing any work, read `STATUS.md`
  (in full if it is under ~60 lines; otherwise its top line, its heading
  list, and the current-state sections only) and the last 3–5 entries of
  `CHANGELOG.md`; skim `DECISIONS.md` for entries touching the area you're
  about to work on.
- **After each meaningful unit of work** (spec drafted, decision made, blocker
  resolved, major refactor): append a CHANGELOG entry, then update STATUS.
  Do this as you go — do not wait for the session to end.
- **STATUS is rewritten, not appended.** Replace the current-state sections
  and bump the last-updated date. Never prepend a session record or leave a
  dated "done" section behind: that record belongs in CHANGELOG, and it must
  already be there before STATUS changes.
- CHANGELOG and DECISIONS are append-only: never edit past entries; append
  corrections or supersessions instead.
- **Precedence.** The three properties above — CHANGELOG before STATUS,
  STATUS rewritten, registers append-only — are the protocol's and are not
  overridden by project convention. Paths, id formats and entry shapes are
  this project's to set, here. If this file and the protocol disagree on one
  of those three properties, the disagreement is a CHANGELOG entry, not a
  habit.
```

### Step 3 — Seed from existing context

Pull whatever you have from memory, prior conversation, or user input:

- **STATUS:** seed the in-flight table with approximate items, **flag them as approximate**, and note that the next session should confirm.
- **GLOSSARY:** populate terms you know, sectioned by the project's domains. Incomplete is fine — empty is bad. But don't over-seed: 15 terms that match reality beat 80 aspirational ones.
- **ROADMAP:** fill near-term detail if you have it; sketch later phases vaguely.
- **BRAND** (if kept): fill what's known (step 1 says what a `[POPULATE]` marker costs).

### Step 4 — Log the installation

Append to CHANGELOG at the top (newest first) — replace the template's placeholder entry, do not keep it above the real one:

```
## YYYY-MM-DD — initialized project documentation system

Installed the project-docs-protocol at <path>. [One sentence on how STATUS
was seeded.] [One sentence on any deviations from default — e.g., "BRAND.md
omitted; no brand dimension."]
```

**Only add a DECISIONS entry if adopting the protocol was genuinely deliberated** — i.e., the user actually weighed it against a real alternative in this conversation. A scripted D-0001 with canned reasoning is a default dressed up as a decision; the CHANGELOG entry above is the record of installation. DECISIONS starts empty otherwise.

### Step 5 — Hand off

Tell the user: "Installed and wired into `CLAUDE.md`/`AGENTS.md` — future sessions will bootstrap and log automatically. The README documents the protocol." Don't over-explain; point at the README and move on.

### Install pitfalls

- **Don't mix modes.** Install now; bootstrap belongs to the next session.
- **Don't delete thin files prematurely.** A sparse ROADMAP is fine for v0 — it grows. Only omit a file that truly doesn't apply (BRAND for a pure-backend tool).

---

## Mode 2 — Bootstrap (resume an existing project)

Read in this order — do not skip or reorder:

1. **`STATUS.md` — in full when it is under ~60 lines.** Past that, read its top line, its heading list (`grep -n '^## ' STATUS.md`), and the current-state sections: current phase, in flight (owners, blockers), blocked (what gates each), deferred (why), next. Do not read the history a bloated STATUS has accumulated — a 600 KB STATUS read in full costs more than the whole rest of the bootstrap, and the history in it belongs to CHANGELOG. Its size is a red flag (below), not context.
2. **Last 3–5 entries of `CHANGELOG.md`** (newest at top). Three is usually enough; go to five if recent sessions were light or the thread is hard to follow. Watch for corrections to earlier entries (they flag where the mental model was wrong) and referenced decision IDs — follow those into DECISIONS.md.
3. **`DECISIONS.md` — skim, don't read whole.** Look for: decisions touching the area you're about to work on, decisions referenced in recent CHANGELOG entries, and the most recent 2–3 regardless of topic (they often set frame). **Do not re-litigate resolved decisions.** If a D-entry chose X over Y, build on X; if the user wants to revisit, the move is a supersession entry, not a rewrite.
4. **`GLOSSARY.md` as a dictionary** — look up terms you don't recognize; don't guess and don't ask the user for a term defined here. Project definitions override general knowledge. Watch for flagged overloaded terms.
5. **`SPEC_TEMPLATE.md`** only if the session involves authoring or reviewing a spec.
6. **Confirm current state with the user** before substantive work — STATUS can lag by a session. One short exchange ("Still focused on X? Anything land that isn't in STATUS?"), not an interrogation.

Only after bootstrap: propose what you're going to do — proposals now fit where the project actually is, not where you assumed it was.

### Red flags during bootstrap

- **STATUS over ~60 lines, or any single line over ~1 KB.** Something is miscategorized — almost always past-tense history kept in STATUS: dated "done" or "shipped" sections, stacked session records at the top, a last-updated line that has become a paragraph. Name the sections; suggest moving them to CHANGELOG. (The template is ~40 lines; a healthy mature STATUS sits near 40. A 40-line cap alone is not the signal — one file folded thirteen sessions into a single 36 KB line and would pass it.)
- **More than one session record at the top of STATUS.** History is being stacked in the one file designed to be rewritten. Stop the inflow first — fix the writer instruction — before discussing compaction.
- **CHANGELOG has a multi-month gap, or its newest entry is more than a month old.** Discipline slipped, or the project was dormant. Ask whether to write a catch-up entry before continuing.
- **DECISIONS entries contradict without supersession links.** The log has lost integrity — flag it.
- **GLOSSARY contradicts usage in STATUS.** Glossary is authoritative; ask whether the definition is stale or the usage is wrong.

Fixes for all of these are small close-ritual adjustments, not a redesign.

---

## Mode 3 — Close (log completed work)

Run this **immediately after each meaningful unit of work completes** — not only at session end. Sessions rarely announce their final message, so a close deferred to "the end" often never happens; logging as you go is what makes the protocol survive interruption. Session-end phrases from the user trigger a final catch-all pass.

If the work was trivial (one-off question, no artifacts, no decisions), no close is needed — don't manufacture an entry to show you did the protocol.

**Order matters.** If the session dies mid-update, the append-only log is what survives:

1. **Write the CHANGELOG entry first** (append to top — formats are in the project README): date, one-line summary, 1–3 sentences of what and why. Never edit old entries; append a correction instead.
2. **Update STATUS.md second, by rewriting it.** Move completed items out of in-flight; add new in-flight items; add/remove blockers (log unblocks in CHANGELOG) and deferrals (with reasons); bump the last-updated date. Replace the top line; never prepend a session record above it. Delete every past-tense sentence you find — it is already in the CHANGELOG entry you just wrote, or it should be. Keep STATUS around ~40 lines and never over ~60: past that, something is miscategorized — an in-flight item that's really deferred, a resolved blocker, a "done" section never moved out.
3. **Add a DECISIONS entry only if a non-obvious choice was made.** Test: can you name the rejected alternative the user actually considered? If not, it's a default — don't log it. Context → Decision → Reasoning → Consequences, numbered sequentially (check the highest existing D-number first), appended at the bottom so the numbering reads in order. A correction to a past decision is a **new** numbered entry that names its target (`corrects D-XXXX`), never the old number with a qualifier — two entries under one id is how a register ends up with contradictory bodies at the same address.
4. **ROADMAP, BRAND, GLOSSARY, README** only when the session's work required it: ROADMAP at phase boundaries; BRAND on visual/voice changes; GLOSSARY for new, stale, or overloaded terms; README for working-preference or convention changes. Restraint is part of the protocol.

### What counts as CHANGELOG-worthy

A spec drafted/reviewed/ratified, a decision made, a blocker resolved, a major refactor or scope change, an audit finding or dependency shift. **Not:** every file touched, every paragraph edited. Aim for 1–3 entries per session; if you have 10, compress them into meaningful units.

### What counts as DECISIONS-worthy

Non-obvious tradeoffs where a reasonable alternative was rejected: scope decisions, framework/tool choices with real tradeoffs, audience or formality calls, supersessions of earlier decisions. **Not:** routine implementation choices, renames, or anything with no alternative actually under consideration.

### Common failure modes

- **Close skipped because "nothing substantive happened."** If an artifact was created or a decision made, close. The bar is lower than you think.
- **STATUS updated before the CHANGELOG entry.** Wrong order — the append-only log must be the thing that got through if the session dies.
- **A default logged as a decision.** No nameable rejected alternative → no entry.
- **STATUS grows unbounded.** Compact when it passes ~60 lines or when a bootstrap red flag fires — not "once a quarter", which in practice has meant never: retro-log completed items to CHANGELOG (check each one already has an entry; write the missing ones first, append-only), demote stale in-flight to deferred, then rewrite the dashboard. Do it from the rewritten file's point of view, not by trimming the old one.

---

## Mode 4 — Doctor (check an installed project)

Doctor is a read-only health check for a project that already carries the protocol. It measures the register against the thresholds this skill states, prints one line per check, and stops. **Doctor never edits.** It reports, and the session proposes; the owner decides; any fix is then an ordinary Close (CHANGELOG entry first) or, for wiring, an Install step 2 re-sync.

### When to run it

- **On demand.** "Check the docs", "doctor", "is the protocol wired here", "how healthy is STATUS", "audit the register" → run Doctor.
- **Automatically, when any Bootstrap red flag fires** — the five listed under Mode 2 — run Doctor before discussing the flag. It turns a hunch into a measured line the owner can act on, and it often finds the second problem behind the first (a dated "done" section, a stale wiring block, a nested register).
- **After Install, once.** A fresh install should exit 0 — or 1 only for brand-placeholders you chose to leave. If it does not, the install is not finished.
- **Not** on every session start. Bootstrap already reads the register; Doctor is for when something looks wrong or the owner asks.

### How to run it

The checker is `scripts/docs-doctor.py` in this skill's directory. Python 3 standard library only; git is optional and used only for the two git lines at the end.

```
python3 <skill-dir>/scripts/docs-doctor.py "<project-root>"
python3 <skill-dir>/scripts/docs-doctor.py "<project-root>" --today 2026-09-04   # reproducible dormancy figure
python3 <skill-dir>/scripts/docs-doctor.py "<project-root>" --no-git             # skip git even if present
```

Pass the **project root** — the directory that holds `CLAUDE.md` / `AGENTS.md`. The register is found at the root or under `docs/`; passing the `docs/` directory itself also works. Quote paths with spaces.

Exit codes: **0** every check passed · **1** at least one WARN and no FAIL — advisory drift, judge each line · **2** at least one FAIL — a protocol property is broken · **3** the checker could not run (no such directory, no register, or a crash). INFO and SKIP lines never affect the exit code. Files with NUL bytes, CRLF endings, or no content are handled without crashing; the report prints under any locale (undecodable characters are replaced, never raised). A malformed decision id of any width is a WARN, not a hang: the id census is linear in the number of ids, whatever their values.

### How to read the output

One line per check: level, check name, measured value with its unit, and the threshold it was judged against. Thresholds are printed so they can be argued with. Read the lines top to bottom; the order is wiring → clauses → path → README → CHANGELOG → decision-refs → STATUS → DECISIONS → BRAND → nesting → siblings → git.

| Line | What it measures | What to do about a WARN/FAIL |
|---|---|---|
| `wiring-block` | Whether `CLAUDE.md` and/or `AGENTS.md` at the root carries the skill's block on a **visible, unquoted** line — text inside code fences, HTML comments or blockquotes (`> `) is dropped before any wiring search, so a quoted or fenced copy of the block is not a block. **PASS** needs the `## Project docs protocol` heading (level 2 or 3, up to three leading spaces) or the sentence *This project uses the project-docs-protocol*. **WARN** *mentioned but no block* when a file names the skill without either. **WARN** *project-authored close instructions* when no block exists but a file names CHANGELOG then STATUS in a close-order sentence. **FAIL** when neither file exists or neither carries a block or any close-order instruction. | The block is the mechanism, not documentation: measured across every install, projects without it accrete history in STATUS. For FAIL and *mentioned but no block*, propose Install step 2 — append the block, adjusted for the docs path. For *project-authored close instructions*, confirm the text says the same three things (CHANGELOG first, STATUS rewritten, registers append-only), then propose a re-sync so the precedence and rewritten-not-appended clauses are present verbatim. Do not call a wired project unwired. |
| `wiring-clauses` | Whether the block carries the three current clauses **inside its own span**: *rewritten, not appended*; the bounded read (*in full if under ~60 lines*); and *Precedence*. The span runs from the block's heading to the next heading of the same or higher level; for the sentence form, from the sentence's paragraph through the bullet list that follows it (at most 40 lines). Clauses found elsewhere in the file — a "historical notes" section, an older copy below — do not count. WARN names which file lacks which. SKIP when there is no skill block to compare. | The block was copied from an older SKILL.md, or its clauses drifted out of it. Propose re-syncing it from Install step 2 as one block and logging the re-sync as a CHANGELOG entry. |
| `wiring-path` | Whether the block's *(docs in `X/`)* names the directory the doctor found the register in. `./docs/`, `docs` and `docs/` all mean `docs/`; `./`, `.`, `root`, `the root` and `repository root` all mean the project root. **FAIL** *block says docs in X/, register found at Y/* on a mismatch; **WARN** when the block carries no path; PASS on a match; SKIP without a block. | A block that points at the wrong directory sends every session to a register that is not there — it reads nothing and writes a second one. Fix the path in the block (Install step 2); if the register was moved, say so in a CHANGELOG entry. A block without a path is fixed the same way — add *(docs in `docs/`)* or `(docs in `./`)`. |
| `readme-footer` | The install footer *Installed via the `project-docs-protocol` skill* in the register's README, on a visible line of its own — a leading `*`, `_` or `>` is allowed, a fenced or commented copy is not, and a line that negates it ("was not installed via", "never installed") is not a footer. WARN when absent, negated, or present only mid-sentence. | Absent footer plus absent block means the register may predate the skill or come from another convention (Keep-a-Changelog plus ADRs looks identical). A negated line is the README saying so outright. Confirm with the owner before treating it as an installation; Install on a pre-existing register means wiring and reconciling, not overwriting. |
| `changelog-entries` | INFO: `##` entry count, distinct dates, span, bytes, and whether an install entry exists. WARN with *0 entries — nothing has been logged* only when the file has no `##` headings **and** no dated lines. A file with no `##` headings but dated lines (one-line bullets, `###` entries) gets *entries in another shape? check the README* — the project logs, just not in the template's shape; dormancy is then measured from those lines and the order and format checks are skipped. | Context for the lines below. For the *another shape* case, confirm the README declares the shape and which end is newest; Bootstrap's "last 3–5 entries" assumes `##` headings, so say how to find the newest entries. |
| `changelog-dormancy` | Days since the newest dated heading (or dated line). WARN over 30. | Ask whether the project is dormant or discipline slipped, and whether to write a catch-up entry before continuing. Do not write one unasked. |
| `changelog-order` | Whether the newest entry is at the top. | Bootstrap reads the top 3–5 entries; a bottom-appended CHANGELOG makes Bootstrap read the oldest work. Propose reversing on the next Close — as one entry, append-only rules still apply to bodies. |
| `changelog-heading-format` | Fraction of `##` headings that match `## YYYY-MM-DD — summary`. PASS at 0.95 or better. Headings inside code fences are ignored and counted separately. | Undated headings cannot be found by date. Propose the format for future entries; never rewrite old headings. Fenced headings are template examples left behind — safe to delete. |
| `changelog-decision-refs` | Decision ids named in CHANGELOG `##` headings only (`D-0006–D-0008 logged`; bodies are never read — they cite other projects' ids). For each id series, the highest cited number is compared with the highest id present in DECISIONS. **WARN** *CHANGELOG names D-XXXX but DECISIONS' highest is D-YYYY* when a cited number is above it, or when DECISIONS holds no ids at all; INFO with the count when every citation resolves — a cited series that this DECISIONS does not keep while it keeps others (`UX-D-` cited beside a register that keeps only `API-D-`) is a parent or sibling register's and is reported, not judged; SKIP when no heading cites an id. | A brief writes CHANGELOG first and DECISIONS second, so a cited id with no entry is a brief that died between the two writes. Write the missing entries under exactly those ids (append-only; never renumber the CHANGELOG line), from the brief's recorded answers — never from memory of what was probably decided. |
| `status-size` | Lines and bytes. WARN over 60 lines, **FAIL** over 100. | Something is miscategorised — almost always past-tense history. Run the compaction in Close: retro-log completed items to CHANGELOG (check each already has an entry; write the missing ones first), demote stale in-flight to deferred, then rewrite the dashboard. Bytes are reported, not judged: a byte cap alone flags well-behaved mature files. |
| `status-longest-line` | Longest line in bytes. WARN over 1,024. | A line that long is a session folded into a paragraph — it passes a line cap while carrying kilobytes of history. Name the line; propose moving its content to CHANGELOG. |
| `status-session-stack` | Session-record lines (`LAST SESSION:`, `PRIOR SESSION`, …) above the first `##` heading. WARN at one, **FAIL** at more than one. | STATUS has become a second append-only log with no protection. **Stop the inflow first** — find the writer instruction that says "prepend" and change it to "replace; the record you displace must already be in CHANGELOG" — before discussing compaction. |
| `status-last-updated` | The `Last updated:` date on a visible line, against the newest CHANGELOG date and against today. WARN with the lag in days when behind; WARN *N days ahead of the newest CHANGELOG entry — a future date* when ahead of the log, and the same WARN naming today when ahead of the clock; WARN *line present but its date is unparseable* (`2026-13-45`, a month name); WARN *no line found* when it is absent or only inside a comment or fence. | A lag means the last Close wrote CHANGELOG and skipped the STATUS rewrite. A date ahead of the log means STATUS was bumped without the CHANGELOG entry that must precede it, or the date is a typo; ahead of today it is a typo or a wrong clock — fix the line in place. An unparseable date is fixed in place too — do not add a second line. A missing line means the close ritual has nothing to bump — propose restoring the template's line. |
| `status-past-tense` | **Heuristic.** Lines containing *shipped / landed / deployed / done / fixed / closed* under a dated heading, plus the count of dated headings. WARN over 3 lines; INFO for 1–3. | Dated headings in STATUS are history in disguise. Read the sections it names before proposing anything — a "Blocked" table row saying "fixed upstream" is a false positive. |
| `status-template-residue` | Visible STATUS lines still carrying a template placeholder — `[one-line question`, `[option label]`, `[The ordered queue`, `[Section name`, `[Item`, or any numbered or bulleted line whose bold text opens with `[`. WARN with the count and the first offender; PASS at 0. Fenced and commented lines are not read. | A bracketed placeholder is not an item: a Brief reads `1. **[one-line question]**` as an askable question and offers the owner a choice that does not exist. Delete the line or fill it at the next Close — Install should already have removed the row when there was nothing to put in it. |
| `decisions-id-malformed` | Ids whose number is wider than 6 digits (`D-20260904`, `D-99999999999999999999`). WARN; excluded from the duplicate, order and gap census. | A date or a typo used as a number. Propose a correction entry under the next real number; the malformed heading stays (append-only) and the correction names it. |
| `decisions-ids` | Decision ids at **both** `##` and `###` level, outside code fences. Recognised forms: `D-NNNN` (the template), `PREFIX-D-NNN` with any chain of upper-case prefixes (`PROJ-D-012`, `API-D-003`, `UX-D-002`), `D-XX-NNN` with a series tag (`D-FW-007`), `ADR-NNN` and `DEC-NNN` (prefixable the same way), optionally behind a bracketed tag (`[Phase 2B] D-0025`). A letter-suffixed id (`D-002b`) counts as a reuse of its base number. Reports count, distinct ids and max per series; **FAIL** on any id used twice at the same level, whichever level carries the ids. WARN when every id sits at `###` level. WARN when the file has headings but none carries a recognisable id — a project convention the doctor cannot census, or entries without ids. INFO *empty is fine* only when there are no headings at all. | Two bodies at one address is how a register contradicts itself. Propose a new numbered entry that names its target (`corrects D-XXXX`); never edit or merge the old ones. For the *no recognisable id* case, check the README for the project's convention and say there which form is used; the doctor cannot check what it cannot read. |
| `decisions-id-reuse` | `##` ids reused with a qualifier at `###` level ("D-032 correction"). WARN. | The same defect in softer form; the fix is the same new-number entry. |
| `decisions-id-level` | Ids minted below `##`. INFO for ids at `###` level with no `##` twin. **WARN** when any id sits at `####` or deeper (*ids at #### or deeper are invisible to a ##-only census; promote them*), with the count and the ids; those ids never enter the duplicate, order or gap census. | An id four levels down is a real decision a Bootstrap will never find. Promote the heading to `##` (or `###` if that is the project's convention, said in the README) — the entry's body and number do not change, so append-only is not broken. |
| `decisions-order` | Whether numbers run ascending (the template's rule), descending (consistent, note it in the README), or mixed (WARN), judged within each prefix series. | Mixed order means insertion out of sequence or reused numbers; check the ids line first. |
| `decisions-gaps` | INFO: unused ids inside each series' span, counted arithmetically (no span is ever materialised). | Harmless unless something cites them. |
| `decisions-template-residue` | Headings still reading `D-NNNN` / `ADR-NNN` / `YYYY-MM-DD` **with no real id** — a heading that carries a real id (`## D-002 — migrate YYYY-MM-DD parser`) is an entry, never residue, and enters the duplicate census like any other; headings inside code fences; and placeholder tokens such as `<decision in one line>` or `[POPULATE` outside fences. WARN. Headings are matched with up to three leading spaces, as CommonMark allows. | Template example blocks that were never deleted. Safe to remove; they distort id counts and confuse a Bootstrap. Template residue is not an entry; deleting it is not a retroactive edit — say so in the Close's CHANGELOG line. |
| `brand-placeholders` | `[POPULATE` markers in BRAND.md, and whether the file has changed since install day. WARN on any marker. | A BRAND with only placeholders is never filled in later (8 of 14 in the audit were untouched after install day). Propose one real value or deleting the file. |
| `nested-register` | Another STATUS/CHANGELOG/DECISIONS set in an ancestor directory (or its `docs/`). WARN. Siblings — a second set beside the one read — are the next line. | Two registers with no ownership rule is how a session writes to the wrong one. Propose writing which register owns this work into **both** READMEs. |
| `sibling-register` | A second full register at the other candidate location: at the root when the register read is under `docs/`, or under `docs/` when it is at the root. WARN, naming which set the doctor read. | Same hazard as nesting, one directory apart, and the pre-install interview's question 7 exactly: decide which register owns this work, write it into both READMEs, and retire or archive the other — never let sessions pick by proximity. |
| `git-repository` | INFO: whether the project root is the repository root, or nested inside a larger repository. | Nested roots share one index with everything above them — relevant to the one-writer rule. |
| `git-status-churn` | With git only: deleted/added lines over commits touching STATUS. WARN below 0.2 over 10 or more commits; INFO under 10 commits; SKIP without git. | Churn near 0.7–0.8 is a file being rewritten; near 0.1 is a file being appended to. The measured split in the audit was exactly this: every root with the wiring block rewrote, every root without it accreted. Fix the wiring first. |

### Acting on it

1. **Read every line, not just the FAILs.** A FAIL on `status-session-stack` with a FAIL on `wiring-block` is one problem, not two — the unwired project invented its own writer instruction. Say that.
2. **Propose, in the order that stops the bleeding:** wiring (Install step 2) → writer instruction → compaction → residue clean-up. Present each as a named alternative with what it trades off, and let the owner decide.
3. **Every fix is a Close.** The CHANGELOG entry for "re-synced the wiring block" or "compacted STATUS: N items retro-logged" is written first; STATUS is rewritten second. Doctor's own output is not a CHANGELOG entry — summarise what was found and what changed, not the transcript.
4. **Re-run after the fix.** The owner's evidence that the fix landed is the exit code, not the session's word for it.
5. **Do not fix what Doctor did not flag** and do not treat INFO lines as work. Restraint is part of the protocol.

### What Doctor does not check

Whether the content is true — a STATUS that is 40 lines of stale in-flight items passes. Whether DECISIONS entries contradict each other. Whether GLOSSARY matches usage. Whether project-authored close instructions are actually equivalent to the block — it reports them, and the session reads them. Those remain Bootstrap's judgement calls, and the one short confirmation with the owner ("Still focused on X?") is still the last step before substantive work.

---

## Mode 5 — Brief (turn open questions into decisions)

A brief is the ritual that moves a question from STATUS's "Open questions (owner)" into DECISIONS. Measured across installs, owners keep such a list (6 of 24 invented one unprompted), but the answers rarely arrive as decisions: the largest register stacked six "open for the owner" sections and three "answered" sections in ten weeks, none of which was ever merged, removed or turned into a numbered entry. Brief is the missing step between asking and recording.

**Triggers.** On demand, when the owner addresses the agent: "brief me", "what do you need from me", "what are you waiting on", "what decisions are you waiting on". If nothing is askable, say so in one line and stop. **Offered at Close** — one line, never forced — only when at least one item is *askable*: an Open question not marked postponed or declined (or whose revisit condition has arrived) and not still in square brackets, or a Blocked row whose blocker is the owner. Otherwise say nothing at Close. A blocker gated on a third party has nothing to ask; a postponed question re-offered every close teaches the owner to ignore the offer; a "nothing open" line printed every session is the unenforced ritual that decays into noise. A declined offer gives every askable line it covered "— declined YYYY-MM-DD"; a marked line is not re-offered until the owner asks or the line changes. An arrived revisit condition is offered with, in the same line, why the agent thinks it arrived; "not yet" re-postpones it with a new date. **Never manufacture a question**: a brief draws only from the registers, not from what the agent would like to ask.

### Read

If this session already bootstrapped, go straight to the questions — do not re-read what Bootstrap read. Otherwise:

1. **STATUS** — "Open questions (owner)" in full; Blocked rows whose "Blocked by" is the owner; Deferred rows whose reason has lapsed (the "deferred to" date or condition has passed) — read on demand only; the Close-time offer does not fire on them (a Deferred row is deferred work, not an owner choice — it becomes askable only when the owner is what it waits on). A line whose question is still in square brackets is template residue, not a question — delete it at the next Close, never brief it.
2. **The last 3–5 CHANGELOG entries** — work since the question was written may have answered or dissolved it; if a question is older than the entries read, grep CHANGELOG for its key terms as well. A dissolved question is dropped, with one line saying which entry dissolved it.
3. **DECISIONS — search, don't skim.** For each question, grep the register for its key terms (`grep -n -i '<term>' DECISIONS.md`); a missed entry re-opens a settled decision with options, which is the re-litigation the mode exists to prevent. When several entries match, the newest wins; follow `supersedes` / `corrects` pointers to the head of the chain before calling anything settled. A settled question is **not** presented with options. List it in the brief's preamble as "settled by D-XXXX (chose X); the only move is a supersession — say so if you want one."

### Present

One message, all questions numbered Q1..Qn, so the owner answers in one exchange ("Q1 the second, Q2 as recommended"). Each question in this fixed shape, no fields skipped:

- **Question** — one line, answerable by picking an option.
- **Context** — plain language, at most five sentences. Every piece of jargon is defined inline the first time it appears ("register — one of the append-only log files"), even if the owner coined it. A future reader without the conversation must be able to follow.
- **Options** — at least one real alternative to the recommendation, plus "do nothing" whenever it has a cost, labelled by that cost. **Never add an option to reach a count.** Every option must trace to a register line, a prior exchange with the owner, or a finding, and the Options line says where each came from ("from the STATUS row", "you raised this at the last close", "from the audit's finding") — an option with no stated source is padding, and a reader of the DECISIONS entry can tell. Label each by what it prioritises and what it trades off, per the protocol's own rule: "Fix the live templates — append-only history first, accept stale one-shots", never "Option B". Each carries its pros and cons.
- **Recommendation** — one option, with the reason in one or two sentences. Never withheld: an agent that presents options without a view is offloading the work.
- **What would change the answer** — the fact, measurement or event that would make a different option right. This is what makes a later supersession legible.

A question with only one real option is not a question; it is a notice, and a notice is ordinary work: state it in the preamble as the plan, do it, and log it as work in CHANGELOG. It is never a decision and needs no answer, so it gets no number; when it retires a line the owner listed, the CHANGELOG line names it ("notice: <question line> — one real option, done as work, no pick required"). A question the agent can settle itself (implementation detail, naming, ordering) never reaches the brief.

### Record

**An answer is an explicit pick by the owner.** A question the owner did not address in their reply is unanswered: it stays in "Open questions (owner)" unchanged, gets no DECISIONS entry, and is listed in the CHANGELOG line as "Qn — not answered". Silence is not concurrence; the recommendation is not an answer; never infer a pick from the owner's tone or from "do the rest as you see fit" — ask again, in one line, for the specific numbers. Ask once and wait for the reply within the exchange; record whatever is explicit after that — one CHANGELOG entry, with the still-unanswered questions listed as not answered. Answers that arrive in a later session are a new brief. DECISIONS is append-only, so an entry minted from silence is permanent. With the explicit picks in hand, record in this order: **CHANGELOG, then DECISIONS, then STATUS.** This is deliberately not Close's STATUS-before-DECISIONS: the STATUS rewrite removes the question, and the DECISIONS entry is the only other place it lives, so DECISIONS must exist before STATUS forgets it. CHANGELOG stays first. If the session dies after CHANGELOG, the brief entry names D-ids above DECISIONS' highest — Doctor's `changelog-decision-refs` line flags it, and the repair is writing the missing entries under those ids, since the log named them first.

1. **CHANGELOG first — one entry for the whole brief**, not one per question: `## YYYY-MM-DD — brief: N of M questions answered; D-XXXX–D-YYYY logged` (omit the D-range when no entry was logged: `brief: 2 of 5 questions answered; no decision entries`), then one line per question giving the answer and where it was recorded, or "not answered". This is the record the owner asked for: what was asked, what was chosen, what happens next.
2. **DECISIONS — one entry per answer that rejected a real alternative**, in the protocol's format, numbered from the highest existing id. **Reasoning** records the owner's stated reason in their words. It names as rejected only the alternatives the owner said were live — in their reply, or in answer to the liveness question — with the reason they gave (an alternative the owner calls live without a reason is recorded as "live for the owner; no reason given" — never supply one); every other presented option is listed as "presented, not chosen" followed by the agent's one-line assessment, marked as the agent's. No reason is ever attributed to the owner that the owner did not give. **If the owner's pick came without saying which alternatives were live, ask once, in one line, covering every presented alternative — "were any of <X>, <Y> live for you?" — not only the strongest.** None → default, no entry (below). Some → record which, with the reason they give. **What would change the answer** becomes the entry's Consequences.
   - Answer stands with an existing entry → no new entry; the CHANGELOG line cites it.
   - Answer overturns an existing entry → a supersession entry, `supersedes D-XXXX`.
   - Answer is a **default** — the owner says no other option was ever live for them, or the brief had only one real option → **no DECISIONS entry**; say so in the CHANGELOG line ("default, no decision entry").
3. **STATUS rewritten** — every answered question leaves "Open questions (owner)"; an unblocked item moves to In flight or Next; a question the owner explicitly postponed stays, with "postponed by owner YYYY-MM-DD, revisit when <condition>"; an unanswered question stays exactly as it was. Never leave an "answered" section behind — that is the stacking failure this mode exists to prevent.
4. **Then move.** State the next concrete action the answers unlock, in one line, and do it or queue it in Next.

### How Brief differs from Bootstrap's "confirm current state"

Bootstrap step 6 checks **facts**: is STATUS current, did anything land, is the focus unchanged. Its answers are yes/no/corrections and land in STATUS. Brief resolves **choices**: which of several defensible paths to take. Its answers are selections between named alternatives and land in DECISIONS. Keep them apart: a confirm exchange that surfaces a choice does not become a brief on the spot — it parks the choice in "Open questions (owner)" and offers a brief; a brief does not re-verify facts already confirmed.

### Common failure modes

- **Silence read as concurrence.** The owner answered Q1 and Q2; the agent logged entries for Q3–Q5 "as recommended". Append-only makes that permanent.
- **Options padded to a count.** An option nobody proposed appears in Reasoning as "rejected", and the entry records a deliberation that never happened.
- **Reasons attributed to the owner that the owner never gave.** Reasoning carries the owner's words for the alternatives they called live; everything else is the agent's assessment, marked as such.
- **Options without a recommendation**, or a recommendation without a reason. Both leave the owner doing the agent's job.
- **Re-opening a settled decision** because the owner's phrasing sounded like a question. Grep DECISIONS before presenting anything.
- **One CHANGELOG entry per question.** A brief is one unit of work; five entries for one exchange is noise that hides the record.
- **Recording the owner's answers in STATUS** as an "answered" section instead of DECISIONS. STATUS is a dashboard; answers are history.
- **Jargon left undefined** because the owner knows it. The brief is also the record a future session reads cold.

---

## Operating principles

**Append-only discipline.** CHANGELOG and DECISIONS are never edited retroactively (placeholder entries that were never used are template residue, not entries). Wrong entries get appended corrections or supersessions — the audit trail is the point.

**Heavy edits concentrated in STATUS.** STATUS is the one file edited aggressively — rewritten, never appended to; everything else grows monotonically. This split is the design property that makes the discipline survive, and it fails silently the moment a project starts prepending session records to STATUS: the file becomes a second append-only log with no protection.

**STATUS stays around ~40 lines and never over ~60.** Past that, something is miscategorized. A single line over ~1 KB is history in disguise.

**One writer at a time.** The protocol assumes a single session writes the registers. Parallel agents on one working tree defeat its id allocation ("check the highest number" is not atomic), its append discipline (uncommitted work in a shared tree is not durable), and any sense of who owns STATUS. Isolate concurrent agents in their own worktrees; do not add lanes to a shared tree and expect the registers to survive.

**Prose over bullets unless bullets earn it.** Tables for genuinely table-shaped data (status rows, glossary); not as a substitute for two sentences of explanation.

**No marketing language in internal docs.** The reader is future-self or future-agent, not an investor.

**Name alternatives when presenting options.** Label each by what it prioritizes and trades off — "Ship fast, accept debt" vs. "Ship slow, compound maintainability" — not "Option A" vs. "Option B."

Per-project workflow norms (commit conventions, session hygiene) live in the project README's "Working preferences" section, not here — see the README template.

---

## Files in this skill

- `SKILL.md` (this file) — all operating instructions for the five modes.
- `templates/` — the starter files. Copy these when installing.
- `scripts/docs-doctor.py` — the Doctor check. Python 3 standard library, read-only, git optional.
- `docs/` — this skill's own registers (it runs the protocol it ships), the anonymised audit evidence, and a worked Brief.
