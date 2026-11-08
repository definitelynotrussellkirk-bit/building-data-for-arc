from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e07bbcbe6ba4 import generator


ROOT = Path(__file__).resolve().parents[1]


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
                    grid = pair["input"]
                    if grid and isinstance(grid[0], str):
                        grid = [
                            [int(value) for value in source_row]
                            for source_row in grid
                        ]
                    output = pair.get("output")
                    if output and isinstance(output[0], str):
                        output = [
                            [int(value) for value in source_row]
                            for source_row in output
                        ]
                    yield grid, output


class E07bbcbe6ba4GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.official_profiles = {
            generator.profile_signature(grid) for grid, _ in cls.pairs
        }

    def test_all_canonical_pairs_match_mirror_and_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        self.assertEqual(
            self.official_profiles,
            {
                (15, 15, 9, 9, False),
                (15, 15, 9, 9, True),
            },
        )
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)

    def test_cross_axis_frame_override_records_final_free_canvas(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                        frame_h=12,
                        frame_w=12,
                    )
                finally:
                    base.set_ctx_observer(None)
                drawn = captured[-1]._drawn
                observed = generator.observe_overrides(grid)
                self.assertEqual(drawn["grid_h"], len(grid))
                self.assertEqual(drawn["grid_w"], len(grid[0]))
                self.assertEqual(drawn["frame_h"], observed["frame_h"])
                self.assertEqual(drawn["frame_w"], observed["frame_w"])
                self.assertEqual(
                    drawn["marker_edge"],
                    observed["marker_edge"],
                )

    def test_marker_edge_override_is_strict_and_exact(self):
        for raw, expected in (
            (True, True),
            (False, False),
            ("true", True),
            ("false", False),
        ):
            grid = generator.generate(0, 0, marker_edge=raw)
            self.assertEqual(
                generator.observe_overrides(grid)["marker_edge"],
                expected,
            )
        for invalid in ("bogus", "yes", "0", 0, 1):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "marker_edge must"):
                    generator.generate(0, 0, marker_edge=invalid)

    def test_linked_canonical_prior_is_stable_in_every_band(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                witnessed = set()
                for offset in range(400):
                    seed = seed_start + offset
                    grid = generator.generate(
                        seed,
                        seed,
                        difficulty=band,
                    )
                    signature = generator.profile_signature(grid)
                    if signature in self.official_profiles:
                        matches += 1
                        witnessed.add(signature)
                self.assertEqual(witnessed, self.official_profiles)
                self.assertGreaterEqual(matches, 80)
                self.assertLessEqual(matches, 165)

    def test_lawful_cross_profile_recombination_is_not_canonical_like(self):
        recombined = generator.generate(
            7,
            7,
            grid_h=15,
            grid_w=15,
            frame_h=9,
            frame_w=10,
            marker_edge=True,
        )
        self.assertEqual(generator.self_check(recombined), [])
        self.assertNotIn(
            generator.profile_signature(recombined),
            self.official_profiles,
        )

    def test_self_check_boundaries_and_deterministic_fresh_returns(self):
        grid = generator.generate(
            0,
            0,
            grid_h=9,
            grid_w=9,
            frame_h=7,
            frame_w=7,
            marker_edge=True,
        )
        self.assertEqual(generator.self_check(grid), [])
        touches_edge = [row[:] for row in grid]
        for row in range(len(touches_edge) - 1):
            touches_edge[row] = touches_edge[row + 1][:]
        touches_edge[-1] = [0] * len(touches_edge[0])
        self.assertTrue(generator.self_check(touches_edge))

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
