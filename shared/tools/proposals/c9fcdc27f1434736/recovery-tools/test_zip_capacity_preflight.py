"""Behavior tests for metadata-only ZIP capacity checks; no large fixtures."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile


HERE = Path(__file__).resolve().parent


class ZipCapacityTests(unittest.TestCase):
    def setUp(self):
        fixture_parent = os.environ.get("ZIP_PREFLIGHT_TEST_TMPDIR", str(HERE))
        self.temporary = tempfile.TemporaryDirectory(prefix=".preflight-test-", dir=fixture_parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def tool(self):
        self.assertTrue((HERE / "zip_capacity_preflight.py").is_file(),
                        "The standalone ZIP capacity utility has not been implemented")
        return importlib.import_module("zip_capacity_preflight")

    def archive(self, entries):
        path = self.root / "fixture.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, payload in entries:
                archive.writestr(name, payload)
        return path

    def test_counts_implicit_and_explicit_directories_once_without_reading_payloads(self):
        # Missing implicit directories or double-counting explicit parents
        # would underestimate/exaggerate the inode budget.
        path = self.archive([
            ("nested/", b""),
            ("nested/one", b"x"),
            ("nested/deeper/two", b"x" * 4097),
            ("zero", b""),
            ("empty/", b""),
        ])
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("Payload read forbidden")):
            report = self.tool().inspect_archive(path, block_size=4096)
        self.assertEqual(report["file_count"], 3)
        self.assertEqual(report["directory_count"], 3)
        self.assertEqual(report["entry_count"], 6)
        self.assertEqual(report["expanded_file_bytes"], 4098)
        self.assertEqual(report["block_rounded_file_bytes"], 12288)

    def test_rejects_traversal_absolute_and_ambiguous_member_names(self):
        # ZIP readers must not normalize an unsafe path into a different name.
        for name in ("../escape", "/absolute", "a/../../escape", "./a", "a//b",
                     "a\\b", "C:/drive", "a:stream", "a/./b", "a//"):
            with self.subTest(name=name):
                path = self.archive([(name, b"")])
                with self.assertRaises(ValueError):
                    self.tool().inspect_archive(path, block_size=4096)

    def test_rejects_nul_before_zipfile_can_hide_the_original_name(self):
        # ZipInfo.filename truncates at NUL; orig_filename must be validated.
        path = self.archive([("axb", b"")])
        path.write_bytes(path.read_bytes().replace(b"axb", b"a\x00b"))
        with self.assertRaises(ValueError):
            self.tool().inspect_archive(path, block_size=4096)

    def test_rejects_duplicate_entries_instead_of_undercounting(self):
        for entries in ([('same', b'x'), ('same', b'y')],
                        [('folder/', b''), ('folder/', b'')]):
            with self.subTest(entries=entries):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    path = self.archive(entries)
                with self.assertRaises(ValueError):
                    self.tool().inspect_archive(path, block_size=4096)

    def test_rejects_case_aliases_and_file_directory_conflicts(self):
        for names in (("File", "file"), ("A/one", "a/two"),
                      ("a", "a/b"), ("a/b", "a"), ("a/", "a")):
            with self.subTest(names=names):
                path = self.archive([(name, b"") for name in names])
                with self.assertRaises(ValueError):
                    self.tool().inspect_archive(path, block_size=4096)

    def test_rejects_symlinks_and_special_unix_member_types(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK):
            with self.subTest(kind=kind):
                member = zipfile.ZipInfo("entry")
                member.create_system = 3
                member.external_attr = (kind | 0o644) << 16
                path = self.archive([(member, b"")])
                with self.assertRaises(ValueError):
                    self.tool().inspect_archive(path, block_size=4096)

    def test_rejects_directory_metadata_that_disagrees_with_the_name(self):
        for name, kind, payload in (("dir", stat.S_IFDIR, b""),
                                    ("file/", stat.S_IFREG, b""),
                                    ("dir/", stat.S_IFDIR, b"payload")):
            with self.subTest(name=name, kind=kind):
                member = zipfile.ZipInfo(name)
                member.create_system = 3
                member.external_attr = (kind | 0o644) << 16
                path = self.archive([(member, payload)])
                with self.assertRaises(ValueError):
                    self.tool().inspect_archive(path, block_size=4096)

    def capacity(self, *, free_bytes=4096, free_inodes=2, total_inodes=100):
        # Filesystem capacity is injected because exhausting the real shared
        # filesystem would be destructive; all ZIP and directory I/O stays real.
        return os.statvfs_result((4096, 4096, 100, free_bytes // 4096,
                                  free_bytes // 4096, total_inodes,
                                  free_inodes, free_inodes, 0, 255))

    def preflight(self, path, destination, capacity, **kwargs):
        function = getattr(self.tool(), "preflight", None)
        self.assertTrue(callable(function), "Capacity preflight is not implemented")
        with patch("os.statvfs", return_value=capacity):
            return function(path, destination, **kwargs)

    def test_exact_capacity_passes_and_one_inode_short_fails(self):
        path = self.archive([("file", b"x")])
        destination = self.root / "new"
        for inodes, code in ((2, 0), (1, 3), (0, 3)):
            with self.subTest(inodes=inodes):
                report = self.preflight(path, destination, self.capacity(free_inodes=inodes))
                self.assertEqual(report["exit_code"], code)
                self.assertEqual(report["checks"]["inodes"]["required"], 2)
                self.assertEqual(report["checks"]["inodes"]["shortfall"], max(0, 2 - inodes))
                self.assertEqual(report["checks"]["bytes"]["required"], 4096)
                self.assertFalse(destination.exists())

    def test_reports_byte_and_inode_shortfalls_together(self):
        path = self.archive([("file", b"x" * 4097)])
        report = self.preflight(path, self.root / "new",
                                self.capacity(free_bytes=4096, free_inodes=1))
        self.assertEqual(report["exit_code"], 3)
        self.assertEqual(report["checks"]["bytes"]["shortfall"], 4096)
        self.assertEqual(report["checks"]["inodes"]["shortfall"], 1)

    def test_counts_missing_destination_ancestors_and_requested_reserves(self):
        path = self.archive([("file", b"x")])
        destination = self.root / "missing" / "nested"
        report = self.preflight(path, destination,
                                self.capacity(free_bytes=8192, free_inodes=4),
                                reserve_bytes=4096, reserve_inodes=1)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["destination"]["new_directory_count"], 2)
        self.assertEqual(report["checks"]["inodes"]["required"], 4)
        self.assertEqual(report["checks"]["bytes"]["required"], 8192)
        self.assertFalse(destination.parent.exists())

    def test_empty_archive_existing_empty_destination_needs_no_new_entries(self):
        path = self.archive([])
        destination = self.root / "empty"
        destination.mkdir()
        report = self.preflight(path, destination, self.capacity(free_bytes=0, free_inodes=0))
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["checks"]["inodes"]["required"], 0)
        self.assertEqual(report["checks"]["bytes"]["required"], 0)

    def test_unknown_inode_accounting_cannot_claim_sufficient_capacity(self):
        path = self.archive([("file", b"x")])
        report = self.preflight(path, self.root / "new",
                                self.capacity(total_inodes=0, free_inodes=0))
        self.assertEqual(report["exit_code"], 4)
        self.assertIsNone(report["checks"]["inodes"]["available"])
        self.assertIsNone(report["checks"]["inodes"]["sufficient"])

    def test_rejects_nonempty_destination_without_overwrite(self):
        path = self.archive([("file", b"new")])
        destination = self.root / "existing"
        destination.mkdir()
        retained = destination / "file"
        retained.write_bytes(b"retained")
        report = self.preflight(path, destination, self.capacity())
        self.assertEqual(report["exit_code"], 4)
        self.assertEqual(retained.read_bytes(), b"retained")

    def test_rejects_destination_symlinks_including_ancestors(self):
        path = self.archive([("file", b"x")])
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        link.symlink_to(real, target_is_directory=True)
        for destination in (link, link / "new"):
            with self.subTest(destination=destination):
                report = self.preflight(path, destination, self.capacity())
                self.assertEqual(report["exit_code"], 4)
        self.assertEqual(list(real.iterdir()), [])

    def test_invalid_archive_returns_json_friendly_error(self):
        path = self.root / "broken.zip"
        path.write_bytes(b"not a zip archive")
        report = self.preflight(path, self.root / "new", self.capacity())
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["status"], "invalid_archive")
        self.assertIsInstance(report["error"], str)

    def test_unsupported_zip_version_is_a_structured_archive_error(self):
        # zipfile raises NotImplementedError before exposing the inventory.
        member = zipfile.ZipInfo("file")
        member.extract_version = 99
        path = self.archive([(member, b"x")])
        try:
            report = self.preflight(path, self.root / "new", self.capacity())
        except NotImplementedError as error:
            self.fail(f"Unsupported archive metadata escaped the JSON error report: {error}")
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["status"], "invalid_archive")

    def test_cli_reports_metadata_without_creating_destination(self):
        path = self.archive([("folder/file", b"x")])
        destination = self.root / "new"
        run = subprocess.run([sys.executable, "-B", str(HERE / "zip_capacity_preflight.py"),
                              str(path), str(destination)],
                             capture_output=True, text=True, check=False)
        self.assertTrue(run.stdout.strip(), "The CLI must emit a JSON report")
        report = json.loads(run.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["archive"]["file_count"], 1)
        self.assertEqual(report["archive"]["directory_count"], 1)
        self.assertEqual(report["checks"]["inodes"]["required"], 3)
        self.assertFalse(destination.exists())

    def test_negative_reserves_cannot_turn_a_shortfall_into_a_pass(self):
        path = self.archive([("file", b"x")])
        for reserves in ({"reserve_bytes": -4096}, {"reserve_inodes": -2}):
            with self.subTest(reserves=reserves):
                report = self.preflight(path, self.root / "new",
                                        self.capacity(free_bytes=0, free_inodes=0), **reserves)
                self.assertEqual(report["exit_code"], 2)
                self.assertEqual(report["status"], "invalid_arguments")

    def test_invalid_block_sizes_are_rejected_explicitly(self):
        path = self.archive([("file", b"x")])
        for block_size in (0, -1, 0.5):
            with self.subTest(block_size=block_size):
                try:
                    self.tool().inspect_archive(path, block_size=block_size)
                except Exception as error:
                    self.assertIsInstance(error, ValueError)
                else:
                    self.fail("Invalid allocation block size was accepted")

    def test_destination_parent_traversal_cannot_hide_a_symlink(self):
        path = self.archive([("file", b"x")])
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        link.symlink_to(real, target_is_directory=True)
        report = self.preflight(path, link / ".." / "new", self.capacity())
        self.assertEqual(report["exit_code"], 4)

    def test_cli_uses_exit_codes_for_shortfall_and_invalid_metadata(self):
        path = self.archive([("file", b"x")])
        destination = self.root / "new"
        command = [sys.executable, "-B", str(HERE / "zip_capacity_preflight.py"),
                   str(path), str(destination)]
        run = subprocess.run([*command, "--reserve-inodes", str(1 << 62)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertFalse(json.loads(run.stdout)["checks"]["inodes"]["sufficient"])
        self.archive([("../escape", b"")])
        run = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "invalid_archive")
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
