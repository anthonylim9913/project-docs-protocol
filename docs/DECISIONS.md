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
**Reasoning:** Rejected a bare 4 KB byte cap: it flags the one mature installation that kept discipline, while passing nothing it should. Rejected "no dated session records in STATUS": it fires on only 5 of 25 roots and misses three game prototypes that are 47%, 32% and 22% history by line — their history headings carry no date. The max-line signal fires on 12 of 25 including the one file that folds thirteen sessions into a 36 KB line and would pass any line cap.
**Consequences:** "~40 lines" survives as the target; "never over ~60" is the flag. The template was cut to 37 lines so a one-row fill sits under the target.

## D-0003 — 2026-09-03 — the three design properties outrank project convention; everything else is the project's

**Context:** The protocol had no precedence rule. The largest project inverted the STATUS design property through its own always-loaded CLAUDE.md ("top line") without ever contradicting the protocol's text, and nothing said which file won.
**Decision:** CHANGELOG-before-STATUS, STATUS-rewritten and registers-append-only are the protocol's and are not overridable; paths, id formats and entry shapes belong to the project's block.
**Reasoning:** Rejected "the project file always wins": it re-licenses exactly the inversion that produced a 611 KB STATUS. Rejected "the protocol always wins": it would override legitimate local choices (docs path, a project-prefixed id scheme, entry shapes) and give projects a reason to stop wiring the block at all. The three properties are the ones the audit measured as load-bearing; the rest were never the problem.
**Consequences:** The wiring block carries a Precedence bullet. A disagreement on a property is to be logged as a CHANGELOG entry, so it gets resolved rather than inherited.

## D-0004 — 2026-09-03 — concurrency gets one stated assumption and a pointer, not an annex and not a second protocol

**Context:** The protocol has no concurrency model (zero occurrences of parallel, worktree, branch, lock). The one repository that ran 5–37 lanes on a shared tree accreted eleven compensating mechanisms in 24 days.
**Decision:** One operating principle — "one writer at a time" — plus a pointer to worktree-per-agent isolation.
**Reasoning:** Rejected an annex: 19 of 25 roots have one worktree or none and would pay for it; and the measured damage was 0.74% docs-shaped — registers were 23 of 3,091 swept file-changes — so the problem is N agents sharing one git index, which no documentation protocol governs. Rejected a separate multi-writer protocol for now: the only multi-worktree installation (9 worktrees) recorded zero collisions using isolation alone, so the cheapest fix has already been demonstrated. Revisit if a second shared-tree project appears.
**Consequences:** Eight of the eleven mechanisms that project invented are git mechanics; SKILL.md already delegates workflow norms to the project README, and that stays true.

## D-0005 — 2026-09-03 — the compaction trigger changes now; the procedure waits for a dry run

**Context:** "Once a quarter, compact" had fired once in 25 projects (agent-proposed, 70 → 38 lines). Writing a full procedure from theory was the alternative.
**Decision:** Change the trigger to size-based (~60 lines or a red flag) and describe the routing rule; defer the step-by-step procedure until it has been dry-run against the largest retired register's five archive sections with a lossless check.
**Reasoning:** Rejected writing the procedure now: the only instance that exists was not observed in detail, and the one file it would most apply to has mechanical consumers (a gate that scans every STATUS line) that a naive split would silence. Rejected leaving the trigger as-is: at the observed rate, quarterly permitted ~470 records between compactions.
**Consequences:** Deferred item in STATUS. The procedure, when written, should generalise that instance rather than invent one.

## D-0006 — 2026-09-04 — go public after v0.2.0, not before and not never

**Context:** The repository is private with no clones. The audit found the pre-audit text on `main`, no repository description or topics, a README that opens with the problem rather than the idea, and a trigger that fires on three filenames alone.
**Decision:** Publish, but only after: the audit branch is merged and tagged `v0.2.0`; the README leads with the design property and the population evidence; `docs/EVIDENCE.md` exists with no project, product or person names; the trigger signature is narrowed.
**Reasoning:** Rejected publishing now — it would publish the pre-audit text and put the false-trigger risk on strangers' machines. Rejected staying private — the work is done and the measurement is the one thing that distinguishes this from transcript-mining memory tools. The evidence is the pitch; publishing without it wastes it.
**Consequences:** Every commit on `main` becomes an unpinned release to anyone following the README's clone instruction. Tag before every behavioural change.

## D-0007 — 2026-09-04 — the prepend instruction is fixed in live templates only, never in historical prompts

**Context:** Twenty-five files in the largest project contain "prepend a session line to STATUS". Two are reusable templates; twenty-three are dated one-shot prompts, register entries and audit snapshots.
**Decision:** Fix the two live templates. Leave the twenty-three.
**Reasoning:** Rejected fixing all twenty-five: dated prompts are the record of what was actually instructed, and rewriting them to hide a past convention is the retroactive edit the protocol forbids in every register. Rejected doing nothing: STATUS was growing at about five records a day.
**Consequences:** A reused historical prompt would still say "prepend"; the wiring block's precedence rule now outranks it.

## D-0008 — 2026-09-04 — colliding decision ids get one correction entry, not a renumber

**Context:** Four addresses in the largest retired register resolve to more than one decision — three to two bodies each, one to four — and nothing acknowledges it.
**Decision:** Append a single correction entry naming every collision and stating which body governs at each address. Do not renumber.
**Reasoning:** Rejected renumbering: it edits an append-only register and breaks every inbound citation. Rejected leaving it: an ambiguity that is written down is a different thing from one that is not.
**Consequences:** The addresses stay ambiguous, knowingly. The entry is drafted by the compaction dry-run session after it has read all eleven bodies, and applied by the owner.

## D-0009 — 2026-09-04 — Brief is offered at Close only when something is askable, not run at every Close

**Context:** The owner asked for a decision brief "every time after each close". The audit's clearest finding about rituals is that the ones nobody needs decay into noise — the 40-line flag fired on 23 of 25 roots and was acted on once; a brief with nothing to brief is the canned adoption decision in a new shape.
**Decision:** Brief runs on demand, and at Close is offered in one line only when STATUS carries an askable item — an open question not postponed, or a blocker gated on the owner. Otherwise nothing is said.
**Reasoning:** Rejected running it at every Close: on a register with no open questions it produces a "nothing open" line every session, which the owner learns to skip, and then skips the one that matters. Rejected firing on any non-empty Blocked section: a vendor's delay is not a question for the owner. Rejected adding an offer bullet to the wiring block: it would make the six blocks re-synced this week stale again immediately; the mode text carries the offer.
**Consequences:** The offer depends on the skill text rather than the always-loaded block. If the offer is measured to be missed in practice, the bullet goes into the block at the next block revision, with a re-sync.

## D-0010 — 2026-09-04 — Doctor and Brief are modes of this skill, not a separate skill

**Context:** The owner asked whether the health check and the decision brief should be a new skill or part of the protocol.
**Decision:** Modes 4 and 5 of project-docs-protocol.
**Reasoning:** Rejected a separate skill: Doctor's checks are the protocol's own red flags and thresholds and must run when a Bootstrap flag fires, which a second skill cannot be made to do; Brief reads and writes the same registers Close does and its record step is the DECISIONS entry with rejected alternatives named — a second skill would duplicate every format rule and drift from it. Both also depend on the wiring block's exact wording, which lives here.
**Consequences:** SKILL.md grows from three modes to five and gains a `scripts/` directory; the trigger list gains six phrases. Anyone forking the skill gets both modes or neither.

## D-0011 — 2026-09-06 — a brief records CHANGELOG, then DECISIONS, then STATUS — deliberately not Close's order

**Context:** Mode 5 said "run as a Close, in Close's order" and then listed CHANGELOG, DECISIONS, STATUS, while Close is CHANGELOG, STATUS, DECISIONS. The independent review called the contradiction a durability defect and recommended one order everywhere.
**Decision:** Briefs record CHANGELOG first, DECISIONS second, STATUS third, and the text says so and why.
**Reasoning:** Rejected the reviewer's "same order everywhere": for a brief the STATUS rewrite removes the question, and the DECISIONS entry is the only other place it lives, so writing STATUS before DECISIONS turns a crash between them into a lost owner pick. Rejected reordering Close to match: Close's STATUS-before-DECISIONS is right for ordinary work, where STATUS is the dashboard and DECISIONS is optional. The crash window that remains — the log naming ids that were never written — is detectable, so Doctor gained `changelog-decision-refs`.
**Consequences:** Two orders in the skill, each stated with its reason; a session that follows the README alone still gets the brief order from the brief entry format.

## D-0012 — 2026-09-06 — Reasoning in a brief's DECISIONS entry carries only reasons the owner gave

**Context:** The worked example's entries "rejected" alternatives with reasons the owner never stated, and the mode text said the protocol's test was met "because the owner read those options and chose among them". The reviewer showed an agent could mint a permanent, evidence-looking entry from its own pros and cons.
**Decision:** Reasoning quotes the owner's reason; it names as rejected only the alternatives the owner called live, with the reason they gave; every other presented option is "presented, not chosen — agent's assessment: …"; no reason is attributed to the owner that the owner did not give; the liveness question names every presented alternative in one line.
**Reasoning:** Rejected the reviewer's proposal of an explicit owner acknowledgement for every rejected alternative: it makes the owner ratify a list to satisfy the record, which is the ritual the restraint principle refuses, and one liveness question over the whole list gets the same honesty in one line. Rejected keeping the "owner read the options" test: it launders the agent's reasoning into an append-only register.
**Consequences:** Entries minted by briefs may carry less reasoning; what they carry is the owner's. A future reader can tell the two apart.

## D-0013 — 2026-09-06 — Doctor's exit code separates advisory drift from a broken property

**Context:** On a 26-root sweep the checker exited 1 on 25 roots; nine of those carried only WARN lines. The reviewer read "exit 1" as "failed installation", and "a fresh install should exit 0" was unmeetable with any advisory present.
**Decision:** 0 every check passed · 1 WARN only · 2 at least one FAIL · 3 the checker could not run.
**Reasoning:** Rejected keeping one non-zero bit: a caller could not tell drift from a broken property. Rejected demoting thresholds to INFO so that more roots exit 0: the thresholds are the audit's measurements; the exit code was the wrong instrument, not the numbers.
**Consequences:** Nothing keyed on the old contract — no release shipped it. The fresh-install promise becomes "exit 0, or 1 only for brand markers you chose to leave".

## D-0014 — 2026-09-06 — category is a tenth `Tags` column with a declared vocabulary, not sigils in free text

**Context:** The measured tracker's best sheet carried two category columns that drifted to 24 and 36 distinct values on 120 rows, while its four-token severity column stayed 100% valid; the ledger design had dropped category altogether, and the owner asked for it back.
**Decision:** A `Tags` column, blank or holding tokens declared on one banner line (at most twelve; a token is `+` then lowercase letters, digits or hyphens), with a Doctor FAIL on anything undeclared and a WARN on a token found in any other cell.
**Reasoning:** Rejected `+tags` written into the Touches cell (the todo.txt convention): a dropped `+` in a 92-value free-text cell is invisible to any scan, and that is the drift path the measured columns took. Rejected declaring the vocabulary in GLOSSARY: the Doctor never opens it and it is absent in 9 of 25 roots. The column costs nothing today — the ledger has zero installs — and it is the extension point the schema was criticised for lacking.
**Consequences:** Ten columns, not nine; the vocabulary is the project's to declare and prune; a project that wants a second category axis has to argue for it.

## D-0015 — 2026-09-06 — lineage is a citation, not a link column: `from LG-NNNN` in Evidence and `extends D-XXXX` in DECISIONS titles

**Context:** Related items and rules recur across long stretches of a register; in the measured DECISIONS, 110 of 222 entries cite an earlier one and one entry has twelve later citers — three of which extend it, none supersede it, nine merely mention it.
**Decision:** A sub-item is a new row whose Evidence opens `from LG-NNNN`; a clarification is an edit to the row; DECISIONS gains one title form, `extends D-XXXX`, beside `corrects` and `supersedes`; a cited id without a verb is a citation; a rule extended more than three times is restated once as a supersession naming every id it replaces; back-links are derived by grep.
**Reasoning:** Rejected renaming Blocked-on to a typed `Links` column with `blocked-by` / `child-of` / `see` verbs: it breaks the one-line invariant BLOCKED ⇔ Blocked-on non-empty, plants a second vocabulary inside a free-text cell, and has no form for the dominant blocker kind — 25 of 42 measured dependencies name an owner ruling, not a row. Rejected a rewritten "current rule" home in README: README is not on the bootstrap path, and the measured project's consolidation surfaces multiplied to three files and bloated. Rejected the verb `refines`: the register's own word, used nine times, is `extends`.
**Consequences:** Grouping and lineage are both greps; no file is ever physically re-sorted (the mint-order check was cut as unimplementable without reading the archive).

## D-0016 — 2026-09-06 — the ledger is opt-in at about fifteen live items, never installed by default

**Context:** Only one of 25 roots has a findings list that outgrows STATUS; the audit measured that a BRAND file installed with only placeholders is never filled in (8 of 14).
**Decision:** Install question 8 offers the ledger only when a project carries, or will imminently carry, about fifteen live items with closing conditions; one ledger per repository, owned by the register that owns the work; dated history in a Known-issues list is compaction material, not ledger material.
**Reasoning:** Rejected shipping `LEDGER.md` in every install: an empty tracker is the BRAND mistake at larger scale, and the Doctor would print ten more lines on 24 roots that have nothing to track. Rejected a size-in-lines trigger: the count-based bar was tested against the population (23 of 25 roots at 0–10 items, the two above at 28 and 52) and a lines bar was not.
**Consequences:** A project below the bar keeps its short lists in STATUS's Blocked and Deferred tables; the Bootstrap red flag names the day the list outgrows them.

## D-0017 — 2026-09-11 — the minimal installation is four files, and the protocol says so

**Context:** Three places in the repository disagreed about what an installation is. README.md called ROADMAP, GLOSSARY, BRAND and SPEC_TEMPLATE "optional scaffolding", its own Files section listed ROADMAP and GLOSSARY among the files copied into every project, and Install's tree implied the same. An independent reviewer raised it as a contract-clarity defect.
**Decision:** The minimal installation is `README.md` plus the three registers `STATUS.md`, `CHANGELOG.md`, `DECISIONS.md`. ROADMAP, GLOSSARY, BRAND, SPEC_TEMPLATE and LEDGER are seeded when the project needs them. Install states it; the README matches.
**Reasoning:** The code was the arbiter, not taste: `has_register` requires exactly the three registers, the README is read for the install footer, and the doctor references ROADMAP, GLOSSARY and SPEC_TEMPLATE zero times. Rejected "keep ROADMAP and GLOSSARY as defaults and fix only the README wording": it would ship two files no check reads and no mode requires, which is the BRAND mistake the audit already measured (8 of 14 placeholder BRAND files were never filled). Rejected "add Doctor checks for ROADMAP and GLOSSARY so the default earns itself": restraint is the protocol's first principle, and nothing measured says a project without a glossary is unhealthy.
**Consequences:** A four-file install is now a supported, documented state rather than an undocumented one this skill happened to be in. Projects wanting the fuller set add files later without ceremony.

## D-0018 — 2026-09-11 — a STATUS table whose columns cannot be named is left unresolved, never mapped

**Context:** Repairing the reported header-detection defect closed the case where recognised labels sat beside an unrecognised one. Attacking the repair surfaced the remaining case: a table whose labels are *all* unrecognised still mapped its rows, so a cell reading `BLOCKED` in a bespoke layout landed in the ledger as an OPEN row with no gate — the same harm as the reported defect, one step narrower.
**Decision:** When no column can be named and a cell holds a bare live-state token, the row becomes an unresolved record requiring an explicit human disposition.
**Reasoning:** Rejected "map it and let plan review catch it", which is how the reported defect did its damage — review catches what it is shown, and a row whose Status cell reads OPEN does not announce that its source said BLOCKED. Rejected the broader "treat any unnamed layout as unresolved": most bespoke tables carry no state token and mapping them is right, so the narrower trigger keeps the guard from taxing ordinary projects. Matching a whole cell rather than a substring keeps a title like "requests blocked by CORS" out of it.
**Consequences:** A project with a bespoke state column does more review work at migration and loses nothing silently. Migration's bias is now uniformly toward refusing to guess.

## D-0019 — 2026-10-02 — the research and Architect protocols ship here as companions a project vendors, not as modes of this skill

**Context:** The owner chose to ship both protocols with this skill. D-0010 made Doctor and Brief modes rather than a separate skill, because they check and write the core registers and must run when a Bootstrap red flag fires.
**Decision:** Each ships under `staging/` as its own skill. A project copies one in, registers it in `SKILL-REGISTRY.md` as `staged`, and promotes it to `active` only on an explicit owner pick. `SKILL.md` specifies once how each joins Bootstrap, Brief and Close.
**Reasoning:** Agent's assessment, recorded as such. Rejected making them modes: unlike Doctor and Brief, each owns a separate folder and must work in a project that does not use this skill, so folding them in would make every core install carry both. Rejected separate repositories: their hooks into Bootstrap, Brief and Close would then be specified in three places and drift, which is the failure D-0010 predicted.
**Consequences:** One repository, one hook specification, and companions that stay inert until a project adopts them.

## D-0020 — 2026-10-02 — the registry line in the wiring block is conditional, not part of the generic block (extends D-0009)

**Context:** The release branch added a nine-line routing bullet to the always-loaded wiring block. No real installation has a registry, the Doctor does not check for the bullet, and none of the 16 projects carrying the current block would ever be prompted to add it.
**Decision:** The generic block carries no registry text. A project that installs `SKILL-REGISTRY.md` adds one *Project skills* line after **Session start**.
**Reasoning:** Agent's assessment. Rejected the generic bullet: it loads about 90 words into every session of every project for a file almost none have, and leaves two block generations that both pass forever — the staleness D-0009 kept a Brief bullet out of the block to avoid. The registry's rules belong in the file the line points to.
**Consequences:** Existing installations do not go stale. A project adopting a registry takes one extra line at the moment it adopts it.

## D-0021 — 2026-10-02 — the registry records authority; it never grants it

**Context:** The registry called itself "an inventory, not an activation mechanism", but routing by trigger plus "active skills obey authorization" read two ways, nothing governed edits to a row's lifecycle, and the validator printed the digest an edited skill needed to pass.
**Decision:** `active` means the owner authorized the skill for its trigger and stages, and the row cites that authorization. Promoting `staged` to `active` takes an explicit owner pick. A registry edit is a register change, CHANGELOG first. A stale digest makes the skill unavailable until its reviewer gate re-passes and the owner records the new digest; the validator never prints a digest to paste. Registry state never blocks or reorders writes to the core registers.
**Reasoning:** Agent's assessment. Rejected keeping the inventory-only wording: an agent that can change a row's lifecycle and re-record a digest can approve itself. Rejected enforcing authorization citations in the validator: it would verify a string's presence, not its truth, and make a structural check look like an approval.
**Consequences:** Adopting or upgrading a vendored skill is visible in CHANGELOG and DECISIONS; the validator stays structural.

## D-0022 — 2026-10-02 — this repository's own process evidence stays private; the public acceptance harness binds public documents

**Context:** The release-readiness packet, research working notes and hardening evidence records were process evidence from building these features. They named a private project, carried hundreds of absolute paths from the owner's machine, and bound commit IDs that a privacy-driven history rewrite removes, so the packet would fail its own Architect doctor once published. The owner's instruction was that nothing published may expose their machine or private work.
**Decision:** That evidence is retained privately, outside this repository. The acceptance harness that hashed it as inputs binds the public normative documents instead.
**Reasoning:** Agent's assessment. Rejected publishing it with placeholders: the packet would still fail its own doctor, and the residue (session identifiers, machine descriptions) is still the owner's. Rejected deleting it: it is the evidence behind several closed ledger rows. This follows v0.2.0, where the full audit stayed private and only an anonymised evidence sheet shipped.
**Consequences:** Some earlier CHANGELOG entries and archived ledger rows cite files that are not public; they are left as written. LG-0044 and LG-0045 are restated against public, testable conditions.
