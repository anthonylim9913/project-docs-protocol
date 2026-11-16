"""Run the workflow's whitespace step against clean committed fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/tests.yml"


class WorkflowWhitespaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ci-whitespace-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.whitespace", "trailing-space")
        self.commit("tracked.txt", "initial\n")

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, name, contents):
        (self.root / name).write_text(contents, encoding="utf-8")
        self.git("add", name)
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def run_step(self, event, base):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        step = workflow.split("      - name: Whitespace\n", 1)[1]
        command = step.split("        run: ", 1)[1]
        script = textwrap.dedent(command.split("\n", 1)[1]) if command.startswith("|\n") else command.strip()
        environment = os.environ.copy()
        environment.update({"GITHUB_EVENT_NAME": event,
                            "PR_BASE_SHA": base if event == "pull_request" else self.git("rev-parse", "HEAD"),
                            "PUSH_BEFORE_SHA": base if event == "push" else self.git("rev-parse", "HEAD")})
        result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script],
                                cwd=self.root, env=environment, capture_output=True, text=True)
        self.assertEqual(self.git("status", "--porcelain"), "")
        return result

    def assert_event_inputs(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}", workflow)
        self.assertIn("PUSH_BEFORE_SHA: ${{ github.event.before }}", workflow)
        self.assertIn("fetch-depth: 0", workflow)

    def test_committed_whitespace_is_rejected_for_both_events(self):
        base = self.git("rev-parse", "HEAD")
        self.commit("tracked.txt", "bad trailing whitespace \n")
        self.commit("later.txt", "clean last commit\n")
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                result = self.run_step(event, base)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("trailing whitespace", result.stdout)
                self.assert_event_inputs()

    def test_clean_range_does_not_recheck_older_whitespace(self):
        base = self.commit("older.txt", "older whitespace \n")
        self.commit("tracked.txt", "clean change\n")
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                result = self.run_step(event, base)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assert_event_inputs()

    def test_first_push_checks_the_complete_initial_tree(self):
        result = self.run_step("push", "0" * 40)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.commit("tracked.txt", "bad trailing whitespace \n")
        result = self.run_step("push", "0" * 40)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("trailing whitespace", result.stdout)
        self.assert_event_inputs()


if __name__ == "__main__":
    unittest.main()
