# project-docs-protocol

A lightweight documentation protocol for multi-session, multi-month projects — built as an [agent skill](https://www.anthropic.com/news/skills) for Claude Code and compatible with Codex/AGENTS.md-based agents.

The problem it solves: working with an AI agent across many sessions on the same project, state gets lost between sessions. Either you re-explain context every time, or the agent guesses and gets it wrong. This protocol gives the agent a small, disciplined set of files to read at the start of a session and write to at the end, so continuity survives the gap.

## How it works

Two rituals, three core files, one design property that makes the whole thing hold up over time:

- **Bootstrap** (session start) — read `STATUS.md` in full, skim the last few `CHANGELOG.md` entries, check `DECISIONS.md` for anything relevant. Confirm state with the user before starting work.
- **Close** (after each meaningful unit of work, not just at session end) — append a `CHANGELOG.md` entry first, then update `STATUS.md`, then log a `DECISIONS.md` entry only if a real alternative was rejected.

The core design property: **`CHANGELOG.md` and `DECISIONS.md` are append-only; `STATUS.md` is the one file edited aggressively every session.** Append-only logs can't be corrupted by a bad edit and survive a session that dies mid-update — CHANGELOG is written *first*, before STATUS, for exactly that reason. Splitting the "grows forever" content from the "gets rewritten constantly" content is what keeps the system from decaying into either a bloated status file or a lost history.

Everything else — `ROADMAP.md`, `GLOSSARY.md`, `BRAND.md`, a spec template — is optional scaffolding for projects that need it, seeded only when it's actually used.

## Install

This repo *is* the skill. Drop it wherever your agent looks for skills:

```bash
git clone https://github.com/anthonylim9913/project-docs-protocol.git ~/.claude/skills/project-docs-protocol
```

For Codex or another `AGENTS.md`-driven agent, symlink it in instead of duplicating:

```bash
ln -s ~/.claude/skills/project-docs-protocol ~/.codex/skills/project-docs-protocol
```

Then, in any project, ask your agent to "set up project docs" (or "bootstrap this project," "cold start," etc. — see the trigger phrases in `SKILL.md`). It'll run an install interview, copy the templates from `templates/`, and — the part that makes it actually stick — append a short block to the project's `CLAUDE.md`/`AGENTS.md` so bootstrap and logging happen automatically every session, instead of depending on the agent noticing on its own.

## Files

- **`SKILL.md`** — the operating instructions: when to trigger, and the full walkthrough for each of the three modes (install / bootstrap / close).
- **`templates/`** — the starter files copied into a new project: `README.md`, `STATUS.md`, `CHANGELOG.md`, `DECISIONS.md`, `ROADMAP.md`, `GLOSSARY.md`, plus optional `BRAND.md` and `SPEC_TEMPLATE.md` for projects that need them.

## Status

Built for and dogfooded on my own multi-session projects. Sharing as-is in case the pattern is useful to others — issues and PRs welcome, but treat it as a personal tool that's now public rather than a maintained product.

## License

[MIT](LICENSE)
