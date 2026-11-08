"""Focused semantic and override regressions for priority sprouts."""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import unittest

TASK_ID = "a3a85fedfec1"


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        here = Path(__file__).resolve()
        home = here.parents[1]
        for parent in here.parents:
            runtime = parent / "shared" / "runtime"
            if runtime.is_dir():
                sys.path.insert(0, str(runtime))
                break
        spec = importlib.util.spec_from_file_location(
            f"generator_{TASK_ID}", home / "generator.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def _facts(grid):
    priority = [value for value in grid[0] if value != 0]
    ranks = {value: index for index, value in enumerate(priority)}
    seeds = [
        (row - 1, col, grid[row][col])
        for row in range(1, len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    ]
    edges = set()
    for index, left in enumerate(seeds):
        for right in seeds[index + 1 :]:
            if (
                left[2] != right[2]
                and abs(left[0] - right[0]) + abs(left[1] - right[1]) == 2
            ):
                edges.add(tuple(sorted((ranks[left[2]], ranks[right[2]]))))
    return priority, seeds, edges


def _canonical_pairs():
    here = Path(__file__).resolve()
    candidates = []
    for parent in here.parents:
        candidates.extend(
            [
                parent / "shared" / "data" / "canonical" / "puzzles.jsonl",
                parent / "data" / "canonical" / "puzzles.jsonl",
            ]
        )
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            record = json.loads(line)
            if record.get("task_id") != TASK_ID:
                continue
            pairs = [*record["train"], record["test"]]
            return [
                {
                    "input": [[int(value) for value in row] for row in pair["input"]],
                    "output": [[int(value) for value in row] for row in pair["output"]],
                }
                for pair in pairs
            ]
    raise AssertionError("canonical task record not found")


def _pair(seed, sample_index, band="medium", **overrides):
    grid = GEN.generate(seed, sample_index, difficulty=band, **overrides)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


class PrioritySproutsGeneratorTests(unittest.TestCase):
    def test_every_generated_input_exposes_the_complete_priority_chain(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                with self.subTest(band=band, seed=seed):
                    grid = GEN.generate(seed + 1000, seed * 17 + 3, difficulty=band)
                    priority, seeds, edges = _facts(grid)
                    self.assertEqual(GEN.self_check(grid), [])
                    self.assertEqual({color for _r, _c, color in seeds}, set(priority))
                    self.assertTrue(
                        {(rank, rank + 1) for rank in range(len(priority) - 1)}
                        <= edges,
                        (priority, seeds, edges),
                    )

    def test_declared_axes_are_only_observable_free_controls(self):
        self.assertEqual(
            set(GEN.AXES),
            {"grid_h", "grid_w", "n_priority", "n_seeds"},
        )
        cases = (
            {"grid_h": 8},
            {"grid_h": 12},
            {"grid_w": 9},
            {"grid_w": 13},
            {"n_priority": 2},
            {"n_priority": 3},
            {"n_seeds": 3},
            {"n_seeds": 6},
            {"grid_h": 8, "grid_w": 9, "n_priority": 3, "n_seeds": 6},
            {"grid_h": 12, "grid_w": 13, "n_priority": 2, "n_seeds": 3},
        )
        for band in ("easy", "medium", "hard"):
            for case in cases:
                with self.subTest(band=band, case=case):
                    grid = GEN.generate(91, 37, difficulty=band, **case)
                    observed = GEN.observe_overrides(grid)
                    for key, expected in case.items():
                        self.assertEqual(observed[key], expected)
                    self.assertEqual(GEN.self_check(grid), [])
        for bad in (
            {"grid_h": 7},
            {"grid_h": 13},
            {"grid_w": 8},
            {"grid_w": 14},
            {"n_priority": 1},
            {"n_priority": 4},
            {"n_seeds": 2},
            {"n_seeds": 7},
            {"palette_kind": "warm"},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(1, 2, **bad)
        with self.assertRaises(ValueError):
            GEN.generate(1, 2, difficulty="extreme")

    def test_self_check_rejects_priority_blind_and_malformed_inputs(self):
        no_conflict = [[0] * 9 for _ in range(8)]
        no_conflict[0][1] = 1
        no_conflict[0][6] = 2
        no_conflict[2][1] = 1
        no_conflict[4][4] = 2
        no_conflict[6][7] = 1
        self.assertEqual(GEN.self_check(no_conflict), [])
        self.assertTrue(GEN.teaching_check(no_conflict))

        unknown_body_color = [row[:] for row in no_conflict]
        unknown_body_color[4][4] = 3
        unknown_body_color[3][3] = 2
        self.assertTrue(GEN.self_check(unknown_body_color))

        malformed = [row[:] for row in no_conflict]
        malformed[3][3] = [1]
        before = [row[:] for row in malformed]
        self.assertTrue(GEN.self_check(malformed))
        self.assertEqual(malformed, before)

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(20261023)
        state = random.getstate()
        first = GEN.generate(77, 19, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GEN.generate(77, 19, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))

    def test_self_check_accepts_all_canonical_inputs(self):
        for index, pair in enumerate(_canonical_pairs()):
            with self.subTest(index=index):
                self.assertEqual(GEN.self_check(pair["input"]), [])

    def test_rule_mirror_matches_all_canonical_pairs_without_mutation(self):
        self.assertEqual(GEN.RULE_HASH, "f96ecacc4b71")
        for index, pair in enumerate(_canonical_pairs()):
            with self.subTest(index=index):
                before = [row[:] for row in pair["input"]]
                self.assertEqual(GEN.strict_canonical_like(pair["input"]), [])
                self.assertEqual(GEN.rule_mirror(pair["input"]), pair["output"])
                self.assertEqual(pair["input"], before)

    def test_canonical_like_support_clears_declared_floor(self):
        self.assertEqual(GEN.MIN_STRICT_FRAC, 0.04)
        accepted = 0
        total = 0
        for band in ("easy", "medium", "hard"):
            for index in range(200):
                grid = GEN.generate(index, index * 7 + 3, difficulty=band)
                accepted += GEN.strict_canonical_like(grid) == []
                total += 1
        self.assertGreaterEqual(accepted / total, GEN.MIN_STRICT_FRAC)

    def test_three_consecutive_demos_refute_every_named_competitor(self):
        expected = {
            "row_major_first_hit",
            "row_major_last_hit",
            "numeric_min_color",
            "numeric_max_color",
        }
        self.assertEqual(set(GEN.LESSON_COMPETITORS), expected)
        self.assertEqual(GEN.CANONICAL_SHORTCUTS, {})
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                with self.subTest(band=band, start=start):
                    demos = [_pair(5000 + start, start + offset, band) for offset in range(3)]
                    query = _pair(5000 + start, start + 3, band)
                    self.assertEqual(GEN.lesson_identifiable(demos, query), [])
                    for name, competitor in GEN.LESSON_COMPETITORS.items():
                        self.assertTrue(
                            any(
                                competitor(pair["input"]) != pair["output"]
                                for pair in demos
                            ),
                            name,
                        )

    def test_lesson_checker_reports_surviving_same_parity_shortcuts(self):
        demos = [_pair(1234, index, "medium", n_priority=2) for index in (0, 2, 4)]
        query = _pair(1234, 1, "medium", n_priority=2)
        reasons = GEN.lesson_identifiable(demos, query)
        self.assertTrue(any("row_major_first_hit" in reason for reason in reasons))
        self.assertTrue(any("numeric_min_color" in reason for reason in reasons))

    def test_semantic_witnesses_fire_and_rivals_preserve_inputs(self):
        grids = [GEN.generate(772, index, difficulty="medium") for index in range(4)]
        self.assertEqual(set(GEN.WITNESS_RIVALS), set(GEN.SEMANTIC_WITNESSES))
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            with self.subTest(witness=witness_name):
                self.assertTrue(any(witness(grid) for grid in grids))
        for name, rival in GEN.LESSON_COMPETITORS.items():
            grid = GEN.generate(991, 5, difficulty="hard")
            before = [row[:] for row in grid]
            output = rival(grid)
            self.assertEqual(grid, before, name)
            self.assertEqual(len(output), len(grid) - 1)
            self.assertTrue(all(len(row) == len(grid[0]) for row in output))


if __name__ == "__main__":
    unittest.main()
