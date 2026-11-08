from __future__ import annotations

import random
import unittest

from puzzle_generators import base
from reviewer_support import canonical_pairs as read_canonical_pairs
from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("dc2c4869445c", root=ROOT)


def canonical_pairs():
    for pair in read_canonical_pairs(generator.TASK_ID, root=ROOT):
        yield pair["input"], pair["output"]


class Dc2c4869445cGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.official_profiles = {
            generator.linked_profile_signature(grid)
            for grid, _ in cls.pairs
        }

    def test_all_canonical_pairs_match_mirror_and_linked_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        self.assertEqual(len(self.official_profiles), 4)
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

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

    def test_default_exact_axis_provenance_matches_returned_grid(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(seed, seed, difficulty=band)
                finally:
                    base.set_ctx_observer(None)
                drawn = captured[-1].recorded_draws()
                observed = generator.observe_overrides(grid)
                self.assertEqual(drawn["grid_h"], len(grid))
                self.assertEqual(drawn["grid_w"], len(grid[0]))
                self.assertEqual(drawn["n_groups"], observed["n_groups"])
                self.assertEqual(
                    drawn["seeds_per_group"],
                    observed["seeds_per_group"],
                )

    def test_complete_linked_prior_is_stable_and_not_outer_tuple_only(self):
        official_dims = {(p[0], p[1]) for p in self.official_profiles}
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                strict = 0
                outer_only = 0
                witnessed = set()
                for offset in range(500):
                    seed = seed_start + offset
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                    signature = generator.linked_profile_signature(grid)
                    if signature in self.official_profiles:
                        strict += 1
                        witnessed.add(signature)
                    elif (len(grid), len(grid[0])) in official_dims:
                        outer_only += 1
                self.assertEqual(witnessed, self.official_profiles)
                self.assertGreaterEqual(strict, 125)
                self.assertLessEqual(strict, 250)
                self.assertGreater(outer_only, 0)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                first = generator.generate(seed, seed, difficulty=band)
                second = generator.generate(seed, seed, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                original = second[0][0]
                first[0][0] = (first[0][0] + 1) % 10
                replay = generator.generate(seed, seed, difficulty=band)
                self.assertEqual(replay[0][0], original)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
