"""Small fixture regressions for replay_return.py; requires Python and real Git."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).with_name("replay_return.py")
PATCH = (
    "diff --git a/repo/message.txt b/repo/message.txt\n"
    "--- a/repo/message.txt\n"
    "+++ b/repo/message.txt\n"
    "@@ -1 +1 @@\n"
    "-before\n"
    "+after\n"
)


class ReplayReturnTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="replay-return-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.original = self.base / "original.zip"
        self.returned = self.base / "returned.zip"
        self.fresh = self.base / "fresh"
        self.receipt = self.base / "receipt.json"

    def archives(self, layout="envelope", patch=PATCH, extra_original=None,
                 extra_return=None, message="before\n"):
        prefix = "WORK/" if layout == "envelope" else ""
        with zipfile.ZipFile(self.original, "w") as archive:
            archive.writestr(prefix + "repo/message.txt", message)
            for name, content in extra_original or []:
                archive.writestr(name, content)
        with zipfile.ZipFile(self.returned, "w") as archive:
            if patch is not None:
                archive.writestr("patches/source.patch", patch)
            for name, content in extra_return or []:
                archive.writestr(name, content)

    def run_command(self, environment=None):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if environment:
            env.update(environment)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.original), str(self.returned),
             str(self.fresh), "--receipt", str(self.receipt)],
            capture_output=True, text=True, env=env, cwd=self.base,
        )
    def invoke(self, environment=None):
        result = self.run_command(environment)
        self.assertTrue(self.receipt.is_file(), result.stderr)
        return result, json.loads(self.receipt.read_text())

    def assert_success(self, result, receipt, root):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["status"], "success")
        self.assertEqual(receipt["git_root"], str(root.resolve()))
        self.assertEqual((root / "repo/message.txt").read_text(), "after\n")
        self.assertEqual(
            receipt["patched_files"]["repo/message.txt"],
            hashlib.sha256(b"after\n").hexdigest(),
        )
        self.assertEqual(receipt["original_zip"]["sha256"],
                         hashlib.sha256(self.original.read_bytes()).hexdigest())
        self.assertEqual(receipt["return_zip"]["sha256"],
                         hashlib.sha256(self.returned.read_bytes()).hexdigest())
        self.assertEqual(receipt["patch"]["sha256"],
                         hashlib.sha256(PATCH.encode()).hexdigest())
        self.assertEqual(receipt["verification"], "patch_application_only")
        self.assertTrue(receipt["commands"])
        self.assertTrue(all(c["cwd"] == str(root.resolve())
                            for c in receipt["commands"]))
        self.assertTrue(all(c["exit_code"] == 0 for c in receipt["commands"]))
        check_positions = [i for i, c in enumerate(receipt["commands"])
                           if "apply" in c["argv"] and "--check" in c["argv"]]
        apply_positions = [i for i, c in enumerate(receipt["commands"])
                           if "apply" in c["argv"] and "--check" not in c["argv"]
                           and "--numstat" not in c["argv"]]
        self.assertEqual(len(check_positions), 1)
        self.assertEqual(len(apply_positions), 1)
        self.assertLess(check_positions[0], apply_positions[0])

    def test_envelope_applies_from_work_and_ignores_inherited_git(self):
        marker = self.base / "must-not-run"
        self.archives(extra_return=[("commands/run.sh", "touch " + str(marker))])
        parent = self.base / "parent"
        parent.mkdir()
        subprocess.run(["git", "init", "-q", str(parent)], check=True,
                       capture_output=True)
        result, receipt = self.invoke({"GIT_DIR": str(parent / ".git"),
                                       "GIT_WORK_TREE": str(parent)})
        self.assert_success(result, receipt, self.fresh / "WORK")
        self.assertFalse((self.fresh / ".git").exists())
        self.assertTrue((self.fresh / "WORK/.git").is_dir())
        self.assertFalse((parent / "repo").exists())
        self.assertFalse(marker.exists())

    def test_legacy_layout_applies_from_extraction_root(self):
        self.archives(layout="legacy")
        result, receipt = self.invoke()
        self.assert_success(result, receipt, self.fresh)

    def test_existing_destination_is_preserved(self):
        self.archives()
        self.fresh.mkdir()
        sentinel = self.fresh / "keep.txt"
        sentinel.write_text("keep exactly\n")
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(sentinel.read_text(), "keep exactly\n")
        self.assertEqual(list(self.fresh.iterdir()), [sentinel])
        self.assertEqual(receipt["commands"], [])

    def test_original_zip_traversal_is_rejected_before_extraction(self):
        self.archives(extra_original=[("../escaped.txt", "bad")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse((self.base / "escaped.txt").exists())
        self.assertFalse(self.fresh.exists())

    def test_return_zip_traversal_is_rejected(self):
        self.archives(extra_return=[("../escaped.txt", "bad")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse((self.base / "escaped.txt").exists())

    def test_original_zip_symlink_is_rejected(self):
        symlink = zipfile.ZipInfo("WORK/repo/link")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.archives(extra_original=[(symlink, "../../outside")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse(self.fresh.exists())

    def test_archive_git_metadata_is_rejected(self):
        self.archives(extra_original=[("WORK/.git/config", "[core]\n")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["commands"], [])

    def test_ambiguous_layout_is_rejected(self):
        self.archives(extra_original=[("repo/other.txt", "other\n")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["commands"], [])

    def test_missing_exact_patch_is_rejected(self):
        self.archives(patch=None, extra_return=[("source.patch", PATCH)])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")

    def test_patch_cannot_write_outside_root(self):
        patch = (
            "diff --git a/../escaped.txt b/../escaped.txt\n"
            "new file mode 100644\n--- /dev/null\n+++ b/../escaped.txt\n"
            "@@ -0,0 +1 @@\n+bad\n"
        )
        self.archives(layout="legacy", patch=patch)
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse((self.base / "escaped.txt").exists())

    def test_patch_cannot_create_symlinks(self):
        patch = (
            "diff --git a/repo/link b/repo/link\nnew file mode 120000\n"
            "--- /dev/null\n+++ b/repo/link\n@@ -0,0 +1 @@\n+../../outside\n"
        )
        self.archives(patch=patch)
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse((self.fresh / "WORK/repo/link").is_symlink())

    def test_failed_apply_check_is_recorded_without_apply(self):
        self.archives(patch=PATCH.replace("-before\n", "-not-the-original\n"))
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        checks = [c for c in receipt["commands"]
                  if "apply" in c["argv"] and "--check" in c["argv"]]
        self.assertEqual(len(checks), 1)
        self.assertNotEqual(checks[0]["exit_code"], 0)
        self.assertFalse(any("apply" in c["argv"]
                             and "--check" not in c["argv"]
                             and "--numstat" not in c["argv"]
                             for c in receipt["commands"]))
        self.assertEqual((self.fresh / "WORK/repo/message.txt").read_text(),
                         "before\n")

    def test_existing_receipt_is_preserved_before_replay(self):
        self.archives()
        original_receipt = b'{"existing": "must remain unchanged"}\n'
        self.receipt.write_bytes(original_receipt)
        result = self.run_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.receipt.read_bytes(), original_receipt)
        self.assertFalse(self.fresh.exists())

    def test_receipt_symlink_and_its_target_are_preserved(self):
        self.archives()
        target = self.base / "existing-receipt-target.json"
        original_receipt = b'{"existing": "symlink target"}\n'
        target.write_bytes(original_receipt)
        self.receipt.symlink_to(target)
        result = self.run_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.receipt.is_symlink())
        self.assertEqual(target.read_bytes(), original_receipt)
        self.assertFalse(self.fresh.exists())

    def test_dangling_receipt_symlink_is_preserved(self):
        self.archives()
        target = self.base / "must-not-create.json"
        self.receipt.symlink_to(target)
        result = self.run_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.receipt.is_symlink())
        self.assertFalse(target.exists())
        self.assertFalse(self.fresh.exists())

    def test_receipt_writer_refuses_a_collision_at_write_time(self):
        # This bypasses CLI preflight to exercise a late collision directly.
        specification = importlib.util.spec_from_file_location("replay_helper", SCRIPT)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        original_receipt = b'{"existing": "created after preflight"}\n'
        self.receipt.write_bytes(original_receipt)
        with self.assertRaises(FileExistsError):
            module.write_receipt(self.receipt, {"replacement": "forbidden"})
        self.assertEqual(self.receipt.read_bytes(), original_receipt)

    def assert_outside_source_rejected(self, patch, destination):
        self.archives(patch=patch, extra_original=[("WORK/outside.txt", "outside\n")])
        result, receipt = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        if self.fresh.exists():
            self.assertEqual((self.fresh / "WORK/outside.txt").read_text(), "outside\n")
        self.assertFalse((self.fresh / "WORK/repo" / destination).exists())

    def test_outside_source_rename_is_rejected(self):
        self.assert_outside_source_rejected(
            "diff --git a/outside.txt b/repo/moved.txt\n"
            "similarity index 100%\nrename from outside.txt\n"
            "rename to repo/moved.txt\n", "moved.txt")

    def test_outside_source_copy_is_rejected(self):
        self.assert_outside_source_rejected(
            "diff --git a/outside.txt b/repo/copied.txt\n"
            "similarity index 100%\ncopy from outside.txt\n"
            "copy to repo/copied.txt\n", "copied.txt")

    def test_outside_source_normal_hunk_is_rejected(self):
        self.assert_outside_source_rejected(
            "diff --git a/outside.txt b/repo/moved.txt\n"
            "--- a/outside.txt\n+++ b/repo/moved.txt\n"
            "@@ -1 +1 @@\n-outside\n+moved\n", "moved.txt")

    def test_header_like_hunk_content_is_supported(self):
        patch = (
            "diff --git a/repo/message.txt b/repo/message.txt\n"
            "--- a/repo/message.txt\n+++ b/repo/message.txt\n"
            "@@ -1 +1 @@\n--- a/outside.txt\n+++ b/outside.txt\n"
        )
        self.archives(patch=patch, message="-- a/outside.txt\n")
        result, receipt = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["status"], "success")
        self.assertEqual((self.fresh / "WORK/repo/message.txt").read_text(),
                         "++ b/outside.txt\n")

    def test_added_and_deleted_files_are_supported_and_hashed(self):
        patch = (
            "diff --git a/repo/message.txt b/repo/message.txt\n"
            "deleted file mode 100644\n--- a/repo/message.txt\n+++ /dev/null\n"
            "@@ -1 +0,0 @@\n-before\n"
            "diff --git a/repo/added.txt b/repo/added.txt\n"
            "new file mode 100644\n--- /dev/null\n+++ b/repo/added.txt\n"
            "@@ -0,0 +1 @@\n+added\n"
        )
        self.archives(patch=patch)
        result, receipt = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["patched_files"], {
            "repo/message.txt": None,
            "repo/added.txt": hashlib.sha256(b"added\n").hexdigest(),
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
