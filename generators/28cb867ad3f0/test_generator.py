from __future__ import annotations

import copy
import importlib
import json
import unittest
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.28cb867ad3f0.generator")


ROOT = Path(__file__).resolve().parents[3]


def canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task not found")


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_match_python_mirror(self):
        pairs = canonical_pairs()
        self.assertEqual(5, len(pairs))
        for pair in pairs:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_every_profile_override_is_exactly_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile in gen.SCENE_PROFILES:
                grid = gen.generate(901, 17, difficulty=band, scene_profile=profile)
                self.assertEqual([], gen.self_check(grid))
                self.assertEqual(profile, gen.observe_overrides(grid)["scene_profile"])

    def test_default_schedule_is_deterministic_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for index in range(18):
                first = gen.generate(121, index, difficulty=band)
                second = gen.generate(121, index, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertEqual(
                    gen.schedule_profile(121, index, band),
                    gen.observe_overrides(first)["scene_profile"],
                )

    def test_unknown_override_rejected(self):
        with self.assertRaises(TypeError):
            gen.generate(1, 0, difficulty="easy", typo_axis="public_1")

    def test_targeted_impostors_are_rejected(self):
        source = gen.generate(41, 7, difficulty="medium", scene_profile="one_tie")

        border_zero = copy.deepcopy(source)
        border_zero[0][1] = 0
        self.assertTrue(gen.self_check(border_zero))

        stray_marker = copy.deepcopy(source)
        # A wall-line intersection is not adjacent to any chamber.
        facts = gen._analysis(stray_marker)
        row = facts["components"][0]["bbox"][2] + 1
        col = facts["components"][0]["bbox"][3] + 1
        stray_marker[row][col] = 1
        self.assertTrue(gen.self_check(stray_marker))

        no_boundary = copy.deepcopy(source)
        component = gen._analysis(no_boundary)["components"][0]
        for row, col in set(component["boundary_positions"]):
            no_boundary[row][col] = 5
        self.assertTrue(gen.self_check(no_boundary))

        missing_palette_role = copy.deepcopy(source)
        for row, values in enumerate(missing_palette_role):
            for col, value in enumerate(values):
                if value == 4:
                    missing_palette_role[row][col] = 3
        self.assertTrue(gen.self_check(missing_palette_role))


    def test_named_rivals_have_real_killing_witnesses(self):
        examples = {
            "unique_presence_only": gen.generate(17, 2, difficulty="hard", scene_profile="all_colors"),
            "global_plurality": gen.generate(18, 2, difficulty="hard", scene_profile="one_tie"),
            "tie_break_smallest": gen.generate(19, 2, difficulty="hard", scene_profile="two_ties"),
            "ignore_shared_markers": gen.generate(20, 2, difficulty="hard", scene_profile="public_4"),
            "rectangles_only": gen.generate(21, 0, difficulty="easy", scene_profile="public_1"),
        }
        for name, grid in examples.items():
            self.assertNotEqual(gen.rule_mirror(grid), gen.SEMANTIC_RIVALS[name](grid), name)


if __name__ == "__main__":
    unittest.main()
