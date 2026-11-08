"""Focused semantic tests for generator 297e46df4407."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

generator = importlib.import_module(
    "puzzle_generators.per_puzzle.297e46df4407.generator"
)


ROOT = Path(__file__).resolve().parents[1]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + (
        test if isinstance(test, list) else [test]
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for delta_row, delta_col in CARDINAL:
                    neighbor = (
                        cell[0] + delta_row,
                        cell[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return result


def independent_rule(grid):
    output = [row[:] for row in grid]
    source = components(grid, 1)
    red = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    green = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    if not source or not red or not green:
        return output
    delta = (
        green[0][0] - red[0][0],
        green[0][1] - red[0][1],
    )
    for row, col in source[0]:
        target = row + delta[0], col + delta[1]
        if (
            0 <= target[0] < len(grid)
            and 0 <= target[1] < len(grid[0])
        ):
            output[target[0]][target[1]] = 8
    return output


def translated_targets(grid):
    source = components(grid, 1)[0]
    red = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )
    green = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    )
    delta = green[0] - red[0], green[1] - red[1]
    return {
        (row + delta[0], col + delta[1])
        for row, col in source
    }


def transform_grid(grid, transform):
    transformed = [row[:] for row in grid]
    if transform >= 4:
        transformed = [
            list(reversed(row)) for row in transformed
        ]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


class Generator297e46df4407Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_collisions_and_rule(self):
        self.assertEqual(len(self.pairs), 5)
        collisions = []
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            snapshot = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, snapshot)
            targets = translated_targets(grid)
            self.assertEqual(len(targets), 4)
            self.assertTrue(all(
                0 <= row < len(grid)
                and 0 <= col < len(grid[0])
                for row, col in targets
            ))
            collisions.append(sorted(
                grid[row][col]
                for row, col in targets
                if grid[row][col] != 0
            ))
        self.assertEqual(collisions, [[], [], [], [5], [2]])

    def test_global_d4_metamorphism_for_every_profile(self):
        for index, pair in enumerate(self.pairs):
            for transform in range(8):
                transformed_input = transform_grid(
                    pair["input"], transform
                )
                transformed_output = transform_grid(
                    pair["output"], transform
                )
                self.assertEqual(
                    independent_rule(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.canonical_profile_index(
                        transformed_input
                    ),
                    index,
                )

    def test_every_exact_profile_axis_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                seed = 10_000 + 100 * profile_index + len(band)
                grid = generator.generate(
                    seed,
                    seed * 19 + 3,
                    difficulty=band,
                    scene_profile=profile,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"scene_profile": profile},
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_distribution_is_complete_stable_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = set()
                shapes = set()
                pairs = set()
                for offset in range(120):
                    seed = start + band_index * 10_000 + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.rule_mirror(grid), output
                    )
                    profiles.add(
                        generator.observe_overrides(grid)[
                            "scene_profile"
                        ]
                    )
                    shapes.add((len(grid), len(grid[0])))
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                self.assertEqual(
                    profiles, set(generator.SCENE_PROFILES)
                )
                self.assertGreaterEqual(len(shapes), 4)
                self.assertGreaterEqual(len(pairs), 119)

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = self.pairs[0]["input"]
        broken_blob = [row[:] for row in original]
        broken_blob[1][3] = 0
        extra_blob = [row[:] for row in original]
        extra_blob[11][10] = 1
        missing_red = [row[:] for row in original]
        missing_red[1][4] = 0
        missing_green = [row[:] for row in original]
        missing_green[2][9] = 0
        prepainted = [row[:] for row in original]
        prepainted[11][10] = 8
        broken_decoy_role = [row[:] for row in original]
        broken_decoy_role[7][7] = 0
        invalid_color = [row[:] for row in original]
        invalid_color[11][10] = 10
        for mutation in (
            broken_blob,
            extra_blob,
            missing_red,
            missing_green,
            prepainted,
            broken_decoy_role,
            invalid_color,
            [],
            original[:-1],
            original + [[0] * len(original[0])],
            [row[:-1] for row in original],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_lawful_unpublished_recombination_is_calibrated_out(self):
        candidate = [row[:] for row in self.pairs[0]["input"]]
        candidate[11][10] = 4
        self.assertEqual(
            generator.self_check(candidate),
            [
                "returned scene must match a complete published "
                "port profile"
            ],
        )
        self.assertEqual(
            generator.rule_mirror(candidate),
            independent_rule(candidate),
        )
        self.assertEqual(
            generator.rule_mirror(candidate)[11][10],
            4,
        )

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        base = json.loads((
            ROOT
            / "data/base/solutions/banks/0d41ded5f4cd/"
            "M85__297e46df4407.json"
        ).read_text())["racket_target"]
        self.assertEqual(base["raw_code"], source)
        self.assertEqual(base["target_code"], source)
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        state = random.getstate()
        first = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        snapshot = [row[:] for row in first]
        generator.generate(91, 97, difficulty="easy")
        self.assertEqual(first, snapshot)
        again = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(
            old_row is not new_row
            for old_row, new_row in zip(first, again)
        ))
        first[0][0] = 1 if first[0][0] != 1 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
