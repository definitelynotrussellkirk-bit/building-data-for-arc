from __future__ import annotations

import random
import unittest

from puzzle_generators import base
from puzzle_generators.per_puzzle.d6607fc42bcc import generator
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


ROOT = find_root(__file__)


def canonical_pairs():
    seen = set()
    for pair in load_canonical_pairs(
        generator.TASK_ID, root=ROOT, labeled_only=True
    ):
        grid = pair["input"]
        output = pair["output"]
        key = (tuple(map(tuple, grid)), tuple(map(tuple, output)))
        if key not in seen:
            seen.add(key)
            yield grid, output


class D6607fc42bccGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_have_complete_profiles_and_match_rule(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            profiles.add(generator.canonical_profile_signature(grid))
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 4)

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
                self.assertLessEqual(matches, 165)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )

    def test_general_path_witnesses_full_lawful_geometry(self):
        heights = set()
        widths = set()
        openings = set()
        notch_columns = set()
        dot_rows = set()
        frame_counts = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = generator.generate(
                    seed,
                    seed * 31 + 7,
                    difficulty=band,
                    grid_h={"easy": 12, "medium": 15, "hard": 18}[band],
                    grid_w={"easy": 12, "medium": 15, "hard": 18}[band],
                )
                self.assertEqual(generator.self_check(grid), [])
                frames = generator._u_frame_records(grid)
                frame_counts.add(len(frames))
                for frame in frames:
                    r0, c0, r1, c1 = frame["bbox"]
                    dot_r, _, _ = frame["dots"][0]
                    heights.add(r1 - r0 + 1)
                    widths.add(c1 - c0 + 1)
                    openings.add(frame["opening"])
                    notch_columns.add(frame["gap_c"] - c0)
                    dot_rows.add(dot_r - r0)
        self.assertEqual(heights, {3, 4, 5, 6})
        self.assertEqual(widths, {5, 6, 7})
        self.assertEqual(openings, {"top", "bottom"})
        self.assertTrue({1, 2, 3, 4, 5}.issubset(notch_columns))
        self.assertTrue({1, 2, 3, 4}.issubset(dot_rows))
        self.assertEqual(frame_counts, {1, 2})

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
            {"grid_h": 18},
            {"grid_w": 10},
            {"grid_w": 18},
            {"frame_count": 1},
            {"frame_count": 2},
            {"grid_h": 10, "grid_w": 10, "frame_count": 2},
            {"grid_h": 18, "grid_w": 18, "frame_count": 1},
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
                if "frame_count" in kwargs:
                    self.assertEqual(
                        observed["frame_count"],
                        kwargs["frame_count"],
                    )

        for texture in generator.PALETTE_KINDS:
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                generator.generate(7, 11, texture=texture)
            finally:
                base.set_ctx_observer(None)
            self.assertEqual(captured[-1]._drawn["texture"], texture)
            self.assertEqual(captured[-1]._drawn["palette_kind"], texture)

        top = generator.generate(3, 5, texture="top_open")
        bottom = generator.generate(3, 5, texture="bottom_open")
        self.assertTrue(
            all(
                frame["opening"] == "top"
                for frame in generator._u_frame_records(top)
            )
        )
        self.assertTrue(
            all(
                frame["opening"] == "bottom"
                for frame in generator._u_frame_records(bottom)
            )
        )

        bad_calls = (
            {"difficulty": "expert"},
            {"texture": "garbage"},
            {"palette_kind": "garbage"},
            {"bogus": 1},
            {"grid_h": "10"},
            {"grid_w": 10.0},
            {"frame_count": True},
            {"grid_h": 9},
            {"grid_w": 19},
            {"frame_count": 3},
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
                    ctx._drawn["frame_count"],
                    generator.observe_overrides(grid)["frame_count"],
                )
                self.assertIn(
                    ctx._drawn["palette_kind"],
                    generator.PALETTE_KINDS,
                )
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
                ctx._drawn["frame_count"],
                generator.observe_overrides(grid)["frame_count"],
            )

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        frame = generator._u_frame_records(original)[0]
        r0, c0, r1, c1 = frame["bbox"]
        dot_r, dot_c, dot_color = frame["dots"][0]

        wide_notch = [row[:] for row in original]
        wide_notch[r0][c0 + 1] = 0
        self.assertTrue(generator.self_check(wide_notch))

        misaligned = [row[:] for row in original]
        misaligned[dot_r][dot_c] = 0
        misaligned[dot_r][c0 + 1] = dot_color
        self.assertTrue(
            any(
                "aligned" in error
                for error in generator.self_check(misaligned)
            )
        )

        both_edges_open = [row[:] for row in original]
        both_edges_open[r1][c0 + 2] = 0
        self.assertTrue(generator.self_check(both_edges_open))

        extra_dot = [row[:] for row in original]
        extra_dot[r1 - 1][c1 - 1] = 9
        self.assertTrue(
            any("dots" in error for error in generator.self_check(extra_dot))
        )

        outside = [row[:] for row in original]
        outside[0][9] = 7
        self.assertTrue(
            any(
                "outside every frame" in error
                for error in generator.self_check(outside)
            )
        )

        no_projection_room = generator._template_from_profile(
            generator._PROFILE_SPECS[1]
        )
        shifted = [[0] * 10 for _ in range(10)]
        source_frame = generator._u_frame_records(no_projection_room)[0]
        sr0, sc0, sr1, sc1 = source_frame["bbox"]
        for r in range(sr0, sr1 + 1):
            for c in range(sc0, sc1 + 1):
                shifted[r - 1][c] = no_projection_room[r][c]
        self.assertTrue(
            any(
                "no row above" in error
                for error in generator.self_check(shifted)
            )
        )

        touching = [row[:] for row in original]
        first, second = generator._u_frame_records(touching)
        bridge_r = first["bbox"][2] + 1
        touching[bridge_r][first["bbox"][1]] = 1
        self.assertTrue(generator.self_check(touching))

    def test_lawful_notch_recombination_is_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        frame = generator._u_frame_records(hybrid)[0]
        r0, c0, _, _ = frame["bbox"]
        dot_r, dot_c, dot_color = frame["dots"][0]
        hybrid[r0][frame["gap_c"]] = 1
        hybrid[r0][c0 + 1] = 0
        hybrid[dot_r][dot_c] = 0
        hybrid[dot_r][c0 + 1] = dot_color
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
