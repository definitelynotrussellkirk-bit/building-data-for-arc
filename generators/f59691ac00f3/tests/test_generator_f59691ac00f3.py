from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK = "f59691ac00f3"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)


def _base_path() -> Path:
    for relative in (
        "data/base/solutions/training/b5bb5719__f59691ac00f3.json",
        "shared/data/base/solutions/training/b5bb5719__f59691ac00f3.json",
    ):
        path = ROOT / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"missing task-local base authority under {ROOT}")


BASE_PATH = _base_path()


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row for {TASK}, found {len(rows)}")
    return rows[0]


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    return [*row["train"], *row["test"]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small test oracle mirroring the pinned Racket rule.

    The worker audit still executes Racket as the sole output authority; this
    mirror only makes focused Python regression tests fast and transparent.
    """
    out = copy.deepcopy(grid)
    height, width = len(out), len(out[0])
    for row in range(1, height):
        for col in range(width):
            left = out[row - 1][col - 1] if col > 0 else 7
            right = out[row - 1][col + 1] if col < width - 1 else 7
            if left != 7 and right != 7:
                out[row][col] = (7 - left) if left == right else right
    return out


def pair_witnesses(grid: list[list[int]]) -> Counter[tuple[int, int]]:
    top = grid[0]
    return Counter(
        (top[col], top[col + 2])
        for col in range(len(top) - 2)
        if top[col] in (2, 5) and top[col + 2] in (2, 5)
    )


class GeneratorTests(unittest.TestCase):
    def test_rule_hash_and_task_local_source_are_canonical(self):
        row = canonical_row()
        base = json.loads(BASE_PATH.read_text())
        canonical = row["program_solution"]
        self.assertEqual(normalized_hash(canonical), "343570d857e4")
        self.assertEqual(MOD.RULE_HASH, normalized_hash(canonical))
        raw_code = base["racket_target"]["raw_code"]
        target_code = base["racket_target"]["target_code"]
        self.assertEqual(normalized_hash(raw_code), normalized_hash(canonical))
        self.assertEqual(normalized_hash(target_code), normalized_hash(canonical))
        self.assertEqual(raw_code, target_code)

    def test_all_canonical_train_and_test_pairs_are_lawful_and_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 8)
        self.assertEqual((len(pairs[-1]["input"]), len(pairs[-1]["input"][0])), (6, 12))
        for index, pair in enumerate(pairs):
            source = pair["input"]
            original = copy.deepcopy(source)
            self.assertEqual(MOD.self_check(source), [], index)
            self.assertEqual(rule_mirror(source), pair["output"], index)
            self.assertEqual(source, original, f"mirror mutated canonical pair {index}")

    def test_every_declared_axis_has_exact_single_axis_boundary_coverage(self):
        axis_values = {
            "grid_h": range(3, 9),
            "grid_w": range(5, 17),
            "chain_length": range(2, 8),
            "seed_profile": MOD.SEED_PROFILES,
            "support_mode": MOD.SUPPORT_MODES,
            "placement": MOD.PLACEMENTS,
        }
        for band in ("easy", "medium", "hard"):
            for axis, values in axis_values.items():
                for serial, value in enumerate(values):
                    grid = MOD.generate(1000 + serial, 3000 + serial, difficulty=band, **{axis: value})
                    self.assertEqual(MOD.self_check(grid), [], (band, axis, value))
                    observed = MOD.observe_overrides(grid)
                    if axis == "grid_h":
                        self.assertEqual(len(grid), value)
                    elif axis == "grid_w":
                        self.assertEqual(len(grid[0]), value)
                    else:
                        self.assertEqual(observed[axis], value, (band, axis, value, observed))

    def test_linked_semantic_profiles_and_all_parent_pairs(self):
        expected_pairs = {(2, 2), (2, 5), (5, 2), (5, 5)}
        expected_by_profile = {
            "same_2": {(2, 2)},
            "same_5": {(5, 5)},
            "alternating": {(2, 5), (5, 2)},
            "mixed": expected_pairs,
        }
        for profile, expected in expected_by_profile.items():
            for support in MOD.SUPPORT_MODES:
                length = max(MOD._PROFILE_MIN_LENGTH[profile], 5)
                grid = MOD.generate(
                    77,
                    91,
                    difficulty="hard",
                    seed_profile=profile,
                    support_mode=support,
                    chain_length=length,
                    grid_w=16,
                    placement="left",
                )
                self.assertEqual(set(pair_witnesses(grid)), expected)
                self.assertEqual(MOD.observe_overrides(grid)["seed_profile"], profile)
                self.assertNotEqual(rule_mirror(grid), grid)

    def test_distribution_is_broad_and_each_linked_branch_fires(self):
        profiles = Counter()
        support_modes = Counter()
        placements = Counter()
        witnesses = Counter()
        inputs, outputs, shapes = set(), set(), set()
        for serial in range(600):
            band = ("easy", "medium", "hard")[serial % 3]
            grid = MOD.generate(200_000 + serial, 17 * serial + 3, difficulty=band)
            observed = MOD.observe_overrides(grid)
            self.assertEqual(set(observed), {"chain_length", "seed_profile", "support_mode", "placement"})
            self.assertEqual(MOD.self_check(grid), [])
            output = rule_mirror(grid)
            self.assertNotEqual(output, grid)
            profiles[observed["seed_profile"]] += 1
            support_modes[observed["support_mode"]] += 1
            placements[observed["placement"]] += 1
            witnesses.update(pair_witnesses(grid))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))
            shapes.add((len(grid), len(grid[0])))
        self.assertEqual(set(profiles), set(MOD.SEED_PROFILES))
        self.assertEqual(set(support_modes), set(MOD.SUPPORT_MODES))
        self.assertEqual(set(placements), set(MOD.PLACEMENTS))
        self.assertEqual(set(witnesses), {(2, 2), (2, 5), (5, 2), (5, 5)})
        self.assertGreaterEqual(min(profiles.values()), 70)
        self.assertGreaterEqual(min(support_modes.values()), 150)
        self.assertGreaterEqual(min(placements.values()), 25)
        self.assertGreater(len(inputs), 500)
        self.assertGreater(len(outputs), 500)
        self.assertGreaterEqual(len(shapes), 30)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(8491)
        before = random.getstate()
        first = MOD.generate(123, 456, difficulty="hard")
        self.assertEqual(random.getstate(), before)
        second = MOD.generate(123, 456, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9
        third = MOD.generate(123, 456, difficulty="hard")
        self.assertEqual(second, third)
        self.assertEqual(random.getstate(), before)

    def test_self_check_rejects_targeted_impostors(self):
        valid = MOD.generate(19, 23, difficulty="medium")
        cases = []

        lower_seed = copy.deepcopy(valid)
        lower_seed[1][0] = 2
        cases.append(lower_seed)

        foreign_color = copy.deepcopy(valid)
        foreign_color[0][0] = 3
        cases.append(foreign_color)

        no_active_pair = [[7] * 7 for _ in range(4)]
        no_active_pair[0][0] = 2
        no_active_pair[0][3] = 5
        cases.append(no_active_pair)

        one_seed = [[7] * 7 for _ in range(4)]
        one_seed[0][2] = 2
        cases.append(one_seed)

        too_large = [[7] * 17 for _ in range(4)]
        too_large[0][0] = too_large[0][2] = 2
        cases.append(too_large)

        cases.extend(([], [[]], [[7, 7], [7]], [[True] * 5 for _ in range(3)]))
        for case in cases:
            self.assertTrue(MOD.self_check(case), case)

    def test_invalid_and_incompatible_overrides_fail_loudly(self):
        invalid = (
            {"texture": "full_top"},
            {"grid_h": 2},
            {"grid_h": True},
            {"grid_w": 17},
            {"grid_w": 6.5},
            {"chain_length": 8},
            {"seed_profile": "unknown"},
            {"support_mode": "unknown"},
            {"placement": "unknown"},
            {"seed_profile": "mixed", "chain_length": 2},
            {"grid_w": 5, "chain_length": 7},
            {"grid_w": 5, "chain_length": 2, "support_mode": "dual_parity", "placement": "free"},
        )
        for overrides in invalid:
            with self.assertRaises(ValueError, msg=overrides):
                MOD.generate(1, 2, **overrides)


if __name__ == "__main__":
    unittest.main()
