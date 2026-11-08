"""Fixture-only acceptance checks for the lossless evidence compression CLI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).with_name("pack_large_evidence.py").resolve()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class EvidenceToolTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), "compression CLI has not been implemented")
        self.temp = tempfile.TemporaryDirectory(prefix="evidence-tool-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "packet"
        (self.root / "checks/tooling").mkdir(parents=True)
        self.originals = {
            "checks/before/report.json": json.dumps(
                {"failures": ["retained-failure-\u2603"] * 900},
                ensure_ascii=False,
            ).encode(),
            "checks/census/instances.jsonl": (
                '{"input":[[1,0]],"failure":"keep every record"}\n' * 400
            ).encode(),
        }
        for name, raw in self.originals.items():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        (self.root / "checks/small.json").write_text("{}\n")
        (self.root / "checks/tooling/leave.json").write_bytes(b"x" * 300)
        self.backup = self.base / "raw"

    def cli(self, *args, good=True, root=None):
        command = [sys.executable, str(TOOL), "--packet-root",
                   str(root or self.root), *map(str, args)]
        try:
            run = subprocess.run(command, text=True, capture_output=True, timeout=8)
        except subprocess.TimeoutExpired:
            self.fail("evidence command blocked instead of rejecting the fixture")
        if good:
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            return json.loads(run.stdout)
        self.assertNotEqual(run.returncode, 0, run.stdout)
        return run

    def pack(self):
        return self.cli("pack", "--threshold-bytes", 128,
                        "--raw-backup", self.backup)

    def manifest(self):
        return json.loads((self.root / "checks/compressed/MANIFEST.json").read_text())

    def write_manifest(self, value):
        (self.root / "checks/compressed/MANIFEST.json").write_text(json.dumps(value))

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def test_list_and_dry_run_do_not_change_files(self):
        before = self.snapshot()
        listing = self.cli("list", "--threshold-bytes", 128)
        dry_run = self.cli("pack", "--dry-run", "--threshold-bytes", 128)
        self.assertEqual(listing["count"], 2)
        self.assertEqual(dry_run["files"], listing["files"])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.backup.exists())

    def test_pack_keeps_raw_backup_and_restores_exact_failures(self):
        result = self.pack()
        self.assertEqual(result["packed"], 2)
        manifest = self.manifest()
        self.assertEqual(manifest["count"], 2)
        for row in manifest["files"]:
            raw = self.originals[row["original_path"]]
            self.assertEqual(row["original_bytes"], len(raw))
            self.assertEqual(row["original_sha256"], sha(raw))
            self.assertEqual((self.backup / row["original_path"]).read_bytes(), raw)
            self.assertFalse((self.root / row["original_path"]).exists())
        self.assertEqual((self.root / "checks/small.json").read_text(), "{}\n")
        self.assertEqual((self.root / "checks/tooling/leave.json").stat().st_size, 300)
        self.assertTrue((self.root / "checks/compressed/RESTORE.md").is_file())
        destination = self.base / "restored"
        restored = self.cli("restore", "--destination", destination)
        self.assertEqual(restored["restored"], 2)
        for name, raw in self.originals.items():
            self.assertEqual((destination / name).read_bytes(), raw)

    def test_deterministic_gzip_and_manifest_across_roots(self):
        import shutil
        other = self.base / "second-packet"
        shutil.copytree(self.root, other)
        self.pack()
        self.cli("pack", "--threshold-bytes", 128, "--raw-backup",
                 self.base / "second-raw", root=other)
        first = self.manifest()
        self.assertEqual((self.root / "checks/compressed/MANIFEST.json").read_bytes(),
                         (other / "checks/compressed/MANIFEST.json").read_bytes())
        for row in first["files"]:
            self.assertEqual((self.root / row["compressed_path"]).read_bytes(),
                             (other / row["compressed_path"]).read_bytes())

    def test_verify_leaves_files_unchanged(self):
        self.pack()
        before = self.snapshot()
        self.assertEqual(self.cli("verify")["verified"], 2)
        self.assertEqual(self.snapshot(), before)

    def test_corruption_is_rejected_before_restore_writes(self):
        self.pack()
        row = self.manifest()["files"][0]
        path = self.root / row["compressed_path"]
        bad = bytearray(path.read_bytes())
        bad[len(bad) // 2] ^= 1
        path.write_bytes(bad)
        destination = self.base / "bad-output"
        self.cli("restore", "--destination", destination, good=False)
        self.assertFalse(destination.exists())

    def test_truncated_gzip_with_rebound_hash_is_rejected(self):
        self.pack()
        manifest = self.manifest()
        row = manifest["files"][0]
        path = self.root / row["compressed_path"]
        raw = path.read_bytes()[:-6]
        path.write_bytes(raw)
        row["compressed_bytes"], row["compressed_sha256"] = len(raw), sha(raw)
        manifest["compressed_bytes"] = sum(r["compressed_bytes"] for r in manifest["files"])
        self.write_manifest(manifest)
        self.cli("verify", good=False)

    def test_manifest_traversal_is_rejected(self):
        self.pack()
        manifest = self.manifest()
        manifest["files"][0]["original_path"] = "checks/../../escaped.json"
        self.write_manifest(manifest)
        destination = self.base / "unsafe-output"
        self.cli("restore", "--destination", destination, good=False)
        self.assertFalse(destination.exists())
        self.assertFalse((self.base / "escaped.json").exists())

    def test_restore_rejects_existing_files_without_overwriting(self):
        self.pack()
        destination = self.base / "existing"
        destination.mkdir()
        sentinel = destination / "keep.txt"
        sentinel.write_text("unchanged")
        self.cli("restore", "--destination", destination, good=False)
        self.assertEqual(sentinel.read_text(), "unchanged")
        self.assertEqual(list(destination.iterdir()), [sentinel])

    def test_restore_rejects_symlink_parent(self):
        self.pack()
        external = self.base / "external"
        external.mkdir()
        (self.base / "alias").symlink_to(external, target_is_directory=True)
        self.cli("restore", "--destination", self.base / "alias/out", good=False)
        self.assertEqual(list(external.iterdir()), [])

    def test_symlink_compressed_source_is_rejected(self):
        self.pack()
        row = self.manifest()["files"][0]
        path = self.root / row["compressed_path"]
        outside = self.base / "outside.gz"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        self.cli("verify", good=False)

    def test_casefold_collision_in_manifest_is_rejected(self):
        self.pack()
        manifest = self.manifest()
        row = dict(manifest["files"][0])
        row["original_path"] = row["original_path"].replace("report", "REPORT")
        row["compressed_path"] = row["compressed_path"].replace("report", "REPORT")
        manifest["files"].append(row)
        manifest["count"] += 1
        manifest["original_bytes"] += row["original_bytes"]
        manifest["compressed_bytes"] += row["compressed_bytes"]
        self.write_manifest(manifest)
        self.cli("verify", good=False)

    def test_pack_rejects_casefold_source_collision_before_mutation(self):
        path = self.root / "checks/before/REPORT.json"
        path.write_bytes(b'{"failure":"capitalized"}\n' * 100)
        before = self.snapshot()
        self.cli("pack", "--threshold-bytes", 128,
                 "--raw-backup", self.backup, good=False)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.backup.exists())

    def test_nonregular_compressed_source_is_rejected_without_blocking(self):
        import os
        self.pack()
        row = self.manifest()["files"][0]
        path = self.root / row["compressed_path"]
        path.unlink()
        os.mkfifo(path)
        self.cli("verify", good=False)

    def test_pack_rejects_symlink_input_and_internal_backup(self):
        before = self.snapshot()
        self.cli("pack", "--threshold-bytes", 128, "--raw-backup",
                 self.root / "raw", good=False)
        self.assertEqual(self.snapshot(), before)
        path = self.root / "checks/link.json"
        path.symlink_to(self.root / "checks/before/report.json")
        self.cli("pack", "--threshold-bytes", 128,
                 "--raw-backup", self.backup, good=False)
        self.assertTrue(path.is_symlink())
        self.assertFalse(self.backup.exists())

    def test_existing_raw_backup_is_not_overwritten(self):
        target = self.backup / "checks/before/report.json"
        target.parent.mkdir(parents=True)
        target.write_text("do not replace")
        self.cli("pack", "--threshold-bytes", 128,
                 "--raw-backup", self.backup, good=False)
        self.assertEqual(target.read_text(), "do not replace")
        self.assertEqual((self.root / "checks/before/report.json").read_bytes(),
                         self.originals["checks/before/report.json"])

    def test_pack_rejects_backup_paths_that_reenter_packet(self):
        renamed = self.base / "checks"
        self.root.rename(renamed)
        self.root = renamed
        before = self.snapshot()
        self.cli("pack", "--threshold-bytes", 128,
                 "--raw-backup", self.base, good=False)
        self.assertEqual(self.snapshot(), before)

    def test_second_pack_extends_manifest_without_losing_first_files(self):
        self.pack()
        extra = self.root / "checks/final.json"
        raw = b'{"failure":"later"}\n' * 100
        extra.write_bytes(raw)
        self.assertEqual(self.pack()["packed"], 1)
        self.assertEqual(self.manifest()["count"], 3)
        destination = self.base / "extended"
        self.assertEqual(self.cli("restore", "--destination", destination)["restored"], 3)
        self.assertEqual((destination / "checks/final.json").read_bytes(), raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceToolTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "schema": "review-evidence-tool-test-v1",
        "fixture_only": True,
        "actual_evidence_compressed": False,
        "cwd": str(Path.cwd()),
        "argv": [sys.executable, *sys.argv],
        "tool_sha256": sha(TOOL.read_bytes()) if TOOL.is_file() else None,
        "test_sha256": sha(Path(__file__).read_bytes()),
        "tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failures": [{"test": str(test), "detail": detail} for test, detail in result.failures],
        "errors": [{"test": str(test), "detail": detail} for test, detail in result.errors],
        "exit_code": 0 if result.wasSuccessful() else 1,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(report["exit_code"])
