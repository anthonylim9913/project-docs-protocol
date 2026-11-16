# Project skill registry

This optional inventory records intentional project skills. It is separate from
the four-document minimum and never grants activation or write permission.
Personalize or remove the example row; keep one row per stable skill name and
retain retired identities for history. Locations are relative to the project root.

| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `example-skill` | explicit fixture request | staged | Bootstrap, Close | fixture records | fixture report | independent review | optional | `skills/example-skill` | `1.0.0` | `sha256v2:REPLACE_WITH_TREE_DIGEST` | continue core and report unavailable fixture |

Lifecycle is `active`, `staged` or `retired`. `active` means the owner authorized
the skill for its trigger and stages: cite that authorization (a D-ID or the
Brief's CHANGELOG line) in the row. Promoting `staged` to `active` takes an
explicit owner pick. A staged row still needs explicit task/project
authorization; retired rows are not invoked. Workflow stages are comma-separated
invocation points such as Bootstrap, Brief, Close, Review or project-specific
stages. Editing this file is a register change: CHANGELOG entry first. All
actions obey higher-priority instructions, and registry state never blocks or
reorders writes to the core registers.

Record the reviewed version and full tree Content-ID, `sha256v2:<64 lowercase hex>`.
SHA-256 hashes the domain tag `b"project-docs-protocol skill-tree v2\n"`, then
each regular file sorted by its strict UTF-8 POSIX relative path bytes: an
8-byte big-endian path length, the path bytes, an 8-byte big-endian content
length and the content bytes. Permissions and empty folders are not covered;
NFC and NFD names remain distinct paths. Any path with a `__pycache__`
component is excluded; stray `.pyc` files elsewhere are hashed. Also exclude
the target root's `.git` and desktop metadata (`.DS_Store`, `Thumbs.db`).
Nested `.git` contents are bound. Refuse links even when their names are excluded,
and fail if an included directory cannot be read rather than hashing a partial tree.
Compute it on the files exactly as committed: a checkout that converts line
endings produces a different digest. Record the digest of the tree
the reviewer actually reviewed (`skill-registry.py <project-root> --digest
<location>` computes it and labels it unreviewed). The validator diagnoses missing paths, stale
identity and incomplete rows; a stale Content-ID means the skill changed since
review, so treat it as unavailable until its reviewer gate re-passes and the
owner records the new digest. Never record a digest nobody reviewed.

The legacy `sha256:` format has an ambiguous encoding, not a weakness in SHA-256.
Active and staged legacy rows FAIL without a replacement digest; there is no
WARN tier or automatic migration. They are unavailable until their reviewer
gate re-passes and the owner records a reviewed v2 identity. Retired rows may
keep their historical IDs and are not compared. A separately owner-approved
identity transfer for unchanged, already reviewed trees requires independent
actual-file comparison against the reviewed version (Git diff plus
extracted-tree comparison) and independent v2 computation, never copied from
`--digest`, before owner recording. This is not automatic migration or
authorization to transfer another project's identities.

For an unavailable optional capability, use its recorded fallback and state the
verification gap while continuing applicable core work. An unavailable required
capability blocks dependent work. A malformed inventory remains a diagnostic,
not a passing registry. Active and staged paths must exist to verify their
Content-ID; retired rows may retain unavailable paths as historical identities.
