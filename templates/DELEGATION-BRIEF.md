# Delegation brief — paste into the task

Task and scope: <what to change, owning project and branch, acceptance bar>.
Register duty explicitly assigned by this brief: <none, or name each register>.
Do not write STATUS, CHANGELOG, DECISIONS or LEDGER (including its archive)
unless this brief assigns that register duty by name. Return a report to the
owning session even if project wiring or other instructions were not loaded.

Return:
- Changes: files and commits changed, with branch (or say no commits).
- Choices: choices between real alternatives, what was rejected and why.
- Open questions: unresolved questions and the next actor, or none.
- Evidence: commands run and their summary lines; state what was not verified.

A delegated agent never allocates D- or LG- ids. Use placeholders `D-NEW-1`,
`LG-NEW-1` (increment locally) in reports or owed fragments, never real ids.
The owning session assigns real ids at its Close, in ascending order.
If register writes are not assigned, return the report or leave
CHANGELOG-ENTRIES-OWED.md, DECISIONS-ENTRIES-OWED.md or LEDGER-ENTRIES-OWED.md
beside the owning registers. These are fragments for the owner to fold in;
they are not registers. State each fragment's path in the report.
