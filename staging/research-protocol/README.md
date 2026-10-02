# research-protocol candidate

This optional companion keeps Markdown source, note, question and synthesis
records with stable IDs. Python 3.9+ standard library; no package dependencies.
Read [SKILL.md](SKILL.md) for provenance exceptions, lifecycle and trust limits.

```sh
python3 scripts/research-doctor.py "/path/to/project"
python3 scripts/research-index.py "/path/to/project" --id SRC-0001
python3 scripts/research-index.py "/path/to/project" --topic naming
python3 scripts/research-write.py --root "/path/to/project" "/path/to/project/research/notes/NOTE-0001.md" "reviewed replacement content" --expected-sha256 "CURRENT_SHA256"
```

Read helpers validate their own boundary without a prior Doctor run. Write only
an explicitly selected existing regular record using its current SHA-256. Paths
inside research cannot be links, hard-link aliases or special files. The project
root is caller-selected and trusted. The writer takes it with `--root` (default:
the current directory) and accepts only targets inside `<root>/research/`;
relative targets are anchored to the current directory. Readers take the same
explicit root. Helper sidecars are reserved write targets.
Ordinary hidden Markdown is discoverable; actual helper metadata is excluded.
Each indexed record occupies its own file with one complete stable declaration.
Multiple declarations fail Doctor and ID retrieval; safe diagnostic retrieval
does not require complete provenance.

Writes require secure descriptor operations and `fcntl.flock`; unavailable
capabilities refuse safely. Cooperating writers retain one stable lock inode.
Locks are never truncated or unlinked by the helper. Expected-hash checks reject
stale generations. Unique temporary files preserve the target mode; replacement
validates target, temp, directory and lock identities. Permission bits (including
set-ID bits) are applied and verified after content flush; failures preserve the
original target. ACLs, ownership and extended attributes are not promised. An arbitrary noncooperating
editor can still race between separate filesystem operations.

After interruption, inspect the actual target: it is a complete old or new
version depending on whether replacement happened. A nonzero exit after
replacement does not mean no write occurred. Abrupt termination may leave an
orphan temp; retries do not remove foreign orphans. Review them separately after
establishing no writer owns them, retain the lock, and retry with the current hash.

Doctor validates structure and reference addresses. It does not fetch URLs,
authenticate private evidence, infer owner intent, detect every stale claim or
prove historical ID integrity. Public fields cannot be blank; explicit private
and unavailable records preserve honest unknowns without fabricated citations.
