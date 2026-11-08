from __future__ import annotations

from collections import Counter
import copy
import hashlib
from importlib import import_module
import json
import random
import unittest

from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
)

RUNTIME_ROOT = find_root(__file__)
TASK_ID = "27f5eba1051c"
generator = import_module(
    "puzzle_generators.per_puzzle.27f5eba1051c.generator"
)


def normalized_grid(grid):
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def canonical_rows():
    rows = []
    for raw in canonical_path(RUNTIME_ROOT).read_text().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    return rows


def canonical_pairs():
    return [
        (pair["split"], pair["input"], pair["output"])
        for pair in read_canonical_pairs(TASK_ID, root=RUNTIME_ROOT)
    ]


class Generator27f5eba1051cTests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 5)
        profiles = []
        for split, source, target in pairs:
            before = copy.deepcopy(source)
            analysis = generator._inspect_scene(source)
            self.assertIsNotNone(analysis, split)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), target)
            self.assertEqual(source, before)
            self.assertIsNotNone(generator.canonical_profile_index(source))
            profiles.append(analysis["scene_profile"])
        self.assertEqual(set(profiles), set(generator._PUBLIC_SPECS))

    def test_rule_hash_matches_canonical_program(self):
        programs = {row["program_solution"] for row in canonical_rows()}
        self.assertEqual(len(programs), 1)
        program = programs.pop()
        normalized = " ".join(program.split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        self.assertEqual(generator.RULE_HASH, digest[:12])

    def test_every_profile_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(24):
                    grid = generator.generate(
                        seed,
                        seed * 41 + 7,
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

    def test_exact_profiles_preserve_complete_linked_signatures(self):
        for profile, spec in generator._PUBLIC_SPECS.items():
            expected = generator._spec_signature(spec)
            placements = set()
            palettes = set()
            for seed in range(160):
                grid = generator.generate(
                    4_000 + seed,
                    seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                analysis = generator._inspect_scene(grid)
                self.assertEqual(analysis["signature"], expected)
                self.assertEqual(analysis["scene_profile"], profile)
                placements.add(
                    tuple(
                        sorted(obj["bbox"] for obj in analysis["objects"])
                    )
                )
                palettes.add(analysis["colors"])
            self.assertGreaterEqual(len(placements), 2)
            self.assertGreaterEqual(len(palettes), 20)

    def test_default_distribution_covers_profiles_and_semantic_extremes(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            ranks = set()
            shapes = set()
            aliases = 0
            size_ties = 0
            column_ties = 0
            color_ties = 0
            distinct = set()
            for index in range(1_000):
                grid = generator.generate(
                    30_000 + band_index,
                    index,
                    difficulty=band,
                )
                analysis = generator._inspect_scene(grid)
                self.assertIsNotNone(analysis)
                profiles[analysis["scene_profile"]] += 1
                ranks.add(analysis["rank"])
                shapes.add(analysis["shape"])
                aliases += bool(analysis["rank_alias_indexes"])
                size_ties += analysis["size_tie"]
                column_ties += analysis["column_tie"]
                color_ties += analysis["color_tie"]
                distinct.add(frozen(grid))
            self.assertEqual(
                set(profiles),
                set(generator.SCENE_PROFILES) - {"generalized"},
            )
            self.assertGreaterEqual(min(profiles.values()), 25)
            self.assertEqual(ranks, {1, 2, 3})
            self.assertTrue({(9, 14), (9, 15), (10, 15), (10, 16)} <= shapes)
            self.assertGreater(aliases, 50)
            self.assertGreater(size_ties, 75)
            self.assertGreater(column_ties, 50)
            self.assertGreater(color_ties, 25)
            self.assertGreaterEqual(len(distinct), 990)

    def test_column_precedes_color_for_equal_area_objects(self):
        grid = [[0 for _ in range(14)] for _ in range(10)]
        grid[0][0] = 2
        for row, col in (
            (3, 5),
            (3, 6),
            (3, 7),
            (4, 5),
            (4, 6),
            (4, 7),
        ):
            grid[row][col] = 6
        for row, col in ((2, 1), (2, 2), (3, 1), (3, 2)):
            grid[row][col] = 9
        for row, col in ((6, 10), (6, 11), (7, 10), (7, 11)):
            grid[row][col] = 3
        analysis = generator._inspect_scene(grid)
        self.assertEqual(analysis["scene_profile"], "column_tie")
        self.assertEqual(generator.rule_mirror(grid), [[9, 9], [9, 9]])

    def test_color_breaks_equal_area_equal_column_tie(self):
        grid = [[0 for _ in range(16)] for _ in range(12)]
        grid[0][0] = 2
        for row, col in (
            (4, 10),
            (4, 11),
            (4, 12),
            (5, 10),
            (5, 11),
            (5, 12),
        ):
            grid[row][col] = 6
        for row, col in ((2, 2), (2, 3), (3, 2), (3, 3)):
            grid[row][col] = 8
        for row, col in ((8, 2), (8, 3), (9, 2), (9, 3)):
            grid[row][col] = 3
        analysis = generator._inspect_scene(grid)
        self.assertEqual(analysis["scene_profile"], "color_tie")
        self.assertEqual(generator.rule_mirror(grid), [[3, 3], [3, 3]])

    def test_rank_marker_color_alias_is_not_erased_from_objects(self):
        for seed in range(80):
            grid = generator.generate(
                seed,
                seed + 1_000,
                difficulty="hard",
                scene_profile="rank2_plus_square_bar_alias_10x16",
            )
            analysis = generator._inspect_scene(grid)
            self.assertEqual(analysis["rank_alias_indexes"], (3,))
            self.assertEqual(len(analysis["objects"]), 3)
            self.assertEqual(generator.self_check(grid), [])
            self.assertNotEqual(generator.rule_mirror(grid), grid)

    def test_generalized_profile_never_claims_an_exact_or_tie_profile(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(320):
                grid = generator.generate(
                    seed,
                    80_000 + seed,
                    difficulty=band,
                    scene_profile="generalized",
                )
                analysis = generator._inspect_scene(grid)
                self.assertEqual(analysis["scene_profile"], "generalized")
                self.assertNotIn(
                    analysis["signature"],
                    generator._EXACT_SIGNATURES,
                )
                self.assertFalse(analysis["size_tie"])

    def test_rule_mirror_is_exact_crop_and_input_pure(self):
        for profile in generator.SCENE_PROFILES:
            for seed in range(80):
                grid = generator.generate(
                    seed,
                    100_000 + seed,
                    difficulty="hard",
                    scene_profile=profile,
                )
                before = copy.deepcopy(grid)
                analysis = generator._inspect_scene(grid)
                selected = analysis["selected_object"]
                top, bottom, left, right = selected["bbox"]
                clean = copy.deepcopy(grid)
                clean[0][0] = 0
                expected = [
                    row[left : right + 1]
                    for row in clean[top : bottom + 1]
                ]
                self.assertEqual(generator.rule_mirror(grid), expected)
                self.assertEqual(grid, before)

    def test_strict_checker_rejects_nearest_destructive_mutations(self):
        grid = generator.generate(
            77,
            91,
            difficulty="medium",
            scene_profile="rank1_l_square_bar_9x14",
        )
        analysis = generator._inspect_scene(grid)
        mutations = []

        wrong_rank = copy.deepcopy(grid)
        wrong_rank[0][0] = 0
        mutations.append(wrong_rank)

        missing_object = copy.deepcopy(grid)
        for row, col in analysis["objects"][0]["cells"]:
            missing_object[row][col] = 0
        mutations.append(missing_object)

        fourth_object = copy.deepcopy(grid)
        fourth_object[-1][0] = 8
        mutations.append(fourth_object)

        split_color = copy.deepcopy(grid)
        first = analysis["objects"][0]
        used_colors = {obj["color"] for obj in analysis["objects"]}
        replacement = next(
            color
            for color in range(1, 10)
            if color not in used_colors and color != analysis["rank"]
        )
        row, col = min(first["cells"])
        split_color[row][col] = replacement
        mutations.append(split_color)

        malformed = copy.deepcopy(grid)
        malformed[0] = malformed[0][:-1]
        mutations.append(malformed)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_generation_is_deterministic_fresh_and_global_rng_isolated(self):
        random.seed(275_105)
        state = random.getstate()
        first = generator.generate(123, 456, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(123, 456, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_invalid_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            generator.generate(0, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(0, 0, unknown_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(0, 0, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.rule_mirror([[0, 2], [3]])
        with self.assertRaises(ValueError):
            generator.rule_mirror([[False]])


if __name__ == "__main__":
    unittest.main()
