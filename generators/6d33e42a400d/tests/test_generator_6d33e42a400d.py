"""Focused semantic tests for generator 6d33e42a400d."""

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
TASK_ID = "6d33e42a400d"


def canonical_row() -> dict:
    path = ROOT / "data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if (
                row.get("task_id") == TASK_ID
                and row.get("source") == "training"
            ):
                return row
    raise KeyError(TASK_ID)


def canonical_pairs(row: dict) -> list[dict]:
    return list(row["train"]) + list(row["test"])


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def role_info(grid: list[list[int]]):
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    colors = [value for value in counts if value != background]
    source = max(colors, key=counts.get)
    paint = min(colors, key=counts.get)
    return background, source, paint


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    background, source, paint = role_info(grid)
    del background
    height, width = len(grid), len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == paint
    ]
    source_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == source
    ]
    if len({row for row, _ in markers}) == 1:
        marker_line = markers[0][0]
        coordinates = sorted(col for _, col in markers)
        target_line = next(
            row
            for row in range(height)
            if row != marker_line
            and [
                col for col in range(width) if grid[row][col] == source
            ]
            == coordinates
        )
        direction = -1 if target_line > marker_line else 1
        copied = [
            (target_line + marker_line - row, col)
            for row, col in source_cells
            if (-1 if row < marker_line else 1 if row > marker_line else 0)
            == direction
        ]
    else:
        marker_line = markers[0][1]
        coordinates = sorted(row for row, _ in markers)
        target_line = next(
            col
            for col in range(width)
            if col != marker_line
            and [
                row for row in range(height) if grid[row][col] == source
            ]
            == coordinates
        )
        direction = -1 if target_line > marker_line else 1
        copied = [
            (row, target_line + marker_line - col)
            for row, col in source_cells
            if (-1 if col < marker_line else 1 if col > marker_line else 0)
            == direction
        ]
    output = [row[:] for row in grid]
    for row, col in copied:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = paint
    return output


class Generator6d33e42a400dTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.row = canonical_row()
        cls.pairs = canonical_pairs(cls.row)
        cls.public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.pairs
        }

    def test_metadata_has_only_observable_exact_axes(self) -> None:
        self.assertEqual(self.module.VERSION, "2.0.0")
        self.assertEqual(self.module.RULE_HASH, "d5de5966b074")
        self.assertEqual(
            set(self.module.AXES),
            {"scene_profile", "orientation"},
        )
        self.assertEqual(
            set(
                self.module.AXES["scene_profile"]["valid"].split("|")
            ),
            set(self.module.SCENE_PROFILES),
        )
        self.assertEqual(
            self.module.AXES["orientation"]["valid"],
            "0..3",
        )

    def test_all_public_pairs_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 3)
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                observed = self.module.observe_overrides(source)
                self.assertEqual(
                    observed["scene_profile"],
                    self.module.PUBLIC_PROFILES[index],
                )
                self.assertIn(observed["orientation"], range(4))
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
                for orientation in range(4):
                    with self.subTest(
                        band=band,
                        profile=profile,
                        orientation=orientation,
                    ):
                        grid = self.module.generate(
                            1_000 + orientation,
                            37 * orientation,
                            difficulty=band,
                            scene_profile=profile,
                            orientation=orientation,
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "orientation": orientation,
                            },
                        )
                        self.assertEqual(
                            self.module.solve_python(grid),
                            independent_rule(grid),
                        )

    def test_constructive_profiles_never_shed_or_drift(self) -> None:
        expected_depth = {
            "shallow_steps": 3,
            "medium_steps": 4,
            "deep_steps": 6,
        }
        expected_size = {
            "easy": {
                "shallow_steps": 20,
                "medium_steps": 21,
                "deep_steps": 22,
            },
            "medium": {
                "shallow_steps": 21,
                "medium_steps": 22,
                "deep_steps": 23,
            },
            "hard": {
                "shallow_steps": 22,
                "medium_steps": 23,
                "deep_steps": 24,
            },
        }
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            for profile in self.module.EXTRAPOLATION_PROFILES:
                for sample_index in range(200):
                    grid = self.module.generate(
                        20_000 + band_index,
                        sample_index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["reasons"], [])
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(
                        analysis["height"],
                        expected_size[band][profile],
                    )
                    self.assertEqual(
                        analysis["max_depth"],
                        expected_depth[profile],
                    )
                    self.assertEqual(
                        analysis["source_component_count"],
                        analysis["marker_count"] + 1,
                    )
                    self.assertEqual(
                        analysis["paint_component_count"],
                        analysis["marker_count"],
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
            self.assertGreaterEqual(len(pairs), 800)

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
        base = self.module.generate(
            61,
            9,
            scene_profile="medium_steps",
            orientation=0,
        )
        background, source, paint = role_info(base)
        geometry = self.module._find_geometry(base, source, paint)
        marker_line = geometry["marker_line"]
        target_line = geometry["target_candidates"][0]
        marker_coords = geometry["marker_coords"]

        wrong_size = copy.deepcopy(base[:-1])
        off_line = copy.deepcopy(base)
        off_line[target_line - 1][marker_coords[0]] = paint
        missing_anchor = copy.deepcopy(base)
        missing_anchor[target_line][marker_coords[0]] = background
        extra_source = copy.deepcopy(base)
        extra_source[
            (marker_line + target_line) // 2
        ][marker_coords[0] + 1] = source
        broken_span = copy.deepcopy(base)
        for row in range(len(base)):
            if row != target_line and broken_span[row][0] == source:
                broken_span[row][0] = background
        merged_roles = [
            [
                source if value == paint else value
                for value in row
            ]
            for row in base
        ]

        invalid = (
            ("wrong_size", wrong_size),
            ("off_line", off_line),
            ("missing_anchor", missing_anchor),
            ("extra_source", extra_source),
            ("broken_span", broken_span),
            ("merged_roles", merged_roles),
            ("ragged", [[0, 1], [0]]),
            ("boolean", [[False for _ in range(22)] for _ in range(22)]),
            ("out_of_range", [[10 for _ in range(22)] for _ in range(22)]),
        )
        for name, grid in invalid:
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_broad_oracle_is_not_tied_to_training_envelope(self) -> None:
        grid = [[8 for _ in range(12)] for _ in range(12)]
        for col in range(12):
            grid[2][col] = 1
        for col in (0, 3, 6, 9):
            grid[3][col] = 2
            grid[8][col] = 1
        before = copy.deepcopy(grid)
        expected = independent_rule(grid)
        self.assertEqual(self.module.solve_python(grid), expected)
        self.assertEqual(grid, before)
        self.assertEqual(expected[9], [2 for _ in range(12)])
        self.assertTrue(self.module.self_check(grid))

        rotated = self.module._rotate90(grid)
        expected_rotated = independent_rule(rotated)
        self.assertEqual(
            self.module.solve_python(rotated),
            expected_rotated,
        )
        self.assertTrue(self.module.self_check(rotated))

    def test_python_determinism_fresh_returns_and_rng_isolation(self) -> None:
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="deep_steps",
            orientation=3,
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            77,
            88,
            difficulty="hard",
            scene_profile="deep_steps",
            orientation=3,
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
            scene_profile="deep_steps",
            orientation=3,
        )
        self.assertEqual(second, third)

    def test_unknown_and_invalid_overrides_reject(self) -> None:
        for overrides in (
            {"unknown": 1},
            {"scene_profile": "not-a-profile"},
            {"orientation": -1},
            {"orientation": 4},
            {"orientation": True},
            {"orientation": 1.5},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self.module.generate(1, 2, **overrides)

    def test_base_and_canonical_sources_are_synchronized(self) -> None:
        program = self.row["program_solution"]
        expected_hash = normalized_rule_hash(program)
        self.assertEqual(
            expected_hash,
            "d5de5966b0742f59d6aef8a587e0a083a87ea3e92a605668d2ed2eaa0f3c30ab",
        )
        for relative in (
            "data/base/solutions/training/66ac4c3b__6d33e42a400d.json",
            "data/base/solutions/augmented/66ac4c3b__c657675720c8.json",
        ):
            with self.subTest(relative=relative):
                base = json.loads(
                    (ROOT / relative).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    base["racket_target"]["raw_code"],
                    program,
                )
                self.assertEqual(
                    base["racket_target"]["target_code"],
                    program,
                )


if __name__ == "__main__":
    unittest.main()
