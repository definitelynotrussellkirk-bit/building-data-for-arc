"""Synthetic tests; no puzzle data, generator imports, or Racket execution."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sys.path.insert(0, str(WORK / "repo/src"))
sys.path.insert(0, str(HERE))

from arcpuzzles.review_full_packet import SCHEMA, canonical_json
from arcpuzzles.review_full_return import build_full_return


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ArchivePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fixture-", dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.work = self.base / "packet/WORK"
        self.work.mkdir(parents=True)
        self.source_zip = self.base / "source.zip"
        self.selected = "repo/generators/fixture/generator.py"
        self.immutable = "repo/shared/immutable.txt"
        self.original = {
            self.selected: b"VALUE = 1\n",
            self.immutable: b"immutable original\n",
            "repo/generators/peer/generator.py": b"VALUE = 99\n",
        }
        entries = {"START-HERE.md": b"Synthetic test packet.\n", "review.py": b"# fixture\n"}
        row = {"generator": "generators/fixture/generator.py",
               "generator_sha256": sha(self.original[self.selected]),
               "rule_task_id": "fixture", "rule_hash": sha(b"synthetic rule"),
               "approved": False}
        question = {"id": "fixture-question", "version": 1, "sha256": sha(b"question")}
        self.manifest = {
            "schema": SCHEMA, "files": {p: sha(raw) for p, raw in self.original.items()},
            "main_ids": ["fixture"], "all_ids": ["fixture"],
            "generators": {"fixture": row}, "questions": [question],
            "layout": {"workspace": "WORK", "entry_files": {p: sha(raw) for p, raw in entries.items()}},
        }
        manifest_bytes = canonical_json(self.manifest)
        seed = bytes.fromhex("12" * 32)
        packet_id = sha(manifest_bytes)
        self.contract = {
            "schema": "arcpuzzles-full-assignment-v2",
            "assignment_id": "review-" + sha(bytes.fromhex(packet_id) + seed)[:16],
            "packet_id": packet_id, "seed": seed.hex(), "task_id": "fixture",
            "generator": row, "question": question,
            "baseline_sha256": {self.selected: sha(self.original[self.selected])},
        }
        self.archive_members = {"WORK/" + p: raw for p, raw in self.original.items()}
        self.archive_members.update(entries)
        self.archive_members["WORK/PACKET-MANIFEST.json"] = manifest_bytes
        self.write_archive()
        for name, raw in self.original.items():
            self.write(self.work / name, raw)
        for name, raw in entries.items():
            self.write(self.work.parent / name, raw)
        self.write(self.work / "PACKET-MANIFEST.json", manifest_bytes)
        self.write(self.work / "ASSIGNMENT.json", canonical_json(self.contract))
        self.write(self.work / ".review/baseline" / self.selected, self.original[self.selected])
        for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
            self.write(self.work / name, b"Synthetic fixture; no feedback.\n")
        self.write(self.work / "RESULTS.json", canonical_json({
            "completion_state": "blocked", "stopping_reason": "Synthetic fixture only.",
            "remaining_failures": [], "verification_commands": [],
        }))
        self.write(self.work / self.selected, b"VALUE = 2\n")

    @staticmethod
    def write(path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def write_archive(self):
        with zipfile.ZipFile(self.source_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in self.archive_members.items():
                info = zipfile.ZipInfo(name)
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, raw)

    def view(self):
        self.assertIsNotNone(importlib.util.find_spec("package_from_archive"),
                             "archive-backed source view has not been implemented")
        module = importlib.import_module("package_from_archive")
        return module.ArchiveBackedWorkspace(self.work, self.source_zip)

    def build(self, view, name="backed.zip"):
        return build_full_return(view.root, self.base / name)

    def test_missing_immutable_source_is_verified_without_materializing_it(self):
        disk = self.work / self.immutable
        disk.unlink()
        with self.view() as view:
            virtual = view.root / self.immutable
            self.assertTrue(virtual.is_file())
            self.assertEqual(virtual.read_bytes(), self.original[self.immutable])
            self.assertFalse(disk.exists())
            result = self.build(view)
            self.assertEqual(result["task_id"], "fixture")
            self.assertIn(self.immutable, view.fallback_reads)
        self.assertFalse(disk.exists())

    def test_materialized_tampering_is_never_replaced_with_archive_bytes(self):
        self.write(self.work / self.immutable, b"tampered\n")
        with self.view() as view:
            self.assertEqual((view.root / self.immutable).read_bytes(), b"tampered\n")
            with self.assertRaisesRegex(ValueError, "Changed or missing shared packet source"):
                self.build(view)
            self.assertNotIn(self.immutable, view.fallback_reads)

    def test_missing_selected_source_is_not_backed(self):
        (self.work / self.selected).unlink()
        with self.view() as view:
            self.assertFalse((view.root / self.selected).is_file())
            with self.assertRaisesRegex(ValueError, "Changed source outside allowed task scope"):
                self.build(view)

    def test_missing_frozen_baseline_still_fails(self):
        (self.work / ".review/baseline" / self.selected).unlink()
        with self.view() as view:
            with self.assertRaisesRegex(ValueError, "Frozen baseline changed"):
                self.build(view)

    def test_symlink_source_is_rejected(self):
        target = self.work / self.immutable
        target.unlink()
        real = self.base / "same-bytes.txt"
        real.write_bytes(self.original[self.immutable])
        target.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "[Ss]ymlink|Changed or missing shared packet source"):
            with self.view() as view:
                self.build(view)

    def test_missing_source_under_symlink_ancestor_is_rejected(self):
        target = self.work / self.immutable
        target.unlink()
        target.parent.rmdir()
        empty = self.base / "empty"
        empty.mkdir()
        target.parent.symlink_to(empty, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "[Ss]ymlink"):
            with self.view() as view:
                self.build(view)

    def test_existing_directory_is_not_treated_as_missing_source(self):
        target = self.work / self.immutable
        target.unlink()
        target.mkdir()
        with self.view() as view:
            self.assertFalse((view.root / self.immutable).is_file())
            with self.assertRaisesRegex(ValueError, "Changed or missing shared packet source"):
                self.build(view)

    def test_original_archive_corruption_fails_even_when_disk_copy_is_valid(self):
        self.archive_members["WORK/" + self.immutable] = b"wrong archive content\n"
        self.write_archive()
        with self.assertRaisesRegex(ValueError, "[Mm]anifest mismatch|[Hh]ash mismatch"):
            with self.view():
                pass

    def test_working_manifest_must_match_original_bytes(self):
        self.write(self.work / "PACKET-MANIFEST.json", b"{}")
        with self.assertRaisesRegex(ValueError, "[Mm]anifest"):
            with self.view():
                pass

    def test_undeclared_real_source_still_fails_official_builder(self):
        self.write(self.work / "repo/unexpected.py", b"UNEXPECTED = True\n")
        with self.view() as view:
            with self.assertRaisesRegex(ValueError, "Undeclared new source outside selected generator"):
                self.build(view)

    def test_missing_immutable_source_cannot_be_written_through_view(self):
        target = self.work / self.immutable
        target.unlink()
        with self.view() as view:
            with self.assertRaises(PermissionError):
                (view.root / self.immutable).write_bytes(b"replacement")
        self.assertFalse(target.exists())

    def test_official_return_zip_is_byte_identical_with_archive_fallback(self):
        ordinary = self.base / "ordinary.zip"
        build_full_return(self.work, ordinary)
        (self.work / self.immutable).unlink()
        with self.view() as view:
            result = self.build(view)
        backed = Path(result["zip"])
        self.assertEqual(ordinary.read_bytes(), backed.read_bytes())
        with zipfile.ZipFile(backed) as archive:
            self.assertIn("patches/source.patch", archive.namelist())
            results = json.loads(archive.read("RESULTS.json"))
            self.assertEqual(results["schema"], "arcpuzzles-full-results-v2")

    def test_cli_rejects_receipt_path_that_escapes_checks_before_loading_code(self):
        module = importlib.import_module("package_from_archive")
        escaping = self.work / "checks/../escaped.json"
        with self.assertRaisesRegex(ValueError, "under WORK/checks"):
            module.main([
                "--work", str(self.work), "--source-zip", str(self.source_zip),
                "--out", str(self.base / "output.zip"),
                "--verification-report", str(escaping),
            ])
        self.assertFalse((self.work / "escaped.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
