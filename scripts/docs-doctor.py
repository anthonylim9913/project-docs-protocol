#!/usr/bin/env python3
"""docs-doctor — health check for a project-docs-protocol installation.

Usage:
    python3 docs-doctor.py <project-root> [--today YYYY-MM-DD] [--no-git]

Reads the register (STATUS.md, CHANGELOG.md, DECISIONS.md, plus README.md
and BRAND.md when present) at <project-root> or <project-root>/docs/, and
the agent-instructions files (CLAUDE.md, AGENTS.md) at the project root.
Prints one line per check — PASS / WARN / FAIL / INFO / SKIP — with the
measured value and its unit, then a summary line.

Exit codes:
    0   every check passed (INFO and SKIP lines do not count)
    1   at least one WARN or FAIL
    2   the checker itself could not run (no such root, no register, crash)

The doctor never modifies anything. It reads files, runs read-only git
commands when git and a repository are available, and prints. Standard
library only; no third-party dependencies; git is optional.

Thresholds come from a 2026-09 audit of 25 installations and are stated
on each line so they can be argued with.
"""

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys

VERSION = "1.2.0"

REGISTER = ("STATUS.md", "CHANGELOG.md", "DECISIONS.md")
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")

# --- thresholds (from the audit) ---------------------------------------
STATUS_LINES_WARN = 60         # lines; template is ~30, healthy mature ~40
STATUS_LINES_FAIL = 100
STATUS_MAXLINE_WARN = 1024     # bytes; one line over ~1 KB is history in disguise
PAST_TENSE_WARN = 3            # lines; heuristic, see check
DORMANT_DAYS_WARN = 30         # days since the newest CHANGELOG entry
HEADING_CONFORMANCE_PASS = 0.95
CHURN_MIN_COMMITS = 10         # commits touching STATUS before churn is judged
CHURN_RATIO_WARN = 0.2         # deleted/added; rewritten files sit near 0.7-0.8
ID_MAX_DIGITS = 6              # a decision number wider than this is malformed
                               # (a date, a typo) and never enters the span

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# A dated heading: any level, carrying an ISO date or an ISO week anywhere.
DATED_HEADING_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{4}-W\d{2}")
# Session-record prefixes seen in the wild at the top of STATUS files.
SESSION_RECORD_RE = re.compile(
    r"^\s*(?:#{1,6}\s+)?\**\s*(?:LAST|PRIOR|PREVIOUS|SAME|EARLIER|THIS|CURRENT)\s+SESSION\b"
    r"|^\s*(?:#{1,6}\s+)?\**\s*SESSION\s*(?:\d+\s*)?[:—–·-]",
    re.IGNORECASE,
)
PAST_TENSE_RE = re.compile(
    r"\b(shipped|landed|deployed|done|fixed|closed)\b", re.IGNORECASE
)
CHANGELOG_HEADING_OK_RE = re.compile(r"^## \d{4}-\d{2}-\d{2}\s*[—–·:-]")
# DECISIONS id at heading level 2 or 3. Covered forms:
#   D-NNNN            the template's default
#   PREFIX-D-NNN      any chain of upper-case/digit prefixes: PROJ-D-012, API-D-003, UX-D-002
#   D-XX-NNN          a series tag between D and the number: D-FW-007
#   ADR-NNN, DEC-NNN  the common alternative conventions, prefixable the same way
#   [tag] D-NNNN      an optional bracketed tag before the id: [Phase 2B] D-0025
#   D-NNNNb           a letter-suffixed id reuses its base number (counted as a reuse)
# Group 1 is everything before the digits (the "prefix"), group 2 the digits.
DECISION_ID_RE = re.compile(
    r"^#{2,3}\s+(?:\[[^\]]*\]\s*)?((?:[A-Z][A-Z0-9]*-)*(?:D|ADR|DEC)-(?:[A-Z]+-)?)(\d+)([a-z])?\b"
)
ID_FORMS_TEXT = "D-NNNN, PREFIX-D-NNN, D-XX-NNN, ADR-NNN, DEC-NNN"
TEMPLATE_HEADING_RE = re.compile(r"D-NNNN|YYYY-MM-DD|D-XXXX|ADR-NNN|ADR-MMM|DEC-NNN|D-XX-NNN|<title>")
PLACEHOLDER_RE = re.compile(r"<decision in one line>|\[POPULATE|<path>|<one[- ]line")
INSTALL_ENTRY_RE = re.compile(r"initiali[sz]ed\b.*\bdocumentation system", re.IGNORECASE)

# The three clauses the current Step-2 wiring block carries. A block that
# lacks one was copied from an older SKILL.md and should be re-synced.
WIRING_CLAUSES = (
    ("rewritten-not-appended", re.compile(r"rewritten,?\s+not\s+appended", re.IGNORECASE)),
    ("bounded-read", re.compile(r"under\s+~?\s*60\s+lines|in\s+full\s+if\s+it\s+is\s+under", re.IGNORECASE)),
    ("precedence", re.compile(r"\*\*\s*Precedence\s*\.?\s*\*\*|^\s*-\s*Precedence\b", re.IGNORECASE | re.MULTILINE)),
)
# The block is present when its heading (level 2 or 3) or its opening
# sentence is present. A bare mention of the skill's name is not a block.
WIRING_HEADING_RE = re.compile(r"^#{2,3}\s+Project docs protocol\b", re.IGNORECASE | re.MULTILINE)
WIRING_SENTENCE_RE = re.compile(r"This project uses the project-docs-protocol", re.IGNORECASE)
WIRING_MENTION_RE = re.compile(r"project-docs-protocol", re.IGNORECASE)
# Project-authored close instructions: CHANGELOG named before STATUS within a
# few lines, with a verb or ordering cue nearby ("append CHANGELOG first, then
# update STATUS", or a numbered list). Not the skill's block, but evidence the
# register is wired by the project's own text.
CHANGELOG_MENTION_RE = re.compile(r"\bCHANGELOG(?:\.md)?\b", re.IGNORECASE)
STATUS_MENTION_RE = re.compile(r"\bSTATUS(?:\.md)?\b", re.IGNORECASE)
CLOSE_CUE_RE = re.compile(
    r"\b(append|add|update|write|log|entry|entries|first|then|second|after|before|rewrite|bump)\b"
    r"|^\s*\d+[.)]\s",
    re.IGNORECASE | re.MULTILINE,
)
CLOSE_WINDOW_LINES = 4


# --- small helpers ------------------------------------------------------

class Report:
    def __init__(self):
        self.lines = []
        self.counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "INFO": 0, "SKIP": 0}

    def add(self, level, check, value):
        self.counts[level] += 1
        self.lines.append((level, check, value))
        print("%-4s  %-26s %s" % (level, check, value))

    def exit_code(self):
        return 1 if (self.counts["WARN"] or self.counts["FAIL"]) else 0


def read_text(path):
    """Read a file as text without ever crashing on its bytes.

    NUL bytes are dropped, CRLF and lone CR become LF, undecodable bytes are
    replaced. Returns (text, size_bytes). Missing file -> (None, 0).
    """
    if not os.path.isfile(path):
        return None, 0
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None, 0
    size = len(raw)
    raw = raw.replace(b"\x00", b"")
    text = raw.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text, size


def split_lines(text):
    """Lines the way `wc -l` counts them: a trailing newline adds no line."""
    if text is None or text == "":
        return []
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def parse_date(s):
    m = DATE_RE.search(s or "")
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


COMMENT_OPEN, COMMENT_CLOSE = "<!--", "-->"


def visible_lines(lines):
    """Yield (index, line, fenced) for lines that are not inside an HTML
    comment. Fence lines themselves are consumed; a commented-out template
    example is invisible, exactly like a fenced one."""
    fenced = False
    comment = False
    for i, line in enumerate(lines):
        if comment:
            if COMMENT_CLOSE in line:
                comment = False
            continue
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced and COMMENT_OPEN in line:
            after = line[line.index(COMMENT_OPEN) + len(COMMENT_OPEN):]
            if COMMENT_CLOSE not in after:
                comment = True
            continue
        yield i, line, fenced


def headings(lines, skip_fenced=True):
    """Yield (index, level, title, fenced) for every heading line."""
    for i, line, fenced in visible_lines(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        yield i, len(m.group(1)), m.group(2).strip(), fenced


def unfenced_lines(lines):
    """Yield the lines that sit outside code fences and HTML comments."""
    for _, line, fenced in visible_lines(lines):
        if not fenced:
            yield line


def has_register(d):
    return all(os.path.isfile(os.path.join(d, f)) for f in REGISTER)


def find_register(root):
    """Return the directory holding the register: <root>/docs first, then <root>."""
    for cand in (os.path.join(root, "docs"), root):
        if has_register(cand):
            return cand
    return None


def rel_label(register_dir, root):
    rel = os.path.relpath(register_dir, root)
    return "./" if rel == "." else rel + "/"


def same_path(a, b):
    return os.path.realpath(a) == os.path.realpath(b)


def gap_census(nums):
    """Unused ids inside the span of `nums`, without materialising the span.

    Returns (count, first_examples). Linear in the number of distinct ids:
    the count is arithmetic and the examples come from walking the sorted
    distinct ids pairwise, bounded by the six examples we print.
    """
    s = sorted(set(nums))
    if len(s) < 2:
        return 0, []
    count = (s[-1] - s[0] + 1) - len(s)
    examples = []
    for a, b in zip(s, s[1:]):
        if b - a > 1:
            room = 6 - len(examples)
            examples.extend(range(a + 1, min(b, a + 1 + room)))
            if len(examples) >= 6:
                break
    return count, examples


def close_order_found(text):
    """True when the text names CHANGELOG before STATUS within a few lines,
    with an action or ordering cue in the same window."""
    lines = split_lines(text)
    for i, line in enumerate(lines):
        m = CHANGELOG_MENTION_RE.search(line)
        if not m:
            continue
        window = lines[i:i + CLOSE_WINDOW_LINES]
        found = STATUS_MENTION_RE.search(line[m.end():]) is not None
        if not found:
            found = any(STATUS_MENTION_RE.search(w) for w in window[1:])
        if found and CLOSE_CUE_RE.search("\n".join(window)):
            return True
    return False


def run_git(root, args, timeout=30):
    """Run a read-only git command; return stdout or None on any failure."""
    git = shutil.which("git")
    if not git:
        return None
    try:
        proc = subprocess.run(
            [git, "-C", root] + args,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


# --- checks -------------------------------------------------------------

def check_wiring(rep, root, register_label):
    present = {}
    for name in INSTRUCTION_FILES:
        text, _ = read_text(os.path.join(root, name))
        if text is None:
            continue
        present[name] = text
    if not present:
        rep.add("FAIL", "wiring-block",
                "no CLAUDE.md or AGENTS.md at the project root — nothing loads the protocol each session (Install step 2)")
        rep.add("SKIP", "wiring-clauses", "no wiring block to compare")
        return
    # Only text outside code fences and comments counts: a quoted block is not a block.
    visible = {n: "\n".join(unfenced_lines(split_lines(t))) for n, t in present.items()}
    wired = [n for n, t in visible.items()
             if WIRING_HEADING_RE.search(t) or WIRING_SENTENCE_RE.search(t)]
    if not wired:
        files = ", ".join(sorted(present))
        close_order = sorted(n for n, t in present.items() if close_order_found(t))
        mention = sorted(n for n, t in present.items() if WIRING_MENTION_RE.search(t))
        if close_order:
            extra = "" if not mention else "; %s also name(s) the skill without its block" % ", ".join(mention)
            rep.add("WARN", "wiring-block",
                    "0 of %d instructions files (%s) carry the 'Project docs protocol' block, but %s carries project-authored "
                    "close instructions naming CHANGELOG then STATUS — not the skill's block; confirm equivalence and propose a "
                    "re-sync so the precedence and rewritten-not-appended clauses are present%s"
                    % (len(present), files, ", ".join(close_order), extra))
            rep.add("SKIP", "wiring-clauses", "project-authored instructions are not clause-checked; re-sync adds the skill's block")
        elif mention:
            rep.add("WARN", "wiring-block",
                    "%s mention(s) project-docs-protocol but no block: neither the '## Project docs protocol' heading nor "
                    "'This project uses the project-docs-protocol' is present (%d instructions files: %s) — mentioned but no block; "
                    "propose Install step 2"
                    % (", ".join(mention), len(present), files))
            rep.add("SKIP", "wiring-clauses", "no wiring block to compare")
        else:
            rep.add("FAIL", "wiring-block",
                    "0 of %d instructions files (%s) carry the 'Project docs protocol' block or any close-order instruction "
                    "naming CHANGELOG then STATUS — the register is not wired"
                    % (len(present), files))
            rep.add("SKIP", "wiring-clauses", "no wiring block to compare")
        return
    unwired = sorted(set(present) - set(wired))
    note = "" if not unwired else " (missing from %s)" % ", ".join(unwired)
    rep.add("PASS", "wiring-block",
            "present in %d of %d instructions files: %s%s" % (len(wired), len(present), ", ".join(sorted(wired)), note))

    # Clause currency: every wired file should carry all three current clauses.
    stale = {}
    for name in wired:
        missing = [label for label, rx in WIRING_CLAUSES if not rx.search(visible[name])]
        if missing:
            stale[name] = missing
    if stale:
        parts = ["%s lacks %s" % (n, "+".join(m)) for n, m in sorted(stale.items())]
        rep.add("WARN", "wiring-clauses",
                "%d of 3 current clauses missing — %s; block predates the current SKILL.md, re-sync it"
                % (max(len(m) for m in stale.values()), "; ".join(parts)))
    else:
        rep.add("PASS", "wiring-clauses",
                "3 of 3 current clauses present (rewritten-not-appended, bounded-read, precedence) in %s"
                % ", ".join(sorted(wired)))


def check_readme_footer(rep, register_dir):
    text, _ = read_text(os.path.join(register_dir, "README.md"))
    if text is None:
        rep.add("WARN", "readme-footer", "no README.md in the register directory — the map file is missing")
        return
    if re.search(r"Installed via the `?project-docs-protocol`? skill", text):
        rep.add("PASS", "readme-footer", "install footer present in README.md")
    elif re.search(r"project-docs-protocol", text):
        rep.add("WARN", "readme-footer",
                "README.md mentions project-docs-protocol but has no install footer — a bespoke or pre-skill register?")
    else:
        rep.add("WARN", "readme-footer",
                "README.md carries no install footer — the register may predate the skill or come from another convention")


def check_status(rep, register_dir, changelog_newest, today):
    path = os.path.join(register_dir, "STATUS.md")
    text, size = read_text(path)
    lines = split_lines(text)
    n = len(lines)
    if text is None:
        rep.add("FAIL", "status-size", "STATUS.md unreadable")
        return None
    if n == 0:
        rep.add("WARN", "status-size", "0 lines, 0 B — STATUS.md is empty")
    elif n > STATUS_LINES_FAIL:
        rep.add("FAIL", "status-size",
                "%d lines, %s B (warn >%d, fail >%d) — history is being kept in the dashboard"
                % (n, "{:,}".format(size), STATUS_LINES_WARN, STATUS_LINES_FAIL))
    elif n > STATUS_LINES_WARN:
        rep.add("WARN", "status-size",
                "%d lines, %s B (warn >%d, fail >%d) — something is miscategorised"
                % (n, "{:,}".format(size), STATUS_LINES_WARN, STATUS_LINES_FAIL))
    else:
        rep.add("PASS", "status-size",
                "%d lines, %s B (warn >%d, fail >%d)" % (n, "{:,}".format(size), STATUS_LINES_WARN, STATUS_LINES_FAIL))

    # Longest line, in bytes as stored (UTF-8).
    longest = max((len(l.encode("utf-8")) for l in lines), default=0)
    if longest > STATUS_MAXLINE_WARN:
        rep.add("WARN", "status-longest-line",
                "%s B (warn >%d) — a line that long is a session folded into one paragraph"
                % ("{:,}".format(longest), STATUS_MAXLINE_WARN))
    else:
        rep.add("PASS", "status-longest-line", "%s B (warn >%d)" % ("{:,}".format(longest), STATUS_MAXLINE_WARN))

    # Stacked session records at the top (before the first `## ` heading).
    # A session record written as a heading is still a record, not the dashboard's first heading.
    first_h2 = next((i for i, lvl, _, fenced in headings(lines)
                     if lvl == 2 and not fenced and not SESSION_RECORD_RE.match(lines[i])), n)
    top_records = sum(1 for l in lines[:first_h2] if SESSION_RECORD_RE.match(l))
    all_records = sum(1 for l in lines if SESSION_RECORD_RE.match(l))
    if top_records > 1:
        rep.add("FAIL", "status-session-stack",
                "%d session records stacked above the first heading (%d in the whole file) — STATUS has become a second log; fix the writer instruction first"
                % (top_records, all_records))
    elif top_records == 1:
        rep.add("WARN", "status-session-stack",
                "1 session record at the top (%d in the whole file) — the protocol replaces the top line, it never prepends a record"
                % all_records)
    else:
        rep.add("PASS", "status-session-stack", "0 session records at the top (%d in the whole file)" % all_records)

    # Last-updated date versus the newest CHANGELOG heading date. A line that
    # exists but carries no parseable date is a different defect from no line.
    status_date = None
    lu_line = None
    for l in lines:
        if re.search(r"last\s+updated", l, re.IGNORECASE):
            if lu_line is None:
                lu_line = l.strip()
            m = re.search(r"last\s+updated", l, re.IGNORECASE)
            tail = l[m.end():]
            dates = [d for d in (parse_date(x) for x in DATE_RE.findall(tail) and [g for g in re.findall(r"\d{4}-\d{2}-\d{2}", tail)]) if d]
            status_date = dates[0] if dates else None
            if status_date:
                break
    if status_date is None and lu_line is None:
        rep.add("WARN", "status-last-updated",
                "no 'Last updated: YYYY-MM-DD' line found — the close ritual has nothing to bump")
    elif status_date is None:
        shown = lu_line if len(lu_line) <= 60 else lu_line[:57] + "..."
        rep.add("WARN", "status-last-updated",
                "'Last updated' line present but its date is unparseable (%s) — not YYYY-MM-DD or not a real date; fix the line rather than adding another"
                % shown)
    elif changelog_newest is None:
        rep.add("INFO", "status-last-updated", "%s (no dated CHANGELOG heading to compare against)" % status_date)
    else:
        lag = (changelog_newest - status_date).days
        if lag > 0:
            rep.add("WARN", "status-last-updated",
                    "%s is %d days behind the newest CHANGELOG entry (%s) — STATUS was not rewritten at the last close"
                    % (status_date, lag, changelog_newest))
        else:
            rep.add("PASS", "status-last-updated",
                    "%s, newest CHANGELOG entry %s (lag %d days)" % (status_date, changelog_newest, max(lag, 0)))

    # Past-tense heuristic: lines under a dated heading carrying done-words.
    dated_headings = 0
    past_lines = 0
    open_level = None          # level of the dated section we are inside, or None
    fenced = False
    for l in lines:
        if FENCE_RE.match(l):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = HEADING_RE.match(l)
        if m:
            lvl = len(m.group(1))
            if DATED_HEADING_RE.search(m.group(2)):
                dated_headings += 1
                if open_level is None or lvl <= open_level:
                    open_level = lvl
            elif open_level is not None and lvl <= open_level:
                open_level = None
            continue
        if open_level is not None and PAST_TENSE_RE.search(l):
            past_lines += 1
    if past_lines > PAST_TENSE_WARN or dated_headings > 0 and past_lines > 0:
        level = "WARN" if past_lines > PAST_TENSE_WARN else "INFO"
        rep.add(level, "status-past-tense",
                "%d lines with shipped/landed/deployed/done/fixed/closed under %d dated headings (warn >%d; heuristic — read the sections it names) — that history belongs in CHANGELOG"
                % (past_lines, dated_headings, PAST_TENSE_WARN))
    else:
        rep.add("PASS", "status-past-tense",
                "%d past-tense lines under %d dated headings (warn >%d; heuristic)" % (past_lines, dated_headings, PAST_TENSE_WARN))
    return status_date


def report_dormancy(rep, newest, today):
    if newest is None:
        rep.add("SKIP", "changelog-dormancy", "no dated heading to measure from")
        return
    age = (today - newest).days
    if age < 0:
        rep.add("INFO", "changelog-dormancy",
                "newest entry (%s) is %d days after today (%s) — a future-dated entry or a wrong clock; check the date"
                % (newest, -age, today))
        return
    if age > DORMANT_DAYS_WARN:
        rep.add("WARN", "changelog-dormancy",
                "%d days since the newest entry (%s; warn >%d) — dormant or discipline slipped; ask whether to write a catch-up entry"
                % (age, newest, DORMANT_DAYS_WARN))
    else:
        rep.add("PASS", "changelog-dormancy", "%d days since the newest entry (%s; warn >%d)" % (age, newest, DORMANT_DAYS_WARN))


def check_changelog(rep, register_dir, today):
    """Returns (newest_date, install_date)."""
    text, size = read_text(os.path.join(register_dir, "CHANGELOG.md"))
    lines = split_lines(text)
    if text is None:
        rep.add("FAIL", "changelog-entries", "CHANGELOG.md unreadable")
        return None, None
    h2 = [(i, title, fenced) for i, lvl, title, fenced in headings(lines) if lvl == 2]
    live = [(i, t) for i, t, f in h2 if not f]
    fenced_examples = len(h2) - len(live)
    fenced_note = ", %d fenced example heading(s)" % fenced_examples if fenced_examples else ""
    if not live:
        # No '##' entries. Dated lines outside fences mean the project logs in
        # another shape (bullets, '###' headings) — say so, do not call it empty.
        dated_lines = [d for d in (parse_date(l) for l in unfenced_lines(lines)) if d]
        if dated_lines:
            newest = max(dated_lines)
            rep.add("WARN", "changelog-entries",
                    "0 '##' headings; %d dated line(s) found (%d lines, %s B%s) — entries in another shape? check the README; "
                    "the bootstrap's 'last 3-5 entries' and the format check read '##' headings"
                    % (len(dated_lines), len(lines), "{:,}".format(size), fenced_note))
            report_dormancy(rep, newest, today)
            rep.add("SKIP", "changelog-order", "entries are not '##' headings — the README should say which end is newest")
            rep.add("SKIP", "changelog-heading-format", "no '##' headings to judge")
            return newest, None
        rep.add("WARN", "changelog-entries",
                "0 entries (%d lines, %s B%s) — nothing has been logged"
                % (len(lines), "{:,}".format(size), fenced_note))
        return None, None

    dated = [(i, parse_date(t), t) for i, t in live]
    dated = [(i, d, t) for i, d, t in dated if d]
    newest = max((d for _, d, _ in dated), default=None)
    oldest = min((d for _, d, _ in dated), default=None)
    install = next((d for _, d, t in dated if INSTALL_ENTRY_RE.search(t)), None)
    span = (newest - oldest).days if newest and oldest else 0
    rep.add("INFO", "changelog-entries",
            "%d entries on %d distinct dates spanning %d days (%s B)%s"
            % (len(live), len({d for _, d, _ in dated}), span, "{:,}".format(size),
               "; install entry dated %s" % install if install else "; no install entry found"))

    report_dormancy(rep, newest, today)

    # Newest at top.
    if newest is not None and dated:
        first_date = dated[0][1]
        if first_date != newest:
            rep.add("WARN", "changelog-order",
                    "first entry is dated %s but the newest is %s — CHANGELOG should be newest-at-top; the bootstrap reads the top 3-5"
                    % (first_date, newest))
        else:
            rep.add("PASS", "changelog-order", "newest entry (%s) is at the top" % newest)

    # Heading format conformance.
    ok = sum(1 for _, t in live if CHANGELOG_HEADING_OK_RE.match("## " + t))
    frac = ok / float(len(live))
    tail = "" if not fenced_examples else "; %d heading(s) inside code fences ignored (template examples left behind?)" % fenced_examples
    if frac >= HEADING_CONFORMANCE_PASS:
        rep.add("PASS", "changelog-heading-format",
                "%d of %d headings match '## YYYY-MM-DD — summary' (%.2f, pass >=%.2f)%s" % (ok, len(live), frac, HEADING_CONFORMANCE_PASS, tail))
    else:
        rep.add("WARN", "changelog-heading-format",
                "%d of %d headings match '## YYYY-MM-DD — summary' (%.2f, pass >=%.2f) — undated headings cannot be found by a bootstrap%s"
                % (ok, len(live), frac, HEADING_CONFORMANCE_PASS, tail))
    return newest, install


def check_decisions(rep, register_dir):
    text, size = read_text(os.path.join(register_dir, "DECISIONS.md"))
    lines = split_lines(text)
    if text is None:
        rep.add("FAIL", "decisions-ids", "DECISIONS.md unreadable")
        return
    entries = []         # (index, level, prefix, number, suffix) outside fences, levels 2-3
    malformed = []       # ids wider than ID_MAX_DIGITS, kept out of every census
    template_heads = 0
    fenced_heads = 0
    live_heads = 0       # '##'/'###' headings outside fences that are not template lines
    deep_heads = 0       # headings at '####' or deeper — ids there are a level too deep
    for i, lvl, title, fenced in headings(lines):
        if lvl not in (2, 3):
            if lvl >= 4 and not fenced and not TEMPLATE_HEADING_RE.search(title):
                deep_heads += 1
            continue
        if fenced:
            fenced_heads += 1
            continue
        if TEMPLATE_HEADING_RE.search(title):
            template_heads += 1
            continue
        live_heads += 1
        m = DECISION_ID_RE.match("#" * lvl + " " + title)
        if not m:
            continue
        digits = m.group(2)
        if len(digits) > ID_MAX_DIGITS:
            malformed.append(m.group(1) + digits + (m.group(3) or ""))
            continue
        entries.append((i, lvl, m.group(1), int(digits), m.group(3) or ""))

    def fmt(p, n, s=""):
        return ("%s%03d" % (p, n) if n < 1000 else "%s%d" % (p, n)) + s

    def listing(items, cap):
        return ", ".join(items[:cap]) + (" ..." if len(items) > cap else "")

    if malformed:
        rep.add("WARN", "decisions-id-malformed",
                "%d id(s) wider than %d digits (%s) — a date or a typo used as a number; excluded from the duplicate, order and gap census"
                % (len(malformed), ID_MAX_DIGITS, listing(malformed, 4)))

    if not entries:
        if live_heads or deep_heads:
            if not live_heads:
                rep.add("WARN", "decisions-ids",
                        "0 '##'/'###' headings but %d heading(s) at '####' or deeper (%d lines, %s B) — ids a level too deep are "
                        "invisible to the census and to a bootstrap; promote them to '##'"
                        % (deep_heads, len(lines), "{:,}".format(size)))
                return
            rep.add("WARN", "decisions-ids",
                    "%d '##'/'###' heading(s), none carry a recognisable id (%s; %d lines, %s B) — a project convention the doctor cannot "
                    "census, or entries without ids; check the README, and say there which form is used"
                    % (live_heads, ID_FORMS_TEXT, len(lines), "{:,}".format(size)))
        else:
            rep.add("INFO", "decisions-ids",
                    "0 headings, 0 decision ids (%d lines, %s B) — empty is fine if nothing was deliberated"
                    % (len(lines), "{:,}".format(size)))
    else:
        ids2 = [e for e in entries if e[1] == 2]
        ids3 = [e for e in entries if e[1] == 3]
        # A suffixed id (D-002b) shares its base number's address: same key.
        seen = {2: {}, 3: {}}
        for _, lvl, p, n, _s in entries:
            seen[lvl][(p, n)] = seen[lvl].get((p, n), 0) + 1
        suffixed = sorted({fmt(p, n, s) for _, _, p, n, s in entries if s})
        dups = {lvl: sorted(fmt(p, n) for (p, n), c in seen[lvl].items() if c > 1) for lvl in (2, 3)}
        primary_level = 2 if ids2 else 3
        primary = ids2 if ids2 else ids3
        distinct = len(seen[primary_level])
        # Ids may run in several prefix series (API-D-, UX-D-, D-FW-); max,
        # order and gaps only mean something within one series.
        series = {}                      # prefix -> numbers in file order, primary level
        for _, _, p, n, _s in primary:
            series.setdefault(p, []).append(n)
        if len(series) == 1:
            max_text = "max %d" % max(next(iter(series.values())))
        else:
            max_text = "%d id series, max %s" % (
                len(series), listing([fmt(p, max(ns)) for p, ns in sorted(series.items())], 4))
        suffix_note = "" if not suffixed else "; %d suffixed id(s) (%s) counted as reuse of the base number" % (
            len(suffixed), listing(suffixed, 4))
        level_note = "" if ids2 else " (0 '##' entries; every id sits at '###' level)"
        if dups[2] or dups[3]:
            parts = ["%d at '%s' level (%s)" % (len(dups[lvl]), "#" * lvl, listing(dups[lvl], 8))
                     for lvl in (2, 3) if dups[lvl]]
            rep.add("FAIL", "decisions-ids",
                    "%d entries at '%s' level, %d distinct ids, %s; %d id(s) used more than once: %s — two bodies at one address; "
                    "a correction is a new number that names its target%s%s"
                    % (len(primary), "#" * primary_level, distinct, max_text,
                       len(dups[2]) + len(dups[3]), "; ".join(parts), suffix_note, level_note))
        elif ids2:
            rep.add("PASS", "decisions-ids",
                    "%d '##' entries, %d distinct ids, %s, 0 duplicates at '##' or '###' level%s"
                    % (len(ids2), distinct, max_text, suffix_note))
        else:
            rep.add("WARN", "decisions-ids",
                    "0 '##' entries but %d id heading(s) at '###' level (%d distinct, %s, 0 duplicates) — entries are minted at the wrong level%s"
                    % (len(ids3), distinct, max_text, suffix_note))

        # '###'-level ids: reuse of a '##' id with a qualifier (the class the
        # protocol forbids) versus new ids minted a level too deep.
        if ids3:
            reused = sorted({fmt(p, n) for _, _, p, n, _s in ids3 if (p, n) in seen[2]})
            minted = sorted({fmt(p, n) for _, _, p, n, _s in ids3 if (p, n) not in seen[2]})
            if reused:
                rep.add("WARN", "decisions-id-reuse",
                        "%d '##' id(s) reused with a qualifier at '###' level (%s) — the protocol wants a new numbered entry that names its target, never the old number plus 'correction'"
                        % (len(reused), listing(reused, 6)))
            if minted:
                rep.add("INFO", "decisions-id-level",
                        "%d id(s) minted at '###' level (%s) — invisible to a '##'-only census; promote or accept the convention"
                        % (len(minted), listing(minted, 6)))

        # Monotonic order within each series at the level that carries the
        # ids: ascending (oldest first, the template's rule) or descending.
        judged = [ns for ns in series.values() if len(ns) >= 2]
        if judged:
            asc_breaks = sum(1 for ns in judged for a, b in zip(ns, ns[1:]) if b < a)
            desc_breaks = sum(1 for ns in judged for a, b in zip(ns, ns[1:]) if b > a)
            across = "" if len(series) == 1 else " across %d id series" % len(series)
            if asc_breaks == 0:
                rep.add("PASS", "decisions-order", "ascending (oldest first, as the template prescribes), 0 out-of-order steps%s" % across)
            elif desc_breaks == 0:
                rep.add("INFO", "decisions-order",
                        "descending (newest first) with 0 out-of-order steps%s — consistent, but the template appends at the bottom; say which in the README" % across)
            else:
                breaks = min(asc_breaks, desc_breaks)
                direction = "ascending" if asc_breaks <= desc_breaks else "descending"
                rep.add("WARN", "decisions-order",
                        "mostly %s with %d out-of-order step(s)%s — entries were inserted out of sequence or numbers reused"
                        % (direction, breaks, across))

        # Gaps within each series, over both levels, counted arithmetically.
        series_all = {}
        for _, _, p, n, _s in entries:
            series_all.setdefault(p, []).append(n)
        gap_total = 0
        gap_examples = []
        for p, ns in sorted(series_all.items()):
            count, examples = gap_census(ns)
            gap_total += count
            if len(gap_examples) < 6:
                gap_examples.extend(fmt(p, g) for g in examples[:6 - len(gap_examples)])
        if gap_total:
            if len(series_all) == 1:
                ns = next(iter(series_all.values()))
                where = "between %d and %d" % (min(ns), max(ns))
            else:
                where = "across %d id series" % len(series_all)
            rep.add("INFO", "decisions-gaps",
                    "%d unused id(s) %s (e.g. %s) — minted elsewhere or lost; harmless unless cited"
                    % (gap_total, where, ", ".join(gap_examples)))

    # Leftover template material, outside code fences (fenced examples are
    # counted once, as fenced headings, not again as placeholders).
    body_placeholders = sum(1 for l in unfenced_lines(lines) if PLACEHOLDER_RE.search(l))
    problems = []
    if template_heads:
        problems.append("%d heading(s) still read D-NNNN / ADR-NNN / YYYY-MM-DD / D-XXXX" % template_heads)
    if fenced_heads:
        problems.append("%d heading(s) inside code fences (fenced template example never deleted)" % fenced_heads)
    if body_placeholders:
        problems.append("%d placeholder token(s) such as '<decision in one line>' or '[POPULATE'" % body_placeholders)
    if problems:
        rep.add("WARN", "decisions-template-residue", "; ".join(problems) + " — delete them; they confuse id counts and bootstraps")
    else:
        rep.add("PASS", "decisions-template-residue", "0 template headings, 0 fenced examples, 0 placeholder tokens")


def check_brand(rep, register_dir, install_date):
    path = os.path.join(register_dir, "BRAND.md")
    text, size = read_text(path)
    if text is None:
        rep.add("INFO", "brand-placeholders", "no BRAND.md (fine — keep it only when a real value exists)")
        return
    markers = len(re.findall(r"\[POPULATE", text))
    try:
        mtime = dt.date.fromtimestamp(os.path.getmtime(path))
    except (OSError, OverflowError, ValueError):
        mtime = None
    untouched = install_date is not None and mtime is not None and mtime <= install_date
    if markers == 0:
        rep.add("PASS", "brand-placeholders", "0 [POPULATE] markers in BRAND.md (%s B)" % "{:,}".format(size))
    else:
        note = " and the file has not changed since install day (%s)" % install_date if untouched else ""
        rep.add("WARN", "brand-placeholders",
                "%d [POPULATE] marker(s) still in BRAND.md%s — fill one real value or delete the file; unfilled BRAND files are never filled later"
                % (markers, note))


def check_ancestor_register(rep, root):
    cur = os.path.dirname(root)
    depth = 1
    while cur and cur != os.path.dirname(cur):
        for cand in (cur, os.path.join(cur, "docs")):
            if has_register(cand):
                where = "docs/ of the" if cand != cur else "the"
                rep.add("WARN", "nested-register",
                        "a second register sits in %s ancestor %d level(s) up — two registers with no ownership rule is how a session writes to the wrong one; say which owns this work in both READMEs"
                        % (where, depth))
                return
        cur = os.path.dirname(cur)
        depth += 1
    rep.add("PASS", "nested-register", "no register in any ancestor directory")


def check_sibling_register(rep, root, register_dir):
    """The other candidate location — root when the register is in docs/, docs/
    when it is at the root — must not carry a second full register."""
    docs = os.path.join(root, "docs")
    other = root if same_path(register_dir, docs) else docs
    if has_register(other) and not same_path(other, register_dir):
        rep.add("WARN", "sibling-register",
                "a second STATUS/CHANGELOG/DECISIONS set sits at %s beside the one at %s — the doctor read only the %s set; "
                "two registers with no ownership rule is how a session writes to the wrong one; say which owns this work in both READMEs"
                % (rel_label(other, root), rel_label(register_dir, root), rel_label(register_dir, root)))
    else:
        rep.add("PASS", "sibling-register", "no second register at %s" % rel_label(other, root))


def check_git(rep, root, register_dir, no_git):
    if no_git:
        rep.add("SKIP", "git-status-churn", "git checks disabled (--no-git)")
        return
    if not shutil.which("git"):
        rep.add("SKIP", "git-status-churn", "git not installed — churn cannot be measured (STATUS size and session-stack checks cover the same failure)")
        return
    top = run_git(root, ["rev-parse", "--show-toplevel"])
    if top is None:
        rep.add("SKIP", "git-status-churn", "not inside a git repository — churn cannot be measured (STATUS size and session-stack checks cover the same failure)")
        return
    top = top.strip()
    try:
        rel_root = os.path.relpath(os.path.realpath(root), os.path.realpath(top))
    except ValueError:
        rel_root = "."
    if rel_root not in (".", ""):
        rep.add("INFO", "git-repository",
                "project root is %d level(s) below the repository root — registers share one index with everything above"
                % (rel_root.count(os.sep) + 1))
    else:
        rep.add("INFO", "git-repository", "project root is the repository root")
    status_rel = os.path.relpath(os.path.join(register_dir, "STATUS.md"), root)
    out = run_git(root, ["log", "--numstat", "--format=%H", "--", status_rel])
    if not out:
        rep.add("SKIP", "git-status-churn", "STATUS.md has no commits in this repository")
        return
    commits = added = deleted = 0
    for line in out.splitlines():
        if re.fullmatch(r"[0-9a-f]{7,40}", line.strip()):
            commits += 1
            continue
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            added += int(parts[0])
            deleted += int(parts[1])
    if commits < CHURN_MIN_COMMITS:
        rep.add("INFO", "git-status-churn",
                "%d commits touching STATUS.md (+%d/-%d lines) — fewer than %d, too few to judge churn"
                % (commits, added, deleted, CHURN_MIN_COMMITS))
        return
    ratio = (deleted / float(added)) if added else 0.0
    if ratio < CHURN_RATIO_WARN:
        rep.add("WARN", "git-status-churn",
                "deleted/added = %d/%d = %.2f over %d commits (warn <%.1f) — STATUS is being appended to, not rewritten"
                % (deleted, added, ratio, commits, CHURN_RATIO_WARN))
    else:
        rep.add("PASS", "git-status-churn",
                "deleted/added = %d/%d = %.2f over %d commits (warn <%.1f) — STATUS is being rewritten"
                % (deleted, added, ratio, commits, CHURN_RATIO_WARN))


# --- main ---------------------------------------------------------------

def run(root, today, no_git):
    rep = Report()
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        print("docs-doctor: not a directory: %s" % root, file=sys.stderr)
        return 2
    register_dir = find_register(root)
    if register_dir is None:
        print("docs-doctor: no register (STATUS.md + CHANGELOG.md + DECISIONS.md) at %s or %s/docs"
              % (root, root), file=sys.stderr)
        return 2
    note = ""
    # The docs directory itself was passed: the instructions files live one up.
    if (register_dir == root and os.path.basename(root) == "docs"
            and not any(os.path.isfile(os.path.join(root, f)) for f in INSTRUCTION_FILES)):
        root = os.path.dirname(root)
        note = " — a docs/ directory was given; treating its parent as the project root"
    print("docs-doctor %s — register at %s (relative to the project root), today %s%s"
          % (VERSION, rel_label(register_dir, root), today, note))
    print()
    check_wiring(rep, root, rel_label(register_dir, root))
    check_readme_footer(rep, register_dir)
    newest, install = check_changelog(rep, register_dir, today)
    check_status(rep, register_dir, newest, today)
    check_decisions(rep, register_dir)
    check_brand(rep, register_dir, install)
    check_ancestor_register(rep, root)
    check_sibling_register(rep, root, register_dir)
    check_git(rep, root, register_dir, no_git)
    print()
    c = rep.counts
    code = rep.exit_code()
    print("%d checks: %d pass, %d warn, %d fail, %d info, %d skipped — exit %d"
          % (sum(c.values()), c["PASS"], c["WARN"], c["FAIL"], c["INFO"], c["SKIP"], code))
    return code


def main(argv=None):
    # The report uses em dashes; never let a non-UTF-8 stdout turn that into a crash.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(
        prog="docs-doctor",
        description="Read-only health check for a project-docs-protocol installation.",
    )
    ap.add_argument("root", help="project root (the directory holding CLAUDE.md/AGENTS.md; the register may be there or under docs/)")
    ap.add_argument("--today", help="date to measure dormancy from (YYYY-MM-DD); default: today", default=None)
    ap.add_argument("--no-git", action="store_true", help="skip git-based checks even when git is available")
    ap.add_argument("--version", action="version", version="docs-doctor %s" % VERSION)
    args = ap.parse_args(argv)
    today = parse_date(args.today) if args.today else dt.date.today()
    if args.today and today is None:
        print("docs-doctor: --today must be YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        return run(args.root, today, args.no_git)
    except Exception as exc:  # noqa: BLE001 — a crash is exit 2, never a silent pass
        print("docs-doctor: checker error: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
