"""Keep the proposed half-threshold rule tied to the issued canonical rule."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

TASK = "661dffbdf39a"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, load_selected_generator


def load_variant():
    path = TASK_HOME / "workspace/parametric/threshold_variant.py"
    spec = importlib.util.spec_from_file_location("threshold_canonical_variant", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CanonicalCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.variant = load_variant()
        cls.pairs = canonical_pairs(TASK, root=REPO, labeled_only=True)
        records = (json.loads(line) for line in
                   (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        cls.canonical = next(row for row in records if row.get("task_id") == TASK)

    def test_default_matches_all_four_canonical_pairs_in_racket(self):
        self.assertEqual(len(self.pairs), 4)
        grids = [pair["input"] for pair in self.pairs]
        before = copy.deepcopy(grids)
        expected = [pair["output"] for pair in self.pairs]
        self.assertEqual(self.variant.run_racket(self.variant.rule_program("1/2"), grids), expected)
        self.assertEqual(grids, before)

    def test_original_and_proposed_default_agree_on_new_and_transposed_inputs(self):
        grids = [self.variant.sample_input(20261023, index) for index in range(6)]
        grids += [[list(column) for column in zip(*grid)] for grid in grids[:]]
        original = self.variant.run_racket(self.canonical["program_solution"], grids)
        proposed = self.variant.run_racket(self.variant.rule_program("1/2"), grids)
        self.assertEqual(proposed, original)
        self.assertEqual([self.variant.solve_python(grid, "1/2") for grid in grids], original)

    def test_default_matches_production_mirror_on_original_inputs(self):
        generator, _, _ = load_selected_generator(TASK, root=REPO)
        for pair in self.pairs:
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(self.variant.solve_python(pair["input"], "1/2"),
                                 generator.rule_mirror(pair["input"]))

    def test_odd_rectangular_axes_use_their_own_strict_majorities(self):
        height, width = 15, 17
        strong_rows, strong_cols = {1, 12}, {3, 15}
        partial_rows, partial_cols = {4, 9}, {6, 8}
        grid = [[5 if r in strong_rows or c in strong_cols else 0
                 for c in range(width)] for r in range(height)]
        available_cols = [c for c in range(width) if c not in strong_cols | partial_cols]
        for r, count in ((4, 8), (9, 9)):
            for c in available_cols[:count - len(strong_cols)]:
                grid[r][c] = 5
        available_rows = [r for r in range(height) if r not in strong_rows | partial_rows]
        for c, count in ((6, 7), (8, 8)):
            for r in available_rows[:count - len(strong_rows)]:
                grid[r][c] = 5
        grid[14][16] = 9
        expected_rows, expected_cols = {1, 9, 12}, {3, 8, 15}
        expected = [[9 if r in expected_rows and c in expected_cols else
                     5 if r in expected_rows or c in expected_cols else 0
                     for c in range(width)] for r in range(height)]
        self.assertEqual(self.variant.solve_python(grid, "1/2"), expected)
        for program in (self.canonical["program_solution"], self.variant.rule_program("1/2")):
            self.assertEqual(self.variant.run_racket(program, [grid]), [expected])


if __name__ == "__main__":
    unittest.main()
