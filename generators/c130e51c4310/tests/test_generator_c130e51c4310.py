from __future__ import annotations

import copy
from importlib import import_module
import hashlib
import json
import random
import unittest

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)


ROOT = find_root(__file__)
generator = import_module(
    "puzzle_generators.per_puzzle.c130e51c4310.generator"
)


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
    return load_canonical_pairs(
        generator.TASK_ID,
        root=ROOT,
        variant=0,
        labeled_only=True,
    )


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


class FixedChoice:
    def __init__(self, value):
        self.value = value

    def choice(self, values):
        if self.value not in values:
            raise AssertionError(f"{self.value!r} not in {values!r}")
        return self.value


class GeneratorC130e51c4310Tests(unittest.TestCase):
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
                        generator.solve_python(copy.deepcopy(grid)),
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

    def test_all_nonempty_edge_signatures_are_generated(self):
        expected = {
            "".join("1" if bit else "0" for bit in bits)
            for bits in generator._EDGE_OPTIONS.values()
            for bits in bits
        }
        self.assertEqual(len(expected), 15)
        observed = set()
        for profile_index, profile in enumerate(
            generator.EXTRAPOLATION_PROFILES
        ):
            for index in range(300):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    difficulty="hard",
                    scene_profile=profile,
                )
                observed.add(generator._analyze(grid)["edge_signature"])
        self.assertEqual(observed, expected)

    def test_public_profiles_preserve_roles_without_literal_replay(self):
        literals = {
            grid_key(pair["input"])
            for pair in canonical_pairs()
        }
        for profile in generator.PUBLIC_PROFILES:
            for color in generator._LEGAL_CUE_COLORS:
                for transform in generator._TRANSFORMS:
                    grid = generator._public_grid(
                        profile,
                        FixedChoice(color),
                        FixedChoice(transform),
                    )
                    self.assertEqual(
                        generator._canonical_answer_profile(grid),
                        profile,
                    )
                    self.assertNotIn(grid_key(grid), literals)

    def test_default_generation_never_replays_a_public_literal(self):
        literals = {
            grid_key(pair["input"])
            for pair in canonical_pairs()
        }
        for index in range(3_000):
            grid = generator.generate(700_000 + index, index)
            self.assertNotIn(grid_key(grid), literals)

    def test_mutations_are_rejected_from_final_grid(self):
        grid = generator.generate(
            800_000,
            0,
            difficulty="hard",
            scene_profile="adjacent_edges",
        )
        analysis = generator._analyze(grid)
        frame_cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 6
        ]

        broken_frame = copy.deepcopy(grid)
        row, col = frame_cells[0]
        broken_frame[row][col] = 7
        self.assertTrue(generator.self_check(broken_frame))

        extra_frame = copy.deepcopy(grid)
        extra_spot = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 7
            and all(
                not (
                    0 <= row + drow < len(grid)
                    and 0 <= col + dcol < len(grid[0])
                    and grid[row + drow][col + dcol] == 6
                )
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
        )
        extra_frame[extra_spot[0]][extra_spot[1]] = 6
        self.assertTrue(generator.self_check(extra_frame))

        cue_overlap = copy.deepcopy(grid)
        frame_row1, frame_col1, _, _ = analysis["frame_bbox"]
        cue_overlap[frame_row1 + 1][frame_col1 + 1] = analysis["cue_color"]
        self.assertTrue(generator.self_check(cue_overlap))

        disconnected_cue = copy.deepcopy(grid)
        cue_cells = generator._cue_info(grid)["cells_set"]
        disconnected_spot = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 7
            and all(
                (row + drow, col + dcol) not in cue_cells
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            and not (
                analysis["frame_bbox"][0]
                <= row
                <= analysis["frame_bbox"][2]
                and analysis["frame_bbox"][1]
                <= col
                <= analysis["frame_bbox"][3]
            )
        )
        disconnected_cue[disconnected_spot[0]][disconnected_spot[1]] = (
            analysis["cue_color"]
        )
        self.assertTrue(generator.self_check(disconnected_cue))

        zero = copy.deepcopy(grid)
        zero[extra_spot[0]][extra_spot[1]] = 0
        self.assertTrue(generator.self_check(zero))

        no_full_edge = [[7 for _ in range(10)] for _ in range(10)]
        for row in range(1, 4):
            for col in range(1, 4):
                if row in (1, 3) or col in (1, 3):
                    no_full_edge[row][col] = 6
        for row, col in ((6, 6), (7, 6), (7, 7), (7, 8), (8, 8)):
            no_full_edge[row][col] = 5
        self.assertIn(
            "empty_edge_signature",
            generator.self_check(no_full_edge),
        )

        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        self.assertTrue(generator.self_check(ragged))

        invalid = copy.deepcopy(grid)
        invalid[0][0] = True
        self.assertTrue(generator.self_check(invalid))

    def test_broad_oracle_outside_strict_training_grammar(self):
        grid = [[7 for _ in range(9)] for _ in range(9)]
        for row in range(1, 5):
            for col in range(1, 5):
                if row in (1, 4) or col in (1, 4):
                    grid[row][col] = 6
        grid[6][0] = 5
        grid[6][2] = 5
        before = copy.deepcopy(grid)
        output = generator.solve_python(grid)
        self.assertEqual(grid, before)
        self.assertTrue(generator.self_check(grid))
        self.assertEqual(output[6][0], 7)
        self.assertEqual(output[6][2], 7)
        self.assertEqual(output[2][2], 5)
        self.assertEqual(output[2][3], 5)
        self.assertEqual(output[3][2], 5)
        self.assertEqual(output[3][3], 5)

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
        base = [
            generator.generate(910_000, index)
            for index in range(8)
        ]
        different_seed = [
            generator.generate(910_001, index)
            for index in range(8)
        ]
        different_index = [
            generator.generate(910_000, index + 1)
            for index in range(8)
        ]
        self.assertNotEqual(base, different_seed)
        self.assertNotEqual(base, different_index)

    def test_invalid_overrides_fail_closed(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 1, unknown_axis="x")
        with self.assertRaises(ValueError):
            generator.generate(1, 1, scene_profile="not_a_profile")

    def test_rule_hash_matches_selected_canonical_program(self):
        program = canonical_row()["program_solution"]
        self.assertEqual(
            hashlib.sha256(program.encode("utf-8")).hexdigest()[:12],
            generator.RULE_HASH,
        )
        self.assertEqual(generator.RULE_HASH, "3d57c85d52e8")


if __name__ == "__main__":
    unittest.main()
