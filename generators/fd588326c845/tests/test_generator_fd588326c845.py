from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from puzzle_generators import base
from puzzle_generators.per_puzzle.fd588326c845 import generator
from solvers.grounded_rules import GROUNDED_RULES
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
CANONICAL_PATH = canonical_path(ROOT)
DATA_ROOT = CANONICAL_PATH.parents[1]


def canonical_rows():
    rows = []
    with CANONICAL_PATH.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def canonical_pairs():
    row = next(
        row for row in canonical_rows() if row["source"] == "training"
    )
    test = row["test"]
    return list(row["train"]) + (
        [test] if isinstance(test, dict) else list(test)
    )


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def bbox(cells):
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def independent_features(grid):
    grid = coerce(grid)
    key_cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] not in (0, 8)
    ]
    cyan_cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 8
    ]
    key_r1, key_c1, key_r2, key_c2 = bbox(key_cells)
    cyan_r1, cyan_c1, cyan_r2, cyan_c2 = bbox(cyan_cells)
    key_size = key_r2 - key_r1 + 1
    return {
        "key_size": key_size,
        "scale_h": (cyan_r2 - cyan_r1 + 1) // key_size,
        "scale_w": (cyan_c2 - cyan_c1 + 1) // key_size,
        "palette_size": len({
            grid[row][col] for row, col in key_cells
        }),
        "key_cells": len(key_cells),
        "key_box": (key_r1, key_c1, key_r2, key_c2),
        "cyan_box": (cyan_r1, cyan_c1, cyan_r2, cyan_c2),
    }


def independent_rule(grid):
    grid = coerce(grid)
    features = independent_features(grid)
    key_r1, key_c1, _key_r2, _key_c2 = features["key_box"]
    cyan_r1, cyan_c1, _cyan_r2, _cyan_c2 = features["cyan_box"]
    key_size = features["key_size"]
    scale_h = features["scale_h"]
    scale_w = features["scale_w"]
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 8:
                continue
            tile_row = (row - cyan_r1) // scale_h
            tile_col = (col - cyan_c1) // scale_w
            output[row][col] = grid[
                key_r1 + key_size - 1 - tile_col
            ][
                key_c1 + tile_row
            ]
    return output


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class Fd588326c845GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_are_complete_profiles(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.pairs), 3)
        profiles = set()
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
        self.assertEqual(profiles, {0, 1, 2})

    def test_complete_profile_prior_is_stable_in_every_band(self):
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
                self.assertGreaterEqual(matches, 130)
                self.assertLessEqual(matches, 220)
                self.assertEqual(profiles, {0, 1, 2})
                self.assertGreaterEqual(len(pairs), 595)

    def test_every_exact_axis_cross_is_realized(self):
        for key_size in (3, 4):
            for scale_h in (1, 6):
                for scale_w in (1, 6):
                    for palette_size in (2, 3, 4):
                        expected = {
                            "key_size": key_size,
                            "scale_h": scale_h,
                            "scale_w": scale_w,
                            "palette_size": palette_size,
                        }
                        grid = generator.generate(
                            key_size * 1000
                            + scale_h * 100
                            + scale_w * 10
                            + palette_size,
                            97,
                            difficulty=("easy", "medium", "hard")[
                                (key_size + scale_h + scale_w) % 3
                            ],
                            **expected,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            expected,
                        )
                        self.assertEqual(
                            independent_rule(grid),
                            generator.rule_mirror(grid),
                        )

    def test_default_distribution_teaches_relation_and_extrapolation(self):
        all_key_sizes = set()
        all_scales = set()
        all_palettes = set()
        for band in ("easy", "medium", "hard"):
            profiles = set()
            equal_scales = 0
            rectangular_scales = 0
            for seed in range(500):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                features = independent_features(grid)
                all_key_sizes.add(features["key_size"])
                all_scales.update((
                    features["scale_h"],
                    features["scale_w"],
                ))
                all_palettes.add(features["palette_size"])
                if features["scale_h"] == features["scale_w"]:
                    equal_scales += 1
                else:
                    rectangular_scales += 1
                profile = generator.canonical_profile_index(grid)
                if profile is not None:
                    profiles.add(profile)
            self.assertEqual(profiles, {0, 1, 2})
            self.assertGreater(equal_scales, rectangular_scales)
            self.assertGreater(rectangular_scales, 20)
        self.assertEqual(all_key_sizes, {3, 4})
        self.assertEqual(all_scales, {1, 2, 3, 4, 5, 6})
        self.assertEqual(all_palettes, {2, 3, 4})

    def test_profile_rotations_and_negative_recombination(self):
        for index, variants in enumerate(generator._PROFILE_VARIANTS):
            self.assertEqual(len(variants), 4)
            for variant_index, roles in enumerate(variants):
                rng = random.Random(index * 10 + variant_index)
                key = generator._color_roles(roles, rng)
                scale = generator._PROFILE_SCALES[index]
                grid = generator._render_scene(key, scale, scale, rng)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.canonical_profile_index(grid),
                    index,
                )

        # Profile zero's key morphology recombined with profile one's scale
        # is lawful but must not be mislabeled as a complete public profile.
        rng = random.Random(991)
        key = generator._color_roles(generator._PROFILE_KEYS[0], rng)
        recombined = generator._render_scene(key, 2, 2, rng)
        self.assertEqual(generator.self_check(recombined), [])
        self.assertIsNone(
            generator.canonical_profile_index(recombined)
        )
        self.assertEqual(
            generator.rule_mirror(recombined),
            independent_rule(recombined),
        )

    def test_mismatched_or_solid_cyan_masks_are_rejected(self):
        grid = generator.generate(
            83,
            97,
            key_size=3,
            scale_h=2,
            scale_w=3,
            palette_size=3,
        )
        features = independent_features(grid)
        cyan_r1, cyan_c1, _cyan_r2, _cyan_c2 = features["cyan_box"]
        broken = [row[:] for row in grid]
        changed = False
        for tile_row in range(features["key_size"]):
            for tile_col in range(features["key_size"]):
                row = cyan_r1 + tile_row * features["scale_h"]
                col = cyan_c1 + tile_col * features["scale_w"]
                if broken[row][col] == 0:
                    broken[row][col] = 8
                    changed = True
                    break
            if changed:
                break
        self.assertTrue(changed)
        self.assertTrue(generator.self_check(broken))

        solid = [row[:] for row in grid]
        _r1, _c1, r2, c2 = features["cyan_box"]
        for row in range(cyan_r1, r2 + 1):
            for col in range(cyan_c1, c2 + 1):
                solid[row][col] = 8
        self.assertTrue(generator.self_check(solid))

    def test_strict_calls_and_removed_controls(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"key_size": 2},
            {"key_size": 5},
            {"key_size": "3"},
            {"key_size": 3.0},
            {"key_size": True},
            {"scale_h": 0},
            {"scale_h": 7},
            {"scale_w": False},
            {"palette_size": 1},
            {"palette_size": 5},
            {"texture": "no_key"},
            {"palette_kind": "warm"},
            {"key_position": "random"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profile_count = 0
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
                profile_count += generator.is_canonical_profile(grid)
        self.assertGreaterEqual(profile_count, 130)

        expected = {
            "key_size": 4,
            "scale_h": 6,
            "scale_w": 1,
            "palette_size": 2,
        }
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(91, 117, **expected)
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn, expected)
        self.assertEqual(captured[-1]._override_used, expected)
        self.assertEqual(generator.observe_overrides(grid), expected)

    def test_self_check_rejects_minimal_and_structural_impostors(self):
        invalid = (
            [],
            [[0]],
            [[0] * 7 for _row in range(7)],
            [[8] * 7 for _row in range(7)],
            [[0] * 7 for _row in range(6)] + [[0, 0, 0, 1, 0, 0, 0]],
            [[0] * 7 for _row in range(5)]
            + [[0, 0, 1, 1, 0, 0, 0]]
            + [[0] * 7],
            [[0] * 7 for _row in range(4)]
            + [[0, 0, 1, 1, 0, 0, 0]]
            + [[0, 0, 1, 1, 0, 0, 0]]
            + [[0] * 7],
            [[0, 1], [2]],
            [[0, 8, 10], [1, 0, 0], [0, 0, 0]],
        )
        for grid in invalid:
            self.assertTrue(generator.self_check(grid))

        valid = generator.generate(7, 11)
        ragged = [row[:] for row in valid]
        ragged[0].pop()
        self.assertTrue(generator.self_check(ragged))
        transposed = [list(row) for row in zip(*valid)]
        self.assertTrue(generator.self_check(transposed))

    def test_source_sync_determinism_freshness_and_global_rng(self):
        sources = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(sources), 1)
        source = next(iter(sources))
        for path in (
            DATA_ROOT
            / "base/solutions/training"
            / "103eff5b__fd588326c845.json",
            DATA_ROOT
            / "base/solutions/augmented"
            / "103eff5b__1bc9d9c90870.json",
        ):
            target = json.loads(path.read_text())["racket_target"]
            self.assertEqual(
                normalized_rule_hash(target["raw_code"]),
                normalized_rule_hash(source),
            )
            self.assertEqual(
                normalized_rule_hash(target["target_code"]),
                normalized_rule_hash(source),
            )
        self.assertEqual(
            normalized_rule_hash(GROUNDED_RULES[generator.TASK_ID]),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        state = random.getstate()
        first = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        first_snapshot = [row[:] for row in first]
        second = generator.generate(91, 97, difficulty="easy")
        self.assertEqual(first, first_snapshot)
        again = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(
            old_row is not new_row
            for old_row, new_row in zip(first, again)
        ))
        first[0][0] = 9 if first[0][0] != 9 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )
        self.assertNotEqual(second, again)


if __name__ == "__main__":
    unittest.main()
