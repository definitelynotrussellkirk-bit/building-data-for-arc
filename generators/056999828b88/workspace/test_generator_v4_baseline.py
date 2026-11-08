"""Focused regression tests for generator 056999828b88."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / "056999828b88" / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_056999828b88", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "056999828b88":
                return [pair["input"] for pair in row["train"]] + [row["test"]["input"]]
    raise AssertionError("canonical task 056999828b88 is missing")


class PackBySizeGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.canonical = canonical_inputs()

    def test_rule_hash_and_exact_canonical_profile_table(self):
        self.assertEqual("d2d58f482c81", self.generator.RULE_HASH)
        derived = {self.generator._linked_profile(grid) for grid in self.canonical}
        self.assertEqual(self.generator._CANONICAL_LINKED_PROFILES, derived)

    def test_every_canonical_input_is_accepted_and_strict(self):
        for index, grid in enumerate(self.canonical):
            with self.subTest(index=index):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual([], self.generator.strict_canonical_like(grid))

    def test_declared_override_boundaries_are_exact_in_every_band(self):
        cases = [
            {"grid_h": 8, "grid_w": 10, "n_objects": 3},
            {"grid_h": 10, "grid_w": 12, "n_objects": 4},
        ]
        for band in ("easy", "medium", "hard"):
            for case in cases:
                grid = self.generator.generate(41, 17, difficulty=band, **case)
                observed = self.generator.observe_overrides(grid)
                with self.subTest(band=band, case=case):
                    self.assertEqual(case, {key: observed[key] for key in case})
                    self.assertEqual([], self.generator.self_check(grid, difficulty=band))

    def test_four_sample_schedule_is_identifiable(self):
        demos = []
        for sample_index in range(4):
            grid = self.generator.generate(12345, sample_index)
            demos.append({"input": grid, "output": self.generator._size_pack(grid)})
        query_grid = self.generator.generate(12345, 4)
        query = {"input": query_grid, "output": self.generator._size_pack(query_grid)}
        self.assertEqual([], self.generator.lesson_identifiable(demos, query))
        self.assertTrue(any(self.generator._has_color_order_conflict(p["input"]) for p in demos))
        self.assertTrue(any(self.generator._has_scan_order_conflict(p["input"]) for p in demos))
        self.assertTrue(any(self.generator._has_bbox_area_conflict(p["input"]) for p in demos))

    def test_self_check_rejects_five_targeted_impostors(self):
        base = self.canonical[0]
        impostors = {}

        duplicate_size = copy.deepcopy(base)
        duplicate_size[2][10] = 0  # size-3 L becomes a size-2 domino
        impostors["duplicate_size"] = duplicate_size

        split_color = copy.deepcopy(base)
        split_color[4][5] = 0
        split_color[6][5] = 3  # color 3 now occupies two disconnected objects
        impostors["split_color"] = split_color

        touching_objects = copy.deepcopy(base)
        touching_objects[1][1] = 0
        touching_objects[3][4] = 2  # directly touches the color-3 domino
        impostors["touching_objects"] = touching_objects

        oversize = copy.deepcopy(base)
        for r, c in ((3, 9), (3, 10), (4, 9), (4, 10)):
            oversize[r][c] = 4  # connected size-7 feature, absent elsewhere
        impostors["size_seven"] = oversize

        two_objects = copy.deepcopy(base)
        two_objects[1][1] = 0
        impostors["two_objects"] = two_objects

        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid), name)

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state_before = random.getstate()
        first = self.generator.generate(777, 19, difficulty="hard")
        state_after = random.getstate()
        second = self.generator.generate(777, 19, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = self.generator.generate(777, 19, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
