from __future__ import annotations

import copy
from importlib import import_module
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


ROOT = find_root(__file__)
generator = import_module(
    "puzzle_generators.per_puzzle.d2534264df36.generator"
)


def canonical_pairs():
    return load_canonical_pairs(generator.TASK_ID, root=ROOT)


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def reference_solve(grid):
    height = len(grid)
    width = len(grid[0])
    out = copy.deepcopy(grid)
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            ring = min(
                row,
                col,
                height - 1 - row,
                width - 1 - col,
            )
            far = height - 1 - ring
            if row in (ring, far) and col in (ring, far):
                targets = (
                    (ring, ring),
                    (ring, far),
                    (far, ring),
                    (far, far),
                )
            else:
                offsets = range(ring + 2, far - 1, 2)
                targets = (
                    [(ring, offset) for offset in offsets]
                    + [(far, offset) for offset in offsets]
                    + [(offset, ring) for offset in offsets]
                    + [(offset, far) for offset in offsets]
                )
            for target_row, target_col in targets:
                out[target_row][target_col] = color
    return out


class GeneratorD2534264df36Tests(unittest.TestCase):
    def test_all_public_pairs_are_strict_and_exact(self):
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.solve_python(grid), pair["output"])
            self.assertEqual(reference_solve(grid), pair["output"])

    def test_every_profile_and_band_is_exactly_observable(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(30):
                    grid = generator.generate(
                        10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        generator.solve_python(grid),
                        reference_solve(grid),
                    )
                    self.assertNotEqual(generator.solve_python(grid), grid)

    def test_default_profile_prior_and_complete_coverage(self):
        public = 0
        total = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            for index in range(2_000):
                grid = generator.generate(
                    500_000 + 10_000 * band_index + index,
                    index,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)["scene_profile"]
                seen.add(observed)
                public += observed in generator.PUBLIC_PROFILES
                total += 1
            self.assertEqual(seen, set(generator.SCENE_PROFILES))
        self.assertGreater(public / total, 0.22)
        self.assertLess(public / total, 0.28)

    def test_public_profiles_do_not_replay_literals(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for profile_index, profile in enumerate(generator.PUBLIC_PROFILES):
            orientations = set()
            for index in range(2_000):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    scene_profile=profile,
                )
                analysis = generator._analyze(grid)
                self.assertNotIn(grid_key(grid), literals)
                orientations.add(analysis["orientation"])
            self.assertEqual(
                orientations,
                set(generator._ORIENTATIONS),
            )

    def test_control_profiles_cover_bands_and_ring_structures(self):
        expected_sizes = {
            "easy": {19},
            "medium": {19, 21},
            "hard": {21, 23},
        }
        expected_masks = {
            "dense_chain": {(True, True, True, True)},
            "alternating_chain": {
                (True, False, True, False),
                (False, True, False, True),
            },
            "sparse_chain": {
                (True, False, False, False),
                (False, True, False, False),
                (False, False, True, False),
                (False, False, False, True),
            },
        }
        for profile_index, profile in enumerate(
            generator.EXTRAPOLATION_PROFILES
        ):
            observed_masks = set()
            for band_index, band in enumerate(("easy", "medium", "hard")):
                observed_sizes = set()
                for index in range(500):
                    grid = generator.generate(
                        700_000
                        + 10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._analyze(grid)
                    self.assertEqual(analysis["ring_count"], 4)
                    observed_sizes.add(len(grid))
                    observed_masks.add(analysis["arm_mask"])
                self.assertEqual(observed_sizes, expected_sizes[band])
            self.assertEqual(observed_masks, expected_masks[profile])

    def test_mutations_are_rejected_from_final_grid(self):
        base = generator.generate(
            800_000,
            0,
            difficulty="hard",
            scene_profile="dense_chain",
        )

        ragged = copy.deepcopy(base)
        ragged[0].pop()
        self.assertEqual(generator.self_check(ragged), ["ragged"])

        invalid = copy.deepcopy(base)
        invalid[0][0] = True
        self.assertEqual(
            generator.self_check(invalid),
            ["invalid_arc_value"],
        )

        off_lattice = copy.deepcopy(base)
        off_lattice[2][2] = 9
        self.assertIn("off_odd_lattice", generator.self_check(off_lattice))

        partial_arm = copy.deepcopy(base)
        analysis = generator._analyze(base)
        ring = analysis["rings"][0]
        vertical, horizontal = analysis["orientation"]
        row = ring if vertical == "top" else len(base) - 1 - ring
        col = ring if horizontal == "left" else len(base) - 1 - ring
        toward_row = row + (2 if vertical == "top" else -2)
        partial_arm[toward_row][col] = 0
        self.assertIn("arm_pair", generator.self_check(partial_arm))

        alias = copy.deepcopy(base)
        corner_positions = []
        for ring in analysis["rings"]:
            row = ring if vertical == "top" else len(base) - 1 - ring
            col = ring if horizontal == "left" else len(base) - 1 - ring
            corner_positions.append((row, col))
        first_row, first_col = corner_positions[0]
        second_row, second_col = corner_positions[1]
        alias[second_row][second_col] = alias[first_row][first_col]
        self.assertIn("role_color_alias", generator.self_check(alias))

        mixed = copy.deepcopy(base)
        last_ring = analysis["rings"][-1]
        old_row = (
            last_ring
            if vertical == "top"
            else len(base) - 1 - last_ring
        )
        old_col = (
            last_ring
            if horizontal == "left"
            else len(base) - 1 - last_ring
        )
        new_col = len(base) - 1 - old_col
        mixed[old_row][new_col] = mixed[old_row][old_col]
        mixed[old_row][old_col] = 0
        self.assertTrue(generator.self_check(mixed))

    def test_broad_oracle_remains_more_general_than_training_grammar(self):
        grid = [[0 for _ in range(15)] for _ in range(15)]
        grid[2][4] = 7
        grid[9][3] = 4
        before = copy.deepcopy(grid)
        self.assertTrue(generator.self_check(grid))
        self.assertEqual(generator.solve_python(grid), reference_solve(grid))
        self.assertNotEqual(generator.solve_python(grid), grid)
        self.assertEqual(grid, before)

    def test_deterministic_fresh_and_global_rng_isolated(self):
        state = random.getstate()
        first = generator.generate(900_000, 17, difficulty="hard")
        second = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_both_matter(self):
        base = [generator.generate(1_000_000, index) for index in range(12)]
        different_seed = [
            generator.generate(1_000_001, index) for index in range(12)
        ]
        different_index = [
            generator.generate(1_000_000, index + 1)
            for index in range(12)
        ]
        self.assertNotEqual(base, different_seed)
        self.assertNotEqual(base, different_index)

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 0, scene_profile="invented")
        with self.assertRaises(ValueError):
            generator.generate(1, 0, grid_size=19)

    def test_version_and_rule_hash_are_pinned(self):
        self.assertEqual(generator.VERSION, "3.0.0")
        self.assertEqual(generator.RULE_HASH, "205ec75568f5")


if __name__ == "__main__":
    unittest.main()
