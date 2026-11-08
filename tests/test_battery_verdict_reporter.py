import copy
import unittest
import importlib.util
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'shared/tools/summarize_battery.py'
spec = importlib.util.spec_from_file_location('battery_verdict_reporter', SCRIPT)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
summarize = api.summarize


def fixture(*statuses):
    counts = {key: statuses.count(key) for key in
              ("green", "advisory", "failed", "interrupted", "pending", "running")}
    counts["total"] = len(statuses)
    return {"schema": "generator_battery_summary/1", "task": "fixture", "phase": "before",
            "counts": counts, "stages": {str(i): {"status": status}
                                         for i, status in enumerate(statuses)}}


class SummaryTests(unittest.TestCase):
    def test_all_green(self):
        result = summarize(fixture("green", "green"))
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(result["every_stage_green"])
        self.assertIsNone(result["completed_nonblocking_exit0"])

    def test_baseline_advisories_are_nonblocking_but_not_green(self):
        result = summarize(fixture(*(["green"] * 10 + ["advisory"] * 2)))
        self.assertEqual(result["counts"], {"PASS": 10, "ADVISORY": 2, "FAIL": 0,
                                          "UNFINISHED": 0, "TOTAL": 12})
        self.assertTrue(result["completed_nonblocking"])
        self.assertFalse(result["every_stage_green"])
        self.assertEqual(result["verdict"], "ADVISORY")

    def test_failed_stage_blocks_even_when_complete(self):
        result = summarize(fixture("green", "failed", "advisory"))
        self.assertTrue(result["complete"])
        self.assertFalse(result["completed_nonblocking"])
        self.assertEqual(result["verdict"], "FAIL")

    def test_each_unfinished_state_blocks(self):
        for status in ("running", "pending", "interrupted"):
            with self.subTest(status=status):
                result = summarize(fixture("green", status))
                self.assertEqual(result["verdict"], "INCOMPLETE")
                self.assertFalse(result["complete"])

    def test_public_exit_zero_is_distinct_from_all_green(self):
        wrapper = {"schema": "arcpuzzles-check-v1", "battery_summary": fixture("advisory"),
                   "exit_code": 0, "status": "completed", "timed_out": False}
        self.assertTrue(summarize(wrapper)["completed_nonblocking_exit0"])
        self.assertFalse(summarize(wrapper)["every_stage_green"])
        for update in ({"exit_code": 1}, {"status": "running"}, {"timed_out": True}):
            changed = copy.deepcopy(wrapper)
            changed.update(update)
            self.assertFalse(summarize(changed)["completed_nonblocking_exit0"])

    def test_corrupt_evidence_is_rejected(self):
        for malformed in ({}, fixture(), fixture("unknown")):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    summarize(malformed)
        mismatched = fixture("green")
        mismatched["counts"]["advisory"] = 1
        with self.assertRaises(ValueError):
            summarize(mismatched)


class IntegrityTests(unittest.TestCase):
    def test_count_types_are_exact_integers(self):
        for value in (True, 1.0):
            row = fixture('green')
            row['counts']['green'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize(row)

    def test_recorded_verdict_cannot_contradict_stages(self):
        row = fixture('green')
        row['verdict'] = 'failed'
        with self.assertRaises(ValueError):
            summarize(row)

    def test_public_exit_and_timeout_types_are_not_coerced(self):
        for change in ({'exit_code': False}, {'exit_code': 0.0}, {'timed_out': 0}):
            row = {'schema': 'arcpuzzles-check-v1', 'battery_summary': fixture('green'),
                   'status': 'completed', 'exit_code': 0, 'timed_out': False}
            row.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                summarize(row)

    def test_ambiguous_json_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'result.json'
            source.write_text('{"schema":"wrong","schema":"generator_battery_summary/1"}')
            result = subprocess.run([sys.executable, str(SCRIPT), str(source)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'duplicate', result.stderr.lower())

    def test_shell_final_verdict_distinguishes_advisories(self):
        source = (ROOT / 'shared/tools/run_generator_battery.sh').read_text()
        if 'case "$(summary_verdict)" in' in source[source.rfind('  echo "SUMMARY '):]:
            fragment = source[source.rfind('  case "$(summary_verdict)" in'):].rsplit('\nfi', 1)[0]
        else:
            fragment = source[source.rfind('  echo "ALL '):].rsplit('\nfi', 1)[0]
        for status in ('all_green', 'passed_with_advisories', 'failed'):
            command = 'summary_verdict() { echo "$VERDICT"; }; STAGES=(a b); TASK=fixture; PHASE=before; SUMMARY=summary.json; ' + fragment
            result = subprocess.run(['bash', '-c', command], env={'VERDICT':status}, capture_output=True, text=True)
            with self.subTest(status=status):
                if status == 'all_green':
                    self.assertEqual(result.returncode, 0)
                    self.assertIn('stages green', result.stdout)
                elif status == 'passed_with_advisories':
                    self.assertEqual(result.returncode, 0)
                    self.assertIn('advisories', result.stdout)
                    self.assertNotIn('stages green', result.stdout)
                else:
                    self.assertNotEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main()
