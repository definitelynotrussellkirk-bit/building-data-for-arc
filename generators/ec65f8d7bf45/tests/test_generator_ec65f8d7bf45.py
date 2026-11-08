from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.ec65f8d7bf45 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    row = canonical_row()
    pairs = list(row["train"])
    pairs.extend(
        [row["test"]] if isinstance(row["test"], dict) else row["test"]
    )
    return [
        {
            "input": generator._coerce_grid(pair["input"]),
            "output": generator._coerce_grid(pair["output"]),
        }
        for pair in pairs
    ]


def independent_rule(grid):
    counts = Counter(
        value for row in grid for value in row if value != 0
    )
    frame_color = max(counts, key=counts.get)
    paint_color = min(counts, key=counts.get)
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == frame_color
    ]
    top = min(row for row, _col in cells)
    bottom = max(row for row, _col in cells)
    left = min(col for _row, col in cells)
    right = max(col for _row, col in cells)
    output = [row[:] for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = (
                paint_color
                if (row - top - 1 + col - left - 1) % 2 == 0
                else 0
            )
    return output


class Ec65f8d7bf45GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add(
                        (
                            tuple(map(tuple, grid)),
                            tuple(map(tuple, output)),
                        )
                    )
                    signature = generator.canonical_profile_signature(grid)
                    if signature is not None:
                        matches += 1
                        profiles.add(signature)
                self.assertGreaterEqual(matches, 100)
                self.assertLessEqual(matches, 200)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 585)

    def test_forced_boundaries_and_dependent_sizes_are_exact(self):
        calls = (
            {
                "grid_h": 7,
                "grid_w": 7,
                "frame_h": 5,
                "frame_w": 5,
                "marker_corner": "top_left",
            },
            {
                "grid_h": 18,
                "grid_w": 18,
                "frame_h": 16,
                "frame_w": 16,
                "marker_corner": "bottom_right",
            },
            {
                "grid_h": 7,
                "grid_w": 18,
                "frame_h": 4,
                "frame_w": 8,
                "marker_corner": "top_right",
            },
            {
                "grid_h": 18,
                "grid_w": 7,
                "frame_h": 8,
                "frame_w": 4,
                "marker_corner": "bottom_left",
            },
        )
        for kwargs in calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    37,
                    71,
                    difficulty=band,
                    **kwargs,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    kwargs,
                )

        tall = generator.generate(
            13, 17, difficulty="easy", frame_h=16
        )
        self.assertEqual(len(tall), 18)
        self.assertEqual(generator.observe_overrides(tall)["frame_h"], 16)

    def test_rule_is_exact_checkerboard_and_input_pure(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                expected = independent_rule(grid)
                actual = generator.rule_mirror(grid)
                self.assertEqual(actual, expected)
                self.assertEqual(grid, before)

                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                top, left, bottom, right = features["bbox"]
                for row in range(top + 1, bottom):
                    for col in range(left + 1, right):
                        expected_value = (
                            features["paint_color"]
                            if (
                                row - top - 1 + col - left - 1
                            ) % 2 == 0
                            else 0
                        )
                        self.assertEqual(actual[row][col], expected_value)

    def test_d4_color_relabeling_and_lawful_nonprofile(self):
        for index, rows in enumerate(generator._PROFILE_ROWS):
            for transform in range(8):
                frame_color = 1 + ((index + transform) % 9)
                paint_color = 1 + ((index + transform + 4) % 9)
                if paint_color == frame_color:
                    paint_color = 1 + (paint_color % 9)
                grid = generator._draw_profile(
                    rows,
                    transform,
                    frame_color,
                    paint_color,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertTrue(generator.is_canonical_profile(grid))
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

        hybrid = generator.generate(
            83,
            97,
            grid_h=12,
            grid_w=13,
            frame_h=6,
            frame_w=7,
            marker_corner="bottom_right",
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertEqual(
            generator.rule_mirror(hybrid),
            independent_rule(hybrid),
        )

    def test_removed_controls_impossible_pairs_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "7"},
            {"grid_w": 7.0},
            {"frame_h": True},
            {"frame_w": "5"},
            {"marker_corner": "center"},
            {"grid_h": 6},
            {"grid_h": 19},
            {"grid_w": 6},
            {"grid_w": 19},
            {"frame_h": 3},
            {"frame_h": 17},
            {"frame_w": 3},
            {"frame_w": 17},
            {"grid_h": 7, "frame_h": 6},
            {"grid_w": 7, "frame_w": 6},
            {"texture": "paint_inside_frame"},
            {"palette_kind": "warm"},
            {"density": "sparse"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(captured[-1]._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 125)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=18,
                grid_w=7,
                frame_h=16,
                frame_w=5,
                marker_corner="bottom_left",
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {
                "grid_h": 18,
                "grid_w": 7,
                "frame_h": 16,
                "frame_w": 5,
                "marker_corner": "bottom_left",
            },
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            grid_h=11,
            grid_w=12,
            frame_h=6,
            frame_w=7,
            marker_corner="top_left",
        )
        mutations = []

        marker_inside = [row[:] for row in valid]
        _coerced, features, _errors = generator._scene_analysis(valid)
        marker = generator._CORNER_COORDS[features["marker_corner"]](
            len(valid), len(valid[0])
        )
        marker_inside[marker[0]][marker[1]] = 0
        top, left, _bottom, _right = features["bbox"]
        marker_inside[top + 1][left + 1] = features["paint_color"]
        mutations.append(marker_inside)

        open_frame = [row[:] for row in valid]
        open_frame[top][left + 1] = 0
        mutations.append(open_frame)

        filled_interior = [row[:] for row in valid]
        filled_interior[top + 1][left + 1] = features["frame_color"]
        mutations.append(filled_interior)

        extra_marker = [row[:] for row in valid]
        extra_marker[-1][-1] = features["paint_color"]
        mutations.append(extra_marker)

        edge_frame = [row[:] for row in valid]
        for row in range(len(edge_frame)):
            for col in range(len(edge_frame[0])):
                if edge_frame[row][col] == features["frame_color"]:
                    edge_frame[row][col] = 0
        generator.draw_rect_outline(
            edge_frame,
            0,
            2,
            features["frame_h"],
            features["frame_w"],
            features["frame_color"],
        )
        mutations.append(edge_frame)

        third_color = [row[:] for row in valid]
        third_color[-1][0] = 9
        if 9 in (features["frame_color"], features["paint_color"]):
            third_color[-1][0] = 8
        mutations.append(third_color)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)
        mutations.append([[0] * 7 for _ in range(6)])
        mutations.append([[0] * 6 for _ in range(7)])
        mutations.append([[0] * 19 for _ in range(7)])
        mutations.append([[0] * 7 for _ in range(19)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_geometry_palette_corners_and_diversity(self):
        mean_areas = {}
        mean_frame_areas = {}
        palette = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            frame_areas = []
            corners = Counter()
            pairs = set()
            profiles = Counter()
            frame_heights = set()
            frame_widths = set()
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    )
                )
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                frame_areas.append(
                    features["frame_h"] * features["frame_w"]
                )
                frame_heights.add(features["frame_h"])
                frame_widths.add(features["frame_w"])
                corners[features["marker_corner"]] += 1
                palette.update(
                    (features["frame_color"], features["paint_color"])
                )
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profiles[signature] += 1

            mean_areas[band] = sum(areas) / len(areas)
            mean_frame_areas[band] = sum(frame_areas) / len(frame_areas)
            self.assertGreaterEqual(len(pairs), 585)
            self.assertEqual(set(corners), set(generator.MARKER_CORNERS))
            self.assertGreaterEqual(min(corners.values()), 100)
            self.assertEqual(
                set(profiles),
                generator._CANONICAL_PROFILE_SIGNATURES,
            )
            self.assertGreaterEqual(len(frame_heights), 3)
            self.assertGreaterEqual(len(frame_widths), 3)

        self.assertEqual(palette, set(range(1, 10)))
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])
        self.assertLess(
            mean_frame_areas["easy"], mean_frame_areas["medium"]
        )
        self.assertLess(
            mean_frame_areas["medium"], mean_frame_areas["hard"]
        )

    def test_source_pin_determinism_freshness_and_global_rng(self):
        canonical = self.row["program_solution"]
        normalized = hashlib.sha256(
            " ".join(canonical.split()).encode()
        ).hexdigest()
        self.assertEqual(generator.RULE_HASH, normalized[:12])
        base_row = json.loads(
            (
                ROOT
                / "data/base/solutions/banks/9a66c53abf7f"
                / "E132__ec65f8d7bf45.json"
            ).read_text()
        )
        self.assertEqual(
            base_row["racket_target"]["raw_code"], canonical
        )
        self.assertEqual(
            base_row["racket_target"]["target_code"], canonical
        )

        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
