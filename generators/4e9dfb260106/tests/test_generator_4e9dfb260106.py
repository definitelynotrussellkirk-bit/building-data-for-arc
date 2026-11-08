"""Focused semantic and contract tests for generator 4e9dfb260106."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from scripts.mine_primitive_usage import summarize_task


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.4e9dfb260106.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/343f662c728a/"
    "M111__4e9dfb260106.json"
)
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


def independent_components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in seen or grid[start_row][start_col] != color:
                continue
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in CARDINAL:
                    neighbor = (row + delta_row, col + delta_col)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return tuple(result)


def independent_rule(grid):
    red_count = sum(
        value == 2 for row in grid for value in row
    )
    target = next(
        (
            component
            for component in independent_components(grid, 1)
            if len(component) == red_count
        ),
        None,
    )
    if target is None:
        return [[0]]
    top = min(row for row, _col in target)
    bottom = max(row for row, _col in target)
    left = min(col for _row, col in target)
    right = max(col for _row, col in target)
    cells = set(target)
    return [
        [
            1 if (row, col) in cells else 0
            for col in range(left, right + 1)
        ]
        for row in range(top, bottom + 1)
    ]


class Generator4e9dfb260106Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 5)
        expected_profiles = (
            "canonical_l3",
            "canonical_square4",
            "canonical_l5",
            "canonical_l3",
            "canonical_zigzag4",
        )
        for pair, profile in zip(self.pairs, expected_profiles):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.observe_overrides(source),
                {"scene_profile": profile},
            )
            self.assertEqual(
                generator.canonical_profile_index(source),
                generator.SCENE_PROFILES.index(profile),
            )
            self.assertEqual(independent_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_exact_profile_in_every_band_and_fallback(self):
        minimum_dimensions = {
            "easy": ((8, 9), (14, 14)),
            "medium": ((9, 10), (16, 16)),
            "hard": ((11, 12), (18, 18)),
        }
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                seed = 10_000 + 100 * profile_index + len(band)
                grid = generator.generate(
                    seed,
                    seed * 17 + 3,
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

                dimensions = minimum_dimensions[band][
                    0 if profile.startswith("canonical_") else 1
                ]
                fallback = generator._fallback_scene(
                    profile,
                    *dimensions,
                    9,
                )
                self.assertEqual(generator.self_check(fallback), [])
                self.assertEqual(
                    generator.observe_overrides(fallback),
                    {"scene_profile": profile},
                )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                inputs = set()
                outputs = set()
                for offset in range(400):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    profiles[observed["scene_profile"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(
                    set(profiles), set(generator.SCENE_PROFILES)
                )
                self.assertGreaterEqual(len(inputs), 395)
                self.assertGreaterEqual(len(outputs), 300)

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = self.pairs[0]["input"]
        no_decoy = [row[:] for row in original]
        no_decoy[-1][-1] = 0

        extra_decoy = [row[:] for row in original]
        extra_decoy[-1][0] = 8

        interior_decoy = [row[:] for row in original]
        interior_decoy[-1][-1] = 0
        interior_decoy[6][5] = 6

        disconnected_marker = [row[:] for row in original]
        disconnected_marker[1][8] = 0
        disconnected_marker[7][0] = 2

        duplicate_target_size = [row[:] for row in original]
        duplicate_target_size[4][1] = 0

        touching_groups = [row[:] for row in original]
        touching_groups[3][2] = 1

        for mutation in (
            no_decoy,
            extra_decoy,
            interior_decoy,
            disconnected_marker,
            duplicate_target_size,
            touching_groups,
            [],
            [[0] * 31],
            [[False, 2], [1, 3]],
            [[10, 2], [1, 3]],
            [row[:-1] for row in original],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_recombination_is_rejected_while_rule_mirror_stays_broad(self):
        zigzag_with_three_marker_cells = [
            row[:] for row in self.pairs[-1]["input"]
        ]
        zigzag_with_three_marker_cells[9][3] = 0
        self.assertTrue(
            generator.self_check(zigzag_with_three_marker_cells)
        )
        self.assertEqual(
            generator.rule_mirror(zigzag_with_three_marker_cells),
            independent_rule(zigzag_with_three_marker_cells),
        )

        no_match = [
            [2, 2, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 0],
        ]
        snapshot = [row[:] for row in no_match]
        self.assertEqual(generator.rule_mirror(no_match), [[0]])
        self.assertEqual(no_match, snapshot)
        self.assertTrue(generator.self_check(no_match))

        tied_match = [
            [2, 2, 2, 0, 1, 1, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [1, 1, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0],
        ]
        self.assertEqual(
            generator.rule_mirror(tied_match),
            [[1, 1], [1, 0]],
        )
        self.assertTrue(generator.self_check(tied_match))

    def test_source_sync_rule_hash_and_primitive_metadata(self):
        source = self.row["program_solution"]
        base = json.loads(BASE_FILE.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )
        mined = summarize_task(generator.TASK_ID, source)
        self.assertEqual(
            base["primitive_metadata"]["primitive_chain"],
            mined["primitive_chain"],
        )
        self.assertEqual(
            base["primitive_metadata"]["family_chain"],
            mined["family_chain"],
        )

    def test_determinism_freshness_and_global_rng_purity(self):
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
