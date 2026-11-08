from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.base import set_ctx_observer

TASK = "196a7ec58bbc"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "data/base/solutions/training/46442a0e__196a7ec58bbc.json"


def canonical_row() -> dict:
    matches = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row for {TASK}, got {len(matches)}")
    return matches[0]


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    original, clockwise, half_turn, counterclockwise = MOD._rotations(grid)
    top = [left + right for left, right in zip(original, clockwise)]
    bottom = [left + right for left, right in zip(counterclockwise, half_turn)]
    return top + bottom


class RotationKaleidoscopeGeneratorTests(unittest.TestCase):
    def test_every_canonical_input_is_accepted_and_matches_quadrants(self):
        row = canonical_row()
        pairs = row["train"] + row["test"]
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            grid = pair["input"]
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(expected_output(grid), pair["output"])

    def test_default_distribution_is_exact_and_rotation_distinct(self):
        medium_sizes = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = MOD.generate(seed, seed * 31 + 7, difficulty=band)
                errors = MOD.self_check(grid, difficulty=band)
                self.assertEqual(errors, [], (band, seed, grid, errors))
                side = len(grid)
                palette_size = len({value for row in grid for value in row})
                self.assertEqual(MOD._rotation_orbit_size(grid), 4)
                self.assertEqual(
                    MOD.observe_overrides(grid),
                    {"grid_n": side, "palette_size": palette_size},
                )
                if side == 2:
                    self.assertIn(palette_size, (3, 4))
                else:
                    self.assertIn(palette_size, (2, 3, 4))
                    counts = {
                        color: sum(value == color for row in grid for value in row)
                        for color in {value for row in grid for value in row}
                    }
                    self.assertGreaterEqual(min(counts.values()), 2)
                if band == "easy":
                    self.assertEqual(side, 2)
                elif band == "hard":
                    self.assertEqual(side, 3)
                else:
                    medium_sizes.add(side)
        self.assertEqual(medium_sizes, {2, 3})

    def test_exact_overrides_and_internal_texture_priors(self):
        for side, palette_size in ((2, 3), (2, 4), (3, 2), (3, 3), (3, 4)):
            for band in (None, "easy", "medium", "hard"):
                for seed in range(30):
                    grid = MOD.generate(
                        10_000 + seed,
                        seed * 17,
                        difficulty=band,
                        grid_n=side,
                        palette_size=palette_size,
                    )
                    self.assertEqual(len(grid), side)
                    self.assertEqual(
                        len({value for row in grid for value in row}), palette_size
                    )
                    self.assertEqual(MOD._rotation_orbit_size(grid), 4)
                    self.assertEqual(
                        MOD.observe_overrides(grid),
                        {"grid_n": side, "palette_size": palette_size},
                    )

        seen_textures = set()
        for seed in range(500):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = MOD.generate(20_000 + seed, seed, difficulty="hard")
            finally:
                set_ctx_observer(None)
            self.assertEqual(MOD.self_check(grid), [], (seed, grid))
            self.assertEqual(MOD._rotation_orbit_size(grid), 4)
            self.assertTrue(captured)
            seen_textures.add(captured[-1]._drawn["texture"])
        self.assertEqual(seen_textures, set(MOD._TEXTURE_PRIORS))

        for seed in range(50):
            grid = MOD.generate(30_000 + seed, seed, palette_size=2)
            self.assertEqual(len(grid), 3)
            self.assertEqual(len({value for row in grid for value in row}), 2)

    def test_incompatible_and_invalid_overrides_fail_loudly(self):
        invalid = (
            {"grid_n": 1},
            {"grid_n": 4},
            {"grid_n": True},
            {"palette_size": 1},
            {"palette_size": 5},
            {"palette_size": False},
            {"texture": "not-a-public-axis"},
            {"unknown_axis": 3},
            {"grid_n": 2, "palette_size": 2},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = {
            "empty": [],
            "ragged": [[1, 2], [3]],
            "non_square": [[1, 2, 3], [4, 5, 6]],
            "oversized": [[(r + c) % 3 for c in range(4)] for r in range(4)],
            "monochrome": [[1, 1], [1, 1]],
            "two_color_row_stripe": [[1, 1], [2, 2]],
            "center_singleton": [[1, 1, 1], [1, 2, 1], [1, 1, 1]],
            "rotation_symmetric_checker": [[1, 2, 1], [2, 1, 2], [1, 2, 1]],
            "invalid_color": [[1, 2], [3, 10]],
            "boolean_color": [[1, 2], [3, True]],
        }
        for name, grid in cases.items():
            with self.subTest(name=name):
                self.assertTrue(MOD.self_check(grid), (name, grid))

        canonical_exception = [[8, 6], [6, 8]]
        self.assertEqual(MOD.self_check(canonical_exception), [])
        self.assertEqual(MOD._rotation_orbit_size(canonical_exception), 2)

    def test_determinism_freshness_and_global_random_state(self):
        for band in (None, "easy", "medium", "hard"):
            random.seed(47)
            state = random.getstate()
            first = MOD.generate(17, 23, difficulty=band)
            self.assertEqual(random.getstate(), state)
            second = MOD.generate(17, 23, difficulty=band)
            self.assertEqual(first, second)
            self.assertIsNot(first, second)
            self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_task_local_rule_sources_are_synchronized(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(digest, "24bc23963715")
        self.assertEqual(MOD.RULE_HASH, digest)

        from solvers.grounded_rules import GROUNDED_RULES

        self.assertEqual(GROUNDED_RULES[TASK], source)
        base = json.loads(BASE_PATH.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(
            base["racket_target"]["canonicalization_status"],
            "synchronized_to_canonical_program_solution",
        )


if __name__ == "__main__":
    unittest.main()
