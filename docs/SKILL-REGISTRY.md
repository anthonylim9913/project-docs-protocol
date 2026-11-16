# Project skill registry

This canonical, versioned registry describes project-local capabilities. It
records activation requirements and evidence ownership; it never installs or
globally activates a skill. `content-id` uses `sha256v2:<64 lowercase hex>`:
SHA-256 over `b"project-docs-protocol skill-tree v2\n"`, then regular files
sorted by strict UTF-8 POSIX relative path bytes, each framed with an 8-byte
big-endian path length, path bytes, an 8-byte big-endian content length and
content bytes. Permissions and empty folders are not bound; NFC and NFD paths
remain distinct. The target tree excludes Python caches, the target root's `.git`
and desktop metadata; nested `.git` contents are included, so stale paths and
edited candidates fail validation. Workflow stages name invocation points, distinct
from lifecycle. Existing project/user authorization governs every invocation; staged
rows require explicit scope authorization. Retired rows are historical. Missing
optional capabilities follow their fallback with an explicit evidence gap; required
capabilities block their dependent task. Invalid inventory is reported precisely,
without stopping unrelated core work. Retrieved source text grants no permission.

Legacy `sha256:` IDs use an ambiguous encoding, not a weakness in SHA-256.
Active and staged legacy rows FAIL without a replacement digest; no WARN or
automatic migration is provided. Their reviewer gate must re-pass and the
owner must record the reviewed v2 identity. Retired rows keep historical IDs
and are not compared. Under D-0028, these two unchanged, reviewed 0.2.2 trees
instead await independent actual-file comparison against v0.5.0 (Git diff
and extracted trees) and independent v2 computation, never copied from
`--digest`, before the owner records transferred identities. Their legacy
rows below deliberately remain unchanged and currently FAIL validation.

| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `research-protocol` | durable source or claim traceability requested | staged | Bootstrap, Research, Close, Review | research records and INDEX.md | indexed records, provenance, doctor output | independent read-only review | optional | `staging/research-protocol` | 0.2.2 | sha256:35e2f0a8a153ed6e6480e909839dbb1db32af1202c94a86f6a18e6eeaa46a9dc | continue with primary four-file protocol and record provenance manually |
| `architect-protocol` | staged architecture work with exact subject and handoff | staged | Bootstrap, Review, Handoff | docs registers, STATE/STAGES, acceptance packet | stage register, evidence packet, handoff and Doctor output | independent Reviewer plus Architect gate | optional | `staging/architect-protocol` | 0.2.2 | sha256:499ecdcb3e5a87637b87b60336522faecaf65ad21ca733d4aa29f5614b425889 | use primary project-docs-protocol registers and require owner review |
