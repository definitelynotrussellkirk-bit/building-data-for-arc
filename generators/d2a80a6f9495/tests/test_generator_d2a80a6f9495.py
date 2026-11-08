from __future__ import annotations

import unittest

from puzzle_generators.per_puzzle.d2a80a6f9495 import generator
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
OFFICIAL_PROFILES = {
    (7, 7, 1, 0),
    (8, 9, 2, 0),
    (12, 12, 4, 0),
    (13, 10, 3, 0),
}


def canonical_inputs():
    for pair in canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True):
        yield pair["input"]


class D2a80a6f9495GeneratorTests(unittest.TestCase):
    def test_every_canonical_input_has_an_official_linked_profile(self):
        inputs = list(canonical_inputs())
        self.assertEqual(len(inputs), 4)
        self.assertEqual(
            {generator.profile_signature(grid) for grid in inputs},
            OFFICIAL_PROFILES,
        )
        for grid in inputs:
            self.assertEqual(generator.self_check(grid), [])

    def test_explicit_none_is_identical_and_unknown_texture_rejects(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                with self.subTest(band=band, seed=seed):
                    omitted = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                    explicit = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture="none",
                    )
                    self.assertEqual(omitted, explicit)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(0, 0, texture="bogus")

    def test_linked_prior_is_stable_in_every_band(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                with self.subTest(seed_start=seed_start, band=band):
                    exact = 0
                    witnessed = set()
                    for offset in range(400):
                        seed = seed_start + offset
                        grid = generator.generate(
                            seed,
                            seed,
                            difficulty=band,
                        )
                        self.assertEqual(
                            generator.self_check(grid, difficulty=band),
                            [],
                        )
                        signature = generator.profile_signature(grid)
                        if signature in OFFICIAL_PROFILES:
                            exact += 1
                            witnessed.add(signature)
                    self.assertEqual(witnessed, OFFICIAL_PROFILES)
                    self.assertGreaterEqual(exact, 70)
                    self.assertLessEqual(exact, 190)

    def test_shape_blind_degenerate_impostors_reject(self):
        def solid(value, height=8, width=8):
            return [[value] * width for _ in range(height)]

        malformed = {
            "one_color_full": solid(3),
            "three_color_full": [
                [1 + (row + col) % 3 for col in range(8)]
                for row in range(8)
            ],
            "singleton": [
                [5 if (row, col) == (3, 3) else 0 for col in range(8)]
                for row in range(8)
            ],
            "solid_2x2": [
                [
                    5 if 2 <= row <= 3 and 2 <= col <= 3 else 0
                    for col in range(8)
                ]
                for row in range(8)
            ],
            "line_1x4": [
                [
                    5 if row == 3 and 2 <= col <= 5 else 0
                    for col in range(8)
                ]
                for row in range(8)
            ],
        }
        for name, grid in malformed.items():
            with self.subTest(name=name):
                self.assertTrue(generator.self_check(grid))

    def test_exact_degenerate_controls_remain_lawful(self):
        for texture in generator.DEGENERATE_TEXTURES:
            grid = generator.generate(
                17,
                17,
                difficulty="medium",
                texture=texture,
            )
            self.assertEqual(generator.self_check(grid), [])


if __name__ == "__main__":
    unittest.main()
