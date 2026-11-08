"""Focused semantic and contract tests for generator bfb4c6fb3c1a."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.bfb4c6fb3c1a import generator
from scripts.rule_smoke import load_rules


ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/8edfaf6db623/"
    "M105__bfb4c6fb3c1a.json"
)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        list(test) if isinstance(test, list) else [test]
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(
        sorted((row - row0, col - col0) for row, col in cells)
    )


def rotate90(cells):
    norm = normalize(cells)
    height = max(row for row, _col in norm) + 1
    return normalize(
        (col, height - 1 - row)
        for row, col in norm
    )


def reflect_rows(cells):
    norm = normalize(cells)
    height = max(row for row, _col in norm) + 1
    return normalize(
        (height - 1 - row, col)
        for row, col in norm
    )


def dihedral_key(cells):
    forms = []
    current = normalize(cells)
    for _index in range(4):
        forms.append(current)
        forms.append(reflect_rows(current))
        current = rotate90(current)
    return min(forms)


def components(grid, color):
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for delta_row, delta_col in (
                (-1, 0),
                (0, -1),
                (0, 1),
                (1, 0),
            ):
                candidate = (row + delta_row, col + delta_col)
                if candidate in remaining:
                    remaining.remove(candidate)
                    queue.append(candidate)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: cells[0])


def reference_rule(grid):
    references = components(grid, 1)
    if not references:
        raise ValueError("missing blue reference")
    reference = sorted(
        references,
        key=lambda cells: (-len(cells), cells[0]),
    )[0]
    reference_key = dihedral_key(reference)
    output = [row[:] for row in grid]
    for candidate in components(grid, 2):
        if dihedral_key(candidate) == reference_key:
            for row, col in candidate:
                output[row][col] = 8
    return output


def transform_grid(grid, transform):
    if transform == "identity":
        return [row[:] for row in grid]
    if transform == "horizontal":
        return [list(reversed(row)) for row in grid]
    if transform == "vertical":
        return [row[:] for row in reversed(grid)]
    if transform == "rotated_180":
        return [
            list(reversed(row))
            for row in reversed(grid)
        ]
    raise AssertionError(transform)


def broad_case():
    grid = [[0 for _col in range(14)] for _row in range(13)]

    def paint(shape, row0, col0, color):
        for row, col in shape:
            grid[row0 + row][col0 + col] = color

    reference = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))
    rotated = rotate90(reference)
    reflected = reflect_rows(reference)
    decoy = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
    paint(reference, 2, 2, 1)
    paint(rotated, 2, 9, 2)
    paint(reflected, 8, 2, 2)
    paint(decoy, 8, 9, 2)
    grid[11][13] = 1
    grid[6][6] = 4
    return grid


class GeneratorBfb4c6fb3c1aTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 5)
        observed_profiles = []
        for index, pair in enumerate(self.pairs):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            observed = generator.observe_overrides(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(observed["scene_transform"], "identity")
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
            observed_profiles.append(observed["scene_profile"])
        self.assertEqual(
            tuple(observed_profiles),
            generator.SCENE_PROFILES,
        )

    def test_every_exact_axis_combination(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for transform_index, transform in enumerate(
                    generator.SCENE_TRANSFORMS
                ):
                    seed = (
                        10_000
                        + 100 * profile_index
                        + 10 * transform_index
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        scene_transform=transform,
                    )
                    expected = {
                        "scene_profile": profile,
                        "scene_transform": transform,
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
                    if transform != "identity":
                        self.assertIsNone(
                            generator.exact_public_profile_index(grid)
                        )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_transform="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        expected_axes = {
            (profile, transform)
            for profile in generator.SCENE_PROFILES
            for transform in generator.SCENE_TRANSFORMS
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
                        observed["scene_transform"],
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
                self.assertGreaterEqual(len(inputs), 600)
                self.assertGreaterEqual(len(outputs), 600)
                self.assertGreaterEqual(exact_public, 20)
                self.assertLessEqual(exact_public, 70)

    def test_public_prior_and_difficulty_profile_weighting(self):
        profiles_by_band = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            transforms = Counter()
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
                transforms[observed["scene_transform"]] += 1
                exact_public += (
                    generator.exact_public_profile_index(grid) is not None
                )
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertEqual(
                set(transforms),
                set(generator.SCENE_TRANSFORMS),
            )
            self.assertGreaterEqual(transforms["identity"], 680)
            self.assertLessEqual(transforms["identity"], 920)
            self.assertGreaterEqual(exact_public, 60)
            self.assertLessEqual(exact_public, 150)
            profiles_by_band[band] = profiles
        self.assertGreater(
            profiles_by_band["easy"]["l3_9x10"],
            profiles_by_band["easy"]["stair5_9x12"],
        )
        self.assertGreater(
            profiles_by_band["hard"]["stair5_9x12"],
            profiles_by_band["hard"]["l3_9x10"],
        )

    def test_structural_and_semantic_mutations_are_rejected(self):
        first = [row[:] for row in self.pairs[0]["input"]]
        second = [row[:] for row in self.pairs[1]["input"]]

        broken_match = [row[:] for row in first]
        broken_match[1][6] = 0

        altered_decoy = [row[:] for row in first]
        altered_decoy[6][8] = 2

        no_decoration = [row[:] for row in first]
        no_decoration[8][9] = 0

        internal_decoration = [row[:] for row in first]
        internal_decoration[8][9] = 0
        internal_decoration[4][4] = 7

        three_matches = [row[:] for row in first]
        for row, col in ((5, 6), (5, 7), (5, 8), (6, 7)):
            three_matches[row][col] = 0
        for row, col in ((5, 6), (6, 6), (6, 7)):
            three_matches[row][col] = 2

        cyan_input = [row[:] for row in first]
        cyan_input[4][4] = 8

        cross_profile_decoy = [row[:] for row in second]
        for row, col in (
            (5, 8),
            (6, 8),
            (6, 9),
            (7, 9),
            (7, 10),
        ):
            cross_profile_decoy[row][col] = 0
        for row, col in ((5, 8), (5, 9), (5, 10), (6, 9)):
            cross_profile_decoy[row][col] = 2

        for mutation in (
            broken_match,
            altered_decoy,
            no_decoration,
            internal_decoration,
            three_matches,
            cyan_input,
            cross_profile_decoy,
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
            [[2] * 2 for _row in range(2)],
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

    def test_whole_scene_transform_commutes(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            source = generator.generate(
                70_000 + profile_index,
                71_000 + profile_index,
                scene_profile=profile,
                scene_transform="identity",
            )
            expected = generator.rule_mirror(source)
            for transform in generator.SCENE_TRANSFORMS:
                transformed_input = transform_grid(source, transform)
                transformed_output = transform_grid(expected, transform)
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.observe_overrides(transformed_input),
                    {
                        "scene_profile": profile,
                        "scene_transform": transform,
                    },
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
        canonical = canonical_row()["program_solution"]
        live = load_rules([generator.TASK_ID])[generator.TASK_ID]
        expected = normalized_rule_hash(canonical)
        self.assertEqual(normalized_rule_hash(live), expected)
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
