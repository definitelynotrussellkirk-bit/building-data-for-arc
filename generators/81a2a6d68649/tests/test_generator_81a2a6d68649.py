"""Focused semantic regressions for generator 81a2a6d68649."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "81a2a6d68649"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/f4facb1306bd/E118__81a2a6d68649.json"
)


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def independent_transform(grid):
    result = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 1
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            replacement = 4 if len(rows) == 1 else 7 if len(cols) == 1 else 1
            for cr, cc in cells:
                result[cr][cc] = replacement
    return result


def color_blind_bar_transform(grid):
    """Wrong shortcut: recolor every straight nonzero bar by orientation."""
    result = copy.deepcopy(grid)
    for component in _components_for_test(grid):
        rows = {row for row, _ in component["cells"]}
        cols = {col for _, col in component["cells"]}
        if len(component["cells"]) < 2:
            continue
        replacement = 4 if len(rows) == 1 else 7 if len(cols) == 1 else None
        if replacement is not None:
            for row, col in component["cells"]:
                result[row][col] = replacement
    return result


def _components_for_test(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": cells})
    return components


class Generator81a2a6d68649Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_rule_hash_version_and_axis_are_pinned(self):
        row = canonical_row()
        base = json.loads(BASE_PATH.read_text())
        canonical_source = row["program_solution"]
        target = base["racket_target"]
        self.assertEqual(target["target_code"], canonical_source)
        self.assertEqual(target["raw_code"], canonical_source)
        self.assertEqual(normalized_hash(canonical_source), "0360b462b672")
        self.assertEqual(self.module.RULE_HASH, "0360b462b672")
        self.assertEqual(self.module.VERSION, "3.0.0")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        self.assertEqual(self.module.HELPFUL_TEXTURES, ())
        self.assertEqual(self.module.DEGENERATE_TEXTURES, ())

    def test_all_canonical_pairs_pass_full_checker_and_transform(self):
        expected_profiles = (
            "horizontal_heavy",
            "minimal_mix",
            "vertical_heavy",
            "horizontal_heavy",
            "horizontal_heavy",
        )
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), len(expected_profiles))
        for pair, expected_profile in zip(pairs, expected_profiles):
            with self.subTest(profile=expected_profile):
                original = copy.deepcopy(pair["input"])
                analysis = self.module._analyze(original)
                self.assertEqual(analysis["reasons"], [])
                self.assertEqual(analysis["scene_profile"], expected_profile)
                self.assertEqual(independent_transform(original), pair["output"])
                self.assertEqual(original, pair["input"])

    def test_every_forced_profile_is_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(self.module.SCENE_PROFILES):
                for sample_index in range(20):
                    grid = self.module.generate(
                        100_000 + profile_index * 10_000 + sample_index,
                        sample_index * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    with self.subTest(band=band, profile=profile, sample=sample_index):
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )
                        analysis = self.module._analyze(grid)
                        self.assertGreaterEqual(analysis["horizontal_blue_bars"], 1)
                        self.assertGreaterEqual(analysis["vertical_blue_bars"], 1)
                        self.assertGreaterEqual(len(analysis["distractor_components"]), 1)
                        output = independent_transform(grid)
                        self.assertNotEqual(output, grid)
                        self.assertNotEqual(color_blind_bar_transform(grid), output)
                        for row in range(len(grid)):
                            for col in range(len(grid[0])):
                                if grid[row][col] != 1:
                                    self.assertEqual(output[row][col], grid[row][col])

    def test_default_prior_reaches_every_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            seen = {
                self.module.observe_overrides(
                    self.module.generate(seed, 31 * seed + 7, difficulty=band)
                )["scene_profile"]
                for seed in range(300)
            }
            self.assertEqual(seen, set(self.module.SCENE_PROFILES))

    def test_targeted_impostors_are_rejected(self):
        valid = self.module.generate(
            777,
            13,
            difficulty="medium",
            scene_profile="minimal_mix",
        )
        impostors = {}

        impostors["all_background"] = [
            [0 for _ in row]
            for row in valid
        ]

        no_distractor = copy.deepcopy(valid)
        for row in range(len(no_distractor)):
            for col in range(len(no_distractor[0])):
                if no_distractor[row][col] not in (0, 1):
                    no_distractor[row][col] = 0
        impostors["missing_distractor"] = no_distractor

        no_vertical = copy.deepcopy(valid)
        for component in self.module._analyze(valid)["blue_components"]:
            if component["orientation"] == "vertical":
                for row, col in component["cells"]:
                    no_vertical[row][col] = 0
        impostors["single_orientation"] = no_vertical

        singleton = copy.deepcopy(valid)
        for component in self.module._analyze(valid)["blue_components"]:
            if component["orientation"] == "horizontal":
                for row, col in component["cells"][1:]:
                    singleton[row][col] = 0
                break
        impostors["singleton_blue"] = singleton

        l_shape = [[0 for _ in range(12)] for _ in range(12)]
        for row, col in ((1, 1), (1, 2), (1, 3)):
            l_shape[row][col] = 1
        for row, col in ((1, 9), (2, 9), (3, 9)):
            l_shape[row][col] = 1
        for row, col in ((7, 1), (8, 1), (8, 2)):
            l_shape[row][col] = 1
        l_shape[10][10] = 3
        impostors["bent_blue_component"] = l_shape

        solid_square = [[0 for _ in range(12)] for _ in range(12)]
        for row, col in ((1, 1), (1, 2), (1, 3)):
            solid_square[row][col] = 1
        for row, col in ((1, 9), (2, 9), (3, 9)):
            solid_square[row][col] = 1
        for row in (7, 8):
            for col in (1, 2):
                solid_square[row][col] = 1
        solid_square[10][10] = 8
        impostors["solid_blue_2x2"] = solid_square

        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))
                with self.assertRaises(ValueError):
                    self.module.observe_overrides(grid)

    def test_output_color_and_orientation_decoys_are_not_rule_targets(self):
        for profile in ("output_color_decoys", "orientation_decoys"):
            grid = self.module.generate(
                909,
                27,
                difficulty="hard",
                scene_profile=profile,
            )
            output = independent_transform(grid)
            for component in self.module._analyze(grid)["distractor_components"]:
                for row, col in component["cells"]:
                    self.assertEqual(output[row][col], grid[row][col])

    def test_replay_freshness_and_global_rng_isolation(self):
        random.seed(912_447)
        before = random.getstate()
        first = self.module.generate(321, 654, difficulty="hard")
        after = random.getstate()
        second = self.module.generate(321, 654, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)

    def test_invalid_controls_fail_loudly(self):
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, scene_profile="not_a_profile")
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, unknown_axis=3)
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, difficulty="nightmare")


if __name__ == "__main__":
    unittest.main()
