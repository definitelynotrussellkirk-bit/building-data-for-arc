"""Focused semantic regressions for generator 1ecf6add3fe7."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
from reviewer_support import find_root, canonical_path
import random
import unittest


TASK_ID = "1ecf6add3fe7"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator1ecf6add3fe7Tests(unittest.TestCase):
    def test_rule_authority_and_all_canonical_pairs(self):
        row = _canonical_row()
        canonical = row["program_solution"]
        base = json.loads((
            canonical_path(ROOT).parent.parent / "base/solutions/banks/5b06d39592a3/H107__1ecf6add3fe7.json"
        ).read_text())
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "9be86eb85768")
        self.assertEqual(_normalized_hash(base["racket_target"]["target_code"]), MODULE.RULE_HASH)
        pairs = [*row["train"], row["test"]]
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            frozen = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            self.assertEqual(source, frozen)

    def test_regression_exact_overrides_are_realized_and_observable(self):
        # The original v2.0.1 ignored base_size=6 for this exact fixture.
        grid = MODULE.generate(0, 0, difficulty="medium", base_size=6)
        self.assertEqual(MODULE.observe_overrides(grid)["base_size"], 6)
        self.assertEqual(MODULE.analyze_grid(grid)["base_size"], 6)

    def test_every_axis_boundary_and_combined_corners(self):
        cases = [
            {"grid_h": 5}, {"grid_h": 9},
            {"panel_w": 4}, {"panel_w": 7},
            {"base_size": 3}, {"base_size": 8},
            {"decoy_size": 3}, {"decoy_size": 8},
            {"match_side": 0}, {"match_side": 1},
            {"grid_h": 5, "panel_w": 4, "base_size": 3, "decoy_size": 3, "match_side": 0},
            {"grid_h": 9, "panel_w": 7, "base_size": 8, "decoy_size": 8, "match_side": 1},
        ]
        for index, overrides in enumerate(cases):
            with self.subTest(overrides=overrides):
                grid = MODULE.generate(900 + index, 70 + index, difficulty="hard", **overrides)
                observed = MODULE.observe_overrides(grid)
                for key, value in overrides.items():
                    self.assertEqual(observed[key], value)
                self.assertEqual(MODULE.self_check(grid), [])

    def test_both_match_sides_equal_area_decoys_and_transform_families(self):
        sides = set()
        equal_area = 0
        transform_families = set()
        for seed in range(500):
            info = MODULE.analyze_grid(MODULE.generate(seed, seed * 17 + 3, difficulty="hard"))
            sides.add(info["match_side"])
            equal_area += int(info["same_size_decoy"])
            candidates = info["transform_candidates"]
            if 0 in candidates:
                transform_families.add("identity")
            if any(code in candidates for code in (1, 2, 3)):
                transform_families.add("rotation")
            if any(code in candidates for code in (4, 5, 6, 7)):
                transform_families.add("reflection")
        self.assertEqual(sides, {0, 1})
        self.assertGreater(equal_area, 40)
        self.assertEqual(transform_families, {"identity", "rotation", "reflection"})

    def test_equal_area_decoy_refutes_count_only_shortcut(self):
        witness = None
        for seed in range(300):
            grid = MODULE.generate(seed + 1000, seed, difficulty="medium", base_size=4, decoy_size=4)
            info = MODULE.analyze_grid(grid)
            if info["match_side"] in (0, 1):
                witness = info
                break
        self.assertIsNotNone(witness)
        self.assertEqual(len(witness["normalized_shapes"][0]), len(witness["normalized_shapes"][1]))
        self.assertNotEqual(
            witness["normalized_shapes"][2] in MODULE._d4_variants(witness["normalized_shapes"][0]),
            witness["normalized_shapes"][2] in MODULE._d4_variants(witness["normalized_shapes"][1]),
        )

    def test_self_check_rejects_targeted_impostors(self):
        base = MODULE.generate(211, 307, difficulty="hard", base_size=5, decoy_size=5)
        info = MODULE.analyze_grid(base)
        pw = info["panel_w"]
        bases = (0, pw + 1, 2 * pw + 2)

        broken_separator = copy.deepcopy(base)
        broken_separator[-1][pw] = 0

        duplicate_label = copy.deepcopy(base)
        duplicate_label[0][bases[1]] = duplicate_label[0][bases[0]]

        query_label_leak = copy.deepcopy(base)
        query_label_leak[0][bases[2]] = 2

        foreign_color = copy.deepcopy(base)
        qr, qc = info["shapes"][2][0]
        foreign_color[qr][bases[2] + qc] = 9

        disconnected = copy.deepcopy(base)
        # Move one query cell to a guaranteed isolated reserved-row position.
        disconnected[qr][bases[2] + qc] = 0
        disconnected[0][bases[2] + pw - 1] = 1

        both_match = copy.deepcopy(base)
        matching = info["normalized_shapes"][info["match_side"]]
        decoy_side = 1 - info["match_side"]
        for r in range(1, len(base)):
            for c in range(pw):
                both_match[r][bases[decoy_side] + c] = 0
        for r, c in matching:
            both_match[1 + r][bases[decoy_side] + c] = 1

        for name, mutation in (
            ("broken_separator", broken_separator),
            ("duplicate_label", duplicate_label),
            ("query_label_leak", query_label_leak),
            ("foreign_color", foreign_color),
            ("disconnected", disconnected),
            ("both_match", both_match),
        ):
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(mutation), name)

    def test_determinism_freshness_and_global_rng_purity(self):
        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        frozen = copy.deepcopy(first)
        MODULE.observe_overrides(first)
        MODULE.rule_mirror(first)
        self.assertEqual(first, frozen)

    def test_unknown_and_out_of_range_overrides_reject(self):
        invalid = (
            {"texture": "no_match"}, {"grid_h": 4}, {"grid_h": 10},
            {"panel_w": 3}, {"panel_w": 8}, {"base_size": 2},
            {"base_size": 9}, {"decoy_size": 2}, {"decoy_size": 9},
            {"match_side": -1}, {"match_side": 2},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises((ValueError, TypeError)):
                    MODULE.generate(1, 2, **overrides)


if __name__ == "__main__":
    unittest.main()
