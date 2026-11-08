from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f2865c4fa81f import generator


ROOT = Path(__file__).resolve().parents[1]


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return value


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                pairs = row.get(split) or []
                pairs = [pairs] if isinstance(pairs, dict) else pairs
                for pair in pairs:
                    yield _grid(pair["input"]), _grid(pair["output"])


def bar_features(grid):
    h, w = len(grid), len(grid[0])
    sep = h // 2
    color = next(
        value
        for row in grid
        for value in row
        if value not in (0, 2)
    )
    top_row = next(r for r in range(sep) if color in grid[r])
    bot_row = next(r for r in range(sep + 1, h) if color in grid[r])
    top_cols = tuple(c for c in range(w) if grid[top_row][c] == color)
    bot_cols = tuple(c for c in range(w) if grid[bot_row][c] == color)
    return sep, top_row, bot_row, top_cols, bot_cols


class F2865c4fa81fGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.official_profiles = {
            generator.canonical_profile_signature(grid)
            for grid, _ in cls.pairs
        }

    def test_all_canonical_pairs_match_complete_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 5)
        self.assertEqual(
            self.official_profiles,
            generator._CANONICAL_SIGNATURES,
        )
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

    def test_explicit_none_is_identical_and_enums_fail_closed(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                self.assertEqual(
                    generator.generate(seed, seed, difficulty=band),
                    generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture="none",
                    ),
                )
        for overrides in (
            {"texture": "garbage"},
            {"palette_kind": "garbage"},
            {"bogus": 1},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **overrides)

    def test_bool_and_integer_overrides_are_not_coerced(self):
        for overrides in (
            {"top_wider": 0},
            {"top_wider": 1},
            {"strict_subset": 0},
            {"strict_subset": 1},
            {"strict_subset": "false"},
            {"grid_h": "9"},
            {"grid_w": 4.0},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    generator.generate(0, 0, **overrides)

    def test_palette_overrides_select_only_the_declared_pool(self):
        for kind in generator.PALETTE_KINDS:
            allowed = set(generator._build_palette(kind))
            seen = set()
            for seed in range(120):
                grid = generator.generate(
                    seed,
                    seed,
                    palette_kind=kind,
                )
                color = next(
                    value
                    for row in grid
                    for value in row
                    if value not in (0, 2)
                )
                self.assertIn(color, allowed)
                seen.add(color)
            self.assertEqual(seen, allowed)

    def test_full_width_records_feasible_default_subset_value(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 19 + 7,
                        difficulty=band,
                        texture="full_width",
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                self.assertIs(captured[-1]._drawn["strict_subset"], True)
                self.assertIs(observed["strict_subset"], True)
                self.assertEqual(generator.self_check(grid), [])

        with self.assertRaisesRegex(ValueError, "strict_subset"):
            generator.generate(
                0,
                0,
                texture="full_width",
                strict_subset=False,
            )

    def test_each_texture_realizes_its_named_geometry(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                for texture in generator.EDGE_TEXTURES:
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture=texture,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    sep, top_row, bot_row, top_cols, bot_cols = (
                        bar_features(grid)
                    )
                    if texture == "edge_bars":
                        self.assertEqual((top_row, bot_row), (0, len(grid) - 1))
                    elif texture == "narrow_touching_sep":
                        if len(top_cols) > len(bot_cols):
                            self.assertEqual(bot_row, sep + 1)
                        else:
                            self.assertEqual(top_row, sep - 1)
                    elif texture == "full_width":
                        self.assertEqual(
                            max(len(top_cols), len(bot_cols)),
                            len(grid[0]),
                        )
                    else:
                        self.assertEqual(
                            len(set(top_cols) & set(bot_cols)),
                            1,
                        )

    def test_explicit_non_subset_never_falls_back(self):
        for texture in (None, "edge_bars", "narrow_touching_sep",
                        "single_shared_col"):
            for band in ("easy", "medium", "hard"):
                for seed in range(80):
                    kwargs = {"strict_subset": False}
                    if texture is not None:
                        kwargs["texture"] = texture
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        **kwargs,
                    )
                    self.assertIs(
                        generator.observe_overrides(grid)["strict_subset"],
                        False,
                    )

    def test_profile_prior_is_stable_and_varies_common_translation(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                origins = set()
                for offset in range(500):
                    seed = seed_start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    signature = generator.canonical_profile_signature(grid)
                    if signature in self.official_profiles:
                        matches += 1
                        profiles.add(signature)
                        _, _, _, top_cols, bot_cols = bar_features(grid)
                        origins.add(min((*top_cols, *bot_cols)))
                self.assertEqual(profiles, self.official_profiles)
                self.assertGreaterEqual(matches, 100)
                self.assertLessEqual(matches, 220)
                self.assertEqual(origins, {0, 1})

    def test_lawful_cross_profile_recombination_is_not_official(self):
        grid = [[0] * 5 for _ in range(13)]
        grid[0][1:3] = [3, 3]
        grid[6] = [2] * 5
        grid[12][1:4] = [3, 3, 3]

        self.assertEqual(generator.self_check(grid), [])
        self.assertIsNotNone(generator.canonical_profile_signature(grid))
        self.assertFalse(generator.is_canonical_profile(grid))

    def test_self_check_enforces_envelope_and_structure(self):
        too_small = [
            [3, 3, 0],
            [0, 0, 0],
            [2, 2, 2],
            [0, 0, 0],
            [0, 3, 0],
        ]
        too_wide = [[0] * 12 for _ in range(9)]
        too_wide[0][1:4] = [3, 3, 3]
        too_wide[4] = [2] * 12
        too_wide[8][2:4] = [3, 3]
        self.assertTrue(generator.self_check(too_small))
        self.assertTrue(generator.self_check(too_wide))

        control = generator.generate(
            0,
            0,
            grid_h=13,
            grid_w=5,
            top_wider=True,
            strict_subset=True,
        )
        self.assertEqual(generator.self_check(control), [])

        no_separator = [
            [0 if value == 2 else value for value in row]
            for row in control
        ]
        self.assertTrue(generator.self_check(no_separator))

        disconnected = [row[:] for row in control]
        _, top_row, _, top_cols, _ = bar_features(disconnected)
        if len(top_cols) >= 3:
            disconnected[top_row][top_cols[1]] = 0
        else:
            disconnected[top_row][min(top_cols) + 2] = disconnected[
                top_row
            ][top_cols[0]]
        self.assertTrue(generator.self_check(disconnected))

    def test_default_provenance_determinism_and_fresh_returns(self):
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    first = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                second = generator.generate(seed, seed, difficulty=band)
                observed = generator.observe_overrides(first)
                drawn = captured[-1]._drawn
                self.assertEqual(drawn["grid_h"], len(first))
                self.assertEqual(drawn["grid_w"], len(first[0]))
                self.assertEqual(drawn["top_wider"], observed["top_wider"])
                self.assertEqual(
                    drawn["strict_subset"],
                    observed["strict_subset"],
                )
                self.assertIn("palette_kind", drawn)
                self.assertIn("texture", drawn)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                expected = second[0][0]
                first[0][0] = (first[0][0] + 1) % 10
                replay = generator.generate(seed, seed, difficulty=band)
                self.assertEqual(replay[0][0], expected)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
