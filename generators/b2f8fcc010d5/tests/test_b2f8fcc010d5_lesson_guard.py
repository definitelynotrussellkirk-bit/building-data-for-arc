"""Regressions for ambiguity under fixed input-coordinate selectors."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from arcpuzzles.worker import lesson_check
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("b2f8fcc010d5", root=ROOT)
FIXTURE = Path(__file__).resolve().parents[1] / "counterexamples" / \
    "review-5bbd1c7f3c08fb63" / "seed67-medium.json"
POLICY = {"demonstration_policy": {"automatic": False, "declared_minimum": None}}


def _witness():
    return json.loads(FIXTURE.read_text())


def _check(demos, queries, *, automatic=False):
    request = deepcopy(POLICY)
    request["demonstration_policy"]["automatic"] = automatic
    return lesson_check(GEN, {"train": demos, "test": queries}, request)


class FixedCoordinateLessonGuardTests(unittest.TestCase):
    def test_automatic_seed67_lesson_no_longer_silently_accepts_corner_swap(self):
        witness = _witness()
        with self.assertRaisesRegex(ValueError, "Automatic lesson unsupported"):
            _check(witness["train"], witness["test"], automatic=True)

    def test_explicit_seed67_lesson_retains_query_specific_diagnostic(self):
        witness = _witness()
        result = _check(witness["train"], witness["test"])
        self.assertEqual(result["status"], "diagnostic_unsupported")
        self.assertTrue(result["queries"][0]["reasons"])

    def test_canonical_shortcut_is_executable_and_fits_all_canonical_labels(self):
        rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
        self.assertIn("swap_opposite_corners", rivals)
        for pair in canonical_pairs("b2f8fcc010d5", root=ROOT):
            self.assertEqual(rivals["swap_opposite_corners"](pair["input"]), pair["output"])

    def test_equal_query_values_do_not_require_distinguishing_equivalent_rules(self):
        witness = _witness()
        result = _check(witness["train"], [witness["train"][0]])
        self.assertEqual(result["status"], "passed_declared_hook")
        self.assertFalse(result["queries"][0]["reasons"])

    def test_each_query_is_checked_against_demonstrations_alone(self):
        witness = _witness()
        queries = [witness["train"][0], witness["test"][0],
                   witness["train"][1], witness["test"][0]]
        untouched = deepcopy((witness["train"], queries))
        result = _check(witness["train"], queries)
        self.assertEqual([bool(row["reasons"]) for row in result["queries"]],
                         [False, True, False, True])
        self.assertEqual((witness["train"], queries), untouched)
        reverse = _check(witness["train"], list(reversed(queries)))
        self.assertEqual([bool(row["reasons"]) for row in reverse["queries"]],
                         [True, False, True, False])

    def test_unsampled_coordinate_substitution_is_detected(self):
        pairs = canonical_pairs("b2f8fcc010d5", root=ROOT)
        demos = deepcopy([pair for pair in pairs if pair["split"] == "train"])
        query = deepcopy(next(pair for pair in pairs if pair["split"] == "test"))
        # This decoy copies the center in every demo, but not in the query.
        # It is a valid one-cell alternative to the fixed center selector.
        for demo in demos:
            demo["input"][0][2] = demo["input"][2][2]
        query["input"][0][2] = query["input"][0][0]
        self.assertTrue(all(not GEN.self_check(pair["input"]) for pair in [*demos, query]))
        result = _check(demos, [query])
        self.assertEqual(result["status"], "diagnostic_unsupported")
        self.assertTrue(any("(1, 1)" in reason for reason in result["queries"][0]["reasons"]))

    def test_original_canonical_lesson_remains_answer_equivalent(self):
        pairs = canonical_pairs("b2f8fcc010d5", root=ROOT)
        demos = [pair for pair in pairs if pair["split"] == "train"]
        query = next(pair for pair in pairs if pair["split"] == "test")
        self.assertEqual(_check(demos, [query])["status"], "passed_declared_hook")

    def test_empty_demonstrations_are_not_identifying(self):
        query = _witness()["test"][0]
        self.assertEqual(_check([], [query])["status"], "diagnostic_unsupported")

    def test_inconsistent_demo_label_cannot_be_accepted(self):
        witness = _witness()
        demos = deepcopy(witness["train"])
        demos[0]["output"][0][0] = 0
        self.assertEqual(_check(demos, witness["test"])["status"], "diagnostic_unsupported")


if __name__ == "__main__":
    unittest.main()
