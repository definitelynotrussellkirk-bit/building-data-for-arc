"""Focused regression tests for generator 5591a8b5bd67.

The repair pins the selected canonical rule, removes dead/misleading controls,
and makes lesson semantics directly observable through exact axes and a
three-example wall-profile schedule.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5591a8b5bd67"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


class TestRuleHashAndCanonicalAcceptance(unittest.TestCase):
    def test_rule_hash_matches_selected_target_code(self):
        path = ROOT / "data/base/solutions/banks/ad4abc25f505/easy_69_cast_rightward_rays_until_wall__5591a8b5bd67.json"
        record = json.loads(path.read_text())
        target = record["racket_target"]["target_code"]
        self.assertEqual(gen.RULE_HASH, _normalized_hash(target))
        self.assertEqual(gen.RULE_HASH, _normalized_hash(_canonical_row()["program_solution"]))

    def test_all_canonical_inputs_are_accepted(self):
        row = _canonical_row()
        for split in ("train", "test"):
            for index, pair in enumerate(row[split]):
                self.assertEqual(
                    gen.self_check(pair["input"]), [],
                    f"rejected canonical {split}[{index}]",
                )


class TestDeterminismAndPurity(unittest.TestCase):
    def test_replay_is_equal_but_fresh(self):
        first = gen.generate(9182, 2, difficulty="hard")
        second = gen.generate(9182, 2, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        for a, b in zip(first, second):
            self.assertIsNot(a, b)

        pristine = copy.deepcopy(second)
        first[0][0] = (first[0][0] + 1) % 10
        replay = gen.generate(9182, 2, difficulty="hard")
        self.assertEqual(replay, pristine, "a prior return contaminated replay")

    def test_generate_does_not_touch_process_global_rng(self):
        random.seed(773311)
        before = random.getstate()
        gen.generate(4, 1, difficulty="medium")
        self.assertEqual(random.getstate(), before)


class TestExactOverrideContract(unittest.TestCase):
    def _draw(self, **case):
        grid = gen.generate(41, 5, difficulty="medium", **case)
        self.assertEqual(gen.self_check(grid), [], case)
        return grid

    def test_each_declared_boundary_is_accepted(self):
        for value in (6, 14):
            grid = self._draw(grid_h=value)
            self.assertEqual(len(grid), value)
        for value in (8, 18):
            grid = self._draw(grid_w=value)
            self.assertEqual(len(grid[0]), value)
        for value in (2, 10):
            grid = self._draw(rays=value)
            self.assertEqual(gen.observe_overrides(grid)["rays"], value)
        for value in (1, 8):
            grid = self._draw(n_distinct_colors=value)
            self.assertEqual(gen.observe_overrides(grid)["n_distinct_colors"], value)
        for value in gen.WALL_PROFILES:
            grid = self._draw(wall_profile=value)
            self.assertEqual(gen.observe_overrides(grid)["wall_profile"], value)

    def test_compatible_combination_is_exact(self):
        case = {
            "grid_h": 10,
            "grid_w": 18,
            "rays": 8,
            "n_distinct_colors": 8,
            "wall_profile": "blocked",
        }
        grid = self._draw(**case)
        observed = gen.observe_overrides(grid)
        self.assertEqual((len(grid), len(grid[0])), (10, 18))
        self.assertEqual(observed["rays"], 8)
        self.assertEqual(observed["n_distinct_colors"], 8)
        self.assertEqual(observed["wall_profile"], "blocked")

    def test_incompatible_combinations_reject_loudly(self):
        for case in (
            {"grid_h": 6, "rays": 10},
            {"rays": 2, "n_distinct_colors": 8},
            {"grid_h": 6, "n_distinct_colors": 8},
            {"wall_profile": "sometimes"},
            {"grid_w": 7},
        ):
            with self.assertRaises((ValueError, AssertionError), msg=case):
                gen.generate(3, 0, difficulty="easy", **case)

    def test_default_profile_schedule_is_semantically_visible(self):
        expected = ("mixed", "blocked", "open")
        for sample_index, profile in enumerate(expected):
            grid = gen.generate(7, sample_index, difficulty="easy")
            self.assertEqual(gen.observe_overrides(grid)["wall_profile"], profile)


class TestLessonStructureAndImpostors(unittest.TestCase):
    def _base(self, profile="mixed"):
        return gen.generate(
            9901,
            0,
            difficulty="medium",
            grid_h=10,
            grid_w=15,
            rays=5,
            n_distinct_colors=4,
            wall_profile=profile,
        )

    @staticmethod
    def _active_rows(grid):
        return [r for r, row in enumerate(grid) if any(v not in (0, 5) for v in row)]

    def test_generated_rows_have_one_visible_seed_and_only_gray_blockers(self):
        for profile in gen.WALL_PROFILES:
            grid = self._base(profile)
            for r in self._active_rows(grid):
                row = grid[r]
                seeds = [c for c, v in enumerate(row) if v not in (0, 5)]
                walls = [c for c, v in enumerate(row) if v == 5]
                self.assertEqual(len(seeds), 1)
                self.assertEqual(row[seeds[0] + 1], 0)
                self.assertLessEqual(len(walls), 1)
                if walls:
                    self.assertGreaterEqual(walls[0], seeds[0] + 2)

    def test_rejects_second_non_gray_seed_in_a_row(self):
        grid = self._base("open")
        r = self._active_rows(grid)[0]
        seed = next(c for c, v in enumerate(grid[r]) if v not in (0, 5))
        grid[r][seed + 2] = 9 if grid[r][seed] != 9 else 8
        self.assertTrue(any("multiple non-gray seeds" in e for e in gen.self_check(grid)))

    def test_rejects_wall_only_row(self):
        grid = self._base("open")
        empty = next(r for r, row in enumerate(grid) if not any(row))
        grid[empty][-1] = 5
        self.assertTrue(any("wall but no seed" in e for e in gen.self_check(grid)))

    def test_rejects_immediately_blocked_seed(self):
        grid = self._base("open")
        r = self._active_rows(grid)[0]
        seed = next(c for c, v in enumerate(grid[r]) if v not in (0, 5))
        grid[r][seed + 1] = 5
        errors = gen.self_check(grid)
        self.assertTrue(any("visible zero" in e or "at least two" in e for e in errors), errors)

    def test_rejects_right_edge_seed(self):
        grid = self._base("open")
        r = self._active_rows(grid)[0]
        seed = next(c for c, v in enumerate(grid[r]) if v not in (0, 5))
        color = grid[r][seed]
        grid[r][seed] = 0
        grid[r][-1] = color
        self.assertTrue(any("right edge" in e for e in gen.self_check(grid)))

    def test_rejects_multiple_walls(self):
        grid = self._base("blocked")
        r = self._active_rows(grid)[0]
        seed = next(c for c, v in enumerate(grid[r]) if v not in (0, 5))
        existing = next(c for c, v in enumerate(grid[r]) if v == 5)
        choices = [c for c in range(seed + 2, len(grid[r])) if c != existing]
        self.assertTrue(choices)
        grid[r][choices[0]] = 5
        self.assertTrue(any("multiple gray walls" in e for e in gen.self_check(grid)))

    def test_rejects_too_few_active_rows(self):
        grid = self._base("open")
        rows = self._active_rows(grid)
        for r in rows[1:]:
            grid[r] = [0] * len(grid[r])
        self.assertTrue(any("at least two" in e for e in gen.self_check(grid)))

    def test_rejects_wall_without_trailing_counterexample_cell(self):
        grid = self._base("blocked")
        r = self._active_rows(grid)[0]
        wall = next(c for c, v in enumerate(grid[r]) if v == 5)
        grid[r][wall] = 0
        grid[r][-1] = 5
        self.assertTrue(any("zero cell beyond" in e for e in gen.self_check(grid)))

    def test_rejects_all_seeds_at_left_edge(self):
        grid = self._base("open")
        for r in self._active_rows(grid):
            c = next(c for c, v in enumerate(grid[r]) if v not in (0, 5))
            color = grid[r][c]
            grid[r][c] = 0
            grid[r][0] = color
        self.assertTrue(any("space to its left" in e for e in gen.self_check(grid)))


if __name__ == "__main__":
    unittest.main()
