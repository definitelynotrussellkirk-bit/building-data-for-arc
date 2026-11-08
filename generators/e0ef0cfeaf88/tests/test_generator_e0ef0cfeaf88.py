from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

from puzzle_generators import base


ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA256 = load_selected_generator("e0ef0cfeaf88", root=ROOT)


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with canonical_path(ROOT).open() as handle:
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


class E0ef0cfeaf88GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        profiles = set()
        unique_inputs = set()
        tail_counts = set()
        tail_indices = set()
        colors = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            profiles.add(generator.canonical_profile_signature(grid))
            unique_inputs.add(tuple(map(tuple, grid)))
            scene = generator._analyze_scene(grid)
            tail_counts.add(len(scene["tails"]))
            tail_indices.update(scene["tail_indices"])
            colors.update(scene["colors"])
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 4)
        self.assertEqual(len(unique_inputs), 4)
        self.assertEqual(tail_counts, {1, 2, 3})
        self.assertEqual(tail_indices, {1, 2, 3})
        self.assertEqual(colors, {3, 4, 7, 8})

    def test_pinned_profile_floor_has_support_in_every_band(self):
        import hashlib

        for band in ("easy", "medium", "hard"):
            hits = 0
            for index in range(20):
                digest = hashlib.sha256(
                    f"profile-floor:v1:{generator.TASK_ID}:{band}:{index}".encode()
                ).hexdigest()
                seed = int(digest[:12], 16)
                sample_index = seed % 7919 + index
                grid = generator.generate(seed, sample_index, difficulty=band)
                hits += generator.is_canonical_profile(grid)
            self.assertGreaterEqual(hits, 1, band)

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(500):
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
                self.assertGreaterEqual(matches, 20)
                self.assertLessEqual(matches, 70)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 450)
                self.assertGreaterEqual(len(outputs), 450)

    def test_general_path_witnesses_every_tail_mask_and_color(self):
        tail_counts = set()
        masks = set()
        colors = set()
        for count in range(1, 5):
            for seed in range(180):
                grid = generator.generate(
                    seed,
                    seed * 31 + count,
                    difficulty="hard",
                    grid_h=20,
                    grid_w=20,
                    tail_count=count,
                )
                self.assertEqual(generator.self_check(grid), [])
                scene = generator._analyze_scene(grid)
                self.assertEqual(len(scene["tails"]), count)
                observed = generator.observe_overrides(grid)
                self.assertEqual(observed["tail_count"], count)
                tail_counts.add(count)
                masks.add(scene["tail_indices"])
                colors.update(scene["colors"])
        self.assertEqual(tail_counts, {1, 2, 3, 4})
        self.assertEqual(len(masks), 15)
        self.assertEqual(colors, set(range(1, 10)))

        for color in range(1, 10):
            grid = generator.generate(
                color,
                color * 101,
                grid_h=10,
                grid_w=10,
                tail_count=4,
                color=color,
            )
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.observe_overrides(grid),
                {
                    "grid_h": 10,
                    "grid_w": 10,
                    "tail_count": 4,
                    "color": color,
                },
            )
            self.assertNotEqual(generator.rule_mirror(grid), grid)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 10},
            {"grid_h": 20},
            {"grid_w": 10},
            {"grid_w": 20},
            {"tail_count": 1},
            {"tail_count": 4},
            {"color": 1},
            {"color": 9},
            {
                "grid_h": 10,
                "grid_w": 10,
                "tail_count": 4,
                "color": 9,
            },
            {
                "grid_h": 20,
                "grid_w": 20,
                "tail_count": 1,
                "color": 1,
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
            {"grid_h": "10"},
            {"grid_w": 10.0},
            {"tail_count": True},
            {"color": False},
            {"grid_h": 9},
            {"grid_h": 21},
            {"grid_w": 9},
            {"grid_w": 21},
            {"tail_count": 0},
            {"tail_count": 5},
            {"color": 0},
            {"color": 10},
            {"texture": "no_body"},
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

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        scene = generator._analyze_scene(original)
        r0, c0 = scene["body"]
        color = next(iter(scene["colors"]))

        broken_body = [row[:] for row in original]
        broken_body[r0][c0] = 0
        self.assertTrue(
            any(
                "2x2 body" in error
                for error in generator.self_check(broken_body)
            )
        )

        stray_tail = [row[:] for row in original]
        stray_tail[8][1] = color
        self.assertTrue(
            any(
                "diagonal positions" in error
                for error in generator.self_check(stray_tail)
            )
        )

        no_tails = [row[:] for row in original]
        for r, c in scene["tails"]:
            no_tails[r][c] = 0
        self.assertTrue(
            any(
                "1..4 tails" in error
                for error in generator.self_check(no_tails)
            )
        )

        second_color = [row[:] for row in original]
        tail_r, tail_c = next(iter(scene["tails"]))
        second_color[tail_r][tail_c] = 9 if color != 9 else 6
        self.assertTrue(
            any(
                "one nonzero color" in error
                for error in generator.self_check(second_color)
            )
        )

        second_body = [row[:] for row in original]
        for r in (7, 8):
            for c in (7, 8):
                second_body[r][c] = color
        self.assertTrue(
            any(
                "exactly one" in error
                for error in generator.self_check(second_body)
            )
        )

        edge_body = generator._paint_scene(10, 10, 2, 1, 2, (0,))
        self.assertTrue(
            any(
                "output cell" in error
                for error in generator.self_check(edge_body)
            )
        )

        invalid_color = [row[:] for row in original]
        invalid_color[r0][c0] = 10
        self.assertTrue(
            any(
                "ARC colors" in error
                for error in generator.self_check(invalid_color)
            )
        )

    def test_lawful_recombination_is_not_a_public_profile(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        scene = generator._analyze_scene(hybrid)
        r0, c0 = scene["body"]
        dr, dc = generator._TAIL_OFFSETS[0]
        hybrid[r0 + dr][c0 + dc] = next(iter(scene["colors"]))
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertNotEqual(
            generator.rule_mirror(hybrid),
            generator.rule_mirror(grid),
        )
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


if __name__ == "__main__":
    unittest.main()
