import copy
import unittest
from summarize_battery import summarize


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


if __name__ == "__main__":
    unittest.main()
