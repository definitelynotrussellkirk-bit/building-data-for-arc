"""Focused semantic regressions for generator 0938f7c346fb."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.0938f7c346fb.generator"
)


ROOT = find_root(__file__)


def canonical():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(
            json.loads(line)
            for line in handle
            if json.loads(line)["task_id"] == gen.TASK_ID
        )


class Generator0938Tests(unittest.TestCase):
    def test_rule_hash_and_all_official_pairs(self):
        row = canonical()
        normalized = " ".join(row["program_solution"].split())
        self.assertEqual(
            gen.RULE_HASH,
            hashlib.sha256(normalized.encode()).hexdigest()[:12],
        )
        profiles = set()
        for pair in canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True):
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(gen.self_check(grid), [])
            self.assertEqual(gen.rule_mirror(grid), pair["output"])
            profiles.add(gen._analyze(grid)["facts"]["scene_profile"])
        self.assertEqual(profiles, set(gen.PUBLIC_PROFILES))

    def test_every_profile_and_band_is_exactly_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile in gen.SCENE_PROFILES:
                for seed in range(60):
                    grid = gen.generate(
                        seed,
                        seed % 5,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_all_operations_have_unique_demo_and_nonempty_query(self):
        seen = set()
        for profile in gen.SCENE_PROFILES:
            for seed in range(40):
                grid = gen.generate(seed, 2, scene_profile=profile)
                facts = gen._analyze(grid)["facts"]
                panels = facts["panels"]
                self.assertEqual(
                    gen._infer_matches(panels[0], panels[1], panels[2]),
                    (facts["operation"],),
                )
                self.assertTrue(any(value for row in facts["output"] for value in row))
                seen.add(facts["operation"])
        self.assertEqual(seen, set(gen.OPS))

    def test_separators_are_solid_gray_and_operand_gray_is_rejected(self):
        grid = gen.generate(2, 0, scene_profile="public_xor")
        width = gen._analyze(grid)["facts"]["panel_width"]
        separators = [index * (width + 1) + width for index in range(4)]
        self.assertTrue(all(grid[row][col] == 5 for row in range(len(grid)) for col in separators))
        broken = copy.deepcopy(grid)
        broken[0][separators[0]] = 0
        self.assertTrue(gen.self_check(broken))
        broken = copy.deepcopy(grid)
        broken[0][0] = 5
        self.assertTrue(gen.self_check(broken))

    def test_invalid_or_ambiguous_demo_is_rejected(self):
        grid = gen.generate(3, 0, scene_profile="public_conflict_merge")
        facts = gen._analyze(grid)["facts"]
        panel_width = facts["panel_width"]
        broken = copy.deepcopy(grid)
        result_left = 2 * (panel_width + 1)
        for row in range(len(broken)):
            for col in range(panel_width):
                broken[row][result_left + col] = 0
        self.assertTrue(gen.self_check(broken))

    def test_last_operation_conflicts_are_red(self):
        witnesses = 0
        for seed in range(200):
            grid = gen.generate(
                seed,
                0,
                scene_profile="generalized_conflict_merge",
            )
            output = gen.rule_mirror(grid)
            witnesses += any(value == 9 for row in output for value in row)
        self.assertGreater(witnesses, 100)

    def test_determinism_freshness_rng_and_validation(self):
        random.seed(99)
        state = random.getstate()
        first = gen.generate(18, 4, difficulty="hard", scene_profile="generalized_left_minus")
        self.assertEqual(random.getstate(), state)
        second = gen.generate(18, 4, difficulty="hard", scene_profile="generalized_left_minus")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 8 if first[0][0] != 8 else 7
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            gen.generate(1, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, bogus="x")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, scene_profile="unknown")


if __name__ == "__main__":
    unittest.main()
