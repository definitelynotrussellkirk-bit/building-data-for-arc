"""Synthetic contract tests for safe ARC packet verification and recovery.

Only tiny, newly generated test data is used; no assignment or packet program runs.
Run with: python -B -m unittest -v test_arc_packet_recover
"""

import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arc_packet_recover as recovery

MANIFEST_NAME = "WORK/PACKET-MANIFEST.json"
STATE_NAME = ".arc-packet-recovery.json"
LOCK_NAME = ".arc-packet-recovery.lock"
TEMP_PREFIX = ".arc-recover-"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def manifest_for(members):
    return {
        "schema": "arcpuzzles-full-packet-v2",
        "layout": {
            "workspace": "WORK",
            "entry_files": {
                name: sha256(members[name])
                for name in ("START-HERE.md", "review.py")
            },
        },
        "files": {
            name[len("WORK/"):]: sha256(data)
            for name, data in members.items()
            if name.startswith("WORK/")
        },
    }


class PacketRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="recovery-test-", dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.destination = self.root / "recovered"
        self.members = {
            "START-HERE.md": b"# Synthetic packet fixture\n",
            "review.py": b'raise RuntimeError("Synthetic fixture must never run")\n',
            "WORK/repo/example.txt": b"A small synthetic payload.\n",
            "WORK/assets/chunk.bin": b"\x00\x01\xffsynthetic binary payload\n",
        }
        self.manifest = manifest_for(self.members)
        self.manifest_bytes = canonical_json(self.manifest)

    def write_zip(self, *, name="packet.zip", members=None, manifest=None,
                  raw_manifest=None, extras=(), symlinks=()):
        path = self.root / name
        members = self.members if members is None else members
        manifest = self.manifest if manifest is None else manifest
        manifest_bytes = canonical_json(manifest) if raw_manifest is None else raw_manifest
        entries = list(members.items()) + [(MANIFEST_NAME, manifest_bytes)] + list(extras)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for member_name, data in entries:
                    info = zipfile.ZipInfo(member_name)
                    info.create_system = 3
                    file_type = stat.S_IFLNK if member_name in symlinks else stat.S_IFREG
                    info.external_attr = (file_type | 0o644) << 16
                    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
        return path

    def assert_error_code(self, expected_code, action):
        with self.assertRaises(recovery.RecoveryError) as caught:
            action()
        self.assertEqual(caught.exception.code, expected_code)
        return caught.exception

    def expected_files(self):
        return {**self.members, MANIFEST_NAME: self.manifest_bytes}

    def assert_complete_extraction(self):
        for name, data in self.expected_files().items():
            with self.subTest(member=name):
                self.assertEqual((self.destination / name).read_bytes(), data)
        self.assertTrue((self.destination / STATE_NAME).is_file())
        json.loads((self.destination / STATE_NAME).read_text(encoding="utf-8"))
        allowed = set(self.expected_files()) | {STATE_NAME, LOCK_NAME}
        actual = {
            str(path.relative_to(self.destination))
            for path in self.destination.rglob("*") if path.is_file()
        }
        self.assertTrue(actual <= allowed, actual - allowed)
        self.assert_no_member_temps()

    def assert_no_member_temps(self):
        if self.destination.exists():
            self.assertEqual(
                [str(p) for p in self.destination.rglob("*") if p.name.startswith(TEMP_PREFIX)],
                [],
            )

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(HERE / "arc_packet_recover.py"), *map(str, arguments)],
            cwd=self.root, capture_output=True, text=True, check=False, timeout=30,
        )

    def test_verify_accepts_valid_archive_without_extracting_or_modifying_it(self):
        archive = self.write_zip()
        original = archive.read_bytes()
        result = recovery.verify_archive(archive)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(archive.read_bytes(), original)
        self.assertEqual(set(self.root.iterdir()), {archive})

    def test_verify_handles_payload_spanning_many_read_chunks(self):
        members = {**self.members, "WORK/assets/long.bin": bytes(range(256)) * 8193}
        archive = self.write_zip(members=members, manifest=manifest_for(members))
        self.assertEqual(recovery.verify_archive(archive)["status"], "verified")

    def test_verify_rejects_wrong_sha256_despite_fresh_valid_zip_crc(self):
        changed = {**self.members, "WORK/repo/example.txt": b"Changed synthetic payload.\n"}
        archive = self.write_zip(members=changed)
        with zipfile.ZipFile(archive) as zipped:
            self.assertIsNone(zipped.testzip())
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_unknown_member(self):
        archive = self.write_zip(extras=[("WORK/assets/unknown.txt", b"extra data")])
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_missing_listed_member(self):
        members = dict(self.members)
        del members["WORK/repo/example.txt"]
        archive = self.write_zip(members=members)
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_duplicate_zip_path(self):
        name = "WORK/repo/example.txt"
        archive = self.write_zip(extras=[(name, self.members[name])])
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.namelist().count(name), 2)
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_manifest_listed_traversal(self):
        for unsafe in ("../escaped.txt", "repo/../../escaped.txt", "/absolute.txt", "repo\\escaped.txt"):
            with self.subTest(path=unsafe):
                members = {**self.members, "WORK/" + unsafe: b"unsafe name fixture"}
                archive = self.write_zip(members=members, manifest=manifest_for(members))
                self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))
                self.assert_error_code(
                    "invalid_archive", lambda: recovery.extract_archive(archive, self.destination)
                )
                self.assertFalse(self.destination.exists())
                self.assertFalse((self.root / "escaped.txt").exists())

    def test_verify_rejects_symlink_zip_attributes_even_with_matching_hash(self):
        archive = self.write_zip(symlinks={"WORK/repo/example.txt"})
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_non_zip_input(self):
        archive = self.root / "not-a-zip.bin"
        archive.write_bytes(b"A harmless non-ZIP fixture.\n")
        self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_rejects_noncanonical_manifest_bytes(self):
        variants = (
            self.manifest_bytes + b"\n",
            json.dumps(self.manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        for raw in variants:
            with self.subTest(raw=raw[:40]):
                self.assertEqual(json.loads(raw), self.manifest)
                archive = self.write_zip(raw_manifest=raw)
                self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_verify_requires_exact_entry_file_set(self):
        for entry_files in (
            {"START-HERE.md": sha256(self.members["START-HERE.md"])},
            {**self.manifest["layout"]["entry_files"], "extra.py": sha256(b"extra")},
        ):
            with self.subTest(entries=list(entry_files)):
                manifest = json.loads(self.manifest_bytes)
                manifest["layout"]["entry_files"] = entry_files
                archive = self.write_zip(manifest=manifest)
                self.assert_error_code("invalid_archive", lambda: recovery.verify_archive(archive))

    def test_extract_preserves_exact_existing_file_and_is_repeatable(self):
        archive = self.write_zip()
        exact = self.destination / "WORK/repo/example.txt"
        exact.parent.mkdir(parents=True)
        exact.write_bytes(self.members["WORK/repo/example.txt"])
        stamp = 1_650_000_000_123_456_789
        os.utime(exact, ns=(stamp, stamp))
        original = exact.stat()
        self.assertEqual(recovery.extract_archive(archive, self.destination)["status"], "extracted")
        self.assert_complete_extraction()
        self.assertEqual(recovery.extract_archive(archive, self.destination)["status"], "extracted")
        self.assertEqual(exact.stat().st_ino, original.st_ino)
        self.assertEqual(exact.stat().st_mtime_ns, original.st_mtime_ns)
        self.assert_complete_extraction()

    def test_extract_refuses_to_overwrite_preexisting_different_file(self):
        archive = self.write_zip()
        edited = self.destination / "START-HERE.md"
        edited.parent.mkdir(parents=True)
        edited.write_bytes(b"Reviewer-owned preexisting text.\n")
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, self.destination)
        )
        self.assertEqual(edited.read_bytes(), b"Reviewer-owned preexisting text.\n")
        self.assertFalse((self.destination / "review.py").exists())
        self.assert_no_member_temps()

    def test_resume_refuses_to_overwrite_reviewer_edits(self):
        archive = self.write_zip()
        recovery.extract_archive(archive, self.destination)
        edited = self.destination / "WORK/repo/example.txt"
        edited.write_bytes(b"Reviewer edits must survive.\n")
        original = edited.stat()
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, self.destination)
        )
        self.assertEqual(edited.read_bytes(), b"Reviewer edits must survive.\n")
        self.assertEqual(edited.stat().st_mtime_ns, original.st_mtime_ns)
        self.assert_no_member_temps()

    def test_extract_rejects_symlink_destination_root(self):
        archive = self.write_zip()
        outside = self.root / "outside"
        outside.mkdir()
        self.destination.symlink_to(outside, target_is_directory=True)
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, self.destination)
        )
        self.assertEqual(list(outside.iterdir()), [])

    def test_extract_rejects_symlink_destination_ancestor(self):
        archive = self.write_zip()
        outside = self.root / "outside"
        outside.mkdir()
        linked_parent = self.root / "linked-parent"
        linked_parent.symlink_to(outside, target_is_directory=True)
        destination = linked_parent / "child"
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, destination)
        )
        self.assertEqual(list(outside.iterdir()), [])

    def test_extract_rejects_symlink_directory_inside_destination(self):
        archive = self.write_zip()
        outside = self.root / "outside"
        outside.mkdir()
        (self.destination / "WORK").mkdir(parents=True)
        (self.destination / "WORK/repo").symlink_to(outside, target_is_directory=True)
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, self.destination)
        )
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.destination / "START-HERE.md").exists())

    def test_extract_rejects_symlink_file_even_when_target_contents_match(self):
        archive = self.write_zip()
        outside = self.root / "outside.txt"
        outside.write_bytes(self.members["START-HERE.md"])
        self.destination.mkdir()
        (self.destination / "START-HERE.md").symlink_to(outside)
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(archive, self.destination)
        )
        self.assertEqual(outside.read_bytes(), self.members["START-HERE.md"])
        self.assertTrue((self.destination / "START-HERE.md").is_symlink())

    def test_resume_rejects_different_archive_bytes_with_identical_members(self):
        first = self.write_zip(name="first.zip")
        second = self.write_zip(name="second.zip")
        with zipfile.ZipFile(second, "a") as zipped:
            zipped.comment = b"A different synthetic archive identity"
        self.assertNotEqual(sha256(first.read_bytes()), sha256(second.read_bytes()))
        self.assertEqual(recovery.verify_archive(second)["status"], "verified")
        recovery.extract_archive(first, self.destination)
        state_before = (self.destination / STATE_NAME).read_bytes()
        self.assert_error_code(
            "destination_conflict", lambda: recovery.extract_archive(second, self.destination)
        )
        self.assertEqual((self.destination / STATE_NAME).read_bytes(), state_before)
        self.assert_complete_extraction()

    def test_disk_full_keeps_completed_files_cleans_partial_and_resumes(self):
        archive = self.write_zip()
        original_copy = recovery._copy_stream
        calls = 0
        interrupted_name = None

        def fail_second_copy(source, destination):
            nonlocal calls, interrupted_name
            calls += 1
            if calls == 2:
                interrupted_name = source.name
                destination.write(source.read(4))
                raise OSError(errno.ENOSPC, "Injected disk full for synthetic test")
            return original_copy(source, destination)

        with mock.patch.object(recovery, "_copy_stream", side_effect=fail_second_copy):
            self.assert_error_code(
                "io_error", lambda: recovery.extract_archive(archive, self.destination)
            )
        self.assertIsNotNone(interrupted_name)
        self.assertFalse((self.destination / interrupted_name).exists())
        completed = {}
        for name, data in self.expected_files().items():
            path = self.destination / name
            if path.is_file():
                self.assertEqual(path.read_bytes(), data)
                completed[name] = (path.stat().st_ino, path.stat().st_mtime_ns)
        self.assertGreaterEqual(len(completed), 1)
        self.assertLess(len(completed), len(self.expected_files()))
        self.assert_no_member_temps()
        self.assertEqual(recovery.extract_archive(archive, self.destination)["status"], "extracted")
        self.assert_complete_extraction()
        for name, before in completed.items():
            after = (self.destination / name).stat()
            self.assertEqual((after.st_ino, after.st_mtime_ns), before)

    def test_cli_verify_and_extract_write_matching_json_reports(self):
        archive = self.write_zip()
        for command, positionals, status in (
            ("verify", [archive], "verified"),
            ("extract", [archive, self.destination], "extracted"),
        ):
            with self.subTest(command=command):
                report = self.root / (command + "-report.json")
                result = self.cli(command, *positionals, "--report", report)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["status"], status)
                self.assertEqual(json.loads(report.read_text(encoding="utf-8")), payload)
        self.assert_complete_extraction()

    def test_cli_distinguishes_invalid_archive_io_error_and_destination_conflict(self):
        archive = self.write_zip()
        invalid = self.root / "invalid.zip"
        invalid.write_bytes(b"Not a ZIP archive")
        self.destination.mkdir()
        (self.destination / "START-HERE.md").write_bytes(b"Existing reviewer text")
        cases = (
            (["verify", invalid], 1),
            (["verify", self.root / "does-not-exist.zip"], 2),
            (["extract", archive, self.destination], 3),
        )
        for arguments, expected_exit in cases:
            with self.subTest(arguments=arguments):
                result = self.cli(*arguments)
                self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)
        self.assertEqual(
            (self.destination / "START-HERE.md").read_bytes(), b"Existing reviewer text"
        )


if __name__ == "__main__":
    unittest.main()
