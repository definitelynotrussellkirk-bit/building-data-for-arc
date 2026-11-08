"""Behavior tests using synthetic WORK trees; no ARC/reference data is loaded."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import receipt_check


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "receipt_check.py"


class ReceiptCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="receipt-test-", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.packet = Path(self.temp.name) / "packet"
        self.work = self.packet / "WORK"
        (self.work / "repo").mkdir(parents=True)
        (self.work / "checks").mkdir()
        (self.work / "checks/sample.json").write_text('{"passed": false}\n')
        (self.work / "run_with_racket.py").write_text("raise RuntimeError('must stay passive')\n")
        self.results = self.work / "RESULTS.json"
        self.command = {
            "cwd": "repo",
            "argv": ["python3", "-m", "unittest"],
            "exit_code": 0,
            "evidence_paths": ["checks/sample.json"],
        }
        self.document = {
            "completion_state": "partial",
            "stopping_reason": "Synthetic fixture; no generator verdict is claimed.",
            "remaining_failures": [],
            "verification_commands": [self.command],
        }

    def write_results(self):
        self.results.write_text(json.dumps(self.document, indent=2) + "\n")

    def check(self, *extra, exit_code=0, write=True):
        if write:
            self.write_results()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--work-root", str(self.work), *extra],
            cwd=HERE, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    @staticmethod
    def codes(report, severity):
        return {item["code"] for item in report[severity]}

    def add_generator(self):
        source = self.work / "repo/generators/synthetic_task/generator.py"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"raise RuntimeError('hash bytes, never import')\n")
        return source, hashlib.sha256(source.read_bytes()).hexdigest()

    def test_valid_receipt_is_passive_and_does_not_claim_semantic_success(self):
        marker = self.work / "MUST_NOT_EXIST"
        self.command["argv"] = [sys.executable, "-c", f"open({str(marker)!r}, 'w').write('bad')"]
        self.write_results()
        before = self.results.read_bytes()
        report = self.check(write=False)
        self.assertFalse(marker.exists())
        self.assertEqual(before, self.results.read_bytes())
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["verification_status"], "not_reexecuted")
        self.assertEqual(report["semantic_verdict"], "not_assessed")
        self.assertNotIn("passed", report)
        self.assertEqual(report["commands"][0]["recorded_outcome"], "recorded_zero")
        self.assertIn("final_generator_hash_not_checked", self.codes(report, "unknowns"))

    def test_unknown_and_failed_exit_codes_are_preserved_without_invalidating_receipts(self):
        for code, outcome in [(None, "unknown"), (7, "recorded_nonzero")]:
            with self.subTest(exit_code=code):
                self.command["exit_code"] = code
                report = self.check()
                self.assertEqual(report["commands"][0]["exit_code"], code)
                self.assertEqual(report["commands"][0]["recorded_outcome"], outcome)
                if code is None:
                    self.assertIn("exit_code_unknown", self.codes(report, "unknowns"))
                else:
                    self.assertEqual(report["counts"]["recorded_nonzero_commands"], 1)

    def test_missing_exit_code_is_invalid_and_unknown(self):
        del self.command["exit_code"]
        report = self.check(exit_code=1)
        self.assertIn("exit_code_missing", self.codes(report, "errors"))
        self.assertEqual(report["commands"][0]["recorded_outcome"], "unknown")

    def test_boolean_and_string_exit_codes_are_invalid_not_success(self):
        for value in [False, True, "0", 0.0]:
            with self.subTest(exit_code=value):
                self.command["exit_code"] = value
                report = self.check(exit_code=1)
                self.assertIn("exit_code_invalid", self.codes(report, "errors"))
                self.assertEqual(report["commands"][0]["recorded_outcome"], "unknown")

    def test_malformed_argv_is_rejected(self):
        for value in ["python3 -m unittest", [], [""], [False], ["python3", 7], ["python3", "x\x00y"]]:
            with self.subTest(argv=value):
                self.command["argv"] = value
                report = self.check(exit_code=1)
                self.assertIn("argv_invalid", self.codes(report, "errors"))

    def test_empty_non_executable_argument_is_valid(self):
        self.command["argv"] = ["program", "", "a value", "$(never executed)"]
        self.assertEqual(self.check()["errors"], [])

    def test_malformed_cwd_and_relative_escape_are_rejected(self):
        for value in [None, 12, "", "x\x00y", "../../outside"]:
            with self.subTest(cwd=value):
                self.command["cwd"] = value
                report = self.check(exit_code=1)
                self.assertTrue(self.codes(report, "errors") & {"cwd_invalid", "cwd_outside_work"})

    def test_missing_relative_cwd_or_file_cwd_is_rejected(self):
        for value in ["missing-folder", "checks/sample.json"]:
            with self.subTest(cwd=value):
                self.command["cwd"] = value
                self.assertIn("cwd_not_directory", self.codes(self.check(exit_code=1), "errors"))

    def test_actual_absolute_cwd_outside_work_is_accepted(self):
        self.command["cwd"] = str(Path(self.temp.name))
        report = self.check()
        self.assertEqual(report["commands"][0]["cwd"]["kind"], "absolute")
        self.assertEqual(report["errors"], [])

    def test_unavailable_or_foreign_absolute_cwd_remains_unknown(self):
        for value in [str(Path(self.temp.name) / "old-checkout"), "C:\\old-checkout\\WORK\\repo"]:
            with self.subTest(cwd=value):
                self.command["cwd"] = value
                report = self.check()
                self.assertIn("absolute_cwd_unavailable", self.codes(report, "unknowns"))

    def test_posix_absolute_cwd_is_unknown_under_windows_path_syntax(self):
        report = {"errors": [], "warnings": [], "unknowns": []}
        # Exercise native Windows path syntax without pretending to run Windows.
        with patch.object(receipt_check, "Path", PureWindowsPath):
            result = receipt_check.check_cwd("/workspace/old/WORK/repo", self.work, report, "cwd")
        self.assertEqual(report["errors"], [])
        self.assertIn("absolute_cwd_unavailable", self.codes(report, "unknowns"))
        self.assertIsNone(result["resolved"])

    def test_packet_root_alias_resolves_to_outer_directory(self):
        self.command["cwd"] = "packet_root"
        report = self.check()
        self.assertEqual(report["commands"][0]["cwd"]["resolved"], str(self.packet))

    def test_missing_empty_or_malformed_evidence_is_rejected(self):
        for value in [["checks/absent.json"], [], "checks/sample.json", [7], [""]]:
            with self.subTest(evidence=value):
                self.command["evidence_paths"] = value
                self.assertTrue(self.check(exit_code=1)["errors"])
        del self.command["evidence_paths"]
        self.assertTrue(self.check(exit_code=1)["errors"])

    def test_absolute_and_escaping_evidence_paths_are_rejected(self):
        outside = self.packet / "outside.json"
        outside.write_text("not evidence in WORK\n")
        for value in [str(outside), "../outside.json", "C:\\outside.json"]:
            with self.subTest(evidence=value):
                self.command["evidence_paths"] = [value]
                self.assertIn("evidence_outside_work", self.codes(self.check(exit_code=1), "errors"))

    def test_evidence_symlink_escape_is_rejected(self):
        outside = self.packet / "outside.json"
        outside.write_text("must not be read\n")
        (self.work / "checks/escape.json").symlink_to(outside)
        self.command["evidence_paths"] = ["checks/escape.json"]
        self.assertIn("evidence_outside_work", self.codes(self.check(exit_code=1), "errors"))

    def test_directory_evidence_is_not_claimed_to_be_inventoried(self):
        self.command["evidence_paths"] = ["checks"]
        report = self.check()
        self.assertIn("evidence_directory_not_inventoried", self.codes(report, "unknowns"))

    def test_evidence_contents_are_not_parsed(self):
        (self.work / "checks/sample.json").write_bytes(b"not JSON; receipt existence only\x00\xff")
        self.assertEqual(self.check()["errors"], [])

    def test_missing_or_malformed_top_level_fields_are_rejected(self):
        for field in ["completion_state", "stopping_reason", "remaining_failures", "verification_commands"]:
            with self.subTest(field=field):
                old = self.document.pop(field)
                self.assertTrue(self.check(exit_code=1)["errors"])
                self.document[field] = old

    def test_empty_command_population_is_unknown(self):
        self.document["verification_commands"] = []
        report = self.check()
        self.assertIn("no_commands_recorded", self.codes(report, "unknowns"))
        self.assertEqual(report["counts"]["commands"], 0)

    def test_missing_and_invalid_json_produce_json_errors(self):
        self.assertIn("results_unreadable", self.codes(self.check(exit_code=1, write=False), "errors"))
        for text in ["{", "[]", '{"duplicate": 1, "duplicate": 2}', '{"value": NaN}']:
            with self.subTest(text=text):
                self.results.write_text(text)
                self.assertTrue(self.check(exit_code=1, write=False)["errors"])

    def test_overflowing_json_number_is_a_json_error(self):
        for field in ['"partial"', '"repo"', '"checks/sample.json"']:
            with self.subTest(field=field):
                self.results.write_text(json.dumps(self.document).replace(field, "1e999"))
                report = self.check(exit_code=1, write=False)
                self.assertIn("results_json_invalid", self.codes(report, "errors"))

    def test_explicit_source_hash_matches_without_importing_generator(self):
        source, digest = self.add_generator()
        report = self.check("--task-id", "synthetic_task", "--expected-final-generator-sha256", digest)
        self.assertEqual(report["source_check"]["status"], "matched")
        self.assertEqual(report["source_check"]["actual_sha256"], digest)
        self.assertEqual(report["source_check"]["path"], str(source))

    def test_source_hash_mismatch_and_bad_hash_are_errors(self):
        self.add_generator()
        for digest, code in [("0" * 64, "generator_hash_mismatch"), ("not-a-hash", "expected_hash_invalid")]:
            with self.subTest(digest=digest):
                report = self.check("--task-id", "synthetic_task", "--expected-final-generator-sha256", digest, exit_code=1)
                self.assertIn(code, self.codes(report, "errors"))

    def test_missing_source_unsafe_task_and_incomplete_hash_options_are_errors(self):
        cases = [
            (["--task-id", "synthetic_task", "--expected-final-generator-sha256", "0" * 64], "generator_unreadable"),
            (["--task-id", "../escape", "--expected-final-generator-sha256", "0" * 64], "task_id_invalid"),
            (["--task-id", "synthetic_task"], "source_options_incomplete"),
            (["--expected-final-generator-sha256", "0" * 64], "source_options_incomplete"),
        ]
        for args, code in cases:
            with self.subTest(args=args):
                self.assertIn(code, self.codes(self.check(*args, exit_code=1), "errors"))

    def test_generator_symlink_outside_work_is_rejected(self):
        source, digest = self.add_generator()
        outside = self.packet / "outside-generator.py"
        source.replace(outside)
        source.symlink_to(outside)
        report = self.check("--task-id", "synthetic_task", "--expected-final-generator-sha256", digest, exit_code=1)
        self.assertIn("generator_outside_work", self.codes(report, "errors"))

    def test_cli_usage_errors_are_json(self):
        report = self.check("--unrecognized-option", exit_code=2)
        self.assertIn("command_line_invalid", self.codes(report, "errors"))

    def test_explicit_results_path_is_resolved_from_caller_cwd(self):
        alternate = self.work / "alternate-results.json"
        self.write_results()
        self.results.replace(alternate)
        report = self.check(str(alternate.relative_to(HERE)), write=False)
        self.assertEqual(report["results_path"], str(alternate))

    def test_legacy_wrapper_at_outer_root_warns_or_fails_by_policy(self):
        self.command.update(cwd="packet_root", argv=["python3", "-B", "run_with_racket.py", "python3", "-m", "unittest"])
        report = self.check()
        self.assertIn("legacy_wrapper_wrong_cwd", self.codes(report, "warnings"))
        report = self.check("--legacy-wrapper-policy", "error", exit_code=1)
        self.assertIn("legacy_wrapper_wrong_cwd", self.codes(report, "errors"))

    def test_correct_wrapper_paths_and_python_code_are_not_flagged(self):
        self.command["cwd"] = "packet_root"
        for argv in [
            ["python3", "review.py", "check"],
            ["python3", "WORK/run_with_racket.py", "python3", "-m", "unittest"],
            ["python3", "-c", "print('run_with_racket.py')"],
            ["echo", "run_with_racket.py"],
        ]:
            with self.subTest(argv=argv):
                self.command["argv"] = argv
                self.assertNotIn("legacy_wrapper_wrong_cwd", self.codes(self.check(), "warnings"))

    def test_attached_python_code_module_and_unknown_options_do_not_false_flag(self):
        self.command["cwd"] = "packet_root"
        for option in ["-cpass", "-mexample", "-Icpass"]:
            with self.subTest(option=option):
                self.command["argv"] = ["python3", option, "run_with_racket.py"]
                report = self.check("--legacy-wrapper-policy", "error")
                self.assertEqual(report["errors"], [])

    def test_default_root_discovery_survives_relocation(self):
        self.write_results()
        copied = self.work / "checks/receipt-helper/receipt_check.py"
        copied.parent.mkdir()
        self.assertTrue(SCRIPT.is_file(), "receipt_check.py has not been implemented")
        shutil.copyfile(SCRIPT, copied)
        result = subprocess.run([sys.executable, str(copied)], cwd=Path(self.temp.name), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["work_root"], str(self.work))
        self.assertEqual(report["results_path"], str(self.results))


if __name__ == "__main__":
    unittest.main()
