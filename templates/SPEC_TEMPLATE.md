# Spec Template

*Opt-in: this file is installed only for spec-driven projects. If the project doesn't write formal specs, it shouldn't have this file.*

*Every project spec follows this structure. Sections appear in this order. Dropping a section is fine if it genuinely doesn't apply — flag it with `*not applicable: <reason>*` rather than deleting silently.*

*Copy the block below as the starting point for any new spec.*

---

## Identity

- **Spec ID:** `[PREFIX]-SPEC-NNNN` (zero-padded, assigned sequentially — check the highest existing ID before picking)
- **Title:** <short, descriptive, no marketing language>
- **Version:** `v0.1` (bump minor for edits during draft; bump major when ratified or materially restructured)
- **Status:** `draft` | `in review` | `ratified` | `superseded by <SPEC-ID>`
- **Author:** [default author] / co-authors if any
- **Last updated:** YYYY-MM-DD

## Scope

- **[Scope dimension 1 — e.g., Jurisdictions, Environments, Tiers]:** state explicitly, don't assume.
- **[Scope dimension 2 — e.g., User segments]:** which user types this applies to.
- **Systems touched:** which services, databases, or external integrations this spec reaches into.
- **Phase:** which phase of the project this belongs to (see ROADMAP.md).

## Context

Why this spec exists. What problem it solves or what gap it closes. If it replaces or extends an existing spec, name the spec and describe the delta. Keep this section short — 3–6 sentences. Long context is a signal the spec is trying to do too many things.

## Functional requirements

What the system must do. Numbered list (`FR-1`, `FR-2`, …) for traceability. Each requirement should be testable — "the system handles errors gracefully" is not a requirement; "the system returns HTTP 429 with Retry-After header when rate limit is exceeded" is.

Reference other specs by Spec ID when building on them (`per PROJ-SPEC-0012 §FR-4`).

## Non-functional requirements

Group into subsections as needed:

- **Performance** — latency budgets, throughput targets, concurrency assumptions.
- **Security** — authentication, authorization, threat model, key management.
- **Data residency** — where data is stored, what leaves its home region and why.
- **Compliance** — specific regulatory requirements. Cite section numbers, not just act names.
- **Observability** — what metrics, logs, and traces this system emits.
- **Reliability** — SLO targets, failure modes, degradation behavior.

Omit subsections that don't apply, but use `*not applicable*` rather than silent deletion.

## Dependencies

- **Upstream specs:** specs this one relies on.
- **Downstream specs:** specs that will depend on this one (may be empty during draft).
- **External references:** regulatory documents, third-party APIs, standards. Link with full URLs, not just names — URLs survive re-reads; names rot.

## Out of scope

Explicit list of things this spec does *not* cover, especially where a reasonable reader might expect it to. This section is doing load-bearing work — it prevents silent scope creep and future "I thought this was covered by <SPEC-ID>" confusion.

## Verification

Concrete acceptance checks — what you'd actually run or click to confirm the requirements were delivered. Numbered list (`V-1`, `V-2`, …). Each item should be specific enough that a future session can confirm "passed" or "failed" without judgment calls.

`V-1` [the runnable check, e.g., "`curl -X POST localhost:3000/api/login` with valid credentials returns 200 + Set-Cookie"]

`V-2` [the runnable check]

Reference the FR each item ties back to where it isn't obvious (`V-1` covers `FR-1, FR-2`).

Vague items ("performs well under load," "handles errors gracefully") don't belong here — they belong in NFR with concrete thresholds. The test for whether something is a verification item is whether you could write a one-line check that returns pass/fail.

When the spec ships, the per-spec changelog entry records which items passed and which deferred. Failed items become open questions or new specs, not silent gaps.

## Open questions

Numbered list of unresolved points, each with:
- the question
- what's blocking resolution (more info, a decision from the owner, external clarity, etc.)
- a proposed default if one exists

Open questions that resolve become DECISIONS.md entries and get removed here.

## Per-spec changelog

Append-only, oldest first — newest at the bottom; this log is short and read whole, unlike the project CHANGELOG.

```
## YYYY-MM-DD — v0.1
Initial draft. [One-sentence summary of scope.]

## YYYY-MM-DD — v0.2
[What changed and why.]
```

Each entry: date, version, 1–3 sentences of what changed and why. Never edit previous entries — add a correction entry below if needed.

---

## Template notes (delete when starting a real spec)

- Keep specs under ~600 lines when possible. Past that, consider breaking into sibling specs and cross-referencing.
- Prose over bullets where prose is clearer. Requirements and dependencies can be lists; context and rationale usually shouldn't be.
- If a spec is hard to write because the problem isn't clear yet, the answer is not "write a vaguer spec" — it's "add an open question and resolve it first."
- Cite external references with specificity (jurisdiction + act + section, or service + API version + endpoint), not just names.
