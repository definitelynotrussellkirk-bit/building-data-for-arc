from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

module = importlib.import_module("puzzle_generators.per_puzzle.1a2f04639576.generator")


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "1a2f04639576"


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def all_pairs(row):
    yield from row["train"]
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    yield from tests


def row_counts(grid):
    return tuple(sum(value != 0 for value in row) for row in grid)


class Generator1a2f04639576Tests(unittest.TestCase):
    def test_rule_hash_sources_and_all_canonical_pairs(self):
        row = canonical_row()
        normalized = " ".join(row["program_solution"].split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
        self.assertEqual(module.RULE_HASH, digest)
        self.assertEqual(module.RULE_HASH, "8cd149b15ecf")

        base_path = ROOT / "data/base/solutions/banks/c0e651d407f3/E153__1a2f04639576.json"
        base = json.loads(base_path.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], row["program_solution"])
        self.assertEqual(base["racket_target"]["target_code"], row["program_solution"])

        expected_profiles = (
            "rows_3203_4x6",
            "rows_222_3x5",
            "rows_3130_4x7",
        )
        for pair, profile in zip(all_pairs(row), expected_profiles):
            self.assertEqual(module.self_check(pair["input"]), [])
            self.assertEqual(module.canonical_profile_signature(pair["input"]), profile)
            self.assertEqual(module.rule_mirror(pair["input"]), pair["output"])

    def test_profiles_are_exact_observable_and_nontrivial(self):
        for profile in module.SCENE_PROFILES:
            for band in ("easy", "medium", "hard"):
                for seed in range(12):
                    grid = module.generate(
                        seed,
                        seed + 100,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(module.self_check(grid, difficulty=band), [])
                    self.assertEqual(module.observe_overrides(grid), {"scene_profile": profile})
                    self.assertNotEqual(module.rule_mirror(grid), grid)
                    if profile in module.PUBLIC_PROFILES:
                        self.assertEqual(module.canonical_profile_signature(grid), profile)
                    else:
                        self.assertIsNone(module.canonical_profile_signature(grid))

    def test_determinism_fresh_returns_and_global_rng(self):
        before = random.getstate()
        first = module.generate(91, 7, difficulty="hard")
        second = module.generate(91, 7, difficulty="hard")
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(second, module.generate(91, 7, difficulty="hard"))
        self.assertEqual(before, after)

    def test_generalized_census_reaches_semantic_branches(self):
        observed_counts = set()
        dimensions = set()
        saw_empty = saw_no_empty = False
        saw_compact_row = saw_repeated_row = False
        for band in ("easy", "medium", "hard"):
            for seed in range(160):
                grid = module.generate(
                    seed,
                    seed + 500,
                    difficulty=band,
                    scene_profile="generalized",
                )
                counts = row_counts(grid)
                observed_counts.update(counts)
                dimensions.add((len(grid), len(grid[0])))
                saw_empty |= 0 in counts
                saw_no_empty |= 0 not in counts
                packed = module.rule_mirror(grid)
                saw_compact_row |= any(
                    count > 0 and row == packed[index]
                    for index, (row, count) in enumerate(zip(grid, counts))
                )
                saw_repeated_row |= any(
                    len(values := [value for value in row if value]) != len(set(values))
                    for row in grid
                )
        self.assertTrue({0, 1, 2, 3, 4}.issubset(observed_counts))
        self.assertIn((3, 5), dimensions)
        self.assertIn((5, 7), dimensions)
        self.assertTrue(saw_empty)
        self.assertTrue(saw_no_empty)
        self.assertTrue(saw_compact_row)
        self.assertTrue(saw_repeated_row)

    def test_structural_impostors_and_negative_recombination_are_rejected(self):
        impostors = {
            "full_one_color": [[3] * 6 for _ in range(4)],
            "singleton": [[0] * 6 for _ in range(4)],
            "solid_2x2": [[0] * 6 for _ in range(4)],
            "short_line": [[0] * 6 for _ in range(4)],
            "identity": [
                [9, 1, 4, 0, 0, 0],
                [3, 2, 0, 0, 0, 0],
                [7, 6, 5, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ],
            "ascending_recombination": [
                [0, 1, 0, 2, 0, 3, 0],
                [4, 0, 0, 5, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ],
        }
        impostors["singleton"][2][3] = 3
        for row in (1, 2):
            for col in (2, 3):
                impostors["solid_2x2"][row][col] = 3
        for col in (1, 2, 3):
            impostors["short_line"][1][col] = 3

        for name, grid in impostors.items():
            self.assertTrue(module.self_check(grid), name)
        recombination = impostors["ascending_recombination"]
        self.assertIsNone(module.canonical_profile_signature(recombination))

    def test_invalid_controls_reject_loudly(self):
        with self.assertRaises(ValueError):
            module.generate(0, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            module.generate(0, 0, unknown_axis=1)
        with self.assertRaises(ValueError):
            module.generate(0, 0, scene_profile="not_a_profile")


if __name__ == "__main__":
    unittest.main()
