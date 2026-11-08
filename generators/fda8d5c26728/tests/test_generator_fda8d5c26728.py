"""Focused regression tests for the row-selector generator repair."""
from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "fda8d5c26728" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_fda8d5c26728",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "fda8d5c26728":
                continue
            test_rows = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [pair["input"] for pair in [*row["train"], *test_rows]]
    raise AssertionError("canonical task fda8d5c26728 is missing")


def apply_rule(grid: list[list[int]]) -> list[list[int]]:
    color_map = (2, 4, 3)
    return [
        [color_map[next(col for col, value in enumerate(row) if value == 5)]]
        * len(row)
        for row in grid
    ]


class RowSelectorGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_self_check_accepts_every_canonical_input(self):
        inputs = canonical_inputs()
        self.assertEqual(5, len(inputs))
        for index, grid in enumerate(inputs):
            with self.subTest(index=index):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertTrue(self.generator.is_canonical_like(grid))

    def test_exact_axes_are_realized_and_observable(self):
        grid = self.generator.generate(
            991,
            17,
            difficulty="easy",
            grid_h=2,
            grid_w=18,
            bg_color=1,
            selector_pattern="reverse_cycle",
            decoy_count=6,
        )
        self.assertEqual(
            {"grid_h": 2, "grid_w": 18, "bg_color": 1, "decoy_count": 6},
            self.generator.observe_overrides(grid),
        )
        self.assertEqual([], self.generator.self_check(grid))
        self.assertEqual((2, 1), self.generator.profile_signature(grid)["selectors"])

    def test_incompatible_exact_decoy_request_rejects_loudly(self):
        with self.assertRaises(ValueError):
            self.generator.generate(
                1,
                2,
                difficulty="hard",
                grid_h=2,
                grid_w=3,
                decoy_count=6,
            )

    def test_each_selector_pattern_fires_and_has_one_answer(self):
        for index, pattern in enumerate(self.generator.SELECTOR_PATTERNS):
            grid = self.generator.generate(
                300 + index,
                700 + index,
                difficulty="medium",
                grid_h=6,
                grid_w=7,
                bg_color=6,
                selector_pattern=pattern,
                decoy_count=4,
            )
            with self.subTest(pattern=pattern):
                self.assertEqual([], self.generator.self_check(grid))
                output = apply_rule(grid)
                facts = self.generator.profile_signature(grid)
                for row, selector in enumerate(facts["selectors"]):
                    self.assertEqual([{0: 2, 1: 4, 2: 3}[selector]] * 7, output[row])

    def test_canonical_prior_is_substantial_and_all_generalized_branches_appear(self):
        for band, minimum in (("easy", 90), ("medium", 60), ("hard", 25)):
            canonical_like = 0
            shapes: set[tuple[int, int]] = set()
            backgrounds: set[int] = set()
            selector_counts = {col: 0 for col in range(3)}
            saw_decoy = False
            for seed in range(200):
                grid = self.generator.generate(seed + 1000, seed * 17 + 5, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                facts = self.generator.profile_signature(grid)
                canonical_like += int(self.generator.is_canonical_like(grid))
                shapes.add((facts["grid_h"], facts["grid_w"]))
                backgrounds.add(facts["bg_color"])
                saw_decoy |= facts["decoy_count"] > 0
                for selector in facts["selectors"]:
                    selector_counts[selector] += 1
            with self.subTest(band=band):
                self.assertGreaterEqual(canonical_like, minimum)
                self.assertGreater(len(shapes), 2)
                self.assertGreater(len(backgrounds), 2)
                self.assertTrue(saw_decoy)
                self.assertTrue(all(count > 0 for count in selector_counts.values()))

    def test_structural_mutations_are_rejected_and_recombinations_distinguished(self):
        valid = self.generator.generate(
            55,
            66,
            difficulty="medium",
            grid_h=3,
            grid_w=6,
            bg_color=0,
            selector_pattern="cycle_012",
            decoy_count=3,
        )
        mutations: list[list[list[int]]] = []

        missing_selector = [row[:] for row in valid]
        missing_selector[0] = [0 if value == 5 else value for value in missing_selector[0]]
        mutations.append(missing_selector)

        two_selectors = [row[:] for row in valid]
        two_selectors[1][0] = 5
        two_selectors[1][1] = 5
        mutations.append(two_selectors)

        illegal_background = [row[:] for row in valid]
        for row in range(len(illegal_background)):
            for col in range(len(illegal_background[0])):
                if illegal_background[row][col] != 5:
                    illegal_background[row][col] = 2
        mutations.append(illegal_background)

        too_many_decoys = [row[:] for row in valid]
        for row in range(len(too_many_decoys)):
            for col in range(3, len(too_many_decoys[0])):
                too_many_decoys[row][col] = 5
        mutations.append(too_many_decoys)

        for index, grid in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertTrue(self.generator.self_check(grid))

        canonical = canonical_inputs()[0]
        widened = [row + [0] for row in canonical]
        recolored = [[1 if value == 0 else value for value in row] for row in canonical]
        self.assertFalse(self.generator.is_canonical_like(widened))
        self.assertFalse(self.generator.is_canonical_like(recolored))
        # Both recombinations are lawful for the broader rule, so this makes
        # the separate teaching-distribution/oracle distinction explicit.
        self.assertEqual([], self.generator.self_check(widened))
        self.assertEqual([], self.generator.self_check(recolored))
        self.assertEqual(3, len(apply_rule(widened)))
        self.assertEqual(3, len(apply_rule(recolored)))

    def test_replay_is_fresh_and_preserves_process_global_rng(self):
        state = random.getstate()
        first = self.generator.generate(777, 888, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(777, 888, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
