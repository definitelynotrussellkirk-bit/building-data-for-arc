"""Focused semantic and contract tests for generator 9d488d6a3875."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from scripts.rule_smoke import load_rules


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.9d488d6a3875.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/be1bc1d91387/"
    "E137__9d488d6a3875.json"
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


def reference_rule(grid):
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    height = len(original)
    width = len(original[0])
    for row in range(height):
        colors = list(dict.fromkeys(
            value for value in original[row] if value
        ))
        for color in colors:
            columns = [
                col
                for col in range(width)
                if original[row][col] == color
            ]
            if len(columns) != 2:
                continue
            start, end = min(columns), max(columns)
            if all(
                original[row][col] in (0, color)
                for col in range(start, end + 1)
            ):
                for col in range(start, end + 1):
                    output[row][col] = color
    for col in range(width):
        colors = list(dict.fromkeys(
            original[row][col]
            for row in range(height)
            if original[row][col]
        ))
        for color in colors:
            rows = [
                row
                for row in range(height)
                if original[row][col] == color
            ]
            if len(rows) != 2:
                continue
            start, end = min(rows), max(rows)
            if all(
                original[row][col] in (0, color)
                for row in range(start, end + 1)
            ):
                for row in range(start, end + 1):
                    output[row][col] = color
    return output


def blank(height, width):
    return [[0 for _col in range(width)] for _row in range(height)]


class Generator9d488d6a3875Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        expected_profiles = generator.SCENE_PROFILES
        self.assertEqual(len(self.pairs), 5)
        for pair, profile in zip(self.pairs, expected_profiles):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.observe_overrides(source),
                {
                    "scene_profile": profile,
                    "span_regime": "canonical",
                },
            )
            self.assertEqual(
                generator.canonical_profile_index(source),
                expected_profiles.index(profile),
            )
            self.assertEqual(reference_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_exact_axis_combination(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for regime in generator.SPAN_REGIMES:
                    seed = (
                        10_000
                        + 100 * profile_index
                        + 10 * generator.SPAN_REGIMES.index(regime)
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        span_regime=regime,
                    )
                    expected = {
                        "scene_profile": profile,
                        "span_regime": regime,
                    }
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        reference_rule(grid),
                    )
                    self.assertNotEqual(grid, reference_rule(grid))
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, span_regime="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        expected_axes = {
            (profile, regime)
            for profile in generator.SCENE_PROFILES
            for regime in generator.SPAN_REGIMES
        }
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                axes = Counter()
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = reference_rule(grid)
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    axes[(
                        observed["scene_profile"],
                        observed["span_regime"],
                    )] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(set(axes), expected_axes)
                self.assertGreaterEqual(len(inputs), 285)
                self.assertGreaterEqual(len(outputs), 285)

    def test_default_prior_and_difficulty_span_mass(self):
        varied_means = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            regimes = Counter()
            profiles = Counter()
            varied_masses = []
            for offset in range(1_000):
                seed = 30_000 + 2_000 * band_index + offset
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                regimes[observed["span_regime"]] += 1
                profiles[observed["scene_profile"]] += 1
                if observed["span_regime"] == "varied":
                    analysis = generator._analyze_scene(grid)
                    varied_masses.append(sum(
                        record["length"]
                        for record in analysis["records"]
                    ))
            self.assertEqual(set(regimes), set(generator.SPAN_REGIMES))
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertGreaterEqual(regimes["canonical"], 320)
            self.assertLessEqual(regimes["canonical"], 480)
            varied_means[band] = sum(varied_masses) / len(varied_masses)
        self.assertLess(varied_means["easy"], varied_means["medium"])
        self.assertLess(varied_means["medium"], varied_means["hard"])

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = self.pairs[0]["input"]
        padded = [[0] * 11]
        padded.extend([[0] + row + [0] for row in original])
        padded.append([0] * 11)

        extra_color = [row[:] for row in original]
        extra_color[0][0] = 9

        off_axis = blank(7, 9)
        off_axis[0][0] = off_axis[2][2] = 2
        off_axis[6][0] = off_axis[6][4] = 3

        crossing = blank(7, 9)
        crossing[3][1] = crossing[3][7] = 2
        crossing[1][4] = crossing[5][4] = 3

        blocked = blank(7, 9)
        blocked[3][1] = blocked[3][7] = 2
        blocked[3][4] = blocked[6][4] = 3

        too_short = blank(7, 9)
        too_short[1][1] = too_short[1][3] = 2
        too_short[6][0] = too_short[6][4] = 3

        repeated_color = blank(7, 9)
        repeated_color[1][1] = repeated_color[1][5] = 4
        repeated_color[5][2] = repeated_color[5][6] = 4

        for mutation in (
            padded,
            extra_color,
            off_axis,
            crossing,
            blocked,
            too_short,
            repeated_color,
        ):
            self.assertNotEqual(generator.self_check(mutation), [])
            self.assertEqual(generator.observe_overrides(mutation), {})

        malformed = (
            [],
            [[]],
            [[1], [1, 2]],
            [[True]],
            [[10]],
            [[0] * 31],
            blank(7, 9),
        )
        for grid in malformed:
            self.assertNotEqual(generator.self_check(grid), [])

    def test_rule_mirror_is_broad_and_preserves_row_then_column_order(self):
        crossing = blank(7, 7)
        crossing[3][1] = crossing[3][5] = 2
        crossing[1][3] = crossing[5][3] = 4

        blocker = blank(7, 7)
        blocker[3][1] = blocker[3][5] = 2
        blocker[3][3] = blocker[6][3] = 4

        repeated = blank(8, 8)
        repeated[1][1] = repeated[1][5] = 5
        repeated[6][2] = repeated[6][6] = 5

        three_in_row = blank(6, 7)
        three_in_row[2][1] = 7
        three_in_row[2][3] = 7
        three_in_row[2][5] = 7

        for grid in (crossing, blocker, repeated, three_in_row):
            snapshot = [row[:] for row in grid]
            self.assertEqual(
                generator.rule_mirror(grid),
                reference_rule(grid),
            )
            self.assertEqual(grid, snapshot)
        crossing_output = generator.rule_mirror(crossing)
        self.assertEqual(crossing_output[3][3], 4)
        self.assertEqual(generator.rule_mirror(three_in_row), three_in_row)

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
