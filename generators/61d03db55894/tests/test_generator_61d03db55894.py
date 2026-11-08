"""Focused semantic regressions for generator 61d03db55894 (a64e4611)."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "61d03db55894"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/training/a64e4611__61d03db55894.json"


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator61d03db55894Tests(unittest.TestCase):
    def test_all_four_canonical_pairs_are_accepted_and_solved(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        profiles = []
        for pair in pairs:
            source = pair["input"]
            self.assertEqual(GEN.self_check(source), [])
            self.assertEqual(GEN.strict_canonical_like(source), [])
            self.assertEqual(GEN.rule_mirror(source), pair["output"])
            profiles.append(GEN.observe_overrides(source)["scene_profile"])
        self.assertEqual(profiles, list(GEN.SCENE_PROFILES))

    def test_every_exact_profile_and_color_override_realizes(self):
        for band in ("easy", "medium", "hard"):
            for profile in GEN.SCENE_PROFILES:
                for color in GEN.TEXTURE_COLORS:
                    grid = GEN.generate(
                        101,
                        203,
                        difficulty=band,
                        scene_profile=profile,
                        texture_color=color,
                    )
                    observed = GEN.observe_overrides(grid)
                    self.assertEqual(
                        observed,
                        {"scene_profile": profile, "texture_color": color},
                    )
                    self.assertEqual(
                        GEN.self_check(
                            grid,
                            meta={
                                "overrides": {
                                    "scene_profile": profile,
                                    "texture_color": color,
                                }
                            },
                        ),
                        [],
                    )
                    output = GEN.rule_mirror(grid)
                    self.assertNotEqual(output, grid)

    def test_default_schedule_covers_all_profiles_per_four_examples(self):
        for band in ("easy", "medium", "hard"):
            for start in range(8):
                profiles = {
                    GEN.observe_overrides(
                        GEN.generate(97, start + offset, difficulty=band)
                    )["scene_profile"]
                    for offset in range(4)
                }
                self.assertEqual(profiles, set(GEN.SCENE_PROFILES))

    def test_semantic_branches_have_real_output_support(self):
        seen_multiple_rows = False
        seen_multiple_cols = False
        seen_three_cols = False
        for index, profile in enumerate(GEN.SCENE_PROFILES):
            grid = GEN.generate(41, index, scene_profile=profile)
            info = GEN._analysis(grid)
            self.assertTrue(info["row_fill"] - info["col_fill"])
            self.assertTrue(info["col_fill"] - info["row_fill"])
            self.assertTrue(info["row_fill"] & info["col_fill"])
            seen_multiple_rows |= len(info["row_details"]) >= 2
            seen_multiple_cols |= len(info["col_details"]) >= 2
            seen_three_cols |= any(
                detail["thickness"] == 3 for detail in info["col_details"]
            )
        self.assertTrue(seen_multiple_rows)
        self.assertTrue(seen_multiple_cols)
        self.assertTrue(seen_three_cols)

    def test_self_check_rejects_nearest_impostors(self):
        base = GEN.generate(
            313,
            509,
            difficulty="medium",
            scene_profile="right_arms_full_column",
            texture_color=4,
        )
        info = GEN._analysis(base)
        ink = info["texture_color"]

        ragged = copy.deepcopy(base)
        ragged[0].pop()
        wrong_size = copy.deepcopy(base[:-1])
        second_color = copy.deepcopy(base)
        r, c = next(
            (r, c)
            for r, row in enumerate(second_color)
            for c, value in enumerate(row)
            if value == ink
        )
        second_color[r][c] = 8 if ink != 8 else 2
        boolean_cell = copy.deepcopy(base)
        boolean_cell[0][0] = True
        full_zero = [[0] * GEN.GRID_SIZE for _ in range(GEN.GRID_SIZE)]

        no_row_branch = copy.deepcopy(base)
        for detail in info["row_details"]:
            group = detail["group"]
            for breaker_row in group[1:-1]:
                for c in range(detail["common_start"], detail["common_end"] + 1):
                    no_row_branch[breaker_row][c] = ink

        no_col_branch = copy.deepcopy(base)
        for detail in info["col_details"]:
            group = detail["group"]
            for breaker_col in group[1:-1]:
                for r in range(detail["common_start"], detail["common_end"] + 1):
                    no_col_branch[r][breaker_col] = ink

        for mutation in (
            ragged,
            wrong_size,
            second_color,
            boolean_cell,
            full_zero,
            no_row_branch,
            no_col_branch,
        ):
            self.assertTrue(GEN.self_check(mutation), mutation)

    def test_lesson_identifiability_requires_all_four_profiles(self):
        demos = []
        for sample_index in range(4):
            grid = GEN.generate(200, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(200, 4, difficulty="medium")
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        self.assertEqual(GEN.lesson_identifiable(demos, query), [])
        reasons = GEN.lesson_identifiable(demos[:3], query)
        self.assertTrue(any("omit profile" in reason for reason in reasons))
        self.assertTrue(any("rival survives" in reason for reason in reasons))

    def test_invalid_overrides_determinism_and_fresh_returns(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"texture_color": 7},
            {"unknown_axis": 1},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    GEN.generate(1, 2, **overrides)
        random.seed(20260726)
        state = random.getstate()
        first = GEN.generate(701, 907, difficulty="hard")
        second = GEN.generate(701, 907, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        self.assertEqual(random.getstate(), state)

    def test_selected_authorities_and_rule_hash_are_synchronized(self):
        row = _canonical_row()
        base = json.loads(BASE.read_text())
        target = base["racket_target"]
        selected = row["program_solution"]
        self.assertEqual(target["target_code"], selected)
        self.assertEqual(target["target_code_role"], "selected_task_rule")
        self.assertEqual(target["raw_code_role"], "archival_executable_source")
        self.assertNotEqual(target["raw_code"], selected)
        self.assertEqual(_rule_hash(selected), GEN.RULE_HASH)
        self.assertEqual(GEN.RULE_HASH, "dd04335d4f92")


if __name__ == "__main__":
    unittest.main()
