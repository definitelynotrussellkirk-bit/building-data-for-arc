from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.ee6ef749efca import generator


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


class Ee6ef749efcaGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.official_profiles = {
            generator.profile_signature(grid) for grid, _ in cls.pairs
        }

    def test_all_canonical_pairs_match_rule_and_complete_profiles(self):
        expected_profiles = {
            (10, 12, 2, ((0, 0), (0, 1), (1, 1), (1, 2)), False),
            (11, 11, 2, ((0, 0), (1, 0), (2, 0), (2, 1)), False),
            (12, 12, 3, ((0, 1), (1, 0), (1, 1), (1, 2)), False),
            (
                11,
                13,
                2,
                ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
                False,
            ),
            (
                12,
                13,
                3,
                ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
                False,
            ),
        }
        self.assertEqual(len(self.pairs), 5)
        self.assertEqual(self.official_profiles, expected_profiles)
        self.assertEqual(
            generator.CANONICAL_PROFILE_SIGNATURES,
            expected_profiles,
        )
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

    def test_explicit_none_is_identical_and_unknown_texture_rejects(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                omitted = generator.generate(seed, seed, difficulty=band)
                explicit = generator.generate(
                    seed,
                    seed,
                    difficulty=band,
                    texture="none",
                )
                self.assertEqual(omitted, explicit)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(0, 0, texture="bogus")

    def test_decoy_override_is_strict_and_exact(self):
        for raw, expected in (
            (True, True),
            (False, False),
            ("true", True),
            ("false", False),
        ):
            grid = generator.generate(0, 0, decoy=raw)
            self.assertEqual(
                generator.observe_overrides(grid)["decoy"],
                expected,
            )
        for invalid in ("yes", "0", "1", 0, 1):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "decoy must"):
                    generator.generate(0, 0, decoy=invalid)

    def test_forced_textures_record_exact_axis_provenance(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                for texture in (
                    "no_markers",
                    "no_decoy",
                    "packed_markers",
                ):
                    captured = []
                    base.set_ctx_observer(captured.append)
                    try:
                        grid = generator.generate(
                            seed,
                            seed,
                            difficulty=band,
                            texture=texture,
                        )
                    finally:
                        base.set_ctx_observer(None)
                    drawn = captured[-1]._drawn
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(
                        drawn["n_markers"],
                        observed["n_markers"],
                    )
                    self.assertEqual(drawn["decoy"], observed["decoy"])

        self.assertEqual(
            generator.observe_overrides(
                generator.generate(1, 1, texture="no_markers", n_markers=0)
            )["n_markers"],
            0,
        )
        self.assertFalse(
            generator.observe_overrides(
                generator.generate(1, 1, texture="no_decoy", decoy=False)
            )["decoy"]
        )
        self.assertEqual(
            generator.observe_overrides(
                generator.generate(1, 1, texture="packed_markers", n_markers=4)
            )["n_markers"],
            4,
        )
        for overrides in (
            {"texture": "no_markers", "n_markers": 1},
            {"texture": "no_decoy", "decoy": True},
            {"texture": "packed_markers", "n_markers": 3},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    generator.generate(1, 1, **overrides)

    def test_self_check_rejects_a_clipping_marker(self):
        grid = generator.generate(
            0,
            0,
            texture="no_markers",
            decoy=False,
        )
        self.assertEqual(generator.self_check(grid), [])
        template = max(generator._components(grid, 6), key=len)
        template_h = (
            max(r for r, _ in template) - min(r for r, _ in template) + 1
        )
        template_w = (
            max(c for _, c in template) - min(c for _, c in template) + 1
        )
        clipping_cell = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0
            and (
                r + template_h > len(grid)
                or c + template_w > len(grid[0])
            )
        )
        malformed = [row[:] for row in grid]
        malformed[clipping_cell[0]][clipping_cell[1]] = 2
        self.assertTrue(
            any(
                "clip the grid edge" in error
                for error in generator.self_check(malformed)
            )
        )

    def test_markers_are_separate_objects_and_self_check_enforces_it(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(160):
                grid = generator.generate(seed, seed, difficulty=band)
                h, w = len(grid), len(grid[0])
                for r in range(h):
                    for c in range(w):
                        if grid[r][c] != 2:
                            continue
                        neighbors = [
                            grid[r + dr][c + dc]
                            for dr in (-1, 0, 1)
                            for dc in (-1, 0, 1)
                            if (dr or dc)
                            and 0 <= r + dr < h
                            and 0 <= c + dc < w
                        ]
                        self.assertTrue(all(value == 0 for value in neighbors))

        grid = generator.generate(
            0,
            0,
            texture="no_markers",
            decoy=False,
        )
        template = max(generator._components(grid, 6), key=len)
        template_h = (
            max(r for r, _ in template) - min(r for r, _ in template) + 1
        )
        template_w = (
            max(c for _, c in template) - min(c for _, c in template) + 1
        )
        touching_cell = next(
            (r + dr, c + dc)
            for r, c in template
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr or dc)
            and 0 <= r + dr < len(grid)
            and 0 <= c + dc < len(grid[0])
            and grid[r + dr][c + dc] == 0
            and r + dr + template_h <= len(grid)
            and c + dc + template_w <= len(grid[0])
        )
        malformed = [row[:] for row in grid]
        malformed[touching_cell[0]][touching_cell[1]] = 2
        self.assertTrue(
            any(
                "touch another nonzero" in error
                for error in generator.self_check(malformed)
            )
        )

    def test_linked_canonical_prior_is_stable_in_every_band(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                witnessed = set()
                for offset in range(400):
                    seed = seed_start + offset
                    signature = generator.profile_signature(
                        generator.generate(
                            seed,
                            seed,
                            difficulty=band,
                        )
                    )
                    if signature in self.official_profiles:
                        matches += 1
                        witnessed.add(signature)
                self.assertEqual(witnessed, self.official_profiles)
                self.assertGreaterEqual(matches, 80)
                self.assertLessEqual(matches, 160)

    def test_lawful_cross_profile_recombination_is_not_canonical_like(self):
        recombined = generator.generate(
            7,
            7,
            grid_h=10,
            grid_w=12,
            n_markers=3,
            decoy=False,
        )
        self.assertEqual(generator.self_check(recombined), [])
        self.assertNotIn(
            generator.profile_signature(recombined),
            self.official_profiles,
        )

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                first = generator.generate(seed, seed, difficulty=band)
                second = generator.generate(seed, seed, difficulty=band)
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
