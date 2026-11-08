from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from reviewer_support import find_root

TASK_ID = "3f5263211041"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("_test_parametric_3f5263211041", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return next(iter(programs))


class ParametricGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = _load()

    def test_canonical_program_is_byte_exact_and_settings_are_strict(self):
        self.assertEqual(self.p.program({"gallery_mode": "direct"}), _canonical_program())
        self.assertNotEqual(
            self.p.program({"gallery_mode": "width_relay"}),
            _canonical_program(),
        )
        for bad in ({}, {"gallery_mode": "bad"}, {"gallery_mode": "direct", "x": 1}):
            with self.assertRaises(ValueError):
                self.p.program(bad)

    def test_inputs_are_matched_across_settings_and_counts_are_prefix_stable(self):
        direct = self.p.generate(17, {"gallery_mode": "direct"}, demos=2, queries=4)
        relay = self.p.generate(17, {"gallery_mode": "width_relay"}, demos=2, queries=4)
        self.assertEqual(
            [pair["input"] for pair in direct["train"] + direct["test"]],
            [pair["input"] for pair in relay["train"] + relay["test"]],
        )
        one = self.p.generate(17, {"gallery_mode": "width_relay"}, demos=2, queries=1)
        six = self.p.generate(17, {"gallery_mode": "width_relay"}, demos=6, queries=4)
        self.assertEqual(one["train"], relay["train"])
        self.assertEqual(one["test"][0], relay["test"][0])
        self.assertEqual(six["train"][:2], relay["train"])
        self.assertEqual(six["test"], relay["test"])

    def test_supported_boundaries_and_content_spread(self):
        episode = self.p.generate(0, {"gallery_mode": "width_relay"}, demos=6, queries=4)
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        self.assertEqual(len(inputs), len({json.dumps(grid) for grid in inputs}))
        shapes = {(len(grid), len(grid[0])) for grid in inputs}
        self.assertIn((10, 17), shapes)
        self.assertIn((30, 30), shapes)
        stress = next(grid for grid in inputs if len(grid) == len(grid[0]) == 30)
        occupied_rows = {r for r, row in enumerate(stress) if any(row)}
        occupied_cols = {c for row in stress for c, value in enumerate(row) if value}
        self.assertIn(0, occupied_cols)
        self.assertIn(29, occupied_cols)
        self.assertGreater(max(occupied_rows), 25)

    def test_two_demos_teach_width_relay_and_wrong_intermediate_changes_output(self):
        episode = self.p.generate(23, {"gallery_mode": "width_relay"}, demos=2, queries=4)
        report = self.p.teaching_check(episode, {"gallery_mode": "width_relay"})
        self.assertEqual(report["harmful_survivors"], [])
        widths = [self.p.analyze_input(pair["input"])["relay_width"] for pair in episode["train"]]
        self.assertEqual(set(widths), {2, 3})
        witnesses = []
        for pair in episode["test"]:
            facts = self.p.analyze_input(pair["input"])
            wrong = self.p.solve_with_intermediate(pair["input"], facts["control_height"])
            if wrong != pair["output"]:
                witnesses.append((facts, wrong))
        self.assertTrue(witnesses)

    def test_two_demo_teaching_is_stable_across_seed_sample(self):
        for seed in range(16):
            for mode in self.p.MODES:
                episode = self.p.generate(seed, {"gallery_mode": mode}, demos=2, queries=4)
                report = self.p.teaching_check(episode, {"gallery_mode": mode})
                self.assertEqual(report["harmful_survivors"], [], (seed, mode, report))

    def test_public_projection_hides_private_fields_and_is_first_turn_stable(self):
        one = self.p.generate(9, {"gallery_mode": "width_relay"}, demos=3, queries=1)
        four = self.p.generate(9, {"gallery_mode": "width_relay"}, demos=3, queries=4)
        first_one = self.p.public_view(one, 0)
        first_four = self.p.public_view(four, 0)
        self.assertEqual(first_one, first_four)
        self.assertEqual(set(first_one), {"train", "test"})
        self.assertNotIn("output", first_one["test"][0])
        self.assertNotIn("settings", json.dumps(first_one))
        self.assertNotIn("program_solution", json.dumps(first_one))


if __name__ == "__main__":
    unittest.main()
