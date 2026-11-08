"""Focused semantic and contract tests for generator 78806e443729."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root

generator = importlib.import_module(
    "puzzle_generators.per_puzzle.78806e443729.generator"
)


ROOT = find_root(__file__)


def canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs() -> list[dict]:
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in load_canonical_pairs(
            generator.TASK_ID, root=ROOT, labeled_only=True
        )
    ]


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def rule_hash(source: str) -> str:
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def valid_handmade_grid() -> list[list[int]]:
    grid = [[0 for _col in range(8)] for _row in range(5)]
    grid[1][2] = 3
    grid[3][1] = 4
    grid[3][5] = 6
    return grid


class Generator78806e443729Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_rule_authorities_and_hash_pin(self):
        canonical = self.row["program_solution"]
        self.assertTrue(canonical.startswith("(rule!"))
        self.assertEqual(generator.RULE_HASH, rule_hash(canonical))
        self.assertEqual(generator.RULE_HASH, "65a855ce11f7")

    def test_all_four_canonical_pairs_and_input_purity(self):
        self.assertEqual(len(self.pairs), 4)
        for pair in self.pairs:
            source = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_right_seed_wins_overlap_and_original_seeds_are_blockers(self):
        source = [
            [0, 7, 0, 0, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 4, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 3, 0, 0],
        ]
        expected = [
            [7, 7, 2, 2, 2, 2, 2, 2],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [4, 4, 4, 4, 4, 4, 4, 4],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [3, 3, 3, 3, 3, 3, 3, 3],
        ]
        self.assertEqual(generator.self_check(source), [])
        self.assertEqual(generator.rule_mirror(source), expected)

    def test_python_mirror_matches_racket_on_generated_inputs(self):
        program = self.row["program_solution"]
        with RacketBridge(timeout=20) as bridge:
            apply = lambda grid: bridge.eval_text(
                f"({wrap_rule(program)} {_literal(grid)})"
            )
            first = generator.generate(701, 11, difficulty="easy")
            second = generator.generate(907, 17, difficulty="hard")
            racket_first = apply(first)
            apply(second)
            racket_first_again = apply(first)
            self.assertEqual(racket_first, racket_first_again)
            self.assertEqual(racket_first, generator.rule_mirror(first))
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for offset in range(3):
                    grid = generator.generate(
                        1200 + band_index * 100 + offset,
                        31 + offset,
                        difficulty=band,
                    )
                    self.assertEqual(
                        apply(grid),
                        generator.rule_mirror(grid),
                    )

    def test_every_axis_override_is_exact_at_boundaries(self):
        for band in ("easy", "medium", "hard"):
            for height in (5, 14):
                for width in (8, 18):
                    for row_count in (2, 5):
                        for profile in generator.BRANCH_PROFILES:
                            grid = generator.generate(
                                401,
                                503,
                                difficulty=band,
                                grid_h=height,
                                grid_w=width,
                                row_count=row_count,
                                branch_profile=profile,
                            )
                            self.assertEqual((len(grid), len(grid[0])), (height, width))
                            self.assertEqual(
                                generator.observe_overrides(grid),
                                {
                                    "row_count": row_count,
                                    "branch_profile": profile,
                                },
                            )
                            self.assertEqual(generator.self_check(grid), [])

    def test_default_generation_covers_all_semantic_branches(self):
        for band in ("easy", "medium", "hard"):
            profiles = set()
            row_counts = set()
            inputs = set()
            outputs = set()
            for seed in range(120):
                grid = generator.generate(seed, seed * 19 + 7, difficulty=band)
                observed = generator.observe_overrides(grid)
                profiles.add(observed["branch_profile"])
                row_counts.add(observed["row_count"])
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, generator.rule_mirror(grid))))
                self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(profiles, set(generator.BRANCH_PROFILES))
            self.assertGreaterEqual(len(row_counts), 2)
            self.assertGreater(len(inputs), 100)
            self.assertGreater(len(outputs), 100)

    def test_self_check_rejects_targeted_impostors(self):
        valid = valid_handmade_grid()
        self.assertEqual(generator.self_check(valid), [])

        blank = [[0 for _col in range(8)] for _row in range(5)]

        one_active_row = copy.deepcopy(valid)
        one_active_row[3] = [0] * 8

        edge_seed = copy.deepcopy(valid)
        edge_seed[1][2] = 0
        edge_seed[1][0] = 3

        adjacent_pair = copy.deepcopy(valid)
        adjacent_pair[1][3] = 5

        repeated_pair_color = copy.deepcopy(valid)
        repeated_pair_color[1][5] = 3

        three_seeds = copy.deepcopy(valid)
        three_seeds[1][4] = 5
        three_seeds[1][6] = 7

        vertical_same_color = copy.deepcopy(valid)
        vertical_same_color[2][2] = 3

        ragged = copy.deepcopy(valid)
        ragged[0].pop()

        invalid_color = copy.deepcopy(valid)
        invalid_color[0][0] = 10

        boolean_cell = copy.deepcopy(valid)
        boolean_cell[0][0] = True

        for mutation in (
            blank,
            one_active_row,
            edge_seed,
            adjacent_pair,
            repeated_pair_color,
            three_seeds,
            vertical_same_color,
            ragged,
            invalid_color,
            boolean_cell,
        ):
            self.assertTrue(generator.self_check(mutation), mutation)
            with self.assertRaises(ValueError):
                generator.observe_overrides(mutation)

    def test_determinism_freshness_global_rng_and_loud_rejection(self):
        random.seed(20260723)
        state = random.getstate()
        first = generator.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

        for kwargs in (
            {"texture": "warm"},
            {"branch_profile": "unknown"},
            {"grid_h": 4},
            {"grid_w": 19},
            {"row_count": 1},
        ):
            with self.assertRaises(ValueError):
                generator.generate(1, 2, **kwargs)


if __name__ == "__main__":
    unittest.main()
