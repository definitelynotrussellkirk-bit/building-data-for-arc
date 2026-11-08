from __future__ import annotations

from collections import Counter
import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path
import random
import unittest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "19c55a8731b1"
generator = import_module(
    "puzzle_generators.per_puzzle.19c55a8731b1.generator"
)


def canonical_row():
    rows = [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row, found {len(rows)}")
    return rows[0]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


class Generator19c55a8731b1Tests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        row = canonical_row()
        pairs = [
            (split, index, pair)
            for split in ("train", "test")
            for index, pair in enumerate(row[split])
        ]
        self.assertEqual(len(pairs), 3)
        observed = []
        for _split, _index, pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)
            analysis = generator._inspect_scene(source)
            self.assertIsNotNone(analysis)
            observed.append(analysis["scene_profile"])
        self.assertEqual(set(observed), set(generator._PUBLIC_SPECS))

    def test_every_profile_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(16):
                    grid = generator.generate(
                        seed,
                        seed * 37 + 11,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._inspect_scene(grid)
                    self.assertIsNotNone(analysis)
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        generator.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": {"scene_profile": profile}},
                        ),
                        [],
                    )

    def test_exact_profiles_preserve_linked_key_and_tile_morphology(self):
        for profile in generator._PUBLIC_SPECS:
            expected = set(generator._PROFILE_VARIANTS[profile])
            witnessed = set()
            for seed in range(120):
                grid = generator.generate(
                    9_000 + seed,
                    seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                analysis = generator._inspect_scene(grid)
                signature = (
                    generator._normalize_labels(analysis["key"]),
                    analysis["tile_mask"],
                )
                self.assertIn(signature, expected)
                witnessed.add(signature)
            self.assertGreaterEqual(len(witnessed), min(2, len(expected)))

    def test_distribution_has_every_profile_and_canonical_extremes(self):
        expected_general_dims = {
            "easy": {(3, 3), (3, 4), (4, 3)},
            "medium": {
                (3, 3),
                (3, 4),
                (3, 5),
                (4, 3),
                (4, 4),
                (4, 5),
                (5, 3),
                (5, 4),
            },
            "hard": {(3, 5), (4, 4), (4, 5), (5, 3), (5, 4)},
        }
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            dimensions = set()
            distinct = set()
            tile_sizes = set()
            for index in range(1_000):
                grid = generator.generate(
                    12_000 + band_index,
                    index,
                    difficulty=band,
                )
                analysis = generator._inspect_scene(grid)
                self.assertIsNotNone(analysis)
                profiles[analysis["scene_profile"]] += 1
                if analysis["scene_profile"] == "generalized":
                    dimensions.add(analysis["key_dims"])
                    tile_sizes.add(analysis["tile_cell_count"])
                distinct.add(frozen(grid))
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertGreaterEqual(min(profiles.values()), 70)
            self.assertEqual(dimensions, expected_general_dims[band])
            self.assertGreaterEqual(len(tile_sizes), 2)
            self.assertGreaterEqual(len(distinct), 995)

    def test_generalized_profile_excludes_public_joint_signatures(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    20_000 + seed,
                    difficulty=band,
                    scene_profile="generalized",
                )
                analysis = generator._inspect_scene(grid)
                signature = (
                    generator._normalize_labels(analysis["key"]),
                    analysis["tile_mask"],
                )
                self.assertNotIn(signature, generator._EXACT_SIGNATURES)
                self.assertEqual(analysis["scene_profile"], "generalized")

    def test_self_check_rejects_nearest_destructive_mutations(self):
        grid = generator.generate(
            77,
            91,
            difficulty="medium",
            scene_profile="key4x4_hourglass",
        )
        analysis = generator._inspect_scene(grid)
        key_top, _key_bottom, key_left, _key_right = analysis["key_bbox"]
        gray_row, gray_col = next(
            (row, col)
            for row in range(23)
            for col in range(23)
            if grid[row][col] == 5
        )

        mutations = []

        wrong_canvas = copy.deepcopy(grid)
        wrong_canvas.append([0] * 23)
        mutations.append(wrong_canvas)

        hole_in_key = copy.deepcopy(grid)
        hole_in_key[key_top][key_left] = 0
        mutations.append(hole_in_key)

        one_key_color = copy.deepcopy(grid)
        for row in range(23):
            for col in range(23):
                if one_key_color[row][col] not in (0, 5):
                    one_key_color[row][col] = 1
        mutations.append(one_key_color)

        broken_tile = copy.deepcopy(grid)
        broken_tile[gray_row][gray_col] = 0
        mutations.append(broken_tile)

        stray_gray = copy.deepcopy(grid)
        stray_gray[22][22] = 5
        mutations.append(stray_gray)

        stray_key = copy.deepcopy(grid)
        stray_key[22][22] = 2
        mutations.append(stray_key)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_rule_mirror_is_broad_and_input_pure(self):
        grid = [[0 for _ in range(10)] for _ in range(10)]
        grid[0][0:2] = [1, 2]
        grid[1][0:2] = [3, 4]
        for top in (3, 6):
            for left in (3, 6):
                for row in range(top, top + 2):
                    for col in range(left, left + 2):
                        grid[row][col] = 5
        before = copy.deepcopy(grid)
        output = generator.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[3][3], 1)
        self.assertEqual(output[3][6], 2)
        self.assertEqual(output[6][3], 3)
        self.assertEqual(output[6][6], 4)
        self.assertTrue(all(value != 5 for row in output for value in row))
        with self.assertRaises(ValueError):
            generator.rule_mirror([[0, 1], [1, 0]])

    def test_output_changes_exactly_gray_cells_to_key_index(self):
        for profile in generator.SCENE_PROFILES:
            for seed in range(40):
                grid = generator.generate(
                    seed,
                    30_000 + seed,
                    difficulty="hard",
                    scene_profile=profile,
                )
                analysis = generator._inspect_scene(grid)
                output = generator.rule_mirror(grid)
                changed = {
                    (row, col)
                    for row in range(23)
                    for col in range(23)
                    if grid[row][col] != output[row][col]
                }
                gray = {
                    (row, col)
                    for row in range(23)
                    for col in range(23)
                    if grid[row][col] == 5
                }
                self.assertEqual(changed, gray)
                for row, col in gray:
                    tile_row = max(
                        index
                        for index, start in enumerate(
                            analysis["tile_row_starts"]
                        )
                        if start <= row
                    )
                    tile_col = max(
                        index
                        for index, start in enumerate(
                            analysis["tile_col_starts"]
                        )
                        if start <= col
                    )
                    self.assertEqual(
                        output[row][col],
                        analysis["key"][tile_row][tile_col],
                    )

    def test_invalid_calls_determinism_freshness_and_global_rng(self):
        with self.assertRaises(ValueError):
            generator.generate(0, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(0, 0, unknown_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(0, 0, scene_profile="unknown")

        random.seed(123456)
        state = random.getstate()
        first = generator.generate(51, 81, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(51, 81, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_all_rule_authorities_are_byte_identical(self):
        from solvers.grounded_rules import GROUNDED_RULES

        canonical = canonical_row()["program_solution"]
        self.assertEqual(GROUNDED_RULES[TASK_ID], canonical)
        record = json.loads(
            (
                ROOT
                / "data/base/solutions/training/33b52de3__19c55a8731b1.json"
            ).read_text()
        )
        self.assertEqual(record["racket_target"]["raw_code"], canonical)
        self.assertEqual(record["racket_target"]["target_code"], canonical)
        self.assertEqual(
            generator.RULE_HASH,
            hashlib.sha256(canonical.encode()).hexdigest()[:12],
        )


if __name__ == "__main__":
    unittest.main()
