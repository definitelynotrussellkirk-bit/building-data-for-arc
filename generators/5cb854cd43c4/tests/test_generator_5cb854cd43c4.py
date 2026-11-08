"""Focused semantic and contract tests for generator 5cb854cd43c4."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter, deque
from pathlib import Path

from scripts.rule_smoke import load_rules


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.5cb854cd43c4.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/765a70430bc9/"
    "M6__5cb854cd43c4.json"
)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for raw in handle:
            row = json.loads(raw)
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


def independent_components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (0, -1),
                    (0, 1),
                    (1, 0),
                ):
                    candidate = (
                        row + delta_row,
                        col + delta_col,
                    )
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            result.append((color, tuple(cells)))
    return result


def independent_rule(grid):
    objects = sorted(
        independent_components(grid),
        key=lambda item: (-len(item[1]), item[0]),
    )
    if not objects:
        raise ValueError("no object")
    output = []
    for index, (color, cells) in enumerate(objects):
        if index:
            output.append(0)
        output.extend([color] * len(cells))
    return [output]


class Generator5cb854cd43c4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        expected_profiles = (
            "compact_5x5_three",
            "compact_6x6_two",
            "sparse_8x7_three",
        )
        self.assertEqual(len(self.pairs), 3)
        for pair, profile in zip(self.pairs, expected_profiles):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.observe_overrides(source),
                {
                    "scene_profile": profile,
                    "size_regime": "canonical",
                },
            )
            self.assertEqual(
                generator.canonical_profile_index(source),
                expected_profiles.index(profile),
            )
            self.assertEqual(independent_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_exact_axis_combination_and_fallback(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for regime in generator.SIZE_REGIMES:
                    seed = (
                        10_000
                        + 100 * profile_index
                        + 10 * generator.SIZE_REGIMES.index(regime)
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        size_regime=regime,
                    )
                    expected = {
                        "scene_profile": profile,
                        "size_regime": regime,
                    }
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        independent_rule(grid),
                    )
                    data = generator._PROFILE_DATA[profile]
                    sizes = (
                        data["canonical_sizes"]
                        if regime == "canonical"
                        else data["varied_sizes"][0]
                    )
                    colors = tuple(range(1, data["count"] + 1))
                    fallback = generator._fallback_scene(
                        profile,
                        sizes,
                        colors,
                    )
                    self.assertEqual(generator.self_check(fallback), [])
                    self.assertEqual(
                        generator.observe_overrides(fallback),
                        expected,
                    )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, size_regime="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        expected_axes = {
            (profile, regime)
            for profile in generator.SCENE_PROFILES
            for regime in generator.SIZE_REGIMES
        }
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                axes = Counter()
                inputs = set()
                outputs = set()
                for offset in range(200):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    axes[(
                        observed["scene_profile"],
                        observed["size_regime"],
                    )] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(set(axes), expected_axes)
                self.assertEqual(len(inputs), 200)
                self.assertGreaterEqual(len(outputs), 180)

    def test_default_size_regime_prior_and_exact_object_counts(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            regimes = Counter()
            profiles = Counter()
            for offset in range(600):
                seed = 30_000 + 1_000 * band_index + offset
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                regimes[observed["size_regime"]] += 1
                profiles[observed["scene_profile"]] += 1
                expected_count = generator._PROFILE_DATA[
                    observed["scene_profile"]
                ]["count"]
                self.assertEqual(
                    len(independent_components(grid)),
                    expected_count,
                )
            self.assertEqual(set(regimes), set(generator.SIZE_REGIMES))
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertGreaterEqual(regimes["canonical"], 180)
            self.assertLessEqual(regimes["canonical"], 300)

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = generator.generate(
            731,
            19,
            scene_profile="compact_5x5_three",
            size_regime="canonical",
        )

        padded = [[0] * 7]
        padded.extend([[0] + row + [0] for row in original])
        padded.append([0] * 7)

        extra_object = [row[:] for row in original]
        used = {value for row in original for value in row}
        extra_color = next(color for color in range(1, 10) if color not in used)
        extra_cell = next(
            (row, col)
            for row in range(5)
            for col in range(5)
            if extra_object[row][col] == 0
        )
        extra_object[extra_cell[0]][extra_cell[1]] = extra_color

        objects = independent_components(original)
        merged_colors = [
            [
                objects[0][0] if value == objects[1][0] else value
                for value in row
            ]
            for row in original
        ]

        equal_sizes = [[0 for _col in range(6)] for _row in range(6)]
        equal_sizes[1][1:4] = [2, 2, 2]
        equal_sizes[4][2:5] = [3, 3, 3]

        unsupported_sizes = [[0 for _col in range(6)] for _row in range(6)]
        for col in range(6):
            unsupported_sizes[0][col] = 2
        unsupported_sizes[1][0] = 2
        unsupported_sizes[5][5] = 3

        for mutation in (
            padded,
            extra_object,
            merged_colors,
            equal_sizes,
            unsupported_sizes,
        ):
            self.assertNotEqual(generator.self_check(mutation), [])

        malformed = (
            [],
            [[]],
            [[1], [1, 2]],
            [[True]],
            [[10]],
            [[0] * 31],
            [[0 for _col in range(5)] for _row in range(5)],
        )
        for grid in malformed:
            self.assertNotEqual(generator.self_check(grid), [])

    def test_rule_mirror_tie_break_is_broad_and_color_ascending(self):
        grid = [[0 for _col in range(7)] for _row in range(5)]
        grid[0][0:3] = [7, 7, 7]
        grid[2][1:4] = [2, 2, 2]
        grid[4][6] = 5
        expected = [[2, 2, 2, 0, 7, 7, 7, 0, 5]]
        self.assertEqual(independent_rule(grid), expected)
        self.assertEqual(generator.rule_mirror(grid), expected)
        self.assertNotEqual(generator.self_check(grid), [])

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(1729)
        state = random.getstate()
        first = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(second, third)

    def test_source_sync_and_rule_hash(self):
        canonical = canonical_row()["program_solution"]
        live = load_rules([generator.TASK_ID])[generator.TASK_ID]
        expected = normalized_rule_hash(canonical)
        self.assertEqual(normalized_rule_hash(live), expected)
        self.assertEqual(generator.RULE_HASH, expected[:12])
        base = json.loads(BASE_FILE.read_text())
        racket = base["racket_target"]
        self.assertEqual(
            normalized_rule_hash(racket["raw_code"]),
            expected,
        )
        self.assertEqual(
            normalized_rule_hash(racket["target_code"]),
            expected,
        )
        self.assertEqual(racket["raw_code"], racket["target_code"])


if __name__ == "__main__":
    unittest.main()
