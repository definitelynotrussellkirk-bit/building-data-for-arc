"""Focused regression tests for the rectangle-outline generator repair."""
from __future__ import annotations

import copy
import random
import unittest

from puzzle_generators.per_puzzle.cd29a4f28d02 import generator as gen
from scripts.canonical_profile_gate import _pinned_seed, canonical_pairs


class RectangleOutlineGeneratorTests(unittest.TestCase):
    def test_canonical_inputs_are_accepted_and_profiles_are_exact(self):
        pairs = canonical_pairs(gen.TASK_ID)
        self.assertEqual(5, len(pairs))
        observed = set()
        for pair in pairs:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))
            observed.add(gen._analyze(pair["input"])["signature"])
        self.assertEqual(gen._CANONICAL_SIGNATURES, observed)

    def test_structural_checker_rejects_targeted_impostors(self):
        lawful = gen.generate(1234, 17, difficulty="medium")
        self.assertEqual([], gen.self_check(lawful))

        blank = [[0 for _ in row] for row in lawful]
        singleton = copy.deepcopy(lawful)
        first_color = next(v for row in singleton for v in row if v)
        removed = False
        for row in singleton:
            for c, value in enumerate(row):
                if value == first_color and not removed:
                    row[c] = 0
                    removed = True
                    break
            if removed:
                break

        collinear = [[0] * 8 for _ in range(7)]
        collinear[1][1] = collinear[1][6] = 2
        collinear[3][1] = 7
        collinear[5][5] = 7

        overlapping = [[0] * 8 for _ in range(7)]
        overlapping[0][0] = overlapping[4][4] = 2
        overlapping[1][1] = overlapping[5][5] = 7

        no_interior = [[0] * 8 for _ in range(7)]
        no_interior[0][0] = no_interior[2][1] = 2
        no_interior[3][3] = no_interior[5][4] = 7

        for name, grid in {
            "blank": blank,
            "singleton": singleton,
            "collinear": collinear,
            "overlapping": overlapping,
            "no_interior": no_interior,
        }.items():
            with self.subTest(name=name):
                self.assertTrue(gen.self_check(grid))

    def test_strict_profile_floor_and_disjoint_stability_census(self):
        for offset in (0, 10_000):
            for band in ("easy", "medium", "hard"):
                hits = 0
                for index in range(200):
                    seed = _pinned_seed(gen.TASK_ID, band, index + offset)
                    grid = gen.generate(
                        seed,
                        seed % 7919 + index + offset,
                        difficulty=band,
                    )
                    self.assertEqual([], gen.self_check(grid, difficulty=band))
                    hits += not gen.strict_canonical_like(grid)
                with self.subTest(offset=offset, band=band, hits=hits):
                    self.assertGreaterEqual(hits, 10)

    def test_axes_are_exact_at_boundaries_and_unknown_keys_reject(self):
        for h in (7, 10):
            for w in (8, 10):
                for palette_kind in gen.PALETTE_KINDS:
                    grid = gen.generate(
                        91,
                        14,
                        difficulty="easy",
                        grid_h=h,
                        grid_w=w,
                        palette_kind=palette_kind,
                    )
                    self.assertEqual(
                        {
                            "grid_h": h,
                            "grid_w": w,
                            "palette_kind": palette_kind,
                        },
                        gen.observe_overrides(grid),
                    )
        with self.assertRaisesRegex(ValueError, "unknown override"):
            gen.generate(1, 2, misspelled_axis="value")

    def test_three_draw_schedule_kills_positive_slant_only_shortcut(self):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(555, sample_index, difficulty="medium")
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                555,
                start + gen.EXAMPLES_NEEDED,
                difficulty="medium",
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            with self.subTest(start=start):
                self.assertEqual([], gen.lesson_identifiable(demos, query))
                self.assertTrue(
                    any(
                        gen._positive_slant_only(demo["input"])
                        != demo["output"]
                        for demo in demos
                    )
                )

    def test_canonical_shortcut_matches_official_but_generated_negative_refutes(self):
        for pair in canonical_pairs(gen.TASK_ID):
            self.assertEqual(
                pair["output"],
                gen._positive_slant_only(pair["input"]),
            )
        grid = gen.generate(19, 1, difficulty="easy")
        self.assertTrue(gen.semantic_observables(grid)["has_negative_slant"])
        self.assertNotEqual(gen.rule_mirror(grid), gen._positive_slant_only(grid))

    def test_replay_fresh_returns_and_global_rng_purity(self):
        random.seed(778899)
        state = random.getstate()
        first = gen.generate(101, 202, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = gen.generate(101, 202, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
