"""Focused semantic and contract tests for generator d01b33f4a589."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.d01b33f4a589 import generator
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs as portable_canonical_pairs, find_root


ROOT = find_root(__file__)
BASE_FILE = (
    ROOT
    / "shared/data/base/solutions/banks/26462ff56908/"
    "M84__d01b33f4a589.json"
)


def decode_grid(value):
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [[int(cell) for cell in row] for row in value]


def canonical_program():
    record = Catalog(ROOT).get(generator.TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    if len(programs) != 1:
        raise AssertionError("expected one selected canonical program")
    return programs.pop()


def canonical_pairs():
    return portable_canonical_pairs(generator.TASK_ID, root=ROOT)


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def flip_ud(grid):
    return [row[:] for row in reversed(grid)]


def transform_code(grid, code):
    if code == 1:
        return rotate_cw(grid)
    if code == 2:
        return rotate_180(grid)
    if code == 3:
        return flip_lr(grid)
    return flip_ud(grid)


def reference_rule(grid):
    height = len(grid)
    width = len(grid[0])
    commands = (
        grid[0][0],
        grid[0][width - 1],
        grid[height - 1][0],
        grid[height - 1][width - 1],
    )
    ignored = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in ignored
    ]
    if not cells:
        raise ValueError("missing motif")
    row0 = min(row for row, _col, _value in cells)
    row1 = max(row for row, _col, _value in cells)
    col0 = min(col for _row, col, _value in cells)
    col1 = max(col for _row, col, _value in cells)
    motif = [
        [0 for _col in range(col0, col1 + 1)]
        for _row in range(row0, row1 + 1)
    ]
    for row, col, value in cells:
        motif[row - row0][col - col0] = value
    variants = [
        transform_code(motif, code)
        for code in commands
    ]
    cell_height = max(len(variant) for variant in variants)
    cell_width = max(len(variant[0]) for variant in variants)
    output = [
        [0 for _col in range(2 * cell_width)]
        for _row in range(2 * cell_height)
    ]
    for index, variant in enumerate(variants):
        top = (index // 2) * cell_height
        left = (index % 2) * cell_width
        for row, values in enumerate(variant):
            for col, value in enumerate(values):
                if value:
                    output[top + row][left + col] = value
    return output


def broad_case():
    grid = [[0 for _col in range(11)] for _row in range(8)]
    grid[0][0] = 1
    grid[0][10] = 4
    grid[7][0] = 2
    grid[7][10] = 9
    grid[2][3] = 5
    grid[2][4] = 6
    grid[3][3] = 7
    grid[5][6] = 8
    return grid


class GeneratorD01b33f4a589Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 5)
        observed_profiles = []
        for index, pair in enumerate(self.pairs):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.canonical_profile_index(source),
                index,
            )
            self.assertEqual(
                generator.exact_public_profile_index(source),
                index,
            )
            self.assertEqual(reference_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
            observed_profiles.append(
                generator.observe_overrides(source)["scene_profile"]
            )
        self.assertEqual(
            tuple(observed_profiles),
            generator.SCENE_PROFILES,
        )
        self.assertEqual(
            generator.observe_overrides(self.pairs[2]["input"])[
                "command_profile"
            ],
            "repeat_two",
        )
        self.assertEqual(
            self.pairs[0]["input"][3][3],
            2,
            "a motif may reuse a corner-command color",
        )

    def test_every_exact_axis_combination(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for command_index, command in enumerate(
                    generator.COMMAND_PROFILES
                ):
                    seed = (
                        10_000
                        + 100 * profile_index
                        + 10 * command_index
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        command_profile=command,
                    )
                    expected = {
                        "scene_profile": profile,
                        "command_profile": command,
                    }
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        reference_rule(grid),
                    )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, command_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        expected_axes = {
            (profile, command)
            for profile in generator.SCENE_PROFILES
            for command in generator.COMMAND_PROFILES
        }
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                axes = Counter()
                inputs = set()
                outputs = set()
                exact_public = 0
                for offset in range(800):
                    seed = start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    observed = generator.observe_overrides(grid)
                    output = reference_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    axes[(
                        observed["scene_profile"],
                        observed["command_profile"],
                    )] += 1
                    exact_public += (
                        generator.exact_public_profile_index(grid)
                        is not None
                    )
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(set(axes), expected_axes)
                self.assertGreaterEqual(len(inputs), 650)
                self.assertGreaterEqual(len(outputs), 550)
                self.assertGreaterEqual(exact_public, 20)
                self.assertLessEqual(exact_public, 70)

    def test_public_prior_and_difficulty_weighting(self):
        profiles_by_band = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            commands = Counter()
            exact_public = 0
            for offset in range(2_000):
                seed = 30_000 + 3_000 * band_index + offset
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                profiles[observed["scene_profile"]] += 1
                commands[observed["command_profile"]] += 1
                exact_public += (
                    generator.exact_public_profile_index(grid) is not None
                )
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertEqual(set(commands), set(generator.COMMAND_PROFILES))
            self.assertGreaterEqual(commands["permutation"], 1_450)
            self.assertLessEqual(commands["permutation"], 1_750)
            self.assertGreaterEqual(exact_public, 60)
            self.assertLessEqual(exact_public, 150)
            profiles_by_band[band] = profiles
        self.assertGreater(
            profiles_by_band["easy"]["l3_9x9"],
            profiles_by_band["easy"]["v5_9x9"],
        )
        self.assertGreater(
            profiles_by_band["hard"]["v5_9x9"],
            profiles_by_band["hard"]["l3_9x9"],
        )

    def test_structural_and_semantic_mutations_are_rejected(self):
        source = [row[:] for row in self.pairs[4]["input"]]

        invalid_command = [row[:] for row in source]
        invalid_command[0][0] = 0

        wrong_multiset = [row[:] for row in source]
        wrong_multiset[0][0] = 1
        wrong_multiset[0][-1] = 1
        wrong_multiset[-1][0] = 2
        wrong_multiset[-1][-1] = 3

        multicolor = [row[:] for row in source]
        multicolor[3][3] = 8

        disconnected = [row[:] for row in source]
        disconnected[2][6] = 7

        border_cell = [row[:] for row in source]
        border_cell[1][0] = 7

        wrong_shape = [row[:] for row in source]
        wrong_shape[4][4] = 7

        wrong_canvas = [
            row[:] + [0]
            for row in source
        ]

        for mutation in (
            invalid_command,
            wrong_multiset,
            multicolor,
            disconnected,
            border_cell,
            wrong_shape,
            wrong_canvas,
        ):
            self.assertNotEqual(generator.self_check(mutation), [])
            self.assertEqual(generator.observe_overrides(mutation), {})

        malformed = (
            [],
            [[]],
            [[1], [1, 2]],
            [[True]],
            [[10]],
            [[0] * 31],
            [[7] * 7 for _row in range(7)],
        )
        for grid in malformed:
            self.assertNotEqual(generator.self_check(grid), [])

    def test_rule_mirror_is_broad_and_input_pure(self):
        grid = broad_case()
        snapshot = [row[:] for row in grid]
        expected = reference_rule(grid)
        self.assertNotEqual(expected, grid)
        self.assertEqual(generator.rule_mirror(grid), expected)
        self.assertEqual(grid, snapshot)
        self.assertNotEqual(generator.self_check(grid), [])
        with self.assertRaises(ValueError):
            generator.rule_mirror([[1, 0, 2], [0, 0, 0], [3, 0, 4]])

        corner_span = [[0 for _col in range(7)] for _row in range(6)]
        corner_span[0][0], corner_span[0][6] = 1, 2
        corner_span[5][0], corner_span[5][6] = 3, 4
        corner_span[0][1] = 5
        corner_span[5][5] = 6
        self.assertEqual(
            generator.rule_mirror(corner_span),
            reference_rule(corner_span),
        )

    def test_corner_reading_order_controls_output_quadrants(self):
        motif = [[5, 5, 0], [0, 5, 0], [0, 5, 5]]
        for commands in (
            (1, 2, 3, 4),
            (2, 2, 3, 1),
            (4, 3, 2, 1),
        ):
            grid = [[0 for _col in range(9)] for _row in range(9)]
            grid[0][0], grid[0][8], grid[8][0], grid[8][8] = commands
            for row, values in enumerate(motif):
                for col, value in enumerate(values):
                    grid[3 + row][3 + col] = value
            self.assertEqual(
                generator.rule_mirror(grid),
                reference_rule(grid),
            )

    def test_motif_translation_and_color_substitution_metamorphisms(self):
        source = [row[:] for row in self.pairs[0]["input"]]
        expected = generator.rule_mirror(source)

        translated = [row[:] for row in source]
        motif_cells = ((3, 3), (4, 3), (5, 3), (5, 4))
        for row, col in motif_cells:
            translated[row][col] = 0
        for row, col in motif_cells:
            translated[row][col + 1] = 2
        self.assertEqual(generator.self_check(translated), [])
        self.assertEqual(generator.rule_mirror(translated), expected)

        recolored = [row[:] for row in source]
        for row, col in motif_cells:
            recolored[row][col] = 9
        recolored_expected = [
            [9 if value == 2 else value for value in row]
            for row in expected
        ]
        self.assertEqual(generator.self_check(recolored), [])
        self.assertEqual(
            generator.rule_mirror(recolored),
            recolored_expected,
        )

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(1729)
        state = random.getstate()
        first = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(second, third)

    def test_source_sync_and_rule_hash(self):
        canonical = canonical_program()
        expected = normalized_rule_hash(canonical)
        self.assertEqual(generator.RULE_HASH, expected[:12])
        base = json.loads(BASE_FILE.read_text())
        racket = base["racket_target"]
        self.assertEqual(
            normalized_rule_hash(racket["raw_code"]),
            expected,
        )
        self.assertEqual(
            normalized_rule_hash(racket["target_code"]),
            expected,
        )
        self.assertEqual(racket["raw_code"], racket["target_code"])


if __name__ == "__main__":
    unittest.main()
