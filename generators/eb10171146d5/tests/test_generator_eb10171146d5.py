from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.eb10171146d5 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split) or []:
                    yield pair["input"], pair["output"]


class Eb10171146d5GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        output_shapes = set()
        output_components = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
            output_cells = {
                (r, c)
                for r, row in enumerate(expected)
                for c, value in enumerate(row)
                if value == 8
            }
            output_shapes.add((len(expected), len(expected[0])))
            output_components.add(generator._component_count(output_cells))
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )
        self.assertEqual(
            output_shapes,
            {(2, 1), (2, 2), (2, 3), (3, 3)},
        )
        self.assertEqual(output_components, {1, 2})

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
                    output = generator.rule_mirror(grid)
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
                self.assertGreaterEqual(matches, 25)
                self.assertLessEqual(matches, 80)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 575)

    def test_forced_dimension_boundaries_are_exact(self):
        for height, width in (
            (7, 9),
            (7, 20),
            (20, 9),
            (20, 20),
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

    def test_rule_is_exact_normalized_xor_and_tight_crop(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(150):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                blue, red, _ba, _ra = generator._scene_shapes(grid)
                xor = generator._xor_features(blue, red)
                output = generator.rule_mirror(grid)
                cells = {
                    (r, c)
                    for r, row in enumerate(output)
                    for c, value in enumerate(row)
                    if value == 8
                }
                self.assertEqual(cells, set(xor["normalized"]))
                self.assertEqual(
                    (len(output), len(output[0])),
                    xor["shape"],
                )
                self.assertTrue(all(
                    value in (0, 8) for row in output for value in row
                ))
                self.assertTrue(any(r == 0 for r, _c in cells))
                self.assertTrue(any(c == 0 for _r, c in cells))

    def test_lawful_cross_profile_recombination_is_not_canonical(self):
        blue = generator._PROFILE_SPECS[0]["blue"]
        red = generator._PROFILE_SPECS[1]["red"]
        grid = generator._place_shapes(
            11,
            14,
            blue,
            red,
            random.Random(17),
        )
        self.assertIsNotNone(grid)
        self.assertEqual(generator.self_check(grid), [])
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertIsNone(generator.canonical_profile_signature(grid))
        self.assertGreaterEqual(
            sum(value == 8 for row in generator.rule_mirror(grid) for value in row),
            2,
        )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 7},
            {"grid_h": 20},
            {"grid_w": 9},
            {"grid_w": 20},
            {"grid_h": 7, "grid_w": 9},
            {"grid_h": 7, "grid_w": 20},
            {"grid_h": 20, "grid_w": 9},
            {"grid_h": 20, "grid_w": 20},
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
            {"grid_h": "7"},
            {"grid_w": 9.0},
            {"grid_h": True},
            {"grid_h": 6},
            {"grid_h": 21},
            {"grid_w": 8},
            {"grid_w": 21},
            {"texture": "identical_shapes"},
            {"palette_kind": "warm"},
            {"anchor_corner": True},
            {"asymmetry_force": True},
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
        self.assertGreater(profiled, 30)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=20,
                grid_w=9,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"grid_h": 20, "grid_w": 9},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            grid_h=12,
            grid_w=14,
        )
        mutations = []

        missing_red = [
            [0 if value == 2 else value for value in row]
            for row in valid
        ]
        mutations.append(missing_red)

        split_blue = [row[:] for row in valid]
        for r, row in enumerate(split_blue):
            for c, value in enumerate(row):
                if value == 0:
                    split_blue[r][c] = 1
                    if len(generator._components(split_blue, 1)) > 1:
                        break
                    split_blue[r][c] = 0
            else:
                continue
            break
        mutations.append(split_blue)

        touching = [[0] * 12 for _ in range(10)]
        touching[2][2] = touching[2][3] = 1
        touching[3][2] = touching[3][3] = 2
        mutations.append(touching)

        identical = [[0] * 12 for _ in range(10)]
        identical[1][1] = identical[1][2] = 1
        identical[6][7] = identical[6][8] = 2
        mutations.append(identical)

        forbidden = [row[:] for row in valid]
        forbidden[0][0] = 5
        mutations.append(forbidden)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[0] * 9 for _ in range(6)])
        mutations.append([[0] * 8 for _ in range(7)])
        mutations.append([[0] * 9 for _ in range(21)])
        mutations.append([[0] * 21 for _ in range(7)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_order_and_cover_xor_topology_crop_and_shape_sizes(self):
        means = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            pairs = set()
            outputs = set()
            components = Counter()
            crop_rows = crop_cols = 0
            blue_sizes = set()
            red_sizes = set()
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
                blue, red, _ba, _ra = generator._scene_shapes(grid)
                xor = generator._xor_features(blue, red)
                components[xor["components"]] += 1
                crop_rows += xor["crop_offset"][0] > 0
                crop_cols += xor["crop_offset"][1] > 0
                blue_sizes.add(len(blue))
                red_sizes.add(len(red))
            means[band] = sum(areas) / len(areas)
            self.assertGreaterEqual(len(pairs), 575)
            self.assertGreaterEqual(len(outputs), 540)
            self.assertGreater(components[1], 30)
            self.assertGreater(components[2], 20)
            self.assertGreater(crop_rows, 10)
            self.assertGreater(crop_cols, 10)
            self.assertGreaterEqual(len(blue_sizes), 4)
            self.assertGreaterEqual(len(red_sizes), 4)
        self.assertLess(means["easy"], means["medium"])
        self.assertLess(means["medium"], means["hard"])

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
