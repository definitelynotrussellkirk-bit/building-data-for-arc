"""Focused semantic regressions for generator 1f3e27c86f7a."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter

from solvers.grounded_rules import GROUNDED_RULES
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
DATA = canonical_path(ROOT).parents[1]
TASK_ID = "1f3e27c86f7a"
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


class Generator1f3e27c86f7aTests(unittest.TestCase):
    def test_rule_authorities_and_metadata_are_synchronized(self):
        row = canonical_row()
        source = row["program_solution"]
        self.assertEqual("3.0.0", GENERATOR.VERSION)
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(source),
        )
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(GROUNDED_RULES[TASK_ID]),
        )
        base = json.loads(
            (
                DATA
                / "base/solutions/training"
                / f"40f6cd08__{TASK_ID}.json"
            ).read_text()
        )
        target = base["racket_target"]["target_code"]
        self.assertEqual(GENERATOR.RULE_HASH, normalized_rule_hash(target))
        self.assertEqual({"rule_branch"}, set(GENERATOR.AXES))

    def test_every_canonical_pair_is_accepted_with_the_expected_branch(self):
        row = canonical_row()
        pairs = row["train"] + row["test"]
        self.assertEqual(4, len(pairs))
        expected = (
            "right_align",
            "top_align",
            "proportional",
            "stripe",
        )
        for pair, branch in zip(pairs, expected):
            source = copy.deepcopy(pair["input"])
            self.assertEqual([], GENERATOR.self_check(source))
            self.assertEqual(
                {"rule_branch": branch},
                GENERATOR.observe_overrides(source),
            )
            self.assertEqual(pair["input"], source)

    def test_every_semantic_branch_is_exactly_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for branch in GENERATOR.BRANCHES:
                for seed in range(20):
                    with self.subTest(band=band, branch=branch, seed=seed):
                        grid = GENERATOR.generate(
                            seed,
                            10_000 + seed,
                            difficulty=band,
                            rule_branch=branch,
                        )
                        self.assertEqual([], GENERATOR.self_check(grid))
                        self.assertEqual(
                            {"rule_branch": branch},
                            GENERATOR.observe_overrides(grid),
                        )

    def test_defaults_are_deterministic_fresh_and_rng_isolation_holds(self):
        global_state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                first = GENERATOR.generate(seed, seed * 17 + 3, difficulty=band)
                second = GENERATOR.generate(seed, seed * 17 + 3, difficulty=band)
                pristine = copy.deepcopy(first)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(a is not b for a, b in zip(first, second)))
                first[0][0] = (first[0][0] + 1) % 10
                self.assertEqual(
                    pristine,
                    GENERATOR.generate(seed, seed * 17 + 3, difficulty=band),
                )
                self.assertEqual(global_state, random.getstate())

    def test_default_distribution_covers_all_branches_shapes_and_colors(self):
        branches = {band: Counter() for band in ("easy", "medium", "hard")}
        shapes = set()
        colors = set()
        inputs = set()
        for band_index, band in enumerate(branches):
            for seed in range(600):
                grid = GENERATOR.generate(
                    100_000 * band_index + seed,
                    seed * 31 + 7,
                    difficulty=band,
                )
                analysis = GENERATOR._analyze(grid)
                self.assertEqual([], analysis["errors"])
                branches[band][analysis["facts"]["branch"]] += 1
                shapes.add((len(grid), len(grid[0])))
                colors.update(value for row in grid for value in row)
                inputs.add(tuple(map(tuple, grid)))
        for counts in branches.values():
            self.assertEqual(set(GENERATOR.BRANCHES), set(counts))
            self.assertGreaterEqual(min(counts.values()), 70)
        self.assertGreaterEqual(len(shapes), 20)
        self.assertEqual(set(range(10)), colors)
        self.assertGreaterEqual(len(inputs), 1_790)

    def test_self_check_rejects_minimal_semantic_impostors(self):
        valid_nested = GENERATOR.generate(
            31,
            41,
            difficulty="medium",
            rule_branch="left_align",
        )
        valid_stripe = GENERATOR.generate(
            37,
            43,
            difficulty="medium",
            rule_branch="stripe",
        )
        impostors = [
            [[0 for _ in row] for row in valid_nested],
            [[1] * 8 for _ in range(8)],
            [row[:-1] if index == 0 else row for index, row in enumerate(valid_nested)],
            [[True if value else 0 for value in row] for row in valid_nested],
        ]
        asymmetric = copy.deepcopy(valid_stripe)
        stripe_row = next(
            index
            for index, row in enumerate(asymmetric)
            if len({value for value in row if value}) > 1
        )
        stripe_cols = [
            col for col, value in enumerate(asymmetric[stripe_row]) if value
        ]
        asymmetric[stripe_row][stripe_cols[-1]] = 0
        impostors.append(asymmetric)
        for index, grid in enumerate(impostors):
            with self.subTest(index=index):
                self.assertTrue(GENERATOR.self_check(grid))

    def test_invalid_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, mystery_axis=3)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, rule_branch="not-a-branch")


if __name__ == "__main__":
    unittest.main()
