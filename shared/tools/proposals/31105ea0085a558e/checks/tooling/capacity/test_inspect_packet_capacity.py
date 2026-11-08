"""Behavior checks for the read-only ZIP capacity inspector."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parent


def entry(name, size=0, mode=0):
    info = zipfile.ZipInfo(name)
    info.file_size = size
    info.external_attr = mode << 16
    return info


class InventorySafety(unittest.TestCase):
    def test_rejects_unsafe_paths_before_extracting(self):
        from inspect_packet_capacity import inventory
        for name in ("../x", "a/../x", "/absolute", "C:/absolute", "C:relative",
                     "a\\b", "a//b", "./a", "a/.", "a\0hidden", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                inventory([entry(name)], 4096)

    def test_rejects_duplicates_and_file_directory_conflicts(self):
        from inspect_packet_capacity import inventory
        for names in (("a", "a"), ("a/", "a/"), ("a", "a/b"), ("a/b", "a"),
                      ("a", "a/"), ("a/", "a")):
            with self.subTest(names=names), self.assertRaises(ValueError):
                inventory([entry(name) for name in names], 4096)

    def test_rejects_symlinks_special_files_and_inconsistent_directories(self):
        from inspect_packet_capacity import inventory
        for item in (entry("link", mode=stat.S_IFLNK), entry("fifo", mode=stat.S_IFIFO),
                     entry("dir", mode=stat.S_IFDIR), entry("file/", mode=stat.S_IFREG),
                     entry("dir/", size=1)):
            with self.subTest(name=item.filename, mode=item.external_attr), self.assertRaises(ValueError):
                inventory([item], 4096)

    def test_counts_explicit_and_implied_directories_once(self):
        from inspect_packet_capacity import inventory
        result = inventory([entry("a/b/file"), entry("a/"), entry("a/b/"), entry("empty/")], 4096)
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["directories"], 3)
        self.assertEqual(result["explicit_directories"], 3)
        self.assertEqual(result["minimum_inodes"], 4)

    def test_rounds_each_nonempty_file_separately(self):
        from inspect_packet_capacity import inventory
        result = inventory([entry("empty"), entry("one", 1), entry("exact", 4096),
                            entry("over", 4097)], 4096)
        self.assertEqual(result["uncompressed_bytes"], 8194)
        self.assertEqual(result["dense_file_allocation_lower_bound_bytes"], 16384)


class FilesystemCapacity(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "sample.zip"
        with zipfile.ZipFile(self.source, "w") as archive:
            archive.writestr("file", b"payload must remain unopened")

    def report(self, total_inodes, available_inodes, available_blocks=100):
        from inspect_packet_capacity import inspect_packet
        filesystem = os.statvfs_result((4096, 4096, 1000, 100, available_blocks,
                                       total_inodes, available_inodes, available_inodes, 0, 255))
        with mock.patch("inspect_packet_capacity.os.statvfs", return_value=filesystem):
            return inspect_packet(self.source, self.root)

    def test_zero_total_inodes_are_unknown_and_json_has_no_infinity(self):
        result = self.report(0, 0)
        self.assertEqual(result["inode_availability"], "unknown")
        self.assertIsNone(result["available_inodes"])
        self.assertIsNone(result["inode_headroom_after_inventory"])
        self.assertEqual(result["capacity_status"], "unknown")
        json.dumps(result, allow_nan=False)

    def test_known_zero_available_inodes_are_exhausted(self):
        result = self.report(1000, 0)
        self.assertEqual(result["available_inodes"], 0)
        self.assertEqual(result["inode_headroom_after_inventory"], -1)
        self.assertEqual(result["capacity_status"], "insufficient")

    def test_byte_shortfall_remains_definitive_with_unknown_inodes(self):
        result = self.report(0, 0, available_blocks=0)
        self.assertEqual(result["byte_headroom_after_file_data_lower_bound"], -4096)
        self.assertEqual(result["capacity_status"], "insufficient")

    def test_never_opens_member_payloads(self):
        from inspect_packet_capacity import inspect_packet
        with mock.patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("member payload read")):
            result = inspect_packet(self.source, self.root)
        self.assertEqual(result["inventory"]["files"], 1)


class CapacityCLI(unittest.TestCase):
    def test_cli_counts_empty_files_and_implied_directories_without_extracting(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            source = root / "sample.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("a/b/item", b"abc")
                archive.writestr("a/empty", b"")
                archive.writestr("empty/", b"")
            destination = root / "new" / "target"
            result = subprocess.run(
                [sys.executable, str(ROOT / "inspect_packet_capacity.py"), str(source), str(destination)],
                capture_output=True, text=True)
            self.assertIn(result.returncode, (0, 1, 3), result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["inventory"]["files"], 2)
            self.assertEqual(report["inventory"]["directories"], 3)
            self.assertEqual(report["inventory"]["uncompressed_bytes"], 3)
            self.assertEqual(report["new_destination_directories"], 2)
            self.assertEqual(report["required_inodes"], 7)
            self.assertFalse(destination.exists())
            self.assertFalse((root / "a").exists())


if __name__ == "__main__":
    unittest.main()
