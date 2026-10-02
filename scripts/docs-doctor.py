#!/usr/bin/env python3
"""docs-doctor — health check for a project-docs-protocol installation.

Usage:
    python3 docs-doctor.py <project-root> [--today YYYY-MM-DD] [--no-git]

Reads the register (STATUS.md, CHANGELOG.md, DECISIONS.md, plus README.md,
BRAND.md and LEDGER.md when present) at <project-root> or
<project-root>/docs/, and the agent-instructions files (CLAUDE.md,
AGENTS.md) at the project root. LEDGER-ARCHIVE.md is checked only for ID
syntax and collisions; its row semantics are outside the Doctor boundary.
Prints one line per check — PASS / WARN / FAIL / INFO / SKIP — with the
measured value and its unit, then a summary line.

Exit codes:
    0   every check passed (INFO and SKIP lines do not count)
    1   at least one WARN and no FAIL — advisory drift, judge each line
    2   at least one FAIL — a protocol property is broken
    3   the checker itself could not run (no such root, no register, crash)

The doctor never modifies anything. It reads files, runs read-only git
commands when git and a repository are available, and prints. Standard
library only; no third-party dependencies; git is optional.

Structural health does not establish semantic accuracy, independent
verification, product acceptance, historical byte integrity or actual write
order. A final diff cannot prove which file was written first.

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

VERSION = "1.5.0"
STRUCTURAL_LIMITS = (
    "Structural health does not establish semantic accuracy, independent "
    "verification, product acceptance, historical byte integrity or actual write order. "
    "A link/hash cannot prove an observation happened; a final diff cannot prove write order."
)

REGISTER = ("STATUS.md", "CHANGELOG.md", "DECISIONS.md")
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")

# Keep direct CLI and importlib callers on the same discovery implementation.
try:
    import register_paths
except ModuleNotFoundError:
    from scripts import register_paths

# --- thresholds (from the audit) ---------------------------------------
STATUS_LINES_WARN = 60         # lines; template is ~40, healthy mature ~40
STATUS_LINES_FAIL = 100
STATUS_MAXLINE_WARN = 1024     # bytes; one line over ~1 KB is history in disguise
PAST_TENSE_WARN = 3            # lines; heuristic, see check
DORMANT_DAYS_WARN = 30         # days since the newest CHANGELOG entry
HEADING_CONFORMANCE_PASS = 0.95
CHURN_MIN_COMMITS = 10         # commits touching STATUS before churn is judged
CHURN_RATIO_WARN = 0.2         # deleted/added; rewritten files sit near 0.7-0.8
ID_MAX_DIGITS = 6              # a decision number wider than this is malformed
                               # (a date, a typo) and never enters the span
# --- ledger thresholds (templates/LEDGER.md's banner is the schema) -----
LEDGER_STALE_DAYS = 60         # days since last touch; INFO with the count over it
LEDGER_STALE_P01_DAYS = 30     # a P0/P1 row over this is a WARN
LEDGER_LIVE_WARN = 100         # live rows; the file stops being read whole
LEDGER_LIVE_FAIL = 250
LEDGER_TAGS_MAX = 12           # declared +tokens on the Tags: line
LEDGER_ID_MAX_DIGITS = 12      # wider IDs are malformed; never pass to int()

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
# CommonMark allows up to three spaces of indentation before an ATX heading.
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>")
LIST_LINE_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
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
# DECISIONS id. Covered forms:
#   D-NNNN            the template's default
#   PREFIX-D-NNN      any chain of upper-case/digit prefixes: PROJ-D-012, API-D-003, UX-D-002
#   D-XX-NNN          a series tag between D and the number: D-FW-007
#   ADR-NNN, DEC-NNN  the common alternative conventions, prefixable the same way
#   [tag] D-NNNN      an optional bracketed tag before the id: [Phase 2B] D-0025
#   D-NNNNb           a letter-suffixed id reuses its base number (counted as a reuse)
# Group 1 is everything before the digits (the "prefix"), group 2 the digits,
# group 3 the optional letter suffix. DECISION_ID_RE is the heading form at
# level 2 or 3; DECISION_TITLE_RE the same on a bare title (any level);
# DECISION_CITE_RE finds the id forms anywhere in a line of text.
DECISION_ID_CORE = r"((?:[A-Z][A-Z0-9]*-)*(?:D|ADR|DEC)-(?:[A-Z]+-)?)(\d+)([a-z])?\b"
DECISION_ID_RE = re.compile(r"^#{2,3}\s+(?:\[[^\]]*\]\s*)?" + DECISION_ID_CORE)
DECISION_TITLE_RE = re.compile(r"^(?:\[[^\]]*\]\s*)?" + DECISION_ID_CORE)
DECISION_CITE_RE = re.compile(r"(?<![A-Za-z0-9])" + DECISION_ID_CORE)
ID_FORMS_TEXT = "D-NNNN, PREFIX-D-NNN, D-XX-NNN, ADR-NNN, DEC-NNN"
TEMPLATE_HEADING_RE = re.compile(r"D-NNNN|YYYY-MM-DD|D-XXXX|ADR-NNN|ADR-MMM|DEC-NNN|D-XX-NNN|<title>")
PLACEHOLDER_RE = re.compile(r"<decision in one line>|\[POPULATE|<path>|<one[- ]line")
# STATUS template placeholders: the bracketed prompts the template ships, and
# any list item whose bold text opens with a bracket ("1. **[one-line question]**").
STATUS_PLACEHOLDER_RE = re.compile(
    r"\[one-line question|\[option label\]|\[The ordered queue|\[Section name|\[Item\b"
    r"|^\s*(?:[-*+]|\d+[.)])\s+\*\*\["
)
INSTALL_ENTRY_RE = re.compile(r"initiali[sz]ed\b.*\bdocumentation system", re.IGNORECASE)
# The README install footer, judged on a visible line with any leading
# emphasis or quote marker removed; it must open the line.
FOOTER_LINE_RE = re.compile(r"^Installed via the `?project-docs-protocol`? skill")
FOOTER_PHRASE_RE = re.compile(r"Installed via the `?project-docs-protocol`? skill", re.IGNORECASE)
FOOTER_NEGATION_RE = re.compile(r"not installed|was not|never installed|wasn't|isn't|is not|\bnever\b|\bnot\b|\bno\b", re.IGNORECASE)
LINE_PREFIX_RE = re.compile(r"^[\s*_>]+")

# The three clauses the current Step-2 wiring block carries. A block that
# lacks one was copied from an older SKILL.md and should be re-synced.
WIRING_CLAUSES = (
    ("rewritten-not-appended", re.compile(r"rewritten,?\s+not\s+appended", re.IGNORECASE)),
    ("bounded-read", re.compile(r"under\s+~?\s*60\s+lines|in\s+full\s+if\s+it\s+is\s+under", re.IGNORECASE)),
    ("precedence", re.compile(r"\*\*\s*Precedence\s*\.?\s*\*\*|^\s*-\s*Precedence\b", re.IGNORECASE | re.MULTILINE)),
)
# The block is present when its heading (level 2 or 3) or its opening
# sentence is present on a visible, unquoted line. A bare mention of the
# skill's name is not a block. The block's span is bounded (see
# wiring_block_span) and only text inside the span is clause- and path-checked.
WIRING_HEADING_RE = re.compile(r"^ {0,3}(#{2,3})\s+Project docs protocol\b", re.IGNORECASE)
WIRING_SENTENCE_RE = re.compile(r"This project uses the project-docs-protocol", re.IGNORECASE)
WIRING_MENTION_RE = re.compile(r"project-docs-protocol", re.IGNORECASE)
WIRING_SENTENCE_SPAN_MAX = 40  # lines after the sentence, when there is no heading
# "(docs in `docs/`)" — the block's declaration of where the register lives.
DOCS_PATH_RE = re.compile(r"\(\s*docs\s+(?:in|at|under)\s+`?([^`)]*?)`?\s*\)", re.IGNORECASE)
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

# --- ledger (templates/LEDGER.md) ------------------------------------------
# The header row must equal these ten names, cells trimmed, case exact.
LEDGER_COLUMNS = ("ID", "P", "Status", "Date", "Title", "Tags",
                  "Closes-when", "Blocked-on", "Touches", "Evidence")
LEDGER_STATUSES = ("OPEN", "BLOCKED", "VERIFYING", "CLOSED", "NOT-AN-ISSUE", "SUPERSEDED")
LEDGER_TERMINAL = ("CLOSED", "NOT-AN-ISSUE", "SUPERSEDED")
LEDGER_PRIORITIES = ("P0", "P1", "P2", "P3")
LEDGER_TOMBSTONE = "DO-NOT-RESURRECT"
# A GFM separator row: pipes, dashes, colons and spaces, at least one dash.
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
# ...but separator *shape* is not enough. GFM builds a table only when the
# delimiter row has exactly as many cells as the header and every cell is
# dashes with optional alignment colons; otherwise the lines are a paragraph.
TABLE_DELIM_CELL_RE = re.compile(r"^:?-+:?$")
TABLE_ROW_RE = re.compile(r"^ {0,3}\|")
# An escaped pipe is replaced by this before splitting; a pipe inside a
# backtick code span is NOT protected — GFM splits the cell there too.
PIPE_STAND_IN = "\ue000"       # a private-use code point no register writes
# Row id: LG-NNNN, or PREFIX-LG-NNNN with an upper-case/digit prefix chain.
LEDGER_ID_RE = re.compile(r"^((?:[A-Z][A-Z0-9]*-)*)LG-(\d+)$")
LEDGER_ID_CITE_RE = re.compile(r"(?<![A-Za-z0-9])((?:[A-Z][A-Z0-9]*-)*)LG-(\d+)\b")
# The Tags grammar: '+', a lowercase letter, then lowercase letters, digits
# or hyphens. '+1', '+Auth' and 'a+b' are text, not tags.
TAG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_+])\+[a-z][a-z0-9-]*(?![A-Za-z0-9_])")
TAG_TITLE_TAIL_RE = re.compile(r"((?:\s+\+[a-z][a-z0-9-]*)+)\s*$")
TAGS_LINE_RE = re.compile(r"^\s*Tags:(.*)$")
# Closes-when that opens with a disposition word is a status wearing a
# different name; a yes/no condition never starts this way.
DISPOSITION_RE = re.compile(
    r"^\W*(?:CLOSED|VERIFIED|DONE|FIXED|RESOLVED|COMPLETED?|SHIPPED|OPEN|BLOCKED|SUPERSEDED"
    r"|NOT-AN-ISSUE|WON[’']T\s+FIX|N/A)\b",
    re.IGNORECASE,
)


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
        if self.counts["FAIL"]:
            return 2
        if self.counts["WARN"]:
            return 1
        return 0


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

# --- Markdown visibility for the supported register syntax -----------------
# Four columns of indentation past the current container's content baseline
# make a code block. That is how a document *quotes* a block it is describing
# instead of installing it, so those lines are as invisible as fenced ones.
INDENT_CODE_WIDTH = 4
# A bullet or ordered marker: up to three spaces, the marker, then its padding
# and the rest of the line (both captured so `-foo` can be rejected).
LIST_MARKER_RE = re.compile(r"^( {0,3})([-*+]|\d{1,9}[.)])( *)(.*)$")
# `- - -`, `***`, `___`: a thematic break, which wins over a bullet marker.
THEMATIC_BREAK_RE = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")


def indent_width(line):
    """Columns of leading whitespace, a tab advancing to the next four-column
    tab stop, the way CommonMark measures indentation."""
    col = 0
    for ch in line:
        if ch == " ":
            col += 1
        elif ch == "\t":
            col += INDENT_CODE_WIDTH - (col % INDENT_CODE_WIDTH)
        else:
            break
    return col


def list_content_column(line):
    """The column a list item's content starts at, or None if `line` is not a
    list marker line.

    CommonMark: content begins after the marker plus one to four spaces of
    padding; an empty item, or five or more spaces, puts the content one
    column past the marker (the surplus is code *inside* the item). `-foo`
    and `1.x` are paragraphs, not markers, and a thematic break is not a
    marker either.
    """
    if THEMATIC_BREAK_RE.match(line):
        return None
    m = LIST_MARKER_RE.match(line.expandtabs(INDENT_CODE_WIDTH))
    if not m:
        return None
    pad, rest = m.group(3), m.group(4)
    if not pad and rest:
        return None
    marker_end = len(m.group(1)) + len(m.group(2))
    if rest and 1 <= len(pad) <= INDENT_CODE_WIDTH:
        return marker_end + len(pad)
    return marker_end + 1


def fence_opener(line):
    """(marker char, opener length) when `line` opens a code fence, else None."""
    fm = FENCE_RE.match(line)
    if not fm or (fm.group(2)[0] == "`" and "`" in fm.group(3)):
        # A backtick opener cannot carry backticks anywhere in its info string.
        return None
    return fm.group(2)[0], len(fm.group(2))


def visible_lines(lines):
    """Yield visible (index, line, False), removing list-container indentation.

    This is a small visibility filter, not a general Markdown parser. It
    handles the fenced/indented examples, comments and list containers used
    by the registers. List-relative headings must reach downstream checks as
    headings; four columns *inside* a list item must remain hidden code. An
    existing paragraph can continue indented without becoming code.

    Authored CLI cases and a separate development-parser snapshot document
    the supported boundaries in tests/fixtures/markdown-oracle/.
    """
    fenced = None   # (marker character, opener length, container baseline)
    comment = False
    code = None     # container baseline of an indented code block
    stack = []      # (content column, list kind, has content), outermost first
    prev = "start"  # the previous processed line: start / blank / block / para
    for i, line in enumerate(lines):
        # Expanding before slicing keeps tab stops tied to document columns.
        line = line.expandtabs(INDENT_CODE_WIDTH)
        blank = not line.strip()
        ind = indent_width(line)
        if comment:
            if COMMENT_CLOSE in line:
                comment = False
                prev = "block"
                rest = line[line.index(COMMENT_CLOSE) + len(COMMENT_CLOSE):]
                if rest.strip():
                    yield i, rest, fenced is not None
            continue
        if fenced is not None:
            # A list's fence ends with its container, or a matching closer.
            if not blank and ind < fenced[2]:
                fenced = None
                prev = "block"
            else:
                cm = FENCE_CLOSE_RE.match(line[fenced[2]:])
                if cm and cm.group(1)[0] == fenced[0] and len(cm.group(1)) >= fenced[1]:
                    fenced = None
                    prev = "block"
                continue

        if code is not None:
            if blank or ind >= code + INDENT_CODE_WIDTH:
                continue
            code = None
            prev = "block"
        if blank:
            prev = "blank"
            yield i, "", False
            continue

        # Match existing containers first, then look for a marker relative to
        # that baseline. A marker beyond document column three can be a live
        # nested list marker; its indentation is not top-level code.
        matched = len(stack)
        while matched and stack[matched - 1][0] > ind:
            matched -= 1
        baseline = stack[matched - 1][0] if matched else 0
        # An empty list item followed by a blank line cannot absorb an
        # indented top-level code block. CommonMark closes the item before
        # parsing four-column code; retaining it would expose a fenced example
        # after ``-\n\n    - - ```markdown`` as live list content.
        if (matched and matched == len(stack) and prev == "blank" and
                ind >= INDENT_CODE_WIDTH and not stack[-1][2]):
            matched -= 1
            baseline = stack[matched - 1][0] if matched else 0
        relative = line[baseline:]
        # Resolve every marker which begins at the current content baseline.
        # CommonMark permits containers to open on the same physical line
        # (``- - ```markdown``). Looking only at the first marker leaves the
        # inner fence visible and can make quoted wiring appear live.
        marker = None
        marker_col = None
        content = relative
        marker_baseline = baseline
        opened = []
        marker_code = False
        while True:
            candidate_col = list_content_column(content)
            candidate = LIST_MARKER_RE.match(content) if candidate_col is not None else None
            if candidate is None:
                break
            if prev == "para" and marker is None:
                kind = candidate.group(2)[-1]
                # A sibling marker may shift by up to three columns while still
                # falling before the old item's content baseline. Compare the
                # first unmatched container's kind, not the old marker column.
                sibling = matched < len(stack) and stack[matched][1] == kind
                root_transition = bool(stack) and matched == 0
                # A newly nested ordered list can interrupt a paragraph only at
                # 1; an empty item cannot interrupt it. Existing siblings may
                # continue with any number.
                if not root_transition and not sibling and (not candidate.group(4) or
                                    (candidate.group(2)[0].isdigit() and int(candidate.group(2)[:-1]) != 1)):
                    break
            marker = candidate
            marker_col = candidate_col
            content_baseline = marker_baseline + candidate_col
            opened.append((content_baseline, candidate.group(2)[-1], bool(candidate.group(4).strip())))
            content = line[content_baseline:]
            marker_baseline = content_baseline
            if content.strip() and indent_width(content) >= INDENT_CODE_WIDTH:
                code = content_baseline
                prev = "block"
                content = ""
                marker_code = True
                break

        opener = fence_opener(content)
        starts_block = (marker is not None or opener is not None
                        or HEADING_RE.match(relative) is not None
                        or THEMATIC_BREAK_RE.match(relative) is not None
                        or BLOCKQUOTE_RE.match(relative) is not None)
        lazy = matched < len(stack) and not starts_block and prev == "para"
        if lazy:
            baseline = min(ind, stack[-1][0])
            relative = line[baseline:]
        else:
            del stack[matched:]
            stack.extend(opened)

        if marker_code:
            continue

        if marker is None and ind - baseline >= INDENT_CODE_WIDTH and prev != "para":
            code = baseline
            prev = "block"
            continue

        if opener is not None or HEADING_RE.match(content) or THEMATIC_BREAK_RE.match(content):
            prev = "block"
        elif marker is not None and not content.strip():
            prev = "block"
        else:
            prev = "para"

        if opener is not None:
            fenced = opener + (stack[-1][0] if marker is not None else baseline,)
            continue
        line = relative
        if COMMENT_OPEN in line:
            # A comment that opens and closes on one line is cut out of it; the
            # text around it is still a live line. One that opens mid-line hides
            # only what follows it.
            head = line[:line.index(COMMENT_OPEN)]
            after = line[line.index(COMMENT_OPEN) + len(COMMENT_OPEN):]
            if COMMENT_CLOSE in after:
                rest = head + after[after.index(COMMENT_CLOSE) + len(COMMENT_CLOSE):]
                if rest.strip():
                    yield i, rest, False
                continue
            if TABLE_ROW_RE.match(line):
                # An unclosed opener inside a table row is literal cell text (GFM
                # still renders the rows below it); it never hides the file.
                yield i, line, False
                continue
            comment = True
            if head.strip():
                yield i, head, False
            continue
        if (marker is None and stack and matched == len(stack) and line.strip()
                and not stack[-1][2]):
            col, kind, _ = stack[-1]
            stack[-1] = (col, kind, True)
        yield i, line, False


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
    return register_paths.has_register(d)


def find_register(root, explicit=None):
    return str(register_paths.select_register(root, explicit))


def rel_label(register_dir, root):
    rel = os.path.relpath(register_dir, root)
    return "./" if rel == "." else rel + "/"


def same_path(a, b):
    return os.path.realpath(a) == os.path.realpath(b)


def normalise_docs_path(s):
    """Reduce a docs-path spelling to a comparable token: 'docs', 'root', or
    the cleaned path. `./docs/`, `docs`, `docs/` -> docs; `./`, `.`, `root`,
    `the root`, `` -> root."""
    s = (s or "").strip().strip("`\"'").strip().lower()
    # "the root", "project root", "repository root", "repo root" all name the root.
    s = re.sub(r"^(?:(?:the|this|project|repository|repo)\s+)+", "", s).strip()
    while s.startswith("./"):
        s = s[2:]
    s = s.strip("/")
    if s in ("", ".", "root"):
        return "root"
    return s


def docs_path_label(token):
    return "./" if token == "root" else token + "/"


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


def close_order_found(lines):
    """True when the lines name CHANGELOG before STATUS within a few lines,
    with an action or ordering cue in the same window."""
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


def wiring_block_span(vis):
    """Locate the wiring block in a list of visible, unquoted lines.

    Returns (form, start, end) with end exclusive, or None. The heading form
    spans from the heading to the next heading of the same or higher level.
    The sentence form spans the sentence's paragraph through the bullet list
    that follows it: it stops at a heading, at a blank line followed by a
    non-list line, or WIRING_SENTENCE_SPAN_MAX lines after the sentence.
    """
    for i, line in enumerate(vis):
        m = WIRING_HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        end = len(vis)
        for j in range(i + 1, len(vis)):
            h = HEADING_RE.match(vis[j])
            if h and len(h.group(1)) <= level:
                end = j
                break
        return "heading", i, end
    for i, line in enumerate(vis):
        if not WIRING_SENTENCE_RE.search(line):
            continue
        start = i
        while start > 0 and vis[start - 1].strip() and not HEADING_RE.match(vis[start - 1]):
            start -= 1
        limit = min(len(vis), i + 1 + WIRING_SENTENCE_SPAN_MAX)
        end = limit
        j = i + 1
        while j < limit:
            cur = vis[j]
            if HEADING_RE.match(cur):
                end = j
                break
            if not cur.strip():
                k = j + 1
                while k < limit and not vis[k].strip():
                    k += 1
                if k >= limit or not LIST_LINE_RE.match(vis[k]):
                    end = j
                    break
                j = k
                continue
            j += 1
        return "sentence", start, end
    return None


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
        rep.add("SKIP", "wiring-path", "no wiring block to compare")
        return
    # Only text outside code fences, HTML comments and blockquotes counts:
    # a quoted or fenced block is not a block.
    visible = {n: [l for l in unfenced_lines(split_lines(t)) if not BLOCKQUOTE_RE.match(l)]
               for n, t in present.items()}
    spans = {}
    for n, vis in visible.items():
        found = wiring_block_span(vis)
        if found:
            spans[n] = "\n".join(vis[found[1]:found[2]])
    wired = sorted(spans)
    if not wired:
        files = ", ".join(sorted(present))
        close_order = sorted(n for n, vis in visible.items() if close_order_found(vis))
        mention = sorted(n for n, vis in visible.items() if any(WIRING_MENTION_RE.search(l) for l in vis))
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
                    "'This project uses the project-docs-protocol' is present on a visible, unquoted line (%d instructions files: %s) "
                    "— mentioned but no block; propose Install step 2"
                    % (", ".join(mention), len(present), files))
            rep.add("SKIP", "wiring-clauses", "no wiring block to compare")
        else:
            rep.add("FAIL", "wiring-block",
                    "0 of %d instructions files (%s) carry the 'Project docs protocol' block or any close-order instruction "
                    "naming CHANGELOG then STATUS on a visible, unquoted line — the register is not wired"
                    % (len(present), files))
            rep.add("SKIP", "wiring-clauses", "no wiring block to compare")
        rep.add("SKIP", "wiring-path", "no wiring block to compare")
        return
    unwired = sorted(set(present) - set(wired))
    note = "" if not unwired else " (missing from %s)" % ", ".join(unwired)
    rep.add("PASS", "wiring-block",
            "present in %d of %d instructions files: %s%s" % (len(wired), len(present), ", ".join(wired), note))

    # Clause currency: every wired file should carry all three current
    # clauses inside the block's span; clauses elsewhere in the file do not count.
    stale = {}
    for name in wired:
        missing = [label for label, rx in WIRING_CLAUSES if not rx.search(spans[name])]
        if missing:
            stale[name] = missing
    if stale:
        parts = ["%s lacks %s" % (n, "+".join(m)) for n, m in sorted(stale.items())]
        rep.add("WARN", "wiring-clauses",
                "%d of 3 current clauses missing inside the block — %s; block predates the current SKILL.md, or its clauses "
                "sit outside it; re-sync it"
                % (max(len(m) for m in stale.values()), "; ".join(parts)))
    else:
        rep.add("PASS", "wiring-clauses",
                "3 of 3 current clauses present inside the block (rewritten-not-appended, bounded-read, precedence) in %s"
                % ", ".join(wired))

    # Docs path: the block's "(docs in `X/`)" must name where the register was found.
    actual = normalise_docs_path(register_label)
    mismatched = []
    unstated = []
    for name in wired:
        m = DOCS_PATH_RE.search(spans[name])
        if not m:
            unstated.append(name)
            continue
        declared = normalise_docs_path(m.group(1))
        if declared != actual:
            mismatched.append((name, declared))
    if mismatched:
        parts = ["%s says docs in %s" % (n, docs_path_label(d)) for n, d in mismatched]
        rep.add("FAIL", "wiring-path",
                "block says docs in %s, register found at %s — %s; a session following the block reads or writes a register "
                "that is not there; fix the block's path (Install step 2)"
                % (docs_path_label(mismatched[0][1]), docs_path_label(actual), "; ".join(parts)))
    elif unstated:
        rep.add("WARN", "wiring-path",
                "block names no docs path in %s (expected '(docs in `%s`)'); register found at %s — add the path so the "
                "block says where the register is"
                % (", ".join(unstated), docs_path_label(actual), docs_path_label(actual)))
    else:
        rep.add("PASS", "wiring-path",
                "block says docs in %s, register found at %s (%s)" % (docs_path_label(actual), docs_path_label(actual), ", ".join(wired)))


def check_readme_footer(rep, register_dir):
    text, _ = read_text(os.path.join(register_dir, "README.md"))
    if text is None:
        rep.add("WARN", "readme-footer", "no README.md in the register directory — the map file is missing")
        return
    footer = negated = inline = mention = 0
    for line in unfenced_lines(split_lines(text)):
        bare = LINE_PREFIX_RE.sub("", line)
        if FOOTER_LINE_RE.match(bare):
            # A declaration is valid only when the whole visible line remains
            # affirmative. Suffixes such as “; this was not installed” revoke
            # the apparent prefix and must not pass the census.
            if not FOOTER_NEGATION_RE.search(bare):
                footer += 1
            else:
                negated += 1
            continue
        m = FOOTER_PHRASE_RE.search(bare)
        if m:
            if FOOTER_NEGATION_RE.search(bare[:m.start()]) or FOOTER_NEGATION_RE.search(bare[m.end():]):
                negated += 1
            else:
                inline += 1
            continue
        if WIRING_MENTION_RE.search(bare):
            mention += 1
    if footer:
        rep.add("PASS", "readme-footer", "install footer present in README.md on its own line")
    elif negated:
        rep.add("WARN", "readme-footer",
                "README.md says the register was *not* installed via the skill (%d negated line(s)) — not an installation; "
                "a pre-existing register the skill must wire and reconcile, never overwrite" % negated)
    elif inline:
        rep.add("WARN", "readme-footer",
                "the install-footer phrase appears mid-line (%d line(s)) but not as its own line — quoted or described, not "
                "declared; restore the template's footer line if this register was installed by the skill" % inline)
    elif mention:
        rep.add("WARN", "readme-footer",
                "README.md mentions project-docs-protocol but has no install footer — a bespoke or pre-skill register?")
    else:
        rep.add("WARN", "readme-footer",
                "README.md carries no install footer — the register may predate the skill or come from another convention")


def status_metadata_lines(lines):
    """Visible STATUS lines outside quoted paragraphs, including lazy tails.

    Layer this narrow quote check over the existing visibility filter rather
    than changing how other register checks interpret Markdown. Blank lines,
    hidden blocks and paragraph-interrupting blocks end a lazy quote. Quoted
    fences, headings, breaks and indented code cannot start a lazy paragraph.
    """
    quoted_paragraph = False
    quoted_fence = None
    previous = -1
    for index, line, fenced in visible_lines(lines):
        if index != previous + 1:
            quoted_paragraph, quoted_fence = False, None
        previous = index
        body = line
        column = list_content_column(body)
        while column is not None:
            body = body[column:]
            column = list_content_column(body)
        quote = BLOCKQUOTE_RE.match(body)
        if quote:
            while re.match(r"^ {0,3}>[ ]?", body):
                body = re.sub(r"^ {0,3}>[ ]?", "", body, count=1)
            if quoted_fence:
                closer = FENCE_CLOSE_RE.match(body)
                if closer and closer.group(1)[0] == quoted_fence[0] and len(closer.group(1)) >= quoted_fence[1]:
                    quoted_fence = None
                quoted_paragraph = False
                continue
            # A quote can contain a list whose paragraph has a lazy tail.
            column = list_content_column(body)
            while column is not None:
                body = body[column:]
                column = list_content_column(body)
            quoted_fence = fence_opener(body)
            quoted_paragraph = bool(body.strip()) and not (
                quoted_fence or HEADING_RE.match(body) or THEMATIC_BREAK_RE.match(body)
                or re.match(r"^ {0,3}=+\s*$", body)
                or (indent_width(body) >= INDENT_CODE_WIDTH and not quoted_paragraph))
            continue
        quoted_fence = None
        if quoted_paragraph:
            marker = LIST_MARKER_RE.match(line) if list_content_column(line) is not None else None
            list_interrupt = marker and marker.group(4).strip() and (
                not marker.group(2)[0].isdigit() or int(marker.group(2)[:-1]) == 1)
            if line.strip() and not (HEADING_RE.match(line) or THEMATIC_BREAK_RE.match(line)
                                     or fence_opener(line) or list_interrupt):
                continue
        quoted_paragraph = False
        if not fenced:
            yield index, line


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

    # The content checks below read visible lines only: a commented-out or
    # fenced template example is not a session record, a date, or history.
    vis = list(unfenced_lines(lines))

    # A dashboard may use a project-specific heading hierarchy, but repeated
    # canonical headings at the same level and in the same parent scope make
    # the current state ambiguous.  This is deliberately advisory: historical
    # dated sections, examples, and separate nested scopes are left alone.
    canonical = {"current phase", "in flight", "blocked", "deferred",
                 "next", "open questions (owner)"}
    heading_stack = []
    heading_groups = {}
    for index, level, title, fenced in headings(lines):
        if fenced:
            continue
        clean = re.sub(r"\s+#+\s*$", "", title)
        clean = re.sub(r"[*_`]+", "", clean).strip().casefold()
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        historical = (level > 1 and bool(DATED_HEADING_RE.search(clean))) or any(item[2] for item in heading_stack)
        parent = heading_stack[-1][1] if heading_stack else None
        if clean in canonical and not historical:
            heading_groups.setdefault((level, clean, parent), []).append(index + 1)
        heading_stack.append((level, index, historical))
    duplicate_groups = [locations for locations in heading_groups.values()
                        if len(locations) > 1]
    if duplicate_groups:
        shown = "; ".join("lines " + ", ".join(str(n) for n in locations)
                           for locations in duplicate_groups)
        rep.add("WARN", "status-headings",
                "%d repeated canonical current-state heading group(s): %s — Doctor cannot choose the authoritative section"
                % (len(duplicate_groups), shown))
    else:
        rep.add("PASS", "status-headings",
                "no repeated canonical current-state headings at the same level and parent scope")

    # Stacked session records at the top (before the first `## ` heading).
    # A session record written as a heading is still a record, not the dashboard's first heading.
    first_h2 = len(vis)
    for i, l in enumerate(vis):
        m = HEADING_RE.match(l)
        if m and len(m.group(1)) == 2 and not SESSION_RECORD_RE.match(l):
            first_h2 = i
            break
    top_records = sum(1 for l in vis[:first_h2] if SESSION_RECORD_RE.match(l))
    all_records = sum(1 for l in vis if SESSION_RECORD_RE.match(l))
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

    # Last-updated date versus the newest CHANGELOG heading date and today. A
    # line that exists but carries no parseable date is a different defect
    # from no line; a date ahead of the log or the clock is a third.
    status_date = None
    updated_candidates = []
    for index, line in status_metadata_lines(lines):
        # visible_lines removes continuation indentation, but a first-line
        # list marker remains; it is a normal metadata formatting variant.
        candidate = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", line)
        candidate = re.sub(r"^ {0,3}#{1,6}\s+", "", candidate)
        candidate = re.sub(r"[*_`]+", "", candidate).strip()
        # The field may follow other metadata on the same line ("Merged to
        # main · Last updated: …"); the date is the first one after it.
        field = re.search(r"\blast(?:\s+|\s*-\s*)updated\s*:", candidate, re.IGNORECASE)
        if not field:
            continue
        tail = candidate[field.end():]
        if field.start() > 0 and not re.match(r"\s*\d{4}-\d{2}-\d{2}", tail):
            # Mid-line, only a dated field counts; "bumps the Last updated:
            # field" is prose about the field, not a second one.
            continue
        dates = [d for d in (parse_date(x) for x in re.findall(r"\d{4}-\d{2}-\d{2}", tail)) if d]
        updated_candidates.append((index + 1, line.strip(), dates[0] if dates else None))
    if len(updated_candidates) == 1:
        _, lu_line, status_date = updated_candidates[0]
    else:
        lu_line = None
    if len(updated_candidates) > 1:
        locations = ", ".join(str(item[0]) for item in updated_candidates)
        rep.add("WARN", "status-last-updated",
                "multiple visible 'Last updated' fields at lines %s — date comparison withheld; choose the current field"
                % locations)
    elif status_date is None and lu_line is None:
        rep.add("WARN", "status-last-updated",
                "no 'Last updated: YYYY-MM-DD' line found — the close ritual has nothing to bump")
    elif status_date is None:
        shown = lu_line if len(lu_line) <= 60 else lu_line[:57] + "..."
        rep.add("WARN", "status-last-updated",
                "'Last updated' line present but its date is unparseable (%s) — not YYYY-MM-DD or not a real date; fix the line rather than adding another"
                % shown)
    elif status_date > today:
        rep.add("WARN", "status-last-updated",
                "%s is %d days ahead of today (%s) — a future date; a typo or a wrong clock, fix the line"
                % (status_date, (status_date - today).days, today))
    elif changelog_newest is None:
        rep.add("INFO", "status-last-updated", "%s (no dated CHANGELOG heading to compare against)" % status_date)
    elif status_date > changelog_newest:
        rep.add("WARN", "status-last-updated",
                "%s is %d days ahead of the newest CHANGELOG entry (%s) — a future date, or STATUS was bumped without the "
                "CHANGELOG entry that must precede it"
                % (status_date, (status_date - changelog_newest).days, changelog_newest))
    else:
        lag = (changelog_newest - status_date).days
        if lag > 0:
            rep.add("WARN", "status-last-updated",
                    "%s is %d days behind the newest CHANGELOG entry (%s) — STATUS was not rewritten at the last close"
                    % (status_date, lag, changelog_newest))
        else:
            rep.add("PASS", "status-last-updated",
                    "%s, newest CHANGELOG entry %s (lag %d days)" % (status_date, changelog_newest, lag))

    # Past-tense heuristic: lines under a dated heading carrying done-words.
    dated_headings = 0
    past_lines = 0
    open_level = None          # level of the dated section we are inside, or None
    for l in vis:
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

    # Template residue: a bracketed placeholder still sitting in the dashboard
    # reads as a real item to a Brief ("[one-line question]" is askable).
    residue = [l.strip() for l in vis if STATUS_PLACEHOLDER_RE.search(l)]
    if residue:
        first = residue[0] if len(residue[0]) <= 60 else residue[0][:57] + "..."
        rep.add("WARN", "status-template-residue",
                "%d line(s) still carry a template placeholder (first: %s) — a Brief reads them as real questions or items; "
                "delete or fill them at the next Close" % (len(residue), first))
    else:
        rep.add("PASS", "status-template-residue", "0 template placeholders on visible lines")
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


def cited_ids(titles):
    """Decision ids cited in heading titles: [(prefix, number)], malformed widths dropped."""
    out = []
    for t in titles:
        for p, digits, _s in DECISION_CITE_RE.findall(t):
            if len(digits) <= ID_MAX_DIGITS:
                out.append((p, int(digits)))
    return out


def cited_ids_with_ranges(text):
    """Collect decision citations from headings and bodies, expanding only
    bounded numeric ranges such as D-0011–D-0012. Used to detect holes and
    interrupted Brief reservations instead of comparing maxima only."""
    found = []
    for m in DECISION_CITE_RE.finditer(text or ""):
        p, digits, _ = m.groups()
        if len(digits) <= ID_MAX_DIGITS:
            found.append((p, int(digits)))
    range_re = re.compile(r"((?:[A-Z][A-Z0-9]*-)*(?:D|ADR|DEC)-(?:[A-Z]+-)?)(\d+)\s*[–—-]\s*\1(\d+)")
    for m in range_re.finditer(text or ""):
        p1, d1, d2 = m.groups()
        if len(d1) <= ID_MAX_DIGITS and len(d2) <= ID_MAX_DIGITS:
            a, b = int(d1), int(d2)
            if b >= a and b - a <= 10000:
                found.extend((p1, n) for n in range(a, b + 1))
    return sorted(set(found))


def check_changelog(rep, register_dir, today):
    """Returns (newest_date, install_date, cited_ids_in_headings)."""
    text, size = read_text(os.path.join(register_dir, "CHANGELOG.md"))
    lines = split_lines(text)
    if text is None:
        rep.add("FAIL", "changelog-entries", "CHANGELOG.md unreadable")
        return None, None, None
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
            return newest, None, []
        rep.add("WARN", "changelog-entries",
                "0 entries (%d lines, %s B%s) — nothing has been logged"
                % (len(lines), "{:,}".format(size), fenced_note))
        return None, None, []

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
        reason = ("an undecodable byte (U+FFFD) sits where the separator should be — not UTF-8?"
                  if any("\ufffd" in str(x) for x in live) else "undated headings cannot be found by a bootstrap")
        rep.add("WARN", "changelog-heading-format",
                "%d of %d headings match '## YYYY-MM-DD — summary' (%.2f, pass >=%.2f) — %s%s"
                % (ok, len(live), frac, HEADING_CONFORMANCE_PASS, reason, tail))
    # Keep heading citations for compatibility, while the body census is used
    # by the exact provenance check below.
    return newest, install, cited_ids_with_ranges("\n".join(t for _, t in live) + "\n" + "\n".join(unfenced_lines(lines)))


ID_WIDTH = {}   # prefix -> widest zero-padded digit run seen in DECISIONS (so messages match the register)


def fmt_id(p, n, s=""):
    w = max(ID_WIDTH.get(p, 3), len(str(n)))
    return ("%s%0*d" % (p, w, n)) + s


def scan_decisions(register_dir):
    """Read DECISIONS.md once and census its headings. Returns a dict, or
    None when the file is unreadable."""
    text, size = read_text(os.path.join(register_dir, "DECISIONS.md"))
    if text is None:
        return None
    lines = split_lines(text)
    d = {
        "lines": lines, "size": size,
        "entries": [],        # (index, level, prefix, number, suffix) outside fences, levels 2-3
        "malformed": [],      # ids wider than ID_MAX_DIGITS, kept out of every census
        "deep_ids": [],       # ids at '####' or deeper: (prefix, number, suffix)
        "template_heads": 0,  # headings still reading D-NNNN / YYYY-MM-DD with no real id
        "fenced_heads": 0,
        "live_heads": 0,      # '##'/'###' headings outside fences that are not template lines
        "deep_heads": 0,      # non-template headings at '####' or deeper
    }
    for i, lvl, title, fenced in headings(lines):
        m = DECISION_TITLE_RE.match(title)
        if lvl not in (2, 3):
            if lvl >= 4 and not fenced:
                if m and len(m.group(2)) <= ID_MAX_DIGITS:
                    d["deep_ids"].append((m.group(1), int(m.group(2)), m.group(3) or ""))
                    d["deep_heads"] += 1
                elif not TEMPLATE_HEADING_RE.search(title):
                    d["deep_heads"] += 1
            continue
        if fenced:
            d["fenced_heads"] += 1
            continue
        # A heading with a real id is never template residue, whatever else
        # its title says ("D-002 — migrate YYYY-MM-DD parser" is D-002).
        if not m:
            if TEMPLATE_HEADING_RE.search(title):
                d["template_heads"] += 1
            else:
                d["live_heads"] += 1
            continue
        d["live_heads"] += 1
        digits = m.group(2)
        if len(digits) > ID_MAX_DIGITS:
            d["malformed"].append(m.group(1) + digits + (m.group(3) or ""))
            continue
        ID_WIDTH[m.group(1)] = max(ID_WIDTH.get(m.group(1), 0), len(digits))
        d["entries"].append((i, lvl, m.group(1), int(digits), m.group(3) or ""))
    return d


def check_decisions(rep, dec):
    if dec is None:
        rep.add("FAIL", "decisions-ids", "DECISIONS.md unreadable")
        return
    lines, size = dec["lines"], dec["size"]
    entries, malformed = dec["entries"], dec["malformed"]
    template_heads, fenced_heads = dec["template_heads"], dec["fenced_heads"]
    live_heads, deep_heads, deep_ids = dec["live_heads"], dec["deep_heads"], dec["deep_ids"]
    fmt = fmt_id

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
        # protocol forbids) versus new ids minted a level too deep. Ids at
        # '####' or deeper are a level further down and never enter the census.
        minted = []
        if ids3:
            reused = sorted({fmt(p, n) for _, _, p, n, _s in ids3 if (p, n) in seen[2]})
            minted = sorted({fmt(p, n) for _, _, p, n, _s in ids3 if (p, n) not in seen[2]})
            if reused:
                rep.add("WARN", "decisions-id-reuse",
                        "%d '##' id(s) reused with a qualifier at '###' level (%s) — the protocol wants a new numbered entry that names its target, never the old number plus 'correction'"
                        % (len(reused), listing(reused, 6)))
        if deep_ids:
            deep_list = sorted({fmt(p, n, s) for p, n, s in deep_ids})
            minted_note = "" if not minted else "; %d id(s) also minted at '###' level (%s)" % (len(minted), listing(minted, 4))
            rep.add("WARN", "decisions-id-level",
                    "%d id(s) at '####' or deeper (%s) — ids at #### or deeper are invisible to a ##-only census; promote them%s"
                    % (len(deep_list), listing(deep_list, 6), minted_note))
        elif minted:
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
        problems.append("%d heading(s) still read D-NNNN / ADR-NNN / YYYY-MM-DD / D-XXXX with no real id" % template_heads)
    if fenced_heads:
        problems.append("%d heading(s) inside code fences (fenced template example never deleted)" % fenced_heads)
    if body_placeholders:
        problems.append("%d placeholder token(s) such as '<decision in one line>' or '[POPULATE'" % body_placeholders)
    if problems:
        rep.add("WARN", "decisions-template-residue", "; ".join(problems) + " — delete them; they confuse id counts and bootstraps")
    else:
        rep.add("PASS", "decisions-template-residue", "0 template headings, 0 fenced examples, 0 placeholder tokens")


def check_changelog_decision_refs(rep, cited, dec):
    """Resolve every visible CHANGELOG decision citation, including body
    citations and supported range interiors, against actual decision IDs.
    Missing IDs can expose a Brief interrupted after reserving its IDs."""
    if cited is None or dec is None:
        rep.add("SKIP", "changelog-decision-refs", "CHANGELOG or DECISIONS unreadable")
        return
    if not cited:
        rep.add("SKIP", "changelog-decision-refs", "CHANGELOG headings and bodies cite no decision ids")
        return
    highest = {}
    exact = set()
    for _, _, p, n, _s in dec["entries"]:
        highest[p] = max(highest.get(p, 0), n)
        exact.add((p, n))
    for p, n, _s in dec["deep_ids"]:
        highest[p] = max(highest.get(p, 0), n)
        exact.add((p, n))
    problems = []
    foreign = []        # cited series this DECISIONS does not keep at all
    for p in sorted({p for p, _ in cited}):
        top = max(n for q, n in cited if q == p)
        have = highest.get(p)
        if have is None:
            # A prefixed series belongs to another register unless this
            # register explicitly declares that same series. Report it for
            # visibility, but never turn a foreign citation into a local hole.
            if p != "D-" or highest:
                foreign.append("%sNNN (highest cited %s)" % (p, fmt_id(p, top)))
            else:
                problems.append("CHANGELOG names %s but DECISIONS holds no ids at all" % fmt_id(p, top))
        elif top > have:
            problems.append("CHANGELOG names %s but DECISIONS' highest is %s" % (fmt_id(p, top), fmt_id(p, have)))
        missing = sorted(n for q, n in cited if q == p and (q, n) not in exact)
        if missing and have is not None:
            problems.append("CHANGELOG cites missing %s (exact citation, range hole, or body provenance)" % ", ".join(fmt_id(p, n) for n in missing[:8]))
    if problems:
        rep.add("WARN", "changelog-decision-refs",
                "; ".join(problems) + " — a brief died between CHANGELOG and DECISIONS; write the missing entries under those ids")
        return
    resolved = sorted(p for p in {p for p, _ in cited} if p in highest)
    parts = []
    if resolved:
        parts.append("%d id citation(s) in CHANGELOG headings and bodies resolve — highest cited %s, DECISIONS' highest %s"
                     % (sum(1 for p, _ in cited if p in highest),
                        ", ".join(fmt_id(p, max(n for q, n in cited if q == p)) for p in resolved),
                        ", ".join(fmt_id(p, highest[p]) for p in resolved)))
    if foreign:
        parts.append("%d series not kept in this DECISIONS (%s) — another register's ids, not judged"
                     % (len(foreign), ", ".join(foreign)))
    rep.add("INFO", "changelog-decision-refs", "; ".join(parts))


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


def split_table_row(line):
    """Cells of one physical table row, the way GFM splits it: `\\|` is an
    escaped pipe, every other pipe — inside a backtick code span or not —
    is a cell boundary. One optional leading and trailing pipe are eaten."""
    s = line.strip().replace("\\|", PIPE_STAND_IN)
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.replace(PIPE_STAND_IN, "|").strip() for c in s.split("|")]


def delimiter_problem(header_cells, sep_line):
    """None when `sep_line` is a GFM delimiter row for a header of
    `len(header_cells)` cells; otherwise the reason it is not.

    GFM: the delimiter row's cell count must equal the header's, or the two
    lines are not a table at all — they render as one paragraph, and every
    row under them renders as prose. Separator *shape* alone is not enough.
    """
    cells = split_table_row(sep_line)
    if len(cells) != len(header_cells):
        return ("delimiter row has %d cells, header has %d — GFM needs them equal, "
                "so this is not a table" % (len(cells), len(header_cells)))
    bad = [c for c in cells if not TABLE_DELIM_CELL_RE.match(c)]
    if bad:
        return ("%d delimiter cell(s) are not dashes with optional alignment colons "
                "(%s) — GFM needs every cell to match `:?-+:?`, so this is not a table"
                % (len(bad), ", ".join("'%s'" % c[:12] for c in bad[:4])))
    return None


def scan_ledger(text):
    """Census of LEDGER.md's visible lines. Returns a dict:
      tables      [(start_index, header_cells)] — each header+separator pair
      header      the first table's header cells, or None
      rows        [dict] well-formed data rows of the first table (ten cells),
                  keyed by LEDGER_COLUMNS, plus 'line' (1-based)
      bad_rows    [(line, cell_count)] rows of the first table with != 10 cells
      tags_line   (line, [tokens]) for the first visible 'Tags:' line, or None
      tags_lines  count of visible 'Tags:' lines
      banner      the visible non-table text, for prefix declarations
      orphans     [line] row-shaped lines outside every table — a blank
                  line split the table and GFM renders them as prose
      bad_delims  [(line, reason)] header rows whose separator row is
                  separator-shaped but not a GFM delimiter row for it
    """
    lines = split_lines(text)
    vis = [(i, l) for i, l, fenced in visible_lines(lines) if not fenced]
    d = {"tables": [], "header": None, "rows": [], "bad_rows": [],
         "tags_line": None, "tags_lines": 0, "banner": [], "orphans": [],
         "bad_delims": []}
    j = 0
    while j < len(vis):
        i, line = vis[j]
        nxt = vis[j + 1] if j + 1 < len(vis) else None
        separator_below = (TABLE_ROW_RE.match(line) and nxt is not None and nxt[0] == i + 1
                           and TABLE_SEP_RE.match(nxt[1]) and not TABLE_SEP_RE.match(line))
        is_table = False
        if separator_below:
            # Count the delimiter cells before believing the table: a
            # separator-shaped line with the wrong cell count builds no table.
            why = delimiter_problem(split_table_row(line), nxt[1])
            if why is None:
                is_table = True
            else:
                d["bad_delims"].append((i + 1, why))
        if not is_table:
            m = TAGS_LINE_RE.match(line)
            if m:
                d["tags_lines"] += 1
                if d["tags_line"] is None:
                    d["tags_line"] = (i + 1, TAG_TOKEN_RE.findall(m.group(1)))
            if d["tables"] and TABLE_ROW_RE.match(line) and not TABLE_SEP_RE.match(line):
                d["orphans"].append(i + 1)
            d["banner"].append(line)
            j += 1
            continue
        header = split_table_row(line)
        first = not d["tables"]
        d["tables"].append((i + 1, header))
        if first:
            d["header"] = header
        # The table runs over consecutive visible, non-blank lines: a wrapped
        # row's continuation is still a row (GFM), just one with too few cells.
        k = j + 2
        prev = i + 1
        while k < len(vis):
            ii, row = vis[k]
            if ii != prev + 1 or not row.strip() or HEADING_RE.match(row):
                break
            prev = ii
            k += 1
            if not first:
                continue
            cells = split_table_row(row)
            if len(cells) != len(LEDGER_COLUMNS):
                d["bad_rows"].append((ii + 1, len(cells)))
                continue
            rec = dict(zip(LEDGER_COLUMNS, cells))
            rec["line"] = ii + 1
            d["rows"].append(rec)
        j = k
    return d


TRIAGE_NOTE_RE = re.compile(r"(?:^|[;|])\s*TRIAGE\s+(\d{4}-\d{2}-\d{2})\s*:", re.IGNORECASE)


def row_touch_date(row, today=None):
    """Return (date, problem). Only Date or ``TRIAGE YYYY-MM-DD:`` in
    Evidence is a touch. Invalid, empty, and future Date cells are visible
    diagnostics; deadlines and arbitrary evidence dates do not reset age."""
    raw = row.get("Date", "").strip()
    if not raw:
        return None, "empty Date"
    m = re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw)
    if not m:
        return None, "malformed Date '%s'" % raw[:32]
    try:
        d = dt.date.fromisoformat(raw)
    except ValueError:
        return None, "invalid Date '%s'" % raw
    if today is not None and d > today:
        return None, "future Date %s" % d
    triage = []
    for m in TRIAGE_NOTE_RE.finditer(row.get("Evidence", "")):
        try:
            td = dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if today is None or td <= today:
            triage.append(td)
    return max([d] + triage), None


def ledger_id_key(prefix, digits):
    """Normalize padding without ever converting unbounded document input."""
    if not digits or len(digits) > LEDGER_ID_MAX_DIGITS or not digits.isdecimal():
        return None
    return (prefix, int(digits))


def check_ledger(rep, register_dir, dec, today):
    """Read live rows and a lightweight archive ID census beside STATUS.md.
    Absent live file: one SKIP line for the whole group."""
    path = os.path.join(register_dir, "LEDGER.md")
    text, size = read_text(path)
    if text is None:
        rep.add("SKIP", "ledger", "no LEDGER.md (optional — install it when the findings list outgrows STATUS)")
        return
    led = scan_ledger(text)
    rows, bad_rows, tables = led["rows"], led["bad_rows"], led["tables"]
    n_rows = len(rows) + len(bad_rows)
    tags_line = led["tags_line"]
    declared = tags_line[1] if tags_line else []
    declared_set = set(declared)

    def listing(items, cap):
        return ", ".join(items[:cap]) + (" ..." if len(items) > cap else "")

    def rid(row):
        return row["ID"] or ("line %d" % row["line"])

    # --- ledger-header ---------------------------------------------------
    problems = []
    header_ok = False
    for line_no, why in led["bad_delims"]:
        problems.append("the row at line %d is followed by a separator row that builds no table: %s — "
                        "copy the template's separator row" % (line_no, why))
    if not tables and not led["bad_delims"]:
        problems.append("no Items table (a header row followed by a separator row) on visible lines (%d lines, %s B) — "
                        "copy the template's header and separator rows" % (len(split_lines(text)), "{:,}".format(size)))
    if tables:
        header = led["header"]
        if header == list(LEDGER_COLUMNS):
            header_ok = True
        elif len(header) != len(LEDGER_COLUMNS):
            problems.append("header row has %d cells, the template has %d (%s) — restore the header verbatim"
                            % (len(header), len(LEDGER_COLUMNS), " | ".join(LEDGER_COLUMNS)))
        else:
            drift = ["cell %d reads '%s' where the template has '%s'" % (k + 1, got, want)
                     for k, (got, want) in enumerate(zip(header, LEDGER_COLUMNS)) if got != want]
            problems.append("%d header cell(s) drift from the template (cells trimmed, case exact): %s — restore the header verbatim"
                            % (len(drift), listing(drift, 3)))
        if bad_rows:
            shown = ["line %d: %d cells" % (ln, c) for ln, c in bad_rows]
            problems.append("%d of %d row(s) with a cell count other than %d (%s) — a wrapped row, or an unescaped pipe "
                            "(a pipe inside a cell is written \\|; backticks do not protect it); one physical line per row, "
                            "those rows are not judged below"
                            % (len(bad_rows), n_rows, len(LEDGER_COLUMNS), listing(shown, 4)))
        if len(tables) > 1:
            problems.append("%d tables in LEDGER.md, one Items table expected (second at line %d) — a side tracker inside the file; "
                            "extra data goes in Evidence, Tags or Touches" % (len(tables), tables[1][0]))
        if led["orphans"]:
            problems.append("%d row-shaped line(s) outside the table (%s) — a blank line split the table and the rows after it "
                            "render as prose and are not judged below; close the gap"
                            % (len(led["orphans"]), listing(["line %d" % ln for ln in led["orphans"]], 4)))
    if problems:
        rep.add("FAIL", "ledger-header", "; ".join(problems))
    else:
        rep.add("PASS", "ledger-header",
                "%d of %d header cells match the template, %d rows x %d cells, 1 table"
                % (len(LEDGER_COLUMNS), len(LEDGER_COLUMNS), n_rows, len(LEDGER_COLUMNS)))

    row_checks = ("ledger-status-enum", "ledger-terminal-leak", "ledger-references", "ledger-schema", "ledger-evidence", "ledger-date", "ledger-closes-when", "ledger-stale-open",
                  "ledger-ids", "ledger-archive-ids", "ledger-tags", "ledger-blocked-on", "ledger-live-size")
    if not header_ok:
        why = "no Items table" if not tables else "header drift"
        for name in row_checks:
            rep.add("SKIP", name, "%s — cells cannot be trusted; fix ledger-header first" % why)
    else:
        # --- ledger-status-enum ------------------------------------------
        bad_status = ["%s '%s'" % (rid(r), r["Status"][:24]) for r in rows if r["Status"] not in LEDGER_STATUSES]
        bad_p = ["%s '%s'" % (rid(r), r["P"][:12]) for r in rows if r["P"] not in LEDGER_PRIORITIES]
        if bad_status or bad_p:
            parts = []
            if bad_status:
                parts.append("%d Status cell(s) not one of %s (%s)" % (len(bad_status), "/".join(LEDGER_STATUSES), listing(bad_status, 4)))
            if bad_p:
                parts.append("%d P cell(s) not one of P0/P1/P2/P3 (%s)" % (len(bad_p), listing(bad_p, 4)))
            rep.add("FAIL", "ledger-status-enum",
                    "%d of %d rows off-enum — %s — move the prose to Evidence; set real tokens"
                    % (len({r["line"] for r in rows if r["Status"] not in LEDGER_STATUSES or r["P"] not in LEDGER_PRIORITIES}),
                       len(rows), "; ".join(parts)))
        else:
            rep.add("PASS", "ledger-status-enum",
                    "%d rows: %d Status cells in the six-token enum, %d P cells in P0-P3" % (len(rows), len(rows), len(rows)))

        # --- ledger-terminal-leak ----------------------------------------
        def is_tombstone(r):
            return LINE_PREFIX_RE.sub("", r["Title"]).lstrip("`").startswith(LEDGER_TOMBSTONE)
        terminal = [r for r in rows if r["Status"] in LEDGER_TERMINAL]
        tombstones = [r for r in terminal if r["Status"] == "NOT-AN-ISSUE" and is_tombstone(r)]
        leaked = [r for r in terminal if r not in tombstones]
        tomb_note = "; %d %s tombstone(s) excepted" % (len(tombstones), LEDGER_TOMBSTONE) if tombstones else ""
        if leaked:
            rep.add("FAIL", "ledger-terminal-leak",
                    "%d of %d rows CLOSED/SUPERSEDED/NOT-AN-ISSUE still in the live file (%s%s) — move them verbatim to "
                    "LEDGER-ARCHIVE.md in the same edit that changes their state"
                    % (len(leaked), len(rows), listing(["%s %s" % (rid(r), r["Status"]) for r in leaked], 4), tomb_note))
        else:
            rep.add("PASS", "ledger-terminal-leak",
                    "0 of %d rows CLOSED/SUPERSEDED/NOT-AN-ISSUE in the live file%s" % (len(rows), tomb_note))

        # Live rows for the lifecycle checks: everything the terminal-leak
        # check does not own (tombstones are sanctioned, leaks are already a FAIL).
        live = [r for r in rows if r["Status"] not in LEDGER_TERMINAL]

        # References are untrusted input too. Normalize once and exclude a
        # malformed reference from successor/blocker decisions, while still
        # reporting it even when it appears in a prose-only cell.
        references = {}
        malformed_refs = []
        for r in rows:
            for column in LEDGER_COLUMNS[1:]:
                keys = []
                for match in LEDGER_ID_CITE_RE.finditer(r[column]):
                    key = ledger_id_key(*match.groups())
                    if key is None:
                        malformed_refs.append("line %d %s: '%s…' (%d digits)" %
                                              (r["line"], column, match.group(0)[:24], len(match.group(2))))
                    else:
                        keys.append(key)
                references[r["line"], column] = keys
        if malformed_refs:
            rep.add("FAIL", "ledger-references", "%d oversized LG reference(s), limit %d digits (%s) — repair the cited ID; later checks continue" %
                    (len(malformed_refs), LEDGER_ID_MAX_DIGITS, listing(malformed_refs, 4)))
        else:
            rep.add("PASS", "ledger-references", "all LG references use at most %d digits" % LEDGER_ID_MAX_DIGITS)

        # Structural invariants are checked independently from semantic
        # evidence checks so a row cannot hide a bad state behind a plausible
        # sentence in Evidence.
        bad_blocked = [r for r in rows if r["Status"] == "BLOCKED" and not r["Blocked-on"].strip()]
        nonblocked_gates = [r for r in rows if r["Status"] != "BLOCKED" and r["Blocked-on"].strip()]
        superseded_missing = []
        closed_bad_evidence = []
        for r in rows:
            if r["Status"] == "SUPERSEDED":
                ids = references[r["line"], "Evidence"]
                self_id = LEDGER_ID_RE.match(r["ID"])
                self_key = ledger_id_key(*self_id.groups()) if self_id else None
                if not any(k != self_key for k in ids):
                    superseded_missing.append(r)
            if r["Status"] == "CLOSED":
                ev = r["Evidence"]
                has_pointer = bool(re.search(r"(?:[0-9a-f]{7,40}\b|(?:^|\s)(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+)", ev, re.I))
                has_check = bool(re.search(r"(?:check|test|command)\s*[:=]?\s*\S+", ev, re.I))
                has_commit = bool(re.search(r"\bcommitted\b|\bcommit\s+[0-9a-f]{7,40}\b|\b(?:sha256|sha-256|content\s+hash)\b", ev, re.I))
                if not (has_pointer and has_check and has_commit):
                    closed_bad_evidence.append(r)
        schema_parts = []
        if bad_blocked:
            schema_parts.append("%d BLOCKED row(s) have no gate" % len(bad_blocked))
        if nonblocked_gates:
            schema_parts.append("%d non-BLOCKED row(s) have Blocked-on text" % len(nonblocked_gates))
        if superseded_missing:
            schema_parts.append("%d SUPERSEDED row(s) lack a successor LG id" % len(superseded_missing))
        if schema_parts:
            rep.add("FAIL", "ledger-schema", "; ".join(schema_parts) + " — enforce the LEDGER state invariants")
        else:
            rep.add("PASS", "ledger-schema", "all %d rows satisfy Blocked-on and SUPERSEDED successor invariants" % len(rows))
        if closed_bad_evidence:
            rep.add("FAIL", "ledger-evidence", "%d CLOSED row(s) lack a repo pointer, check reading, or committed-work marker (%s)" % (len(closed_bad_evidence), listing([rid(r) for r in closed_bad_evidence], 4)))
        else:
            rep.add("PASS", "ledger-evidence", "all CLOSED rows satisfy the structural evidence contract")

        date_problems = []
        for r in live:
            _touch, problem = row_touch_date(r, today)
            if problem:
                date_problems.append("%s: %s" % (rid(r), problem))
        if date_problems:
            rep.add("WARN", "ledger-date", "%d live row(s) have invalid, empty, or future Date cells (%s) — staleness is unjudgeable" % (len(date_problems), listing(date_problems, 4)))
        else:
            rep.add("PASS", "ledger-date", "%d live rows have valid non-future Date cells" % len(live))

        # --- ledger-closes-when ------------------------------------------
        empty_cw = [r for r in live if not r["Closes-when"]]
        dispo_cw = [r for r in live if r["Closes-when"] and DISPOSITION_RE.match(r["Closes-when"])]
        if empty_cw or dispo_cw:
            parts = []
            if empty_cw:
                parts.append("%d empty (%s)" % (len(empty_cw), listing([rid(r) for r in empty_cw], 4)))
            if dispo_cw:
                parts.append("%d opening with a disposition word (%s)"
                             % (len(dispo_cw), listing(["%s '%s'" % (rid(r), r["Closes-when"][:20]) for r in dispo_cw], 3)))
            rep.add("WARN", "ledger-closes-when",
                    "%d of %d live rows with a Closes-when that is no yes/no condition (warn >0) — %s — rewrite as a condition "
                    "that either holds or doesn't, at triage if not now"
                    % (len(empty_cw) + len(dispo_cw), len(live), "; ".join(parts)))
        else:
            rep.add("PASS", "ledger-closes-when",
                    "0 of %d live rows with an empty or disposition-word Closes-when (warn >0)" % len(live))

        # --- ledger-stale-open -------------------------------------------
        judged = [r for r in live if r["Status"] in ("OPEN", "VERIFYING")]
        ages = []          # (days, row)
        undated = []
        for r in judged:
            touch, problem = row_touch_date(r, today)
            if touch is None:
                undated.append((r, problem))
                continue
            ages.append(((today - touch).days, r))
        over60 = [(a, r) for a, r in ages if a > LEDGER_STALE_DAYS]
        p01_over = [(a, r) for a, r in ages if a > LEDGER_STALE_P01_DAYS and r["P"] in ("P0", "P1")]
        majority = len(over60) * 2 > len(live) and over60
        undated_note = "" if not undated else "; %d OPEN/VERIFYING row(s) unjudgeable (%s)" % (len(undated), listing(["%s: %s" % (rid(r), p) for r, p in undated], 3))
        bar = "warn: a P0/P1 row over %d days, or over half of %d non-terminal live rows over %d" % (LEDGER_STALE_P01_DAYS, len(live), LEDGER_STALE_DAYS)
        if p01_over or majority:
            parts = []
            if p01_over:
                parts.append("%d P0/P1 row(s) untouched over %d days (%s)"
                             % (len(p01_over), LEDGER_STALE_P01_DAYS,
                                listing(["%s %s, %d days" % (rid(r), r["P"], a) for a, r in sorted(p01_over, key=lambda x: -x[0])], 3)))
            if majority:
                parts.append("a majority of the %d non-terminal live rows — triage has stopped" % len(live))
            rep.add("WARN", "ledger-stale-open",
                    "%d of %d OPEN/VERIFYING rows untouched over %d days; %s — a triage prompt, never a close: run a triage "
                    "pass before adding rows; a dated triage note in Evidence resets the clock (%s)%s"
                    % (len(over60), len(judged), LEDGER_STALE_DAYS, "; ".join(parts), bar, undated_note))
        elif over60:
            oldest = max(over60, key=lambda x: x[0])
            rep.add("INFO", "ledger-stale-open",
                    "%d of %d OPEN/VERIFYING rows untouched over %d days (oldest %s, %d days; %s) — a triage prompt, never a close; "
                    "a dated triage note in Evidence resets the clock%s"
                    % (len(over60), len(judged), LEDGER_STALE_DAYS, rid(oldest[1]), oldest[0], bar, undated_note))
        elif undated:
            rep.add("WARN", "ledger-stale-open",
                    "%d of %d OPEN/VERIFYING rows have an unjudgeable touch date%s — fix Date or add an exact TRIAGE YYYY-MM-DD: note; staleness remains advisory" % (len(undated), len(judged), undated_note))
        else:
            rep.add("PASS", "ledger-stale-open",
                    "0 of %d OPEN/VERIFYING rows untouched over %d days (%s)%s" % (len(judged), LEDGER_STALE_DAYS, bar, undated_note))

        # --- ledger-ids --------------------------------------------------
        banner_text = "\n".join(led["banner"])
        malformed = []
        undeclared_prefix = []
        seen = {}                          # (prefix, number) -> [id strings]
        highest = {}                       # prefix -> (number, id string)
        for r in rows:
            m = LEDGER_ID_RE.match(r["ID"])
            if not m:
                malformed.append("line %d '%s'" % (r["line"], r["ID"][:20]))
                continue
            key = ledger_id_key(*m.groups())
            if key is None:
                malformed.append("line %d '%s…'" % (r["line"], r["ID"][:20]))
                continue
            seen.setdefault(key, []).append(r["ID"])
            if key[1] >= highest.get(m.group(1), (-1, ""))[0]:
                highest[m.group(1)] = (key[1], r["ID"])
            if m.group(1) and (m.group(1) + "LG-") not in banner_text:
                undeclared_prefix.append(m.group(1) + "LG-")
        dups = sorted(ids[0] for key, ids in seen.items() if len(ids) > 1)
        undeclared_prefix = sorted(set(undeclared_prefix))
        highest_text = "highest %s" % listing([v[1] for _, v in sorted(highest.items())], 4) if highest else "no ids"
        if dups or malformed:
            parts = []
            if dups:
                parts.append("%d id(s) used more than once (%s) — two rows at one address; mint the next number, never renumber"
                             % (len(dups), listing(dups, 6)))
            if malformed:
                parts.append("%d ID cell(s) not LG-NNNN or PREFIX-LG-NNNN (%s) — a row without an address cannot be cited"
                             % (len(malformed), listing(malformed, 4)))
            rep.add("FAIL", "ledger-ids", "%d rows, %d distinct ids, %s; %s" % (len(rows), len(seen), highest_text, "; ".join(parts)))
        elif undeclared_prefix:
            rep.add("WARN", "ledger-ids",
                    "%d rows, %d distinct ids, %s, 0 duplicates; %d prefix series not declared in the banner (%s) — "
                    "a family prefix is allowed only when the banner names it"
                    % (len(rows), len(seen), highest_text, len(undeclared_prefix), listing(undeclared_prefix, 4)))
        else:
            series_note = "" if len(highest) <= 1 else " across %d id series" % len(highest)
            rep.add("INFO", "ledger-ids", "%d rows, %d distinct ids, %s, 0 duplicates%s" % (len(rows), len(seen), highest_text, series_note))

        # Archive ids remain reserved forever. The Doctor does not validate
        # archive row semantics, but it does catch a live/archive collision so
        # a replayed allocator cannot resurrect an old address.
        archive_path = os.path.join(register_dir, "LEDGER-ARCHIVE.md")
        archive_text, _ = read_text(archive_path)
        archive_ids = set()
        archive_bad = []
        if archive_text is not None:
            for index, line, fenced in visible_lines(split_lines(archive_text)):
                if fenced or not TABLE_ROW_RE.match(line) or TABLE_SEP_RE.match(line):
                    continue
                cells = split_table_row(line)
                if cells == list(LEDGER_COLUMNS):
                    continue
                match = LEDGER_ID_RE.fullmatch(cells[0]) if cells else None
                key = ledger_id_key(*match.groups()) if match else None
                if key is None:
                    archive_bad.append("line %d: '%s'" % (index + 1, cells[0][:24] if cells else ""))
                else:
                    # A reopened item may have multiple historical closures;
                    # repeated IDs in the archive are not themselves errors.
                    archive_ids.add(key)
        collisions = sorted(seen[key][0] for key in set(seen) & archive_ids)
        archive_problems = []
        if collisions:
            archive_problems.append("%d live id(s) also exist in LEDGER-ARCHIVE.md (%s) — numeric aliases share an address; archive ids remain reserved (verify reopen events manually)" % (len(collisions), listing(collisions, 6)))
        if archive_bad:
            archive_problems.append("%d malformed or oversized archive ID cell(s) (%s) — repair ID syntax before trusting the archive census" % (len(archive_bad), listing(archive_bad, 4)))
        if archive_problems:
            rep.add("FAIL", "ledger-archive-ids", "; ".join(archive_problems))
        elif archive_text is not None:
            rep.add("PASS", "ledger-archive-ids", "%d archived ids checked, 0 live/archive collisions" % len(archive_ids))
        else:
            rep.add("SKIP", "ledger-archive-ids", "no LEDGER-ARCHIVE.md to check")

        # --- ledger-tags -------------------------------------------------
        undeclared_cells = []
        for r in rows:
            for piece in r["Tags"].replace(",", " ").split():
                if piece not in declared_set:
                    undeclared_cells.append("%s '%s'" % (rid(r), piece[:20]))
        stray = []
        for r in rows:
            for col in LEDGER_COLUMNS:
                if col == "Tags":
                    continue
                for tok in TAG_TOKEN_RE.findall(r[col]):
                    stray.append("%s %s in %s" % (rid(r), tok, col))
        tags_note = ("%d tokens declared on the Tags: line (warn >%d)" % (len(declared), LEDGER_TAGS_MAX) if tags_line
                     else "no Tags: line in the banner (0 tokens declared, warn >%d)" % LEDGER_TAGS_MAX)
        if led["tags_lines"] > 1:
            tags_note += ", %d Tags: lines — the first is read" % led["tags_lines"]
        if undeclared_cells:
            rep.add("FAIL", "ledger-tags",
                    "%d Tags cell token(s) not declared on the Tags: line (%s); %s — declare the token or delete it"
                    % (len(undeclared_cells), listing(undeclared_cells, 4), tags_note))
        elif len(declared) > LEDGER_TAGS_MAX or stray:
            parts = []
            if len(declared) > LEDGER_TAGS_MAX:
                parts.append("%s — Tags is one axis; an over-full line is a second axis in disguise" % tags_note)
            if stray:
                parts.append("%d +token(s) outside the Tags cell (%s) — tags live in the Tags cell" % (len(stray), listing(stray, 4)))
            if len(declared) <= LEDGER_TAGS_MAX:
                parts.append(tags_note)
            rep.add("WARN", "ledger-tags", "; ".join(parts))
        else:
            rep.add("PASS", "ledger-tags",
                    "%s, 0 undeclared Tags cell tokens, 0 +tokens outside the Tags cell" % tags_note)

        # --- ledger-blocked-on -------------------------------------------
        live_keys = set(seen)
        blocked = [r for r in rows if r["Status"] == "BLOCKED"]
        empty_bo = [r for r in blocked if not r["Blocked-on"]]
        parked = []
        for r in blocked:
            cited = references[r["line"], "Blocked-on"]
            if cited and not any(c in live_keys for c in cited):
                parked.append("%s on %s" % (rid(r), r["Blocked-on"][:30]))
        invalid_gate = [r for r in blocked if r["Blocked-on"].strip() and not (
            re.search(r"\bowner\b", r["Blocked-on"], re.I) or references[r["line"], "Blocked-on"] or
            re.search(r"\b(?:external|vendor|dependency|gate|ticket|issue|approval)\b", r["Blocked-on"], re.I))]
        if empty_bo or nonblocked_gates or invalid_gate:
            parts = []
            if empty_bo:
                parts.append("%d empty" % len(empty_bo))
            if nonblocked_gates:
                parts.append("%d non-BLOCKED rows not blank" % len(nonblocked_gates))
            if invalid_gate:
                parts.append("%d BLOCKED rows with no recognised gate" % len(invalid_gate))
            rep.add("FAIL", "ledger-blocked-on",
                    "%s — BLOCKED rows name owner, a live LG id, or an external gate; every other state is blank" % "; ".join(parts))
        elif parked:
            rep.add("WARN", "ledger-blocked-on",
                    "%d of %d BLOCKED rows cite only ids absent from the live file (%s) — the blockers closed and the row is parked "
                    "where ledger-stale-open cannot see it; re-open it or name the gate that remains"
                    % (len(parked), len(blocked), listing(parked, 3)))
        else:
            rep.add("PASS", "ledger-blocked-on",
                    "%d BLOCKED rows, 0 with an empty Blocked-on, 0 gated only on ids absent from the live file" % len(blocked))

        # --- ledger-live-size --------------------------------------------
        size_text = "%d live rows (warn >%d, fail >%d)" % (n_rows, LEDGER_LIVE_WARN, LEDGER_LIVE_FAIL)
        if n_rows > LEDGER_LIVE_FAIL:
            rep.add("FAIL", "ledger-live-size",
                    size_text + " — a live file nobody can read whole stops being read; a backlog-bankruptcy tranche: rule, close or park "
                    "items until the open set is readable again")
        elif n_rows > LEDGER_LIVE_WARN:
            rep.add("WARN", "ledger-live-size", size_text + " — over the bar the remedy is a triage pass")
        else:
            rep.add("PASS", "ledger-live-size", size_text)

    # --- decisions-tags ------------------------------------------------------
    if dec is None:
        rep.add("SKIP", "decisions-tags", "DECISIONS.md unreadable")
        return
    tagged = 0
    undeclared = []
    for _, lvl, title, fenced in headings(dec["lines"]):
        if fenced or lvl not in (2, 3):
            continue
        m = TAG_TITLE_TAIL_RE.search(title)
        if not m:
            continue
        tagged += 1
        for tok in TAG_TOKEN_RE.findall(m.group(1)):
            if tok not in declared_set:
                head = title if len(title) <= 40 else title[:37] + "..."
                undeclared.append("%s on '%s'" % (tok, head))
    if undeclared:
        where = "the ledger's Tags: line" if tags_line else "a Tags: line the ledger does not have"
        rep.add("FAIL", "decisions-tags",
                "%d +tag(s) ending a DECISIONS title not declared on %s, %d tagged heading(s): %s — a decision tagged with a token "
                "the ledger does not know is grouped with nothing; declare it in the ledger or append a correction; preserve the historical title"
                % (len(undeclared), where, tagged, listing(undeclared, 4)))
    else:
        rep.add("PASS", "decisions-tags",
                "%d DECISIONS heading(s) end in +tags, 0 undeclared (%d tokens declared)" % (tagged, len(declared)))


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

def run(root, today, no_git, register=None):
    rep = Report()
    root = os.path.realpath(root)
    if not os.path.isdir(root):
        print("docs-doctor: not a directory: %s" % root, file=sys.stderr)
        return 3
    try:
        register_dir = find_register(root, register)
    except ValueError as exc:
        print("docs-doctor: %s" % exc, file=sys.stderr)
        return 3
    note = ""
    # The docs directory itself was passed: the instructions files live one up.
    if (register_dir == root and os.path.basename(root) == "docs"
            and not any(os.path.isfile(os.path.join(root, f)) for f in INSTRUCTION_FILES)):
        root = os.path.dirname(root)
        note = " — a docs/ directory was given; treating its parent as the project root"
    print("docs-doctor %s — register at %s (relative to the project root), today %s%s"
          % (VERSION, rel_label(register_dir, root), today, note))
    print()
    dec = scan_decisions(register_dir)
    check_wiring(rep, root, rel_label(register_dir, root))
    check_readme_footer(rep, register_dir)
    newest, install, cited = check_changelog(rep, register_dir, today)
    check_changelog_decision_refs(rep, cited, dec)
    check_status(rep, register_dir, newest, today)
    check_decisions(rep, dec)
    check_brand(rep, register_dir, install)
    check_ancestor_register(rep, root)
    check_sibling_register(rep, root, register_dir)
    check_ledger(rep, register_dir, dec, today)
    check_git(rep, root, register_dir, no_git)
    print()
    c = rep.counts
    code = rep.exit_code()
    print("%d checks: %d pass, %d warn, %d fail, %d info, %d skipped — exit %d"
          % (sum(c.values()), c["PASS"], c["WARN"], c["FAIL"], c["INFO"], c["SKIP"], code))
    print("Scope: " + STRUCTURAL_LIMITS)
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
        description="Read-only health check for a project-docs-protocol installation. "
                    "Exit 0 all pass; 1 WARN only; 2 any FAIL; 3 could not run.",
        epilog=STRUCTURAL_LIMITS,
    )
    ap.add_argument("root", help="project root (the directory holding CLAUDE.md/AGENTS.md; the register may be there or under docs/)")
    ap.add_argument("--register-dir", help="explicit register directory, relative to project root or absolute")
    ap.add_argument("--today", help="date to measure dormancy from (YYYY-MM-DD); default: today", default=None)
    ap.add_argument("--no-git", action="store_true", help="skip git-based checks even when git is available")
    ap.add_argument("--version", action="version", version="docs-doctor %s" % VERSION)
    args = ap.parse_args(argv)
    today = parse_date(args.today) if args.today else dt.date.today()
    if args.today and today is None:
        print("docs-doctor: --today must be YYYY-MM-DD", file=sys.stderr)
        return 3
    try:
        return run(args.root, today, args.no_git, args.register_dir)
    except Exception as exc:  # noqa: BLE001 — a crash is exit 3, never a silent pass
        print("docs-doctor: checker error: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
