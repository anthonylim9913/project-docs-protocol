#!/usr/bin/env python3
"""Run the same executable suite as `python3 -m unittest discover -v`."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def main():
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / 'tests'), pattern='test_*.py', top_level_dir=str(ROOT)
    )
    if suite.countTestCases() == 0:
        print('No executable regression tests discovered', file=sys.stderr)
        return 1
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
