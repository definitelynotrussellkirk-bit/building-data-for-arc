from __future__ import annotations

import random
import unittest
from collections import Counter

from puzzle_generators import base
from puzzle_generators.per_puzzle.ebe910be6876 import generator
from reviewer_support import canonical_pairs as portable_canonical_pairs
from reviewer_support import find_root


ROOT = find_root(__file__)


def canonical_pairs():
    seen = set()
    for pair in portable_canonical_pairs(generator.TASK_ID, root=ROOT):
        key = (
            tuple(map(tuple, pair["input"])),
            tuple(map(tuple, pair["output"])),
        )
        if key not in seen:
            seen.add(key)
            yield pair["input"], pair["output"]


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0] * (2 * width) for _ in range(2 * height)]
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            start_row = 2 * row - 2
            start_col = 2 * col - 2
            for out_row in range(start_row, start_row + 4):
                for out_col in range(start_col, start_col + 4):
                    if (
                        0 <= out_row < 2 * height
                        and 0 <= out_col < 2 * width
                    ):
                        output[out_row][out_col] = color
    return output


class Ebe910be6876GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), expected)
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
            self.assertEqual((len(expected), len(expected[0])), (20, 20))
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_on_two_ranges(self):
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
                    self.assertEqual(generator.self_check(grid), [])
                    output = independent_rule(grid)
                    pairs.add(
                        (
                            tuple(map(tuple, grid)),
                            tuple(map(tuple, output)),
                        )
                    )
                    signature = generator.canonical_profile_signature(grid)
                    if signature is not None:
                        matches += 1
                        profiles.add(signature)
                self.assertGreaterEqual(matches, 120)
                self.assertLessEqual(matches, 250)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 570)

    def test_forced_dimension_boundaries_are_exact(self):
        for height, width in (
            (6, 6),
            (6, 15),
            (15, 6),
            (15, 15),
        ):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    height * 101 + width,
                    width * 103 + height,
                    difficulty=band,
                    grid_h=height,
                    grid_w=width,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"grid_h": height, "grid_w": width},
                )

    def test_rule_is_exact_aligned_four_by_four_expansion(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(150):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                self.assertEqual(output, independent_rule(grid))
                self.assertEqual(len(output), 2 * len(grid))
                self.assertEqual(len(output[0]), 2 * len(grid[0]))
                markers = generator._markers(grid)
                self.assertEqual(
                    sum(value != 0 for row in output for value in row),
                    16 * len(markers),
                )
                for row, col, color in markers:
                    tile = [
                        values[2 * col - 2:2 * col + 2]
                        for values in output[2 * row - 2:2 * row + 2]
                    ]
                    self.assertEqual(tile, [[color] * 4 for _ in range(4)])

    def test_lawful_cross_profile_recombination_is_not_canonical(self):
        geometry = generator._PROFILE_SPECS[0]["points"]
        colors = [1, 1, 2, 2, 3, 4]
        grid = generator._paint_logical(10, 10, geometry, colors)
        self.assertEqual(generator.self_check(grid), [])
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertIsNone(generator.canonical_profile_signature(grid))
        self.assertEqual(generator.rule_mirror(grid), independent_rule(grid))

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 6},
            {"grid_h": 15},
            {"grid_w": 6},
            {"grid_w": 15},
            {"grid_h": 6, "grid_w": 6},
            {"grid_h": 6, "grid_w": 15},
            {"grid_h": 15, "grid_w": 6},
            {"grid_h": 15, "grid_w": 15},
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                for key, value in kwargs.items():
                    self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "6"},
            {"grid_w": 6.0},
            {"grid_h": True},
            {"grid_h": 5},
            {"grid_h": 16},
            {"grid_w": 5},
            {"grid_w": 16},
            {"texture": "full_grid"},
            {"palette_kind": "warm"},
            {"n_paint": 6},
            {"anchor_corner": True},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_default_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx.axis_value(key), observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 150)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=15,
                grid_w=6,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1].recorded_draws(),
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1].overrides_used(),
            {"grid_h": 15, "grid_w": 6},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(1, 2, grid_h=10, grid_w=10)
        mutations = []

        too_few = [[0] * 10 for _ in range(10)]
        for row, col, color in generator._markers(valid)[:3]:
            too_few[row][col] = color
        mutations.append(too_few)

        even_marker = [row[:] for row in valid]
        row, col, color = generator._markers(even_marker)[0]
        even_marker[row][col] = 0
        even_marker[row - 1][col] = color
        mutations.append(even_marker)

        one_color = [
            [1 if value else 0 for value in row]
            for row in valid
        ]
        mutations.append(one_color)

        too_many = [[0] * 15 for _ in range(15)]
        for index, (row, col) in enumerate(
            (r, c) for r in range(1, 15, 2) for c in range(1, 15, 2)
        ):
            if index == 15:
                break
            too_many[row][col] = 1 + index % 2
        mutations.append(too_many)

        invalid_color = [row[:] for row in valid]
        invalid_color[0][0] = 10
        mutations.append(invalid_color)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[0] * 6 for _ in range(5)])
        mutations.append([[0] * 5 for _ in range(6)])
        mutations.append([[0] * 6 for _ in range(16)])
        mutations.append([[0] * 16 for _ in range(6)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_order_and_cover_lattice_counts_colors_and_diversity(self):
        mean_areas = {}
        mean_counts = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            counts = []
            pairs = set()
            outputs = set()
            profile_counts = Counter()
            palette_sizes = set()
            marker_counts = set()
            spans = set()
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    )
                )
                outputs.add(tuple(map(tuple, output)))
                areas.append(len(grid) * len(grid[0]))
                markers = generator._markers(grid)
                counts.append(len(markers))
                marker_counts.add(len(markers))
                palette_sizes.add(len({value for _r, _c, value in markers}))
                logical = [(row // 2, col // 2)
                           for row, col, _value in markers]
                spans.add((
                    max(row for row, _col in logical)
                    - min(row for row, _col in logical) + 1,
                    max(col for _row, col in logical)
                    - min(col for _row, col in logical) + 1,
                ))
                self.assertTrue(all(
                    row % 2 == col % 2 == 1
                    for row, col, _value in markers
                ))
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profile_counts[signature] += 1
            mean_areas[band] = sum(areas) / len(areas)
            mean_counts[band] = sum(counts) / len(counts)
            self.assertGreaterEqual(len(pairs), 580)
            self.assertGreaterEqual(len(outputs), 580)
            self.assertEqual(
                set(profile_counts),
                generator._CANONICAL_PROFILE_SIGNATURES,
            )
            self.assertGreaterEqual(len(marker_counts), 3)
            self.assertGreaterEqual(len(palette_sizes), 3)
            self.assertGreaterEqual(len(spans), 8)
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])
        self.assertLess(mean_counts["easy"], mean_counts["medium"])
        self.assertLess(mean_counts["medium"], mean_counts["hard"])

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
