#!/usr/bin/env python3
"""Read-only release gate, Python 3.9+, standard library only.

Count grammar (case insensitive, Markdown emphasis ignored): ``N core``,
``core N``, ``core suite: N tests`` and corresponding research/Architect forms;
``N overall``, ``N total``, ``total N`` and ``N automated test methods`` denote
all three suites together. Counts are decimal integers, optionally comma-grouped.
Only README.md, docs/STATUS.md and the newest ## entry in docs/CHANGELOG.md
are current claims. Other numeric test/method claims are 'not checked'; subset
counts such as registry methods are never equated with an entire suite.
This is a bounded prose parser, not a semantic audit of arbitrary release notes.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

SUITES = (
    ('core', '.', ['-m', 'unittest', 'discover', '-q']),
    ('research', 'staging/research-protocol', ['-m', 'unittest', 'discover', '-s', 'tests', '-q']),
    ('Architect', 'staging/architect-protocol', ['-m', 'unittest', 'discover', '-s', 'tests', '-q']),
)
NUMBER = r'\d+(?:,\d{3})*'
LABEL = r'core|research|Architect|overall|total'
CLAIM = re.compile(
    r'\b(?:(?P<before>' + NUMBER + r')\s+(?P<suffix>' + LABEL + r')\b|'
    r'(?P<prefix>' + LABEL + r')\b(?:\s+suite)?\s*[:=]?\s*(?P<after>' + NUMBER + r')\b|'
    r'(?P<total>' + NUMBER + r')\s+automated test methods\b)', re.I)
TEST_WORD = re.compile(r'\b(?:tests?|methods?)\b', re.I)
COUNT_NUMBER = re.compile(r'\b' + NUMBER + r'\b')
RAN = re.compile(r'^Ran (\d+) tests? in .+$', re.M)


def run(command, cwd):
    try:
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, errors='replace',
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        return result.returncode, result.stdout
    except OSError:
        return None, 'could not start command'


def count_claims(root, measured):
    """Return gate success, emitting locations without guessing unknown counts."""
    passed = True
    for name in ('README.md', 'docs/CHANGELOG.md', 'docs/STATUS.md'):
        try:
            lines = (root / name).read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeError):
            print('FAIL counts {}: could not read'.format(name))
            passed = False
            continue
        in_entry = False
        checked = 0
        for lineno, line in enumerate(lines, 1):
            if name == 'docs/CHANGELOG.md' and line.startswith('## '):
                if in_entry:
                    break
                in_entry = True
            if name == 'docs/CHANGELOG.md' and not in_entry:
                continue
            plain = line.replace('*', '').replace('_', '').replace('`', '')
            spans = []
            for match in CLAIM.finditer(plain):
                spans.append(match.span())
                label = (match['suffix'] or match['prefix'] or 'total').lower()
                if label in ('overall', 'total'):
                    label = 'total'
                value = int((match['before'] or match['after'] or match['total']).replace(',', ''))
                where = '{}:{}'.format(name, lineno)
                if label not in measured:
                    print('INFO counts {}: {} not checked (no measurement)'.format(where, label))
                elif value != measured[label]:
                    print('FAIL counts {}: {} stated {}; measured {}'.format(where, label, value, measured[label]))
                    passed = False
                else:
                    checked += 1
            # Any remaining number on a test-count line needs a notice. This
            # deliberately favors an extra notice over silently losing prose
            # outside the bounded attribution grammar (including reversed or
            # arbitrarily long labels and mixed attributed/subset counts).
            remainder = list(plain)
            for start, end in spans:
                remainder[start:end] = ' ' * (end - start)
            if TEST_WORD.search(plain) and COUNT_NUMBER.search(''.join(remainder)):
                print('INFO counts {}:{}: not checked (unattributed test count)'.format(name, lineno))
        print('{} counts {}: {} claims checked{}'.format(
            'PASS' if passed else 'INFO', name, checked,
            '' if measured else '; suites not checked'))
    return passed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--python', action='append', metavar='PATH', help='suite interpreter (repeatable; default: running interpreter)')
    parser.add_argument('--allow-doctor-warn', action='store_true', help='accept Doctor exit 1 (WARN only)')
    parser.add_argument('--skip-suites', action='store_true', help='script testing only; result is not a release check')
    parser.add_argument('--base', metavar='REF', help='committed whitespace base (default: newest reachable tag)')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    passed = True
    measurements = []
    if args.skip_suites:
        print('SKIP suites: not a release check')
    else:
        for index, interpreter in enumerate(args.python or [sys.executable], 1):
            measured = {}
            for label, directory, command in SUITES:
                code, output = run([interpreter, '-B', *command], root / directory)
                summaries = RAN.findall(output)
                count = int(summaries[0]) if len(summaries) == 1 else None
                ok = code == 0 and count is not None and count > 0
                print('{} {} [interpreter {}]: {} tests; exit {}'.format(
                    'PASS' if ok else 'FAIL', label, index,
                    count if count is not None else 'unknown', code))
                if not ok:
                    passed = False
                    # Child diagnostics are useful for suite failures. Interpreter
                    # paths are not printed by this gate itself.
                    print(output.rstrip())
                if ok:
                    measured[label.lower()] = count
            if len(measured) == len(SUITES):
                measured['total'] = sum(measured.values())
            measurements.append(measured)
    checks = [
            ('Doctor', [sys.executable, '-B', 'scripts/docs-doctor.py', '.']),
            ('skill-registry', [sys.executable, '-B', 'scripts/skill-registry.py', '.']),
            ('git diff --check', ['git', 'diff', '--check']),
            ('git diff --check --cached', ['git', 'diff', '--check', '--cached'])]
    base = args.base
    if base is None:
        code, output = run(['git', 'describe', '--tags', '--abbrev=0', 'HEAD'], root)
        if code == 0:
            base = output.strip()
        else:
            print('INFO committed range not checked (no reachable tag)')
    if base is not None:
        checks.append(('committed whitespace', ['git', 'diff', '--check', base, 'HEAD', '--']))
    for label, command in checks:
        code, output = run(command, root)
        warn = label == 'Doctor' and code == 1
        ok = code == 0 or (warn and args.allow_doctor_warn)
        print('{} {}: exit {}{}'.format('WARN' if warn else 'PASS' if ok else 'FAIL', label, code,
                                       ' (allowed)' if warn and ok else ''))
        if not ok:
            passed = False
            print(output.rstrip())
    for measured in measurements or [{}]:
        if not count_claims(root, measured):
            passed = False
    if args.skip_suites:
        print('INCOMPLETE release-check (suites skipped)')
        return 3
    print('{} release-check'.format('PASS' if passed else 'FAIL'))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
