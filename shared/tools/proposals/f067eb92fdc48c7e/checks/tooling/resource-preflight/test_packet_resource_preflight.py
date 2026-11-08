import io
import unittest
import warnings
import zipfile

from packet_resource_preflight import archive_inventory, capacity_report


def inventory(entries):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(stream, "w") as archive:
            for name, content in entries:
                archive.writestr(name, content)
    stream.seek(0)
    with zipfile.ZipFile(stream) as archive:
        return archive_inventory(archive)


class PreflightTests(unittest.TestCase):
    def test_shared_implicit_directories_count_once(self):
        result = inventory([("a/b/x", b"x"), ("a/b/y", b"y"), ("a/", b"")])
        self.assertEqual(result["distinct_files"], 2)
        self.assertEqual(result["distinct_directories"], 2)
        self.assertEqual(result["estimated_inodes"], 4)
        self.assertEqual(result["rounded_file_bytes"], 8192)
        self.assertEqual(result["errors"], [])

    def test_low_inodes_despite_enough_bytes(self):
        result = capacity_report(inventory([("a/b/file", b"x")]), 1_000_000, 2)
        self.assertTrue(result["bytes_sufficient"])
        self.assertFalse(result["inodes_sufficient"])
        self.assertFalse(result["capacity_sufficient"])

    def test_path_traversal_and_absolute_paths_rejected(self):
        result = inventory([("../file", b"x"), ("a/../file", b"x"), ("/absolute", b"x"),
                            ("C:/drive", b"x"), ("a\\file", b"x")])
        self.assertEqual(len(result["errors"]), 5)
        self.assertTrue(all(row["kind"] == "unsafe_path" for row in result["errors"]))

    def test_duplicate_archive_names_rejected(self):
        result = inventory([("a/file", b"first"), ("a/file", b"second")])
        self.assertEqual(result["distinct_files"], 1)
        self.assertEqual(result["errors"], [{"kind": "duplicate_member", "member": "a/file", "count": 2}])

    def test_file_as_parent_rejected(self):
        result = inventory([("a", b"x"), ("a/file", b"y")])
        self.assertIn({"kind": "file_directory_conflict", "member": "a"}, result["errors"])

    def test_copy_and_reserve_budgets(self):
        result = capacity_report(inventory([("file", b"x")]), 1_000_000, 100,
            extra_bytes=100, extra_inodes=3,
            copies=[{"kind": "runtime", "count": 2, "bytes_per_copy": 8192,
                     "files_per_copy": 2, "directories_per_copy": 1}])
        self.assertEqual(result["required_bytes_estimate"], 4096 + 100 + 2 * 12288)
        self.assertEqual(result["required_inodes_estimate"], 1 + 3 + 2 * 3)

    def test_unknown_inode_capacity_reported(self):
        result = capacity_report(inventory([("file", b"x")]), 1_000_000, None)
        self.assertIsNone(result["inodes_sufficient"])
        self.assertFalse(result["inode_check_known"])


if __name__ == "__main__":
    unittest.main()
