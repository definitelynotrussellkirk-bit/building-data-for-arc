"""Regression tests for the concentric-layer generator repair."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "8291f3ee7e54"
GENERATOR_PATH = TASK_ROOT / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


def teaching_distractor_input() -> list[list[int]]:
    grid = [[0 for _ in range(12)] for _ in range(12)]

    def paint_frame(top: int, left: int, side: int, color: int) -> None:
        for r in range(top, top + side):
            for c in range(left, left + side):
                if r in (top, top + side - 1) or c in (left, left + side - 1):
                    grid[r][c] = color

    paint_frame(1, 1, 5, 2)
    paint_frame(7, 1, 3, 3)
    grid[11][11] = 4
    grid[1][7] = 2
    return grid


class ConcentricLayerProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.official_inputs = canonical_inputs()

    def test_all_official_inputs_match_the_complete_linked_profile_set(self):
        signatures = {
            self.generator.canonical_profile_signature(grid)
            for grid in self.official_inputs
        }
        self.assertNotIn(None, signatures)
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)
        for grid in self.official_inputs:
            self.assertEqual([], self.generator.self_check(grid))

    def test_default_prior_reaches_every_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {
                signature: 0
                for signature in self.generator._CANONICAL_SIGNATURES
            }
            for seed in range(600):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 1,
                    difficulty=band,
                )
                self.assertEqual(
                    [],
                    self.generator.self_check(grid, difficulty=band),
                )
                signature = self.generator.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1

            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 150)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_near_miss_is_lawful_but_not_an_official_profile(self):
        changed = [row[:] for row in self.official_inputs[0]]
        self.assertEqual(4, changed[1][3])
        changed[1][3] = 0

        self.assertEqual([], self.generator.self_check(changed))
        self.assertIsNone(
            self.generator.canonical_profile_signature(changed)
        )

    def test_exact_generalized_axes_hit_boundaries(self):
        cases = (
            {"layout_kind": "scattered", "grid_size": 12, "n_layers": 3},
            {"layout_kind": "overlap", "grid_size": 22, "n_layers": 5},
            {"layout_kind": "clipped", "grid_size": 12, "n_layers": 3},
            {"layout_kind": "clipped", "grid_size": 22, "n_layers": 5},
        )
        for index, overrides in enumerate(cases):
            grid = self.generator.generate(
                9000 + index,
                100 + index,
                difficulty="hard",
                **overrides,
            )
            with self.subTest(overrides=overrides):
                self.assertEqual(overrides["grid_size"], len(grid))
                self.assertEqual(
                    overrides["n_layers"],
                    self.generator.observe_overrides(grid)["n_layers"],
                )
                self.assertEqual([], self.generator.self_check(grid))


    def test_external_singleton_distractor_is_lawful_and_teaches_component_selection(self):
        grid = teaching_distractor_input()
        self.assertEqual([], self.generator.self_check(grid))

        layers = self.generator._layer_analysis(grid)
        self.assertEqual([5, 3, 1], [layer["span"] for layer in layers])
        self.assertEqual([7, 3, 1], [layer["union_span"] for layer in layers])
        self.assertEqual(1, layers[0]["distractor_count"])

    def test_two_detached_singletons_are_outside_the_controlled_grammar(self):
        grid = teaching_distractor_input()
        grid[7][7] = 2

        errors = self.generator.self_check(grid)
        self.assertTrue(errors)
        self.assertTrue(
            any("unsupported disconnected cells" in error for error in errors),
            errors,
        )

    def test_distractor_layout_emits_a_union_bbox_counterexample(self):
        for index, overrides in enumerate(
            (
                {"grid_size": 12, "n_layers": 3},
                {"grid_size": 22, "n_layers": 5},
            )
        ):
            grid = self.generator.generate(7300 + index, 19 + index, layout_kind="distractor", **overrides)
            layers = self.generator._layer_analysis(grid)
            with self.subTest(overrides=overrides):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertTrue(any(layer["union_span"] > layer["span"] for layer in layers))
                self.assertEqual(1, sum(layer["distractor_count"] for layer in layers))

    def test_canonical_layout_remains_an_exact_linked_profile(self):
        grid = self.generator.generate(17, 3, layout_kind="canonical")
        self.assertIsNotNone(self.generator.canonical_profile_signature(grid))
        self.assertTrue(
            all(
                layer["union_span"] == layer["span"]
                and layer["distractor_count"] == 0
                for layer in self.generator._layer_analysis(grid)
            )
        )

    def test_canonical_overrides_reject_impossible_recombinations(self):
        with self.assertRaises(ValueError):
            self.generator.generate(
                1,
                2,
                difficulty="easy",
                layout_kind="canonical",
                grid_size=12,
                n_layers=3,
            )


if __name__ == "__main__":
    unittest.main()
