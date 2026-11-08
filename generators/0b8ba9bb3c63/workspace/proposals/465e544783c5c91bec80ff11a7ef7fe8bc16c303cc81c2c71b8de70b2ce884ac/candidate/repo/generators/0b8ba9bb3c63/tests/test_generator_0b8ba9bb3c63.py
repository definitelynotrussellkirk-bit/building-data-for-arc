"""Focused semantic tests for generator 0b8ba9bb3c63."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest
from unittest import mock

from reviewer_support import canonical_path, find_root, load_selected_generator
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
TASK_ID = "0b8ba9bb3c63"
FULL_RULE_HASH = (
    "757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb"
)


def canonical_rows() -> list[dict]:
    rows = []
    path = canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 2:
        raise AssertionError(f"expected two canonical rows, found {len(rows)}")
    return rows


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def components4(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for row_delta, col_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_cell = current[0] + row_delta, current[1] + col_delta
                    if not (
                        0 <= next_cell[0] < height
                        and 0 <= next_cell[1] < width
                        and next_cell not in seen
                        and grid[next_cell[0]][next_cell[1]] == color
                    ):
                        continue
                    seen.add(next_cell)
                    stack.append(next_cell)
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            objects.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return objects


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Straight transcription of the written beam/blocker semantics."""
    objects = components4(grid)
    cyan = next(obj for obj in objects if obj["color"] == 8)
    blockers = [obj for obj in objects if obj["color"] not in (2, 8)]
    row1, col1, row2, col2 = cyan["bbox"]
    height, width = len(grid), len(grid[0])
    output = copy.deepcopy(grid)

    for row in range(row1, row2 + 1):
        left = [obj for obj in blockers if obj["bbox"][0] <= row <= obj["bbox"][2] and obj["bbox"][3] < col1]
        right = [obj for obj in blockers if obj["bbox"][0] <= row <= obj["bbox"][2] and obj["bbox"][1] > col2]
        first_col = max((obj["bbox"][1] for obj in left), default=0)
        last_col = min((obj["bbox"][3] for obj in right), default=width - 1)
        for col in range(first_col, last_col + 1):
            if not col1 <= col <= col2:
                output[row][col] = 4

    for col in range(col1, col2 + 1):
        above = [obj for obj in blockers if obj["bbox"][1] <= col <= obj["bbox"][3] and obj["bbox"][2] < row1]
        below = [obj for obj in blockers if obj["bbox"][1] <= col <= obj["bbox"][3] and obj["bbox"][0] > row2]
        first_row = max((obj["bbox"][0] for obj in above), default=0)
        last_row = min((obj["bbox"][2] for obj in below), default=height - 1)
        for row in range(first_row, last_row + 1):
            if not row1 <= row <= row2:
                output[row][col] = 4

    for row, col in cyan["cells"]:
        output[row][col] = 8
    for blocker in blockers:
        for row, col in blocker["cells"]:
            output[row][col] = blocker["color"]
    return output


class Generator0b8ba9bb3c63Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_selected_generator(TASK_ID, root=ROOT)[0]
        cls.rows = canonical_rows()
        cls.pairs = [pair for row in cls.rows for pair in row["train"] + row["test"]]
        cls.public_inputs = {
            json.dumps(pair["input"], separators=(",", ":")) for pair in cls.pairs
        }

    def test_metadata_pins_rule_and_only_observable_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "4.1.0")
        self.assertEqual(self.module.RULE_HASH, FULL_RULE_HASH[:12])
        self.assertEqual(set(self.module.AXES), {"scene_family"})
        self.assertEqual(self.module.AXES["scene_family"]["valid"], "public|generalized")

    def test_all_twelve_canonical_occurrences_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 12)
        self.assertEqual(len(self.public_inputs), 6)
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(self.module.canonical_profile_signature(source), "public")
                self.assertEqual(self.module.observe_overrides(source), {"scene_family": "public"})
                self.assertEqual(self.module.rule_mirror(source), pair["output"])
                self.assertEqual(independent_rule(source), pair["output"])
                self.assertEqual(source, pair["input"])

    def test_exact_family_axis_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for family in ("public", "generalized"):
                for sample_index in range(100):
                    grid = self.module.generate(
                        10_000 + sample_index,
                        sample_index,
                        difficulty=band,
                        scene_family=family,
                    )
                    self.assertEqual(self.module.self_check(grid), [])
                    self.assertEqual(
                        self.module.observe_overrides(grid), {"scene_family": family}
                    )
                    self.assertEqual(self.module.rule_mirror(grid), independent_rule(grid))

    def test_natural_prior_is_balanced_and_diverse(self) -> None:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            pairs = set()
            blocker_colors = set()
            for sample_index in range(1_000):
                grid = self.module.generate(20_000 + band_index, sample_index, difficulty=band)
                self.assertEqual(self.module.self_check(grid), [])
                family = self.module.observe_overrides(grid)["scene_family"]
                families[family] += 1
                blocker_colors.update(
                    obj["color"]
                    for obj in components4(grid)
                    if obj["color"] not in (2, 8)
                )
                output = self.module.rule_mirror(grid)
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, output))))
            self.assertGreaterEqual(families["public"], 330)
            self.assertLessEqual(families["public"], 470)
            self.assertEqual(set(families), {"public", "generalized"})
            self.assertEqual(blocker_colors, {1, 3, 5, 6, 7, 9})
            self.assertGreaterEqual(len(pairs), 990)

    def test_generation_does_not_replay_a_canonical_input(self) -> None:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for sample_index in range(500):
                grid = self.module.generate(30_000 + band_index, sample_index, difficulty=band)
                self.assertNotIn(json.dumps(grid, separators=(",", ":")), self.public_inputs)

    def test_cross_profile_recombination_is_not_mislabeled_public(self) -> None:
        # Start from official profile 0 (4x4 cyan, 2 red, 1 blocker), then
        # splice in the role counts from profile 1 (6 red, 4 blockers).  Every
        # former independent range still passes, but the linked tuple is not an
        # official profile and must therefore leave the public family.
        grid = copy.deepcopy(self.rows[0]["train"][0]["input"])
        for color, count in ((2, 4), (1, 3)):
            for _ in range(count):
                placed = False
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        if self.module._rect_clear(grid, row, col, 1, 1):
                            self.module._paint_rect(grid, row, col, 1, 1, color)
                            placed = True
                            break
                    if placed:
                        break
                self.assertTrue(placed)
        self.assertEqual(self.module.self_check(grid), [])
        facts = self.module._analyze(grid)["facts"]
        self.assertEqual(facts["cyan_size"], (4, 4))
        self.assertEqual((facts["red_count"], facts["blocker_count"]), (6, 4))
        self.assertEqual(self.module.canonical_profile_signature(grid), "generalized")

    def test_self_check_rejects_structural_shortcuts(self) -> None:
        valid = self.module.generate(
            73, 19, difficulty="medium", scene_family="generalized"
        )
        yellow_input = copy.deepcopy(valid)
        yellow_input[0][0] = 4
        no_red = [[0 if value == 2 else value for value in row] for row in valid]
        no_cyan = [[0 if value == 8 else value for value in row] for row in valid]
        broken_cyan = copy.deepcopy(valid)
        cyan_cell = next(
            (row, col)
            for row, values in enumerate(broken_cyan)
            for col, value in enumerate(values)
            if value == 8
        )
        broken_cyan[cyan_cell[0]][cyan_cell[1]] = 0
        no_blocker = [
            [0 if value not in (0, 2, 8) else value for value in row]
            for row in valid
        ]
        non_rectangular = [row[:-1] if index == 0 else row for index, row in enumerate(valid)]
        too_short = copy.deepcopy(valid[:10])
        too_tall = copy.deepcopy(valid) + [copy.deepcopy(valid[-1]) for _ in range(31 - len(valid))]
        all_background = [[0 for _col in range(15)] for _row in range(15)]
        for name, grid in (
            ("yellow_input", yellow_input),
            ("no_red", no_red),
            ("no_cyan", no_cyan),
            ("broken_cyan", broken_cyan),
            ("no_blocker", no_blocker),
            ("non_rectangular", non_rectangular),
            ("dimension_min_minus_one", too_short),
            ("dimension_max_plus_one", too_tall),
            ("all_background", all_background),
        ):
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_determinism_fresh_returns_rng_and_checker_observation(self) -> None:
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            77, 88, difficulty="hard", scene_family="generalized"
        )
        self.assertEqual(random.getstate(), state)
        before_check = copy.deepcopy(first)
        self.assertEqual(self.module.self_check(first), [])
        self.assertEqual(first, before_check)
        second = self.module.generate(
            77, 88, difficulty="hard", scene_family="generalized"
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        third = self.module.generate(
            77, 88, difficulty="hard", scene_family="generalized"
        )
        self.assertEqual(second, third)

    def test_invalid_difficulty_and_overrides_reject(self) -> None:
        for difficulty, overrides in (
            ("impossible", {}),
            (None, {"unknown": 1}),
            (None, {"scene_family": "not-a-family"}),
            (None, {"scene_family": True}),
        ):
            with self.subTest(difficulty=difficulty, overrides=overrides):
                with self.assertRaises(ValueError):
                    self.module.generate(1, 2, difficulty=difficulty, **overrides)

    def test_exhausted_layout_fails_closed_without_global_rng_mutation(self) -> None:
        random.seed(161_803)
        state = random.getstate()
        with mock.patch.object(
            self.module, "_place_directional_blocker", return_value=False
        ):
            with self.assertRaisesRegex(RuntimeError, "could not construct"):
                self.module._construct_scene(random.Random(99), "medium", "public")
        self.assertEqual(random.getstate(), state)

    def test_canonical_grounded_and_base_rule_sources_are_synchronized(self) -> None:
        programs = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(programs), 1)
        program = programs.pop()
        self.assertEqual(normalized_rule_hash(program), FULL_RULE_HASH)
        self.assertEqual(normalized_rule_hash(GROUNDED_RULES[TASK_ID]), FULL_RULE_HASH)
        for source, content_hash in (
            ("training", "0b8ba9bb3c63"),
            ("augmented", "7a159f50b0e0"),
        ):
            path = (
                (ROOT / "shared/data" if (ROOT / "shared/data").is_dir() else ROOT / "data") / "base" / "solutions" / source
                / f"6ffe8f07__{content_hash}.json"
            )
            base = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(normalized_rule_hash(base["racket_target"]["raw_code"]), FULL_RULE_HASH)
            self.assertEqual(base["racket_target"]["target_code"], program)


if __name__ == "__main__":
    unittest.main()
