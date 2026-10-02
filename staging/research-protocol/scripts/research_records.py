"""Bounded record declarations shared by Doctor and exact-ID retrieval.

Only column-zero first-level headings declare records. This is deliberately
not a Markdown visibility engine; quoted/fenced excerpts must avoid this shape.
"""
import re

ID_RE = re.compile(r'^(SRC|NOTE|RQ|SYN)-[0-9]{4}$')


def heading_tokens(body):
    # Whitespace, a colon or an em dash starts an optional title. Punctuation
    # and Unicode suffixes otherwise remain part of the full identity token.
    return re.findall(r'(?m)^#[ \t]+([^\s—:]+)', body)


def record_id(body):
    declarations = [token for token in heading_tokens(body) if ID_RE.fullmatch(token)]
    seen = set()
    for ident in declarations:
        if ident in seen:
            raise ValueError('duplicate id ' + ident)
        seen.add(ident)
    if len(declarations) > 1:
        raise ValueError('multiple record declarations in one file')
    return declarations[0] if declarations else None
