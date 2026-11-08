"""Regressions for the d35dbdf1cfc2 motif-order prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d35dbdf1cfc2"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SOURCE = HERE / "motif_order.py"


def _load():
    if not SOURCE.is_file():
        raise AssertionError(f"missing parametric prototype: {SOURCE}")
    spec = importlib.util.spec_from_file_location("d35_motif_order", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(TASK_ID)


def _span(grid):
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return (
        max(r for r, _ in occupied) - min(r for r, _ in occupied),
        max(c for _, c in occupied) - min(c for _, c in occupied),
    )


class MotifOrderPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_exact_canonical_default_and_strict_setting_contract(self):
        self.assertEqual(self.mod.program({"order": "size_desc"}), _canonical_program())
        self.assertNotEqual(self.mod.program({"order": "size_asc"}), _canonical_program())
        for bad in ({}, {"order": "color"}, {"order": True}, {"order": "size_desc", "x": 1}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.mod.program(bad)

    def test_all_demo_counts_identify_order_and_keep_four_novel_queries(self):
        for setting in self.mod.SETTINGS:
            for demos in range(2, 7):
                episode = self.mod.generate(500 + demos, setting, demos, 4)
                self.assertEqual((len(episode["train"]), len(episode["test"])), (demos, 4))
                self.assertEqual(episode["program_solution"], self.mod.program(setting))
                self.assertEqual(
                    len({self.mod.digest(pair["input"]) for pair in episode["train"] + episode["test"]}),
                    demos + 4,
                )
                other = next(candidate for candidate in self.mod.SETTINGS if candidate != setting)
                self.assertTrue(
                    all(self.mod.transform(pair["input"], other) != pair["output"]
                        for pair in episode["train"])
                )
                self.assertTrue(any((len(pair["input"]), len(pair["input"][0])) == (30, 30)
                                    for pair in episode["test"]))
                large = next(pair["input"] for pair in episode["test"]
                             if (len(pair["input"]), len(pair["input"][0])) == (30, 30))
                self.assertGreaterEqual(_span(large)[0], 24)
                self.assertGreaterEqual(_span(large)[1], 24)
                for pair in episode["train"] + episode["test"]:
                    objects = self.mod.GEN._extract_objects(pair["input"])
                    self.assertGreaterEqual(len({len(obj["cells"]) for obj in objects}), 2)
                    self.assertTrue(any(
                        obj["r2"] - obj["r1"] > obj["c2"] - obj["c1"]
                        for obj in objects
                    ))

    def test_python_and_protected_racket_agree_for_both_orders(self):
        with self.mod.RacketRunner() as execute:
            for setting in self.mod.SETTINGS:
                episode = self.mod.generate(77, setting, 2, 4)
                for pair in episode["train"] + episode["test"]:
                    before = copy.deepcopy(pair["input"])
                    self.assertEqual(self.mod.transform(pair["input"], setting), pair["output"])
                    self.assertEqual(pair["input"], before)
                    self.assertEqual(execute(self.mod.program(setting), pair["input"]), pair["output"])

    def test_query_prefix_and_count_grid_setting_failures_are_explicit(self):
        setting = {"order": "size_desc"}
        one = self.mod.generate(91, setting, 3, 1)
        four = self.mod.generate(91, setting, 3, 4)
        self.assertEqual(one["train"], four["train"])
        self.assertEqual(one["test"][0], four["test"][0])
        for demos in (1, 7, True, 3.0):
            with self.subTest(demos=demos), self.assertRaises(ValueError):
                self.mod.generate(1, setting, demos, 4)
        for queries in (0, 9, True, 4.0):
            with self.subTest(queries=queries), self.assertRaises(ValueError):
                self.mod.generate(1, setting, 3, queries)
        for grid in ([], [[0]], [[True]], [[0], [0, 0]], [[2, 2], [2, 0]]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.mod.transform(grid, setting)

    def test_public_projection_hides_order_program_and_query_answers(self):
        episode = self.mod.generate(91, {"order": "size_asc"}, 3, 4)
        mutated = copy.deepcopy(episode)
        mutated["program_solution"] = "private"
        mutated["settings"] = {"order": "size_desc"}
        for pair in mutated["test"]:
            pair["output"] = [[9]]
        self.assertEqual(public_challenge_bytes(mutated), public_challenge_bytes(episode))
        self.assertEqual(public_challenge_id(mutated), public_challenge_id(episode))


if __name__ == "__main__":
    unittest.main()
