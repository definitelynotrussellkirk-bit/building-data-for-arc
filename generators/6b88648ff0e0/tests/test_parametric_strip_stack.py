"""Focused canonical-preservation and semantic-variant tests (stdlib)."""
import importlib
import json
import sys
import unittest
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK / "workspace/parametric"
REPO = TASK.parents[1]
sys.path[:0] = [str(PARAMETRIC), str(REPO / "shared/runtime")]


class StripStackTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((PARAMETRIC / "strip_stack.py").is_file(), "strip-stack prototype is not implemented")
        self.m = importlib.import_module("strip_stack")

    def test_default_program_preserves_exact_canonical_source(self):
        programs = {json.loads(line)["program_solution"]
                    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                    if json.loads(line).get("task_id") == "6b88648ff0e0"}
        self.assertEqual({self.m.render_program("top_to_bottom")}, programs)

    def test_reverse_order_keeps_rows_within_each_strip(self):
        grid = [[(r + c) % 8 for c in range(9)] for r in range(9)]
        for top in (1, 5):
            for r in (top, top + 1):
                for c in (0, 1, 5, 6):
                    grid[r][c] = 8
        grid[0][0] = 9
        top = [row[2:5] for row in grid[1:3]]
        bottom = [row[2:5] for row in grid[5:7]]
        self.assertEqual(self.m.python_expected(grid, "top_to_bottom"), top + bottom)
        self.assertEqual(self.m.python_expected(grid, "bottom_to_top"), bottom + top)
        self.assertNotEqual(bottom + top, (top + bottom)[::-1])

    def test_sampler_has_shared_inputs_and_distinguishing_demonstration(self):
        for seed in (0, 1, 17):
            a = self.m.sample_input(seed, 0)
            self.assertEqual(a, self.m.sample_input(seed, 0))
            self.assertNotEqual(self.m.python_expected(a, "top_to_bottom"),
                                self.m.python_expected(a, "bottom_to_top"))

    def test_one_group_alternatives_can_agree(self):
        grid = self.m.sample_input(5, 3)
        self.assertEqual(self.m.python_expected(grid, "top_to_bottom"),
                         self.m.python_expected(grid, "bottom_to_top"))

    def test_fresh_samples_do_not_alias(self):
        first = self.m.sample_input(17, 2)
        original = [row[:] for row in first]
        first[0][0] = 8
        self.assertEqual(self.m.sample_input(17, 2), original)

    def test_bad_settings_and_noninteger_seeds_fail_closed(self):
        for setting in (None, True, 0, "reverse"):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                self.m.render_program(setting)
        for seed, index in ((True, 0), (1, False), (1, -1), (1.5, 0)):
            with self.subTest(seed=seed, index=index), self.assertRaises(ValueError):
                self.m.sample_input(seed, index)


if __name__ == "__main__":
    unittest.main()
