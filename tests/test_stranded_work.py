"""Advisory stranded-work checks against independent disposable repositories."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.test_doctor import ROOT, load_doctor, seed_register


class StrandedWorkTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="stranded-work-")).resolve()
        self.addCleanup(shutil.rmtree, self.project)
        seed_register(self.project)
        self.doctor = load_doctor()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                        GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")

    def git(self, *args):
        done = subprocess.run(["git", "-C", str(self.project)] + list(args),
                              capture_output=True, text=True, env=self.env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip()

    def init(self):
        if not shutil.which("git"):
            self.skipTest("git unavailable")
        self.git("init", "-b", "trunk")
        self.commit("install")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)

    def branch_report(self):
        report = self.doctor.Report(echo=False)
        self.doctor.check_unlisted_branches(report, str(self.project),
                                           str(self.project / "docs"), str(self.project))
        self.assertEqual(len(report.lines), 1)
        self.assertIn(report.lines[0][0], ("INFO", "WARN", "SKIP"))
        return report.lines[0]

    def test_many_local_branches_have_exact_counts_in_two_git_calls(self):
        self.init()
        self.git("checkout", "-b", "lane-000")
        (self.project / "code.txt").write_text("one")
        self.commit("work")
        with (self.project / "docs/STATUS.md").open("a") as out:
            out.write("\nregister edit\n")
        self.commit("register only")
        (self.project / "code.txt").write_text("two")
        with (self.project / "docs/CHANGELOG.md").open("a") as out:
            out.write("\nmixed\n")
        self.commit("mixed work")
        self.git("commit", "--allow-empty", "-m", "empty")
        tip = self.git("rev-parse", "HEAD")
        for number in range(1, 120):
            self.git("branch", "lane-%03d" % number, tip)
        self.git("checkout", "trunk")
        calls = []
        original = self.doctor.run_git

        def bounded(root, args):
            calls.append(args)
            self.assertLessEqual(len(calls), 2, "Git calls must not scale with branches")
            return original(root, args)

        with patch.object(self.doctor, "run_git", side_effect=bounded):
            level, _, message = self.branch_report()
        self.assertEqual(level, "WARN")
        self.assertIn("120 unlisted", message)
        self.assertIn("lane-000 (2 commits)", message)
        self.assertIn("lane-004 (2 commits)", message)
        self.assertNotIn("lane-005", message)
        self.assertEqual(len(calls), 2)

    def test_listed_worktree_branch_is_info_and_remote_only_refs_are_ignored(self):
        self.init()
        self.git("checkout", "-b", "lane-listed")
        (self.project / "work.txt").write_text("work")
        self.commit("work")
        self.git("update-ref", "refs/remotes/origin/remote-only", "HEAD")
        self.git("checkout", "trunk")
        worktree = self.project.parent / (self.project.name + "-lane")
        self.git("worktree", "add", str(worktree), "lane-listed")
        self.addCleanup(lambda: shutil.rmtree(worktree) if worktree.exists() else None)
        self.assertEqual(self.branch_report()[0], "WARN")
        with (self.project / "docs/STATUS.md").open("a") as out:
            out.write("\n| Lane | `lane-listed` | owner reviews |\n")
        level, _, message = self.branch_report()
        self.assertEqual(level, "INFO")
        self.assertIn("lane-listed (1 commits)", message)
        self.assertNotIn("remote-only", message)
        self.git("worktree", "remove", str(worktree))
        self.git("branch", "-D", "lane-listed")
        self.assertIn("0 local branches", self.branch_report()[2])

    def test_merged_and_register_only_ignored_but_squash_equivalent_warns(self):
        self.init()
        self.git("checkout", "-b", "register-only")
        with (self.project / "docs/DECISIONS.md").open("a") as out:
            out.write("\nregister\n")
        self.commit("register")
        self.git("checkout", "trunk")
        self.assertEqual(self.branch_report()[0], "INFO")
        self.git("checkout", "-b", "merged")
        (self.project / "code.txt").write_text("work")
        self.commit("work")
        self.git("checkout", "trunk")
        self.git("merge", "--no-ff", "merged", "-m", "merge")
        self.assertEqual(self.branch_report()[0], "INFO")
        self.git("checkout", "-b", "squashed")
        (self.project / "code.txt").write_text("squash work")
        self.commit("squash work")
        self.git("checkout", "trunk")
        self.git("merge", "--squash", "squashed")
        self.commit("squash")
        level, _, message = self.branch_report()
        self.assertEqual(level, "WARN")
        self.assertIn("squashed (1 commits)", message)
        self.assertNotIn("merged (", message)

    def test_longer_branch_name_does_not_list_a_shorter_one(self):
        self.init()
        for name in ("lane-one", "lane-one+more", "lane-one@x", "lane-one=y"):
            self.git("checkout", "-b", name, "trunk")
            (self.project / "code.txt").write_text(name)
            self.commit("work on " + name)
        self.git("checkout", "trunk")
        with (self.project / "docs/STATUS.md").open("a") as out:
            out.write("\nIn flight: `lane-one+more`, (lane-one@x), and lane-one=y.\n")
        self.commit("list three of four")
        level, _, message = self.branch_report()
        self.assertEqual(level, "WARN", message)
        self.assertIn("1 unlisted", message)
        self.assertIn("lane-one (1 commits)", message)
        self.assertIn("3 listed", message)

    def test_user_git_configuration_cannot_hide_changed_paths(self):
        self.init()
        nested = self.project / "nested"
        nested.mkdir()
        (nested / "keep.txt").write_text("x")
        self.commit("nested folder")
        self.git("checkout", "-b", "lane-outside")
        (self.project / "outside.txt").write_text("work outside the nested folder")
        self.commit("outside work")
        self.git("checkout", "-b", "lane-gitlink", "trunk")
        self.git("update-index", "--add", "--cacheinfo", "160000," + self.git("rev-parse", "HEAD") + ",component")
        self.git("commit", "-m", "add a gitlink")
        self.git("checkout", "-f", "trunk")
        self.git("config", "diff.relative", "true")
        self.git("config", "diff.ignoreSubmodules", "all")
        report = self.doctor.Report(echo=False)
        with patch.dict(os.environ, self.env):
            self.doctor.check_unlisted_branches(report, str(nested), str(self.project / "docs"), str(self.project))
        level, _, message = report.lines[0]
        self.assertEqual(level, "WARN", message)
        self.assertIn("2 unlisted", message)

    def test_capability_and_read_errors_are_skip_never_fail(self):
        for no_git, installed, top in ((True, True, "repo"), (False, False, "repo"), (False, True, None)):
            report = self.doctor.Report(echo=False)
            with patch.object(self.doctor.shutil, "which", return_value="git" if installed else None), patch.object(self.doctor, "run_git", return_value=top):
                self.doctor.check_git(report, str(self.project), str(self.project / "docs"), no_git)
            result = [line for line in report.lines if line[1] == "git-unlisted-branches"]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "SKIP")
        for answers in ((None,), ("refs/heads/lane " + "a" * 40, None),
                        ("malformed",), ("refs/heads/lane " + "a" * 40, "malformed")):
            with patch.object(self.doctor, "run_git", side_effect=answers):
                self.assertEqual(self.branch_report()[0], "SKIP")

    def test_owed_fragments_are_named_even_without_git(self):
        names = ("CHANGELOG-ENTRIES-OWED.md", "DECISIONS-ENTRIES-OWED.md", "LEDGER-ENTRIES-OWED.md")
        report = self.doctor.Report(echo=False)
        self.doctor.check_owed_fragments(report, str(self.project / "docs"))
        self.assertEqual(report.lines[0][0], "INFO")
        for name in names:
            (self.project / "docs" / name).write_text("owed")
        report = self.doctor.Report(echo=False)
        self.doctor.check_owed_fragments(report, str(self.project / "docs"))
        self.assertEqual(report.lines[0][0], "WARN")
        for name in names:
            self.assertIn(name, report.lines[0][2])
        self.assertEqual(report.exit_code(), 1)

    def test_owed_fragment_presence_errors_skip_and_dangling_entries_warn(self):
        report = self.doctor.Report(echo=False)
        with patch.object(self.doctor.os, "lstat", side_effect=PermissionError("fixture")):
            self.doctor.check_owed_fragments(report, str(self.project / "docs"))
        self.assertEqual(report.lines[0][0], "SKIP")
        (self.project / "docs/LEDGER-ENTRIES-OWED.md").symlink_to("missing-fragment")
        report = self.doctor.Report(echo=False)
        self.doctor.check_owed_fragments(report, str(self.project / "docs"))
        self.assertEqual(report.lines[0][0], "WARN")
        self.assertIn("LEDGER-ENTRIES-OWED.md", report.lines[0][2])

    def test_placeholder_ids_are_rejected_in_real_registers(self):
        path = self.project / "docs/DECISIONS.md"
        path.write_text("# DECISIONS\n\n## D-0001 — real\n\n## D-NEW-1 — pending\n")
        report = self.doctor.Report(echo=False)
        decisions = self.doctor.scan_decisions(str(path.parent), report)
        self.doctor.check_decisions(report, decisions)
        self.assertTrue(any(level == "WARN" and name == "decisions-template-residue"
                            for level, name, _ in report.lines), report.lines)
        self.assertFalse(any(entry[2] == "D-NEW-" for entry in decisions["entries"]))
        ledger = (ROOT / "templates/LEDGER.md").read_text()
        ledger = ledger[:ledger.index("| LG-0001")] if "| LG-0001" in ledger else ledger
        ledger = ledger.rstrip() + "\n| LG-NEW-1 | P3 | OPEN | 2026-11-26 | Pending | | Reviewed | | code | Report |\n"
        (path.parent / "LEDGER.md").write_text(ledger)
        report = self.doctor.Report(echo=False)
        import datetime
        self.doctor.check_ledger(report, str(path.parent), decisions, datetime.date(2026, 11, 26))
        self.assertIn(("FAIL", "ledger-ids"), [line[:2] for line in report.lines])

    def test_brief_is_short_self_contained_and_linked_from_close(self):
        brief = ROOT / "templates/DELEGATION-BRIEF.md"
        self.assertTrue(brief.is_file(), "missing paste-ready delegation brief")
        text = brief.read_text()
        self.assertLess(len(text.splitlines()), 25)
        for phrase in ("STATUS", "CHANGELOG", "DECISIONS", "LEDGER", "branch", "commits",
                       "alternatives", "rejected", "questions", "commands", "summary lines",
                       "not verified", "D-NEW-1", "LG-NEW-1", "ascending"):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r"\b(?:D|LG)-\d+")
        close = (ROOT / "SKILL.md").read_text().split("### Close after delegation", 1)[1].split("###", 1)[0]
        self.assertIn("templates/DELEGATION-BRIEF.md", close)
        self.assertIn("never allocates", close)
