"""Regression tests for the exact 180-degree rotation generator repair."""
from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path

import sys

RUNTIME = Path(__file__).resolve().parents[3] / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "0a855288946a"
ROOT = find_root(__file__)


def load_generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]


class RotationGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_canonical_inputs_are_accepted_and_strict(self):
        for grid in canonical_inputs():
            self.assertEqual([], self.generator.self_check(grid))
            self.assertEqual([], self.generator.strict_canonical_like(grid))

    def test_exact_overrides_work_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            grid = self.generator.generate(
                17, 29, difficulty=band, grid_h=8, grid_w=3, palette_size=4
            )
            self.assertEqual(
                {"grid_h": 8, "grid_w": 3, "palette_size": 4},
                self.generator.observe_overrides(grid),
            )
            self.assertEqual([], self.generator.self_check(grid))

    def test_every_default_draw_refutes_all_named_rivals(self):
        for band in ("easy", "medium", "hard"):
            for sample_index in range(24):
                grid = self.generator.generate(1000 + sample_index, sample_index, difficulty=band)
                expected = self.generator.rule_mirror(grid)
                self.assertEqual([], self.generator.self_check(grid))
                for name, rival in self.generator.SEMANTIC_RIVALS.items():
                    with self.subTest(band=band, sample_index=sample_index, rival=name):
                        self.assertNotEqual(expected, rival(grid))

    def test_four_targeted_impostors_are_rejected(self):
        impostors = {
            "rot180_symmetric": [[1, 0, 1], [0, 2, 0], [1, 0, 1]],
            "singleton": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
            "horizontal_line": [[1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
            "solid_rectangle": [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_replay_is_fresh_and_global_rng_is_unchanged(self):
        random.seed(12345)
        before = random.getstate()
        first = self.generator.generate(7, 11, difficulty="hard")
        middle = self.generator.generate(8, 12, difficulty="easy")
        second = self.generator.generate(7, 11, difficulty="hard")
        after = random.getstate()
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, middle)

    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.generator.generate(1, 1, typo_axis=4)


if __name__ == "__main__":
    unittest.main()
