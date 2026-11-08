"""Fast, synthetic-only tests. No issued packet files are opened."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "start_capacity.py"
CANONICAL = "repo/shared/data/canonical/puzzles.jsonl"
LOCAL = "repo/generators/synthetic/generator.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()


class StartCapacityTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "startup helper is not implemented")
        spec = importlib.util.spec_from_file_location("start_capacity", SCRIPT)
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-", dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / "WORK"
        self.work.mkdir()
        self.payloads = {CANONICAL: b"synthetic data only\n" * 300,
                         LOCAL: b"synthetic fixture only\n"}
        for name, raw in self.payloads.items():
            path = self.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.manifest = {"schema": "arcpuzzles-full-packet-v2",
                         "files": {name: sha(raw) for name, raw in self.payloads.items()}}
        self.manifest_raw = canonical(self.manifest)
        (self.work / "PACKET-MANIFEST.json").write_bytes(self.manifest_raw)
        packet_id = sha(self.manifest_raw)
        seed = "12" * 32
        self.contract = {"schema": "arcpuzzles-full-assignment-v2",
                         "packet_id": packet_id, "seed": seed,
                         "assignment_id": "review-" + sha(bytes.fromhex(packet_id) + bytes.fromhex(seed))[:16],
                         "baseline_sha256": self.manifest["files"],
                         "task_id": "DO_NOT_PRINT_SYNTHETIC_TASK"}
        self.fs = {"filesystem": "ext4", "block_size": 4096,
                   "available_bytes": 10**9, "available_inodes": 10**6,
                   "free_bytes_including_reserved": 10**9}
        self.memory = {"effective_available_bytes": 10**9,
                       "host_available_bytes": 10**9, "cgroup_v2": []}

    def pending(self, *, assigned=False):
        review = self.work / ".review"
        review.mkdir(exist_ok=True)
        (review / "main-draw.lock").touch()
        raw = (json.dumps({"schema": "arcpuzzles-pending-main-draw-v1",
                           "contract": self.contract}, indent=2) + "\r\n").encode()
        (review / "pending-main-draw.json").write_bytes(raw)
        if assigned:
            (self.work / "ASSIGNMENT.json").write_bytes(canonical(self.contract))
        return raw

    def report(self, **options):
        with mock.patch.object(self.helper, "filesystem_snapshot", return_value=self.fs), \
             mock.patch.object(self.helper, "memory_snapshot", return_value=self.memory):
            return self.helper.report(self.work, reserve_bytes=0, reserve_inodes=0, **options)

    def test_pending_report_does_not_read_baseline_source_contents(self):
        self.pending()
        real_open = os.open
        original = Path.open

        def guarded_os_open(path, *args, **kwargs):
            candidate = Path(path).absolute()
            self.assertFalse(self.work / "repo" in candidate.parents,
                             "report opened a semantic source")
            self.assertFalse(self.work / ".review/baseline" in candidate.parents,
                             "report opened a baseline source")
            return real_open(path, *args, **kwargs)

        def guarded_path_open(path, *args, **kwargs):
            candidate = Path(path).absolute()
            self.assertFalse(self.work / "repo" in candidate.parents,
                             "report opened a semantic source")
            self.assertFalse(self.work / ".review/baseline" in candidate.parents,
                             "report opened a baseline source")
            return original(path, *args, **kwargs)

        with mock.patch("os.open", side_effect=guarded_os_open), \
             mock.patch.object(Path, "open", guarded_path_open):
            value = self.report()
        self.assertEqual(value["draw_state"], "pending_only")
        self.assertEqual(value["estimate"]["missing_baseline_bytes"], 12288)
        self.assertEqual(value["estimate"]["copy_bytes_upper_bound"], 12288)
        emitted = json.dumps(value)
        self.assertNotIn(self.contract["seed"], emitted)
        self.assertNotIn(self.contract["task_id"], emitted)
        self.assertNotIn(LOCAL, emitted)

    def test_existing_same_size_bad_baseline_remains_in_upper_bound(self):
        self.pending()
        target = self.work / ".review/baseline" / CANONICAL
        target.parent.mkdir(parents=True)
        target.write_bytes(b"X" * len(self.payloads[CANONICAL]))
        value = self.report()
        self.assertEqual(value["estimate"]["missing_baseline_bytes"], 4096)
        self.assertEqual(value["estimate"]["copy_bytes_upper_bound"], 12288)
        self.assertEqual(value["estimate"]["existing_unverified_files"], 1)

    def test_completed_assignment_means_idempotent_start_not_review_complete(self):
        (self.work / "ASSIGNMENT.json").write_bytes(canonical(self.contract))
        value = self.report()
        self.assertEqual(value["draw_state"], "completed")
        self.assertEqual(value["estimate"]["copy_bytes_upper_bound"], 0)
        self.assertFalse(value["review_completion_assessed"])

    def test_pending_with_matching_assignment_is_unfinished_finalization(self):
        self.pending(assigned=True)
        self.assertEqual(self.report()["draw_state"], "pending_finalization")

    def test_conflicting_assignment_and_pending_are_rejected(self):
        self.pending(assigned=True)
        bad = dict(self.contract, task_id="conflicting")
        (self.work / "ASSIGNMENT.json").write_bytes(canonical(bad))
        with self.assertRaisesRegex(self.helper.GuardError, "conflicting_assignment"):
            self.report()

    def test_unstarted_uses_selection_free_repository_upper_bound(self):
        value = self.report()
        self.assertEqual(value["draw_state"], "unstarted")
        self.assertEqual(value["estimate"]["scope"], "all_manifest_repo_files_selection_unknown")
        self.assertEqual(value["estimate"]["copy_bytes_upper_bound"], 12288)

    def test_unjournaled_baseline_is_rejected_without_mutation(self):
        target = self.work / ".review/baseline/orphan"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"orphan")
        with self.assertRaisesRegex(self.helper.GuardError, "unjournaled_baseline"):
            self.report()
        self.assertEqual(target.read_bytes(), b"orphan")

    def test_disk_and_inode_exhaustion_are_distinct(self):
        self.pending()
        self.fs.update(available_bytes=0, available_inodes=0)
        value = self.report()
        self.assertEqual(value["status"], "blocked")
        self.assertIn("insufficient_disk_bytes", value["failures"])
        self.assertIn("insufficient_inodes", value["failures"])

    def test_tmpfs_capacity_also_checks_memory(self):
        self.pending()
        self.fs["filesystem"] = "tmpfs"
        self.memory["effective_available_bytes"] = 16000
        value = self.report()
        self.assertEqual(value["status"], "blocked")
        self.assertIn("insufficient_memory_headroom", value["failures"])
        self.assertGreater(value["requirements"]["available_memory_bytes"], 16000)

    def test_unknown_memory_does_not_report_ready(self):
        self.pending()
        self.memory["effective_available_bytes"] = None
        value = self.report()
        self.assertEqual(value["status"], "indeterminate")
        self.assertIn("memory_headroom_unknown", value["warnings"])

    def test_symlink_marker_is_rejected(self):
        self.pending()
        marker = self.work / ".review/pending-main-draw.json"
        other = self.root / "journal"
        marker.rename(other)
        marker.symlink_to(other)
        with self.assertRaisesRegex(self.helper.GuardError, "symlink"):
            self.report()

    def test_source_symlink_is_rejected_without_following(self):
        self.pending()
        path = self.work / LOCAL
        path.unlink()
        path.symlink_to(self.root / "not_a_source")
        with self.assertRaisesRegex(self.helper.GuardError, "symlink"):
            self.report()

    def test_unsafe_baseline_name_is_rejected(self):
        self.contract["baseline_sha256"] = {"repo/../../outside": "f" * 64}
        self.pending()
        with self.assertRaisesRegex(self.helper.GuardError, "unsafe_baseline_path"):
            self.report()

    def test_sparse_source_uses_logical_size(self):
        self.pending()
        with (self.work / CANONICAL).open("wb") as stream:
            stream.truncate(1024 * 1024)
        value = self.report()
        self.assertEqual(value["estimate"]["copy_bytes_upper_bound"], 1024 * 1024 + 4096)

    def test_visible_ancestor_cgroup_can_be_tighter_than_leaf(self):
        cgroup = self.root / "cgroup"
        leaf = cgroup / "a/b"
        leaf.mkdir(parents=True)
        for group, maximum, current in ((cgroup, 10000, 9000),
                                        (cgroup / "a", "max", 4000),
                                        (leaf, 8000, 3000)):
            (group / "memory.max").write_text(str(maximum))
            (group / "memory.current").write_text(str(current))
        meminfo = self.root / "meminfo"
        meminfo.write_text("MemAvailable: 100 kB\n")
        membership = self.root / "membership"
        membership.write_text("0::/a/b\n")
        value = self.helper.memory_snapshot(cgroup, meminfo, membership)
        self.assertEqual(value["effective_available_bytes"], 1000)
        self.assertEqual(len(value["cgroup_v2"]), 3)

    def test_malformed_cgroup_is_reported_as_unknown(self):
        cgroup = self.root / "cgroup"
        cgroup.mkdir()
        (cgroup / "memory.max").write_text("not-a-limit")
        (cgroup / "memory.current").write_text("30")
        value = self.helper.memory_snapshot(cgroup, self.root / "absent", self.root / "absent")
        self.assertIsNone(value["effective_available_bytes"])
        self.assertTrue(value["warnings"])

    def test_unreadable_cgroup_cannot_be_overridden_by_large_host_memory(self):
        self.pending()
        cgroup = self.root / "cgroup"
        cgroup.mkdir()
        (cgroup / "memory.max").write_text("not-a-limit")
        (cgroup / "memory.current").write_text("30")
        meminfo = self.root / "meminfo"
        meminfo.write_text("MemAvailable: 100000 kB\n")
        self.memory = self.helper.memory_snapshot(cgroup, meminfo, self.root / "absent")
        self.assertEqual(self.report()["status"], "indeterminate")
        self.assertFalse(self.memory["cgroup_v2_complete"])

    def test_unreadable_membership_cannot_claim_complete_cgroup_measurement(self):
        self.pending()
        cgroup = self.root / "cgroup"
        cgroup.mkdir()
        (cgroup / "memory.max").write_text("max")
        (cgroup / "memory.current").write_text("30")
        meminfo = self.root / "meminfo"
        meminfo.write_text("MemAvailable: 100000 kB\n")
        self.memory = self.helper.memory_snapshot(cgroup, meminfo, self.root / "absent")
        self.assertEqual(self.report()["status"], "indeterminate")
        self.assertFalse(self.memory["cgroup_v2_complete"])

    def test_filesystem_capacity_uses_caller_available_not_reserved_blocks(self):
        values = SimpleNamespace(f_frsize=4096, f_bsize=8192, f_bavail=3,
                                 f_bfree=9, f_files=100, f_favail=0)
        with mock.patch("os.statvfs", return_value=values):
            value = self.helper.filesystem_snapshot(self.work)
        self.assertEqual(value["available_bytes"], 3 * 4096)
        self.assertEqual(value["free_bytes_including_reserved"], 9 * 4096)
        self.assertEqual(value["available_inodes"], 0)

    def test_filesystem_without_inode_accounting_is_explicitly_unknown(self):
        values = SimpleNamespace(f_frsize=0, f_bsize=8192, f_bavail=3,
                                 f_bfree=9, f_files=0, f_favail=0)
        with mock.patch("os.statvfs", return_value=values):
            value = self.helper.filesystem_snapshot(self.work)
        self.assertEqual(value["block_size"], 8192)
        self.assertIsNone(value["available_inodes"])

    def test_checkpoint_preserves_exact_bytes_and_verifies_hashes(self):
        raw = self.pending(assigned=True)
        destination = self.root / "saved"
        result = self.helper.checkpoint_pending(self.work, destination)
        self.assertEqual(result["status"], "checkpointed")
        self.assertEqual((destination / "pending-main-draw.json").read_bytes(), raw)
        self.assertEqual((destination / "PACKET-MANIFEST.json").read_bytes(), self.manifest_raw)
        checked = self.helper.verify_checkpoint(destination)
        self.assertEqual(checked["status"], "verified")
        self.assertEqual(checked["packet_manifest_sha256"], sha(self.manifest_raw))
        self.assertNotIn(self.contract["seed"], json.dumps(result))

    def test_checkpoint_tampering_is_detected(self):
        self.pending()
        destination = self.root / "saved"
        self.helper.checkpoint_pending(self.work, destination)
        with (destination / "pending-main-draw.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(self.helper.GuardError, "checkpoint_hash_mismatch"):
            self.helper.verify_checkpoint(destination)

    def test_checkpoint_cannot_be_created_inside_work_or_through_alias(self):
        self.pending()
        alias = self.root / "alias"
        alias.symlink_to(self.work, target_is_directory=True)
        for destination in (self.work / "saved", alias / "saved"):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(self.helper.GuardError, "checkpoint_destination_inside_work"):
                    self.helper.checkpoint_pending(self.work, destination)

    def test_checkpoint_does_not_overwrite_existing_destination(self):
        self.pending()
        destination = self.root / "saved"
        destination.mkdir()
        (destination / "keep").write_bytes(b"existing")
        with self.assertRaisesRegex(self.helper.GuardError, "checkpoint_destination_exists"):
            self.helper.checkpoint_pending(self.work, destination)
        self.assertEqual((destination / "keep").read_bytes(), b"existing")

    def test_checkpoint_accepts_sibling_with_work_name_prefix(self):
        self.pending()
        self.assertEqual(self.helper.checkpoint_pending(self.work, self.root / "WORK2")["status"], "checkpointed")

    def test_checkpoint_requires_pending_state(self):
        (self.work / "ASSIGNMENT.json").write_bytes(canonical(self.contract))
        with self.assertRaisesRegex(self.helper.GuardError, "pending_journal_required"):
            self.helper.checkpoint_pending(self.work, self.root / "saved")

    def test_checkpoint_rejects_active_official_draw(self):
        self.pending()
        try:
            import fcntl
        except ImportError:
            self.skipTest("POSIX advisory locks unavailable")
        with (self.work / ".review/main-draw.lock").open("rb") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(self.helper.GuardError, "draw_in_progress"):
                self.helper.checkpoint_pending(self.work, self.root / "saved")

    def test_failed_checkpoint_write_never_publishes_success_receipt(self):
        self.pending()
        destination = self.root / "saved"
        real = self.helper.write_exclusive

        def fail_second(path, raw):
            if Path(path).name == "pending-main-draw.json":
                raise OSError(28, "synthetic ENOSPC")
            return real(path, raw)

        with mock.patch.object(self.helper, "write_exclusive", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.helper.checkpoint_pending(self.work, destination)
        self.assertFalse((destination / "CHECKPOINT.json").exists())
        self.assertTrue((self.work / ".review/pending-main-draw.json").is_file())

    def test_source_change_during_checkpoint_never_publishes_success_receipt(self):
        raw = self.pending()
        destination = self.root / "saved"
        real = self.helper.write_exclusive

        def mutate_source(path, contents):
            real(path, contents)
            if Path(path).name == "pending-main-draw.json":
                (self.work / ".review/pending-main-draw.json").write_bytes(raw + b" ")

        with mock.patch.object(self.helper, "write_exclusive", side_effect=mutate_source):
            with self.assertRaisesRegex(self.helper.GuardError, "metadata_changed_during_checkpoint"):
                self.helper.checkpoint_pending(self.work, destination)
        self.assertFalse((destination / "CHECKPOINT.json").exists())

    def test_checkpoint_refuses_missing_lock_without_creating_one(self):
        self.pending()
        path = self.work / ".review/main-draw.lock"
        path.unlink()
        with self.assertRaisesRegex(self.helper.GuardError, "existing_posix_draw_lock_required"):
            self.helper.checkpoint_pending(self.work, self.root / "saved")
        self.assertFalse(path.exists())

    def test_final_checkpoint_verification_failure_withdraws_success_receipt(self):
        self.pending()
        destination = self.root / "saved"
        with mock.patch.object(self.helper, "verify_checkpoint", side_effect=self.helper.GuardError("synthetic_final_failure")):
            with self.assertRaisesRegex(self.helper.GuardError, "synthetic_final_failure"):
                self.helper.checkpoint_pending(self.work, destination)
        self.assertFalse((destination / "CHECKPOINT.json").exists())
        self.assertTrue((destination / "pending-main-draw.json").exists())

    def test_checkpoint_syncs_new_directory_parent(self):
        self.pending()
        destination = self.root / "saved"
        calls = []
        real = self.helper.sync_directory

        def capture_sync(path):
            calls.append(Path(path))
            return real(path)

        with mock.patch.object(self.helper, "sync_directory", side_effect=capture_sync):
            receipt = self.helper.checkpoint_pending(self.work, destination)
        self.assertIn(destination.parent, calls)
        self.assertIn("parent_directory_fsync_supported", receipt)

    def test_cli_emits_json_without_semantic_identifiers(self):
        self.pending()
        result = subprocess.run([sys.executable, str(SCRIPT), "report", "--work", str(self.work),
                                 "--reserve-mib", "0", "--reserve-inodes", "0"],
                                text=True, capture_output=True, check=False)
        self.assertIn(result.returncode, (0, 2))
        value = json.loads(result.stdout)
        self.assertEqual(value["draw_state"], "pending_only")
        self.assertNotIn(self.contract["seed"], result.stdout + result.stderr)
        self.assertNotIn(self.contract["task_id"], result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
