"""Synthetic storage-adapter regressions using the unmodified official builder.

Run with pyfakefs==5.9.3 and the verified packet's repo/src on PYTHONPATH.
These tests make no claims about the actual review's completion or runtime.
"""
from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from arcpuzzles import review_full_return as official
from pyfakefs.fake_filesystem_unittest import Patcher

HELPER = Path(__file__).parents[1] / "workspace/tools/package_in_memory.py"
spec = importlib.util.spec_from_file_location("memory_packaging", HELPER)
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


class MemoryPackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="arcpuzzles-memory-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "WORK"
        self.work.mkdir()
        self.generator = "repo/generators/fixture/generator.py"
        self.support = "repo/shared/runtime/support.py"
        self.opaque = "repo/shared/data/opaque.bin"
        self.files = {self.generator: b"VALUE = 1\n", self.support: b"VALUE = 2\n",
                      self.opaque: bytes(range(256))}
        row = {"generator": self.generator.removeprefix("repo/"),
               "generator_sha256": adapter.sha(self.files[self.generator]),
               "rule_task_id": "fixture", "rule_hash": "synthetic", "approved": False}
        question = {"id": "q", "version": 1, "sha256": adapter.sha(b"question")}
        self.manifest = {"schema": "arcpuzzles-full-packet-v2", "main_ids": ["fixture"],
                         "all_ids": ["fixture"], "generators": {"fixture": row},
                         "questions": [question],
                         "files": {n: adapter.sha(b) for n, b in self.files.items()},
                         "layout": {"workspace": "WORK", "entry_files": {"review.py": adapter.sha(b"# entry\n")}}}
        original = {"WORK/" + n: b for n, b in self.files.items()}
        original.update({"WORK/PACKET-MANIFEST.json": adapter.canonical(self.manifest), "review.py": b"# entry\n"})
        self.packet = self.root / "original.zip"
        self.write_zip(original)
        members = [n for n in original if n != "WORK/" + self.opaque]
        for name in members:
            self.write(self.root / name, original[name])
        contract = {"schema": "arcpuzzles-full-assignment-v2", "assignment_id": "review-0123456789abcdef",
                    "packet_id": adapter.sha(adapter.canonical(self.manifest)), "task_id": "fixture",
                    "generator": row, "question": question,
                    "baseline_sha256": {self.generator: adapter.sha(self.files[self.generator])}}
        self.write(self.work / "ASSIGNMENT.json", adapter.canonical(contract))
        self.write(self.work / ".review/baseline" / self.generator, self.files[self.generator])
        inventory = {"schema": "arcpuzzles-partial-extraction-inventory-v1",
                     "source_archive_sha256": adapter.sha(self.packet.read_bytes()),
                     "packet_sha256": contract["packet_id"], "members": members}
        self.write(self.work / "extraction_inventory.json", adapter.canonical(inventory))
        for doc in official.REQUIRED_DOCS:
            self.write(self.work / doc, b"Synthetic storage-adapter test only.\n")
        self.write(self.work / "RESULTS.json", adapter.canonical(
            {"completion_state": "in_progress", "stopping_reason": "synthetic regression fixture"}))

    @staticmethod
    def write(path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def write_zip(self, members):
        with zipfile.ZipFile(self.packet, "w") as archive:
            for name, raw in members.items():
                info = zipfile.ZipInfo(name)
                info.external_attr = 0o100644 << 16
                archive.writestr(info, raw)

    def snapshot(self):
        return adapter.read_snapshot(self.packet, self.work)

    def test_original_and_overlay_bytes_roundtrip_and_external_validation(self):
        evidence = b"\x00\xff\r\n" + bytes(range(256))
        self.write(self.work / "checks/opaque.bin", evidence)
        self.write(self.work / "repo/generators/fixture/workspace/new.txt", "café\r\nfinal line".encode())
        snapshot = self.snapshot()
        with Patcher(use_known_patches=False) as patcher:
            adapter.hydrate(snapshot, patcher.fs)
            self.assertEqual((self.work / self.opaque).read_bytes(), self.files[self.opaque])
        raw = adapter.memory_return(snapshot, official)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            checked = official.validate_full_return(archive, self.manifest)
            self.assertEqual(archive.read("checks/opaque.bin"), evidence)
            self.assertIn("café\r\n".encode(), archive.read("patches/source.patch"))
            self.assertEqual(checked["completion_state"], "in_progress")
        self.assertEqual(self.snapshot(), snapshot)
        self.assertFalse((self.work / self.opaque).exists())

    def test_official_builder_rejects_out_of_scope_corruption(self):
        self.write(self.work / self.support, b"CORRUPTED = True\n")
        with self.assertRaisesRegex(ValueError, "Changed or missing shared packet source"):
            adapter.memory_return(self.snapshot(), official)

    def test_missing_extracted_file_is_not_restored(self):
        (self.work / self.support).unlink()
        with self.assertRaisesRegex(ValueError, "Missing extracted member"):
            self.snapshot()

    def test_new_source_outside_selected_task_is_visible(self):
        self.write(self.work / "repo/shared/unexpected.py", b"unexpected = True\n")
        with self.assertRaisesRegex(ValueError, "Undeclared new source outside selected generator"):
            adapter.memory_return(self.snapshot(), official)

    def test_executable_source_mode_is_preserved_and_rejected(self):
        (self.work / self.generator).chmod(0o755)
        with self.assertRaisesRegex(ValueError, "Unsafe changed source"):
            adapter.memory_return(self.snapshot(), official)

    def test_symlink_source_is_preserved_and_rejected(self):
        path = self.work / self.generator
        path.unlink()
        path.symlink_to(self.work / self.support)
        with self.assertRaisesRegex(ValueError, "Unsafe changed source"):
            adapter.memory_return(self.snapshot(), official)

    def test_changed_outer_entry_and_frozen_baseline_are_rejected(self):
        self.write(self.root / "review.py", b"altered entry\n")
        with self.assertRaisesRegex(ValueError, "Changed immutable packet entry"):
            self.snapshot()
        self.write(self.root / "review.py", b"# entry\n")
        self.write(self.work / ".review/baseline" / self.generator, b"changed baseline\n")
        with self.assertRaisesRegex(ValueError, "Frozen baseline changed"):
            self.snapshot()

    def test_original_unextracted_bytes_are_hash_checked(self):
        with zipfile.ZipFile(self.packet) as archive:
            members = {n: archive.read(n) for n in archive.namelist()}
        members["WORK/" + self.opaque] = b"corrupt original"
        self.write_zip(members)
        with self.assertRaisesRegex(ValueError, "Original member hash differs"):
            self.snapshot()

    def test_nul_in_raw_zip_filename_is_rejected_before_normalization(self):
        with zipfile.ZipFile(self.packet) as archive:
            members = {n: archive.read(n) for n in archive.namelist()}
        with zipfile.ZipFile(self.packet, "w") as archive:
            for name, raw in members.items():
                info = zipfile.ZipInfo(name)
                if name == "WORK/" + self.opaque:
                    info.filename += "\0"  # Preserve a raw malformed ZIP name.
                info.external_attr = 0o100644 << 16
                archive.writestr(info, raw)
        with self.assertRaisesRegex(ValueError, "Unsafe packet path|Altered raw ZIP filename"):
            adapter.read_original(self.packet)

    def test_outer_manifest_cannot_override_workspace_hash_or_manifest(self):
        with zipfile.ZipFile(self.packet) as archive:
            members = {n: archive.read(n) for n in archive.namelist()}
        malformed = json.loads(adapter.canonical(self.manifest))
        malformed["files"][self.opaque] = "0" * 64
        malformed["layout"]["entry_files"]["WORK/" + self.opaque] = adapter.sha(self.files[self.opaque])
        members["WORK/PACKET-MANIFEST.json"] = adapter.canonical(malformed)
        self.write_zip(members)
        with self.assertRaisesRegex(ValueError, "Outer entry must be outside WORK"):
            adapter.read_original(self.packet)
        malformed = json.loads(adapter.canonical(self.manifest))
        malformed["files"]["PACKET-MANIFEST.json"] = "0" * 64
        members["WORK/PACKET-MANIFEST.json"] = adapter.canonical(malformed)
        self.write_zip(members)
        with self.assertRaisesRegex(ValueError, "Manifest cannot declare itself"):
            adapter.read_original(self.packet)


if __name__ == "__main__":
    unittest.main()
