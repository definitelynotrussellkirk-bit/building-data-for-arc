from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.d4ea5a7deae6 import generator


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
            for pair in row["train"]:
                yield as_grid(pair["input"]), as_grid(pair["output"])
            yield as_grid(row["test"]["input"]), as_grid(row["test"]["output"])


def frame_is_clipped(frame):
    r0, c0, r1, c1 = frame["bbox"]
    sr, sc, _ = frame["seeds"][0]
    token = frame["tokens"][0][2]
    return any(
        not (r0 < sr + dr < r1 and c0 < sc + dc < c1)
        for dr, dc in generator._kernel(token)
    )


class D4ea5a7deae6GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_have_complete_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            profiles.add(generator.canonical_profile_signature(grid))
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)

    def test_complete_profile_prior_is_substantive_and_stable(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                for offset in range(400):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 80)
                self.assertLessEqual(matches, 160)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )

    def test_general_path_witnesses_tokens_sizes_and_clipping(self):
        tokens = set()
        sizes = set()
        clipped = 0
        centered = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    seed * 17 + 7,
                    difficulty=band,
                )
                self.assertEqual(generator.self_check(grid), [])
                for frame in generator._frame_records(grid):
                    r0, c0, r1, c1 = frame["bbox"]
                    sizes.add((r1 - r0 + 1, c1 - c0 + 1))
                    tokens.add(frame["tokens"][0][2])
                    if frame_is_clipped(frame):
                        clipped += 1
                    else:
                        centered += 1
        self.assertEqual(tokens, {2, 3, 4})
        self.assertTrue({5, 6, 7}.issubset({h for h, _ in sizes}))
        self.assertTrue({4, 5, 6}.issubset({w for _, w in sizes}))
        self.assertGreater(clipped, 100)
        self.assertGreater(centered, 500)

    def test_boundaries_textures_and_strict_controls(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                self.assertEqual(
                    generator.generate(seed, seed, difficulty=band),
                    generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        texture="none",
                    ),
                )

        boundary_calls = (
            {"grid_h": 10},
            {"grid_h": 16},
            {"grid_w": 13},
            {"grid_w": 20},
            {"n_frames": 1},
            {"n_frames": 2},
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                if "grid_h" in kwargs:
                    self.assertEqual(len(grid), kwargs["grid_h"])
                if "grid_w" in kwargs:
                    self.assertEqual(len(grid[0]), kwargs["grid_w"])
                if "n_frames" in kwargs:
                    self.assertEqual(observed["n_frames"], kwargs["n_frames"])

        for texture in generator.PALETTE_KINDS:
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                generator.generate(7, 11, texture=texture)
            finally:
                base.set_ctx_observer(None)
            self.assertEqual(captured[-1]._drawn["texture"], texture)
            self.assertEqual(captured[-1]._drawn["palette_kind"], texture)

        clipped = generator.generate(3, 5, texture="clipped")
        centered = generator.generate(3, 5, texture="centered")
        self.assertTrue(
            all(frame_is_clipped(frame)
                for frame in generator._frame_records(clipped))
        )
        self.assertTrue(
            all(not frame_is_clipped(frame)
                for frame in generator._frame_records(centered))
        )

        bad_calls = (
            {"difficulty": "expert"},
            {"texture": "garbage"},
            {"palette_kind": "garbage"},
            {"bogus": 1},
            {"grid_h": "10"},
            {"grid_w": 13.0},
            {"n_frames": True},
            {"n_frames": 3},
            {"texture": "warm", "palette_kind": "cool"},
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
                self.assertEqual(ctx._drawn["grid_h"], len(grid))
                self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
                self.assertEqual(
                    ctx._drawn["n_frames"],
                    generator.observe_overrides(grid)["n_frames"],
                )
                self.assertIn(ctx._drawn["palette_kind"], generator.PALETTE_KINDS)
                self.assertEqual(ctx._drawn["texture"], "none")
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 150)

        for texture in generator.SEMANTIC_TEXTURES:
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(13, 29, texture=texture)
            finally:
                base.set_ctx_observer(None)
            ctx = captured[-1]
            self.assertEqual(ctx._drawn["texture"], texture)
            self.assertEqual(ctx._drawn["grid_h"], len(grid))
            self.assertEqual(ctx._drawn["grid_w"], len(grid[0]))
            self.assertEqual(
                ctx._drawn["n_frames"],
                generator.observe_overrides(grid)["n_frames"],
            )

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]

        opened = [row[:] for row in original]
        opened[1][2] = 0
        self.assertTrue(generator.self_check(opened))

        extra_token = [row[:] for row in original]
        extra_token[2][4] = 3
        self.assertTrue(
            any("tokens" in error for error in generator.self_check(extra_token))
        )

        outside = [row[:] for row in original]
        outside[9][9] = 7
        self.assertTrue(
            any("outside every frame" in error
                for error in generator.self_check(outside))
        )

        repeated_token = [row[:] for row in original]
        frames = generator._frame_records(repeated_token)
        r, c, _ = frames[1]["tokens"][0]
        repeated_token[r][c] = frames[0]["tokens"][0][2]
        self.assertTrue(
            any("same token" in error
                for error in generator.self_check(repeated_token))
        )

        repeated_seed = [row[:] for row in original]
        frames = generator._frame_records(repeated_seed)
        r, c, _ = frames[1]["seeds"][0]
        repeated_seed[r][c] = frames[0]["seeds"][0][2]
        self.assertTrue(
            any("same seed color" in error
                for error in generator.self_check(repeated_seed))
        )

        too_short = [row[:] for row in original[:-2]]
        self.assertTrue(
            any("height" in error for error in generator.self_check(too_short))
        )

    def test_lawful_cross_profile_token_recombination_is_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        frames = generator._frame_records(hybrid)
        first = frames[0]["tokens"][0]
        second = frames[1]["tokens"][0]
        hybrid[first[0]][first[1]] = second[2]
        hybrid[second[0]][second[1]] = first[2]
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNotNone(generator.rule_mirror(hybrid))
        self.assertFalse(generator.is_canonical_profile(hybrid))

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 99
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
