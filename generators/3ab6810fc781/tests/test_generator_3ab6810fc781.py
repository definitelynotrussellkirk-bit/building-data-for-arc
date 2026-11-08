from __future__ import annotations

import importlib
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.3ab6810fc781.generator"
)


def canonical_pairs():
    pairs = []
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != GEN.TASK_ID:
                continue
            for split in ("train", "test"):
                pairs.extend(row.get(split, []))
    return pairs


class Generator3ab6810fc781Tests(unittest.TestCase):
    def test_all_canonical_pairs_are_accepted_and_oracle_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 3)
        signatures = set()
        for pair in pairs:
            grid = pair["input"]
            self.assertEqual(GEN.self_check(grid), [])
            self.assertEqual(GEN.rule_mirror(grid), pair["output"])
            signatures.add(GEN.canonical_profile_signature(grid))
        self.assertEqual(signatures, set(GEN._CANONICAL_SIGNATURES))
        self.assertEqual(len(signatures), 3)

    def test_generated_instances_are_deterministic_fresh_valid_and_nonidentity(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for sample_index in range(80):
                first = GEN.generate(314159, sample_index, difficulty=difficulty)
                second = GEN.generate(314159, sample_index, difficulty=difficulty)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertIsNot(first[0], second[0])
                self.assertEqual(GEN.self_check(first, difficulty=difficulty), [])
                output = GEN.rule_mirror(first)
                self.assertNotEqual(first, output)
                self.assertLessEqual(len(output), len(first))
                self.assertLessEqual(len(output[0]), len(first[0]))

    def test_default_distribution_reaches_all_profiles_and_bbox_area_traps(self):
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            profile_counts = {signature: 0 for signature in GEN._CANONICAL_SIGNATURES}
            bbox_traps = 0
            for sample_index in range(600):
                grid = GEN.generate(700000 + band_index, sample_index, difficulty=difficulty)
                signature = GEN.canonical_profile_signature(grid)
                if signature in profile_counts:
                    profile_counts[signature] += 1
                analysis = GEN._analysis(grid)
                largest = max(analysis["components"], key=len)
                largest_area = GEN._bbox(largest)[2] * GEN._bbox(largest)[3]
                decoy_area = max(
                    GEN._bbox(cells)[2] * GEN._bbox(cells)[3]
                    for cells in analysis["components"]
                    if cells != largest
                )
                bbox_traps += decoy_area > largest_area
            self.assertGreaterEqual(sum(profile_counts.values()), 30, profile_counts)
            self.assertTrue(all(count >= 5 for count in profile_counts.values()), profile_counts)
            self.assertGreaterEqual(bbox_traps, 20)

    def test_exact_dimension_overrides_and_contract(self):
        for height, width in ((8, 8), (8, 16), (16, 8), (16, 16), (11, 13)):
            grid = GEN.generate(42, height * 100 + width, grid_h=height, grid_w=width)
            self.assertEqual((len(grid), len(grid[0])), (height, width))
            self.assertEqual(
                GEN.observe_overrides(grid),
                {"grid_h": height, "grid_w": width},
            )
            self.assertEqual(GEN.self_check(grid), [])
        with self.assertRaises(ValueError):
            GEN.generate(1, 0, grid_h=7)
        with self.assertRaises(ValueError):
            GEN.generate(1, 0, grid_w=17)
        with self.assertRaises(TypeError):
            GEN.generate(1, 0, texture="legacy")

    def test_valid_negative_recombination_is_not_a_canonical_profile(self):
        near_miss = [list(row) for row in GEN._CANONICAL_TEMPLATES[0]]
        near_miss[1][1] = 9
        self.assertEqual(GEN.self_check(near_miss), [])
        self.assertNotIn(
            GEN.canonical_profile_signature(near_miss),
            GEN._CANONICAL_SIGNATURES,
        )

    def test_self_check_rejects_targeted_mutations_and_minimal_impostors(self):
        base = [list(row) for row in GEN._CANONICAL_TEMPLATES[0]]
        mutations = {
            "min_minus_one": base[:-2],
            "max_plus_one": base + [[0] * len(base[0]) for _ in range(8)],
            "all_zero": [[0] * 9 for _ in range(9)],
            "single_blob": [[0] * 9 for _ in range(9)],
            "full_grid": [[3] * 9 for _ in range(9)],
        }
        mutations["single_blob"][3][3] = 3

        only_two = [row[:] for row in base]
        for row in range(len(only_two)):
            for column in range(len(only_two[0])):
                if only_two[row][column] == 4:
                    only_two[row][column] = 0
        mutations["only_two_components"] = only_two

        tied = [[0] * 10 for _ in range(10)]
        for row, column in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1)):
            tied[row][column] = 2
        for row, column in ((6, 6), (6, 7), (7, 6), (7, 7), (8, 6)):
            tied[row][column] = 3
        tied[1][8] = tied[2][8] = 4
        mutations["tied_largest"] = tied

        solid = [[0] * 10 for _ in range(10)]
        for row in range(1, 4):
            for column in range(1, 4):
                solid[row][column] = 2
        solid[7][1] = solid[7][2] = 3
        solid[7][7] = solid[8][7] = 4
        mutations["solid_largest"] = solid

        leaking = [[0] * 10 for _ in range(10)]
        for column in range(1, 6):
            leaking[1][column] = 2
        for row in range(2, 6):
            leaking[row][1] = 2
        leaking[3][3] = 4
        leaking[7][1] = leaking[7][2] = 5
        leaking[7][7] = leaking[8][7] = 6
        mutations["decoy_inside_selected_bbox"] = leaking

        for name, grid in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid), name)

    def test_generation_preserves_process_global_rng(self):
        random.seed(99173)
        before = random.getstate()
        GEN.generate(100, 4, difficulty="hard")
        self.assertEqual(before, random.getstate())


if __name__ == "__main__":
    unittest.main()
