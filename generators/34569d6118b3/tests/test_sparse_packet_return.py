"""Focused packaging gates; each fixture is removed before the next test.

Run from WORK/repo with Python's standard library:
  python3 -B -m unittest discover -s generators/34569d6118b3/tests \
    -p test_sparse_packet_return.py -v
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile


REPO = Path(__file__).resolve().parents[3]
HELPER = Path(__file__).resolve().parents[1] / "workspace/tools/package_sparse_return.py"
SPEC = importlib.util.spec_from_file_location("sparse_packet_return", HELPER)
sparse = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sparse)
TASK = "aaaa00000003"
GENERATOR = f"repo/generators/{TASK}/generator.py"
NOTES = f"repo/generators/{TASK}/notes.md"
SHARED = "repo/shared/untouched.txt"


def issued_code():
    """Only the issued builder's transitive local import closure, about 20 files."""
    source = REPO / "src/arcpuzzles"
    pending, read = {"__init__", "review_full_return"}, {}
    while pending:
        name = pending.pop()
        if name in read:
            continue
        raw = (source / (name + ".py")).read_bytes()
        read[name] = raw
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                if node.module:
                    pending.add(node.module.split(".")[0])
                else:
                    pending.update(alias.name for alias in node.names)
    return {f"repo/src/arcpuzzles/{name}.py": raw for name, raw in read.items()}


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="sparse-return-test-") as temporary:
        base = Path(temporary)
        work = base / "WORK"
        work.mkdir()
        source = {**issued_code(), GENERATOR: b"VERSION = 'original'\n",
                  NOTES: b"Original notes.\n", SHARED: b"Shared unchanged bytes.\n"}
        generator = {"generator": f"generators/{TASK}/generator.py",
                     "generator_sha256": sparse.sha(source[GENERATOR]),
                     "rule_task_id": TASK, "rule_hash": "abc", "approved": True}
        question = {"id": "q", "version": 1, "sha256": "0" * 64}
        entries = {"START-HERE.md": b"Fixture-only entry document.\n",
                   "review.py": b"# Fixture-only outer entry point.\n"}
        manifest = {"schema": "arcpuzzles-full-packet-v2",
                    "files": {name: sparse.sha(raw) for name, raw in source.items()},
                    "layout": {"workspace": "WORK", "entry_files": {
                        name: sparse.sha(raw) for name, raw in entries.items()}},
                    "main_ids": [TASK], "all_ids": [TASK],
                    "generators": {TASK: generator}, "questions": [question]}
        raw_manifest = sparse.canonical(manifest)
        packet_id = sparse.sha(raw_manifest)
        baseline = {name: manifest["files"][name] for name in (GENERATOR, NOTES)}
        contract = {"schema": "arcpuzzles-full-assignment-v2", "task_id": TASK,
                    "assignment_id": "review-0123456789abcdef", "packet_id": packet_id,
                    "baseline_sha256": baseline, "generator": generator,
                    "question": question, "seed": "0" * 64}
        overlay = {"PACKET-MANIFEST.json": raw_manifest,
                   "ASSIGNMENT.json": sparse.canonical(contract),
                   GENERATOR: source[GENERATOR], NOTES: b"Actual authored correction.\n",
                   "RESULTS.json": sparse.canonical({"completion_state": "complete",
                                                     "stopping_reason": "fixture only"}),
                   ".review/materialized-files.json": sparse.canonical({
                       "schema": sparse.SCHEMA, "packet_manifest_sha256": packet_id,
                       "paths": [GENERATOR, NOTES]})}
        for name in sparse.ROOT_DOCUMENTS:
            if name in {"REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"}:
                overlay[name] = b"Fixture report, not a claim about the real task.\n"
        for name in baseline:
            overlay[".review/baseline/" + name] = source[name]
        for name, raw in overlay.items():
            destination = work / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        original = base / "issued.zip"
        with zipfile.ZipFile(original, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in {**source, "PACKET-MANIFEST.json": raw_manifest}.items():
                archive.writestr("WORK/" + name, raw)
            for name, raw in entries.items():
                archive.writestr(name, raw)
        yield base, work, original, manifest, source, overlay


class SparseReturnTests(unittest.TestCase):
    def test_exact_zip_matches_normal_builder_and_retains_shared_bytes(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            # Checks preserve every byte, including suffixes ignored for source.
            for name, raw in {"checks/raw.pyc": b"\0binary check evidence",
                              "checks/.cache/detail.txt": b"Raw check evidence\r\n"}.items():
                overlay[name] = raw
                destination = work / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
            sparse_result = sparse.package(original, work, base / "sparse.zip")
            self.assertFalse((work / SHARED).exists())
            full = base / "full"
            for name, raw in {**source, **overlay}.items():
                destination = full / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
            with sparse.issued_imports(source):
                from arcpuzzles.review_full_return import build_full_return
                normal_result = build_full_return(full, base / "normal.zip")
            self.assertEqual(Path(sparse_result["zip"]).read_bytes(),
                             Path(normal_result["zip"]).read_bytes())
            self.assertEqual(sparse_result["patch_paths"], [NOTES])
            self.assertEqual(sparse_result["completion_state"], "complete")

    def test_undeclared_shared_source_is_rejected_by_original_builder(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            target = work / "repo/rogue.py"
            target.write_text("SHARED_EDIT = True\n")
            with self.assertRaisesRegex(ValueError, "Undeclared new source"):
                sparse.package(original, work, base / "invalid.zip")
            self.assertFalse((base / "invalid.zip").exists())

    def test_missing_materialized_shared_source_cannot_fall_back(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            inventory = work / ".review/materialized-files.json"
            data = json.loads(inventory.read_text())
            data["paths"].append(SHARED)
            inventory.write_bytes(sparse.canonical(data))
            with self.assertRaisesRegex(ValueError, "Missing materialized"):
                sparse.package(original, work, base / "invalid.zip")
            self.assertFalse((base / "invalid.zip").exists())

    def test_changed_shared_source_is_rejected(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            target = work / SHARED
            target.parent.mkdir(parents=True)
            target.write_bytes(b"Unallowed edit\n")
            with self.assertRaisesRegex(ValueError, "Changed shared"):
                sparse.package(original, work, base / "invalid.zip")

    def test_unmaterialized_source_cannot_be_shadowed_by_empty_directory(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            (work / SHARED).mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "Directory shadows issued packet file"):
                sparse.package(original, work, base / "invalid.zip")
            self.assertFalse((base / "invalid.zip").exists())

    def test_missing_selected_source_is_not_restored(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            (work / GENERATOR).unlink()
            with self.assertRaisesRegex(ValueError, "Missing materialized or selected"):
                sparse.package(original, work, base / "invalid.zip")

    def test_missing_and_changed_frozen_baselines_fail(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            baseline = work / ".review/baseline" / GENERATOR
            baseline.unlink()
            with self.assertRaisesRegex(ValueError, "Missing frozen baseline"):
                sparse.package(original, work, base / "invalid.zip")
            baseline.write_bytes(b"Altered baseline")
            with self.assertRaisesRegex(ValueError, "Frozen baseline changed"):
                sparse.package(original, work, base / "invalid.zip")

    def test_original_hash_corruption_fails(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            bad = base / "bad-original.zip"
            with zipfile.ZipFile(original) as before, zipfile.ZipFile(bad, "w") as after:
                for item in before.infolist():
                    raw = b"corrupt" if item.filename == "WORK/" + SHARED else before.read(item)
                    after.writestr(item, raw)
            with self.assertRaisesRegex(ValueError, "Original manifest hash mismatch"):
                sparse.package(bad, work, base / "invalid.zip")

    def test_outer_entry_hash_corruption_fails(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            bad = base / "bad-entry.zip"
            with zipfile.ZipFile(original) as before, zipfile.ZipFile(bad, "w") as after:
                for item in before.infolist():
                    raw = b"altered launcher" if item.filename == "review.py" else before.read(item)
                    after.writestr(item, raw)
            with self.assertRaisesRegex(ValueError, "Original entry-file hash mismatch"):
                sparse.package(bad, work, base / "invalid.zip")

    def test_undeclared_outer_file_is_rejected(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            with zipfile.ZipFile(original, "a") as archive:
                archive.writestr("unexpected.txt", b"unbound outer bytes")
            with self.assertRaisesRegex(ValueError, "Original ZIP inventory differs"):
                sparse.package(original, work, base / "invalid.zip")

    def test_zip_traversal_duplicate_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sparse-unsafe-test-") as temporary:
            for attack in ("traversal", "duplicate", "symlink"):
                with self.subTest(attack=attack):
                    bad = Path(temporary) / "bad.zip"
                    with warnings.catch_warnings(), zipfile.ZipFile(bad, "w") as archive:
                        warnings.simplefilter("ignore", UserWarning)
                        if attack == "traversal":
                            archive.writestr("WORK/../escape", b"bad")
                        elif attack == "duplicate":
                            archive.writestr("WORK/a", b"one")
                            archive.writestr("WORK/a", b"two")
                        else:
                            item = zipfile.ZipInfo("WORK/link")
                            item.external_attr = (stat.S_IFLNK | 0o777) << 16
                            archive.writestr(item, b"outside")
                    with self.assertRaises(ValueError):
                        sparse.read_issued(bad)
                    bad.unlink()

    def test_local_symlink_cannot_hide_in_archive_overlay(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            target = work / NOTES
            target.unlink()
            target.symlink_to(work / GENERATOR)
            with self.assertRaisesRegex(ValueError, "Symlink"):
                sparse.package(original, work, base / "invalid.zip")

    def test_invalid_results_are_rejected_by_original_validator(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            (work / "RESULTS.json").write_text('{"completion_state":"invented-success"}')
            with self.assertRaisesRegex(ValueError, "Invalid result identity or completion state"):
                sparse.package(original, work, base / "invalid.zip")
            self.assertFalse((base / "invalid.zip").exists())

    def test_missing_evidence_is_rejected_by_original_builder(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            (work / "RESULTS.json").write_bytes(sparse.canonical({
                "verification_commands": [{"cwd": "repo", "argv": ["python3", "probe.py"],
                                            "evidence_paths": ["checks/missing.json"]}]}))
            with self.assertRaisesRegex(ValueError, "checks/missing.json"):
                sparse.package(original, work, base / "invalid.zip")
            self.assertFalse((base / "invalid.zip").exists())

    def test_existing_output_is_not_overwritten(self):
        with fixture() as (base, work, original, manifest, source, overlay):
            out = base / "existing.zip"
            out.write_bytes(b"Keep this user's file")
            with self.assertRaises(FileExistsError):
                sparse.package(original, work, out)
            self.assertEqual(out.read_bytes(), b"Keep this user's file")


if __name__ == "__main__":
    unittest.main()
