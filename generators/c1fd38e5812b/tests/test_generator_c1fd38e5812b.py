from __future__ import annotations

import copy
import json
import random
import unittest

from reviewer_support import (
    canonical_pairs as selected_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
generator, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    "c1fd38e5812b", root=ROOT)


def canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (
            row.get("task_id") == generator.TASK_ID
            and row.get("source") == "training"
        ):
            return row
    raise RuntimeError("canonical row not found")


def canonical_pairs():
    rows = [json.loads(line) for line in
            canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    variants = [row for row in rows if row.get("task_id") == generator.TASK_ID]
    training = next(index for index, row in enumerate(variants)
                    if row.get("source") == "training")
    return selected_canonical_pairs(generator.TASK_ID, root=ROOT, variant=training)


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def reference_solve(grid):
    row_starts = [0] + [
        row
        for row in range(1, len(grid))
        if grid[row][0] != grid[row - 1][0]
    ]
    col_starts = [0] + [
        col
        for col in range(1, len(grid[0]))
        if grid[0][col] != grid[0][col - 1]
    ]
    return [
        [grid[row][col] for col in col_starts]
        for row in row_starts
    ]


class GeneratorC1fd38e5812bTests(unittest.TestCase):
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

    def test_default_profile_prior_and_band_coverage(self):
        public = 0
        uniform = 0
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
                uniform += observed == "uniform_runs"
                total += 1
            self.assertEqual(seen, set(generator.SCENE_PROFILES))
        self.assertGreater(public / total, 0.22)
        self.assertLess(public / total, 0.28)
        self.assertGreater(uniform / total, 0.07)
        self.assertLess(uniform / total, 0.13)

    def test_public_profiles_preserve_roles_without_literal_replay(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for profile_index, profile in enumerate(generator.PUBLIC_PROFILES):
            observed_shapes = set()
            for index in range(1_000):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    scene_profile=profile,
                )
                analysis = generator._analyze(grid)
                self.assertEqual(
                    analysis["canonical_answer_profile"],
                    profile,
                )
                self.assertNotIn(grid_key(grid), literals)
                observed_shapes.add((len(grid), len(grid[0])))
            expected_shapes = {
                (
                    len(generator._transform(
                        generator._PUBLIC_INPUTS[profile],
                        transform,
                    )),
                    len(generator._transform(
                        generator._PUBLIC_INPUTS[profile],
                        transform,
                    )[0]),
                )
                for transform in generator._PUBLIC_SAFE_TRANSFORMS[profile]
            }
            self.assertEqual(observed_shapes, expected_shapes)

    def test_default_generation_never_replays_a_public_literal(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for index in range(5_000):
            grid = generator.generate(700_000 + index, index)
            self.assertNotIn(grid_key(grid), literals)

    def test_nonuniform_and_interior_profiles_cover_hard_cases(self):
        row_spans = set()
        col_spans = set()
        logical_shapes = set()
        for profile_index, profile in enumerate(
            ("nonuniform_runs", "interior_merges")
        ):
            for index in range(2_000):
                grid = generator.generate(
                    800_000 + 10_000 * profile_index + index,
                    index,
                    difficulty="hard",
                    scene_profile=profile,
                )
                analysis = generator._analyze(grid)
                self.assertGreater(len(set(analysis["row_spans"])), 1)
                self.assertGreater(len(set(analysis["col_spans"])), 1)
                self.assertEqual(
                    analysis["interior_merge"],
                    profile == "interior_merges",
                )
                row_spans.update(analysis["row_spans"])
                col_spans.update(analysis["col_spans"])
                logical_shapes.add(
                    (
                        analysis["logical_rows"],
                        analysis["logical_cols"],
                    )
                )
        self.assertEqual(row_spans, set(range(2, 13)))
        self.assertEqual(col_spans, set(range(2, 13)))
        self.assertTrue(
            {
                (rows, cols)
                for rows in range(3, 7)
                for cols in range(3, 7)
            }.issubset(logical_shapes)
        )

    def test_uniform_profile_is_lawful_but_explicit(self):
        for index in range(500):
            grid = generator.generate(
                900_000 + index,
                index,
                difficulty="hard",
                scene_profile="uniform_runs",
            )
            analysis = generator._analyze(grid)
            self.assertTrue(analysis["uniform_runs"])
            self.assertFalse(analysis["interior_merge"])
            self.assertEqual(analysis["scene_profile"], "uniform_runs")

    def test_mutations_are_rejected_from_final_grid(self):
        grid = generator.generate(
            1_000_000,
            0,
            difficulty="hard",
            scene_profile="nonuniform_runs",
        )
        analysis = generator._analyze(grid)

        broken_block = copy.deepcopy(grid)
        row1 = analysis["row_starts"][0]
        row2 = analysis["row_starts"][1]
        col1 = analysis["col_starts"][0]
        col2 = analysis["col_starts"][1]
        row = row1 if row2 - row1 == 1 else row1 + 1
        col = col1 if col2 - col1 == 1 else col1 + 1
        broken_block[row][col] = (
            broken_block[row][col] + 1
        ) % 10
        self.assertIn(
            "non_solid_logical_block",
            generator.self_check(broken_block),
        )

        collapsed_row_axis = copy.deepcopy(grid)
        boundary_row = analysis["row_starts"][1]
        collapsed_row_axis[boundary_row][0] = grid[boundary_row - 1][0]
        self.assertTrue(generator.self_check(collapsed_row_axis))

        collapsed_col_axis = copy.deepcopy(grid)
        boundary_col = analysis["col_starts"][1]
        collapsed_col_axis[0][boundary_col] = grid[0][boundary_col - 1]
        self.assertTrue(generator.self_check(collapsed_col_axis))

        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        self.assertEqual(generator.self_check(ragged), ["ragged"])

        invalid = copy.deepcopy(grid)
        invalid[0][0] = True
        self.assertEqual(
            generator.self_check(invalid),
            ["invalid_arc_value"],
        )

        too_small = generator._expand(
            [[1, 2], [3, 4]],
            [2, 2],
            [2, 2],
        )
        self.assertIn("dimension_range", generator.self_check(too_small))

        monochrome = [[3 for _ in range(12)] for _ in range(12)]
        self.assertIn("output_palette", generator.self_check(monochrome))

        identity = [[1, 2], [3, 4]]
        self.assertIn("identity", generator.self_check(identity))

    def test_broad_oracle_outside_strict_training_grammar(self):
        grid = generator._expand(
            [[1, 2, 3], [4, 5, 6]],
            [1, 6],
            [2, 3, 4],
        )
        before = copy.deepcopy(grid)
        self.assertTrue(generator.self_check(grid))
        self.assertEqual(
            generator.solve_python(grid),
            [[1, 2, 3], [4, 5, 6]],
        )
        self.assertEqual(generator.solve_python(grid), reference_solve(grid))
        self.assertEqual(grid, before)

    def test_deterministic_fresh_and_rng_isolated(self):
        state = random.getstate()
        first = generator.generate(1_100_000, 17, difficulty="hard")
        second = generator.generate(1_100_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_both_matter(self):
        base = [
            generator.generate(1_200_000, index)
            for index in range(12)
        ]
        different_seed = [
            generator.generate(1_200_001, index)
            for index in range(12)
        ]
        different_index = [
            generator.generate(1_200_000, index + 1)
            for index in range(12)
        ]
        self.assertNotEqual(base, different_seed)
        self.assertNotEqual(base, different_index)

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 1, unknown_axis="x")
        with self.assertRaises(ValueError):
            generator.generate(1, 1, scene_profile="not_a_profile")

    def test_base_sources_match_canonical_program(self):
        program = canonical_row()["program_solution"]
        for relative in (
            "base/solutions/training/"
            "e1baa8a4__c1fd38e5812b.json",
            "base/solutions/augmented/"
            "e1baa8a4__ae9e6741664f.json",
        ):
            data_root = canonical_path(ROOT).parents[1]
            base = json.loads((data_root / relative).read_text(encoding="utf-8"))
            self.assertEqual(base["racket_target"]["raw_code"], program)
            self.assertEqual(base["racket_target"]["target_code"], program)
        # The inherited module pin remains a separate, unresolved provenance
        # discrepancy. Canonical program identity above comes from the ledger.
        self.assertEqual(generator.RULE_HASH, "dc8aa1222f34")


if __name__ == "__main__":
    unittest.main()
