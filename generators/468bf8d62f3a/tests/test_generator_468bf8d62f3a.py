"""Focused regression tests for generator 468bf8d62f3a."""
from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "468bf8d62f3a" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_468bf8d62f3a", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "468bf8d62f3a":
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task 468bf8d62f3a is missing")


class VerticalRunGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gen = load_generator()

    def test_rule_hash_and_every_canonical_input(self):
        self.assertEqual("7fb4ccc318f8", self.gen.RULE_HASH)
        for index, grid in enumerate(canonical_inputs()):
            with self.subTest(index=index):
                self.assertEqual([], self.gen.self_check(grid))
                self.assertEqual([], self.gen.strict_canonical_like(grid))

    def test_override_boundaries_are_exact_and_observable(self):
        cases = [
            dict(grid_h=6, grid_w=7, run_count=3, n_distinct_colors=2),
            dict(grid_h=11, grid_w=11, run_count=6, n_distinct_colors=3),
        ]
        for layout in self.gen._LAYOUTS:
            for case in cases:
                with self.subTest(layout=layout, case=case):
                    grid = self.gen.generate(
                        1201, 19, difficulty="hard", layout_mode=layout, **case
                    )
                    observed = self.gen.observe_overrides(grid)
                    self.assertEqual(case["grid_h"], len(grid))
                    self.assertEqual(case["grid_w"], len(grid[0]))
                    self.assertEqual(case["run_count"], observed["run_count"])
                    self.assertEqual(
                        case["n_distinct_colors"], observed["n_distinct_colors"]
                    )
                    self.assertEqual(layout, observed["layout_mode"])
                    self.assertEqual([], self.gen.self_check(grid))

    def test_removed_dead_texture_axis_is_loud(self):
        with self.assertRaisesRegex(ValueError, "unknown override axis"):
            self.gen.generate(42, 0, texture="warm")

    def test_default_schedule_refutes_named_shortcuts(self):
        seed = 987654
        pairs = []
        modes = []
        for sample_index in range(4):
            grid = self.gen.generate(seed, sample_index)
            modes.append(self.gen.observe_overrides(grid)["layout_mode"])
            pairs.append({"input": grid, "output": self.gen.rule_mirror(grid)})
        self.assertEqual(
            [
                "separate_columns",
                "stacked_gaps",
                "touching_colors",
                "separate_columns",
            ],
            modes,
        )
        self.assertTrue(self.gen._has_repeated_colour_runs(pairs[1]["input"]))
        self.assertEqual([], self.gen.lesson_identifiable(pairs[:3], pairs[3]))

    def test_self_check_rejects_four_structural_impostors(self):
        base = [
            [1, 0, 0, 2, 0, 0, 0],
            [1, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 3],
            [0, 0, 0, 0, 0, 0, 3],
            [0, 0, 0, 0, 0, 0, 0],
        ]
        self.assertEqual([], self.gen.self_check(base))

        singleton = [row[:] for row in base]
        singleton[1][0] = 0

        horizontal_recombination = [row[:] for row in base]
        horizontal_recombination[3][6] = 0
        horizontal_recombination[4][6] = 0
        horizontal_recombination[5][4] = 3
        horizontal_recombination[5][5] = 3

        too_few_runs = [row[:] for row in base]
        for r in range(len(too_few_runs)):
            too_few_runs[r][3] = 0
            too_few_runs[r][6] = 0

        too_many_colours = [row[:] for row in base]
        too_many_colours[3][1] = 4
        too_many_colours[4][1] = 4

        impostors = {
            "singleton": singleton,
            "horizontal_recombination": horizontal_recombination,
            "too_few_runs": too_few_runs,
            "too_many_colours": too_many_colours,
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.gen.self_check(grid))

        # Distribution rejection and oracle executability are separate facts.
        self.assertEqual(
            len(horizontal_recombination),
            len(self.gen.rule_mirror(horizontal_recombination)),
        )

    def test_replay_returns_fresh_objects_without_touching_global_rng(self):
        random.seed(4444)
        before = random.getstate()
        first = self.gen.generate(77, 22, difficulty="medium")
        after = random.getstate()
        self.assertEqual(before, after)

        pristine = [row[:] for row in first]
        first[0][0] = 9 if first[0][0] != 9 else 8
        second = self.gen.generate(77, 22, difficulty="medium")
        self.assertEqual(pristine, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))

    def test_strict_anchor_and_each_witness_fire_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            strict = 0
            hits = {name: 0 for name in self.gen.SEMANTIC_WITNESSES}
            for index in range(90):
                grid = self.gen.generate(91000 + index, index, difficulty=band)
                strict += not self.gen.strict_canonical_like(grid)
                for name, predicate in self.gen.SEMANTIC_WITNESSES.items():
                    hits[name] += bool(predicate(grid))
            with self.subTest(band=band, strict=strict, hits=hits):
                self.assertGreaterEqual(strict, 25)
                self.assertTrue(all(count > 0 for count in hits.values()))


if __name__ == "__main__":
    unittest.main()
