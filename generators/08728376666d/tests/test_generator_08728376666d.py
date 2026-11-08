"""Focused regression tests for the H31 color-frequency generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


MODULE_PATH = REPO_ROOT / "puzzle_generators" / "per_puzzle" / "08728376666d" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_08728376666d", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class Generator08728376666dTests(unittest.TestCase):
    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(1, 0, typo_axis=3)

    def test_every_profile_and_color_count_is_observable(self):
        for profile in GEN.PROFILES:
            for n_colors in range(2, 6):
                grid = GEN.generate(
                    301 + n_colors,
                    17,
                    grid_h=10,
                    grid_w=13,
                    n_colors=n_colors,
                    profile=profile,
                )
                self.assertEqual(GEN.self_check(grid), [])
                observed = GEN.observe_overrides(grid)
                self.assertEqual(observed["grid_h"], 10)
                self.assertEqual(observed["grid_w"], 13)
                self.assertEqual(observed["n_colors"], n_colors)
                self.assertEqual(observed["profile"], profile)

    def test_three_consecutive_demos_identify_rule(self):
        demos = []
        for sample_index in range(3):
            grid = GEN.generate(911, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(911, 3, difficulty="medium")
        self.assertEqual(
            GEN.lesson_identifiable(demos, {"input": query_grid}),
            [],
        )

    def test_minimal_impostors_are_rejected(self):
        impostors = [
            [[0] * 8 for _ in range(7)],
            [[1] + [0] * 7 for _ in range(7)],
            [[1, 1, 1, 1] + [0] * 4] + [[0] * 8 for _ in range(6)],
        ]
        for grid in impostors:
            self.assertTrue(GEN.self_check(grid))


if __name__ == "__main__":
    unittest.main()
