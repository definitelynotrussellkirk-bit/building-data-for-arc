from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve()
PACKAGE = HERE.parents[2]
TOOL = HERE.parents[1] / "verify_response.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("verify_response", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_zip(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


class VerifyResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_current_directory_is_clean(self):
        report = self.tool.verify_path(PACKAGE)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["facts"]["evidence_files"], 361)
        self.assertEqual(report["facts"]["patch_paths"], 4)

    def test_packaged_zip_is_clean(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "package.zip"
            make_zip(PACKAGE, path)
            report = self.tool.verify_path(path)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["facts"]["assignment_id"], "review-484b6daa042b533a")

    def test_root_evidence_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "package"
            shutil.copytree(PACKAGE, root)
            (root / "REVIEW.md").write_text((root / "REVIEW.md").read_text() + "\ntamper\n")
            report = self.tool.verify_path(root)
            self.assertTrue(any("root hash mismatch REVIEW.md" in x for x in report["issues"]))

    def test_evidence_manifest_count_tamper_is_detected_after_rebinding_root_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "package"
            shutil.copytree(PACKAGE, root)
            manifest_path = root / "EVIDENCE-BUNDLE.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["count"] += 1
            manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
            intake_path = root / "INTAKE.json"
            intake = json.loads(intake_path.read_text())
            intake["evidence_sha256"]["EVIDENCE-BUNDLE.json"] = sha256(manifest_path)
            intake_path.write_text(json.dumps(intake, sort_keys=True, separators=(",", ":")))
            report = self.tool.verify_path(root)
            self.assertTrue(any("evidence count" in x for x in report["issues"]))

    def test_declared_patch_path_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "package"
            shutil.copytree(PACKAGE, root)
            intake_path = root / "INTAKE.json"
            intake = json.loads(intake_path.read_text())
            intake["changed_paths"] = intake["changed_paths"][:-1]
            intake_path.write_text(json.dumps(intake, sort_keys=True, separators=(",", ":")))
            report = self.tool.verify_path(root)
            self.assertTrue(any("patch paths differ" in x for x in report["issues"]))


    def test_original_worktree_helper_checks_hashes_and_patch_applicability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "work"
            (root / "repo").mkdir(parents=True)
            source = root / "repo/a.txt"
            source.write_text("old\n")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            assignment = {"baseline_sha256": {"repo/a.txt": sha256(source)}}
            patch = (
                "diff --git a/repo/a.txt b/repo/a.txt\n"
                "--- a/repo/a.txt\n"
                "+++ b/repo/a.txt\n"
                "@@ -1 +1 @@\n"
                "-old\n"
                "+new\n"
            ).encode()
            issues = []
            facts = {}
            self.tool._verify_original_worktree(root, assignment, patch, issues, facts)
            self.assertEqual(issues, [])
            self.assertEqual(facts["original_baseline_files_checked"], 1)
            self.assertEqual(facts["git_apply_check_exit_code"], 0)
            self.assertEqual(source.read_text(), "old\n")

    def test_unsafe_zip_member_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "unsafe.zip"
            make_zip(PACKAGE, path)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("../escape.txt", "no")
            report = self.tool.verify_path(path)
            self.assertTrue(any("unsafe ZIP path" in x for x in report["issues"]))


if __name__ == "__main__":
    unittest.main()
