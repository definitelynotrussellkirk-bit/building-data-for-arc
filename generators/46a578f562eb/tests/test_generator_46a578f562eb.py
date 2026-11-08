"""Focused semantic tests for generator 46a578f562eb."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from itertools import permutations
from pathlib import Path


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.46a578f562eb.generator"
)

ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + (
        test if isinstance(test, list) else [test]
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def independent_rule(grid):
    output = [row[:] for row in grid]
    for col in range(len(grid[0])):
        topmost = None
        for row in range(len(grid)):
            value = grid[row][col]
            if value != 0:
                if topmost is None:
                    topmost = value
            elif topmost is not None:
                output[row][col] = topmost
    return output


def permute_columns(grid, order):
    result = [[0 for _col in order] for _row in grid]
    for row in range(len(grid)):
        for old_col, new_col in enumerate(order):
            result[row][new_col] = grid[row][old_col]
    return result


class Generator46a578f562ebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 4)
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            snapshot = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, snapshot)

    def test_column_and_color_permutation_metamorphisms(self):
        for pair in self.pairs:
            for order in permutations(range(3)):
                transformed_input = permute_columns(
                    pair["input"], order
                )
                transformed_output = permute_columns(
                    pair["output"], order
                )
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    independent_rule(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.self_check(transformed_input),
                    [],
                )
            mapping = {
                value: 10 - value
                for row in pair["input"]
                for value in row
                if value != 0
            }
            recolored_input = [
                [mapping.get(value, value) for value in row]
                for row in pair["input"]
            ]
            recolored_output = [
                [mapping.get(value, value) for value in row]
                for row in pair["output"]
            ]
            self.assertEqual(
                generator.rule_mirror(recolored_input),
                recolored_output,
            )

    def test_every_exact_axis_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for layout_index, layout in enumerate(
                    generator.LAYOUT_MODES
                ):
                    for canvas_index, canvas in enumerate(
                        generator.CANVAS_MODES
                    ):
                        seed = (
                            10_000
                            + 100 * profile_index
                            + 20 * layout_index
                            + 10 * canvas_index
                            + len(band)
                        )
                        grid = generator.generate(
                            seed,
                            seed * 19 + 3,
                            difficulty=band,
                            scene_profile=profile,
                            layout_mode=layout,
                            canvas_mode=canvas,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "layout_mode": layout,
                                "canvas_mode": canvas,
                            },
                        )
                        self.assertEqual(
                            generator.rule_mirror(grid),
                            independent_rule(grid),
                        )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, layout_mode="rotated")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, canvas_mode="unbounded")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_distribution_is_complete_stable_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = set()
                layouts = set()
                canvases = set()
                pairs = set()
                for offset in range(180):
                    seed = start + band_index * 10_000 + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.rule_mirror(grid), output
                    )
                    profiles.add(observed["scene_profile"])
                    layouts.add(observed["layout_mode"])
                    canvases.add(observed["canvas_mode"])
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                self.assertEqual(
                    profiles, set(generator.SCENE_PROFILES)
                )
                self.assertEqual(
                    layouts, set(generator.LAYOUT_MODES)
                )
                self.assertEqual(
                    canvases, set(generator.CANVAS_MODES)
                )
                self.assertGreaterEqual(len(pairs), 175)

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = self.pairs[0]["input"]
        repeated_color = [row[:] for row in original]
        repeated_color[1][0] = repeated_color[0][1]
        repeated_column = [row[:] for row in original]
        repeated_column[1][0] = 0
        repeated_column[2][1] = 7
        uncalibrated_rows = [row[:] for row in original]
        uncalibrated_rows[1][0] = 0
        uncalibrated_rows[0][0] = 7
        extra_seed = [row[:] for row in original]
        extra_seed[2][0] = 4
        invalid_color = [row[:] for row in original]
        invalid_color[2][2] = 10
        for mutation in (
            repeated_color,
            repeated_column,
            uncalibrated_rows,
            extra_seed,
            invalid_color,
            [],
            original[:-1],
            original + [[0, 0, 0]] * 4,
            [row[:-1] for row in original],
            [[True, 0, 0], [0, 2, 0], [0, 0, 0]],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_lawful_unpublished_recombinations_are_calibrated_out(self):
        row_recombination = [
            [1, 2, 0],
            [0, 0, 3],
            [0, 0, 0],
        ]
        stacked_seeds = [
            [1, 0, 2],
            [3, 0, 0],
            [0, 0, 0],
        ]
        for candidate in (row_recombination, stacked_seeds):
            self.assertTrue(generator.self_check(candidate))
            self.assertEqual(
                generator.rule_mirror(candidate),
                independent_rule(candidate),
            )

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        base = json.loads((
            ROOT
            / "data/base/solutions/training/"
            "d037b0a7__46a578f562eb.json"
        ).read_text())["racket_target"]
        self.assertEqual(base["raw_code"], source)
        self.assertEqual(base["target_code"], source)
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        state = random.getstate()
        first = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        snapshot = [row[:] for row in first]
        generator.generate(91, 97, difficulty="easy")
        self.assertEqual(first, snapshot)
        again = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(
            old_row is not new_row
            for old_row, new_row in zip(first, again)
        ))
        first[0][0] = 1 if first[0][0] != 1 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
