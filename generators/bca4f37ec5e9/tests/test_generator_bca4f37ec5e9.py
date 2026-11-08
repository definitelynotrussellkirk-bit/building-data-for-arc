"""Focused semantic regressions for generator bca4f37ec5e9."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "bca4f37ec5e9"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
BANDS = ("easy", "medium", "hard")
BASE_PATHS = (
    DATA_ROOT / "base/solutions/training/8eb1be9a__bca4f37ec5e9.json",
    DATA_ROOT / "base/solutions/augmented/8eb1be9a__a501c3ffda80.json",
)


def _canonical_rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if not rows:
        raise AssertionError(f"missing canonical task {TASK_ID}")
    return rows


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


class GeneratorBca4f37ec5e9Tests(unittest.TestCase):
    def test_all_six_canonical_pairs_are_accepted_and_solved(self):
        reviewed = 0
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertTrue(MODULE.strict_canonical_like(source))
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)
            reviewed += 1
        self.assertEqual(reviewed, 6)

    def test_rule_pin_and_selected_authorities_are_exact(self):
        canonical = _canonical_rows()[0]["program_solution"]
        self.assertEqual(MODULE.RULE_HASH, "868f6b6ec7f1")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        for path in BASE_PATHS:
            target = json.loads(path.read_text())["racket_target"]
            self.assertEqual(target["target_code"], canonical)
            self.assertEqual(target["target_code_role"], "selected_task_rule")
            self.assertEqual(target["raw_code_role"], "archival_executable_source")
            self.assertNotEqual(target["raw_code"], canonical)

    def test_every_profile_override_is_exact_in_every_band(self):
        for band in BANDS:
            for profile in MODULE._PROFILE_NAMES:
                for seed in range(3):
                    grid = MODULE.generate(
                        1000 + seed,
                        37 * seed + 5,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertEqual(
                        MODULE.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_two_disjoint_censuses_keep_strict_canonical_support(self):
        for seed_start in (0, 100_000):
            for band in BANDS:
                strict = 0
                inputs = set()
                periods = set()
                placements = set()
                profiles = set()
                for offset in range(200):
                    seed = seed_start + offset
                    grid = MODULE.generate(seed, seed * 19 + 7, difficulty=band)
                    self.assertEqual(MODULE.self_check(grid), [])
                    features = MODULE.semantic_features(grid)
                    strict += int(features["strict_canonical_like"])
                    inputs.add(_freeze(grid))
                    periods.add(features["period"])
                    placements.add(
                        (features["empty_rows_above"], features["empty_rows_below"])
                    )
                    profiles.add(features["scene_profile"])
                self.assertGreaterEqual(strict, 10, (seed_start, band, strict))
                self.assertGreaterEqual(len(inputs), 100, (seed_start, band, len(inputs)))
                self.assertEqual(periods, {2, 3, 4, 5})
                self.assertGreaterEqual(len(placements), 7)
                self.assertEqual(profiles, set(MODULE._PROFILE_NAMES))

    def test_every_cyclic_three_demo_lesson_rejects_grid_top_phase(self):
        def grid_top_phase_rival(grid):
            nonzero_rows = [
                r for r, row in enumerate(grid) if any(value != 0 for value in row)
            ]
            first, last = nonzero_rows[0], nonzero_rows[-1]
            period_rows = grid[first : last + 1]
            return [
                list(period_rows[r % len(period_rows)]) for r in range(len(grid))
            ]

        seed_bases = {"easy": 100_000, "medium": 200_000, "hard": 300_000}
        for band in BANDS:
            for start in range(4):
                for offset in range(100):
                    seed = seed_bases[band] + offset
                    demos = [
                        MODULE.generate(seed, start + step, difficulty=band)
                        for step in range(3)
                    ]
                    self.assertTrue(
                        any(
                            MODULE.rule_mirror(grid) != grid_top_phase_rival(grid)
                            for grid in demos
                        ),
                        (band, seed, start),
                    )

    def test_mutation_fixtures_are_rejected(self):
        fixtures = MODULE.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 5)
        for name, grid in fixtures:
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(grid), name)

    def test_unknown_override_rejects_loudly(self):
        with self.assertRaisesRegex(TypeError, "unknown override"):
            MODULE.generate(1, 2, difficulty="medium", typo_profile="period2_top")

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260725)
        state = random.getstate()
        first = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 9
        third = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(second, third)

    def test_negative_recombination_uses_absent_second_color(self):
        fixtures = dict(MODULE.mutation_fixtures())
        bad = fixtures["second_nonzero_color"]
        colors = {value for row in bad for value in row if value}
        self.assertEqual(len(colors), 2)
        self.assertTrue(MODULE.self_check(bad))


if __name__ == "__main__":
    unittest.main()
