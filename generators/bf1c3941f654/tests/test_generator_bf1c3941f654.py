"""Focused regression tests for generator bf1c3941f654."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.bf1c3941f654.generator"
)


def _normal(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _canonical_pairs():
    row = _canonical_row()
    return [*row["train"], *row["test"]]


class GeneratorBf1c3941f654Tests(unittest.TestCase):
    def test_rule_hash_and_every_canonical_pair(self):
        row = _canonical_row()
        actual_hash = hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, actual_hash)
        self.assertEqual(len(row["train"]), 2)
        self.assertEqual(len(row["test"]), 1)

        profiles = []
        for pair in _canonical_pairs():
            source = _normal(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), _normal(pair["output"]))
            self.assertEqual(source, before)
            profile = MODULE.semantic_profile(source)
            profiles.append(
                (
                    profile["grid_h"],
                    profile["grid_w"],
                    profile["frame_signatures"],
                    profile["outside_twos"],
                )
            )
            self.assertTrue(MODULE.canonical_like(source))
        self.assertEqual(
            profiles,
            [
                (10, 12, ((4, 5, 1), (4, 5, 1)), 2),
                (11, 13, ((4, 4, 1), (5, 6, 2)), 2),
                (12, 14, ((5, 5, 2), (5, 5, 2)), 2),
            ],
        )

    def test_declared_axes_are_exact_observable_and_band_independent(self):
        self.assertEqual(
            set(MODULE.AXES),
            {"grid_h", "grid_w", "n_frames", "inside_twos", "outside_twos"},
        )
        boundary_cases = (
            {"grid_h": 10, "grid_w": 12, "n_frames": 2, "inside_twos": 2, "outside_twos": 1},
            {"grid_h": 14, "grid_w": 16, "n_frames": 2, "inside_twos": 4, "outside_twos": 3},
            {"grid_h": 10, "grid_w": 16, "n_frames": 2, "inside_twos": 4, "outside_twos": 1},
            {"grid_h": 14, "grid_w": 12, "n_frames": 2, "inside_twos": 2, "outside_twos": 3},
        )
        for band in ("easy", "medium", "hard"):
            for case_index, overrides in enumerate(boundary_cases):
                for seed in range(4):
                    grid = MODULE.generate(
                        1000 + seed,
                        2000 + case_index,
                        difficulty=band,
                        **overrides,
                    )
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertEqual(MODULE.observe_overrides(grid), overrides)

    def test_invalid_overrides_reject_loudly(self):
        for overrides in (
            {"grid_h": 9},
            {"grid_h": 15},
            {"grid_w": 11},
            {"grid_w": 17},
            {"n_frames": 1},
            {"n_frames": 3},
            {"inside_twos": 1},
            {"inside_twos": 5},
            {"outside_twos": 0},
            {"outside_twos": 4},
            {"texture": "canonical"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")

    def test_default_linked_census_covers_rule_and_shortcut_rebuttals(self):
        for band in ("easy", "medium", "hard"):
            inputs = set()
            outputs = set()
            canonical_like = 0
            inside_totals = Counter()
            outside_totals = Counter()
            frame_shapes = set()
            frame_positions = set()
            per_frame_allocations = set()
            for seed in range(240):
                grid = MODULE.generate(seed + 5000, seed * 29 + 7, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                output = MODULE.rule_mirror(grid)
                profile = MODULE.semantic_profile(grid)
                changed = {
                    (r, c)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if output[r][c] != value
                }
                expected_changed = {
                    (r, c)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value == 2
                    and any(frame.contains_strictly(r, c) for frame in MODULE.find_frames(grid)[0])
                }
                self.assertEqual(changed, expected_changed)
                self.assertEqual(len(changed), profile["inside_twos"])
                self.assertGreater(profile["outside_twos"], 0)
                self.assertTrue(
                    all(
                        grid[r][c] == output[r][c] == 2
                        for r, row in enumerate(grid)
                        for c, value in enumerate(row)
                        if value == 2
                        and not any(
                            frame.contains_strictly(r, c)
                            for frame in MODULE.find_frames(grid)[0]
                        )
                    )
                )
                canonical_like += int(MODULE.canonical_like(grid))
                inside_totals[profile["inside_twos"]] += 1
                outside_totals[profile["outside_twos"]] += 1
                frame_shapes.add(profile["frame_signatures"])
                per_frame_allocations.add(tuple(sorted(profile["inside_counts"])))
                frames, _ = MODULE.find_frames(grid)
                frame_positions.add(tuple((f.r1, f.c1, f.r2, f.c2) for f in frames))
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, output)))

            self.assertGreaterEqual(canonical_like, 60)
            self.assertGreaterEqual(len(inputs), 235)
            self.assertGreaterEqual(len(outputs), 235)
            self.assertGreaterEqual(len(frame_shapes), 8)
            self.assertGreaterEqual(len(frame_positions), 100)
            if band in ("easy", "medium"):
                self.assertIn(2, inside_totals)
            if band in ("medium", "hard"):
                self.assertIn(4, inside_totals)
            self.assertGreaterEqual(len(outside_totals), 2)
            if band in ("easy", "medium"):
                self.assertIn((1, 1), per_frame_allocations)
            self.assertTrue(any(max(values) >= 2 for values in per_frame_allocations))

    def test_every_three_example_lesson_contains_multi_red_witness(self):
        for band in ("easy", "medium", "hard"):
            for start in range(30):
                profiles = [
                    MODULE.semantic_profile(
                        MODULE.generate(777, start + offset, difficulty=band)
                    )
                    for offset in range(3)
                ]
                self.assertTrue(all(profile["outside_twos"] >= 1 for profile in profiles))
                self.assertTrue(any(profile["inside_twos"] >= 3 for profile in profiles))

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260724)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)
        self.assertNotEqual(second, MODULE.generate(98, 103, difficulty="hard"))
        self.assertNotEqual(second, MODULE.generate(97, 104, difficulty="hard"))

    def test_self_check_rejects_targeted_impostors_and_local_mutations(self):
        base = MODULE.generate(
            451,
            919,
            difficulty="hard",
            grid_h=12,
            grid_w=14,
            inside_twos=4,
            outside_twos=2,
        )
        frames, _ = MODULE.find_frames(base)

        broken_frame = copy.deepcopy(base)
        r, c = next(iter(frames[0].cells))
        broken_frame[r][c] = 0

        no_outside_distractor = copy.deepcopy(base)
        for r, row in enumerate(no_outside_distractor):
            for c, value in enumerate(row):
                if value == 2 and not any(f.contains_strictly(r, c) for f in frames):
                    no_outside_distractor[r][c] = 0

        empty_second_frame = copy.deepcopy(base)
        for r, c in frames[1].interior():
            if empty_second_frame[r][c] == 2:
                empty_second_frame[r][c] = 0

        fully_filled_interior = copy.deepcopy(base)
        for r, c in frames[0].interior():
            fully_filled_interior[r][c] = 2

        extra_color = copy.deepcopy(base)
        destination = next(
            (r, c)
            for r, row in enumerate(extra_color)
            for c, value in enumerate(row)
            if value == 0 and not any(f.contains_strictly(r, c) for f in frames)
        )
        extra_color[destination[0]][destination[1]] = 3

        extra_irregular_one = copy.deepcopy(base)
        destination = next(
            (r, c)
            for r, row in enumerate(extra_irregular_one)
            for c, value in enumerate(row)
            if value == 0
            and all(abs(r - rr) + abs(c - cc) > 1 for f in frames for rr, cc in f.cells)
        )
        extra_irregular_one[destination[0]][destination[1]] = 1

        ragged = copy.deepcopy(base)
        ragged[0].pop()

        boolean_color = copy.deepcopy(base)
        boolean_color[0][0] = True

        for mutation in (
            broken_frame,
            no_outside_distractor,
            empty_second_frame,
            fully_filled_interior,
            extra_color,
            extra_irregular_one,
            ragged,
            boolean_color,
        ):
            with self.subTest(mutation=mutation):
                self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_negative_recombination_executes_broad_rule_but_is_rejected(self):
        # Replace the second valid frame with an open U-shape while preserving
        # red counts. The broad rule mirror can execute and recolor the first
        # frame, but the lesson distribution rejects the malformed enclosure.
        grid = MODULE.generate(
            811,
            1217,
            difficulty="medium",
            grid_h=11,
            grid_w=13,
            inside_twos=2,
            outside_twos=2,
        )
        frames, _ = MODULE.find_frames(grid)
        malformed = copy.deepcopy(grid)
        r, c = next(iter(frames[1].cells))
        malformed[r][c] = 0
        output = MODULE.rule_mirror(malformed)
        self.assertNotEqual(output, malformed)
        self.assertTrue(MODULE.self_check(malformed))


if __name__ == "__main__":
    unittest.main()
