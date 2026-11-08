"""Regressions for the task-local phase-anchor parametric prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "bca4f37ec5e9"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SOURCE = HERE / "phase_anchor.py"


def _load():
    if not SOURCE.is_file():
        raise AssertionError(f"missing parametric prototype: {SOURCE}")
    spec = importlib.util.spec_from_file_location("bca_phase_anchor", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"missing canonical task {TASK_ID}")


class PhaseAnchorPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_default_program_is_exact_canonical_and_settings_are_strict(self):
        self.assertEqual(
            self.mod.program({"phase_anchor": "source"}),
            _canonical_program(),
        )
        self.assertNotEqual(
            self.mod.program({"phase_anchor": "grid_top"}),
            _canonical_program(),
        )
        for bad in (
            {},
            {"phase_anchor": "other"},
            {"phase_anchor": True},
            {"phase_anchor": "source", "extra": 1},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.mod.program(bad)

    def test_every_supported_demo_count_teaches_the_setting_and_keeps_four_queries(self):
        for setting in self.mod.SETTINGS:
            for demos in range(2, 7):
                with self.subTest(setting=setting, demos=demos):
                    episode = self.mod.generate(1000 + demos, setting, demos, 4)
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), 4)
                    self.assertEqual(episode["program_solution"], self.mod.program(setting))
                    self.assertEqual(
                        len({self.mod.digest(pair["input"]) for pair in episode["train"] + episode["test"]}),
                        demos + 4,
                    )
                    other = next(candidate for candidate in self.mod.SETTINGS if candidate != setting)
                    self.assertTrue(
                        any(
                            self.mod.transform(pair["input"], other) != pair["output"]
                            for pair in episode["train"]
                        )
                    )
                    self.assertTrue(
                        any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                            for pair in episode["test"])
                    )

    def test_python_transform_is_immutable_and_racket_agrees_for_both_settings(self):
        with self.mod.RacketRunner() as execute:
            for setting in self.mod.SETTINGS:
                episode = self.mod.generate(41, setting, 2, 4)
                for pair in episode["train"] + episode["test"]:
                    before = copy.deepcopy(pair["input"])
                    self.assertEqual(
                        self.mod.transform(pair["input"], setting),
                        pair["output"],
                    )
                    self.assertEqual(pair["input"], before)
                    self.assertEqual(
                        execute(self.mod.program(setting), pair["input"]),
                        pair["output"],
                    )

    def test_counts_and_grid_contract_reject_without_partial_episode(self):
        setting = {"phase_anchor": "source"}
        for demos in (1, 7, True, 3.0):
            with self.subTest(demos=demos), self.assertRaises(ValueError):
                self.mod.generate(7, setting, demos, 4)
        for queries in (0, 9, True, 4.0):
            with self.subTest(queries=queries), self.assertRaises(ValueError):
                self.mod.generate(7, setting, 3, queries)
        for seed in (True, 1.0, "1"):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                self.mod.generate(seed, setting, 3, 4)
        for grid in ([], [[0], [0, 0]], [[True]], [[10]], [[0, 0]]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.mod.transform(grid, setting)

    def test_public_bytes_hide_settings_programs_and_query_answers(self):
        episode = self.mod.generate(89, {"phase_anchor": "source"}, 3, 4)
        public = json.loads(public_challenge_bytes(episode))
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        mutated = copy.deepcopy(episode)
        mutated["program_solution"] = "PRIVATE-MUTATION"
        for pair in mutated["test"]:
            pair["output"] = [[9]]
        mutated["private_settings"] = {"phase_anchor": "grid_top"}
        self.assertEqual(public_challenge_bytes(mutated), public_challenge_bytes(episode))
        self.assertEqual(public_challenge_id(mutated), public_challenge_id(episode))


if __name__ == "__main__":
    unittest.main()
