"""Synthetic-only safety tests; never reads the uploaded task library."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import warnings
import zipfile
import stat
from unittest.mock import patch

try:
    import packet_recovery as recovery
except ModuleNotFoundError:
    recovery = None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(recovery, "Recovery implementation is missing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "WORK"
        self.work.mkdir()
        self.files = {"repo/src/arcpuzzles/__init__.py": b"", "repo/common.py": b"issued\n",
                      "repo/generators/synthetic/generator.py": b"synthetic\n"}
        self.archive = self.root / "source.zip"

    def packet(self, *, corrupt=None, extra=None, duplicate=False):
        entries = {"START-HERE.md": b"test\n", "review.py": b"# synthetic\n"}
        manifest = {"schema": "arcpuzzles-full-packet-v2", "files": {
            name: digest(raw) for name, raw in self.files.items()},
            "layout": {"workspace": "WORK", "entry_files": {
                name: digest(raw) for name, raw in entries.items()}}}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "w") as z:
                z.writestr("WORK/PACKET-MANIFEST.json", canonical(manifest))
                for name, raw in entries.items():
                    z.writestr(name, raw)
                for name, raw in self.files.items():
                    z.writestr("WORK/" + name, b"corrupt" if name == corrupt else raw)
                if extra:
                    z.writestr(extra, b"unsafe")
                if duplicate:
                    z.writestr("WORK/repo/common.py", b"duplicate")
        return recovery.Packet(self.archive)

    def test_verify_hashes_all_members_and_outer_entries(self):
        with self.packet() as packet:
            self.assertEqual(packet.verify()["files_verified"], len(self.files))

    def test_corrupt_member_rejected_on_verify_and_hydrate(self):
        with self.packet(corrupt="repo/common.py") as packet:
            with self.assertRaises(ValueError):
                packet.verify()
            with self.assertRaises(ValueError):
                packet.hydrate(self.work, ["repo/common.py"])
        self.assertFalse((self.work / "repo/common.py").exists())

    def test_duplicate_archive_member_rejected(self):
        with self.assertRaises(ValueError):
            self.packet(duplicate=True)

    def test_symlink_archive_member_rejected(self):
        with self.packet():
            pass
        with zipfile.ZipFile(self.archive, "a") as z:
            info = zipfile.ZipInfo("WORK/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, "repo/common.py")
        with self.assertRaises(ValueError):
            recovery.Packet(self.archive)

    def test_traversal_archive_member_rejected(self):
        for name in ("../escape", "/absolute", "WORK/repo/../escape", "WORK\\escape"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.packet(extra=name)

    def test_hydrate_is_idempotent_and_preserves_local_edit(self):
        with self.packet() as packet:
            packet.hydrate(self.work, ["repo/common.py"])
            packet.hydrate(self.work, ["repo/common.py"])
            target = self.work / "repo/common.py"
            self.assertEqual(target.read_bytes(), self.files["repo/common.py"])
            target.write_bytes(b"local edit")
            with self.assertRaises(ValueError):
                packet.hydrate(self.work, ["repo/common.py"])
            self.assertEqual(target.read_bytes(), b"local edit")

    def test_hydrate_rejects_unknown_or_traversal_requested_member(self):
        with self.packet() as packet:
            for name in ("../escape", "repo/unknown.py", "/absolute", "repo\\common.py"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    packet.hydrate(self.work, [name])

    def test_hydrate_rejects_symlink_parent(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.work / "repo").symlink_to(elsewhere, target_is_directory=True)
        with self.packet() as packet, self.assertRaises(ValueError):
            packet.hydrate(self.work, ["repo/common.py"])
        self.assertFalse((elsewhere / "common.py").exists())

    def test_seed_is_durable_and_retry_does_not_redraw(self):
        with self.packet() as packet:
            first = recovery.commit_seed(self.work, packet.packet_id)
            self.assertEqual(len(first), 32)
            with patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")):
                second = recovery.commit_seed(self.work, packet.packet_id)
            self.assertEqual(first, second)
            saved = json.loads((self.work / ".review/portable-seed.json").read_text())
            self.assertEqual(saved["packet_id"], packet.packet_id)
            self.assertEqual(saved["seed"], first.hex())

    def test_seed_survives_later_hydration_failure(self):
        with self.packet(corrupt="repo/common.py") as packet:
            seed = recovery.commit_seed(self.work, packet.packet_id)
            with self.assertRaises(ValueError):
                packet.hydrate(self.work, ["repo/common.py"])
            self.assertEqual(recovery.commit_seed(self.work, packet.packet_id), seed)

    def test_seed_cannot_be_reused_for_different_packet(self):
        with self.packet() as packet:
            recovery.commit_seed(self.work, packet.packet_id)
            with self.assertRaises(ValueError):
                recovery.commit_seed(self.work, "0" * 64)

    def test_native_seed_journal_is_adopted_without_new_entropy(self):
        with self.packet() as packet:
            (self.work / ".review").mkdir()
            (self.work / ".review/main-draw-seed.json").write_bytes(canonical({
                "schema": "arcpuzzles-main-draw-seed-v1", "packet_id": packet.packet_id,
                "seed": "9a" * 32}))
            with patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")):
                self.assertEqual(recovery.commit_seed(self.work, packet.packet_id), bytes.fromhex("9a" * 32))

    def test_native_and_portable_journal_conflict_is_rejected(self):
        with self.packet() as packet:
            recovery.commit_seed(self.work, packet.packet_id)
            (self.work / ".review/main-draw-seed.json").write_bytes(canonical({
                "schema": "arcpuzzles-main-draw-seed-v1", "packet_id": packet.packet_id,
                "seed": "ab" * 32}))
            with self.assertRaisesRegex(ValueError, "conflict"):
                recovery.commit_seed(self.work, packet.packet_id)

    def test_seed_journal_schemas_and_encodings_are_strict(self):
        with self.packet() as packet:
            (self.work / ".review").mkdir()
            for name, schema in (("portable-seed.json", "arcpuzzles-portable-seed-v1"),
                                 ("main-draw-seed.json", "arcpuzzles-main-draw-seed-v1")):
                target = self.work / ".review" / name
                valid = {"schema": schema, "packet_id": packet.packet_id, "seed": "cd" * 32}
                for record in (dict(valid, schema="unknown"), dict(valid, schema=None),
                               dict(valid, packet_id="0" * 64), dict(valid, seed="CD" * 32),
                               dict(valid, seed=None), [], dict(valid, seed="cd")):
                    target.write_bytes(canonical(record))
                    with self.subTest(name=name, record=record), \
                            patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")), \
                            self.assertRaises(ValueError):
                        recovery.commit_seed(self.work, packet.packet_id)
                target.unlink()

    def test_enospc_hydration_retry_keeps_seed_without_capacity_gate(self):
        with self.packet() as packet:
            packet.manifest["questions"] = [{"id": "q"}]
            packet.infos["WORK/repo/REVIEW/questions/q.json"] = SimpleNamespace(file_size=1)
            draw = SimpleNamespace(main_selection_for_seed=lambda manifest, seed: ("synthetic", None),
                _base_paths=lambda work, manifest, task: ["repo/common.py"])
            calls = []

            def hydrate(work, names):
                calls.append(list(names))
                if len(calls) % 2 == 0:
                    raise OSError(28, "No space left on device")
                return {}

            with patch.object(packet, "bootstrap", return_value={}), \
                    patch.object(packet, "hydrate", side_effect=hydrate), \
                    patch("packet_recovery.import_workflow", return_value=draw), \
                    patch("shutil.disk_usage", side_effect=AssertionError("capacity preflight")):
                with self.assertRaisesRegex(OSError, "No space"):
                    recovery.hydrate_main(packet, self.root)
                saved = (self.work / ".review/portable-seed.json").read_bytes()
                with patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")), \
                        self.assertRaisesRegex(OSError, "No space"):
                    recovery.hydrate_main(packet, self.root)
                self.assertEqual((self.work / ".review/portable-seed.json").read_bytes(), saved)

    def test_existing_assignment_seed_is_adopted_without_new_entropy(self):
        with self.packet() as packet:
            (self.work / "ASSIGNMENT.json").write_bytes(canonical({
                "packet_id": packet.packet_id, "seed": "12" * 32}))
            with patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")):
                self.assertEqual(recovery.commit_seed(self.work, packet.packet_id), bytes.fromhex("12" * 32))

    def test_pending_seed_is_adopted_and_conflict_is_rejected(self):
        with self.packet() as packet:
            (self.work / ".review").mkdir()
            pending = self.work / ".review/pending-main-draw.json"
            pending.write_bytes(canonical({"schema": "arcpuzzles-pending-main-draw-v1",
                "contract": {"packet_id": packet.packet_id, "seed": "34" * 32}}))
            with patch("packet_recovery.os.urandom", side_effect=AssertionError("redraw")):
                self.assertEqual(recovery.commit_seed(self.work, packet.packet_id), bytes.fromhex("34" * 32))
            (self.work / "ASSIGNMENT.json").write_bytes(canonical({
                "packet_id": packet.packet_id, "seed": "56" * 32}))
            with self.assertRaisesRegex(ValueError, "conflict"):
                recovery.commit_seed(self.work, packet.packet_id)

    def test_seed_symlink_cannot_be_followed(self):
        with self.packet() as packet:
            (self.work / ".review").mkdir()
            elsewhere = self.root / "external-seed.json"
            elsewhere.write_text("do not touch")
            (self.work / ".review/portable-seed.json").symlink_to(elsewhere)
            with self.assertRaises(ValueError):
                recovery.commit_seed(self.work, packet.packet_id)
            self.assertEqual(elsewhere.read_text(), "do not touch")

    def test_completed_draw_resumes_without_rehydrating_edited_sources(self):
        with self.packet() as packet:
            contract = {"packet_id": packet.packet_id, "seed": "78" * 32,
                        "assignment_id": "existing", "task_id": "synthetic"}
            (self.work / "ASSIGNMENT.json").write_bytes(canonical(contract))
            draw = SimpleNamespace(draw_main=lambda work, seed: contract)
            with patch.object(packet, "bootstrap", return_value={}), \
                    patch.object(packet, "hydrate", side_effect=AssertionError("rehydration")), \
                    patch("packet_recovery.import_workflow", return_value=draw):
                result = recovery.hydrate_main(packet, self.root)
            self.assertEqual(result["assignment_id"], "existing")

    def test_package_fallback_verifies_absent_unselected_member(self):
        with self.packet() as packet:
            self.assertTrue(packet.unchanged_source(self.work, "repo/common.py", digest(b"issued\n")))

    def test_package_fallback_rejects_changed_local_member(self):
        with self.packet() as packet:
            packet.hydrate(self.work, ["repo/common.py"])
            (self.work / "repo/common.py").write_bytes(b"changed")
            self.assertFalse(packet.unchanged_source(self.work, "repo/common.py", digest(b"issued\n")))

    def test_package_fallback_rejects_corrupt_absent_source(self):
        with self.packet(corrupt="repo/common.py") as packet, self.assertRaises(ValueError):
            packet.unchanged_source(self.work, "repo/common.py", digest(b"issued\n"))

    def test_package_adapter_retains_missing_selected_candidate_rejection(self):
        source = '''def build_full_return(packet_root, out=None, *, bundle_evidence=False):
    contract = {"baseline_sha256": {"repo/generators/synthetic/generator.py": "digest"}}
    candidates = set(contract["baseline_sha256"])
    for path in candidates:
        target = packet_root / path
        if not target.is_file():
            raise ValueError("Changed source outside allowed task scope: " + path)
    for path, digest in manifest["files"].items():
        if path.startswith("repo/") and path not in candidates:
            target = packet_root / path
            if not target.is_file() or target.is_symlink() or _sha(target.read_bytes()) != digest:
                raise ValueError("Changed source outside allowed task scope: " + path)
    return "packaged"
'''
        with self.packet() as packet:
            adapted = recovery.compile_package_adapter(source, {"manifest": packet.manifest,
                "_sha": digest}, packet, self.work)
            with self.assertRaisesRegex(ValueError, "synthetic/generator.py"):
                adapted(self.work)
            packet.hydrate(self.work, ["repo/generators/synthetic/generator.py"])
            self.assertEqual(adapted(self.work), "packaged")

    def test_package_adapter_fails_closed_on_unrecognized_source(self):
        with self.packet() as packet, self.assertRaises(ValueError):
            recovery.compile_package_adapter("def build_full_return(*args): return 1", {}, packet, self.work)

    def test_replay_adapter_changes_only_source_path_resolution(self):
        source = '''def replay_return(source_zip, return_zip, compare_work, out, *, runtime_closure=False):
    source_zip, return_zip = Path(source_zip).resolve(), Path(return_zip).resolve()
    owner, out = Path(compare_work).absolute(), Path(out).absolute()
    validate_full_return(return_zip, owner)
    return source_zip, return_zip, owner, out, runtime_closure
'''
        events = []

        class TracePath:
            def __init__(self, value):
                self.value = value

            def resolve(self):
                events.append(("resolve", self.value))
                return "resolved:" + self.value

            def absolute(self):
                events.append(("absolute", self.value))
                return "absolute:" + self.value

        def validate(returned, owner):
            events.append(("validate", returned, owner))

        function = recovery.compile_replay_adapter(source, {"Path": TracePath,
            "validate_full_return": validate})
        result = function("/proc/self/fd/7", "return.zip", "owner", "out", runtime_closure=True)
        self.assertEqual(result, ("absolute:/proc/self/fd/7", "resolved:return.zip",
                                 "absolute:owner", "absolute:out", True))
        self.assertEqual(events, [("absolute", "/proc/self/fd/7"), ("resolve", "return.zip"),
            ("absolute", "owner"), ("absolute", "out"),
            ("validate", "resolved:return.zip", "absolute:owner")])

    @unittest.skipUnless(hasattr(os, "memfd_create"), "Linux memfd transport test")
    def test_replay_adapter_reads_memfd_and_keeps_return_symlink_resolution(self):
        source = '''def replay_return(source_zip, return_zip, compare_work, out, *, runtime_closure=False):
    source_zip, return_zip = Path(source_zip).resolve(), Path(return_zip).resolve()
    return source_zip.read_bytes(), return_zip, runtime_closure
'''
        descriptor = os.memfd_create("recovery-synthetic-test")
        self.addCleanup(os.close, descriptor)
        os.write(descriptor, b"synthetic sealed-source transport")
        source_path = Path(f"/proc/self/fd/{descriptor}")
        self.assertFalse(source_path.resolve().exists())
        returned = self.root / "return.zip"
        returned.write_bytes(b"synthetic return")
        link = self.root / "return-link.zip"
        link.symlink_to(returned)
        function = recovery.compile_replay_adapter(source, {"Path": Path})
        self.assertEqual(function(source_path, link, self.work, self.root / "out"),
                         (b"synthetic sealed-source transport", returned.resolve(), False))

    def test_replay_adapter_rejects_unrecognized_or_ambiguous_assignment(self):
        correct = "source_zip, return_zip = Path(source_zip).resolve(), Path(return_zip).resolve()"
        variants = ["source_zip = Path(source_zip).resolve()",
                    correct.replace("Path(return_zip).resolve()", "Path(return_zip).absolute()"),
                    correct + "\n    " + correct]
        for assignment in variants:
            source = "def replay_return(source_zip, return_zip, *args):\n    " + assignment + "\n"
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                recovery.compile_replay_adapter(source, {"Path": Path})
        with self.assertRaisesRegex(ValueError, "Malformed"):
            recovery.compile_replay_adapter("def replay_return(", {"Path": Path})

    def test_replay_entry_refuses_non_fd_transport_before_bootstrap(self):
        with self.packet() as packet, patch.object(packet, "bootstrap", side_effect=AssertionError("bootstrap")), \
                self.assertRaisesRegex(ValueError, "proc/self/fd"):
            recovery.replay_return(packet, self.root, self.root / "return.zip", self.work, self.root / "fresh")

    def test_replay_entry_rejects_changed_issued_module_before_compiling(self):
        with self.packet() as packet:
            packet.path = Path("/proc/self/fd/999")
            name = "repo/src/arcpuzzles/review_replay.py"
            path = self.work / name
            path.parent.mkdir(parents=True)
            path.write_bytes(b"changed module")
            packet.files[name] = digest(b"issued module")
            with patch.object(packet, "bootstrap", return_value={}), \
                    patch("packet_recovery.import_workflow", return_value=None), \
                    patch("packet_recovery.compile_replay_adapter", side_effect=AssertionError("compiled altered code")), \
                    patch("packet_recovery.importlib.import_module", return_value=SimpleNamespace(__file__=str(path))), \
                    self.assertRaisesRegex(ValueError, "differs from original"):
                recovery.replay_return(packet, self.root, self.root / "return.zip", self.work, self.root / "fresh")


if __name__ == "__main__":
    unittest.main()
