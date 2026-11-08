"""Synthetic behavioral tests; no current review evidence is changed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name("compress_evidence.py")


class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arc-compression-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.work = self.base / "WORK"
        self.source = self.work / "checks/failures.json"
        self.source.parent.mkdir(parents=True)
        self.raw = b'{"failure": [1,2,3], "text":"exact\\nbytes"}\r\n' * 100
        self.source.write_bytes(self.raw)
        self.archive = self.base / "evidence-raw"
        self.dest = self.base / "restored-WORK"

    def run_tool(self, command, *arguments):
        return subprocess.run([sys.executable, str(TOOL), command, "--work", str(self.work),
                               *arguments], text=True, capture_output=True)

    def compress(self):
        return self.run_tool("compress", "--raw-archive", str(self.archive),
                             "--path", "checks/failures.json")

    def test_byte_exact_restore_and_retained_raw(self):
        result = self.compress()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.source.exists())
        self.assertEqual((self.archive / "checks/failures.json").read_bytes(), self.raw)
        mapping = json.loads((self.work / "checks/COMPRESSION-MAP.json").read_text())
        self.assertEqual(mapping["status"], "complete")
        self.assertEqual(mapping["files"][0]["state"], "complete")
        result = self.run_tool("restore", "--dest", str(self.dest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.dest / "checks/failures.json").read_bytes(), self.raw)

    def test_restore_collision_refusal(self):
        self.assertEqual(self.compress().returncode, 0)
        existing = self.dest / "checks/failures.json"
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b"existing must survive")
        result = self.run_tool("restore", "--dest", str(self.dest))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("collision", result.stderr)
        self.assertEqual(existing.read_bytes(), b"existing must survive")

    def test_compress_collision_keeps_original(self):
        compressed = self.source.with_name(self.source.name + ".gz")
        compressed.write_bytes(b"existing archive")
        result = self.compress()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertEqual(compressed.read_bytes(), b"existing archive")
        self.assertFalse((self.work / "checks/COMPRESSION-MAP.json").exists())

    def test_symlink_escape_is_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "linked.json").write_bytes(self.raw)
        (self.work / "checks/escape").symlink_to(outside, target_is_directory=True)
        result = self.run_tool("compress", "--raw-archive", str(self.archive),
                               "--path", "checks/escape/linked.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Symlink", result.stderr)
        self.assertEqual((outside / "linked.json").read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
