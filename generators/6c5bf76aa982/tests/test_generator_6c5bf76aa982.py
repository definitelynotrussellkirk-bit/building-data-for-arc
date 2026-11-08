"""Focused semantic tests for generator 6c5bf76aa982."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest


for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import (  # noqa: E402
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
TASK_ID = "6c5bf76aa982"


def canonical_row() -> dict:
    path = canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def components(grid: list[list[int]]) -> list[dict]:
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if not (
                        0 <= next_row < height
                        and 0 <= next_col < width
                    ):
                        continue
                    if (
                        (next_row, next_col) in seen
                        or grid[next_row][next_col] != color
                    ):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            found.append({"color": color, "cells": tuple(cells)})
    return found


def touch_count(cells, height: int, width: int) -> int:
    return sum(
        (
            any(row == 0 for row, _ in cells),
            any(row == height - 1 for row, _ in cells),
            any(col == 0 for _, col in cells),
            any(col == width - 1 for _, col in cells),
        )
    )


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    for obj in components(grid):
        if (
            obj["color"] == 7
            and touch_count(obj["cells"], height, width) == 1
        ):
            for row, col in obj["cells"]:
                output[row][col] = 3
    return output


class Generator6c5bf76aa982Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_selected_generator(TASK_ID, root=ROOT)[0]
        cls.row = canonical_row()
        cls.pairs = load_canonical_pairs(
            TASK_ID,
            root=ROOT,
            labeled_only=True,
        )
        cls.public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.pairs
        }

    def test_metadata_has_only_observable_exact_axes(self) -> None:
        self.assertEqual(self.module.VERSION, "2.0.0")
        self.assertEqual(self.module.RULE_HASH, "7bcfd291ec7c")
        self.assertEqual(
            set(self.module.AXES),
            {"scene_profile", "transform"},
        )
        self.assertEqual(
            set(
                self.module.AXES["scene_profile"]["valid"].split("|")
            ),
            set(self.module.SCENE_PROFILES),
        )
        self.assertEqual(self.module.AXES["transform"]["valid"], "0..7")

    def test_all_public_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 5)
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                observed = self.module.observe_overrides(source)
                self.assertEqual(
                    observed["scene_profile"],
                    self.module.PUBLIC_PROFILES[index],
                )
                self.assertIn(observed["transform"], range(8))
                self.assertEqual(
                    self.module.solve_python(source),
                    pair["output"],
                )
                self.assertEqual(
                    independent_rule(source),
                    pair["output"],
                )
                self.assertEqual(source, pair["input"])

    def test_every_exact_axis_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile in self.module.SCENE_PROFILES:
                for transform in range(8):
                    with self.subTest(
                        band=band,
                        profile=profile,
                        transform=transform,
                    ):
                        grid = self.module.generate(
                            1_000 + transform,
                            37 * transform,
                            difficulty=band,
                            scene_profile=profile,
                            transform=transform,
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "transform": transform,
                            },
                        )
                        self.assertEqual(
                            self.module.solve_python(grid),
                            independent_rule(grid),
                        )

    def test_exact_component_counts_never_shed_under_stress(self) -> None:
        orange_counts = {
            "public_9x10": {3},
            "public_10x10": {4},
            "public_8x11": {5},
            "public_9x9": {5},
            "public_10x12": {5},
            "balanced_small": {3, 4, 5, 6},
            "all_sides": {5, 6},
            "role_alias": {3, 4},
        }
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            for profile in self.module.SCENE_PROFILES:
                for sample_index in range(200):
                    grid = self.module.generate(
                        20_000 + band_index,
                        sample_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["reasons"], [])
                    self.assertIn(
                        analysis["orange_component_count"],
                        orange_counts[profile],
                    )
                    if profile == "role_alias":
                        self.assertIn(
                            analysis["distractor_component_count"],
                            (1, 2),
                        )

    def test_default_prior_is_calibrated_diverse_and_complete(self) -> None:
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            profiles = Counter()
            answer_profiles = Counter()
            palettes = set()
            pairs = set()
            for sample_index in range(1_000):
                grid = self.module.generate(
                    30_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                self.assertEqual(self.module.self_check(grid), [])
                observed = self.module.observe_overrides(grid)
                profiles[observed["scene_profile"]] += 1
                canonical = self.module._analyze(grid)[
                    "canonical_answer_profile"
                ]
                if canonical is not None:
                    answer_profiles[canonical] += 1
                palettes.update(value for row in grid for value in row)
                output = independent_rule(grid)
                self.assertEqual(self.module.solve_python(grid), output)
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    )
                )
            self.assertEqual(
                set(profiles),
                set(self.module.SCENE_PROFILES),
            )
            self.assertEqual(
                set(answer_profiles),
                set(self.module.PUBLIC_PROFILES),
            )
            self.assertGreaterEqual(sum(answer_profiles.values()), 180)
            self.assertLessEqual(sum(answer_profiles.values()), 320)
            self.assertEqual(palettes, set(range(10)))
            self.assertGreaterEqual(len(pairs), 700)

    def test_default_generation_never_replays_a_public_literal(self) -> None:
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            for sample_index in range(1_000):
                grid = self.module.generate(
                    40_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                self.assertNotIn(
                    json.dumps(grid, separators=(",", ":")),
                    self.public_inputs,
                )

    def test_self_check_rejects_shortcuts_and_malformed_scenes(self) -> None:
        only_target = [[0 for _ in range(9)] for _ in range(9)]
        only_target[0][3] = only_target[1][3] = 7
        only_interior = [[0 for _ in range(9)] for _ in range(9)]
        for offset in range(3):
            only_interior[4][3 + offset] = 7
        oversized = [[0 for _ in range(9)] for _ in range(9)]
        for col in range(5):
            oversized[0][2 + col] = 7
        oversized[4][4] = oversized[4][5] = 7
        oversized[7][7] = oversized[7][8] = 7
        three_border = [[0 for _ in range(9)] for _ in range(9)]
        for row in range(9):
            three_border[row][0] = 7
        three_border[4][4] = three_border[4][5] = 7
        three_border[7][7] = three_border[7][8] = 7
        too_many_distractors = self.module.generate(
            61,
            9,
            scene_profile="balanced_small",
        )
        for row, col, color in ((0, 0, 1), (0, 2, 2), (0, 4, 4)):
            too_many_distractors[row][col] = color

        invalid = (
            ("only_target", only_target),
            ("only_interior", only_interior),
            ("oversized", oversized),
            ("three_border", three_border),
            ("too_many_distractors", too_many_distractors),
            ("dimension", [[0 for _ in range(14)] for _ in range(14)]),
            ("ragged", [[0, 7], [0]]),
            ("boolean", [[False for _ in range(9)] for _ in range(9)]),
            ("out_of_range", [[10 for _ in range(9)] for _ in range(9)]),
        )
        for name, grid in invalid:
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_broad_oracle_uses_components_color_and_border_count(self) -> None:
        grid = [[0 for _ in range(7)] for _ in range(6)]
        grid[0][2] = grid[1][2] = grid[1][3] = 7
        grid[2][0] = grid[3][0] = 7
        grid[5][5] = grid[5][6] = 7
        grid[0][0] = 3
        grid[3][3] = grid[3][4] = 4
        before = copy.deepcopy(grid)
        expected = independent_rule(grid)
        self.assertEqual(self.module.solve_python(grid), expected)
        self.assertEqual(grid, before)
        self.assertEqual(expected[0][2], 3)
        self.assertEqual(expected[2][0], 3)
        self.assertEqual(expected[5][5], 7)
        self.assertEqual(expected[0][0], 3)
        self.assertEqual(expected[3][3], 4)
        self.assertTrue(self.module.self_check(grid))

    def test_python_determinism_fresh_returns_and_rng_isolation(self) -> None:
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="role_alias",
            transform=7,
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="role_alias",
            transform=7,
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(
                first_row is not second_row
                for first_row, second_row in zip(first, second)
            )
        )
        first[0][0] = (first[0][0] + 1) % 10
        third = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="role_alias",
            transform=7,
        )
        self.assertEqual(second, third)

    def test_unknown_and_invalid_overrides_reject(self) -> None:
        for overrides in (
            {"unknown": 1},
            {"scene_profile": "not-a-profile"},
            {"transform": -1},
            {"transform": 8},
            {"transform": True},
            {"transform": 1.5},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self.module.generate(1, 2, **overrides)

    def test_base_and_canonical_sources_are_synchronized(self) -> None:
        program = self.row["program_solution"]
        expected_hash = normalized_rule_hash(program)
        self.assertEqual(
            expected_hash,
            "7bcfd291ec7c790d03e86fe0197529edd7faa4861d68cc2709b26c65875096f8",
        )
        relative = Path(
            "base/solutions/banks/385e738e9e70/E96__6c5bf76aa982.json"
        )
        base_path = next(
            (
                candidate
                for candidate in (
                    ROOT / "data" / relative,
                    ROOT / "shared" / "data" / relative,
                )
                if candidate.is_file()
            ),
            None,
        )
        self.assertIsNotNone(base_path)
        base = json.loads(base_path.read_text(encoding="utf-8"))
        self.assertEqual(base["racket_target"]["raw_code"], program)
        self.assertEqual(base["racket_target"]["target_code"], program)


if __name__ == "__main__":
    unittest.main()
