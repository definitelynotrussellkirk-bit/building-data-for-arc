"""Focused preflight regressions; run with python -B -m unittest discover."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import warnings
import zipfile


TOOL = Path(__file__).parents[1] / "workspace/tools/packet_space.py"
packet_space = None
if TOOL.exists():
    spec = importlib.util.spec_from_file_location("packet_space", TOOL)
    packet_space = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packet_space)


def archive(entries):
    data = io.BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(data, "w") as output:
        warnings.simplefilter("ignore", UserWarning)
        for name, payload in entries:
            output.writestr(name, payload)
    return zipfile.ZipFile(data)


class PacketSpaceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(packet_space, "packet_space implementation missing")
        self.fs = SimpleNamespace(f_frsize=4096, f_bavail=100, f_favail=100,
                                  f_ffree=100)

    def test_budget_counts_unique_directories_and_both_resource_limits(self):
        with archive([("a/", b""), ("a/x", b"abc"), ("a/b/y", b"12345")]) as z:
            report, _ = packet_space.assess(z, self.fs, 0.1)
            self.assertEqual((report["declared_bytes"], report["file_count"],
                              report["directory_count"], report["required_inodes"]),
                             (8, 2, 2, 5))
            self.assertEqual(report["required_bytes"], 18023)
            self.assertTrue(report["full_extraction_fits"])
            self.fs.f_favail = 4
            self.assertFalse(packet_space.assess(z, self.fs, 0.1)[0]["full_extraction_fits"])
            self.fs.f_favail, self.fs.f_bavail = 100, 4
            self.assertFalse(packet_space.assess(z, self.fs, 0.1)[0]["full_extraction_fits"])

    def test_unsafe_names_duplicates_links_and_file_directory_collisions(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases = [[(name, b"x")] for name in
                 ("../escape", "/absolute", "C:/drive", "a\\b", "a/../b", "a//b", "a/./b")]
        cases += [[("same", b"x"), ("same", b"y")], [(link, b"target")],
                  [("a", b"x"), ("a/b", b"y")]]
        for entries in cases:
            with self.subTest(entries=entries), archive(entries) as z:
                with self.assertRaises(ValueError):
                    packet_space.assess(z, self.fs, 0.1)

    def test_verification_covers_work_and_outer_entries_and_rejects_changes(self):
        digest = hashlib.sha256(b"abc").hexdigest()
        manifest = {"files": {"x": digest},
                    "layout": {"workspace": "WORK", "entry_files": {"review.py": digest}}}
        base = [("WORK/PACKET-MANIFEST.json", json.dumps(manifest)),
                ("WORK/x", b"abc"), ("review.py", b"abc")]
        with archive(base) as z:
            _, files = packet_space.assess(z, self.fs, 0.1)
            result = packet_space.verify(z, files)
            self.assertTrue(result["archive_bytes_verified"])
            self.assertEqual(result["verified_files"], 2)
        for entries in [base[:2] + [("review.py", b"changed")],
                        base + [("unlisted", b"x")]]:
            with self.subTest(entries=entries), archive(entries) as z:
                _, files = packet_space.assess(z, self.fs, 0.1)
                with self.assertRaises(ValueError):
                    packet_space.verify(z, files)

    def test_cli_statuses_and_json_without_extraction(self):
        with tempfile.TemporaryDirectory(prefix="packet-space-test-") as folder:
            root = Path(folder)
            bad, good = root / "invalid.zip", root / "good.zip"
            bad.write_bytes(b"not a ZIP")
            with zipfile.ZipFile(good, "w") as output:
                output.writestr("would_extract/x", b"y")
            cases = [(bad, [], 3), (root / "missing.zip", [], 2),
                     (good, ["--verify"], 4), (good, ["--margin", "0"], 0),
                     (good, ["--margin", "1e10"], 1)]
            for source, options, expected in cases:
                with self.subTest(source=source, options=options):
                    result = subprocess.run([sys.executable, "-B", str(TOOL),
                                             str(source), folder, "--json", *options],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report["exit_status"], expected)
                    self.assertFalse(report["archive_bytes_verified"])
            self.assertFalse((root / "would_extract").exists())


if __name__ == "__main__":
    unittest.main()
