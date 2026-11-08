"""Focused regression tests for task 11221f58af4b."""
from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
MODULE_PATH = Path(__file__).with_name("generator.py")
SPEC = importlib.util.spec_from_file_location("task_11221f58af4b_generator", MODULE_PATH)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


class GeneratorRegressionTest(unittest.TestCase):
    def _canonical_row(self):
        root = REPO_ROOT
        with (root / "data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == GEN.TASK_ID:
                    return row
        self.fail("canonical row missing")

    def test_canonical_inputs_and_outputs(self):
        for pair in self._canonical_row()["train"] + self._canonical_row()["test"]:
            self.assertEqual([], GEN.self_check(pair["input"]))
            self.assertEqual(pair["output"], GEN.rule_mirror(pair["input"]))
            self.assertEqual([], GEN.strict_canonical_like(pair["input"]))

    def test_exact_overrides_and_unknown_key(self):
        for n_frames in (1, 2, 3):
            grid = GEN.generate(
                41,
                n_frames,
                difficulty="hard",
                grid_h=18,
                grid_w=20,
                n_frames=n_frames,
                fill_color=9,
                corner_pattern="zeros_tr_bl",
            )
            self.assertEqual(
                {
                    "grid_h": 18,
                    "grid_w": 20,
                    "n_frames": n_frames,
                    "fill_color": 9,
                    "corner_pattern": "zeros_tr_bl",
                },
                GEN.observe_overrides(grid),
            )
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(0, 0, typo_axis=1)

    def test_four_sample_schedule_identifies_rule(self):
        for start in range(8):
            pairs = []
            for sample_index in range(start, start + 5):
                grid = GEN.generate(900 + sample_index, sample_index, difficulty="medium")
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            self.assertEqual([], GEN.lesson_identifiable(pairs[:4], pairs[4]))

    def test_mutation_fixtures_are_rejected(self):
        for name, grid in GEN.mutation_fixtures():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid))

    def test_determinism_freshness_and_global_rng_purity(self):
        random.seed(314159)
        before = random.getstate()
        first = GEN.generate(17, 3, difficulty="hard")
        after = random.getstate()
        second = GEN.generate(17, 3, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertEqual(second, GEN.generate(17, 3, difficulty="hard"))


if __name__ == "__main__":
    unittest.main()
