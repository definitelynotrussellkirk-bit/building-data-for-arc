"""Behavioral replay tests; synthetic files only, no puzzle/reference access."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name("replay_return.py")
GENERATOR = "repo/generators/0123456789ab/generator.py"
BEFORE = b"VALUE = 'old'\n"
AFTER = b"VALUE = 'new'\n"


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arc-replay-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.work = self.base / "fresh" / "WORK"
        target = self.work / GENERATOR
        target.parent.mkdir(parents=True)
        target.write_bytes(BEFORE)
        self.patch = self.base / "source.patch"
        self.patch.write_text(
            f"diff --git a/{GENERATOR} b/{GENERATOR}\n"
            f"--- a/{GENERATOR}\n+++ b/{GENERATOR}\n"
            "@@ -1 +1 @@\n-VALUE = 'old'\n+VALUE = 'new'\n")
        self.receipt = self.base / "receipt.json"

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.work,
                              text=True, capture_output=True)

    def replay(self, expected=None):
        result = subprocess.run([
            sys.executable, str(TOOL), "--work", str(self.work),
            "--patch", str(self.patch), "--generator", GENERATOR,
            "--sha256", expected or hashlib.sha256(AFTER).hexdigest(),
            "--receipt", str(self.receipt)], text=True, capture_output=True)
        receipt = json.loads(self.receipt.read_text())
        return result, receipt

    def test_parent_git_silent_noop_regression(self):
        self.assertEqual(self.git("init", "-q", str(self.base)).returncode, 0)
        # Existing Git behavior: both operations succeed while skipping this path.
        self.assertEqual(self.git("apply", "--check", str(self.patch)).returncode, 0)
        self.assertEqual(self.git("apply", str(self.patch)).returncode, 0)
        self.assertEqual((self.work / GENERATOR).read_bytes(), BEFORE)
        result, receipt = self.replay()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual((self.work / GENERATOR).read_bytes(), AFTER)
        self.assertEqual(self.git("rev-parse", "--show-toplevel").stdout.strip(), str(self.work))

    def test_successful_nested_fresh_work(self):
        result, receipt = self.replay()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["actual_generator_sha256"], hashlib.sha256(AFTER).hexdigest())
        self.assertEqual(len(receipt["commands"]), 4)
        self.assertTrue(all(row["exit_code"] == 0 for row in receipt["commands"]))
        self.assertTrue(all(row["cwd"] == str(self.work) for row in receipt["commands"]))

    def test_hash_mismatch_is_failure(self):
        result, receipt = self.replay("0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertIn("SHA-256 mismatch", receipt["error"])
        self.assertEqual(receipt["actual_generator_sha256"], hashlib.sha256(AFTER).hexdigest())

    def test_patch_failure_does_not_apply(self):
        (self.work / GENERATOR).write_bytes(b"VALUE = 'other'\n")
        result, receipt = self.replay()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertNotEqual(receipt["commands"][-1]["exit_code"], 0)
        self.assertIn("--check", receipt["commands"][-1]["argv"])
        self.assertEqual((self.work / GENERATOR).read_bytes(), b"VALUE = 'other'\n")

    def test_symlink_git_directory_is_rejected(self):
        self.assertEqual(self.git("init", "-q", str(self.base)).returncode, 0)
        (self.work / ".git").symlink_to(self.base / ".git", target_is_directory=True)
        result, receipt = self.replay()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Symlink", receipt["error"])
        self.assertEqual(receipt["commands"], [])
        self.assertEqual((self.work / GENERATOR).read_bytes(), BEFORE)

    def test_gitfile_is_rejected(self):
        (self.work / ".git").write_text("gitdir: /unexpected/repository\n")
        result, receipt = self.replay()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a gitfile", receipt["error"])
        self.assertEqual(receipt["commands"], [])

    def test_existing_git_root_redirect_is_rejected(self):
        self.assertEqual(self.git("init", "-q").returncode, 0)
        self.assertEqual(self.git("config", "core.worktree", str(self.base)).returncode, 0)
        result, receipt = self.replay()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unexpected Git root", receipt["error"])
        self.assertEqual(len(receipt["commands"]), 1)
        self.assertEqual((self.work / GENERATOR).read_bytes(), BEFORE)


if __name__ == "__main__":
    unittest.main()
