from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e1be962ccf97 import generator


ROOT = Path(__file__).resolve().parents[1]


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split)
                pairs = value if isinstance(value, list) else [value]
                for pair in pairs:
                    if pair:
                        yield as_grid(pair["input"]), as_grid(pair["output"])


class E1be962ccf97GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        winners = set()
        divider_rows = set()
        divider_cols = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            signature = generator.canonical_profile_signature(grid)
            profiles.add(signature)
            scene = generator._analyze_scene(grid)
            self.assertEqual(scene["layout_kind"], "cross")
            self.assertEqual(len(scene["components"]), 4)
            self.assertEqual(len(scene["winner_indices"]), 1)
            winners.add(scene["winner_indices"][0])
            divider_rows.update(scene["divider_rows"])
            divider_cols.update(scene["divider_cols"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(winners, {1, 2, 3})
        self.assertEqual(divider_rows, {5, 6, 7})
        self.assertEqual(divider_cols, {4, 6, 7})

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, generator.rule_mirror(grid)))
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 25)
                self.assertLessEqual(matches, 85)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 550)
                self.assertGreaterEqual(len(outputs), 550)

    def test_general_path_witnesses_every_layout_and_winner_position(self):
        winner_positions = {
            "horizontal": set(),
            "vertical": set(),
            "cross": set(),
        }
        loser_counts = set()
        winner_counts = set()
        winner_not_largest_area = 0
        winner_not_densest = 0
        for layout_kind in generator._LAYOUT_KINDS:
            for winner_count in range(3, 8):
                for seed in range(80):
                    grid = generator.generate(
                        seed,
                        seed * 31 + winner_count,
                        difficulty="hard",
                        grid_h=15,
                        grid_w=16,
                        layout_kind=layout_kind,
                        winner_count=winner_count,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    scene = generator._analyze_scene(grid)
                    self.assertEqual(scene["layout_kind"], layout_kind)
                    self.assertEqual(
                        len(scene["components"]),
                        4 if layout_kind == "cross" else 2,
                    )
                    winner_index = scene["winner_indices"][0]
                    winner_positions[layout_kind].add(winner_index)
                    winner_counts.add(scene["red_counts"][winner_index])
                    areas = [len(cells) for cells in scene["components"]]
                    if areas[winner_index] < max(areas):
                        winner_not_largest_area += 1
                    winner_density = (
                        scene["red_counts"][winner_index],
                        areas[winner_index],
                    )
                    if any(
                        count * winner_density[1]
                        > winner_density[0] * area
                        for index, (count, area) in enumerate(
                            zip(scene["red_counts"], areas)
                        )
                        if index != winner_index
                    ):
                        winner_not_densest += 1
                    loser_counts.update(
                        count
                        for index, count in enumerate(scene["red_counts"])
                        if index != winner_index
                    )
        self.assertEqual(winner_positions["horizontal"], {0, 1})
        self.assertEqual(winner_positions["vertical"], {0, 1})
        self.assertEqual(winner_positions["cross"], {0, 1, 2, 3})
        self.assertEqual(winner_counts, {3, 4, 5, 6, 7})
        self.assertEqual(loser_counts, {0, 1, 2, 3, 4, 5, 6})
        self.assertGreater(winner_not_largest_area, 100)
        self.assertGreater(winner_not_densest, 20)

    def test_rule_changes_only_winning_background_cells(self):
        for layout_kind in generator._LAYOUT_KINDS:
            for seed in range(60):
                grid = generator.generate(
                    seed,
                    seed * 43 + 3,
                    grid_h=14,
                    grid_w=15,
                    layout_kind=layout_kind,
                    winner_count=7,
                )
                scene = generator._analyze_scene(grid)
                winner = set(
                    scene["components"][scene["winner_indices"][0]]
                )
                output = generator.rule_mirror(grid)
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        expected = 8 if (r, c) in winner and value == 0 else value
                        self.assertEqual(output[r][c], expected)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 9},
            {"grid_h": 22},
            {"grid_w": 9},
            {"grid_w": 22},
            {"layout_kind": "horizontal"},
            {"layout_kind": "vertical"},
            {"layout_kind": "cross"},
            {"winner_count": 3},
            {"winner_count": 7},
            {
                "grid_h": 9,
                "grid_w": 9,
                "layout_kind": "cross",
                "winner_count": 7,
            },
            {
                "grid_h": 22,
                "grid_w": 22,
                "layout_kind": "vertical",
                "winner_count": 3,
            },
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                for key, value in kwargs.items():
                    self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "9"},
            {"grid_w": 9.0},
            {"layout_kind": 1},
            {"winner_count": True},
            {"grid_h": 8},
            {"grid_h": 23},
            {"grid_w": 8},
            {"grid_w": 23},
            {"layout_kind": "grid"},
            {"winner_count": 2},
            {"winner_count": 8},
            {"texture": "no_divider"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 30)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=9,
                grid_w=22,
                layout_kind="cross",
                winner_count=7,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]

        bad_color = [row[:] for row in original]
        bad_color[0][0] = 7
        self.assertTrue(
            any(
                "colors 0, 2, or 5" in error
                for error in generator.self_check(bad_color)
            )
        )

        stray_wall = [row[:] for row in original]
        stray_wall[0][0] = 5
        self.assertTrue(
            any(
                "complete divider" in error
                for error in generator.self_check(stray_wall)
            )
        )

        broken_wall = [row[:] for row in original]
        broken_wall[7][0] = 0
        self.assertTrue(generator.self_check(broken_wall))

        tied = generator._paint_scene(
            11,
            11,
            (7,),
            (4,),
            (4, 2, 4, 1),
            random.Random(3),
        )
        self.assertTrue(
            any(
                "exactly one chamber" in error
                for error in generator.self_check(tied)
            )
        )

        too_few = generator._paint_scene(
            11,
            11,
            (7,),
            (4,),
            (2, 1, 0, 1),
            random.Random(4),
        )
        too_many = generator._paint_scene(
            11,
            11,
            (7,),
            (4,),
            (8, 1, 0, 1),
            random.Random(5),
        )
        self.assertTrue(generator.self_check(too_few))
        self.assertTrue(generator.self_check(too_many))

    def test_lawful_cross_profile_recombination_is_rejected(self):
        h, w, divider_row, divider_col, red_counts = (
            generator._PROFILE_SPECS[0]
        )
        hybrid_counts = (*red_counts[:-1], 1)
        hybrid = generator._paint_scene(
            h,
            w,
            (divider_row,),
            (divider_col,),
            hybrid_counts,
            random.Random(72),
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertNotIn(
            generator.canonical_profile_signature(hybrid),
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
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
