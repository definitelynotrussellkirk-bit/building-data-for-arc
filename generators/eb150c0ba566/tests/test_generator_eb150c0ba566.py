from __future__ import annotations

import unittest

from puzzle_generators.per_puzzle.eb150c0ba566 import generator


CANONICAL_ZERO_ANCHOR = [
    [0, 2, 0, 9, 0, 3, 3],
    [0, 2, 0, 9, 3, 3, 0],
    [2, 2, 0, 9, 0, 0, 0],
    [9, 9, 9, 9, 9, 9, 9],
    [0, 3, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]


class Eb150c0ba566GeneratorTests(unittest.TestCase):
    def test_self_check_accepts_canonical_prototypes_without_top_left_cells(self):
        self.assertEqual(generator.self_check(CANONICAL_ZERO_ANCHOR), [])

    def test_impossible_exact_seed_override_is_rejected_not_silently_underplaced(self):
        with self.assertRaises(ValueError):
            generator.generate(
                0,
                0,
                difficulty="easy",
                grid_h=9,
                grid_w=7,
                n_seeds=3,
            )

    def test_sampler_exercises_seed_erasure_cases(self):
        saw_proto2_without_top_left = False
        saw_proto3_without_top_left = False
        for seed in range(200):
            grid = generator.generate(seed, seed * 13 + 1, difficulty="medium")
            self.assertEqual(generator.self_check(grid), [])
            saw_proto2_without_top_left |= grid[0][0] == 0
            saw_proto3_without_top_left |= grid[0][4] == 0
        self.assertTrue(saw_proto2_without_top_left)
        self.assertTrue(saw_proto3_without_top_left)


if __name__ == "__main__":
    unittest.main()
