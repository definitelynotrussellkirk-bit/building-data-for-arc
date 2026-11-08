"""Focused regressions for the optional, metadata-only ZIP capacity helper."""
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import warnings
import zipfile

HELPER = Path(__file__).with_name("zip_capacity.py")


class ZipCapacityTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HELPER.is_file(), "Standalone ZIP capacity helper is not implemented")
        spec = importlib.util.spec_from_file_location("zip_capacity_under_test", HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temporary = tempfile.TemporaryDirectory(prefix="zip-capacity-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root / "packet.zip"
        self.destination = self.root / "new" / "review"

    def make_archive(self, rows=None):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Duplicate name:")
            with zipfile.ZipFile(self.archive, "w") as archive:
                for name, content in rows or [("a/b.txt", b"x"), ("a/", b""), ("a/c", b"")]:
                    archive.writestr(name, content)

    def counters(self, **changes):
        values = dict(f_bsize=4096, f_frsize=4096, f_blocks=100000,
                      f_bfree=90000, f_bavail=80000, f_files=100000,
                      f_ffree=90000, f_favail=80000, f_flag=0, f_namemax=255)
        values.update(changes)
        return SimpleNamespace(**values)

    def inspect(self, **counter_changes):
        with patch.object(self.module.os, "statvfs", return_value=self.counters(**counter_changes)):
            return self.module.inspect_capacity(self.archive, self.destination)

    def test_zero_inodes_blocks_even_with_positive_free_and_available_bytes(self):
        # Removing the inode admission check must fail this observed-incident regression.
        self.make_archive()
        report = self.inspect(f_ffree=0, f_favail=0)
        self.assertEqual(report["status"], "insufficient")
        self.assertEqual(report["exit_code"], 2)
        self.assertGreater(report["filesystem"]["free_bytes"], 0)
        self.assertGreater(report["filesystem"]["available_bytes"], 0)
        self.assertIn("available_inodes", report["shortages"])

    def test_reserved_free_bytes_do_not_count_as_available(self):
        self.make_archive()
        report = self.inspect(f_bavail=0)
        self.assertEqual(report["exit_code"], 2)
        self.assertIn("available_bytes", report["shortages"])
        self.assertGreater(report["filesystem"]["free_bytes"], 0)

    def test_counts_implicit_directories_once_and_includes_missing_target_chain(self):
        self.make_archive()
        report = self.inspect()
        self.assertEqual(report["status"], "sufficient")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["archive"]["files"], 2)
        self.assertEqual(report["archive"]["directories"], 1)
        self.assertEqual(report["destination"]["missing_directories"], 2)
        self.assertEqual(report["required"]["inodes"], 5)
        self.assertEqual(report["required"]["estimated_allocated_bytes"], 16384)
        self.assertEqual(report["filesystem"]["path"], str(self.root))

    def test_existing_directory_is_not_counted_as_a_missing_inode(self):
        self.make_archive()
        self.destination.mkdir(parents=True)
        report = self.inspect()
        self.assertEqual(report["destination"]["missing_directories"], 0)
        self.assertEqual(report["required"]["inodes"], 3)

    def test_rejects_traversal_absolute_and_ambiguous_member_paths(self):
        for name in ["../escape", "/escape", "C:/escape", "C:escape",
                     "a\\escape", "a/../escape", "a//escape", "a/./escape"]:
            with self.subTest(name=name):
                self.make_archive([(name, b"x")])
                report = self.inspect()
                self.assertEqual(report["status"], "invalid")
                self.assertEqual(report["exit_code"], 2)

    def test_rejects_embedded_nul_before_zipfile_truncation(self):
        self.make_archive([("badX", b"x")])
        self.archive.write_bytes(self.archive.read_bytes().replace(b"badX", b"bad\x00"))
        self.assertEqual(self.inspect()["status"], "invalid")

    def test_rejects_symlink_archive_members(self):
        member = zipfile.ZipInfo("link")
        member.create_system = 3
        member.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make_archive([(member, b"outside")])
        self.assertEqual(self.inspect()["status"], "invalid")

    def test_rejects_duplicate_member_names(self):
        self.make_archive([("same", b"x"), ("same", b"y")])
        self.assertEqual(self.inspect()["status"], "invalid")

    def test_rejects_file_directory_conflicts_in_both_orders(self):
        for rows in [[("a", b"x"), ("a/b", b"y")],
                     [("a/b", b"y"), ("a", b"x")],
                     [("a/", b""), ("a", b"x")]]:
            with self.subTest(rows=rows):
                self.make_archive(rows)
                self.assertEqual(self.inspect()["status"], "invalid")

    def test_unknown_inode_accounting_is_not_misreported_as_zero_or_sufficient(self):
        self.make_archive()
        report = self.inspect(f_files=0, f_ffree=0, f_favail=0)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["exit_code"], 1)
        self.assertIsNone(report["filesystem"]["available_inodes"])
        self.assertEqual(report["shortages"], [])

    def test_known_byte_shortage_takes_precedence_over_unknown_inodes(self):
        self.make_archive()
        report = self.inspect(f_files=0, f_ffree=0, f_favail=0, f_bavail=0)
        self.assertEqual(report["status"], "insufficient")
        self.assertEqual(report["exit_code"], 2)

    def test_metadata_only_inspection_does_not_read_members_or_create_destination(self):
        self.make_archive()
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("Read member content")), \
             patch.object(zipfile.ZipFile, "extract", side_effect=AssertionError("Extraction")), \
             patch.object(zipfile.ZipFile, "extractall", side_effect=AssertionError("Extraction")):
            report = self.inspect()
        after = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        self.assertEqual(report["status"], "sufficient")
        self.assertEqual(before, after)
        self.assertFalse(self.destination.exists())
        self.assertIn("mount_namespace", report["environment"])

    def test_rejects_non_directory_destination_ancestor(self):
        self.make_archive()
        self.destination.parent.write_text("file")
        self.assertEqual(self.inspect()["status"], "invalid")

    def test_invalid_zip_returns_json_and_nonzero_cli_status(self):
        self.archive.write_text("not a zip")
        run = subprocess.run([sys.executable, "-B", str(HELPER), "--archive", str(self.archive),
                              "--destination", str(self.destination)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "invalid")
        self.assertFalse(self.destination.exists())

    def test_cli_reports_current_namespace_without_extracting(self):
        self.make_archive()
        run = subprocess.run([sys.executable, "-B", str(HELPER), "--archive", str(self.archive),
                              "--destination", str(self.destination)], text=True, capture_output=True)
        report = json.loads(run.stdout)
        self.assertEqual(run.returncode, report["exit_code"], run.stderr)
        self.assertIn(run.returncode, [0, 1, 2])
        self.assertNotEqual(report["status"], "invalid")
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
