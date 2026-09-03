# Evidence — the 2026-09-02 audit, at population level

On 2026-09-02 the protocol was measured, read-only, against every project on one machine whose folder carried its signature files. Sixteen investigation lanes and thirteen adversarial verifiers took every figure; the full report is private because it names projects, people and paths. This page carries what survives anonymisation: the population, the mechanisms, and the numbers with their units. Projects are described neutrally or by opaque labels (P01…). Nothing here identifies one.

Every count says whether it was taken from the working tree (the files as they sit on disk) or from committed history (git). Token figures are bytes ÷ 4, not tokenizer output.

## 1. The population

- **25 roots** carried `STATUS.md` + `CHANGELOG.md` + `DECISIONS.md` (working-tree census; worktree copies and one audit snapshot excluded). **14 of the 25 are in no git repository** at all, so for them only the working tree could be measured.
- The roots sort by *how they came to carry the signature*:

| Cohort | Roots | State found |
|---|---|---|
| Installed by the current skill text, wired into CLAUDE.md/AGENTS.md | 5 | STATUS 40–54 lines; 0 duplicate decision ids; 0 canned adoption decisions |
| Installed by an earlier (April) version of the skill, never wired by it | 10 | All carry the canned "adopt the protocol" D-0001 the current text forbids; the wiring step did not exist yet |
| Carry the three filenames but never ran Install | 9 | Three registers scaffolded by another agent tool in its own dialect, one family of four related product repositories, one game prototype with a hand-written register, one fresh experiment |
| Mature installations | **1** | 91 entries over 125 days; a member of the second cohort, wired by its own hand-written instructions file rather than the skill's block |

The three provenance cohorts sum to 24; the remaining root is a near-verbatim copy of one register packaged with a deliverable, counted in the census and not in the cohorts.

- Three of the four projects the audit brief named as "controls" were **one or two session-days old** (7, 10 and 9 entries on one or two dates). The only mature installation is n = 1.
- **The protocol has essentially never been tested at scale.** Every dramatic failure in the audit belongs to a system that was never wired to it (see §8). That is the frame for everything below; it is not an acquittal.

## 2. Maturity versus size

Entries are `## ` headings in CHANGELOG; size is STATUS bytes in the working tree.

- Across all 23 roots with at least one entry, entries vs STATUS bytes: **Spearman +0.75**. Excluding the four related-product roots (n = 19, none of which stack session records): **+0.674**.
- Mature roots (≥ 20 entries) sit at a median of **86.5 lines / 16.5 KB**; young ones at **59 lines / 3.2 KB**. Five of the six mature roots without stacked records exceed 60 lines. The one exception is the one mature installation (42 lines / 4,980 bytes), and it is n = 1.
- The largest project's STATUS is roughly an order of magnitude above what maturity alone predicts: **12.5×** on a log-log fit over the 19 roots, but that fit has R² 0.337 and the file sits four times beyond its largest input. Leave-one-out gives a range of **5.2× to 16.3×**. The sign is robust; the magnitude is proxy-dependent. Its parent register is ~10.8×; the mature installation is 0.3×.
- **The exposure variable was not "prepends session records".** Four roots with zero prepends are 47–71% retained past-tense history by bytes (71.1%, 60.1%, 50.7%, 46.8% — all game prototypes). Across all 23 roots, "retains history in STATUS" predicts STATUS bytes better than "uses prepends": **Spearman 0.757 vs 0.536**. Retained history is population-wide; the record stack is one project's dialect of it.
- Only 5 of 25 roots have any stacked session record at all, and **11 of the 16 roots over 60 lines have none**.

## 3. The largest STATUS file, decomposed

Working tree, 1,027 lines, 611,267 bytes.

| Component | Lines | Bytes | Share |
|---|---|---|---|
| Stacked "last session" records | 182 | 347,755 | 56.9% |
| Demoted records (prior / same-session / earlier) | 27 | 85,690 | 14.0% |
| Continuation bullets under those records | 143 | 58,945 | 9.6% |
| Emoji-prefixed deploy stack | 18 | 31,470 | 5.1% |
| **Whole history stack** | **370** | **523,860** | **85.7%** |
| Everything else (headings, prose, dashboard) | 373 non-blank | 87,123 | 14.3% |

Delete the entire stack and the file is still 373 lines and 87 KB — 9.3× the ~40-line target. A second accumulation channel the stack does not explain: eleven dated "known issues" sections, six "open for the owner" and three "answered" sections, appended per parallel lane and never merged — **263 lines, 55,797 bytes**. That is the protocol's own named failure mode (completed items never moved out) arriving through a door prepending does not touch.

Growth from committed history (114 commits touching the file): 87 lines / 1 record on day 0 → 344 / 80 forty-one days later with **no commits in between** → 1,025 / 181 after 71 days. Roughly 1.9 records/day early, 3.5/day during the first multi-lane period, 5.3/day at the end; 2.4 KB → 3.3 KB per record.

## 4. What determines whether STATUS is rewritten

Churn = deleted ÷ added STATUS lines over committed history (git-tracked roots only). It does not track whether the template's "past-tense content belongs in CHANGELOG" line survived — the roots at 0.83, 0.16 and 0.12 below all still carry it. It tracks the **agent-instructions file**:

| Root | Churn | What the instructions file says about closing |
|---|---|---|
| P03 — the one mature installation | 0.83 | hand-written file restating the close ritual in the protocol's own shape |
| P04 — a game prototype | 0.81 | the skill's wiring block, verbatim |
| P05 — a game prototype | 0.67 | hand-written: "1. Add a CHANGELOG entry. 2. Update STATUS." |
| P06 — a game prototype | 0.16 | no instructions file |
| P07 — a game prototype | 0.12 | no instructions file |
| P01 — the largest project | 0.12 | project-authored: read STATUS's "top line + current phase" |
| P02 — its parent register | 0.01 | project-authored: update the "top line" |

Every root whose instructions file orders CHANGELOG-then-STATUS rewrites STATUS. Every root with no instructions file, or one that names a "top line", accretes. The install step that writes that block is not documentation of the protocol; it is the mechanism. The pre-audit text contained zero occurrences of "replace", "rewrite", "overwrite" or "prepend" — it said what STATUS should contain and never how it is written — so a project could invert the design property without contradicting a word. The current text says it.

## 5. What held

1. **Append-only held almost absolutely, and line-count diffs understate it.** The right instrument is the multiset of every non-blank line ever committed to a register, asked how many are absent from the working tree today. Across the largest project's three append-only registers — CHANGELOG, DECISIONS and a third append-only decision log — over **311 commits** and **18,470 distinct committed lines**, exactly **9** are absent: 1 heading changed from `###` to `##` (disclosed in its own commit body), 1 decision id renumbered under a recorded owner decision with a 22-line receipt appended, and 7 status markers flipped from "pending" to "executed". All nine are address, heading-level or status markers; zero lines of substantive record were destroyed in git. The 48 DECISIONS "deletions" git reports are a block move, all re-added verbatim in the same commit. Caveat: this held in the repository while *uncommitted* work died in a shared working tree — 544 lines by the headline count, of which 330 were recovered in full and at most 143 are permanently lost. The guarantee's scope is committed history, and no documentation protocol supplies durability git does not.
2. **CHANGELOG-first is visible in commit timing.** All 17 CHANGELOG-only commits are followed by a STATUS commit, median **+7 minutes**; 9 of 13 STATUS-only commits have a CHANGELOG commit within 8 minutes before them — split closes, not skipped ones. One commit was paused by the owner mid-close: it landed CHANGELOG and DECISIONS, not STATUS, and recorded the owed STATUS update. The ordering rationale, working as written.
3. **The entry format transferred without enforcement.** **1,017 of 1,029** CHANGELOG headings across the 24 roots with entries carry a date — **98.8%**, with 17 roots at 100%. Nothing checks this anywhere. "Newest at top" holds in 22 of 24.
4. **Corrections-not-edits is a culture, not one project's habit.** **20 of 25** roots carry at least one correction, amendment, supersession or renumber heading; the five without are the five smallest by volume. In the largest CHANGELOG (11,401 lines, 367 entries): 11,369 lines added, **1** deleted, across 118 commits.
5. **"Name the rejected alternative" is followed in form.** Of 30 sampled DECISIONS entries across 7 projects, 22 name a real rejected alternative explicitly and none name none.
6. **"1–3 entries per session" did not decay.** 367 entries over 209 session records is **1.76 per session**; 95 of 118 CHANGELOG commits add exactly one heading. A per-day figure of 6.8 reflected 24 parallel sessions on one date, not oversized sessions.
7. **Signature detection kept the protocol running with no instructions file.** Eleven roots have neither CLAUDE.md nor AGENTS.md; they still carry protocol-shaped registers across real commit dates (15 CHANGELOG commits over 6 days; 18 over 4). The cleanest case is a post-rewrite research corpus with no instructions file anywhere: 9 entries, all correctly formatted, newest at top, last-updated maintained.
8. **The July rewrite's ban on a canned adoption decision worked.** 10 of 25 roots carry one, four sharing a near-identical skeleton; all 10 predate the rewrite, and **0 of the 9** roots installed after it carry one.
9. **The close ritual survived unattended execution.** A scheduled automation, under a prompt telling it not to modify source files, ran the close in order anyway: CHANGELOG patched, then STATUS fifteen seconds later.

## 6. What failed

1. **The ~40-line rule carried no signal.** Read literally it fired on **23 of 25** roots and on the protocol's own STATUS template (44 lines, 35 of them chrome). The largest file breached it at its *first* commit, at 87 lines, before any concurrency. The flag was raised **once** across the whole population — 55 days after that first breach, at 15.6× the threshold, by a lane doing a handoff rather than by a bootstrap.
2. **Compaction fired once in 25 projects.** "Once a quarter" had no trigger, owner, procedure or check. The one instance (+15 / −39, the largest single-commit STATUS deletion anywhere in the population) cut a STATUS from 70 lines / 12,218 bytes to 38 lines / 3,935 bytes; it was agent-proposed under the protocol's own wording and approved by the user with a single character. At the observed rate, "quarterly" permitted ~470 records between compactions. Leaving STATUS unprotected is also why that repair was possible: under an append-only rule it would have been forbidden.
3. **The protocol mandated DECISIONS corrections in three places and supplied a format for none.** The template README carried four forms (CHANGELOG entry and correction, DECISIONS entry and supersession); a correction is not a supersession. It permitted id-reuse-with-a-qualifier by omission. Measured: in the largest DECISIONS register, 205 headings, 199 distinct ids, **6 duplicated** (each an amendment or correction reusing its target's number) and 15 gap ids (8 of them decisions minted at `###`, invisible to a `##` census; 7 true gaps). In the parent register, **four ids resolve to more than one body** with no qualifier and no resolution entry — three to two bodies each, one to four.
4. **Date-addressed CHANGELOG corrections were used zero times across all 25 roots.** A date is ambiguous for **98%** of entries in the largest register, **90%** in the mature installation's, 98% in the parent's. The two installed roots that ever wrote a correction both abandoned the form.
5. **Bootstrap step 1 read STATUS in full, unconditionally.** On the largest file that is 611,267 bytes ≈ 153,000 tokens; steps 1 and 2 together **634,573 bytes (~159,000 tokens)** against **4,645–7,320 bytes** in the five wired installs — **87× to 137×** more expensive in the one root that never installed the protocol. The sentence that followed ("don't look for history in it") was false for that file and for 22 others.
6. **Smaller dead text.** "Flag seeded items as approximate": used by 0 of 10 install entries, contradicted by 3. BRAND.md: kept in 14 roots, **8 never modified after install day**; one carried 10 `[POPULATE]` markers after 124 days in a project that had a design-tokens spec. Two README subsections were deleted by **16 of 16** installs that kept the section. DECISIONS entry order was unstated; installs split 14 oldest-first / 7 newest-first. The dormancy flag fired on 1 root as written and on **12** measured as days since the last entry — what a returning session actually faces.
7. **No concurrency model, textually.** The pre-audit SKILL.md contained "session" 31 times and zero occurrences of subagent, parallel, concurrent, worktree or branch; its only allocator was "check the highest existing D-number". But the causal claim over-reached: across the seven commits that swept other lanes' work, protocol registers were **23 of 3,091 file-changes (0.74%)** — damaged at their population share of the tree. Both loss events happened on a shared git index; none happened in the one installation using worktree-per-agent isolation (9 worktrees, 0 recorded collisions).

## 7. Population tests of the replacement signals

Each candidate red flag was run against all 25 STATUS files before it was adopted or rejected.

| Signal | Fires on | Verdict |
|---|---|---|
| > 40 lines (the old rule) | 23 of 25 | no signal |
| > 60 lines | 16 of 25 | adopted as the flag |
| > 80 lines / > 100 lines | 10 / 7 | discriminates; 60 adopted, ~40 stays the target |
| Bare 4 KB byte cap | flags the best-behaved mature root (4,980 bytes) | **rejected** |
| "STATUS contains dated session records" | 5 of 25 | **rejected**: misses exactly the roots that need it — three game prototypes that are 47%, 32% and 22% history by line, with undated history headings |
| Any single line > ~1 KB | **12 of 25**, six of them game prototypes with no lineage to the largest project | **adopted** alongside the line flag |

The max-line signal catches what no line count can: one STATUS (91 lines, 45,537 bytes) folds thirteen sessions into a **single 36,130-byte line**.

## 8. The admissibility finding — a methodological lesson

The project that generated almost all of the evidence had **never installed the protocol**. No instruction file anywhere in its repository family — five files — carried the wiring block. Its docs README was a bespoke 23-line "five-file" system against the template's 107 lines and eight files. Its parent register was created **one day before** the earliest surviving copy of the skill; its own register **three weeks before** the current SKILL.md was written. It is the protocol's ancestor: a protocol-shaped system sharing the file names, predating the text, never wired to it. Three adversarial lanes reached that conclusion independently, each trying to break a different hypothesis.

The lessons, which changed the skill:

- **Three matching filenames are not the signature.** 9 of 25 roots had never run Install; elsewhere a Keep-a-Changelog file plus an ADR folder produces the same three names. The trigger now requires the wiring block or the install footer as well.
- **Sort the population by provenance before measuring the protocol against it.** The audit brief's own framing ("one protocol, five projects, one anomaly") was not the comparison the disk supported, and the first fact sheet repeated the error. Six of the brief's premises did not survive re-measurement.
- **Retained history is the population-wide mechanism, and it is protocol-level;** the stack that reached 611 KB was one project's dialect of it. The largest fix therefore went into the protocol, not into that project.
- The defects in §6 are real regardless: they were found in the protocol's own text and in installed roots, not only in the ancestor.

## 9. What could not be measured

- Whether the protocol works at scale: one mature installation, confounded by a daily human reader, a scheduled automation and a single compaction.
- The 41-day window in which 79 session records accumulated with no commits; the first act of non-removal cannot be dated.
- Whether zero *recorded* incidents means zero incidents; clean records may measure recording culture. Incidents per 1,000 CHANGELOG lines was not computed.
- The counterfactual: nothing shows any protocol change would have prevented any of the seven sweeps.
- True concurrency: the lock file records shell pids, not sessions. Tightest honest proxy: 19 distinct pids in one 60-minute window, 37 distinct lane labels in one day.
- The content of 298 CHANGELOG and 32 STATUS lines lost on one date — never staged, no blob.
- Steps 2–6 of Bootstrap, beyond "newest at top" (22 of 24) — not assessed.
- Gate exit codes at audit time (read-only rules); token counts (bytes ÷ 4).
