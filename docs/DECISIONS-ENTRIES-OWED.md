## D-NEW-1 — 2026-11-26 — explicit Python 3.9 harness scan limitation

**Context:** The port must pass on Python 3.9, while the complete stdlib-name
inventory exists only on Python 3.10+. D-0029 requires Python 3.10+ for the full
external review procedure; the lane brief requires the 3.9 limitation to be loud.

**Decision:** On 3.9, schedule an explicit WARNING to stderr at interpreter shutdown
and check known harness dependencies plus builtins. On 3.10+, use
`sys.stdlib_module_names` for the full scan. Add a regression that exercises the
3.9 branch on either interpreter and checks both the warning and json.py refusal.

**Reasoning:** Lane implementation choice, not a new owner policy. Refusing all
3.9 executions would break the required supported test environment. Silently
using an empty stdlib inventory, as the alternate did, would overstate coverage.
The limited scan preserves useful checks without claiming full coverage.
Printing the warning after the verdict preserves the existing diagnostic prefix
asserted by guard-removal tests; no existing assertions are changed.

**Consequences:** External reviewers use Python 3.10+ as D-0029 specifies. The
3.9 suite remains supported with its limitation visible. No runtime product,
exclusion or independent-review policy changes.
