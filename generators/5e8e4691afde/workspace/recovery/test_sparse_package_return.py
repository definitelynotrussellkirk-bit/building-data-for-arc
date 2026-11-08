"""Integration regressions using the unchanged official builder in a tiny packet.

Set ARC_SPARSE_SOURCE_ZIP to the original full review ZIP. The fixture reads
only official shared Python modules, never a supplied generator or reference.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


HERE = Path(__file__).resolve().parent
HELPER = HERE / "sparse_package_return.py"
SOURCE_ARCHIVE = Path(os.environ["ARC_SPARSE_SOURCE_ZIP"]) if os.environ.get(
    "ARC_SPARSE_SOURCE_ZIP") else None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()


class SparseReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SOURCE_ARCHIVE is None or not SOURCE_ARCHIVE.is_file():
            raise RuntimeError("Set ARC_SPARSE_SOURCE_ZIP to the original review ZIP")
        with zipfile.ZipFile(SOURCE_ARCHIVE) as original:
            cls.official = {name[5:]: original.read(name)
                            for name in original.namelist()
                            if name.startswith("WORK/repo/src/arcpuzzles/")
                            and name.endswith(".py")}
        if "repo/src/arcpuzzles/review_full_return.py" not in cls.official:
            raise RuntimeError("The source ZIP has no official full-return builder")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="arc-sparse-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "packet"
        self.root.mkdir()
        self.archive = self.base / "source.zip"
        self.out = self.base / "return.zip"
        self.source = "repo/generators/demo/generator.py"
        self.shared = "repo/src/arcpuzzles/review_full_return.py"
        self.canonical_path = "repo/shared/data/canonical/puzzles.jsonl"
        files = {**self.official,
                 self.source: b"value = 1\n",
                 "repo/generators/demo/notes.md": b"Initial notes.\n",
                 self.canonical_path: b'{"task_id":"demo","value":1}\n'
                                      b'{"task_id":"other","value":2}\n',
                 "repo/shared/never-materialized.txt": b"Immutable original.\n"}
        row = {"generator": self.source,
               "generator_sha256": sha(files[self.source]),
               "rule_task_id": "demo"}
        question = {"id": "fixture", "text": "Record this bounded review."}
        self.manifest = {"schema": "arcpuzzles-full-packet-v2",
                         "layout": {"workspace": "WORK", "entry_files": {
                             "START-HERE.md": sha(b"Synthetic fixture.\n"),
                             "review.py": sha(b"# Synthetic launcher.\n")}},
                         "main_ids": ["demo"], "all_ids": ["demo"],
                         "generators": {"demo": row}, "questions": [question],
                         "files": {name: sha(raw) for name, raw in files.items()}}
        self.contents = {"START-HERE.md": b"Synthetic fixture.\n",
                         "review.py": b"# Synthetic launcher.\n",
                         "WORK/PACKET-MANIFEST.json": canonical(self.manifest),
                         **{"WORK/" + name: raw for name, raw in files.items()}}
        self.rewrite_archive()
        baseline_names = [self.source, "repo/generators/demo/notes.md",
                          self.canonical_path]
        self.contract = {"schema": "arcpuzzles-full-assignment-v2",
                         "packet_id": sha(canonical(self.manifest)),
                         "assignment_id": "review-0123456789abcdef",
                         "task_id": "demo", "generator": row,
                         "question": question,
                         "baseline_sha256": {name: sha(files[name])
                                             for name in baseline_names}}
        self.entries = ["START-HERE.md", "WORK/PACKET-MANIFEST.json",
                        "WORK/" + self.shared,
                        *("WORK/" + name for name in baseline_names)]
        for name in self.entries:
            self.write(name, self.contents[name])
        for name in baseline_names:
            self.write("WORK/.review/baseline/" + name, files[name])
        self.write("WORK/ASSIGNMENT.json", canonical(self.contract))
        for doc in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md",
                    "FEEDBACK_TO_CODEX.md"):
            self.write("WORK/" + doc, b"Synthetic test record.\n")
        self.write("WORK/RESULTS.json", canonical({
            "completion_state": "in_progress", "stopping_reason": "Test fixture."}))
        self.write_inventory()
        self.write("WORK/" + self.source, b"value = 2\n")

    def write(self, name, raw):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    def rewrite_archive(self):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in self.contents.items():
                info = zipfile.ZipInfo(name)
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, raw)

    def write_inventory(self, digest=None):
        self.write("MATERIALIZED.json", canonical({
            "schema": "arc-review-materialization-v1",
            "archive_sha256": digest or sha(self.archive.read_bytes()),
            "entries": self.entries,
        }))

    def refresh_manifest(self):
        raw = canonical(self.manifest)
        self.contents["WORK/PACKET-MANIFEST.json"] = raw
        self.rewrite_archive()
        self.write("WORK/PACKET-MANIFEST.json", raw)
        self.contract["packet_id"] = sha(raw)
        self.write("WORK/ASSIGNMENT.json", canonical(self.contract))
        self.write_inventory()

    def run_helper(self):
        return subprocess.run([
            sys.executable, "-B", str(HELPER), "--archive", str(self.archive),
            "--root", str(self.root), "--out", str(self.out),
        ], capture_output=True, text=True, timeout=30)

    def assert_rejected(self, message):
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0, result.stdout[:400])
        self.assertIn(message, result.stderr)
        self.assertFalse(self.out.exists(), "Rejected return was retained")
        return result

    def test_normal_delta_uses_actual_bytes_and_leaves_shared_files_unmaterialized(self):
        # Archive fallback masking the edited disk source would lose this hunk.
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["patch_paths"], [self.source])
        self.assertEqual(report["completion_state"], "in_progress")
        with zipfile.ZipFile(self.out) as archive:
            patch = archive.read("patches/source.patch").decode()
        self.assertIn("-value = 1\n+value = 2\n", patch)
        self.assertFalse((self.root / "WORK/repo/shared/never-materialized.txt").exists())

    def test_mutated_shared_python_is_rejected_without_executing_it(self):
        self.write("WORK/" + self.shared,
                   b'raise RuntimeError("EXECUTED_MUTATED_SHARED_SOURCE")\n')
        result = self.assert_rejected("Changed or missing shared packet source")
        self.assertNotIn("EXECUTED_MUTATED_SHARED_SOURCE", result.stderr)

    def test_deleted_materialized_source_cannot_fall_back_to_archive(self):
        (self.root / "WORK" / self.source).unlink()
        self.assert_rejected("Materialized file missing")

    def test_deleted_materialized_shared_file_is_rejected(self):
        (self.root / "WORK" / self.shared).unlink()
        self.assert_rejected("Materialized file missing")

    def test_materialized_symlink_is_rejected(self):
        target = self.root / "WORK" / self.source
        target.unlink()
        target.symlink_to(self.base / "outside.py")
        self.assert_rejected("Symlink")

    def test_new_evidence_symlink_is_rejected(self):
        self.write("WORK/checks/result.txt", b"result\n")
        (self.root / "WORK/checks/link.txt").symlink_to("result.txt")
        self.assert_rejected("Symlink")

    def test_symlink_ancestor_is_rejected(self):
        target = self.root / "WORK/.review/baseline/repo/generators/demo"
        target.rename(self.base / "frozen")
        target.symlink_to(self.base / "frozen", target_is_directory=True)
        self.assert_rejected("Symlink")

    def test_archive_digest_mismatch_is_rejected(self):
        self.write_inventory(digest="0" * 64)
        self.assert_rejected("Archive SHA-256 mismatch")

    def test_manifest_hash_mismatch_is_rejected_even_when_archive_digest_matches(self):
        self.contents["WORK/repo/shared/never-materialized.txt"] = b"altered\n"
        self.rewrite_archive()
        self.write_inventory()
        self.assert_rejected("Manifest hash mismatch")

    def test_local_manifest_cannot_replace_archive_manifest(self):
        changed = dict(self.manifest, main_ids=["other"])
        self.write("WORK/PACKET-MANIFEST.json", canonical(changed))
        self.assert_rejected("Packet manifest differs from original archive")

    def test_unallowed_new_source_is_rejected_by_official_guard(self):
        self.write("WORK/repo/new_shared.py", b"new = True\n")
        self.assert_rejected("Undeclared new source outside selected generator")

    def test_allowed_new_workspace_source_is_returned(self):
        self.write("WORK/repo/generators/demo/workspace/helper.py", b"print('fixture')\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["patch_paths"], [self.source,
            "repo/generators/demo/workspace/helper.py"])

    def test_frozen_baseline_hash_guard_is_unchanged(self):
        self.write("WORK/.review/baseline/" + self.source, b"value = 99\n")
        self.assert_rejected("Frozen baseline changed")

    def test_executable_source_guard_is_unchanged(self):
        (self.root / "WORK" / self.source).chmod(0o755)
        self.assert_rejected("Unsafe changed source")

    def test_unrelated_canonical_row_guard_is_unchanged(self):
        self.write("WORK/" + self.canonical_path,
                   b'{"task_id":"demo","value":1}\n'
                   b'{"task_id":"other","value":9}\n')
        self.assert_rejected("Patch changed an unrelated canonical row")

    def test_unrecorded_materialization_is_rejected(self):
        name = "WORK/repo/shared/never-materialized.txt"
        self.write(name, self.contents[name])
        self.assert_rejected("Archive file on disk is absent from materialization inventory")

    def test_archive_file_missing_from_manifest_is_rejected(self):
        self.contents["WORK/repo/unmanifested.py"] = b"extra = True\n"
        self.rewrite_archive()
        self.write_inventory()
        self.assert_rejected("Archive/manifest file set differs")

    def test_archive_traversal_member_is_rejected(self):
        self.contents["WORK/../escape.txt"] = b"escape\n"
        self.rewrite_archive()
        self.write_inventory()
        self.assert_rejected("Unsafe archive path")

    def test_inventory_unknown_member_is_rejected(self):
        self.entries.append("WORK/repo/not-in-source.py")
        self.write_inventory()
        self.assert_rejected("Inventory path is not an original archive file")

    def test_outer_entry_digest_is_verified_against_manifest(self):
        self.contents["review.py"] = b"# Altered unmaterialized launcher.\n"
        self.rewrite_archive()
        self.write_inventory()
        self.assert_rejected("Manifest hash mismatch: review.py")

    def test_layout_workspace_must_be_work(self):
        self.manifest["layout"]["workspace"] = "OTHER"
        self.refresh_manifest()
        self.assert_rejected("Packet layout.workspace must be WORK")

    def test_layout_entry_file_set_must_be_exact(self):
        self.manifest["layout"]["entry_files"]["unexpected.py"] = "0" * 64
        self.refresh_manifest()
        self.assert_rejected("Packet layout.entry_files must contain exactly")


if __name__ == "__main__":
    unittest.main()
