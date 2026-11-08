from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.d68754fb0d84 import generator


ROOT = Path(__file__).resolve().parents[1]


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split)
                pairs = value if isinstance(value, list) else [value]
                for pair in pairs:
                    if pair:
                        yield (
                            as_grid(pair["input"]),
                            as_grid(pair["output"]),
                        )


class D68754fb0d84GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_have_complete_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        codes = set()
        shapes = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            profiles.add(generator.canonical_profile_signature(grid))
            scene = generator._analyze_scene(grid)
            codes.update(code for _, _, code in scene["anchors"])
            shapes.add(scene["shape"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(codes, set(range(1, 9)))
        self.assertEqual(len(shapes), 5)

    def test_complete_profile_prior_is_substantive_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                grids = set()
                for offset in range(500):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    grids.add(tuple(map(tuple, grid)))
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 30)
                self.assertLessEqual(matches, 85)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(grids), 450)

    def test_general_path_witnesses_all_codes_sizes_and_shapes(self):
        codes = set()
        template_sizes = set()
        shapes = set()
        anchor_counts = set()
        asymmetric = 0
        for cells in range(4, 8):
            for count in range(1, 5):
                for seed in range(45):
                    grid = generator.generate(
                        seed,
                        seed * 31 + cells * 7 + count,
                        difficulty="hard",
                        grid_h=20,
                        grid_w=22,
                        n_anchors=count,
                        template_cells=cells,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    scene = generator._analyze_scene(grid)
                    codes.update(code for _, _, code in scene["anchors"])
                    template_sizes.add(len(scene["shape"]))
                    shapes.add(scene["shape"])
                    anchor_counts.add(len(scene["anchors"]))
                    asymmetric += (
                        len({
                            generator._transform(scene["shape"], code)
                            for code in range(1, 9)
                        }) == 8
                    )
        self.assertEqual(codes, set(range(1, 9)))
        self.assertEqual(template_sizes, {4, 5, 6, 7})
        self.assertEqual(anchor_counts, {1, 2, 3, 4})
        self.assertGreater(len(shapes), 100)
        self.assertGreater(asymmetric, 600)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 11},
            {"grid_h": 20},
            {"grid_w": 13},
            {"grid_w": 22},
            {"n_anchors": 1},
            {"n_anchors": 4},
            {"template_cells": 4},
            {"template_cells": 7},
            {
                "grid_h": 11,
                "grid_w": 13,
                "n_anchors": 4,
                "template_cells": 7,
            },
            {
                "grid_h": 20,
                "grid_w": 22,
                "n_anchors": 1,
                "template_cells": 4,
            },
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                if "grid_h" in kwargs:
                    self.assertEqual(len(grid), kwargs["grid_h"])
                if "grid_w" in kwargs:
                    self.assertEqual(len(grid[0]), kwargs["grid_w"])
                for key in ("n_anchors", "template_cells"):
                    if key in kwargs:
                        self.assertEqual(observed[key], kwargs[key])

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "11"},
            {"grid_w": 13.0},
            {"n_anchors": True},
            {"template_cells": "4"},
            {"grid_h": 10},
            {"grid_w": 23},
            {"n_anchors": 0},
            {"n_anchors": 5},
            {"template_cells": 3},
            {"template_cells": 8},
            {"texture": "no_template"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                self.assertEqual(ctx._drawn["grid_h"], len(grid))
                self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
                self.assertEqual(
                    ctx._drawn["n_anchors"],
                    observed["n_anchors"],
                )
                self.assertEqual(
                    ctx._drawn["template_cells"],
                    observed["template_cells"],
                )
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 50)

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        scene = generator._analyze_scene(original)
        template = sorted(scene["template_cells"])

        short_template = [row[:] for row in original]
        r, c = template[-1]
        short_template[r][c] = 0
        self.assertTrue(
            any(
                "template" in error
                for error in generator.self_check(short_template)
            )
        )

        disconnected = [row[:] for row in original]
        r, c = template[-1]
        disconnected[r][c] = 0
        disconnected[5][1] = 2
        self.assertTrue(
            any(
                "connected" in error
                for error in generator.self_check(disconnected)
            )
        )

        missing_anchor = [row[:] for row in original]
        ar, ac, _ = scene["anchors"][0]
        missing_anchor[ar][ac] = 0
        self.assertTrue(generator.self_check(missing_anchor))

        missing_code = [row[:] for row in original]
        ar, ac, _ = scene["anchors"][0]
        missing_code[ar][ac - 1] = 0
        self.assertTrue(
            any(
                "lacks a code" in error
                for error in generator.self_check(missing_code)
            )
        )

        repeated_code = [row[:] for row in original]
        first, second = scene["anchors"][:2]
        repeated_code[second[0]][second[1] - 1] = first[2]
        self.assertTrue(
            any(
                "not distinct" in error
                for error in generator.self_check(repeated_code)
            )
        )

        outside = [row[:] for row in original]
        outside[10][13] = 4
        self.assertTrue(
            any(
                "outside the grammar" in error
                for error in generator.self_check(outside)
            )
        )

        early_code_two = [row[:] for row in original]
        ar, ac, _ = scene["anchors"][0]
        early_code_two[ar][ac - 1] = 0
        early_code_two[0][0] = 2
        early_code_two[0][1] = 9
        self.assertTrue(
            any(
                "precedes the template" in error
                for error in generator.self_check(early_code_two)
            )
        )

        out_of_bounds = [row[:] for row in original]
        ar, ac, code = scene["anchors"][0]
        out_of_bounds[ar][ac - 1] = 0
        out_of_bounds[ar][ac] = 0
        out_of_bounds[10][12] = code
        out_of_bounds[10][13] = 9
        self.assertTrue(
            any(
                "out-of-bounds" in error
                for error in generator.self_check(out_of_bounds)
            )
        )

    def test_lawful_code_recombination_is_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        first, second = generator._analyze_scene(hybrid)["anchors"][:2]
        hybrid[first[0]][first[1] - 1] = second[2]
        hybrid[second[0]][second[1] - 1] = first[2]
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNotNone(generator.rule_mirror(hybrid))
        self.assertFalse(generator.is_canonical_profile(hybrid))

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 99
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
