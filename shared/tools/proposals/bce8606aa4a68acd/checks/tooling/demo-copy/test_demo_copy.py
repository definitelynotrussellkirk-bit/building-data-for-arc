"""CLI behavior tests; no generator, canonical data, or reference imports."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

CLI = Path(__file__).with_name("demo_copy.py")


def lesson(source, target, output=None, demo_output=None):
    query = {"input": target}
    if output is not None:
        query["output"] = output
    return {"train": [{"input": source, "output": demo_output or source}],
            "test": [query]}


class DemoCopyTests(unittest.TestCase):
    def run_cli(self, value, expected_code=0):
        result = subprocess.run([sys.executable, str(CLI), "-"],
                                input=json.dumps(value), text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, expected_code, result.stderr)
        return json.loads(result.stdout)

    def query(self, value):
        return self.run_cli(value)["lessons"][0]["queries"][0]

    def test_recolor_copy_predicts_and_scores_actual_label(self):
        q = self.query(lesson([[0, 2], [3, 2]], [[0, 7], [9, 7]],
                              [[7, 9]], [[2, 3]]))
        self.assertEqual(q["input_match_count"], 1)
        self.assertEqual(q["actual_agreement_count"], 1)
        self.assertEqual(q["matches"][0]["prediction"], [[7, 9]])
        self.assertIs(q["matches"][0]["agrees_with_query_label"], True)

    def test_geometric_mismatch_has_no_match(self):
        for target in ([[7, 0], [9, 7]], [[0, 7, 0], [9, 7, 0]]):
            with self.subTest(target=target):
                self.assertEqual(self.query(lesson([[0, 2], [3, 2]], target))
                                 ["input_match_count"], 0)

    def test_inconsistent_nonbijective_and_background_changes_have_no_match(self):
        for source, target in (([[2, 2]], [[7, 9]]),
                               ([[2, 3]], [[7, 7]]),
                               ([[0, 2]], [[7, 9]]),
                               ([[2, 3]], [[0, 9]])):
            with self.subTest(source=source, target=target):
                self.assertEqual(self.query(lesson(source, target))["input_match_count"], 0)

    def test_absent_label_is_unscored_even_when_prediction_exists(self):
        q = self.query(lesson([[0, 2]], [[0, 7]], demo_output=[[2]]))
        self.assertEqual(q["label_status"], "unscored")
        self.assertIsNone(q["actual_agreement_count"])
        self.assertEqual(q["matches"][0]["prediction"], [[7]])
        self.assertIsNone(q["matches"][0]["agrees_with_query_label"])

    def test_novel_demo_output_color_does_not_invent_mapping(self):
        q = self.query(lesson([[0, 2]], [[0, 7]], [[8]], [[8]]))
        match = q["matches"][0]
        self.assertEqual(q["input_match_count"], 1)
        self.assertEqual(q["prediction_count"], 0)
        self.assertEqual(match["prediction_status"], "unmapped_output_colors")
        self.assertEqual(match["unmapped_output_colors"], [8])
        self.assertIsNone(match["prediction"])
        self.assertIsNone(match["agrees_with_query_label"])

    def test_wrong_query_label_is_reported_as_disagreement(self):
        q = self.query(lesson([[2]], [[7]], [[9]], [[2]]))
        self.assertEqual(q["actual_agreement_count"], 0)
        self.assertIs(q["matches"][0]["agrees_with_query_label"], False)

    def test_identity_and_legitimate_recolor_remain_diagnostic_only(self):
        report = self.run_cli([lesson([[0, 2]], [[0, 2]], [[2]], [[2]]),
                               lesson([[0, 2]], [[0, 7]], [[7]], [[2]])])
        self.assertEqual(len(report["lessons"]), 2)
        self.assertIsNone(report["admission_decision"])
        self.assertIn("legitimate", report["caution"])
        self.assertTrue(all(row["queries"][0]["actual_agreement_count"] == 1
                            for row in report["lessons"]))

    def test_multiple_demonstration_candidates_are_all_retained(self):
        value = lesson([[2]], [[7]], [[7]], [[2]])
        value["train"].append({"input": [[3]], "output": [[0]]})
        q = self.query(value)
        self.assertEqual(q["input_match_count"], 2)
        self.assertEqual([m["agrees_with_query_label"] for m in q["matches"]], [True, False])

    def test_invalid_arc_grid_returns_structured_error(self):
        for grid in ([[True]], [[10]], [[0], [0, 2]], []):
            with self.subTest(grid=grid):
                report = self.run_cli(lesson(grid, [[0]]), expected_code=2)
                self.assertIn("error", report)


if __name__ == "__main__":
    unittest.main()
