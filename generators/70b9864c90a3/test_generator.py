"""Focused regression tests for task 70b9864c90a3."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("generator.py")
SPEC = importlib.util.spec_from_file_location("task_70b9864c90a3_generator", MODULE_PATH)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


class GeneratorRegressionTest(unittest.TestCase):
    def test_canonical_inputs_and_outputs(self):
        row = None
        source = Path(__file__).resolve()
        candidates = (
            source.parents[2] / "shared/data/canonical/puzzles.jsonl",
            source.parents[3] / "data/canonical/puzzles.jsonl",
        )
        canonical = next(path for path in candidates if path.is_file())
        with canonical.open() as handle:
            for line in handle:
                candidate = json.loads(line)
                if candidate.get("task_id") == GEN.TASK_ID:
                    row = candidate
                    break
        self.assertIsNotNone(row)
        for pair in row["train"] + row["test"]:
            self.assertEqual([], GEN.self_check(pair["input"]))
            self.assertEqual(pair["output"], GEN._apply_rule(pair["input"]))

    def test_override_axes_are_observable(self):
        for texture in GEN.TEXTURES:
            grid = GEN.generate(
                41,
                7,
                difficulty="easy",
                grid_h=7,
                grid_w=7,
                cross_count=3,
                color_mode="shared",
                texture=texture,
            )
            self.assertEqual(
                {
                    "grid_h": 7,
                    "grid_w": 7,
                    "cross_count": 3,
                    "color_mode": "shared",
                    "texture": texture,
                },
                GEN.observe_overrides(grid),
            )

    def test_schedule_falsifies_all_rivals(self):
        demos = []
        for sample_index in range(3):
            grid = GEN.generate(9, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN._apply_rule(grid)})
        query_grid = GEN.generate(9, 3, difficulty="medium")
        query = {"input": query_grid, "output": GEN._apply_rule(query_grid)}
        self.assertEqual([], GEN.lesson_identifiable(demos, query))

    def test_mutations_are_rejected_or_change_rival_answer(self):
        grid = GEN.generate(3, 1, difficulty="easy")
        active = GEN._classify_centers(grid)["active"]
        self.assertGreaterEqual(len(active), 2)
        row, col, _color = active[0]
        malformed = [line[:] for line in grid]
        malformed[row - 1][col - 1] = 0
        self.assertTrue(GEN.self_check(malformed))

        shared = GEN.generate(5, 1, difficulty="easy", color_mode="shared")
        self.assertNotEqual(GEN._apply_rule(shared), GEN._rival_one_center_per_color(shared))

    def test_unknown_override_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(0, 0, typo_axis=1)


if __name__ == "__main__":
    unittest.main()
