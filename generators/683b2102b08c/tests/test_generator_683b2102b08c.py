"""Focused semantic regressions for generator 683b2102b08c."""

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
TASK_ID = "683b2102b08c"
BASE_PATHS = (
    ROOT
    / "data/base/solutions/training/dc46ea44__683b2102b08c.json",
    ROOT
    / "data/base/solutions/augmented/dc46ea44__5cad013a710b.json",
)


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_rows():
    return [
        row
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    ]


def bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    line_row = next(
        row
        for row in range(height)
        if all(grid[row][col] == 4 for col in range(width))
    )
    cells_by_color = {}
    for row in range(line_row + 1, height):
        for col in range(width):
            value = grid[row][col]
            if value not in (4, 7):
                cells_by_color.setdefault(value, []).append((row, col))
    ranked = sorted(
        cells_by_color.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    main_color, main_cells = ranked[0]
    secondary_color, secondary_cells = ranked[1]
    main_r1, main_c1, main_r2, _ = bbox(main_cells)
    sec_r1, sec_c1, sec_r2, sec_c2 = bbox(secondary_cells)
    main_height = main_r2 - main_r1 + 1
    secondary_height = sec_r2 - sec_r1 + 1
    secondary_width = sec_c2 - sec_c1 + 1
    output = [[7 for _ in row] for row in grid]
    output[line_row] = [4] * width
    for row, col in main_cells:
        output[row - main_r1][col] = main_color
    target_row = (main_height - secondary_height) // 2
    target_col = main_c1 + 1 - secondary_width
    for row, col in secondary_cells:
        output[target_row + row - sec_r1][target_col + col - sec_c1] = (
            secondary_color
        )
    return output


class Generator683B2102B08CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_all_canonical_occurrences_and_linked_profiles(self):
        rows = canonical_rows()
        self.assertEqual(2, len(rows))
        occurrences = [
            pair for row in rows for pair in row["train"] + row["test"]
        ]
        self.assertEqual(8, len(occurrences))
        profiles = set()
        for pair in occurrences:
            with self.subTest(source=pair["input"][0][0]):
                grid = copy.deepcopy(pair["input"])
                analysis = self.module._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual("linked", analysis["facts"]["family"])
                profiles.add(analysis["facts"]["linked_profile"])
                self.assertEqual(pair["output"], independent_rule(grid))
                self.assertEqual(pair["output"], self.module.rule_mirror(grid))
                self.assertEqual(pair["input"], grid)
        self.assertEqual(
            {
                "public_train_1",
                "public_train_2",
                "public_train_3",
                "public_test_1",
            },
            profiles,
        )

    def test_all_rule_sources_are_text_synced_and_pinned(self):
        rows = canonical_rows()
        canonical = rows[0]["program_solution"]
        self.assertEqual(canonical, rows[1]["program_solution"])
        self.assertEqual("0afee0287491", normalized_hash(canonical))
        self.assertEqual(normalized_hash(canonical), self.module.RULE_HASH)
        for path in BASE_PATHS:
            target = json.loads(path.read_text(encoding="utf-8"))[
                "racket_target"
            ]["target_code"]
            self.assertEqual(canonical, target)

    def test_forced_families_and_every_profile(self):
        linked_profiles = set()
        generalized_profiles = set()
        overlap_seen = no_overlap_seen = 0
        split_main_seen = split_secondary_seen = 0
        for band in ("easy", "medium", "hard"):
            for family in ("linked", "generalized"):
                for sample_index in range(300):
                    grid = self.module.generate(
                        100_000 + sample_index,
                        sample_index * 17 + 5,
                        difficulty=band,
                        scene_family=family,
                    )
                    before = copy.deepcopy(grid)
                    analysis = self.module._analyze(grid)
                    self.assertEqual([], analysis["errors"])
                    facts = analysis["facts"]
                    self.assertEqual(family, facts["family"])
                    self.assertEqual(
                        {"scene_family": family},
                        self.module.observe_overrides(grid),
                    )
                    self.assertEqual(independent_rule(grid), facts["output"])
                    self.assertEqual(before, grid)
                    overlap_seen += facts["collision_count"] > 0
                    no_overlap_seen += facts["collision_count"] == 0
                    split_main_seen += facts["main_component_count"] >= 2
                    split_secondary_seen += (
                        facts["secondary_component_count"] >= 2
                    )
                    if family == "linked":
                        linked_profiles.add(facts["linked_profile"])
                    else:
                        generalized_profiles.add(
                            facts["generalized_profile"]
                        )
        self.assertEqual(
            {
                "public_train_1",
                "public_train_2",
                "public_train_3",
                "public_test_1",
            },
            linked_profiles,
        )
        self.assertEqual(
            set(self.module.GENERAL_PROFILES), generalized_profiles
        )
        self.assertGreater(overlap_seen, 500)
        self.assertGreater(no_overlap_seen, 200)
        self.assertGreater(split_main_seen, 100)
        self.assertGreater(split_secondary_seen, 100)

    def test_row_normalization_and_secondary_input_position_invariance(self):
        grid = self.module.generate(
            333,
            444,
            difficulty="hard",
            scene_family="generalized",
        )
        facts = self.module._analyze(grid)["facts"]
        shifted = copy.deepcopy(grid)
        movable = list(facts["main_cells"]) + list(facts["secondary_cells"])
        if max(row for row, _ in movable) + 1 >= len(grid):
            self.skipTest("selected layout has no lower-row shift room")
        for row, col in movable:
            shifted[row][col] = 7
        for row, col in facts["main_cells"]:
            shifted[row + 1][col] = facts["main_color"]
        for row, col in facts["secondary_cells"]:
            shifted[row + 1][col] = facts["secondary_color"]
        self.assertEqual([], self.module._analyze(shifted)["errors"])
        self.assertEqual(independent_rule(grid), independent_rule(shifted))

        # Moving the lower secondary mask does not change its packed output.
        moved = copy.deepcopy(grid)
        for row, col in facts["secondary_cells"]:
            moved[row][col] = 7
        min_row, min_col, max_row, max_col = facts["secondary_bbox"]
        delta_col = -1 if min_col > 0 else 1
        candidates = {
            (row, col + delta_col)
            for row, col in facts["secondary_cells"]
        }
        if any(
            not 0 <= col < len(grid[0])
            or moved[row][col] != 7
            for row, col in candidates
        ):
            self.skipTest("selected layout has no secondary horizontal shift")
        for row, col in candidates:
            moved[row][col] = facts["secondary_color"]
        self.assertEqual([], self.module._analyze(moved)["errors"])
        self.assertEqual(independent_rule(grid), independent_rule(moved))

    def test_frequency_swap_changes_main_role(self):
        grid = [
            [7] * 12 for _ in range(12)
        ]
        grid[5] = [4] * 12
        for row, col in ((6, 7), (7, 7), (8, 6), (8, 7), (9, 6)):
            grid[row][col] = 1
        for row, col in ((7, 2), (8, 2), (8, 3)):
            grid[row][col] = 3
        first = self.module._analyze(grid)
        self.assertEqual([], first["errors"])
        self.assertEqual(1, first["facts"]["main_color"])

        swapped = copy.deepcopy(grid)
        for row, col in ((6, 1), (7, 1), (9, 2)):
            swapped[row][col] = 3
        second = self.module._analyze(swapped)
        self.assertEqual([], second["errors"])
        self.assertEqual(3, second["facts"]["main_color"])
        self.assertNotEqual(
            independent_rule(grid), independent_rule(swapped)
        )

    def test_secondary_overwrites_on_output_overlap(self):
        rows = canonical_rows()
        pair = rows[0]["train"][0]
        facts = self.module._analyze(pair["input"])["facts"]
        self.assertEqual(1, facts["collision_count"])
        output = self.module.rule_mirror(pair["input"])
        self.assertEqual(pair["output"], output)
        main_r1, _, _, _ = facts["main_bbox"]
        sec_r1, sec_c1, _, _ = facts["secondary_bbox"]
        main_targets = {
            (row - main_r1, col)
            for row, col in facts["main_cells"]
        }
        secondary_targets = {
            (
                facts["target_secondary_r1"] + row - sec_r1,
                facts["target_secondary_c1"] + col - sec_c1,
            )
            for row, col in facts["secondary_cells"]
        }
        overlaps = main_targets & secondary_targets
        self.assertEqual(1, len(overlaps))
        overlap_row, overlap_col = next(iter(overlaps))
        self.assertEqual(
            facts["secondary_color"],
            output[overlap_row][overlap_col],
        )

    def test_natural_prior_diversity_and_difficulty(self):
        shape_sets = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            profiles = set()
            inputs = set()
            outputs = set()
            shapes = set()
            for sample_index in range(800):
                grid = self.module.generate(
                    600_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[facts["family"]] += 1
                profiles.add(
                    facts["linked_profile"]
                    or facts["generalized_profile"]
                )
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertGreaterEqual(families["linked"], 180)
            self.assertGreaterEqual(families["generalized"], 480)
            self.assertEqual(11, len(profiles))
            self.assertGreaterEqual(len(inputs), 770)
            self.assertGreaterEqual(len(outputs), 770)
            shape_sets[band] = shapes
        self.assertNotEqual(shape_sets["easy"], shape_sets["medium"])
        self.assertNotEqual(shape_sets["medium"], shape_sets["hard"])

    def test_self_check_rejects_semantic_impostors(self):
        valid = self.module.generate(
            91,
            92,
            difficulty="medium",
            scene_family="generalized",
        )
        impostors = {
            "all_background": [[7] * 11 for _ in range(11)],
            "no_shapes": [
                [4 if row == 5 else 7 for _ in range(11)]
                for row in range(11)
            ],
            "top_noise": copy.deepcopy(valid),
            "second_separator": copy.deepcopy(valid),
            "bad_value": copy.deepcopy(valid),
            "ragged": [row[:] for row in valid[:-1]] + [valid[-1][:-1]],
            "boolean": copy.deepcopy(valid),
        }
        impostors["top_noise"][0][0] = 1
        impostors["second_separator"][1] = [4] * len(valid[0])
        impostors["bad_value"][0][0] = 10
        impostors["boolean"][0][0] = True
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        second = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        second[0][0] = 1
        third = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, third)
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, unknown_axis="x")
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, scene_family="wrong")


if __name__ == "__main__":
    unittest.main()
