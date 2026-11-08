"""Focused semantic regressions for generator 2b3472c73d30."""

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
TASK_ID = "2b3472c73d30"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/b64eb6bd4039/E57__2b3472c73d30.json"
)


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def independent_rule(grid):
    output = copy.deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color in dict.fromkeys(value for value in row if value):
            columns = [
                col for col, value in enumerate(row) if value == color
            ]
            if (
                len(columns) == 2
                and all(
                    row[col] == 0
                    for col in range(columns[0] + 1, columns[1])
                )
            ):
                for col in range(columns[0], columns[1] + 1):
                    output[row_index][col] = color
    return output


class Generator2B3472C73D30Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_all_canonical_pairs_and_linked_profiles(self):
        row = canonical_row()
        pairs = row["train"] + [row["test"]]
        profiles = (
            "public_train_1",
            "public_train_2",
            "public_test_1",
        )
        self.assertEqual(len(pairs), 3)
        for pair, profile in zip(pairs, profiles):
            with self.subTest(profile=profile):
                grid = copy.deepcopy(pair["input"])
                analysis = self.module._analyze(grid)
                self.assertEqual(analysis["errors"], [])
                self.assertEqual(analysis["facts"]["family"], "linked")
                self.assertEqual(
                    analysis["facts"]["linked_profile"], profile
                )
                self.assertEqual(self.module.rule_mirror(grid), pair["output"])
                self.assertEqual(independent_rule(grid), pair["output"])
                self.assertEqual(grid, pair["input"])

    def test_rule_target_is_pinned(self):
        canonical = canonical_row()["program_solution"]
        target = json.loads(BASE_PATH.read_text())["racket_target"]["target_code"]
        self.assertEqual(normalized_hash(canonical), "9f6d9dc4a68d")
        self.assertEqual(self.module.RULE_HASH, normalized_hash(canonical))
        self.assertEqual(target, canonical)

    def test_forced_families_and_every_semantic_profile(self):
        linked_profiles = set()
        generalized_profiles = set()
        for band in ("easy", "medium", "hard"):
            for family in ("linked", "generalized"):
                for sample_index in range(300):
                    grid = self.module.generate(
                        100_000 + sample_index,
                        sample_index * 19 + 7,
                        difficulty=band,
                        scene_family=family,
                    )
                    before = copy.deepcopy(grid)
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["errors"], [])
                    facts = analysis["facts"]
                    self.assertEqual(facts["family"], family)
                    self.assertEqual(
                        self.module.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    self.assertEqual(
                        self.module.rule_mirror(grid),
                        independent_rule(grid),
                    )
                    self.assertGreaterEqual(facts["eligible_count"], 2)
                    self.assertGreaterEqual(facts["changed_count"], 2)
                    self.assertEqual(grid, before)
                    if family == "linked":
                        linked_profiles.add(facts["linked_profile"])
                    else:
                        generalized_profiles.add(
                            facts["generalized_profile"]
                        )
        self.assertEqual(
            linked_profiles,
            {"public_train_1", "public_train_2", "public_test_1"},
        )
        self.assertEqual(
            generalized_profiles, set(self.module.GENERAL_PROFILES)
        )

    def test_near_miss_rows_remain_unchanged(self):
        for profile, count_name in (
            ("blocked", "blocked_count"),
            ("count_decoys", "repeated_count"),
            ("mixed", "blocked_count"),
        ):
            seen = 0
            for sample_index in range(80):
                grid = self.module.generate(
                    222,
                    sample_index,
                    difficulty="hard",
                    scene_family="generalized",
                )
                facts = self.module._analyze(grid)["facts"]
                if facts["generalized_profile"] != profile:
                    continue
                output = independent_rule(grid)
                self.assertGreater(facts[count_name], 0)
                for row, *_ in facts["blocked"]:
                    self.assertEqual(output[row], grid[row])
                for row, *_ in facts["adjacent"]:
                    self.assertEqual(output[row], grid[row])
                for row, *_ in facts["repeated"]:
                    self.assertEqual(output[row], grid[row])
                seen += 1
            self.assertGreater(seen, 0)

    def test_causal_blocker_and_count_mutations(self):
        grid = self.module.generate(
            333, 444, difficulty="medium", scene_family="generalized"
        )
        facts = self.module._analyze(grid)["facts"]
        row, color, left, right = facts["eligible"][0]
        blocked = copy.deepcopy(grid)
        blocker_col = left + 1
        blocker_color = next(value for value in range(1, 10) if value != color)
        blocked[row][blocker_col] = blocker_color
        blocked_output = independent_rule(blocked)
        self.assertEqual(blocked_output[row], blocked[row])

        third = copy.deepcopy(grid)
        third_col = left + 1
        third[row][third_col] = color
        third_output = independent_rule(third)
        self.assertEqual(third_output[row], third[row])

        blocked_scene = next(
            candidate
            for index in range(300)
            if (
                candidate := self.module.generate(
                    555,
                    index,
                    difficulty="medium",
                    scene_family="generalized",
                )
            )
            and self.module._analyze(candidate)["facts"]["blocked"]
        )
        blocked_facts = self.module._analyze(blocked_scene)["facts"]
        row, color, left, right = blocked_facts["blocked"][0]
        cleared = copy.deepcopy(blocked_scene)
        for col in range(left + 1, right):
            cleared[row][col] = 0
        cleared_output = independent_rule(cleared)
        self.assertTrue(
            all(cleared_output[row][col] == color for col in range(left, right + 1))
        )

    def test_row_reflection_color_and_order_automorphisms(self):
        grid = copy.deepcopy(canonical_row()["train"][0]["input"])
        color_map = {2: 9, 4: 1, 6: 7}
        transformed = [
            [color_map.get(value, value) for value in reversed(row)]
            for row in reversed(grid)
        ]
        expected = [
            [color_map.get(value, value) for value in reversed(row)]
            for row in reversed(independent_rule(grid))
        ]
        self.assertEqual(independent_rule(transformed), expected)
        self.assertEqual(
            self.module._analyze(transformed)["facts"]["linked_profile"],
            "public_train_1",
        )

    def test_natural_prior_diversity_and_difficulty(self):
        shape_sets = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            profiles = set()
            inputs = set()
            outputs = set()
            shapes = set()
            for sample_index in range(800):
                grid = self.module.generate(
                    600_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[facts["family"]] += 1
                profiles.add(
                    facts["linked_profile"]
                    or facts["generalized_profile"]
                )
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertGreaterEqual(families["linked"], 180)
            self.assertGreaterEqual(families["generalized"], 480)
            self.assertGreaterEqual(len(profiles), 10)
            self.assertGreaterEqual(len(inputs), 780)
            self.assertGreaterEqual(len(outputs), 780)
            shape_sets[band] = shapes
        self.assertNotEqual(shape_sets["easy"], shape_sets["medium"])
        self.assertNotEqual(shape_sets["medium"], shape_sets["hard"])

    def test_self_check_rejects_semantic_impostors(self):
        impostors = {
            "all_background": [[0] * 9 for _ in range(7)],
            "full_color": [[4] * 9 for _ in range(7)],
            "one_pair": [[4 if r == 2 and c in (1, 7) else 0
                          for c in range(9)] for r in range(7)],
            "singleton": [[4 if (r, c) == (2, 2) else 0
                           for c in range(9)] for r in range(7)],
            "ragged": [[0] * 9 for _ in range(6)] + [[0] * 8],
            "boolean": [[True if (r, c) == (2, 2) else 0
                         for c in range(9)] for r in range(7)],
            "bad_value": [[10 if (r, c) == (2, 2) else 0
                           for c in range(9)] for r in range(7)],
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            777, 888, difficulty="hard", scene_family="generalized"
        )
        second = self.module.generate(
            777, 888, difficulty="hard", scene_family="generalized"
        )
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 8 if first[0][0] == 0 else 0
        self.assertEqual(
            second,
            self.module.generate(
                777, 888, difficulty="hard", scene_family="generalized"
            ),
        )
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            self.module.generate(0, 0, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, nonexistent_axis=True)
        with self.assertRaises((ValueError, KeyError)):
            self.module.generate(0, 0, scene_family="unknown")


if __name__ == "__main__":
    unittest.main()
