# project-docs-protocol

Three small files an AI agent reads at the start of a session and writes at the end, so a project's state survives the gap between sessions instead of being re-explained every time or guessed wrong. It ships as an [agent skill](https://www.anthropic.com/news/skills) for Claude Code and works with Codex and other `AGENTS.md`-driven agents.

The whole thing rests on one design property. `CHANGELOG.md` and `DECISIONS.md` are append-only registers: they only ever grow, so a bad edit cannot corrupt them and a session that dies mid-update leaves them intact. `STATUS.md` is the opposite, a short dashboard that is rewritten at every close and never appended to. And at close the CHANGELOG entry is written first, before STATUS is touched, so that if only one write gets through it is the one carrying the history. Separating what grows forever from what gets rewritten constantly is what stops the system decaying into either a bloated status file or a lost history. Everything else, a roadmap, a glossary, a brand sheet, a spec template, is optional scaffolding seeded only when a project needs it.

## Measured, not asserted

Before this release the skill was audited, read-only, against every project on one machine that carried its three signature files: 25 in the dated 2026-09-02 census, which excludes worktree copies and review directories. Signature files do not establish installation provenance; some roots predate the skill. The anonymised evidence sheet ships in `docs/EVIDENCE.md`; the full report stays private.

- **The wiring block tracks the intended write pattern.** In the dated sample, projects whose instructions file carried the block rewrote STATUS (churn 0.67–0.83); projects without it or with a “top line” variant accreted history (0.01–0.16). This is an association across a small, provenance-mixed sample, including compatible hand-written instructions; it is not causal proof that this exact text produced the result.
- **Append-only held without enforcement.** The largest CHANGELOG in the population had 11,369 lines added over its committed history and 1 line deleted. Nothing checks this; the instruction alone did it.
- **The entry format transferred by itself.** 1,017 of 1,029 CHANGELOG headings across the population carry a date in the template's shape, 98.8%, with no linter, hook or check anywhere.
- **A mature install stays small.** The one installation with real age, 91 entries over 125 days, had a STATUS of 42 lines. The template is 39 lines.

The audit also found things wrong, and they are worth stating plainly. The bootstrap red flag "STATUS over ~40 lines" was true in 23 of 25 projects, including the skill's own template, so it carried no signal; the threshold is now ~60 lines, with a second signal for any single line over ~1 KB, which is history in disguise. The instruction to compact STATUS "once a quarter" fired exactly once in 25 projects; compaction is now triggered by size and by the red flags, not by the calendar. The skill triggered on three matching filenames alone, which pulled in registers it had never installed; the signature is now narrower (see "When it fires"). The wiring block never actually said that STATUS is *rewritten*, the property the churn numbers show matters most, so it says so now, with a precedence clause that stops project convention from quietly overriding it. And the brand template was never filled in on 8 of the 14 installs that kept it, so Install now asks for one concrete value before keeping it. Version 0.2.0 is the response to those findings.

## The modes

**Install** runs once per project. It asks a short set of questions in one exchange (project name, where the docs live, whether the project is new or mid-flight, who reads the docs, whether brand and specs matter, whether a register already exists above this folder, whether a long findings list needs a ledger, and whether the project depends on other skills), then copies the templates into place and personalises them. The step that makes it stick is the wiring block appended to `CLAUDE.md` or `AGENTS.md`, so that bootstrap and logging fire from the instructions file every session instead of depending on the agent noticing a trigger phrase. STATUS is seeded from whatever context exists, flagged as approximate; the installation is logged as the first CHANGELOG entry; DECISIONS starts empty unless adopting the protocol was genuinely weighed against an alternative.

**Bootstrap** runs at the start of every session on an installed project, before any work is proposed. The agent reads STATUS in full while it is under ~60 lines and only its top line, headings and current-state sections past that; then the last three to five CHANGELOG entries, following any decision IDs they reference into DECISIONS; then skims DECISIONS for anything touching the area at hand, without re-litigating what was already decided. It uses the glossary as a dictionary if one exists, reads live LEDGER rows when installed (never the archive at Bootstrap), then the skill registry and a bounded slice of the research index when those are installed, then confirms current state with the user in one short exchange, since STATUS can lag by a session. Bootstrap is also where the red flags fire: an oversized STATUS, stacked session records, a changelog that has gone quiet for a month, decisions that contradict without a supersession link.

**Close** runs after each meaningful unit of work, not just at session end, because sessions rarely announce their last message. The order is fixed. First the CHANGELOG entry: date, one-line summary, one to three sentences of what and why, appended at the top, never editing old entries. Second, LEDGER rows are updated if installed, with terminal rows archived and verified before live removal. Third, STATUS is rewritten: completed items out, new in-flight items in, blockers and deferrals updated, every past-tense sentence deleted because it is already in the entry just written. Then, a DECISIONS entry only if a real alternative was rejected; if the rejected alternative cannot be named, it was a default, not a decision. Trivial work gets no close at all; the protocol asks for one to three entries a session, not an entry per file touched.

**Doctor** (added in 0.3.0) is a read-only health check for an installed project: `python3 scripts/docs-doctor.py <project-root>`. It runs the bootstrap red flags as a script — wiring, STATUS, changelog and decision registers, and, when LEDGER.md is installed, table shape, dates, state invariants, evidence, archive ID collisions and staleness — and prints one line per check with the measured value, its unit and the threshold. Standard library only, works without git, never edits. Run it on demand, after an install, or when a red flag fires; not at every session start.

**Brief** (added in 0.3.0) turns the open questions STATUS carries into decisions. On demand, or offered in one line at close when there is something askable, it presents each question in a fixed shape — context with jargon defined, options labelled by what they trade off, a recommendation with its reason, and what would change it — and records the owner's explicit answers as DECISIONS entries with the rejected alternatives named. Silence is not an answer, options are never padded to a count, and a question already settled is presented as settled rather than re-opened. Brief records CHANGELOG, reserved DECISIONS entries when warranted, LEDGER updates if installed, then STATUS. A default can cite the Brief CHANGELOG entry without inventing a decision; unanswered execution gates remain open. A worked example is in `docs/BRIEF-EXAMPLE.md`.

## When it fires

Trigger phrases ("set up project docs", "bootstrap this project", "where were we", "close out the session", and the rest listed in `SKILL.md`) start the matching mode. Beyond phrases, the skill recognises an installed project by its signature: `STATUS.md`, `CHANGELOG.md` and `DECISIONS.md` at the root or under `docs/`, **and** either the "Project docs protocol" block in `CLAUDE.md`/`AGENTS.md` or the install footer in the docs README. The three filenames alone are not enough; Keep-a-Changelog plus an ADR folder produces the same three names. On a register it did not install, the skill says so and offers Install, which on an existing register means wiring and reconciling, not overwriting.

## Install

This repo *is* the skill. Drop it wherever your agent looks for skills:

```bash
git clone https://github.com/anthonylim9913/project-docs-protocol.git ~/.claude/skills/project-docs-protocol
```

For Codex or another `AGENTS.md`-driven agent, symlink it in instead of duplicating:

```bash
ln -s ~/.claude/skills/project-docs-protocol ~/.codex/skills/project-docs-protocol
```

Then, in any project, ask your agent to "set up project docs". It runs the install interview, copies the templates, and wires the block into the project's instructions file so the next session bootstraps on its own.

## Files

- **`SKILL.md`** — the operating instructions: when to trigger, and the full walkthrough for each of the five modes — Install, Bootstrap, Close, Doctor (the read-only health check, run by `scripts/docs-doctor.py`) and Brief (turns STATUS's open owner questions into DECISIONS entries with explicit picks).
- **`templates/`** — the starter files. Four documentation files plus project-level agent wiring form the minimal installation: `README.md`, `STATUS.md`, `CHANGELOG.md`, `DECISIONS.md`. `ROADMAP.md`, `GLOSSARY.md`, `BRAND.md`, `SPEC_TEMPLATE.md` and `LEDGER.md` (the tracker for a findings list too long for STATUS) are the optional scaffolding above — seeded when the project needs them, not by default. This skill's own register also uses the optional ledger for review findings.
- **`scripts/docs-doctor.py`** — the Doctor check.
- **`scripts/docs-migrate.py`** — reviewed STATUS-to-LEDGER reconciliation with stable source mappings and replayable writes; see [migration workflow](docs/MIGRATION.md).
- **`scripts/skill-registry.py`** — optional read-only validation for a project's `SKILL-REGISTRY.md`; absence is valid.
- **`tests/`** — discoverable standard-library tests (`python3 -B -m unittest discover -v` or `python3 -B tests/run_regression.py`); [coverage and limitations](tests/README.md).
- **`docs/`** — the skill's own registers. It runs the protocol it ships, so its STATUS, CHANGELOG and DECISIONS are a live example of the format; `EVIDENCE.md` holds the anonymised audit figures and `BRIEF-EXAMPLE.md` a worked brief.
- **`staging/research-protocol/`** and **`staging/architect-protocol/`** — the two optional companions: durable, provenance-tracked research records, and staged architectural work with a frozen subject, independent review and an evidence-backed handoff. A project vendors and registers one only when it needs it; neither is part of the global installation or the four-document minimum. How they combine with the core is in `SKILL.md` under *Optional companions*.
- **`templates/SKILL-REGISTRY.md`** — optional project skill inventory template; it does not activate or install skills.

## Status

Built for and dogfooded on my own multi-session projects, then measured on one machine before going public. Sharing as-is in case the pattern is useful to others. Issues and pull requests are welcome, but treat it as a personal tool that is now public rather than a maintained product. The dated observations describe one owner's working habits and do not establish that the design will hold for everyone.

## License

[MIT](LICENSE)
