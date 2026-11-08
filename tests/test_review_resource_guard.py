"""Small, offline regression tests using only synthetic packets and records."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

import importlib.util
import sys
GUARD_PATH = Path(__file__).resolve().parents[1] / 'shared/tools/arc_review_guard.py'
_spec = importlib.util.spec_from_file_location('arc_review_guard', GUARD_PATH)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)



GOOD_MEMORY = {
    "cgroup_v2": [{"path": "/synthetic-cgroup", "events": {"oom": 0, "oom_kill": 0}}],
    "host_available_bytes": 8 * 1024**3,
    "effective_available_bytes": 8 * 1024**3,
}
GOOD_FS = {
    "filesystem": "tmpfs", "mountpoint": "/dev/shm", "probed_path": "/dev/shm",
    "block_size": 4096, "available_bytes": 8 * 1024**3,
    "available_inodes": 100000,
}


class GuardCase(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix="arc_guard_test_")
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)

    def make_zip(self, members, name="toy.zip"):
        path = self.root / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
                for member, raw in members:
                    archive.writestr(member, raw)
        return path

    def packet(self, members=None, name="toy.zip"):
        members = members if members is not None else [("nested/note.txt", b"synthetic content\n")]
        manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {
            member: hashlib.sha256(raw).hexdigest() for member, raw in members
        }}
        raw = json.dumps(manifest, sort_keys=True).encode()
        return self.make_zip(members + [("PACKET-MANIFEST.json", raw)], name), raw

    def work_records(self):
        work = self.root / "work"
        work.mkdir()
        manifest = b'{"schema":"synthetic-packet"}\n'
        (work / "PACKET-MANIFEST.json").write_bytes(manifest)
        assignment = {"assignment_id": "synthetic-assignment", "task_id": "synthetic-task",
                      "packet_id": hashlib.sha256(manifest).hexdigest()}
        (work / "ASSIGNMENT.json").write_bytes(json.dumps(assignment, indent=3).encode() + b"\r\n")
        (work / "DUTIES.md").write_bytes(b"Synthetic duties.\r\nPreserve exact bytes.\r\n")
        (work / "RESULTS.json").write_bytes(b'{"status":"not_started"}\n')
        return work

    def ready_resources(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(guard, "memory_snapshot", return_value=copy.deepcopy(GOOD_MEMORY)))
        stack.enter_context(mock.patch.object(guard, "filesystem_snapshot", return_value=copy.deepcopy(GOOD_FS)))
        return stack


class ResourceTests(GuardCase):
    def decision(self, **changes):
        inventory = {"allocation_estimate_bytes": 8192, "inode_estimate": 4}
        filesystem = {"filesystem": "ext4", "available_bytes": 12288, "available_inodes": 7}
        memory = {"effective_available_bytes": 4096}
        filesystem.update(changes.pop("filesystem", {}))
        memory.update(changes.pop("memory", {}))
        return guard.resource_decision(inventory, filesystem, memory, 4096, 3)

    def test_exact_capacity_is_ready(self):
        result = self.decision()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["required_available_disk_bytes"], 12288)
        self.assertEqual(result["required_available_inodes"], 7)

    def test_disk_inode_and_memory_shortages_are_independent(self):
        for fields, expected in [
            ({"filesystem": {"available_bytes": 12287}}, "insufficient_disk_bytes"),
            ({"filesystem": {"available_inodes": 6}}, "insufficient_inodes"),
            ({"memory": {"effective_available_bytes": 4095}}, "insufficient_memory_headroom"),
        ]:
            with self.subTest(expected=expected):
                result = self.decision(**fields)
                self.assertEqual(result["failures"], [expected])

    def test_tmpfs_requires_extraction_bytes_in_memory(self):
        result = self.decision(filesystem={"filesystem": "tmpfs"})
        self.assertEqual(result["required_available_memory_bytes"], 12288)
        self.assertIn("insufficient_memory_headroom", result["failures"])

    def test_unknown_memory_blocks_tmpfs_but_warns_for_disk(self):
        for fs, status in [("tmpfs", "blocked"), ("ext4", "ready")]:
            with self.subTest(fs=fs):
                result = self.decision(filesystem={"filesystem": fs},
                                       memory={"effective_available_bytes": None})
                self.assertEqual(result["status"], status)
                self.assertIn("memory_headroom_unknown", result["failures"] + result["warnings"])

    def test_unknown_inodes_are_explicit(self):
        self.assertIn("inode_availability_unknown", self.decision(
            filesystem={"available_inodes": None})["warnings"])

    def test_mount_match_uses_component_boundary_and_unescapes_spaces(self):
        mounts = "10 0 0:1 / / rw - overlay overlay rw\n"
        mounts += "11 10 0:2 / /dev rw - tmpfs tmpfs rw\n"
        mounts += "12 10 0:3 / /some\\040space rw - ext4 /dev/a rw\n"
        self.assertEqual(guard.mount_for("/device/file", mounts)["mountpoint"], "/")
        self.assertEqual(guard.mount_for("/some space/file", mounts)["mountpoint"], "/some space")

    def test_memory_limit_is_tighter_than_host_memory(self):
        group = self.root / "cgroup"
        group.mkdir()
        (group / "memory.max").write_text("10000")
        (group / "memory.high").write_text("8000")
        (group / "memory.current").write_text("7500")
        (group / "memory.events").write_text("oom 2\noom_kill 1\n")
        result = guard.memory_snapshot(group, "MemAvailable: 40000 kB\n")
        self.assertEqual(result["effective_available_bytes"], 2500)
        self.assertEqual(result["cgroup_v2"][0]["high_bytes"], 8000)
        self.assertEqual(result["cgroup_v2"][0]["events"]["oom_kill"], 1)


class ArchiveTests(GuardCase):
    def test_reject_unsafe_paths(self):
        for name in ["../x", "/x", "a/../x", "a\\x", "C:/x", "C:x", "a//b", "./x", "a/./b", "a\x00b"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    guard.member_path(zipfile.ZipInfo(name))

    def test_special_and_conflicting_metadata_is_rejected(self):
        for name, kind in [("link", stat.S_IFLNK), ("fifo", stat.S_IFIFO),
                           ("directory", stat.S_IFDIR), ("file/", stat.S_IFREG)]:
            info = zipfile.ZipInfo(name)
            info.external_attr = (kind | 0o600) << 16
            with self.subTest(name=name), self.assertRaises(ValueError):
                guard.member_path(info)

    def test_permission_bits_without_type_are_accepted(self):
        info = zipfile.ZipInfo("ordinary.txt")
        info.external_attr = 0o600 << 16
        self.assertEqual(str(guard.member_path(info)), "ordinary.txt")

    def test_encryption_and_unknown_compression_rejected(self):
        info = zipfile.ZipInfo("a")
        info.flag_bits = 1
        with self.assertRaises(ValueError):
            guard.member_path(info)
        info.flag_bits, info.compress_type = 0, 65535
        with self.assertRaises(ValueError):
            guard.member_path(info)

    def test_duplicate_and_file_directory_collisions_rejected(self):
        for members in [[("a", b"1"), ("a", b"2")],
                        [("a", b"1"), ("a/b", b"2")],
                        [("a/b", b"2"), ("a", b"1")]]:
            with self.subTest(members=members):
                archive = self.make_zip(members)
                with self.assertRaises(ValueError):
                    guard.archive_inventory(archive)

    def test_implicit_directories_and_block_rounding_counted(self):
        archive = self.make_zip([("deep/tree/a.txt", b"x")])
        result = guard.archive_inventory(archive, 4096)
        self.assertEqual(result["file_count"], 1)
        self.assertEqual(result["directory_count"], 2)
        self.assertEqual(result["inode_estimate"], 4)
        self.assertEqual(result["allocation_estimate_bytes"], 4 * 4096)

    def test_nonempty_directory_rejected(self):
        archive = self.make_zip([("a/", b"hidden payload")])
        with self.assertRaises(ValueError):
            guard.archive_inventory(archive)

    def test_manifest_verified_and_bad_hash_rejected(self):
        archive, raw = self.packet()
        result = guard.verify_packet_manifest(archive)
        self.assertEqual(result["manifest_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["verified_file_count"], 1)
        bad = json.loads(raw)
        bad["files"]["nested/note.txt"] = "0" * 64
        archive = self.make_zip([("nested/note.txt", b"synthetic content\n"),
                                 ("PACKET-MANIFEST.json", json.dumps(bad).encode())])
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            guard.verify_packet_manifest(archive)

    def test_manifest_missing_member_rejected(self):
        manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {"missing": "0" * 64}}
        archive = self.make_zip([("PACKET-MANIFEST.json", json.dumps(manifest).encode())])
        with self.assertRaisesRegex(ValueError, "Missing manifest member"):
            guard.verify_packet_manifest(archive)

    def test_manifest_unlisted_member_rejected(self):
        manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {}}
        archive = self.make_zip([("PACKET-MANIFEST.json", json.dumps(manifest).encode()),
                                 ("unlisted.txt", b"synthetic")])
        with self.assertRaisesRegex(ValueError, "Unlisted packet member"):
            guard.verify_packet_manifest(archive)

    def test_extract_round_trip_and_existing_destination_refusal(self):
        archive, _ = self.packet()
        destination = self.root / "extract"
        with self.ready_resources():
            result = guard.extract_packet(archive, destination, 0, 0)
            self.assertEqual(result["status"], "extracted")
            self.assertEqual((destination / "nested/note.txt").read_bytes(), b"synthetic content\n")
            again = guard.extract_packet(archive, destination, 0, 0)
        self.assertEqual(again["status"], "blocked")
        self.assertIn("extraction_destination_already_exists", again["failures"])
        self.assertEqual(json.loads((destination / "GUARD-EXTRACTION.json").read_text())["status"], "extracted")

    def test_reserved_receipt_collision_rejected_before_mkdir(self):
        for member in ["GUARD-EXTRACTION.json", "GUARD-EXTRACTION.json/child"]:
            with self.subTest(member=member):
                archive, _ = self.packet([(member, b"synthetic")])
                destination = self.root / "not-created"
                with self.ready_resources(), self.assertRaises(ValueError):
                    guard.extract_packet(archive, destination, 0, 0)
                self.assertFalse(destination.exists())

    def test_extraction_write_failure_preserves_failed_receipt(self):
        archive, _ = self.packet()
        destination = self.root / "partial"
        with self.ready_resources(), mock.patch.object(guard.shutil, "copyfileobj", side_effect=OSError("synthetic ENOSPC")):
            with self.assertRaises(OSError):
                guard.extract_packet(archive, destination, 0, 0)
        self.assertTrue(destination.is_dir())
        receipt = json.loads((destination / "GUARD-EXTRACTION.json").read_text())
        self.assertEqual(receipt["status"], "failed_partial_preserved")
        self.assertIn("synthetic ENOSPC", receipt["error"])

    def test_preflight_refuses_private_dev_without_creating_it(self):
        archive, _ = self.packet()
        with self.ready_resources():
            result = guard.preflight(archive, "/dev/arc-guard-synthetic-never-created", 0, 0)
        self.assertIn("private_dev_destination_not_supported", result["failures"])

    def test_critically_low_memory_refuses_before_loading_zip_metadata(self):
        archive, _ = self.packet()
        low = copy.deepcopy(GOOD_MEMORY)
        low["effective_available_bytes"] = 32 * guard.MIB
        with mock.patch.object(guard, "memory_snapshot", return_value=low), \
                mock.patch.object(guard, "filesystem_snapshot", return_value=copy.deepcopy(GOOD_FS)), \
                mock.patch.object(guard, "archive_inventory") as inventory:
            result = guard.preflight(archive, self.root / "not-created", 0, 0)
        inventory.assert_not_called()
        self.assertEqual(result["inventory"]["status"], "not_inspected")
        self.assertIn("insufficient_memory_for_metadata_inspection", result["failures"])


class CheckpointTests(GuardCase):
    def test_exact_bytes_hashes_and_manifest_binding(self):
        work = self.work_records()
        destination = self.root / "checkpoint"
        result = guard.checkpoint(work, destination)
        self.assertEqual(result["status"], "checkpointed")
        self.assertEqual(result["packet_manifest_sha256"], guard.digest_file(work / "PACKET-MANIFEST.json"))
        for name, info in result["files"].items():
            self.assertEqual((work / name).read_bytes(), (destination / name).read_bytes())
            self.assertEqual(info["sha256"], guard.digest_file(destination / name))
        self.assertEqual(result, json.loads((destination / "CHECKPOINT.json").read_text()))

    def test_missing_assignment_and_manifest_fail_without_destination(self):
        work = self.work_records()
        for name in ["ASSIGNMENT.json", "PACKET-MANIFEST.json"]:
            with self.subTest(name=name):
                raw = (work / name).read_bytes()
                (work / name).unlink()
                destination = self.root / "not-created"
                with self.assertRaises(ValueError):
                    guard.checkpoint(work, destination)
                self.assertFalse(destination.exists())
                (work / name).write_bytes(raw)

    def test_assignment_with_wrong_packet_hash_rejected(self):
        work = self.work_records()
        path = work / "ASSIGNMENT.json"
        record = json.loads(path.read_bytes())
        record["packet_id"] = "0" * 64
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "not bound"):
            guard.checkpoint(work, self.root / "not-created")
        self.assertFalse((self.root / "not-created").exists())

    def test_manifest_symlink_rejected(self):
        work = self.work_records()
        original = work / "PACKET-MANIFEST.json"
        target = self.root / "manifest-bytes"
        original.rename(target)
        original.symlink_to(target)
        with self.assertRaises(ValueError):
            guard.checkpoint(work, self.root / "not-created")

    def test_record_change_during_copy_is_detected(self):
        work = self.work_records()
        path = work / "ASSIGNMENT.json"
        real_read = Path.read_bytes
        reads = 0
        def changing_read(candidate):
            nonlocal reads
            raw = real_read(candidate)
            if candidate == path:
                reads += 1
                if reads > 1:
                    return raw + b" "
            return raw
        with mock.patch.object(Path, "read_bytes", changing_read):
            with self.assertRaisesRegex(ValueError, "changed during checkpoint"):
                guard.checkpoint(work, self.root / "partial")
        self.assertTrue((self.root / "partial").is_dir())
        self.assertFalse((self.root / "partial/CHECKPOINT.json").exists())

    def test_manifest_change_during_checkpoint_is_detected(self):
        work = self.work_records()
        real_read = Path.read_bytes
        changed = False
        def changing_read(candidate):
            nonlocal changed
            raw = real_read(candidate)
            if candidate == work / "ASSIGNMENT.json" and not changed:
                changed = True
                (work / "PACKET-MANIFEST.json").write_bytes(b"changed manifest")
            return raw
        with mock.patch.object(Path, "read_bytes", changing_read):
            with self.assertRaises(ValueError):
                guard.checkpoint(work, self.root / "checkpoint")


class StreamTests(GuardCase):
    def test_head_tail_retention_is_bounded_and_exact(self):
        for raw in [b"", b"small", b"a" * 1024, b"HEAD" + b"x" * 10000 + b"TAIL"]:
            with self.subTest(length=len(raw)):
                path = self.root / ("log-" + str(len(raw)))
                metadata = {}
                guard._drain(io.BytesIO(raw), path, 1024, metadata)
                retained = path.read_bytes()
                self.assertNotIn("capture_error", metadata)
                self.assertEqual(metadata["observed_bytes"], len(raw))
                self.assertEqual(metadata["omitted_bytes"], max(0, len(raw) - 1024))
                self.assertLessEqual(len(retained), 1124)
                self.assertEqual(metadata["retained_sha256"], guard.digest_file(path))
                if len(raw) <= 1024:
                    self.assertEqual(retained, raw)
                else:
                    self.assertTrue(retained.startswith(raw[:512]))
                    self.assertTrue(retained.endswith(raw[-512:]))

    def test_capture_error_still_drains_pipe(self):
        path = self.root / "occupied"
        path.write_bytes(b"unchanged")
        pipe = io.BytesIO(b"child output")
        metadata = {}
        guard._drain(pipe, path, 1024, metadata)
        self.assertIn("capture_error", metadata)
        self.assertTrue(pipe.closed)
        self.assertEqual(path.read_bytes(), b"unchanged")


class CommandTests(GuardCase):
    """Six Popen attempts across this class; all memory probes are mocked."""
    def run_command(self, argv, **kwargs):
        work = self.work_records()
        destination = self.root / "run"
        with mock.patch.object(guard, "memory_snapshot", return_value=copy.deepcopy(GOOD_MEMORY)):
            result, code = guard.run_guarded(argv, self.root, work, destination,
                                            min_memory_bytes=0, max_output_bytes=1024, **kwargs)
        self.assertEqual(result, json.loads((destination / "COMMAND.json").read_text()))
        self.assertTrue((destination / "CHECKPOINT.json").is_file())
        return result, code, destination

    def test_success_streams_bounded_output_and_preserves_checkpoint(self):
        result, code, destination = self.run_command([sys.executable, "-c",
            "import sys; sys.stdout.write('H' + 'x'*10000 + 'T'); sys.stderr.write('stderr marker')"])
        self.assertEqual(code, 0)
        self.assertTrue(result["passed"])
        self.assertIsNone(result["signal"])
        self.assertEqual(result["stdout"]["observed_bytes"], 10002)
        self.assertEqual(result["stdout"]["omitted_bytes"], 10002 - 1024)
        self.assertLessEqual((destination / "stdout.log").stat().st_size, 1124)
        self.assertEqual((destination / "stderr.log").read_bytes(), b"stderr marker")

    def test_exit_137_is_not_reported_as_a_signal(self):
        result, code, _ = self.run_command([sys.executable, "-c", "raise SystemExit(137)"])
        self.assertEqual((code, result["returncode"], result["signal"]), (137, 137, None))
        self.assertFalse(result["passed"])
        self.assertFalse(result["cgroup_oom_kill_observed"])

    @unittest.skipUnless(os.name == "posix", "POSIX signal return codes")
    def test_signal_has_negative_raw_returncode(self):
        result, code, _ = self.run_command([sys.executable, "-c",
            "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"])
        self.assertEqual(result["returncode"], -signal.SIGTERM)
        self.assertEqual(result["signal"], "SIGTERM")
        self.assertEqual(code, 128 + signal.SIGTERM)
        self.assertFalse(result["passed"])

    def test_timeout_has_distinct_status(self):
        result, code, _ = self.run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
        self.assertEqual(result["status"], "timed_out")
        self.assertEqual(code, 124)
        self.assertFalse(result["passed"])

    @unittest.skipUnless(hasattr(os, "fork"), "POSIX inherited-pipe scenario")
    def test_timeout_includes_pipes_inherited_by_descendant(self):
        # Parent exits successfully; its child still owns stdout/stderr. The
        # guard deadline must cover that drain phase and kill the process group.
        script = "import os,time\nchild=os.fork()\nif child == 0:\n time.sleep(5)\n os._exit(0)\nos._exit(0)\n"
        result, code, _ = self.run_command([sys.executable, "-c", script], timeout=0.2)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual((result["status"], code), ("timed_out", 124))
        self.assertFalse(result["passed"])
        self.assertLess(result["duration_seconds"], 3)

    def test_missing_executable_leaves_spawn_failure_receipt(self):
        result, code, _ = self.run_command([str(self.root / "does-not-exist")])
        self.assertEqual(result["status"], "spawn_failed")
        self.assertEqual(code, 2)
        self.assertIsNone(result["returncode"])

    def test_low_memory_checkpoints_but_does_not_spawn(self):
        work = self.work_records()
        destination = self.root / "blocked"
        low = copy.deepcopy(GOOD_MEMORY)
        low["effective_available_bytes"] = 0
        with mock.patch.object(guard, "memory_snapshot", return_value=low), \
                mock.patch.object(guard.subprocess, "Popen") as spawn:
            result, code = guard.run_guarded(["unused"], self.root, work, destination,
                                            min_memory_bytes=1, max_output_bytes=1024)
        spawn.assert_not_called()
        self.assertEqual((result["status"], code), ("blocked_before_execution", 2))
        self.assertTrue((destination / "CHECKPOINT.json").is_file())
        self.assertTrue((destination / "COMMAND.json").is_file())


if __name__ == "__main__":
    unittest.main()
