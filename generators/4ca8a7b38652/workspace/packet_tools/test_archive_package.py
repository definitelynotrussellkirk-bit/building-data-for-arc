"""Synthetic source-ZIP packaging regressions; no real puzzle source reads."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = next((p / "src" for p in HERE.parents if (p / "src/arcpuzzles/review_full_return.py").is_file()), None)
CANDIDATE = HERE / "review_full_return_sourcezip.py"
if SOURCE:
    sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(HERE))


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ArchivePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="archive-package-tests-")
        self.root = Path(self.temp.name)
        self.work = self.root / "checkout/WORK"
        self.work.mkdir(parents=True)
        self.archive = self.root / "source.zip"
        self.output = self.root / "return.zip"
        self.tid = "0123456789ab"
        self.gen = f"repo/generators/{self.tid}/generator.py"
        self.shared = "repo/shared/support.py"
        self.bodies = {
            "START-HERE.md": b"Synthetic packet.\n",
            "review.py": b"# synthetic entrypoint\n",
            "WORK/" + self.gen: b"value = 1\n",
            "WORK/" + self.shared: b"support = 7\n",
        }
        row = {"generator": f"generators/{self.tid}/generator.py", "generator_sha256": sha(b"value = 1\n"),
               "rule_task_id": self.tid, "rule_hash": "test", "approved": False}
        question = {"id": "synthetic-question", "version": 1, "sha256": "0" * 64}
        self.manifest = {
            "schema": "arcpuzzles-full-packet-v2", "all_ids": [self.tid], "main_ids": [self.tid],
            "generators": {self.tid: row}, "questions": [question],
            "layout": {"workspace": "WORK", "entry_files": {
                n: sha(self.bodies[n]) for n in ("START-HERE.md", "review.py")}},
            "files": {n.removeprefix("WORK/"): sha(raw) for n, raw in self.bodies.items() if n.startswith("WORK/")},
        }
        self.bodies["WORK/PACKET-MANIFEST.json"] = canonical(self.manifest)
        self.write_zip()
        for name, raw in self.bodies.items():
            if name != "WORK/" + self.shared:
                target = self.work.parent / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        contract = {"schema": "arcpuzzles-full-assignment-v2", "assignment_id": "review-0000000000000001",
                    "packet_id": sha(canonical(self.manifest)), "task_id": self.tid, "generator": row,
                    "question": question, "seed": "00" * 32,
                    "baseline_sha256": {self.gen: sha(b"value = 1\n")}}
        (self.work / "ASSIGNMENT.json").write_bytes(canonical(contract))
        frozen = self.work / ".review/baseline" / self.gen
        frozen.parent.mkdir(parents=True)
        frozen.write_bytes(b"value = 1\n")
        (self.work / self.gen).write_bytes(b"value = 2\n")
        for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
            (self.work / name).write_text("# Synthetic fixture\nTest evidence only.\n")
        (self.work / "RESULTS.json").write_bytes(canonical({
            "completion_state": "blocked", "stopping_reason": "Synthetic fixture, no puzzle tests.",
            "remaining_failures": [], "verification_commands": []}))

    def tearDown(self):
        self.temp.cleanup()

    def write_zip(self):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in self.bodies.items():
                archive.writestr(name, raw)

    def build(self, source=True):
        self.assertTrue(CANDIDATE.is_file(), "copied source-ZIP builder has not been implemented")
        self.assertIsNotNone(SOURCE, "official runtime source is required for the synthetic builder integration")
        spec = importlib.util.spec_from_file_location("arcpuzzles._sourcezip_candidate_test", CANDIDATE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.build_full_return(self.work, self.output, source_zip=self.archive if source else None)

    def test_cli_emits_independent_official_validation(self):
        env = dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, str(HERE / "package_sourcezip.py"), str(self.work),
                                 "--source-zip", str(self.archive), "--out", str(self.output)],
                                env=env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["local_proposal"])
        self.assertTrue(output["source_zip_mode"])
        self.assertEqual(output["official_validation"]["patch_paths"], [self.gen])

    def test_sparse_success_passes_unchanged_official_validator(self):
        result = self.build()
        from arcpuzzles.review_full_return import validate_full_return
        with zipfile.ZipFile(self.output) as archive:
            checked = validate_full_return(archive, self.manifest)
            receipt = json.loads(archive.read("checks/packet-source/archive-backed-verification.json"))
        self.assertEqual(result["patch_paths"], [self.gen])
        self.assertEqual(checked["patch_paths"], [self.gen])
        self.assertEqual(receipt["archive_body_count_verified"], 5)
        self.assertEqual(receipt["missing_protected_sources_supplied_by_archive"], 1)

    def test_omitting_flag_retains_original_missing_source_failure(self):
        with self.assertRaisesRegex(ValueError, "Changed or missing shared packet source"):
            self.build(source=False)
        self.assertFalse(self.output.exists())

    def test_default_branch_still_packages_complete_original_inventory(self):
        path = self.work / self.shared
        path.parent.mkdir(parents=True)
        path.write_bytes(b"support = 7\n")
        result = self.build(source=False)
        self.assertEqual(result["patch_paths"], [self.gen])
        with zipfile.ZipFile(self.output) as archive:
            self.assertNotIn("checks/packet-source/archive-backed-verification.json", archive.namelist())

    def test_corrupt_omitted_source_is_rejected(self):
        self.bodies["WORK/" + self.shared] = b"corrupt source\n"
        self.write_zip()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_missing_original_archive_member_is_rejected(self):
        del self.bodies["WORK/" + self.shared]
        self.write_zip()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_materialized_shared_drift_is_rejected(self):
        path = self.work / self.shared
        path.parent.mkdir(parents=True)
        path.write_bytes(b"drifted live source\n")
        with self.assertRaisesRegex(ValueError, "protected source"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_undeclared_live_shared_file_is_rejected(self):
        path = self.work / "repo/shared/new-helper.py"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"unapproved = True\n")
        with self.assertRaisesRegex(ValueError, "Undeclared"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_live_shared_symlink_is_rejected(self):
        path = self.work / self.shared
        path.parent.mkdir(parents=True)
        destination = self.root / "outside.py"
        destination.write_bytes(b"support = 7\n")
        path.symlink_to(destination)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_undeclared_cache_symlink_is_rejected_before_cache_exclusion(self):
        path = self.work / "repo/shared/cache.pyc"
        path.parent.mkdir(parents=True)
        destination = self.root / "outside-cache.pyc"
        destination.write_bytes(b"synthetic cache bytes\n")
        path.symlink_to(destination)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_live_manifest_must_be_byte_exact_original(self):
        with (self.work / "PACKET-MANIFEST.json").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.build()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
