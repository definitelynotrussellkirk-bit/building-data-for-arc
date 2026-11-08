from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs as _canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator("c1b540a1d7b0", root=ROOT)
OFFICIAL_PROFILES = {
    (8, 10, 1, 3, 2, 9, 12),
    (9, 11, 1, 2, 3, 9, 12),
    (8, 9, 2, 2, 2, 6, 8),
    (8, 11, 1, 3, 4, 12, 12),
}


def canonical_pairs():
    for row in _canonical_pairs(generator.TASK_ID, root=ROOT):
        yield row["input"], row.get("output")


def grid_with(cells):
    grid = [[0] * 10 for _ in range(8)]
    for row, col in cells:
        grid[row][col] = 5
    return grid


class C1b540a1d7b0GeneratorTests(unittest.TestCase):
    def test_canonical_pairs_match_mirror_and_complete_profiles(self):
        profiles = set()
        pairs = list(canonical_pairs())
        self.assertEqual(len(pairs), 4)
        for grid, expected in pairs:
            self.assertEqual(generator.self_check(grid), [])
            if expected is not None:
                self.assertEqual(generator.rule_mirror(grid), expected)
            profiles.add(generator.profile_signature(grid))
        self.assertEqual(profiles, OFFICIAL_PROFILES)

    def test_linked_profile_prior_is_stable_in_every_band(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                with self.subTest(seed_start=seed_start, band=band):
                    witnessed = set()
                    exact = 0
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
                        red, cyan = generator._mirror_totals(grid)
                        self.assertGreater(red, 0)
                        self.assertGreater(cyan, 0)
                        signature = generator.profile_signature(grid)
                        if signature in OFFICIAL_PROFILES:
                            exact += 1
                            witnessed.add(signature)
                    self.assertEqual(witnessed, OFFICIAL_PROFILES)
                    self.assertGreaterEqual(exact, 60)
                    self.assertLessEqual(exact, 140)

    def test_strict_profile_is_linked_not_marginal(self):
        for profile in OFFICIAL_PROFILES:
            for other in OFFICIAL_PROFILES:
                if profile == other:
                    continue
                recombined = profile[:5] + other[5:]
                if recombined != profile:
                    self.assertNotIn(recombined, OFFICIAL_PROFILES)

    def test_self_check_rejects_malformed_room_impostors(self):
        room = {(2, 2), (2, 3), (3, 2), (3, 3)}
        malformed = {
            "singleton": {(3, 3)},
            "domino": {(3, 3), (3, 4)},
            "l_triomino": {(3, 3), (3, 4), (4, 3)},
            "solid_3x3": {
                (row, col)
                for row in range(2, 5)
                for col in range(2, 5)
            },
            "two_singletons": {(2, 2), (5, 7)},
            "bent_arm": room | {(3, 4), (4, 4)},
            "plus_arm": room
            | {(2, 4), (2, 5), (1, 5), (3, 5), (2, 6)},
        }
        for name, cells in malformed.items():
            with self.subTest(name=name):
                self.assertTrue(generator.self_check(grid_with(cells)))

    def test_declared_edge_cases_are_narrow_and_lawful(self):
        for texture in generator.DEGENERATE_TEXTURES:
            grid = generator.generate(
                0,
                0,
                difficulty="medium",
                texture=texture,
            )
            self.assertEqual(generator.self_check(grid), [])

        wrong_size_empty = [[0] * 9 for _ in range(8)]
        wrong_size_full = [[5] * 9 for _ in range(8)]
        self.assertTrue(generator.self_check(wrong_size_empty))
        self.assertTrue(generator.self_check(wrong_size_full))

        for seed in range(30):
            pure_room = generator.generate(
                seed,
                seed,
                difficulty="medium",
                n_rooms=1,
                n_tips=0,
            )
            self.assertEqual(generator.self_check(pure_room), [])
            self.assertEqual(generator.observe_overrides(pure_room)["n_rooms"], 1)
            self.assertEqual(generator.observe_overrides(pure_room)["n_tips"], 0)

            linked_rooms = generator.generate(
                seed,
                seed,
                difficulty="medium",
                n_rooms=2,
                n_tips=0,
            )
            self.assertEqual(generator.self_check(linked_rooms), [])
            red, cyan = generator._mirror_totals(linked_rooms)
            self.assertGreater(red, 0)
            self.assertGreater(cyan, 0)


if __name__ == "__main__":
    unittest.main()
