"""Regressions for the color-4 authority boundary; runnable with unittest."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("canonical_generator", TASK / "generator.py")
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)
AUDIT = (TASK / "counterexamples/review-0697b52e64b4b855-v0001/retained/checks"
         / "audit/c4f6a0585dbf/semantic")


class CanonicalPaletteTests(unittest.TestCase):
    def test_palette_overrides_fail_explicitly(self):
        # Removing advertised metadata alone must not silently ignore this key.
        for value in ("warm", "cool", "broad", "primary", "unknown", "", 4, False):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "palette_kind"):
                    GENERATOR.generate(13, 5, difficulty="medium", palette_kind=value)

    def test_palette_texture_aliases_are_rejected(self):
        for texture in ("warm", "cool", "broad", "primary"):
            with self.subTest(texture=texture):
                with self.assertRaisesRegex(ValueError, "texture"):
                    GENERATOR.generate(13, 5, texture=texture)

    def test_combining_overrides_cannot_restore_recoloring(self):
        for texture in ("warm", "no_targets", "full_grid"):
            with self.subTest(texture=texture):
                with self.assertRaises(ValueError):
                    GENERATOR.generate(13, 5, texture=texture, palette_kind="warm")

    def test_retained_warm_counterexample_is_outside_canonical_domain(self):
        warm = json.loads((AUDIT / "input.json").read_text())
        self.assertTrue(GENERATOR.self_check(warm))

    def test_noncanonical_port_colors_are_rejected(self):
        control = json.loads((AUDIT / "control_input.json").read_text())
        for color in (-1, 2, 3, 5, 6, 7, 8, 9, 10):
            with self.subTest(color=color):
                recolored = [[color if value == 4 else value for value in row]
                             for row in control]
                self.assertTrue(GENERATOR.self_check(recolored))

    def test_no_targets_cannot_bypass_palette_validation(self):
        no_targets = GENERATOR.generate(13, 5, texture="no_targets")
        for color in (-1, 2, 3, 5, 6, 7, 8, 9, 10):
            with self.subTest(color=color):
                recolored = [[color if value == 4 else value for value in row]
                             for row in no_targets]
                self.assertTrue(GENERATOR.self_check(recolored))

    def test_full_grid_only_accepts_canonical_one_color(self):
        for color in (0, 2, 3, 4, 5, 6, 7, 8, 9):
            with self.subTest(color=color):
                self.assertTrue(GENERATOR.self_check([[color] * 23 for _ in range(23)]))

    def test_supported_degenerates_remain_usable(self):
        for texture in ("no_targets", "full_grid"):
            with self.subTest(texture=texture):
                grid = GENERATOR.generate(13, 5, texture=texture)
                self.assertEqual([], GENERATOR.self_check(grid))
                self.assertEqual((23, 23), (len(grid), len(grid[0])))
                self.assertLessEqual({value for row in grid for value in row}, {0, 1, 4})

    def test_none_palette_override_keeps_the_canonical_control(self):
        control = json.loads((AUDIT / "control_input.json").read_text())
        actual = GENERATOR.generate(13, 5, difficulty="medium", palette_kind=None)
        self.assertEqual(control, actual)
        self.assertEqual([], GENERATOR.self_check(actual))

    def test_default_seed_keeps_the_exact_retained_control(self):
        control = json.loads((AUDIT / "control_input.json").read_text())
        actual = GENERATOR.generate(13, 5, difficulty="medium")
        self.assertEqual(control, actual)
        self.assertEqual([], GENERATOR.self_check(actual))


if __name__ == "__main__":
    unittest.main(verbosity=2)
