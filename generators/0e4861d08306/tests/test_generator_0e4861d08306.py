"""Focused semantic regressions for generator 0e4861d08306."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "0e4861d08306"
BASE_PATH = (
    ROOT
    / "data"
    / "base"
    / "solutions"
    / "custom"
    / "36f9e4ca__0e4861d08306.json"
)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def canonical_row() -> dict:
    rows = [
        json.loads(line)
        for line in (ROOT / "data" / "canonical" / "puzzles.jsonl")
        .read_text()
        .splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row, found {len(rows)}")
    return rows[0]


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Literal reading-order BFS transcription, independent of module helpers."""
    height, width = len(grid), len(grid[0])
    start = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    )
    reached = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for row_delta, col_delta in CARDINAL:
            candidate = row + row_delta, col + col_delta
            if (
                0 <= candidate[0] < height
                and 0 <= candidate[1] < width
                and candidate not in reached
                and grid[candidate[0]][candidate[1]] in (1, 2)
            ):
                reached.add(candidate)
                stack.append(candidate)
    output = copy.deepcopy(grid)
    for row, col in reached:
        if output[row][col] == 1:
            output[row][col] = 3
    return output


class Generator0e4861d08306Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)

    def test_rule_authorities_are_content_identical_and_pinned(self) -> None:
        canonical = canonical_row()["program_solution"]
        base = json.loads(BASE_PATH.read_text())["racket_target"]
        expected = normalized_rule_hash(canonical)
        self.assertEqual(expected[:12], "08735d91bff4")
        self.assertEqual(self.module.RULE_HASH, expected[:12])
        self.assertEqual(normalized_rule_hash(base["raw_code"]), expected)
        self.assertEqual(normalized_rule_hash(base["target_code"]), expected)
        self.assertEqual(canonical_row()["train"], [])
        self.assertEqual(canonical_row()["test"], [])

    def test_every_family_is_constructive_observable_and_semantic(self) -> None:
        for band in ("easy", "medium", "hard"):
            for family in ("authored", "generalized"):
                for sample_index in range(100):
                    grid = self.module.generate(
                        10_000 + sample_index,
                        sample_index * 37 + 5,
                        difficulty=band,
                        scene_family=family,
                    )
                    before = copy.deepcopy(grid)
                    self.assertEqual(self.module.self_check(grid), [])
                    self.assertEqual(
                        self.module.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    output = self.module.rule_mirror(grid)
                    self.assertEqual(output, independent_rule(grid))
                    self.assertNotEqual(output, grid)
                    self.assertEqual(grid, before)

    def test_natural_prior_is_three_to_one_and_highly_diverse(self) -> None:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            pairs = set()
            reached_counts = set()
            unreachable_counts = set()
            for sample_index in range(1_200):
                grid = self.module.generate(
                    20_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[self.module.canonical_profile_signature(grid)] += 1
                reached_counts.add(facts["reached_blue_count"])
                unreachable_counts.add(facts["unreachable_blue_count"])
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, self.module.rule_mirror(grid))),
                    )
                )
            self.assertGreaterEqual(families["generalized"], 220)
            self.assertLessEqual(families["generalized"], 380)
            self.assertEqual(sum(families.values()), 1_200)
            self.assertGreaterEqual(len(pairs), 1_190)
            self.assertGreaterEqual(len(reached_counts), 6)
            self.assertGreaterEqual(len(unreachable_counts), 6)

    def test_walls_and_later_seed_are_causally_relevant(self) -> None:
        for band in ("easy", "medium", "hard"):
            grid = self.module.generate(
                31,
                41,
                difficulty=band,
                scene_family="generalized",
            )
            facts = self.module._analyze(grid)["facts"]
            first_seed, later_seed = facts["seeds"]
            self.assertLess(first_seed, later_seed)
            self.assertNotIn(later_seed, facts["reached"])
            self.assertGreaterEqual(facts["relevant_wall_count"], 1)
            self.assertTrue(
                any(
                    (later_seed[0] + dr, later_seed[1] + dc)
                    in facts["unreachable_blue"]
                    for dr, dc in CARDINAL
                )
            )
            output = self.module.rule_mirror(grid)
            self.assertEqual(output[later_seed[0]][later_seed[1]], 2)
            self.assertTrue(
                all(output[row][col] == 1 for row, col in facts["unreachable_blue"])
            )
            self.assertTrue(
                all(output[row][col] == 3 for row, col in facts["reached_blue"])
            )

    def test_self_check_rejects_nearest_structural_impostors(self) -> None:
        authored = self.module.generate(
            73,
            19,
            difficulty="medium",
            scene_family="authored",
        )
        generalized = self.module.generate(
            79,
            23,
            difficulty="medium",
            scene_family="generalized",
        )
        generalized_facts = self.module._analyze(generalized)["facts"]

        wrong_palette = copy.deepcopy(authored)
        wrong_palette[0][0] = 7
        no_seed = [
            [0 if value == 2 else value for value in row]
            for row in authored
        ]
        no_wall = [
            [0 if value == 8 else value for value in row]
            for row in authored
        ]
        no_negative_witness = copy.deepcopy(generalized)
        for row, col in generalized_facts["unreachable_blue"]:
            no_negative_witness[row][col] = 0
        three_seeds = copy.deepcopy(generalized)
        extra_seed = min(generalized_facts["unreachable_blue"])
        three_seeds[extra_seed[0]][extra_seed[1]] = 2
        connected_across_wall = copy.deepcopy(generalized)
        relevant_wall = next(
            (row, col)
            for row in range(len(generalized))
            for col in range(len(generalized[0]))
            if generalized[row][col] == 8
            and any(
                (row + dr1, col + dc1) in generalized_facts["reached"]
                and (row + dr2, col + dc2)
                in generalized_facts["unreachable_blue"]
                for (dr1, dc1), (dr2, dc2) in (
                    ((0, -1), (0, 1)),
                    ((0, 1), (0, -1)),
                    ((-1, 0), (1, 0)),
                    ((1, 0), (-1, 0)),
                )
            )
        )
        connected_across_wall[relevant_wall[0]][relevant_wall[1]] = 1
        non_rectangular = copy.deepcopy(authored)
        non_rectangular[0].pop()
        too_small = [row[:8] for row in authored[:8]]
        too_large = [
            [0 for _col in range(31)]
            for _row in range(31)
        ]

        for name, grid in (
            ("wrong_palette", wrong_palette),
            ("no_seed", no_seed),
            ("no_wall", no_wall),
            ("no_negative_witness", no_negative_witness),
            ("three_seeds", three_seeds),
            ("connected_across_wall", connected_across_wall),
            ("non_rectangular", non_rectangular),
            ("dimension_min_minus_one", too_small),
            ("dimension_max_plus_one", too_large),
        ):
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))
                self.assertEqual(self.module.observe_overrides(grid), {})

    def test_determinism_fresh_returns_and_global_rng_purity(self) -> None:
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 9
        third = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(third, second)

    def test_invalid_calls_reject_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            self.module.generate(0, 0, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, nonexistent_axis="x")
        with self.assertRaises((ValueError, KeyError)):
            self.module.generate(0, 0, scene_family="not-a-family")


if __name__ == "__main__":
    unittest.main()
