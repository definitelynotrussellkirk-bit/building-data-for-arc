from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.ec1260207f71 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    seen = set()
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split) or []:
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
    edge_rows = {
        "left": [r for r in range(height) if grid[r][0] == 2],
        "right": [r for r in range(height) if grid[r][-1] == 2],
    }
    dots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    dot_side = next(
        side
        for side, rows in edge_rows.items()
        if {r for r, _c in dots}.issubset(set(rows))
    )
    plain_side = "right" if dot_side == "left" else "left"
    dot_start = min(edge_rows[dot_side])
    plain_start = min(edge_rows[plain_side])
    dot_edge = 0 if dot_side == "left" else width - 1
    plain_edge = width - 1 if dot_side == "left" else 0

    output = [row[:] for row in grid]
    for row, marker_col in dots:
        offset = row - dot_start
        lo, hi = sorted((dot_edge, marker_col))
        for col in range(lo + 1, hi):
            output[row][col] = 8
        output[row][marker_col] = 4
        for col in range(width):
            if col != plain_edge:
                output[plain_start + offset][col] = 8
    return output


class Ec1260207f71GeneratorTests(unittest.TestCase):
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
            self.assertEqual(
                (len(expected), len(expected[0])),
                (len(grid), len(grid[0])),
            )
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_without_harming_diversity(self):
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
                self.assertGreaterEqual(matches, 20)
                self.assertLessEqual(matches, 75)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 545)

    def test_forced_dimension_side_and_band_boundaries_are_exact(self):
        for height, width in (
            (14, 7),
            (14, 16),
            (28, 7),
            (28, 16),
        ):
            for side in ("left", "right"):
                for dot_band in ("upper", "lower"):
                    for band in ("easy", "medium", "hard"):
                        grid = generator.generate(
                            height * 101 + width,
                            width * 103 + height,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            dot_side=side,
                            dot_band=dot_band,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {
                                "grid_h": height,
                                "grid_w": width,
                                "dot_side": side,
                                "dot_band": dot_band,
                            },
                        )

    def test_rule_is_exact_offset_transfer_and_partial_join(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                output = generator.rule_mirror(grid)
                self.assertEqual(output, independent_rule(grid))
                self.assertEqual(grid, before)

                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                width = features["grid_w"]
                dot_edge = 0 if features["dot_side"] == "left" else width - 1
                plain_edge = width - 1 if dot_edge == 0 else 0
                selected_rows = set()
                for offset, marker_col in features["dots"]:
                    dot_row = features["dot_start"] + offset
                    plain_row = features["plain_start"] + offset
                    selected_rows.update((dot_row, plain_row))
                    self.assertEqual(output[dot_row][marker_col], 4)
                    lo, hi = sorted((dot_edge, marker_col))
                    self.assertTrue(all(
                        output[dot_row][col] == 8
                        for col in range(lo + 1, hi)
                    ))
                    self.assertTrue(all(
                        output[plain_row][col] == (2 if col == plain_edge else 8)
                        for col in range(width)
                    ))
                for row in range(len(grid)):
                    if row not in selected_rows:
                        self.assertEqual(output[row], grid[row])

    def test_lawful_cross_profile_recombination_is_not_canonical(self):
        grid = generator._draw_scene(
            20,
            10,
            5,
            1,
            11,
            "left",
            "upper",
            ((1, 6), (3, 5)),
        )
        self.assertEqual(generator.self_check(grid), [])
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertIsNone(generator.canonical_profile_signature(grid))
        self.assertEqual(generator.rule_mirror(grid), independent_rule(grid))

    def test_boundaries_removed_controls_and_strict_types(self):
        boundary_calls = (
            {"grid_h": 14},
            {"grid_h": 28},
            {"grid_w": 7},
            {"grid_w": 16},
            {"dot_side": "left"},
            {"dot_side": "right"},
            {"dot_band": "upper"},
            {"dot_band": "lower"},
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
            {"grid_h": "14"},
            {"grid_w": 7.0},
            {"grid_h": True},
            {"grid_h": 13},
            {"grid_h": 29},
            {"grid_w": 6},
            {"grid_w": 17},
            {"dot_side": 1},
            {"dot_side": "center"},
            {"dot_band": False},
            {"dot_band": "middle"},
            {"bar_col_offset": 1},
            {"n_dots": 3},
            {"texture": "full_grid"},
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
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 25)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=28,
                grid_w=7,
                dot_side="right",
                dot_band="lower",
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {
                "grid_h": 28,
                "grid_w": 7,
                "dot_side": "right",
                "dot_band": "lower",
            },
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator._draw_scene(
            18,
            9,
            5,
            1,
            11,
            "left",
            "upper",
            ((0, 3), (4, 6)),
        )
        self.assertEqual(generator.self_check(valid), [])
        mutations = []

        missing_bar = [row[:] for row in valid]
        for row in missing_bar:
            row[-1] = 0
        mutations.append(missing_bar)

        inward_bar = [row[:] for row in valid]
        for row in inward_bar:
            if row[-1] == 2:
                row[-1] = 0
                row[-2] = 2
        mutations.append(inward_bar)

        unequal = [row[:] for row in valid]
        unequal[11][-1] = 0
        mutations.append(unequal)

        noncontiguous = [row[:] for row in valid]
        noncontiguous[13][-1] = 0
        noncontiguous[16][-1] = 2
        mutations.append(noncontiguous)

        overlapping = [[0] * 9 for _ in range(18)]
        for offset in range(5):
            overlapping[1 + offset][0] = 2
            overlapping[5 + offset][-1] = 2
        overlapping[2][3] = 8
        mutations.append(overlapping)

        no_dots = [
            [0 if value == 8 else value for value in row]
            for row in valid
        ]
        mutations.append(no_dots)

        same_row_dots = [row[:] for row in valid]
        same_row_dots[1][5] = 8
        mutations.append(same_row_dots)

        split_dots = [row[:] for row in valid]
        split_dots[12][4] = 8
        mutations.append(split_dots)

        forbidden = [row[:] for row in valid]
        forbidden[0][0] = 5
        mutations.append(forbidden)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[0] * 7 for _ in range(13)])
        mutations.append([[0] * 6 for _ in range(14)])
        mutations.append([[0] * 7 for _ in range(29)])
        mutations.append([[0] * 17 for _ in range(14)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_counts_boundaries_profiles_and_diversity(self):
        mean_areas = {}
        mean_dot_counts = {}
        all_dot_counts = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            dot_counts = []
            pairs = set()
            outputs = set()
            profiles = Counter()
            sides = Counter()
            dot_bands = Counter()
            lengths = set()
            starts_at_top = ends_at_bottom = 0
            first_offsets = last_offsets = 0
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
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                count = len(features["dots"])
                dot_counts.append(count)
                all_dot_counts.add(count)
                sides[features["dot_side"]] += 1
                dot_bands[features["dot_band"]] += 1
                lengths.add(features["length"])
                starts_at_top += (
                    min(features["left_start"], features["right_start"]) == 0
                )
                ends_at_bottom += (
                    max(features["left_start"], features["right_start"])
                    + features["length"]
                    == len(grid)
                )
                first_offsets += any(
                    offset == 0 for offset, _col in features["dots"]
                )
                last_offsets += any(
                    offset == features["length"] - 1
                    for offset, _col in features["dots"]
                )
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profiles[signature] += 1

            mean_areas[band] = sum(areas) / len(areas)
            mean_dot_counts[band] = sum(dot_counts) / len(dot_counts)
            self.assertGreaterEqual(len(pairs), 545)
            self.assertGreaterEqual(len(outputs), 545)
            self.assertEqual(set(sides), {"left", "right"})
            self.assertEqual(set(dot_bands), {"upper", "lower"})
            self.assertEqual(
                set(profiles),
                generator._CANONICAL_PROFILE_SIGNATURES,
            )
            self.assertGreaterEqual(len(lengths), 3)
            self.assertGreater(starts_at_top, 50)
            self.assertGreater(ends_at_bottom, 50)
            self.assertGreater(first_offsets, 100)
            self.assertGreater(last_offsets, 100)

        self.assertEqual(all_dot_counts, {1, 2, 3, 4, 5})
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])
        self.assertLess(
            mean_dot_counts["easy"],
            mean_dot_counts["medium"],
        )
        self.assertLess(
            mean_dot_counts["medium"],
            mean_dot_counts["hard"],
        )

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
