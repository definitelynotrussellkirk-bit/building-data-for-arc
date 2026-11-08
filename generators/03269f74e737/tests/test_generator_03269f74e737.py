"""Focused semantic regressions for generator 03269f74e737."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "03269f74e737"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/9da77d17d00f/S20_M3__03269f74e737.json"
)


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    divider = next(
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    )
    left = [row[:divider] for row in grid]
    board = [list(row[divider + 1 :]) for row in grid]
    cells = [
        (row, col, left[row][col])
        for row in range(height)
        for col in range(divider)
        if left[row][col] not in (0, 9)
    ]
    min_row = min(row for row, _, _ in cells)
    max_row = max(row for row, _, _ in cells)
    min_col = min(col for _, col, _ in cells)
    max_col = max(col for _, col, _ in cells)
    template = [
        left[row][min_col : max_col + 1]
        for row in range(min_row, max_row + 1)
    ]
    template_height = len(template)
    template_width = len(template[0])
    repairs = []
    for row in range(height - template_height + 1):
        for col in range(len(board[0]) - template_width + 1):
            missing = []
            valid = True
            for trow in range(template_height):
                for tcol in range(template_width):
                    template_value = template[trow][tcol]
                    board_value = board[row + trow][col + tcol]
                    if template_value == 0:
                        valid &= board_value == 0
                    elif board_value == 0:
                        missing.append(
                            (row + trow, col + tcol, template_value)
                        )
                    else:
                        valid &= board_value == template_value
            if valid and len(missing) == 1:
                repairs.extend(missing)
    for row, col, value in repairs:
        board[row][col] = value
    return board


class Generator03269f74e737Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_all_canonical_pairs_and_linked_profiles(self):
        row = canonical_row()
        self.assertEqual(len(row["train"]), 2)
        self.assertIsInstance(row["test"], dict)
        pairs = row["train"] + [row["test"]]
        expected_profiles = (
            "public_train_1",
            "public_train_2",
            "public_test_1",
        )
        for pair, profile in zip(pairs, expected_profiles):
            with self.subTest(profile=profile):
                grid = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(grid), [])
                facts = self.module._analyze(grid)["facts"]
                self.assertEqual(facts["profile"], profile)
                self.assertEqual(facts["family"], "linked")
                self.assertEqual(
                    self.module.rule_mirror(grid), pair["output"]
                )
                self.assertEqual(independent_rule(grid), pair["output"])
                self.assertEqual(grid, pair["input"])

    def test_rule_target_is_pinned(self):
        canonical = canonical_row()["program_solution"]
        target = json.loads(BASE_PATH.read_text())["racket_target"]
        expected = normalized_hash(canonical)[:12]
        self.assertEqual(expected, "d65573c288f6")
        self.assertEqual(self.module.RULE_HASH, expected)
        self.assertEqual(target["target_code"], canonical)

    def test_every_forced_profile_is_exact_and_semantic(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                self.module.SCENE_PROFILES
            ):
                for sample_index in range(40):
                    grid = self.module.generate(
                        100_000 + 10_000 * profile_index + sample_index,
                        sample_index * 13 + 5,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    before = copy.deepcopy(grid)
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(
                        analysis["facts"]["profile"], profile
                    )
                    self.assertEqual(
                        self.module.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        self.module.rule_mirror(grid),
                        independent_rule(grid),
                    )
                    self.assertNotEqual(
                        analysis["facts"]["board"],
                        analysis["facts"]["output"],
                    )
                    self.assertEqual(grid, before)

    def test_near_miss_profiles_remain_untouched(self):
        for profile in (
            "complete_copy",
            "two_hole",
            "wrong_color",
            "rotated_copy",
        ):
            grid = self.module.generate(
                222,
                333,
                difficulty="hard",
                scene_profile=profile,
            )
            facts = self.module._analyze(grid)["facts"]
            board = facts["board"]
            output = facts["output"]
            template = facts["template"]
            if profile == "complete_copy":
                candidates = self.module._scan_windows(
                    board, template, 0
                )
                protected = [
                    (
                        match["row"] + row,
                        match["col"] + col,
                    )
                    for match in candidates
                    for row, col in template
                ]
            elif profile == "two_hole":
                candidates = self.module._scan_windows(
                    board, template, 2
                )
                protected = [
                    (
                        match["row"] + row,
                        match["col"] + col,
                    )
                    for match in candidates
                    for row, col, _ in match["missing"]
                ]
            elif profile == "wrong_color":
                candidates = self.module._scan_windows(
                    board, template, 0, wrong=1
                )
                protected = [
                    (
                        match["row"] + row,
                        match["col"] + col,
                    )
                    for match in candidates
                    for row, col, _ in match["wrong"]
                ]
            else:
                rotated = self.module._rotate_template_cw(template)
                candidates = self.module._scan_windows(
                    board, rotated, 1
                )
                protected = [
                    (
                        match["row"] + row,
                        match["col"] + col,
                    )
                    for match in candidates
                    for row, col, _ in match["missing"]
                ]
            self.assertTrue(candidates)
            for row, col in protected:
                self.assertEqual(output[row][col], board[row][col])

    def test_multicolor_repairs_use_template_values(self):
        repaired_colors = set()
        for sample_index in range(80):
            grid = self.module.generate(
                444,
                sample_index,
                scene_profile="multicolor",
            )
            facts = self.module._analyze(grid)["facts"]
            self.assertEqual(len(set(facts["template"].values())), 2)
            for match in facts["matches"]:
                repaired_colors.update(
                    value for _, _, value in match["missing"]
                )
            self.assertEqual(
                self.module.rule_mirror(grid),
                independent_rule(grid),
            )
        self.assertGreaterEqual(len(repaired_colors), 2)

    def test_natural_prior_diversity_and_difficulty(self):
        dimensions = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            match_counts = Counter()
            inputs = set()
            outputs = set()
            shapes = set()
            for sample_index in range(600):
                grid = self.module.generate(
                    500_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                profiles[facts["profile"]] += 1
                match_counts[facts["match_count"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertEqual(set(profiles), set(self.module.SCENE_PROFILES))
            self.assertTrue(all(count >= 35 for count in profiles.values()))
            self.assertGreaterEqual(
                sum(profiles[name] for name in self.module.PUBLIC_PROFILES),
                140,
            )
            self.assertGreaterEqual(len(inputs), 560)
            self.assertGreaterEqual(len(outputs), 560)
            self.assertGreaterEqual(len(shapes), 8)
            dimensions[band] = (shapes, match_counts)
        self.assertNotEqual(dimensions["easy"], dimensions["medium"])
        self.assertNotEqual(dimensions["medium"], dimensions["hard"])

    def test_self_check_rejects_semantic_impostors(self):
        grid = self.module.generate(
            777, 888, scene_profile="plain"
        )
        facts = self.module._analyze(grid)["facts"]

        zero_divider = copy.deepcopy(grid)
        for row in zero_divider:
            row[facts["divider_col"]] = 0

        extra_divider = copy.deepcopy(grid)
        for row in extra_divider:
            row[0] = 9

        empty_template = copy.deepcopy(grid)
        for row in empty_template:
            for col in range(facts["divider_col"]):
                row[col] = 0

        no_matches = copy.deepcopy(grid)
        for row in no_matches:
            for col in range(facts["divider_col"] + 1, len(row)):
                row[col] = 0

        ragged = copy.deepcopy(grid)
        ragged[0].pop()

        boolean_cell = copy.deepcopy(grid)
        boolean_cell[0][0] = True

        bad_value = copy.deepcopy(grid)
        bad_value[0][0] = 10

        for name, mutation in (
            ("zero_divider", zero_divider),
            ("extra_divider", extra_divider),
            ("empty_template", empty_template),
            ("no_matches", no_matches),
            ("ragged", ragged),
            ("boolean_cell", boolean_cell),
            ("bad_value", bad_value),
        ):
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(mutation))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            999,
            111,
            difficulty="hard",
            scene_profile="rotated_copy",
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            999,
            111,
            difficulty="hard",
            scene_profile="rotated_copy",
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 8
        self.assertEqual(
            second,
            self.module.generate(
                999,
                111,
                difficulty="hard",
                scene_profile="rotated_copy",
            ),
        )
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            self.module.generate(0, 0, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, nonexistent_axis=True)
        with self.assertRaises((ValueError, KeyError)):
            self.module.generate(
                0, 0, scene_profile="unknown_profile"
            )


if __name__ == "__main__":
    unittest.main()
