"""Synthetic exact-assignment recovery fixtures; no puzzle data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

GUARD_PATH = Path(__file__).resolve().parents[1] / 'shared/tools/arc_review_guard.py'
_spec = importlib.util.spec_from_file_location('arc_review_guard', GUARD_PATH)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        self.fresh = self.root / "fresh"
        source = "# Synthetic baseline; not a task implementation.\n"
        self.name = "repo/generators/toy/source.txt"
        self.sha = hashlib.sha256(source.encode()).hexdigest()
        manifest = {"schema": "arcpuzzles-full-packet-v2", "main_ids": ["toy"],
                    "files": {self.name: self.sha}}
        raw_manifest = json.dumps(manifest, sort_keys=True).encode()
        packet_id = hashlib.sha256(raw_manifest).hexdigest()
        seed = bytes(32)
        self.contract = {"packet_id": packet_id, "task_id": "toy", "seed": seed.hex(),
            "assignment_id": "review-"+hashlib.sha256(bytes.fromhex(packet_id)+seed).hexdigest()[:16],
            "baseline_sha256": {self.name: self.sha}}
        for work in (self.work, self.fresh):
            (work / self.name).parent.mkdir(parents=True)
            (work / self.name).write_text(source)
            (work / "PACKET-MANIFEST.json").write_bytes(raw_manifest)
        (self.work / "ASSIGNMENT.json").write_text(json.dumps(self.contract, indent=2)+"\n")
        (self.work / "DUTIES.md").write_text("Synthetic fixture duties.\n")
        self.saved = self.root / "saved"
        guard.checkpoint(self.work, self.saved)
        fs = {"block_size": 4096, "available_bytes": 10**9, "available_inodes": 10**6,
              "filesystem": "ext4", "probed_path": str(self.fresh), "mountpoint": "/"}
        self.fs_patch = patch.object(guard, "filesystem_snapshot", return_value=fs)
        self.memory_patch = patch.object(guard, "memory_snapshot", return_value={"effective_available_bytes": 10**9})
        self.fs_patch.start()
        self.memory_patch.start()
        self.addCleanup(self.fs_patch.stop)
        self.addCleanup(self.memory_patch.stop)

    def test_exact_restore_and_idempotent_repeat(self):
        report = guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertEqual(report["assignment_id"], self.contract["assignment_id"])
        self.assertEqual(report["baseline_files_restored"], 1)
        self.assertEqual((self.fresh/"ASSIGNMENT.json").read_bytes(), (self.work/"ASSIGNMENT.json").read_bytes())
        self.assertEqual(guard.digest_file(self.fresh/".review/baseline"/self.name), self.sha)
        repeated = guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertEqual(repeated["baseline_files_restored"], 0)

    def test_tampered_checkpoint_refused(self):
        (self.saved/"DUTIES.md").write_text("Changed")
        with self.assertRaisesRegex(ValueError, "Checkpoint hash mismatch"):
            guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertFalse((self.fresh/"ASSIGNMENT.json").exists())

    def test_different_packet_refused(self):
        (self.fresh/"PACKET-MANIFEST.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "manifest does not match"):
            guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)

    def test_existing_draw_not_overwritten(self):
        (self.fresh/"ASSIGNMENT.json").write_text("existing draw\n")
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertEqual((self.fresh/"ASSIGNMENT.json").read_text(), "existing draw\n")

    def test_changed_original_source_refused(self):
        (self.fresh/self.name).write_text("changed baseline")
        with self.assertRaisesRegex(ValueError, "Original baseline source mismatch"):
            guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertFalse((self.fresh/"ASSIGNMENT.json").exists())

    def test_symlink_baseline_directory_refused(self):
        outside = self.root/"outside"
        outside.mkdir()
        (self.fresh/".review").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "traverses a symlink"):
            guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_memory_block_precedes_publishing_draw(self):
        with patch.object(guard, "memory_snapshot", return_value={"effective_available_bytes": 0}):
            with self.assertRaisesRegex(ValueError, "insufficient_memory"):
                guard.restore_checkpoint(self.saved, self.fresh, reserve_bytes=100)
        self.assertFalse((self.fresh/"ASSIGNMENT.json").exists())
