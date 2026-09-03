# CHANGELOG

*Append-only history of what happened and why. Reverse chronological — newest on top. Never edit past entries; append corrections instead. Entry and correction formats: see the templates' README.md.*

---

## 2026-09-03 — templates: STATUS cut to 37 lines with Next and Open-questions sections; DECISIONS order fixed; README trimmed and given a correction form

STATUS template dropped five horizontal rules and the note-plus-table duplication in Blocked (35 of 44 lines were chrome; a one-row fill exceeded the protocol's own 40-line rule) and gained `## Next` and `## Open questions (owner)`, which 6 and 7 of 24 installs had invented independently under other names. DECISIONS template now states entry order (bottom, oldest first; installs had split 14/7) and forbids reusing a number with a qualifier. README template: CHANGELOG corrections address by summary or token instead of date (the date form was used 0 times across 25 roots and is ambiguous for 90–98% of entries); a DECISIONS correction form added (the protocol mandated corrections in three places and formatted none); the Commits and External-comms subsections deleted (16 of 16 installs that kept the section had deleted both). Report recs 3, 5, 7.

## 2026-09-03 — SKILL.md: how STATUS is edited, precedence, a bounded bootstrap read, red flags that discriminate, single-writer assumption, nested-register question

The Step-2 wiring block now says STATUS is rewritten rather than appended and that the three design properties (CHANGELOG first, STATUS rewritten, registers append-only) are not overridable by project convention — measured across every install, the presence and wording of that block predicted STATUS churn (0.67–0.83 with it, 0.01–0.16 without or with a "top line" variant). Bootstrap step 1 reads STATUS in full only under ~60 lines (the full read cost ~153,000 tokens on the largest file). Red flags: threshold moved to ~60 lines (the literal 40 fired on 23 of 25 roots and on the template itself), a max-line signal added (one STATUS carried a 36 KB single line), stacked session records named, dormancy-on-return added. Mode 3: step 2 says rewrite; step 3 says corrections take a new number; the compaction trigger is size-based instead of quarterly (quarterly had fired once in 25 projects). Operating principles gain "one writer at a time". Install interview gains the BRAND value gate (8 of 14 BRAND files were never touched) and a nested-register question. Report recs 1, 2, 3, 4 (trigger only), 6, 8.

## 2026-09-03 — baseline tagged v0.1.0; work branch opened; share-bundle installer guarded

Tagged the pre-audit state as `v0.1.0` (first tag; the repo had two commits and no version). Opened `audit-2026-09-02` so `main` stays at the baseline until reviewed. Patched `~/.codex/skills/Share Skills/project-docs-protocol-share/install.sh` (outside this repo) to refuse a symlink or git-clone target and to back up rather than `rm -rf` — its default mode would have replaced the Codex symlink with the July snapshot, and `--claude` would have deleted this clone.

## 2026-09-03 — initialized project documentation system

Installed the project-docs-protocol on itself at `docs/`, seeded from the 2026-09-02 audit (not approximate: the in-flight items are this session's own work). BRAND.md omitted; no brand dimension. SPEC_TEMPLATE.md omitted; not spec-driven. GLOSSARY and ROADMAP omitted for now — the protocol's own terms are defined in SKILL.md and its roadmap is the audit report's ranked list.
