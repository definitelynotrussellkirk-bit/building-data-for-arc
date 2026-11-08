"""Small, synthetic fixtures; no real review assignment is drawn or repaired."""

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

import checkpoint_workspace as checkpoint


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="checkpoint-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "WORK"
        self.work.mkdir()
        self.source = self.root / "source.zip"
        self.output = self.root / "checkpoint.zip"
        self.original = {"a.txt": b"original a\n", "b.txt": b"original b\n"}
        manifest = json.dumps({"files": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in self.original.items()
        }}).encode()
        with zipfile.ZipFile(self.source, "w") as archive:
            for name, data in self.original.items():
                archive.writestr("WORK/" + name, data)
                (self.work / name).write_bytes(data)
            archive.writestr("WORK/PACKET-MANIFEST.json", manifest)
            archive.writestr("review.py", b"# synthetic controller\n")
        (self.work / "PACKET-MANIFEST.json").write_bytes(manifest)

    def create(self, **kwargs):
        return checkpoint.create_checkpoint(self.work, self.source, self.output, **kwargs)

    def rewrite_checkpoint(self, transform):
        with zipfile.ZipFile(self.output) as archive:
            entries = [(item.filename, archive.read(item)) for item in archive.infolist()]
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in transform(entries):
                archive.writestr(name, data)
        self.output.write_bytes(buffer.getvalue())

    def test_round_trip_retains_assignment_frozen_baseline_and_deletions(self):
        (self.work / "a.txt").write_bytes(b"edited a\n")
        (self.work / "b.txt").unlink()
        assignment = b'{"fixture_only":true,"seed":"unchanged bytes"}\n'
        (self.work / "ASSIGNMENT.json").write_bytes(assignment)
        frozen = self.work / ".review" / "baseline"
        frozen.mkdir(parents=True)
        (frozen / "a.txt").write_bytes(self.original["a.txt"])
        metadata = self.create()
        self.assertEqual(metadata["deleted"], ["b.txt"])
        with zipfile.ZipFile(self.output) as archive:
            self.assertNotIn("files/PACKET-MANIFEST.json", archive.namelist())
            self.assertEqual(archive.read("files/ASSIGNMENT.json"), assignment)
        destination = self.root / "restored"
        checkpoint.restore_checkpoint(self.output, self.source, destination)
        self.assertEqual((destination / "a.txt").read_bytes(), b"edited a\n")
        self.assertFalse((destination / "b.txt").exists())
        self.assertEqual((destination / "ASSIGNMENT.json").read_bytes(), assignment)
        self.assertEqual((destination / ".review/baseline/a.txt").read_bytes(),
                         self.original["a.txt"])
        self.assertEqual((destination / "PACKET-MANIFEST.json").read_bytes(),
                         (self.work / "PACKET-MANIFEST.json").read_bytes())

    def test_existing_checkpoint_is_not_overwritten_without_replace(self):
        self.create()
        before = self.output.read_bytes()
        with self.assertRaises((checkpoint.CheckpointError, FileExistsError)):
            self.create()
        self.assertEqual(self.output.read_bytes(), before)

    def test_failed_replacement_preserves_previous_checkpoint_and_cleans_temp(self):
        self.create()
        before = self.output.read_bytes()
        (self.work / "a.txt").write_bytes(b"changed")
        with mock.patch.object(checkpoint, "_copy_stream", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.create(replace=True)
        self.assertEqual(self.output.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),
                         ["WORK", "checkpoint.zip", "source.zip"])

    def test_capture_rejects_workspace_mutation(self):
        (self.work / "a.txt").write_bytes(b"changed before capture")
        copy_stream = checkpoint._copy_stream
        mutated = False

        def mutate_after_copy(reader, writer=None):
            nonlocal mutated
            result = copy_stream(reader, writer)
            if writer is not None and not mutated:
                (self.work / "a.txt").write_bytes(b"changed during capture")
                mutated = True
            return result

        with mock.patch.object(checkpoint, "_copy_stream", side_effect=mutate_after_copy):
            with self.assertRaises(checkpoint.CheckpointError):
                self.create()
        self.assertFalse(self.output.exists())

    def test_exclusions_are_narrow_and_evidence_zips_are_retained(self):
        for name in [".review/racket-runtime/runtime", "tmp/scratch"]:
            target = self.work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"regenerable")
        (self.work / "review_response_fixture.zip").write_bytes(b"generated return")
        (self.work / "evidence.zip").write_bytes(b"authored evidence")
        metadata = self.create()
        self.assertIn("evidence.zip", metadata["files"])
        self.assertFalse(any("racket-runtime" in name for name in metadata["files"]))
        self.assertNotIn("tmp/scratch", metadata["files"])
        self.assertNotIn("review_response_fixture.zip", metadata["files"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_workspace_symlink_is_rejected(self):
        (self.work / "alias").symlink_to("a.txt")
        with self.assertRaises(checkpoint.CheckpointError):
            self.create()
        self.assertFalse(self.output.exists())

    def test_wrong_source_is_rejected_before_restore_writes(self):
        self.create()
        with zipfile.ZipFile(self.source, "a") as archive:
            archive.writestr("different.txt", b"different source")
        destination = self.root / "restored"
        with self.assertRaises(checkpoint.CheckpointError):
            checkpoint.restore_checkpoint(self.output, self.source, destination)
        self.assertFalse(destination.exists())

    def test_corrupt_payload_is_rejected_before_restore_writes(self):
        (self.work / "a.txt").write_bytes(b"changed")
        self.create()
        self.rewrite_checkpoint(lambda entries: [
            (name, b"corruption" if name == "files/a.txt" else data)
            for name, data in entries
        ])
        destination = self.root / "restored"
        with self.assertRaises(checkpoint.CheckpointError):
            checkpoint.restore_checkpoint(self.output, self.source, destination)
        self.assertFalse(destination.exists())

    def test_unsafe_and_duplicate_archive_members_are_rejected(self):
        self.create()
        good_bytes = self.output.read_bytes()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for name in ["../escape", "/absolute", "files/../escape", "files\\escape",
                         "CHECKPOINT.json"]:
                with self.subTest(name=name):
                    self.output.write_bytes(good_bytes)
                    self.rewrite_checkpoint(lambda entries: entries + [(name, b"unsafe")])
                    with self.assertRaises(checkpoint.CheckpointError):
                        checkpoint.verify_checkpoint(self.output, self.source)

    def test_restore_never_overwrites_nonempty_destination(self):
        self.create()
        before = (self.work / "a.txt").read_bytes()
        with self.assertRaises(checkpoint.CheckpointError):
            checkpoint.restore_checkpoint(self.output, self.source, self.work)
        self.assertEqual((self.work / "a.txt").read_bytes(), before)

    def test_run_checkpoints_before_returning_original_nonzero_exit(self):
        command = [sys.executable, "-c",
                   "from pathlib import Path; import sys; "
                   "Path('ASSIGNMENT.json').write_bytes(b'fixture assignment'); sys.exit(7)"]
        result = checkpoint.run_checkpoint(self.work, self.source, self.output, command)
        self.assertEqual(result, 7)
        metadata = checkpoint.verify_checkpoint(self.output, self.source)
        self.assertIn("ASSIGNMENT.json", metadata["files"])

    def test_run_reports_checkpoint_failure_and_preserves_command_error(self):
        for command_status, expected in [(0, 1), (7, 7)]:
            with self.subTest(status=command_status), \
                    mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], command_status)), \
                    mock.patch.object(checkpoint, "create_checkpoint", side_effect=OSError("disk full")), \
                    mock.patch("sys.stderr", new_callable=io.StringIO) as errors:
                result = checkpoint.run_checkpoint(self.work, self.source, self.output,
                                                   ["synthetic-command"])
            self.assertEqual(result, expected)
            self.assertIn("checkpoint failed", errors.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
