from __future__ import annotations

import json
import unittest
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_pairs as read_canonical_pairs, find_root, load_selected_generator

generator, _, _ = load_selected_generator("dc155169ea57", root=find_root(__file__))


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_PROFILES = {
    (9, 9, 5, 3, 1, 2),
    (7, 7, 3, 1, 0, 1),
    (11, 11, 6, 3, 1, 2),
    (18, 18, 8, 5, 3, 2),
}


def canonical_pairs():
    for pair in read_canonical_pairs(generator.TASK_ID, root=find_root(__file__)):
        yield pair["input"], pair["output"]


class Dc155169ea57GeneratorTests(unittest.TestCase):
    def test_canonical_pairs_match_mirror_and_linked_profiles(self):
        pairs = list(canonical_pairs())
        self.assertEqual(len(pairs), 4)
        self.assertEqual(
            {generator.profile_signature(grid) for grid, _ in pairs},
            OFFICIAL_PROFILES,
        )
        for grid, expected in pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

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
                    self.assertGreaterEqual(exact, 75)
                    self.assertLessEqual(exact, 165)

    def test_narrow_width_draws_shape_count_from_feasible_domain(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        grid_w=7,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertTrue(captured)
                drawn = captured[-1].recorded_draws()["n_shapes"]
                observed = generator.observe_overrides(grid)["n_shapes"]
                self.assertEqual(drawn, observed)

    def test_line_requires_three_rows_below(self):
        lawful = generator.generate(
            0,
            0,
            difficulty="easy",
            grid_h=7,
            grid_w=7,
            line_row=3,
            n_shapes=1,
            thin_frac=1.0,
        )
        self.assertEqual(generator.self_check(lawful), [])

        malformed = [row[:] for row in lawful]
        malformed[3], malformed[4] = malformed[4], malformed[3]
        self.assertTrue(generator.self_check(malformed))
        with self.assertRaises(ValueError):
            generator.generate(
                0,
                0,
                difficulty="easy",
                grid_h=7,
                grid_w=7,
                line_row=4,
                n_shapes=1,
                thin_frac=1.0,
            )

    def test_explicit_none_is_identical_and_unknown_texture_rejects(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                omitted = generator.generate(seed, seed, difficulty=band)
                explicit = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    texture="none",
                )
                self.assertEqual(omitted, explicit)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(0, 0, texture="bogus")


if __name__ == "__main__":
    unittest.main()
