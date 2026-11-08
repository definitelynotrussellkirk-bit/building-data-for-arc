"""Canonical basin acceptance and exact, feasible override behavior."""
import importlib.util

import unittest

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs, find_root

TASK_ID = "c1ae510562f9"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.exists():
    SOURCE = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("contract_test_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

AXIS_RANGES = {"grid_h": (5, 16), "grid_w": (6, 16),
               "interior_h": (2, 12), "interior_w": (1, 10),
               "empty_rows": (0, 10)}


def measure(grid):
    """Recover exact controls independently from gray container geometry."""
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    top, bottom = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "interior_h": bottom - top, "interior_w": right - left - 1,
            "empty_rows": sum(all(v == 0 for v in grid[r][left + 1:right])
                              for r in range(top, bottom))}


class OverrideContractTests(unittest.TestCase):
    def test_canonical_inputs_are_accepted(self):
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            with self.subTest(variant=pair["variant"], split=pair["split"], index=pair["pair_index"]):
                self.assertEqual(GEN.self_check(pair["input"]), [])

    def test_axes_are_the_supported_exact_controls(self):
        self.assertEqual(set(GEN.AXES), set(AXIS_RANGES))

    def test_unknown_and_retired_controls_rejected(self):
        for name in ("typo_axis", "pillar_h_min", "pillar_h_max", "position_bias",
                     "anchor_corner", "texture", "c1", "c2"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                GEN.generate(17, 3, difficulty="medium", **{name: 1})

    def test_single_axis_boundaries_are_feasible_and_observed(self):
        for band in ("easy", "medium", "hard"):
            for name, endpoints in AXIS_RANGES.items():
                for value in endpoints:
                    with self.subTest(band=band, name=name, value=value):
                        contexts = []
                        set_ctx_observer(contexts.append)
                        try:
                            grid = GEN.generate(17, 3, difficulty=band, **{name: value})
                        finally:
                            set_ctx_observer(None)
                        self.assertEqual(GEN.self_check(grid), [])
                        actual = measure(grid)
                        self.assertEqual(actual[name], value)
                        self.assertEqual(GEN.observe_overrides(grid), actual)
                        self.assertEqual(contexts[-1].overrides_used()[name], value)

    def test_exact_integer_controls_reject_coercion(self):
        for name in AXIS_RANGES:
            for value in (True, 7.0, "7"):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    GEN.generate(17, 3, **{name: value})

    def test_none_is_unpinned(self):
        for name in AXIS_RANGES:
            with self.subTest(name=name):
                self.assertEqual(GEN.generate(17, 3, **{name: None}), GEN.generate(17, 3))

    def test_impossible_pinned_pairs_rejected_with_actual_axes(self):
        cases = [
            ({"grid_h": 5, "interior_h": 12}, {"grid_h", "interior_h"}),
            ({"grid_w": 6, "interior_w": 10}, {"grid_w", "interior_w"}),
            ({"interior_h": 2, "empty_rows": 2}, {"interior_h", "empty_rows"}),
            ({"grid_h": 5, "empty_rows": 10}, {"grid_h", "empty_rows"}),
        ]
        for case, conflict in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError) as caught:
                    GEN.generate(17, 3, **case)
                self.assertEqual(set(caught.exception.incompatible_axes), conflict)

    def test_joint_feasible_extremes_and_default_provenance(self):
        cases = [
            {"grid_h": 5, "grid_w": 6, "interior_h": 2, "interior_w": 1, "empty_rows": 0},
            {"grid_h": 16, "grid_w": 16, "interior_h": 12, "interior_w": 10, "empty_rows": 10},
        ]
        for case in cases:
            with self.subTest(case=case):
                grid = GEN.generate(17, 3, **case)
                self.assertEqual(measure(grid), case)
                self.assertEqual(GEN.self_check(grid), [])
                contexts = []
                set_ctx_observer(contexts.append)
                try:
                    default = GEN.generate(17, 3)
                finally:
                    set_ctx_observer(None)
                self.assertEqual(GEN.observe_overrides(default), measure(default))
                self.assertEqual({name: contexts[-1].axis_value(name) for name in AXIS_RANGES}, measure(default))


if __name__ == "__main__":
    unittest.main()
