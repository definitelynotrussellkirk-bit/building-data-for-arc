"""Query-sensitive regressions for the finite beam-depth cap rival family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("depth_cap_generator", TASK / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
AUDIT = (TASK / "counterexamples/review-c163cb377b0acf2c-v0001/retained/checks"
         / "audit/038f266f3acf")
LESSON = json.loads((AUDIT / "lesson.json").read_text())
QUERIES = {item["case"]: item for item in LESSON["queries"]}


def depth_query(depth, *, clipped=False):
    """Two separate rim-marked rectangles; left launch has the requested depth."""
    height, width = (7 if clipped else depth + 3), max(12, depth + 5)
    grid = [[0] * width for _ in range(height)]
    first_row = 2 if clipped else height - 3
    for row in range(first_row, first_row + 3):
        for col in range(2, 3 + depth):
            grid[row][col] = 3
    grid[first_row + 1][2] = 2
    for row in range(3):
        for col in (width - 3, width - 2):
            grid[row][col] = 3
    grid[1][width - 2] = 2
    return grid


class QueryWithForbiddenLabel(dict):
    def __getitem__(self, key):
        if key == "output":
            raise AssertionError("the held-out query label must not be read")
        return super().__getitem__(key)

    def get(self, key, *args):
        if key == "output":
            raise AssertionError("the held-out query label must not be read")
        return super().get(key, *args)


class DepthCapLessonTests(unittest.TestCase):
    def test_canonical_depth_five_query_rejects_surviving_cap_four(self):
        reasons = GEN.lesson_identifiable(LESSON["demos"],
                                         {"input": QUERIES["canonical_depth_five"]["input"]})
        self.assertTrue(any("half-width cap 4" in reason for reason in reasons), reasons)

    def test_query_label_is_never_used_to_reject_cap_four(self):
        grid = QUERIES["canonical_depth_five"]["input"]
        without_label = GEN.lesson_identifiable(LESSON["demos"], {"input": grid})
        hostile_label = QueryWithForbiddenLabel(input=grid, output=[[9]])
        with_label = GEN.lesson_identifiable(LESSON["demos"], hostile_label)
        self.assertEqual(without_label, with_label)
        self.assertTrue(any("half-width cap 4" in reason for reason in with_label), with_label)

    def test_small_lawful_depth_five_query_is_also_rejected(self):
        grid = QUERIES["small_depth_five"]["input"]
        self.assertEqual([], GEN.self_check(grid))
        reasons = GEN.lesson_identifiable(LESSON["demos"], {"input": grid})
        self.assertTrue(any("half-width cap 4" in reason for reason in reasons), reasons)

    def test_cap_family_extends_beyond_the_reported_cap_four(self):
        canonical = QUERIES["canonical_depth_five"]
        demos = LESSON["demos"] + [{"input": canonical["input"],
                                    "output": canonical["racket_output"]}]
        grid = depth_query(6)
        self.assertEqual([], GEN.self_check(grid))
        reasons = GEN.lesson_identifiable(demos, {"input": grid})
        self.assertTrue(any("half-width cap 5" in reason for reason in reasons), reasons)
        self.assertFalse(any("half-width cap 4" in reason for reason in reasons), reasons)

    def test_depth_five_demo_can_refute_cap_four_for_a_distinct_query(self):
        canonical = QUERIES["canonical_depth_five"]
        demos = LESSON["demos"] + [{"input": canonical["input"],
                                    "output": canonical["racket_output"]}]
        self.assertEqual([], GEN.lesson_identifiable(
            demos, {"input": QUERIES["small_depth_five"]["input"]}))

    def test_clipping_can_make_a_surviving_cap_query_equivalent(self):
        grid = depth_query(5, clipped=True)
        self.assertEqual([], GEN.self_check(grid))
        self.assertEqual([], GEN.lesson_identifiable(LESSON["demos"], {"input": grid}))

    def test_invalid_query_returns_a_reason_without_raising(self):
        reasons = GEN.lesson_identifiable(LESSON["demos"], {"input": [[0]]})
        self.assertIn("query input is outside the teaching grammar", reasons)

    def test_invalid_demo_output_still_rejects_the_lesson(self):
        demos = deepcopy(LESSON["demos"])
        demos[0]["output"] = [[9]]
        reasons = GEN.lesson_identifiable(demos, {"input": depth_query(6)})
        self.assertIn("demo 0 output does not match the beam rule", reasons)

    def test_all_four_profile_rotations_keep_generated_queries_usable(self):
        for band in ("easy", "medium", "hard"):
            for start in range(4):
                with self.subTest(band=band, start=start):
                    demos = []
                    for index in range(start, start + 4):
                        grid = GEN.generate(6000 + start, index, difficulty=band)
                        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
                    query = GEN.generate(7000 + start, start + 4, difficulty=band)
                    self.assertEqual([], GEN.lesson_identifiable(demos, {"input": query}))

    def test_original_seeded_inputs_match_retained_racket_witness(self):
        inputs = [demo["input"] for demo in LESSON["demos"]]
        inputs.append(QUERIES["generated_4"]["input"])
        for index, expected in enumerate(inputs):
            with self.subTest(index=index):
                self.assertEqual(expected, GEN.generate(20261012, index, difficulty="easy"))

    def test_lesson_check_does_not_mutate_inputs_or_demonstrations(self):
        demos = deepcopy(LESSON["demos"])
        query = {"input": depth_query(6)}
        before = deepcopy((demos, query))
        GEN.lesson_identifiable(demos, query)
        self.assertEqual(before, (demos, query))


if __name__ == "__main__":
    unittest.main(verbosity=2)
