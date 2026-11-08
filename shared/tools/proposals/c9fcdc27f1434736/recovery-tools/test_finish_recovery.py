"""Recovery orchestration tests use synthetic packets, never ARC task data."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
import zipfile


HERE = Path(__file__).resolve().parent
TASK = "aaaaaaaaaaaa"
GENERATOR = f"repo/generators/{TASK}/generator.py"
OLD = b"VALUE = 'original'\n"
NEW = b"VALUE = 'repaired'\n"
PATCH = (f"diff --git a/{GENERATOR} b/{GENERATOR}\n"
         f"--- a/{GENERATOR}\n+++ b/{GENERATOR}\n@@ -1 +1 @@\n"
         "-VALUE = 'original'\n+VALUE = 'repaired'\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get("ZIP_PREFLIGHT_TEST_TMPDIR", str(HERE))
        self.temporary = tempfile.TemporaryDirectory(prefix="recovery-test-", dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def tool(self):
        self.assertTrue((HERE / "finish_recovery.py").is_file(), "Recovery helper is not implemented")
        return importlib.import_module("finish_recovery")

    def fixture(self, native_gate_exit=0):
        """A tiny fake native lifecycle, explicitly not an ARCpuzzles validation."""
        seed = "11" * 32
        assignment_base = {
            "schema": "arcpuzzles-full-assignment-v2", "assignment_id": "review-" + "22" * 8,
            "seed": seed, "task_id": TASK,
            "generator": {"generator": GENERATOR.removeprefix("repo/"),
                          "generator_sha256": digest(OLD), "rule_task_id": TASK},
            "baseline_sha256": {GENERATOR: digest(OLD)},
        }
        draw = f'''from pathlib import Path
import hashlib, json, shutil
BASE = {assignment_base!r}
def draw_main(root, seed=None):
    assert seed.hex() == BASE['seed']
    contract = dict(BASE, packet_id=hashlib.sha256((root/'PACKET-MANIFEST.json').read_bytes()).hexdigest())
    for name, expected in contract['baseline_sha256'].items():
        raw = (root/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
        target = root/'.review/baseline'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (root/'ASSIGNMENT.json').write_text(json.dumps(contract, sort_keys=True, indent=2)+'\\n')
    (root/'RESULTS.json').write_text('{{}}\\n')
    return contract
def draw_audit(root, seed=None):
    assert seed.hex() == '33' * 32
    result = {{'schema': 'arcpuzzles-full-audit-v3', 'seed': seed.hex(),
              'packet_id': hashlib.sha256((root/'PACKET-MANIFEST.json').read_bytes()).hexdigest(),
              'targets': []}}
    (root/'AUDIT_ASSIGNMENT.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\\n')
    return result
'''.encode()
        verify = b'''from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parent
assert sys.argv[1:] == ['verify']
for name, expected in json.loads((root/'WORK/PACKET-MANIFEST.json').read_text())['files'].items():
    assert hashlib.sha256((root/'WORK'/name).read_bytes()).hexdigest() == expected
print('SYNTHETIC PACKET VERIFIED')
'''
        packager = f'''from pathlib import Path
import argparse, hashlib, json, zipfile
root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert hashlib.sha256((root/{GENERATOR!r}).read_bytes()).hexdigest() == {digest(NEW)!r}
assert (root/'.review/baseline'/{GENERATOR!r}).read_bytes() == {OLD!r}
assert (root/'checks/focused-ran.txt').read_text() == 'yes'
with zipfile.ZipFile(args.out, 'x') as output:
    output.writestr('patches/source.patch', {PATCH!r})
    output.writestr('RESULTS.json', (root/'RESULTS.json').read_bytes())
    output.writestr('SYNTHETIC-TEST-FIXTURE.txt', 'This is not a real official review return.')
print(args.out)
'''.encode()
        entries = {
            "START-HERE.md": b"Synthetic recovery fixture only.\n",
            "review.py": verify,
            "WORK/" + GENERATOR: OLD,
            "WORK/repo/shared/data/canonical/puzzles.jsonl": b"synthetic ledger only\n",
            "WORK/repo/src/arcpuzzles/__init__.py": b"",
            "WORK/repo/src/arcpuzzles/review_full_draw.py": draw,
            "WORK/setup_racket.py": b"print('SYNTHETIC SETUP')\n",
            "WORK/run_with_racket.py": f"import sys\nassert 'task_tests' in sys.argv\nprint('SYNTHETIC NATIVE PREREQUISITE/TEST GATE')\nraise SystemExit({native_gate_exit})\n".encode(),
            "WORK/package_return.py": packager,
        }
        manifest = {"files": {name.removeprefix("WORK/"): digest(raw)
                              for name, raw in entries.items() if name.startswith("WORK/")}}
        manifest_raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        entries["WORK/PACKET-MANIFEST.json"] = manifest_raw
        assignment = dict(assignment_base, packet_id=digest(manifest_raw))
        archive_path = self.root / "original.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for name, raw in entries.items():
                archive.writestr(name, raw)
        recovery = self.root / "RECOVERY"
        recovery.mkdir()
        payload = {
            "contracts/ASSIGNMENT.json": json_bytes(assignment),
            "provenance/scoped_extraction_receipt.json": json_bytes({"archive_sha256": digest(archive_path.read_bytes())}),
            "payload/RESULTS.json": json_bytes({"completion_state": "blocked", "stopping_reason": "Awaiting replay", "verification_commands": []}),
        }
        for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
            payload["payload/" + name] = b"Synthetic reviewer report.\n"
        for name, raw in payload.items():
            path = recovery / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (recovery / "source.patch").write_bytes(PATCH)
        config = {
            "schema": "arcpuzzles-recovery-v1", "original_archive_sha256": digest(archive_path.read_bytes()),
            "patch_sha256": digest(PATCH), "final_generator_sha256": digest(NEW),
            "packet_id": assignment["packet_id"], "assignment_id": assignment["assignment_id"], "task_id": TASK,
            "files": {name: digest(raw) for name, raw in payload.items()},
            "reserve_bytes": 0, "reserve_inodes": 0,
            "focused_tests": [{"cwd": "WORK/repo", "argv": ["{python}", "-B", "-c",
                "from pathlib import Path; p=Path('../checks'); p.mkdir(exist_ok=True); (p/'focused-ran.txt').write_text('yes')"],
                "timeout_seconds": 10}],
        }
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        return recovery, archive_path, self.root / "reconstructed", config

    def test_default_plan_verifies_payload_without_creating_destination(self):
        recovery, archive, destination, _ = self.fixture()
        before = {path.relative_to(recovery): digest(path.read_bytes())
                  for path in recovery.rglob("*") if path.is_file()}
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["status"], "ready_to_replay")
        self.assertFalse(report["official_return_created"])
        self.assertFalse(destination.exists())
        self.assertEqual(before, {path.relative_to(recovery): digest(path.read_bytes())
                                  for path in recovery.rglob("*") if path.is_file()})

    def test_rejects_changed_overlay_before_creating_output(self):
        recovery, archive, destination, _ = self.fixture()
        (recovery / "payload/REVIEW.md").write_bytes(b"unrecorded edit")
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(destination.exists())

    def test_requires_original_archive_and_preserved_receipt_to_agree(self):
        recovery, archive, destination, config = self.fixture()
        config["original_archive_sha256"] = "0" * 64
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(destination.exists())

    def test_refuses_existing_destination_even_when_empty(self):
        recovery, archive, destination, _ = self.fixture()
        destination.mkdir()
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(list(destination.iterdir()), [])

    def test_rejects_hashed_private_or_outside_overlay_paths(self):
        recovery, archive, destination, config = self.fixture()
        for name in ("payload/.review/labels.json", "../outside.txt"):
            with self.subTest(name=name):
                path = recovery / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic forbidden payload")
                candidate = dict(config, files={**config["files"], name: digest(path.read_bytes())})
                (recovery / "recovery.json").write_bytes(json_bytes(candidate))
                report = self.tool().finalize(recovery, archive, destination)
                self.assertEqual(report["exit_code"], 2)
                self.assertFalse(destination.exists())

    def test_rejects_symlinked_payload_even_when_its_hash_matches(self):
        recovery, archive, destination, _ = self.fixture()
        file = recovery / "payload/REVIEW.md"
        outside = self.root / "same-report.md"
        outside.write_bytes(file.read_bytes())
        file.unlink()
        file.symlink_to(outside)
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)

    def test_rejects_patch_outside_selected_task_before_execution(self):
        recovery, archive, destination, config = self.fixture()
        unsafe = PATCH.replace(TASK.encode(), b"bbbbbbbbbbbb")
        (recovery / "source.patch").write_bytes(unsafe)
        config["patch_sha256"] = digest(unsafe)
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(destination.exists())

    def test_rejects_mismatched_contract_identity(self):
        recovery, archive, destination, config = self.fixture()
        config["assignment_id"] = "review-" + "ff" * 8
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)

    def test_rejects_unsafe_focused_test_working_directory(self):
        recovery, archive, destination, config = self.fixture()
        config["focused_tests"][0]["cwd"] = "../../outside"
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)

    def test_rejects_duplicate_recovery_json_keys(self):
        recovery, archive, destination, _ = self.fixture()
        path = recovery / "recovery.json"
        text = path.read_text().rstrip()
        path.write_text(text[:-1] + ',"schema":"arcpuzzles-recovery-v1"}')
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)

    def test_executes_synthetic_native_lifecycle_and_retains_complete_receipts(self):
        recovery, archive, destination, config = self.fixture()
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 0, report)
        self.assertTrue(report["official_return_created"])
        self.assertEqual((destination / "WORK" / GENERATOR).read_bytes(), NEW)
        self.assertEqual((destination / "WORK/.review/baseline" / GENERATOR).read_bytes(), OLD)
        self.assertTrue((destination / "RECOVERY-FINALIZATION.json").is_file())
        phases = [command["phase"] for command in report["commands"]]
        self.assertLess(phases.index("native_draw"), phases.index("git_apply"))
        self.assertLess(phases.index("native_task_tests"), phases.index("native_package_return"))
        result = json.loads((destination / "WORK/RESULTS.json").read_text())
        self.assertEqual(result["completion_state"], "blocked")
        self.assertEqual(result["stopping_reason"], "Awaiting replay")
        self.assertGreaterEqual(len(result["verification_commands"]), 2)
        with zipfile.ZipFile(report["return_zip"]) as output:
            self.assertIn("SYNTHETIC-TEST-FIXTURE.txt", output.namelist())
            self.assertEqual(digest(output.read("patches/source.patch")), config["patch_sha256"])

    def test_failed_focused_test_retains_workspace_and_stops_packaging(self):
        recovery, archive, destination, config = self.fixture()
        config["focused_tests"][0]["argv"][-1] = "raise SystemExit(23)"
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 1)
        self.assertFalse(report["official_return_created"])
        self.assertTrue(report["commands"], "Execution must retain the failed command")
        self.assertEqual(report["commands"][-1]["exit_code"], 23)
        self.assertTrue((destination / "WORK" / GENERATOR).is_file())
        saved = json.loads((destination / "RECOVERY-FINALIZATION.json").read_text())
        self.assertEqual(saved["status"], "replay_failed")
        self.assertNotIn("native_package_return", [entry["phase"] for entry in report["commands"]])

    def test_native_prerequisite_failure_cannot_be_skipped(self):
        recovery, archive, destination, _ = self.fixture(native_gate_exit=17)
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 1)
        self.assertTrue(report["commands"], "Native prerequisite command must run")
        self.assertEqual(report["commands"][-1]["phase"], "native_task_tests")
        self.assertEqual(report["commands"][-1]["exit_code"], 17)
        self.assertFalse(report["official_return_created"])

    def test_wrong_final_source_hash_stops_before_tests(self):
        recovery, archive, destination, config = self.fixture()
        config["final_generator_sha256"] = "99" * 32
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 1)
        self.assertFalse(report["official_return_created"])
        self.assertIn("git_apply", [entry["phase"] for entry in report["commands"]])
        self.assertNotIn("native_task_tests", [entry["phase"] for entry in report["commands"]])

    def test_recreates_audit_with_preserved_seed_and_contract(self):
        recovery, archive, destination, config = self.fixture()
        audit = {"schema": "arcpuzzles-full-audit-v3", "seed": "33" * 32,
                 "packet_id": config["packet_id"], "targets": []}
        raw = json_bytes(audit)
        (recovery / "contracts/AUDIT_ASSIGNMENT.json").write_bytes(raw)
        (recovery / "payload/AUDIT.md").write_bytes(b"Synthetic audit fixture.\n")
        config["files"].update({"contracts/AUDIT_ASSIGNMENT.json": digest(raw),
                                "payload/AUDIT.md": digest(b"Synthetic audit fixture.\n")})
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual((destination / "WORK/AUDIT_ASSIGNMENT.json").read_bytes(), raw)

    def test_restores_public_snapshot_without_private_labels_or_new_solve(self):
        recovery, archive, destination, config = self.fixture()
        summary = {"status": "finished", "task_id": TASK,
                   "generator_hash": digest(NEW),
                   "canonical_sha256": digest(b"synthetic ledger only\n")}
        raw = json_bytes(summary)
        path = recovery / "payload/solve/summary.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        config["files"]["payload/solve/summary.json"] = digest(raw)
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual((destination / "WORK/solve/summary.json").read_bytes(), raw)
        self.assertEqual((destination / "WORK/solve/source/generator.py").read_bytes(), NEW)
        self.assertFalse((destination / "WORK/.review/solve-private/labels.json").exists())

    def test_relative_python_becomes_absolute_without_losing_venv_symlink(self):
        recovery, archive, destination, _ = self.fixture()
        interpreter = self.root / "python-link"
        interpreter.symlink_to(sys.executable)
        relative = os.path.relpath(interpreter, Path.cwd())
        report = self.tool().finalize(recovery, archive, destination, execute=True, python=relative)
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual(report["commands"][0]["argv"][0], str(interpreter))

    def test_output_cannot_be_nested_in_recovery_payload(self):
        recovery, archive, _, _ = self.fixture()
        destination = recovery / "payload" / "new"
        report = self.tool().finalize(recovery, archive, destination)
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(destination.exists())

    def test_destination_parent_traversal_is_not_normalized_past_symlink(self):
        recovery, archive, _, _ = self.fixture()
        actual = self.root / "actual"
        actual.mkdir()
        link = self.root / "link"
        link.symlink_to(actual)
        report = self.tool().finalize(recovery, archive, link / ".." / "new")
        self.assertEqual(report["exit_code"], 2)

    def test_focused_command_cannot_silently_rewrite_retained_report(self):
        recovery, archive, destination, config = self.fixture()
        config["focused_tests"][0]["argv"][-1] += "; Path('../REVIEW.md').write_text('unrecorded rewrite')"
        (recovery / "recovery.json").write_bytes(json_bytes(config))
        report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 1)
        self.assertNotIn("native_package_return", [entry["phase"] for entry in report["commands"]])

    def test_capacity_block_stops_before_any_destination_or_command(self):
        recovery, archive, destination, _ = self.fixture()
        capacity = os.statvfs_result((4096, 4096, 100, 0, 0, 100, 0, 0, 0, 255))
        with patch("os.statvfs", return_value=capacity):
            report = self.tool().finalize(recovery, archive, destination, execute=True)
        self.assertEqual(report["exit_code"], 3)
        self.assertEqual(report["commands"], [])
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
