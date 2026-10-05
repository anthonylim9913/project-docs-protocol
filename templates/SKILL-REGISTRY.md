# Project skill registry

This optional inventory records intentional project skills. It is separate from
the four-document minimum and never grants activation or write permission.
Personalize or remove the example row; keep one row per stable skill name and
retain retired identities for history. Locations are relative to the project root.

| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `example-skill` | explicit fixture request | staged | Bootstrap, Close | fixture records | fixture report | independent review | optional | `skills/example-skill` | `1.0.0` | `sha256:REPLACE_WITH_TREE_DIGEST` | continue core and report unavailable fixture |

Lifecycle is `active`, `staged` or `retired`. `active` means the owner authorized
the skill for its trigger and stages: cite that authorization (a D-ID or the
Brief's CHANGELOG line) in the row. Promoting `staged` to `active` takes an
explicit owner pick. A staged row still needs explicit task/project
authorization; retired rows are not invoked. Workflow stages are comma-separated
invocation points such as Bootstrap, Brief, Close, Review or project-specific
stages. Editing this file is a register change: CHANGELOG entry first. All
actions obey higher-priority instructions, and registry state never blocks or
reorders writes to the core registers.

Record the reviewed version and full tree Content-ID. Its SHA256 encoding is
sorted relative file path, NUL, file bytes, NUL for each file; exclude Python
caches, `.git` and desktop metadata (`.DS_Store`, `Thumbs.db`) and refuse links.
Compute it on the files exactly as committed: a checkout that converts line
endings produces a different digest. Record the digest of the tree
the reviewer actually reviewed (`skill-registry.py <project-root> --digest
<location>` computes it and labels it unreviewed). The validator diagnoses missing paths, stale
identity and incomplete rows; a stale Content-ID means the skill changed since
review, so treat it as unavailable until its reviewer gate re-passes and the
owner records the new digest. Never record a digest nobody reviewed.

For an unavailable optional capability, use its recorded fallback and state the
verification gap while continuing applicable core work. An unavailable required
capability blocks dependent work. A malformed inventory remains a diagnostic,
not a passing registry. Active and staged paths must exist to verify their
Content-ID; retired rows may retain unavailable paths as historical identities.
