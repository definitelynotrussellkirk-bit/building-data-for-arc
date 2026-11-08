from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.ead22faa41ef import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split) or []:
                    yield pair["input"], pair["output"]


class Ead22faa41efGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        directions = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
            features = generator._scene_features(grid)
            directions.update(
                name
                for name in generator._DIRECTION_DELTAS
                if features["directions"][name]
            )
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )
        self.assertEqual(directions, set(generator._DIRECTION_DELTAS))

    def test_complete_profile_prior_is_stable_on_two_ranges(self):
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
                    self.assertEqual(generator.self_check(grid), [])
                    output = generator.rule_mirror(grid)
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
                self.assertGreaterEqual(matches, 40)
                self.assertLessEqual(matches, 110)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 570)

    def test_every_direction_mode_is_exact_and_semantically_live(self):
        for direction in generator._DIRECTION_MODES:
            for height, width in ((3, 3), (3, 14), (14, 3), (14, 14)):
                grid = generator.generate(
                    height * 101 + width,
                    width * 103 + height,
                    difficulty="hard",
                    grid_h=height,
                    grid_w=width,
                    pair_direction=direction,
                )
                observed = generator.observe_overrides(grid)
                self.assertEqual(observed, {
                    "grid_h": height,
                    "grid_w": width,
                    "pair_direction": direction,
                })
                features = generator._scene_features(grid)
                present = {
                    name
                    for name in generator._DIRECTION_DELTAS
                    if features["directions"][name]
                }
                if direction == "mixed":
                    self.assertGreaterEqual(len(present), 2)
                else:
                    self.assertEqual(present, {direction})

    def test_rule_changes_only_opposite_color_adjacencies(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                h, w = len(grid), len(grid[0])
                for r in range(h):
                    for c in range(w):
                        neighbors = [
                            grid[rr][cc]
                            for _name, rr, cc in generator._neighbors(
                                r, c, h, w
                            )
                        ]
                        expected = grid[r][c]
                        if expected == 3 and 2 in neighbors:
                            expected = 8
                        elif expected == 2 and 3 in neighbors:
                            expected = 0
                        self.assertEqual(output[r][c], expected)

    def test_lawful_cross_profile_recombination_is_not_canonical(self):
        hybrid = [
            [3, 2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 2, 3, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 3, 2],
            [5, 0, 0, 0, 0, 5],
        ]
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertIsNone(generator.canonical_profile_signature(hybrid))
        self.assertEqual(
            Counter(v for row in generator.rule_mirror(hybrid) for v in row)[8],
            3,
        )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 3},
            {"grid_h": 14},
            {"grid_w": 3},
            {"grid_w": 14},
            {"pair_direction": "up"},
            {"pair_direction": "down"},
            {"pair_direction": "left"},
            {"pair_direction": "right"},
            {"pair_direction": "mixed"},
            {"grid_h": 3, "grid_w": 3},
            {"grid_h": 3, "grid_w": 14},
            {"grid_h": 14, "grid_w": 3},
            {"grid_h": 14, "grid_w": 14},
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
            {"grid_h": "3"},
            {"grid_w": 3.0},
            {"grid_h": True},
            {"grid_h": 2},
            {"grid_h": 15},
            {"grid_w": 2},
            {"grid_w": 15},
            {"pair_direction": 1},
            {"pair_direction": "horizontal"},
            {"texture": "all_pairs"},
            {"n_pairs": 2},
            {"distractor_color": 5},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_default_profile_and_forced_paths_record_exact_provenance(self):
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
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 50)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=14,
                grid_w=3,
                pair_direction="left",
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
                "grid_h": 14,
                "grid_w": 3,
                "pair_direction": "left",
            },
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            grid_h=7,
            grid_w=7,
            pair_direction="right",
        )
        mutations = []

        no_pair = [[0] * 7 for _ in range(7)]
        no_pair[0][0] = 3
        no_pair[6][6] = 2
        mutations.append(no_pair)

        cluster = [[0] * 7 for _ in range(7)]
        cluster[3][3] = 3
        cluster[3][2] = 2
        cluster[3][4] = 2
        mutations.append(cluster)

        forbidden = [row[:] for row in valid]
        forbidden[0][0] = 7
        mutations.append(forbidden)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[3, 2], [0, 0]])
        mutations.append([[3, 2, 0] for _ in range(15)])
        mutations.append([[3, 2] + [0] * 13 for _ in range(3)])

        too_many_fives = [row[:] for row in valid]
        written = 0
        for r in range(7):
            for c in range(7):
                if too_many_fives[r][c] == 0 and written < 6:
                    too_many_fives[r][c] = 5
                    written += 1
        mutations.append(too_many_fives)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_order_size_and_cover_negative_and_boundary_branches(self):
        means = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            pairs = set()
            directions = Counter()
            lone3_seen = lone2_seen = pair_edge_seen = 0
            zero_lone_seen = 0
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
                h, w = len(grid), len(grid[0])
                areas.append(h * w)
                features = generator._scene_features(grid)
                signature = features["signature"]
                lone3_seen += signature[7] > 0
                lone2_seen += signature[8] > 0
                zero_lone_seen += signature[7] == 0 and signature[8] == 0
                pair_edge_seen += signature[13] > 0
                for name in generator._DIRECTION_DELTAS:
                    directions[name] += features["directions"][name] > 0
            means[band] = sum(areas) / len(areas)
            self.assertGreaterEqual(len(pairs), 570)
            self.assertGreater(lone3_seen, 40)
            self.assertGreater(lone2_seen, 40)
            self.assertGreater(zero_lone_seen, 5)
            self.assertGreater(pair_edge_seen, 150)
            for name in generator._DIRECTION_DELTAS:
                self.assertGreater(directions[name], 80)
        self.assertLess(means["easy"], means["medium"])
        self.assertLess(means["medium"], means["hard"])

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
