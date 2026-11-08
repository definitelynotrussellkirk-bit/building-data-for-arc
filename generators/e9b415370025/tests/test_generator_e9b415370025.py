"""Focused semantic and contract tests for generator e9b415370025."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.e9b415370025 import generator
from puzzle_generators.runner import _load_rule
from scripts.rule_smoke import load_rules


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_ID = "878187ab"


def canonical_pairs():
    challenges = json.loads(
        (ROOT / "data/raw/arc-agi_training_challenges.json").read_text()
    )[ORIGINAL_ID]
    solutions = json.loads(
        (ROOT / "data/raw/arc-agi_training_solutions.json").read_text()
    )[ORIGINAL_ID]
    pairs = [
        {
            "input": pair["input"],
            "output": pair["output"],
        }
        for pair in challenges["train"]
    ]
    pairs.extend(
        {
            "input": pair["input"],
            "output": solutions[index],
        }
        for index, pair in enumerate(challenges["test"])
    )
    return pairs


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def reference_rule(grid):
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    background = counts.most_common(1)[0][0]
    foreground_counts = [
        count
        for color, count in counts.items()
        if color != background
    ]
    if not foreground_counts:
        raise ValueError("missing foreground")
    height_count = min(foreground_counts)
    width_count = max(foreground_counts)
    output = [
        [background for _col in range(16)]
        for _row in range(16)
    ]
    top = 16 - height_count
    for index in range(height_count):
        row = top + index
        for col in range(width_count):
            output[row][col] = 2
        offset = width_count - height_count + index
        left = min(offset, width_count - 1 - offset)
        right = width_count - 1 - left
        output[row][left] = 4
        output[row][right] = 4
    return output


def broad_case(background):
    grid = [
        [background for _col in range(11)]
        for _row in range(9)
    ]
    layers = (
        (0 if background != 0 else 1, ((0, 0), (8, 10))),
        (3 if background != 3 else 5, ((1, 7), (4, 4), (7, 2))),
        (
            8 if background != 8 else 9,
            ((0, 9), (2, 1), (3, 8), (6, 5), (8, 0)),
        ),
    )
    for color, cells in layers:
        for row, col in cells:
            grid[row][col] = color
    return grid


class GeneratorE9b415370025Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 3)
        for index, pair in enumerate(self.pairs):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.canonical_profile_index(source),
                index,
            )
            self.assertEqual(
                generator.exact_public_profile_index(source),
                index,
            )
            self.assertEqual(
                generator.observe_overrides(source),
                {"scene_profile": generator.SCENE_PROFILES[index]},
            )
            self.assertEqual(reference_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_exact_axis_value_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for index, profile in enumerate(generator.SCENE_PROFILES):
                grid = generator.generate(
                    10_000 + index,
                    20_000 + index,
                    difficulty=band,
                    scene_profile=profile,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"scene_profile": profile},
                )
                self.assertEqual(
                    generator.canonical_profile_index(grid),
                    (
                        index
                        if profile in generator.PUBLIC_SCENE_PROFILES
                        else None
                    ),
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    reference_rule(grid),
                )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_census_is_complete_and_diverse(self):
        expected = set(generator.SCENE_PROFILES)
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                inputs = set()
                outputs = set()
                exact_public = 0
                for offset in range(600):
                    seed = start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    observed = generator.observe_overrides(grid)
                    profiles[observed["scene_profile"]] += 1
                    output = reference_rule(grid)
                    self.assertEqual(generator.rule_mirror(grid), output)
                    exact_public += (
                        generator.exact_public_profile_index(grid)
                        is not None
                    )
                    inputs.add(
                        json.dumps(grid, separators=(",", ":"))
                    )
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(set(profiles), expected)
                self.assertGreaterEqual(len(inputs), 540)
                self.assertGreaterEqual(len(outputs), 15)
                self.assertGreaterEqual(exact_public, 12)
                self.assertLessEqual(exact_public, 55)

    def test_public_prior_difficulty_and_palette_coverage(self):
        profile_counts = {}
        foreground_palette = set()
        background_palette = set()
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            exact_public = 0
            for offset in range(2_000):
                seed = 30_000 + 3_000 * band_index + offset
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                analysis = generator._analyze_scene(grid)
                profiles[observed["scene_profile"]] += 1
                exact_public += (
                    generator.exact_public_profile_index(grid) is not None
                )
                background_palette.add(analysis["background"])
                foreground_palette.update(
                    (analysis["min_color"], analysis["max_color"])
                )
            self.assertEqual(
                set(profiles),
                set(generator.SCENE_PROFILES),
            )
            self.assertGreaterEqual(exact_public, 60)
            self.assertLessEqual(exact_public, 140)
            profile_counts[band] = profiles
        self.assertGreater(
            profile_counts["easy"]["h5_w7_15"],
            profile_counts["easy"]["h12_w14_16"],
        )
        self.assertGreater(
            profile_counts["hard"]["h12_w14_16"],
            profile_counts["hard"]["h5_w7_15"],
        )
        self.assertEqual(background_palette, set(range(10)))
        self.assertEqual(foreground_palette, set(range(10)))

    def test_negative_recombinations_are_rejected(self):
        grid = generator.generate(
            811,
            917,
            scene_profile="h5_w7_15",
        )
        self.assertEqual(generator.self_check(grid), [])
        analysis = generator._analyze_scene(grid)
        self.assertIsNotNone(analysis)
        min_color = analysis["min_color"]
        max_color = analysis["max_color"]

        wrong_background = [
            [6 if value == 7 else value for value in row]
            for row in grid
        ]
        self.assertEqual(generator.self_check(wrong_background), [])
        self.assertEqual(
            generator.observe_overrides(wrong_background),
            {"scene_profile": "generalized"},
        )
        self.assertIsNone(
            generator.canonical_profile_index(wrong_background)
        )

        third_color = [row[:] for row in grid]
        row, col = next(
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == 7
        )
        third_color[row][col] = next(
            color
            for color in range(10)
            if color not in (7, min_color, max_color)
        )
        self.assertTrue(generator.self_check(third_color))

        wrong_link = [row[:] for row in grid]
        background_cells = [
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == 7
        ]
        for row, col in background_cells[:3]:
            wrong_link[row][col] = max_color
        self.assertEqual(generator.self_check(wrong_link), [])
        self.assertEqual(
            generator.observe_overrides(wrong_link),
            {"scene_profile": "generalized"},
        )
        self.assertIsNone(
            generator.canonical_profile_index(wrong_link)
        )

        equal_counts = [row[:] for row in grid]
        row, col = next(
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == max_color
        )
        equal_counts[row][col] = min_color
        self.assertTrue(generator.self_check(equal_counts))

        self.assertTrue(generator.self_check(grid[:-1]))
        self.assertTrue(generator.self_check([[7] * 15 for _ in range(15)]))
        self.assertTrue(generator.self_check([]))
        self.assertTrue(generator.self_check([[7, 7], [7]]))
        other = next(
            profile
            for profile in generator.SCENE_PROFILES
            if profile != analysis["scene_profile"]
        )
        self.assertTrue(
            generator.self_check(
                grid,
                meta={"overrides": {"scene_profile": other}},
            )
        )

    def test_broad_rule_mirror_and_metamorphic_count_invariance(self):
        for background in (2, 4, 7):
            grid = broad_case(background)
            snapshot = [row[:] for row in grid]
            self.assertEqual(
                generator.rule_mirror(grid),
                reference_rule(grid),
            )
            self.assertEqual(grid, snapshot)

        grid = generator.generate(
            12_345,
            67_890,
            scene_profile="h12_w14_16",
        )
        output = generator.rule_mirror(grid)
        rotated = [
            list(reversed(row))
            for row in reversed(grid)
        ]
        self.assertEqual(generator.self_check(rotated), [])
        self.assertEqual(generator.rule_mirror(rotated), output)

        colors = [
            color
            for color in Counter(
                value for row in grid for value in row
            )
            if color != 7
        ]
        replacements = [
            color
            for color in range(10)
            if color not in {7, *colors}
        ][:2]
        recolored = [
            [
                replacements[colors.index(value)]
                if value in colors
                else value
                for value in row
            ]
            for row in grid
        ]
        self.assertEqual(generator.self_check(recolored), [])
        self.assertEqual(generator.rule_mirror(recolored), output)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(20260718)
        expected = [random.random() for _index in range(12)]
        random.seed(20260718)
        for index in range(120):
            generator.generate(
                90_000 + index,
                17 * index + 3,
                difficulty=("easy", "medium", "hard")[index % 3],
            )
        actual = [random.random() for _index in range(12)]
        self.assertEqual(actual, expected)

        first = generator.generate(77, 88, difficulty="medium")
        second = generator.generate(77, 88, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        snapshot = [row[:] for row in second]
        first[0][0] = (first[0][0] + 1) % 10
        third = generator.generate(77, 88, difficulty="medium")
        self.assertEqual(second, snapshot)
        self.assertEqual(third, snapshot)

    def test_rule_hash_and_base_source_sync(self):
        canonical = load_rules([generator.TASK_ID])[generator.TASK_ID]
        base, _path = _load_rule(generator.TASK_ID)
        self.assertEqual(
            normalized_rule_hash(canonical)[:12],
            generator.RULE_HASH,
        )
        self.assertEqual(
            normalized_rule_hash(base),
            normalized_rule_hash(canonical),
        )


if __name__ == "__main__":
    unittest.main()
