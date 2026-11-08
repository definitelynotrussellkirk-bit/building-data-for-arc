from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.b94abe09d9ac import generator as mod

TASK = "b94abe09d9ac"
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/dc02f6f7c147/M103__b94abe09d9ac.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def normalized_pairs(row):
    pairs = []
    for split in ("train", "test"):
        value = row[split]
        pairs.extend(value if isinstance(value, list) else [value])
    return pairs


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(cell) for cell in row] for row in grid]
    return grid


class GeneratorB94Tests(unittest.TestCase):
    def test_rule_hash_authority_and_all_five_canonical_pairs(self):
        row = canonical_row()
        source = row["program_solution"]
        self.assertEqual(
            mod.RULE_HASH,
            hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
        )
        base = json.loads(BASE.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)

        pairs = normalized_pairs(row)
        self.assertEqual(len(pairs), 5)
        expected_profiles = {name for name, *_ in mod.CANONICAL_PROFILES}
        observed_profiles = set()
        for pair in pairs:
            grid = normalize_grid(pair["input"])
            expected = normalize_grid(pair["output"])
            self.assertEqual(mod.self_check(grid), [])
            self.assertEqual(mod.rule_mirror(grid), expected)
            profile = mod.canonical_profile_signature(grid)
            self.assertIsNotNone(profile)
            observed_profiles.add(profile)
        self.assertEqual(observed_profiles, expected_profiles)

    def test_every_exact_axis_boundary_and_observer(self):
        for band in ("easy", "medium", "hard"):
            for height in (7, 9):
                for width in (13, 18):
                    for count in (3, 5):
                        for colors in (2, 3):
                            grid = mod.generate(
                                37,
                                53,
                                difficulty=band,
                                grid_h=height,
                                grid_w=width,
                                n_blobs=count,
                                n_distinct_colors=colors,
                            )
                            self.assertEqual(mod.self_check(grid, difficulty=band), [])
                            self.assertEqual(
                                mod.observe_overrides(grid),
                                {
                                    "grid_h": height,
                                    "grid_w": width,
                                    "n_blobs": count,
                                    "n_distinct_colors": colors,
                                },
                            )

    def test_complete_output_alphabet_and_all_official_profiles_are_reachable(self):
        outputs = set()
        profiles = set()
        for seed in range(800):
            for sample_index in range(6):
                grid = mod.generate(seed, sample_index)
                outputs.add(tuple(map(tuple, mod.rule_mirror(grid))))
                profile = mod.canonical_profile_signature(grid)
                if profile is not None:
                    profiles.add(profile)
        self.assertEqual(len(outputs), mod.EXPECTED_OUTPUT_CODOMAIN)
        self.assertEqual(profiles, {name for name, *_ in mod.CANONICAL_PROFILES})

    def test_color_is_counterevidence_not_a_shape_label(self):
        for colors in (2, 3):
            grid = mod.generate(
                71,
                89,
                grid_h=9,
                grid_w=18,
                n_blobs=5,
                n_distinct_colors=colors,
            )
            analysis = mod._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            self.assertTrue(analysis["duplicate_shape_different_color"])
            if colors < analysis["n_blobs"]:
                self.assertTrue(analysis["same_color_different_shape"])

    def test_self_check_rejects_minimal_and_semantic_impostors(self):
        cases = []
        cases.append([[0] * 13 for _ in range(7)])
        cases.append([[4] * 13 for _ in range(7)])
        singleton = [[0] * 13 for _ in range(7)]
        singleton[3][6] = 4
        cases.append(singleton)
        square = [[0] * 13 for _ in range(7)]
        square[2][5] = square[2][6] = square[3][5] = square[3][6] = 4
        cases.append(square)
        line = [[0] * 13 for _ in range(7)]
        line[3][5:8] = [4, 4, 4]
        cases.append(line)
        for grid in cases:
            self.assertTrue(mod.self_check(grid), grid)

        valid = mod.generate(29, 31, grid_h=9, grid_w=18, n_blobs=3, n_distinct_colors=3)
        analysis = mod._analysis(valid)
        recolored = [row[:] for row in valid]
        first = analysis["components"][0]
        row, col = first["cells"][0]
        recolored[row][col] = 9 if first["color"] != 9 else 8
        self.assertTrue(any("monochrome" in error for error in mod.self_check(recolored)))

        duplicate_indices = None
        for left in range(len(analysis["components"])):
            for right in range(left + 1, len(analysis["components"])):
                if analysis["components"][left]["shape"] == analysis["components"][right]["shape"]:
                    duplicate_indices = (left, right)
                    break
            if duplicate_indices:
                break
        self.assertIsNotNone(duplicate_indices)
        same_color = [row[:] for row in valid]
        left, right = duplicate_indices
        replacement = analysis["components"][left]["color"]
        for row, col in analysis["components"][right]["cells"]:
            same_color[row][col] = replacement
        self.assertTrue(
            any("equal-shape pair must use different colors" in error for error in mod.self_check(same_color))
        )

    def test_negative_official_recombination_is_not_strict(self):
        _, _, _, shapes = mod.CANONICAL_PROFILES[0]
        labels = [0, 0, 1]
        grid = mod._render_scene(8, 13, list(shapes), labels, 2, random.Random(5))
        self.assertEqual(mod.self_check(grid), [])
        self.assertIsNone(mod.canonical_profile_signature(grid))

    def test_determinism_fresh_returns_global_rng_and_unknowns(self):
        random.seed(12345)
        state = random.getstate()
        first = mod.generate(17, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = mod.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            mod.generate(1, 2, difficulty="extreme")
        with self.assertRaises(ValueError):
            mod.generate(1, 2, texture="warm")
        with self.assertRaises(ValueError):
            mod.generate(1, 2, grid_h=6)


if __name__ == "__main__":
    unittest.main()
