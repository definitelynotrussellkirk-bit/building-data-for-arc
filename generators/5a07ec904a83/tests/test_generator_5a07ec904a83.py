"""Focused semantic tests for generator 5a07ec904a83."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module
from solvers.grounded_rules import GROUNDED_RULES


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "5a07ec904a83"


def canonical_row() -> dict:
    path = ROOT / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def canonical_pairs(row: dict) -> list[dict]:
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def make_uniform(
    height: int,
    width: int,
    background: int,
    marker: tuple[int, int],
) -> list[list[int]]:
    grid = [
        [background for _col in range(width)]
        for _row in range(height)
    ]
    grid[marker[0]][marker[1]] = 0
    return grid


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    marker_row, marker_col = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    )
    background = grid[0][0]
    return [
        [
            0
            if abs(row - marker_row) == abs(col - marker_col)
            else background
            for col in range(len(grid[0]))
        ]
        for row in range(len(grid))
    ]


class Generator5a07ec904a83Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.row = canonical_row()
        cls.pairs = canonical_pairs(cls.row)
        cls.public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.pairs
        }

    def test_metadata_exact_axes_and_finite_codomain(self) -> None:
        self.assertEqual(self.module.VERSION, "3.0.0")
        self.assertEqual(self.module.RULE_HASH, "2d673baf6c22")
        self.assertEqual(
            set(self.module.AXES),
            {"scene_profile", "background_color"},
        )
        self.assertEqual(
            set(
                self.module.AXES["scene_profile"]["valid"].split("|")
            ),
            set(self.module.SCENE_PROFILES),
        )

        sides = self.module.ODD_SIDES
        offset_square = sum(
            (side - 2) ** 2 - 1
            for side in sides
            if side >= 5
        )
        edge_square = sum(4 * side - 5 for side in sides)
        rectangle_dimensions = [
            (height, width)
            for height in sides
            for width in sides
            if height != width
        ]
        rect_center = len(rectangle_dimensions)
        rect_offset = sum(
            (height - 2) * (width - 2) - 1
            for height, width in rectangle_dimensions
        )
        codomain = 9 * (
            len(self.module.PUBLIC_PROFILES)
            + 1
            + offset_square
            + edge_square
            + rect_center
            + rect_offset
        )
        self.assertEqual(codomain, 23_544)
        self.assertEqual(
            self.module.EXPECTED_OUTPUT_CODOMAIN,
            codomain,
        )

    def test_all_public_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 4)
        observed = []
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(
                    self.module.canonical_profile_index(source),
                    index,
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
                observed.append(self.module.observe_overrides(source))
        self.assertEqual(
            [item["scene_profile"] for item in observed],
            list(self.module.PUBLIC_PROFILES),
        )
        self.assertEqual(
            [item["background_color"] for item in observed],
            [2, 1, 3, 6],
        )

    def test_every_exact_axis_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile in self.module.SCENE_PROFILES:
                for background in range(1, 10):
                    with self.subTest(
                        band=band,
                        profile=profile,
                        background=background,
                    ):
                        grid = self.module.generate(
                            100 + background,
                            37 * background,
                            difficulty=band,
                            scene_profile=profile,
                            background_color=background,
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "background_color": background,
                            },
                        )
                        self.assertEqual(
                            self.module.solve_python(grid),
                            independent_rule(grid),
                        )

    def test_default_prior_is_calibrated_diverse_and_complete(self) -> None:
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            profiles = Counter()
            colors = set()
            pairs = set()
            for index in range(1_000):
                grid = self.module.generate(
                    20_000 + band_index,
                    index,
                    difficulty=band,
                )
                self.assertEqual(self.module.self_check(grid), [])
                observed = self.module.observe_overrides(grid)
                profiles[observed["scene_profile"]] += 1
                colors.add(observed["background_color"])
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
            self.assertEqual(colors, set(range(1, 10)))
            self.assertGreaterEqual(linked, 180)
            self.assertLessEqual(linked, 320)
            self.assertGreaterEqual(len(pairs), 650)

    def test_default_generation_never_replays_a_public_literal(self) -> None:
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            for index in range(500):
                grid = self.module.generate(
                    30_000 + band_index,
                    index,
                    difficulty=band,
                )
                self.assertNotIn(
                    json.dumps(grid, separators=(",", ":")),
                    self.public_inputs,
                )
        for profile in self.module.PUBLIC_PROFILES:
            published_color = self.module._PUBLIC_BG_BY_PROFILE[
                profile
            ]
            for seed in range(64):
                grid = self.module.generate(
                    seed,
                    50_000 + seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                observed = self.module.observe_overrides(grid)
                self.assertNotEqual(
                    observed["background_color"],
                    published_color,
                )

    def test_off_center_and_rectangular_witnesses_refute_shortcuts(self) -> None:
        offset = make_uniform(7, 7, 4, (1, 4))
        rectangle = make_uniform(5, 11, 8, (3, 7))
        for grid, profile in (
            (offset, "offset_square"),
            (rectangle, "rect_offset"),
        ):
            with self.subTest(profile=profile):
                before = copy.deepcopy(grid)
                output = self.module.solve_python(grid)
                self.assertEqual(self.module.self_check(grid), [])
                self.assertEqual(
                    self.module.observe_overrides(grid)[
                        "scene_profile"
                    ],
                    profile,
                )
                self.assertEqual(output, independent_rule(grid))
                self.assertEqual(grid, before)
                self.assertNotEqual(output, grid)

    def test_public_feature_recombination_is_not_a_public_profile(self) -> None:
        recombined = make_uniform(5, 7, 4, (2, 3))
        self.assertEqual(self.module.self_check(recombined), [])
        self.assertEqual(
            self.module.observe_overrides(recombined)["scene_profile"],
            "rect_center",
        )
        self.assertIsNone(
            self.module.canonical_profile_index(recombined)
        )

    def test_self_check_rejects_structural_and_minimal_impostors(self) -> None:
        valid = self.module.generate(
            17,
            9,
            difficulty="hard",
            scene_profile="offset_square",
            background_color=4,
        )
        no_marker = copy.deepcopy(valid)
        for row in range(len(no_marker)):
            for col in range(len(no_marker[0])):
                if no_marker[row][col] == 0:
                    no_marker[row][col] = 4
        two_markers = copy.deepcopy(valid)
        two_markers[0][1] = 0
        origin_marker = copy.deepcopy(valid)
        for row in range(len(origin_marker)):
            for col in range(len(origin_marker[0])):
                if origin_marker[row][col] == 0:
                    origin_marker[row][col] = 4
        origin_marker[0][0] = 0
        third_color = copy.deepcopy(valid)
        third_color[0][1] = 9

        impostors = {
            "no_marker": no_marker,
            "two_markers": two_markers,
            "origin_marker": origin_marker,
            "third_color": third_color,
            "even_square": make_uniform(4, 4, 2, (2, 2)),
            "unsupported_center_13": make_uniform(
                13, 13, 2, (6, 6)
            ),
            "rectangular_edge": make_uniform(5, 7, 2, (0, 3)),
            "all_background": [[3 for _ in range(3)] for _ in range(3)],
            "singleton": [[0]],
            "solid_2x2": [[0, 0], [0, 0]],
            "short_line": [[0, 3, 3]],
            "ragged": [[1, 1], [1]],
            "boolean_cell": [[1, 1, 1], [1, False, 1], [1, 1, 1]],
        }
        for label, grid in impostors.items():
            with self.subTest(label=label):
                before = copy.deepcopy(grid)
                self.assertTrue(self.module.self_check(grid))
                self.assertEqual(self.module.observe_overrides(grid), {})
                self.assertEqual(grid, before)

    def test_unknown_controls_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, marker_row=1)
        with self.assertRaisesRegex(ValueError, "difficulty must"):
            self.module.generate(0, 0, difficulty="expert")
        with self.assertRaisesRegex(ValueError, "unknown scene_profile"):
            self.module.generate(0, 0, scene_profile="missing")
        with self.assertRaisesRegex(ValueError, "background_color"):
            self.module.generate(0, 0, background_color=0)
        with self.assertRaisesRegex(ValueError, "background_color"):
            self.module.generate(0, 0, background_color=True)

    def test_determinism_fresh_returns_and_global_rng_isolation(self) -> None:
        random.seed(20260719)
        global_state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(24):
                first = self.module.generate(seed, 13, difficulty=band)
                second = self.module.generate(seed, 13, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                snapshot = copy.deepcopy(first)
                self.module.self_check(first, difficulty=band, meta={})
                self.assertEqual(first, snapshot)
                self.module.generate(seed + 1_000, 7, difficulty=band)
                self.assertEqual(first, snapshot)
                first[0][0] = 9 if first[0][0] != 9 else 8
                self.assertEqual(
                    self.module.generate(seed, 13, difficulty=band),
                    second,
                )
        self.assertEqual(random.getstate(), global_state)

    def test_rule_hash_base_source_and_grounded_source_agree(self) -> None:
        program = self.row["program_solution"]
        digest = normalized_rule_hash(program)
        self.assertEqual(self.module.RULE_HASH, digest[:12])
        self.assertEqual(
            normalized_rule_hash(GROUNDED_RULES[TASK_ID]),
            digest,
        )
        path = (
            ROOT
            / "data/base/solutions/training"
            / "ea786f4a__5a07ec904a83.json"
        )
        record = json.loads(path.read_text())
        self.assertEqual(record["racket_target"]["raw_code"], program)
        self.assertEqual(record["racket_target"]["target_code"], program)
        self.assertEqual(
            record["primitive_metadata"]["primitive_chain"],
            ["at", "first", "find-color", "fst", "snd", "cellmap"],
        )


if __name__ == "__main__":
    unittest.main()
