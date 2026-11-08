from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import sys
import unittest


for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (  # noqa: E402
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("b57f299dcdb3", root=ROOT)


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
    row = canonical_row()
    return row["train"] + row["test"]


class GeneratorB57f299dcdb3Tests(unittest.TestCase):
    def test_all_public_pairs_are_strict_and_exact(self):
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.solve_python(grid), pair["output"])

    def test_every_profile_and_band_is_exactly_observable(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(20):
                    grid = generator.generate(
                        10_000 * profile_index + 1_000 * band_index + index,
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
                        [[generator._analyze(grid)["winner"]]],
                    )
                    self.assertNotEqual(generator.solve_python(grid), grid)

    def test_default_profile_prior_and_band_coverage(self):
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

    def test_defaults_never_replay_a_public_literal(self):
        literals = {
            tuple(tuple(row) for row in pair["input"])
            for pair in canonical_pairs()
        }
        for index in range(3_000):
            grid = generator.generate(600_000 + index, index)
            self.assertNotIn(
                tuple(tuple(row) for row in grid),
                literals,
            )

    def test_public_profiles_preserve_complete_role_morphology(self):
        for profile in generator.PUBLIC_PROFILES:
            for index in range(50):
                grid = generator.generate(
                    700_000 + index,
                    index,
                    scene_profile=profile,
                )
                self.assertEqual(
                    generator._canonical_answer_profile(grid),
                    profile,
                )

    def test_mutations_are_rejected_from_final_grid(self):
        grid = generator.generate(
            800_000,
            0,
            scene_profile="synthetic_texture",
        )
        analysis = generator._analyze(grid)
        background = analysis["background"]
        centers = generator._plus_centers(grid, background)

        broken_center = copy.deepcopy(grid)
        row, col, _ = centers[0]
        broken_center[row][col] = background
        self.assertTrue(generator.self_check(broken_center))

        no_winner = copy.deepcopy(grid)
        winner_center = next(
            center for center in centers if center[2] == analysis["winner"]
        )
        row, col, _ = winner_center
        replacement = next(
            color
            for color in generator._LEGAL_PALETTE
            if color not in {value for values in grid for value in values}
        )
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            no_winner[row + drow][col + dcol] = replacement
        self.assertTrue(generator.self_check(no_winner))

        no_texture = [
            [
                background if value == 0 else value
                for value in values
            ]
            for values in grid
        ]
        self.assertTrue(generator.self_check(no_texture))

        false_yellow = copy.deepcopy(grid)
        false_yellow[0][0] = 4
        self.assertTrue(generator.self_check(false_yellow))

        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        self.assertTrue(generator.self_check(ragged))

        invalid = copy.deepcopy(grid)
        invalid[0][0] = True
        self.assertTrue(generator.self_check(invalid))

    def test_broad_oracle_outside_training_grammar(self):
        grid = [[8 for _ in range(9)] for _ in range(9)]
        petals = (2, 2, 3)
        for (row, col), color in zip(((2, 2), (2, 6), (6, 4)), petals):
            grid[row][col] = 4
            grid[row - 1][col] = color
            grid[row + 1][col] = color
            grid[row][col - 1] = color
            grid[row][col + 1] = color
        self.assertTrue(generator.self_check(grid))
        self.assertEqual(generator.solve_python(grid), [[2]])

    def test_deterministic_fresh_and_rng_isolated(self):
        state = random.getstate()
        first = generator.generate(900_000, 17, difficulty="hard")
        second = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_both_matter(self):
        base = generator.generate(910_000, 1)
        self.assertNotEqual(base, generator.generate(910_001, 1))
        self.assertNotEqual(base, generator.generate(910_000, 2))

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 1, unknown_axis="x")
        with self.assertRaises(ValueError):
            generator.generate(1, 1, scene_profile="not_a_profile")

    def test_base_sources_match_canonical_program(self):
        program = canonical_row()["program_solution"]
        data_root = canonical_path(ROOT).parent.parent
        for relative in (
            "base/solutions/training/642d658d__b57f299dcdb3.json",
            "base/solutions/augmented/642d658d__ac47405ead15.json",
        ):
            base = json.loads((data_root / relative).read_text(encoding="utf-8"))
            self.assertEqual(base["racket_target"]["raw_code"], program)
            self.assertEqual(base["racket_target"]["target_code"], program)
        self.assertEqual(generator.RULE_HASH, "793f1a180fe5")


if __name__ == "__main__":
    unittest.main()
