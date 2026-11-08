"""Focused semantic tests for generator 6b5d8752c5c4."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import random
import unittest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs as reviewer_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)
from solvers.grounded_rules import GROUNDED_RULES


TASK_ID = "6b5d8752c5c4"
ROOT = find_root(__file__)


def canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def racket_grid_literal(grid: list[list[int]]) -> str:
    rows = ["(" + " ".join(map(str, row)) + ")" for row in grid]
    return "'(" + " ".join(rows) + ")"


def components8(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        next_row = current_row + row_delta
                        next_col = current_col + col_delta
                        cell = (next_row, next_col)
                        if (
                            0 <= next_row < height
                            and 0 <= next_col < width
                            and grid[next_row][next_col] != 0
                            and cell not in seen
                        ):
                            seen.add(cell)
                            stack.append(cell)
            result.append(cells)
    return result


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _col in range(width)] for _row in range(height)]
    for cells in components8(grid):
        first_row = min(row for row, _col in cells)
        last_row = max(row for row, _col in cells)
        first_col = min(col for _row, col in cells)
        last_col = max(col for _row, col in cells)
        object_height = last_row - first_row + 1
        object_width = last_col - first_col + 1
        vertical = object_height > object_width
        cut = (object_height if vertical else object_width) // 2
        for row, col in cells:
            if grid[row][col] != 9:
                continue
            if vertical:
                next_row = row + (
                    -1 if row - first_row < cut else 1
                )
                next_col = col
            else:
                next_row = row
                next_col = col + (
                    -1 if col - first_col < cut else 1
                )
            if 0 <= next_row < height and 0 <= next_col < width:
                output[next_row][next_col] = 9
    return output


class Generator6b5d8752c5c4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module, cls.source_path, cls.source_sha256 = load_selected_generator(
            TASK_ID,
            root=ROOT,
        )
        cls.row = canonical_row()
        cls.pairs = reviewer_canonical_pairs(
            TASK_ID,
            root=ROOT,
            variant=0,
            labeled_only=True,
        )
        cls.public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.pairs
        }

    def test_metadata_has_only_observable_exact_axes(self) -> None:
        self.assertEqual(self.module.VERSION, "3.0.0")
        self.assertEqual(self.module.RULE_HASH, "1eb213be2892")
        self.assertEqual(
            set(self.module.AXES),
            {"scene_profile", "cut_color"},
        )
        self.assertEqual(
            set(
                self.module.AXES["scene_profile"]["valid"].split("|")
            ),
            set(self.module.SCENE_PROFILES),
        )
        self.assertEqual(
            self.module.AXES["cut_color"]["valid"],
            "1..8",
        )

    def test_all_public_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 4)
        self.assertEqual(
            self.module.PUBLIC_PROFILES,
            ("public_12", "public_8", "public_16", "public_19"),
        )
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(
                    self.module.canonical_profile_index(source),
                    index,
                )
                self.assertEqual(
                    self.module.observe_overrides(source),
                    {
                        "scene_profile": self.module.PUBLIC_PROFILES[
                            index
                        ],
                        "cut_color": 6,
                    },
                )
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
                for cut_color in range(1, 9):
                    with self.subTest(
                        band=band,
                        profile=profile,
                        cut_color=cut_color,
                    ):
                        grid = self.module.generate(
                            1_000 + cut_color,
                            37 * cut_color,
                            difficulty=band,
                            scene_profile=profile,
                            cut_color=cut_color,
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "cut_color": cut_color,
                            },
                        )
                        self.assertEqual(
                            self.module.solve_python(grid),
                            independent_rule(grid),
                        )

    def test_exact_object_count_never_sheds_under_stress(self) -> None:
        fixed_counts = {
            "public_12": {3},
            "public_8": {1},
            "public_16": {4},
            "public_19": {7},
            "single_bar": {1},
            "paired_bars": {2},
            "edge_bars": {3},
            "mixed_bars": {4, 5, 6},
        }
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            for profile in self.module.SCENE_PROFILES:
                observed_counts = set()
                for sample_index in range(300):
                    grid = self.module.generate(
                        20_000 + band_index,
                        sample_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(self.module.self_check(grid), [])
                    count = len(components8(grid))
                    self.assertIn(count, fixed_counts[profile])
                    observed_counts.add(count)
                if profile == "mixed_bars":
                    self.assertEqual(observed_counts, {4, 5, 6})

    def test_default_prior_is_calibrated_diverse_and_complete(self) -> None:
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            profiles = Counter()
            answer_profiles = Counter()
            colors = set()
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
                answer_index = self.module.canonical_profile_index(grid)
                if answer_index is not None:
                    answer_profiles[
                        self.module.PUBLIC_PROFILES[answer_index]
                    ] += 1
                colors.add(observed["cut_color"])
                output = independent_rule(grid)
                self.assertEqual(self.module.solve_python(grid), output)
                pairs.add((
                    tuple(map(tuple, grid)),
                    tuple(map(tuple, output)),
                ))
            linked = sum(
                profiles[profile]
                for profile in self.module.PUBLIC_PROFILES
            )
            self.assertEqual(
                set(profiles),
                set(self.module.SCENE_PROFILES),
            )
            self.assertEqual(colors, set(range(1, 9)))
            self.assertGreaterEqual(linked, 180)
            self.assertLessEqual(linked, 320)
            self.assertEqual(
                set(answer_profiles),
                set(self.module.PUBLIC_PROFILES),
            )
            self.assertGreaterEqual(sum(answer_profiles.values()), 100)
            self.assertLessEqual(sum(answer_profiles.values()), 220)
            self.assertGreaterEqual(len(pairs), 750)

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

    def test_self_check_rejects_shortcuts_and_malformed_bars(self) -> None:
        valid = self.module.generate(
            61,
            9,
            difficulty="hard",
            scene_profile="single_bar",
            cut_color=6,
        )
        no_cut = [
            [9 if value == 6 else value for value in row]
            for row in valid
        ]
        extra_color = copy.deepcopy(valid)
        location = next(
            (row, col)
            for row, values in enumerate(extra_color)
            for col, value in enumerate(values)
            if value == 6
        )
        extra_color[location[0]][location[1]] = 5
        non_square = [row[:-1] for row in valid]
        all_background = [[0 for _col in range(9)] for _row in range(9)]
        full_nines = [[9 for _col in range(9)] for _row in range(9)]
        singleton = [[0 for _col in range(9)] for _row in range(9)]
        singleton[4][4] = 9
        solid_square = [[0 for _col in range(9)] for _row in range(9)]
        for row in range(3, 6):
            for col in range(3, 6):
                solid_square[row][col] = 9
        wrong_scene = [[0 for _col in range(12)] for _row in range(12)]
        for row in range(3, 9):
            for col in range(4, 7):
                wrong_scene[row][col] = 9
        for col in range(4, 7):
            wrong_scene[5 + col % 2][col] = 6

        for name, grid in (
            ("no_cut", no_cut),
            ("extra_color", extra_color),
            ("non_square", non_square),
            ("all_background", all_background),
            ("full_nines", full_nines),
            ("singleton", singleton),
            ("solid_square", solid_square),
            ("wrong_scene", wrong_scene),
        ):
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_broad_oracle_handles_square_ties_and_clipping(self) -> None:
        grid = [[0 for _col in range(5)] for _row in range(5)]
        for row in range(2):
            for col in range(2):
                grid[row][col] = 9
        grid[0][0] = 6
        before = copy.deepcopy(grid)
        expected = independent_rule(grid)
        self.assertEqual(self.module.solve_python(grid), expected)
        self.assertEqual(grid, before)
        self.assertTrue(self.module.self_check(grid))

    def test_python_determinism_fresh_returns_and_rng_isolation(self) -> None:
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="mixed_bars",
            cut_color=4,
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="mixed_bars",
            cut_color=4,
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
            scene_profile="mixed_bars",
            cut_color=4,
        )
        self.assertEqual(second, third)

    def test_unknown_and_invalid_overrides_reject(self) -> None:
        for overrides in (
            {"unknown": 1},
            {"scene_profile": "not-a-profile"},
            {"cut_color": 0},
            {"cut_color": 9},
            {"cut_color": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self.module.generate(1, 2, **overrides)

    def test_canonical_authority_and_archival_base_programs_are_exact(self) -> None:
        program = self.row["program_solution"]
        expected_hash = normalized_rule_hash(program)
        self.assertEqual(
            expected_hash,
            "1eb213be2892b12500888cf6cf5a21845f6d7cbbc220a0a7a6cbd76679c79170",
        )
        self.assertEqual(
            normalized_rule_hash(GROUNDED_RULES[TASK_ID]),
            expected_hash,
        )
        base_path = (
            canonical_path(ROOT).parent.parent
            / "base"
            / "solutions"
            / "training"
            / "2faf500b__6b5d8752c5c4.json"
        )
        base = json.loads(base_path.read_text(encoding="utf-8"))
        self.assertEqual(base["verification"]["status"], "available_from_canonical")
        self.assertNotEqual(base["racket_target"]["raw_code"], program)
        self.assertNotEqual(base["racket_target"]["target_code"], program)
        self.assertEqual(
            " ".join(wrap_rule(base["racket_target"]["raw_code"]).split()),
            " ".join(wrap_rule(base["racket_target"]["target_code"]).split()),
        )

        with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
            for source_name in ("raw_code", "target_code"):
                executable = wrap_rule(base["racket_target"][source_name])
                for pair_index, pair in enumerate(self.pairs):
                    with self.subTest(
                        source_name=source_name,
                        pair_index=pair_index,
                    ):
                        actual = bridge.eval_text(
                            f"({executable} {racket_grid_literal(pair['input'])})"
                        )
                        self.assertEqual(actual, pair["output"])


if __name__ == "__main__":
    unittest.main()
