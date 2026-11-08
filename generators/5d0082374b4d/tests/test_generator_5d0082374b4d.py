from __future__ import annotations

import importlib
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.5d0082374b4d.generator"
)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "5d0082374b4d":
                return row
    raise AssertionError("canonical task row not found")


def normalize(grid):
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


class Generator5d0082374b4dTests(unittest.TestCase):
    def test_rule_hash_and_version_are_pinned(self):
        self.assertEqual(MODULE.RULE_HASH, "80261197592b")
        self.assertEqual(MODULE.VERSION, "2.0.0")

    def test_all_canonical_inputs_are_accepted_and_mirror_outputs(self):
        row = canonical_row()
        pairs = list(row["train"]) + [row["test"]]
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            grid = normalize(pair["input"])
            expected = normalize(pair["output"])
            self.assertEqual(MODULE.self_check(grid), [])
            self.assertEqual(MODULE.expected_output(grid), expected)

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state = random.getstate()
        first = MODULE.generate(1234, 56, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(1234, 56, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        second[0][0] = 9 if second[0][0] != 9 else 8
        self.assertNotEqual(first, second)

    def test_boundary_overrides_are_exact_in_every_band(self):
        for difficulty in ("easy", "medium", "hard"):
            for grid_h in (9, 14):
                for grid_w in (12, 20):
                    for n_frames in (2, 3):
                        grid = MODULE.generate(
                            77,
                            91,
                            difficulty=difficulty,
                            grid_h=grid_h,
                            grid_w=grid_w,
                            n_frames=n_frames,
                            texture="cool",
                        )
                        self.assertEqual((len(grid), len(grid[0])), (grid_h, grid_w))
                        self.assertEqual(MODULE.observe_overrides(grid)["n_frames"], n_frames)
                        self.assertEqual(MODULE.self_check(grid), [])

    def test_helpful_textures_are_live_and_valid(self):
        signatures = {texture: [] for texture in MODULE.HELPFUL_TEXTURES}
        for seed in range(8):
            for texture in MODULE.HELPFUL_TEXTURES:
                grid = MODULE.generate(
                    seed,
                    seed * 13 + 1,
                    difficulty="medium",
                    texture=texture,
                )
                self.assertEqual(MODULE.self_check(grid), [])
                signatures[texture].append(MODULE.semantic_features(grid)["marker_pairs"])
        for left_index, left in enumerate(MODULE.HELPFUL_TEXTURES):
            for right in MODULE.HELPFUL_TEXTURES[left_index + 1 :]:
                self.assertNotEqual(signatures[left], signatures[right])

    def test_semantic_branches_and_shortcut_rebuttals_appear(self):
        seen_frames = set()
        odd = even = less = greater = 0
        dimensions = set()
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for seed in range(80):
                grid = MODULE.generate(
                    10_000 + band_index * 1_000 + seed,
                    seed * 29 + 7,
                    difficulty=difficulty,
                )
                facts = MODULE.semantic_features(grid)
                self.assertEqual(facts["errors"], [])
                self.assertGreaterEqual(facts["n_frames"], 2)
                self.assertNotEqual(grid, MODULE.expected_output(grid))
                seen_frames.add(facts["n_frames"])
                odd += facts["odd_inner_width_count"]
                even += facts["even_inner_width_count"]
                less += facts["left_marker_less_count"]
                greater += facts["left_marker_greater_count"]
                dimensions.add((facts["grid_h"], facts["grid_w"]))
        self.assertEqual(seen_frames, {2, 3})
        self.assertGreater(odd, 0)
        self.assertGreater(even, 0)
        self.assertGreater(less, 0)
        self.assertGreater(greater, 0)
        self.assertGreater(len(dimensions), 10)

    def test_declared_mutation_fixtures_are_rejected(self):
        fixtures = MODULE.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 4)
        for name, grid in fixtures:
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(grid))

    def test_degenerate_textures_are_rejected_by_self_check(self):
        for texture in MODULE.DEGENERATE_TEXTURES:
            grid = MODULE.generate(1, 2, texture=texture)
            self.assertTrue(MODULE.self_check(grid), texture)

    def test_unknown_override_rejects_loudly(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            MODULE.generate(1, 2, bogus_axis=3)


if __name__ == "__main__":
    unittest.main()
