import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile

import sys
try:
    from reviewer_support import find_root
except ModuleNotFoundError:
    tool_home = Path(__file__).resolve().parents[1] / "workspace" / "packet_tools"
else:
    tool_home = find_root(__file__) / "generators/8b6a2892a064/workspace/packet_tools"
sys.path.insert(0, str(tool_home))
import memory_safe_extract as subject

SAME = b"unchanged source\n"
PAYLOAD = {
    "START-HERE.md": b"Start\n",
    "review.py": b"Review\n",
    "WORK/repo/generators/other/a.py": SAME,
    "WORK/repo/generators/other/b.py": SAME,
    "WORK/repo/generators/chosen/generator.py": SAME,
    "WORK/repo/shared/data/sample.txt": SAME,
}

def bundle(path, *, tamper=False, missing=False, extra=None):
    files = {name[5:]: hashlib.sha256(raw).hexdigest()
             for name, raw in PAYLOAD.items() if name.startswith("WORK/")}
    entries = {name: hashlib.sha256(raw).hexdigest()
               for name, raw in PAYLOAD.items() if not name.startswith("WORK/")}
    manifest = {"files": files, "layout": {"workspace": "WORK", "entry_files": entries}}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, raw in PAYLOAD.items():
            if missing and name.endswith("/b.py"):
                continue
            if tamper and name.endswith("/b.py"):
                raw = b"different content\n"
            archive.writestr(name, raw)
        archive.writestr("WORK/PACKET-MANIFEST.json",
                         json.dumps(manifest, sort_keys=True, separators=(",", ":")))
        if extra is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(*extra)

class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "source.zip"
        self.dest = self.root / "out"
        bundle(self.archive)

    def extract(self):
        return subject.extract(self.archive, self.dest, editable_tasks=["chosen"])

    def test_links_only_immutable_sources_and_keeps_all_bytes(self):
        report = self.extract()
        for name, content in PAYLOAD.items():
            self.assertEqual((self.dest / name).read_bytes(), content)
        other = self.dest / "WORK/repo/generators/other"
        a, b = other / "a.py", other / "b.py"
        self.assertTrue(os.path.samefile(a, b))
        self.assertFalse(os.path.samefile(a, self.dest / "WORK/repo/generators/chosen/generator.py"))
        self.assertFalse(os.path.samefile(a, self.dest / "WORK/repo/shared/data/sample.txt"))
        self.assertEqual(report["hardlinks"], 1)
        self.assertEqual(report["bytes_saved"], len(SAME))

    def test_hash_mismatch_is_rejected_even_for_duplicate_candidate(self):
        bundle(self.archive, tamper=True)
        with self.assertRaises(ValueError):
            self.extract()

    def test_verification_detects_mutated_protected_file(self):
        self.extract()
        target = self.dest / "WORK/repo/generators/chosen/generator.py"
        target.write_bytes(b"edited\n")
        with self.assertRaises(ValueError):
            subject.verify(self.dest)

    def test_verification_detects_missing_file(self):
        self.extract()
        (self.dest / "review.py").unlink()
        with self.assertRaises(ValueError):
            subject.verify(self.dest)

    def test_traversal_is_rejected_without_writing_outside_destination(self):
        bundle(self.archive, extra=("../escape.py", b"bad"))
        with self.assertRaises(ValueError):
            self.extract()
        self.assertFalse((self.root / "escape.py").exists())

    def test_archive_symlink_is_rejected(self):
        info = zipfile.ZipInfo("WORK/repo/symlink")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        bundle(self.archive, extra=(info, b"../outside"))
        with self.assertRaises(ValueError):
            self.extract()

    def test_missing_manifest_member_is_rejected(self):
        bundle(self.archive, missing=True)
        with self.assertRaises(ValueError):
            self.extract()

    def test_duplicate_archive_member_is_rejected(self):
        bundle(self.archive, extra=("review.py", b"again"))
        with self.assertRaises(ValueError):
            self.extract()

    def test_nonempty_destination_is_not_overwritten(self):
        self.dest.mkdir()
        sentinel = self.dest / "keep"
        sentinel.write_bytes(b"mine")
        with self.assertRaises(FileExistsError):
            self.extract()
        self.assertEqual(sentinel.read_bytes(), b"mine")

    def test_detach_before_edit_keeps_other_original_intact(self):
        self.extract()
        changed = subject.detach_tasks(self.dest, ["other"])
        a = self.dest / "WORK/repo/generators/other/a.py"
        b = self.dest / "WORK/repo/generators/other/b.py"
        self.assertGreaterEqual(changed["detached_files"], 1)
        self.assertFalse(os.path.samefile(a, b))
        a.write_bytes(b"changed\n")
        self.assertEqual(b.read_bytes(), SAME)

    def test_verification_rejects_symlink_replacement(self):
        self.extract()
        target = self.dest / "review.py"
        target.unlink()
        target.symlink_to(self.dest / "START-HERE.md")
        with self.assertRaises(ValueError):
            subject.verify(self.dest)

    def test_unknown_editable_task_does_not_disable_protection(self):
        with self.assertRaises(ValueError):
            subject.extract(self.archive, self.dest, editable_tasks=["chsoen"])
        self.assertFalse(self.dest.exists())

    def test_directory_payload_is_rejected(self):
        bundle(self.archive, extra=("WORK/unchecked/", b"unexpected data"))
        with self.assertRaises(ValueError):
            self.extract()

    def test_empty_directory_is_checked_and_counted(self):
        bundle(self.archive, extra=("WORK/empty/", b""))
        report = self.extract()
        self.assertTrue((self.dest / "WORK/empty").is_dir())
        self.assertEqual(report["members"], 8)

    def test_creation_race_does_not_delete_another_owners_file(self):
        from unittest.mock import patch
        real_link = os.link
        def competing_create_then_link(source, destination):
            Path(destination).write_bytes(b"other owner's file")
            return real_link(source, destination)
        with patch.object(subject.os, "link", side_effect=competing_create_then_link):
            with self.assertRaises(FileExistsError):
                self.extract()
        collision = self.dest / "WORK/repo/generators/other/b.py"
        self.assertTrue(collision.exists())
        self.assertEqual(collision.read_bytes(), b"other owner's file")

if __name__ == "__main__":
    unittest.main(verbosity=2)
