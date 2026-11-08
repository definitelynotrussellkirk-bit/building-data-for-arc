"""Regressions for the d1dab66b0d54 direction prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d1dab66b0d54"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SOURCE = HERE / "guide_shift.py"


def _load():
    if not SOURCE.is_file():
        raise AssertionError(f"missing parametric prototype: {SOURCE}")
    spec = importlib.util.spec_from_file_location("d1_guide_shift", SOURCE)
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


class GuideShiftPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_exact_canonical_default_and_strict_setting_contract(self):
        self.assertEqual(self.mod.program({"direction": "forward"}), _canonical_program())
        self.assertNotEqual(self.mod.program({"direction": "backward"}), _canonical_program())
        for bad in ({}, {"direction": "sideways"}, {"direction": True}, {"direction": "forward", "x": 1}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.mod.program(bad)

    def test_all_demo_counts_identify_direction_and_keep_four_novel_queries(self):
        for setting in self.mod.SETTINGS:
            for demos in range(2, 7):
                episode = self.mod.generate(400 + demos, setting, demos, 4)
                self.assertEqual((len(episode["train"]), len(episode["test"])), (demos, 4))
                self.assertEqual(episode["program_solution"], self.mod.program(setting))
                self.assertEqual(
                    len({self.mod.digest(pair["input"]) for pair in episode["train"] + episode["test"]}),
                    demos + 4,
                )
                other = next(candidate for candidate in self.mod.SETTINGS if candidate != setting)
                self.assertTrue(all(self.mod.transform(pair["input"], other) != pair["output"] for pair in episode["train"]))
                self.assertTrue(any((len(pair["input"]), len(pair["input"][0])) == (30, 30) for pair in episode["test"]))
                self.assertTrue(all(sum(cell == 2 for row in pair["output"] for cell in row) == 8 for pair in episode["train"] + episode["test"]))

    def test_eight_queries_remain_unique_and_prefix_stable_for_extreme_seed(self):
        setting = {"direction": "forward"}
        four = self.mod.generate(-(2**63), setting, demos=2, queries=4)
        eight = self.mod.generate(-(2**63), setting, demos=2, queries=8)
        self.assertEqual(four["train"], eight["train"])
        self.assertEqual(four["test"], eight["test"][:4])
        inputs = eight["train"] + eight["test"]
        self.assertEqual(
            len({self.mod.digest(pair["input"]) for pair in inputs}),
            len(inputs),
        )
        # Query index 4 takes the novelty-retry path for this seed. Verify that
        # the replacement remains executable under both protected Racket rules.
        with self.mod.RacketRunner() as execute:
            for chosen in self.mod.SETTINGS:
                retried = self.mod.generate(-(2**63), chosen, demos=2, queries=8)["test"][4]
                self.assertEqual(
                    execute(self.mod.program(chosen), retried["input"]),
                    retried["output"],
                )

    def test_python_and_protected_racket_agree_for_both_directions(self):
        with self.mod.RacketRunner() as execute:
            for setting in self.mod.SETTINGS:
                episode = self.mod.generate(77, setting, 2, 4)
                for pair in episode["train"] + episode["test"]:
                    before = copy.deepcopy(pair["input"])
                    self.assertEqual(self.mod.transform(pair["input"], setting), pair["output"])
                    self.assertEqual(pair["input"], before)
                    self.assertEqual(execute(self.mod.program(setting), pair["input"]), pair["output"])

    def test_count_grid_and_setting_failures_are_explicit(self):
        setting = {"direction": "forward"}
        for demos in (1, 7, True, 3.0):
            with self.subTest(demos=demos), self.assertRaises(ValueError):
                self.mod.generate(1, setting, demos, 4)
        for queries in (0, 9, True, 4.0):
            with self.subTest(queries=queries), self.assertRaises(ValueError):
                self.mod.generate(1, setting, 3, queries)
        for grid in ([], [[0]], [[True]], [[0], [0, 0]], [[3, 3, 3], [0, 2, 0]]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.mod.transform(grid, setting)

    def test_public_projection_hides_direction_program_and_query_answers(self):
        episode = self.mod.generate(91, {"direction": "backward"}, 3, 4)
        mutated = copy.deepcopy(episode)
        mutated["program_solution"] = "private"
        mutated["settings"] = {"direction": "forward"}
        for pair in mutated["test"]:
            pair["output"] = [[9]]
        self.assertEqual(public_challenge_bytes(mutated), public_challenge_bytes(episode))
        self.assertEqual(public_challenge_id(mutated), public_challenge_id(episode))


if __name__ == "__main__":
    unittest.main()
