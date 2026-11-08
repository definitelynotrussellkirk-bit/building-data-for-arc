"""Behavior tests for the standalone private packet workspace proposal."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

BASE = Path(__file__).resolve().parent
HELPER = BASE / "packet_tmpfs.py"


class PacketWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HELPER.is_file(), "The requested recovery CLI has not been implemented")
        self.temp = tempfile.TemporaryDirectory(prefix="test-", dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mountpoint = self.root / "mount"
        self.output = self.root / "output"
        self.mountpoint.mkdir()
        self.output.mkdir()
        self.packet = self.root / "packet.zip"

    def archive(self, entries):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.packet, "w") as archive:
                for name, data in entries:
                    archive.writestr(name, data)

    def cli(self, *extra, env=None):
        return subprocess.run([
            sys.executable, str(HELPER), str(self.packet),
            "--mountpoint", str(self.mountpoint), "--output-dir", str(self.output),
            *extra,
        ], text=True, capture_output=True, env=env)

    def module(self):
        spec = importlib.util.spec_from_file_location("packet_tmpfs", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_preflight_counts_implicit_directories_and_payload(self):
        self.archive([("a/b.txt", b"abc"), ("a/c/d.bin", b"12345"), ("empty/", b"")])
        result = self.cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["files"], 2)
        self.assertEqual(plan["directories"], 3)
        self.assertEqual(plan["payload_bytes"], 8)
        self.assertEqual(plan["required_inodes"], 5)
        self.assertGreater(plan["tmpfs_bytes"], 8)
        self.assertGreater(plan["tmpfs_inodes"], 5)
        self.assertEqual(list(self.mountpoint.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])

    def test_rejects_unsafe_member_paths_without_writes(self):
        for name in ("../escape", "/absolute", "a/../../escape", "a\\escape", "C:/escape", "a/./b"):
            with self.subTest(name=name):
                self.archive([(name, b"bad")])
                result = self.cli("--dry-run")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("unsafe", result.stderr.lower())
                self.assertEqual(list(self.mountpoint.iterdir()), [])

    def test_rejects_symlink_and_special_zip_entries(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO):
            entry = zipfile.ZipInfo("link")
            entry.create_system = 3
            entry.external_attr = (kind | 0o600) << 16
            self.archive([(entry, b"target")])
            result = self.cli("--dry-run")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe", result.stderr.lower())

    def test_rejects_duplicate_and_file_parent_entries(self):
        for entries in ([('a', b'1'), ('a', b'2')], [('a/', b''), ('a', b'1')],
                        [('a', b'1'), ('a/b', b'2')], [('a/b', b'2'), ('a', b'1')]):
            self.archive(entries)
            result = self.cli("--dry-run")
            self.assertNotEqual(result.returncode, 0)
            self.assertRegex(result.stderr.lower(), "duplicate|parent|conflict")

    def test_nonempty_mountpoint_preserves_existing_file(self):
        self.archive([("safe", b"data")])
        sentinel = self.mountpoint / "keep.txt"
        sentinel.write_bytes(b"existing user bytes")
        result = self.cli("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty", result.stderr.lower())
        self.assertEqual(sentinel.read_bytes(), b"existing user bytes")

    def test_symlink_mountpoint_is_rejected(self):
        self.archive([("safe", b"data")])
        real = self.root / "real"
        real.mkdir()
        self.mountpoint.rmdir()
        self.mountpoint.symlink_to(real, target_is_directory=True)
        result = self.cli("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())
        self.assertEqual(list(real.iterdir()), [])

    def test_missing_namespace_tools_fail_closed(self):
        self.archive([("safe", b"data")])
        result = self.cli("--dry-run", env={**os.environ, "PATH": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unshare", result.stderr)
        self.assertEqual(list(self.mountpoint.iterdir()), [])

    def test_command_or_explicit_shell_is_required(self):
        self.archive([("safe", b"data")])
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command", result.stderr.lower())
        self.assertEqual(list(self.mountpoint.iterdir()), [])

    def response(self, relative):
        path = self.mountpoint / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("fixture.txt", "synthetic response")
        return path

    def test_exports_only_new_response_zip_bytes(self):
        generated = self.response("WORK/review_response_fixture.zip")
        original = self.response("review_response_original.zip")
        self.response("other.zip")
        expected = generated.read_bytes()
        exported = self.module().export_outputs(self.mountpoint, self.output,
                                                {"review_response_original.zip"})
        self.assertEqual([Path(p).name for p in exported], ["review_response_fixture.zip"])
        self.assertEqual((self.output / generated.name).read_bytes(), expected)
        self.assertTrue(original.exists())
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_export_does_not_overwrite_existing_output(self):
        self.response("review_response_fixture.zip")
        existing = self.output / "review_response_fixture.zip"
        existing.write_bytes(b"keep these bytes")
        with self.assertRaises((ValueError, FileExistsError)):
            self.module().export_outputs(self.mountpoint, self.output, set())
        self.assertEqual(existing.read_bytes(), b"keep these bytes")

    def test_export_rejects_output_symlink(self):
        target = self.root / "target.zip"
        target.write_bytes(b"outside")
        (self.mountpoint / "review_response_link.zip").symlink_to(target)
        with self.assertRaises(ValueError):
            self.module().export_outputs(self.mountpoint, self.output, set())
        self.assertEqual(list(self.output.iterdir()), [])

    def test_no_responses_reports_empty_export(self):
        self.assertEqual(self.module().export_outputs(self.mountpoint, self.output, set()), [])
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
