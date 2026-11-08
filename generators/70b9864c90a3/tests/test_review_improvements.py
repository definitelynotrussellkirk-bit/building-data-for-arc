"""Adversarial regressions added during review review-50d575e3add2d4ef."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("task_70b9864c90a3_reviewed", MODULE_PATH)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)

ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _texture_conditioned_one_per_color(grid, texture):
    if GEN._classify_centers(grid)[texture]:
        return GEN._apply_rule(grid)
    return GEN._rival_one_center_per_color(grid)


class ReviewImprovementTest(unittest.TestCase):
    def test_default_lessons_refute_each_texture_conditioned_color_shortcut(self):
        """No distractor kind may be a perfect proxy for when reuse is allowed."""
        for seed in range(8):
            for start in (0, 11):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty="medium")
                    demos.append((grid, GEN._apply_rule(grid)))
                for texture in GEN.TEXTURES:
                    with self.subTest(seed=seed, start=start, texture=texture):
                        self.assertTrue(
                            any(
                                _texture_conditioned_one_per_color(grid, texture) != output
                                for grid, output in demos
                            ),
                            f"{texture}-conditioned shortcut survived every demo",
                        )

    def test_every_three_sample_window_contains_orthogonal_context_witness(self):
        """The rule must be demonstrated with a relevant orthogonal cell present."""
        for seed in range(8):
            for start in range(6):
                witnessed = False
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty="medium")
                    for row, col, _color in GEN._classify_centers(grid)["active"]:
                        if any(grid[row + dr][col + dc] != 0 for dr, dc in ORTHOGONALS):
                            witnessed = True
                with self.subTest(seed=seed, start=start):
                    self.assertTrue(witnessed, "blank-orthogonal shortcut survives this lesson")

    def test_active_centers_are_not_confined_to_fixed_mod_three_lattice(self):
        residues = set()
        for seed in range(12):
            for sample_index in range(9):
                grid = GEN.generate(seed, sample_index, difficulty="medium")
                residues.update(
                    (row % 3, col % 3)
                    for row, col, _color in GEN._classify_centers(grid)["active"]
                )
        self.assertGreaterEqual(
            len(residues),
            6,
            f"active centers only occupied residue classes {sorted(residues)}",
        )
        self.assertNotEqual({(1, 1)}, residues)


if __name__ == "__main__":
    unittest.main()
