"""Task-local threshold prototype checks; separate from canonical repair coverage."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "520fe6e64fb6"
ROOT = find_root(__file__)


def prototype():
    path = ROOT / "generators" / TASK / "workspace/parametric/threshold.py"
    assert path.is_file(), "task-local threshold prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("_threshold_520fe6e64fb6", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fixture_grid():
    grid = [[6] * 9 for _ in range(9)]
    grid[1][3] = grid[1][5] = 9  # disconnected 9s: their global span is 3..5
    for c in range(3, 7):
        grid[7][c] = 7
    for r, columns in ((3, (0,)), (4, (0, 8)), (5, (0, 4, 8))):
        for c in columns:
            grid[r][c] = 0
    grid[4][4] = 1  # original non-background cell must survive a trigger
    return grid


def transpose(grid):
    return [list(row) for row in zip(*grid)]


class ThresholdPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge()
        cls._episodes = None

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def episodes(self):
        if self.__class__._episodes is None:
            p = prototype()
            self.__class__._episodes = {value: p.build_episode(17, self.bridge, value) for value in p.SETTINGS}
        return self.__class__._episodes

    def test_threshold_changes_executed_trigger_without_changing_roles(self):
        p = prototype()
        for min_zeros in (1, 2, 3):
            for horizontal in (False, True):
                with self.subTest(min_zeros=min_zeros, horizontal=horizontal):
                    grid = fixture_grid()
                    expected = [row[:] for row in grid]
                    expected[1][3] = expected[1][5] = 7
                    for c in range(3, 7):
                        expected[7][c] = 6
                    for count, row in ((1, 3), (2, 4), (3, 5)):
                        if count >= min_zeros:
                            for col in range(3, 6):
                                if grid[row][col] == 6:
                                    expected[row][col] = 2
                    if horizontal:
                        grid, expected = transpose(grid), transpose(expected)
                    before = [row[:] for row in grid]
                    self.assertEqual(p.execute(self.bridge, p.program(min_zeros), grid), expected)
                    self.assertEqual(grid, before)

    def test_horizontal_fallback_uses_min_columns_even_with_row_misalignment(self):
        p = prototype()
        for min_zeros in (1, 2, 3):
            with self.subTest(min_zeros=min_zeros):
                aligned = transpose(fixture_grid())
                off_axis = [row[:] for row in aligned]
                positions = [(r, c) for r, row in enumerate(off_axis) for c, value in enumerate(row) if value == 7]
                for r, c in positions:
                    off_axis[r][c] = 6
                for r, c in positions:
                    off_axis[r + 1][c] = 7
                expected = p.execute(self.bridge, p.program(min_zeros), aligned)
                self.assertEqual(p.execute(self.bridge, p.program(min_zeros), off_axis), expected)

    def test_default_is_exact_selected_authority_and_matches_all_canonical_labels(self):
        p = prototype()
        gen, _, _ = load_selected_generator(TASK, root=ROOT)
        self.assertEqual(p.DEFAULT, 1)
        self.assertEqual(p.SETTINGS, (1, 2, 3))
        self.assertEqual(p.program(), p.canonical_program())
        pairs = canonical_pairs(TASK, root=ROOT)
        self.assertEqual(len(pairs), 8)
        for pair in pairs:
            self.assertEqual(gen.self_check(pair["input"]), [])
            self.assertEqual(p.execute(self.bridge, p.program(), pair["input"]), pair["output"])

    def test_invalid_thresholds_are_rejected_without_coercion(self):
        for invalid in (0, 4, -1, True, False, 1.0, "2", None):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "min_zeros"):
                    prototype().program(invalid)

    def test_complete_episodes_are_racket_labeled_and_identifiable_in_every_query_rotation(self):
        p = prototype()
        gen, _, _ = load_selected_generator(TASK, root=ROOT)
        for setting, (public, private) in self.episodes().items():
            with self.subTest(min_zeros=setting):
                self.assertEqual(set(public), {"train", "test"})
                self.assertEqual(len(public["train"]), 3)
                self.assertEqual(len(public["test"]), 1)
                self.assertEqual(set(public["test"][0]), {"input"})
                self.assertEqual(private["parameters"], {"min_zeros": setting})
                self.assertEqual(private["reference_program"], p.program(setting))
                self.assertEqual(len(private["query_outputs"]), 1)
                self.assertEqual(len(private["pairs"]), 4)
                self.assertEqual(len({p.encoded(pair["input"]) for pair in private["pairs"]}), 4)
                for index, pair in enumerate(private["pairs"]):
                    self.assertEqual(gen.self_check(pair["input"]), [])
                    outputs = pair["outputs"]
                    self.assertEqual(len({p.encoded(value) for value in outputs.values()}), 3)
                    for rival in p.SETTINGS:
                        self.assertEqual(outputs[str(rival)], p.execute(self.bridge, p.program(rival), pair["input"]))
                    target = public["train"][index]["output"] if index < 3 else private["query_outputs"][0]
                    self.assertEqual(target, outputs[str(setting)])
                checks = private["identifiability"]
                self.assertEqual(checks["production_status"], "no_ambiguity_found")
                self.assertEqual(checks["rotation_status"], "no_ambiguity_found")
                self.assertEqual(len(checks["rotations"]), 4)
                for rotation in checks["rotations"]:
                    self.assertEqual(len(rotation["rivals"]), 2)
                    for rival in rotation["rivals"]:
                        self.assertEqual(rival["status"], "eliminated")
                        self.assertIs(rival["query_differs"], True)
                        self.assertEqual(len(rival["demo_mismatches"]), 3)

    def test_deterministic_rule_is_selected_once_per_episode_without_global_rng_changes(self):
        p = prototype()
        random.seed(9839)
        before = random.getstate()
        chosen = p.choose_min_zeros(17)
        self.assertIn(chosen, p.SETTINGS)
        self.assertEqual(p.build_episode(17, self.bridge), self.episodes()[chosen])
        self.assertEqual(random.getstate(), before)
        self.assertEqual(p.build_episode(17, self.bridge, 2), self.episodes()[2])
        self.assertEqual(p.choose_min_zeros(17), chosen)

    def test_negative_control_reports_actual_parameter_ambiguity(self):
        p = prototype()
        grid = fixture_grid()
        uninformative = [row[:] for row in grid]
        for r in (3, 4):
            uninformative[r] = [6 if v == 0 else v for v in uninformative[r]]
        pairs = [{"input": value, "outputs": p.outputs_for(self.bridge, value)}
                 for value in (uninformative, uninformative, uninformative, grid)]
        checks = p.identifiability(pairs, 2)
        self.assertEqual(checks["production_status"], "ambiguous")
        original = checks["rotations"][3]
        self.assertTrue(all(rival["status"] == "ambiguous" for rival in original["rivals"]))
        self.assertTrue(all(rival["demo_mismatches"] == [] for rival in original["rivals"]))
        self.assertTrue(all(rival["query_differs"] for rival in original["rivals"]))
        self.assertEqual(checks["rotation_status"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
