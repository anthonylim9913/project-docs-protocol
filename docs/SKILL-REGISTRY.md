# Project skill registry

This canonical, versioned registry describes project-local capabilities. It
records activation requirements and evidence ownership; it never installs or
globally activates a skill. `content-id` uses `sha256v2:<64 lowercase hex>`:
SHA-256 over `b"project-docs-protocol skill-tree v2\n"`, then regular files
sorted by strict UTF-8 POSIX relative path bytes, each framed with an 8-byte
big-endian path length, path bytes, an 8-byte big-endian content length and
content bytes. Permissions and empty folders are not bound; NFC and NFD paths
remain distinct. Any path with a `__pycache__` component is excluded; stray
`.pyc` files elsewhere are hashed. The target root's `.git` and desktop metadata
are excluded; nested `.git` contents are included, so stale paths and
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
and are not compared. Following LG-0052 verification under D-0028, the owner
authorized recording the transferred v2 identities below for the unchanged,
reviewed 0.2.2 companion trees. Final-tree `--digest` computations confirm the
recorded identities; neither companion version nor lifecycle changes.

| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `research-protocol` | durable source or claim traceability requested | staged | Bootstrap, Research, Close, Review | research records and INDEX.md | indexed records, provenance, doctor output | independent read-only review | optional | `staging/research-protocol` | 0.2.2 | sha256v2:6f92603a518f98d3c03839d422185db3427d21ea44e7ac6f0e3300c7b0dd6b9d | continue with primary four-file protocol and record provenance manually |
| `architect-protocol` | staged architecture work with exact subject and handoff | staged | Bootstrap, Review, Handoff | docs registers, STATE/STAGES, acceptance packet | stage register, evidence packet, handoff and Doctor output | independent Reviewer plus Architect gate | optional | `staging/architect-protocol` | 0.2.2 | sha256v2:9231d4e62ef7240385b292865d87c2b514ad8f2c239e917956ce213372c8e09b | use primary project-docs-protocol registers and require owner review |
