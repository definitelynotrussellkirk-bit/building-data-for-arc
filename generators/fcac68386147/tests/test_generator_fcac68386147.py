from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.fcac68386147 import generator
from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)


ROOT = find_root(__file__)


def canonical_row():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in load_canonical_pairs(
            generator.TASK_ID,
            root=ROOT,
            labeled_only=True,
        )
    ]


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def independent_rule(grid):
    grid = coerce(grid)
    side = len(grid)
    return [
        [
            grid[row % side][col % side]
            for col in range(side * side)
        ]
        for row in range(side * side)
    ]


def independent_features(grid):
    grid = coerce(grid)
    colors = {
        value for row in grid for value in row if value != 0
    }
    foreground = sum(
        value != 0 for row in grid for value in row
    )
    return {
        "side": len(grid),
        "palette_size": len(colors),
        "foreground_count": foreground,
        "density": foreground / (len(grid) ** 2),
    }


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class Fcac68386147GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_complete_profiles(self):
        self.assertEqual(len(self.pairs), 7)
        profiles = set()
        sides = set()
        colors = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profile = generator.canonical_profile_index(grid)
            self.assertIsNotNone(profile)
            profiles.add(profile)
            features = independent_features(grid)
            sides.add(features["side"])
            colors.update(
                value for row in grid for value in row if value
            )
            self.assertEqual(features["palette_size"], 1)
        self.assertEqual(profiles, set(range(7)))
        self.assertEqual(sides, {2, 3, 4, 5})
        self.assertEqual(colors, {1, 2, 3, 7, 8})

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                    profile = generator.canonical_profile_index(grid)
                    if profile is not None:
                        matches += 1
                        profiles.add(profile)
                self.assertGreaterEqual(matches, 50)
                self.assertLessEqual(matches, 140)
                self.assertEqual(profiles, set(range(7)))
                self.assertGreaterEqual(len(pairs), 570)

    def test_every_axis_value_and_boundary_cross_is_exact(self):
        for side in (2, 3, 4, 5):
            for palette_size in (1, 2, 3):
                grid = generator.generate(
                    side * 101 + palette_size,
                    side * 37 + palette_size,
                    difficulty=("easy", "medium", "hard")[
                        (side + palette_size) % 3
                    ],
                    side=side,
                    palette_size=palette_size,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {
                        "side": side,
                        "palette_size": palette_size,
                    },
                )
                self.assertIsNone(
                    generator.canonical_profile_index(grid)
                    if palette_size > 1
                    else None
                )

    def test_defaults_preserve_binary_majority_and_bounded_extrapolation(self):
        all_sides = set()
        all_palette_sizes = set()
        for band in ("easy", "medium", "hard"):
            palette_counts = Counter()
            side_counts = Counter()
            density_min = 1.0
            density_max = 0.0
            for seed in range(500):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                self.assertEqual(grid, before)
                features = independent_features(grid)
                palette_counts[features["palette_size"]] += 1
                side_counts[features["side"]] += 1
                density_min = min(density_min, features["density"])
                density_max = max(density_max, features["density"])
            self.assertGreater(palette_counts[1], 250)
            self.assertGreater(palette_counts[2], 30)
            self.assertEqual(set(side_counts), {2, 3, 4, 5})
            self.assertGreater(density_max, density_min)
            all_sides.update(side_counts)
            all_palette_sizes.update(palette_counts)
        self.assertEqual(all_sides, {2, 3, 4, 5})
        self.assertEqual(all_palette_sizes, {1, 2, 3})

    def test_profile_metamorphisms_and_color_relabeling(self):
        for index, variants in enumerate(generator._PROFILE_VARIANTS):
            self.assertGreaterEqual(len(variants), 2)
            self.assertEqual(
                len(variants),
                len({tuple(map(tuple, grid)) for grid in variants}),
            )
            for variant_index, binary in enumerate(variants):
                color = 1 + (variant_index % 9)
                grid = [
                    [color if value else 0 for value in row]
                    for row in binary
                ]
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.canonical_profile_index(grid),
                    index,
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

        multicolor = generator.generate(
            83,
            97,
            side=5,
            palette_size=3,
        )
        self.assertEqual(generator.self_check(multicolor), [])
        self.assertIsNone(
            generator.canonical_profile_index(multicolor)
        )
        self.assertEqual(
            generator.rule_mirror(multicolor),
            independent_rule(multicolor),
        )

    def test_periodic_output_uses_both_residue_coordinates(self):
        grid = [
            [1, 2, 0],
            [3, 0, 1],
            [0, 2, 3],
        ]
        output = generator.rule_mirror(grid)
        for row in range(9):
            for col in range(9):
                self.assertEqual(
                    output[row][col],
                    grid[row % 3][col % 3],
                )

        row_only = [
            [grid[row % 3][0] for _col in range(9)]
            for row in range(9)
        ]
        column_only = [
            [grid[0][col % 3] for col in range(9)]
            for _row in range(9)
        ]
        self.assertNotEqual(output, row_only)
        self.assertNotEqual(output, column_only)

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"side": "3"},
            {"side": 3.0},
            {"side": True},
            {"side": 1},
            {"side": 6},
            {"palette_size": 0},
            {"palette_size": 4},
            {"texture": "noise"},
            {"fill_density": 0.5},
            {"noise_overlay": 0.1},
            {"fg_color": 8},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiles = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 41 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                for label in generator.AXES:
                    self.assertEqual(
                        captured[-1]._drawn[label],
                        observed[label],
                    )
                profiles += generator.is_canonical_profile(grid)
        self.assertGreaterEqual(profiles, 85)

        overrides = {"side": 5, "palette_size": 3}
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(91, 117, **overrides)
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn, overrides)
        self.assertEqual(captured[-1]._override_used, overrides)
        self.assertEqual(generator.observe_overrides(grid), overrides)

    def test_self_check_rejects_structural_impostors(self):
        invalid = (
            [],
            [[0]],
            [[0, 0], [0, 0]],
            [[1, 1], [1, 1]],
            [[0, 1, 2], [1, 2, 3]],
            [[0, 1], [2]],
            [[0, 1], [2, 10]],
            [[1, 0], [0, 0]],
            [
                [0, 1, 2, 3],
                [1, 2, 3, 4],
                [2, 3, 4, 1],
                [3, 4, 1, 2],
            ],
            [[0] * 6 for _row in range(6)],
        )
        for grid in invalid:
            self.assertTrue(generator.self_check(grid))

        valid = generator.generate(
            7,
            11,
            side=5,
            palette_size=3,
        )
        ragged = [row[:] for row in valid]
        ragged[0].pop()
        self.assertTrue(generator.self_check(ragged))
        all_background = [[0] * 5 for _row in range(5)]
        self.assertTrue(generator.self_check(all_background))
        monochrome = [[7] * 5 for _row in range(5)]
        self.assertTrue(generator.self_check(monochrome))

    def test_source_sync_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        data_root = canonical_path(ROOT).parents[1]
        base_row = json.loads((
            data_root
            / "base/solutions/training"
            / "ccd554ac__fcac68386147.json"
        ).read_text())
        target = base_row["racket_target"]
        self.assertEqual(
            normalized_rule_hash(target["raw_code"]),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            normalized_rule_hash(target["target_code"]),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        kwargs = {
            "difficulty": "hard",
            "side": 5,
            "palette_size": 3,
        }
        first = generator.generate(17, 23, **kwargs)
        second = generator.generate(17, 23, **kwargs)
        self.assertEqual(first, second)
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = generator.generate(17, 23, **kwargs)
        self.assertNotEqual(first, third)
        self.assertEqual(second, third)

        random.seed(777)
        expected = [random.random() for _ in range(6)]
        random.seed(777)
        generator.generate(31, 37, difficulty="medium")
        actual = [random.random() for _ in range(6)]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
