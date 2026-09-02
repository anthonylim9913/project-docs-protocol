---
name: project-docs-protocol
description: "Lightweight documentation protocol for multi-session projects. Use when the user wants to bootstrap project docs, resume work on an existing project, or log completed work. Triggers on: 'set up project docs', 'initialize docs', 'install the project docs protocol', 'cold start', 'coldstart', 'bootstrap this project', 'catch me up on <project>', 'resume work', 'where were we', 'close out the session', 'log this session', 'update the changelog', and whenever a project folder contains STATUS.md + CHANGELOG.md + DECISIONS.md at the root or under /docs/ (the signature of an installed project-docs-protocol system)."
---

# Coldstart — project documentation protocol

This skill installs and operates a small-file documentation protocol designed for multi-session, multi-month projects where continuity across sessions is the main cost. The protocol is portable — it works for any project, not a specific one.

## When to use this skill

Invoke automatically, without asking, in any of these situations:

1. **User asks to set up project docs** for a new or existing project. Phrases like "set up the docs folder," "initialize project docs," "install the project-docs-protocol system," "bootstrap this project." → Run **Install**.
2. **User returns to work on a project** whose root (or `/docs/`) contains `STATUS.md`, `CHANGELOG.md`, and `DECISIONS.md` — the signature of an installed system. Always run **Bootstrap** before proposing work.
3. **A meaningful unit of work just completed** on such a project — a spec drafted, a decision made, a blocker resolved, a major refactor landed. Run **Close** immediately; don't wait for the session to end. Session-end phrases ("close out," "log the session," "let's wrap") also trigger Close as a catch-all.
4. **User asks to catch up or resume:** "where were we on X," "catch me up on X," "resume work on X." → Run **Bootstrap**.

**If a resume-style phrase fires but no signature files exist** in the project, don't hunt indefinitely — say the protocol isn't installed here and offer Install instead.

---

## Mode 1 — Install (cold start a new project)

### Pre-install interview

Ask these before creating any files (or confirm from memory/conversation). Keep it to one exchange; don't over-interrogate.

1. **Project name.** The canonical name used in prose, plus any shorthand.
2. **Doc location.** Default: `/docs/` at the repo root. Alternatives: `./` (root) for small projects, `~/<project>/docs/` for non-code projects.
3. **Current phase.** Truly new, or mid-flight? Mid-flight installs seed STATUS with approximate in-flight items (flagged as approximate).
4. **Primary reader.** Default: the user + future agent sessions. Formality target: "wouldn't embarrass in a review." Any additional reviewers?
5. **Does brand matter?** If the project has a brand dimension (products, public comms, design assets), keep BRAND.md. Otherwise skip it — don't keep placeholder files that rot.
6. **Spec-driven?** If the project will use written specs, confirm the spec ID prefix (default `PROJ-SPEC-NNNN`) and include SPEC_TEMPLATE.md. Otherwise skip it.

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

Personalize each template with the project name, reader audience, working preferences, and any initial content you can infer. Leave `[POPULATE]` markers where specific input is required.

### Step 2 — Wire up auto-triggering

This is the step that makes the protocol survive. Skill-trigger phrases are unreliable; instructions files are loaded every session. Append this block (adjusted for the actual docs path) to the project's agent-instructions file — `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex and other agents. Update whichever exist; if neither exists, create the one(s) matching the tools the user works with — when in doubt, create both with identical content:

```markdown
## Project docs protocol

This project uses the project-docs-protocol (docs in `<docs-path>/`).

- **Session start:** before proposing or doing any work, read `STATUS.md` in
  full and the last 3–5 entries of `CHANGELOG.md`; skim `DECISIONS.md` for
  entries touching the area you're about to work on.
- **After each meaningful unit of work** (spec drafted, decision made, blocker
  resolved, major refactor): append a CHANGELOG entry, then update STATUS.
  Do this as you go — do not wait for the session to end.
- CHANGELOG and DECISIONS are append-only: never edit past entries; append
  corrections or supersessions instead.
```

### Step 3 — Seed from existing context

Pull whatever you have from memory, prior conversation, or user input:

- **STATUS:** seed the in-flight table with approximate items, **flag them as approximate**, and note that the next session should confirm.
- **GLOSSARY:** populate terms you know, sectioned by the project's domains. Incomplete is fine — empty is bad. But don't over-seed: 15 terms that match reality beat 80 aspirational ones.
- **ROADMAP:** fill near-term detail if you have it; sketch later phases vaguely.
- **BRAND** (if kept): fill what's known, `[POPULATE]` the rest.

### Step 4 — Log the installation

Append to CHANGELOG:

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

1. **`STATUS.md` in full.** The current-state dashboard: current phase, in-flight (owners, blockers), blocked (what gates each), deferred (why). Past-tense content doesn't belong here, so don't look for history in it.
2. **Last 3–5 entries of `CHANGELOG.md`** (newest at top). Three is usually enough; go to five if recent sessions were light or the thread is hard to follow. Watch for corrections to earlier entries (they flag where the mental model was wrong) and referenced decision IDs — follow those into DECISIONS.md.
3. **`DECISIONS.md` — skim, don't read whole.** Look for: decisions touching the area you're about to work on, decisions referenced in recent CHANGELOG entries, and the most recent 2–3 regardless of topic (they often set frame). **Do not re-litigate resolved decisions.** If a D-entry chose X over Y, build on X; if the user wants to revisit, the move is a supersession entry, not a rewrite.
4. **`GLOSSARY.md` as a dictionary** — look up terms you don't recognize; don't guess and don't ask the user for a term defined here. Project definitions override general knowledge. Watch for flagged overloaded terms.
5. **`SPEC_TEMPLATE.md`** only if the session involves authoring or reviewing a spec.
6. **Confirm current state with the user** before substantive work — STATUS can lag by a session. One short exchange ("Still focused on X? Anything land that isn't in STATUS?"), not an interrogation.

Only after bootstrap: propose what you're going to do — proposals now fit where the project actually is, not where you assumed it was.

### Red flags during bootstrap

- **STATUS well over ~40 lines.** Something is miscategorized. Flag it gently; suggest moving stale items to CHANGELOG or deferred.
- **CHANGELOG has a multi-month gap.** Discipline slipped. Ask whether to write a catch-up entry before continuing.
- **DECISIONS entries contradict without supersession links.** The log has lost integrity — flag it.
- **GLOSSARY contradicts usage in STATUS.** Glossary is authoritative; ask whether the definition is stale or the usage is wrong.

Fixes for all of these are small close-ritual adjustments, not a redesign.

---

## Mode 3 — Close (log completed work)

Run this **immediately after each meaningful unit of work completes** — not only at session end. Sessions rarely announce their final message, so a close deferred to "the end" often never happens; logging as you go is what makes the protocol survive interruption. Session-end phrases from the user trigger a final catch-all pass.

If the work was trivial (one-off question, no artifacts, no decisions), no close is needed — don't manufacture an entry to show you did the protocol.

**Order matters.** If the session dies mid-update, the append-only log is what survives:

1. **Write the CHANGELOG entry first** (append to top — formats are in the project README): date, one-line summary, 1–3 sentences of what and why. Never edit old entries; append a correction instead.
2. **Update STATUS.md second.** Move completed items out of in-flight; add new in-flight items; add/remove blockers (log unblocks in CHANGELOG) and deferrals (with reasons); bump the last-updated date. Keep STATUS under ~40 lines — past that, something is miscategorized: an in-flight item that's really deferred, a resolved blocker, completed items never moved out.
3. **Add a DECISIONS entry only if a non-obvious choice was made.** Test: can you name the rejected alternative the user actually considered? If not, it's a default — don't log it. Context → Decision → Reasoning → Consequences, numbered sequentially (check the highest existing D-number first).
4. **ROADMAP, BRAND, GLOSSARY, README** only when the session's work required it: ROADMAP at phase boundaries; BRAND on visual/voice changes; GLOSSARY for new, stale, or overloaded terms; README for working-preference or convention changes. Restraint is part of the protocol.

### What counts as CHANGELOG-worthy

A spec drafted/reviewed/ratified, a decision made, a blocker resolved, a major refactor or scope change, an audit finding or dependency shift. **Not:** every file touched, every paragraph edited. Aim for 1–3 entries per session; if you have 10, compress them into meaningful units.

### What counts as DECISIONS-worthy

Non-obvious tradeoffs where a reasonable alternative was rejected: scope decisions, framework/tool choices with real tradeoffs, audience or formality calls, supersessions of earlier decisions. **Not:** routine implementation choices, renames, or anything with no alternative actually under consideration.

### Common failure modes

- **Close skipped because "nothing substantive happened."** If an artifact was created or a decision made, close. The bar is lower than you think.
- **STATUS updated before the CHANGELOG entry.** Wrong order — the append-only log must be the thing that got through if the session dies.
- **A default logged as a decision.** No nameable rejected alternative → no entry.
- **STATUS grows unbounded.** Once a quarter, compact: retro-log completed items to CHANGELOG, demote stale in-flight to deferred.

---

## Operating principles

**Append-only discipline.** CHANGELOG and DECISIONS are never edited retroactively. Wrong entries get appended corrections or supersessions — the audit trail is the point.

**Heavy edits concentrated in STATUS.** STATUS is the one file edited aggressively; everything else grows monotonically. This split is the design property that makes the discipline survive.

**STATUS stays under ~40 lines.** Past that, something is miscategorized.

**Prose over bullets unless bullets earn it.** Tables for genuinely table-shaped data (status rows, glossary); not as a substitute for two sentences of explanation.

**No marketing language in internal docs.** The reader is future-self or future-agent, not an investor.

**Name alternatives when presenting options.** Label each by what it prioritizes and trades off — "Ship fast, accept debt" vs. "Ship slow, compound maintainability" — not "Option A" vs. "Option B."

Per-project workflow norms (commit conventions, session hygiene) live in the project README's "Working preferences" section, not here — see the README template.

---

## Files in this skill

- `SKILL.md` (this file) — all operating instructions for the three modes.
- `templates/` — the starter files. Copy these when installing.
