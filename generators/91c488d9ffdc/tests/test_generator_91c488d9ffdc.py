"""Portable regression tests for the opposite-corners-to-outlines generator."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import random
from pathlib import Path
import unittest

gen = importlib.import_module("puzzle_generators.per_puzzle.91c488d9ffdc.generator")
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)


class RectangleOutlineGeneratorTests(unittest.TestCase):
    def test_canonical_authority_is_pinned_and_mirrored(self):
        self.assertEqual("515ca330e152", gen.RULE_HASH)
        pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
        self.assertEqual(5, len(pairs))
        signatures = set()
        for pair in pairs:
            with self.subTest(split=pair["split"], pair_index=pair["pair_index"]):
                self.assertEqual([], gen.self_check(pair["input"]))
                self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))
                signatures.add(gen._analyze(pair["input"])["signature"])
        self.assertEqual(gen._CANONICAL_SIGNATURES, signatures)

    def test_exact_override_axes_and_unknown_key_contract(self):
        for h in (7, 12):
            for w in (7, 12):
                for n_rects in (1, 3):
                    grid = gen.generate(
                        91,
                        14,
                        difficulty="easy",
                        grid_h=h,
                        grid_w=w,
                        n_rects=n_rects,
                    )
                    self.assertEqual([], gen.self_check(grid))
                    self.assertEqual(
                        {"grid_h": h, "grid_w": w, "n_rects": n_rects},
                        gen.observe_overrides(grid),
                    )
        for bad in (True, 8.0, "8"):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    gen.generate(1, 2, grid_h=bad)
        with self.assertRaisesRegex((TypeError, ValueError), "unknown override"):
            gen.generate(1, 2, misspelled_axis=8)

    def test_generation_never_clamps_or_drops_requested_rectangles(self):
        for band in ("easy", "medium", "hard"):
            for index in range(120):
                grid = gen.generate(7000 + index, index, difficulty=band)
                with self.subTest(band=band, index=index):
                    self.assertEqual([], gen.self_check(grid, difficulty=band))
                    observed = gen.observe_overrides(grid)
                    nonzero = {value for row in grid for value in row if value}
                    self.assertEqual(observed["n_rects"], len(nonzero))
                    self.assertTrue(1 <= observed["n_rects"] <= 2)

    def test_every_three_draw_window_teaches_declared_rivals(self):
        for band in ("easy", "medium", "hard"):
            for start in range(18):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(555, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    555, start + gen.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                with self.subTest(band=band, start=start):
                    self.assertEqual([], gen.lesson_identifiable(demos, query))
                    observables = [gen.semantic_observables(d["input"]) for d in demos]
                    self.assertTrue(any(o["strict_canonical"] for o in observables))
                    self.assertTrue(any(o["has_negative_slant"] for o in observables))
                    self.assertTrue(any(o["multiple_rectangles"] for o in observables))

    def test_workspace_schedule_probe_enumerates_windows(self):
        probe_path = (
            Path(__file__).resolve().parents[1]
            / "workspace"
            / "probe_schedule_windows.py"
        )
        spec = importlib.util.spec_from_file_location(
            "probe_schedule_windows_91c488d9ffdc", probe_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)

        report = probe.probe_schedule(seed=555, starts=6)
        self.assertEqual(18, report["summary"]["windows_checked"])
        self.assertEqual(0, report["summary"]["unidentifiable_windows"])
        self.assertEqual(
            {"canonical-positive", "negative", "mixed"},
            set(report["summary"]["profiles_seen"]),
        )

    def test_positive_slant_shortcut_fits_canonical_but_not_curriculum(self):
        for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
            self.assertEqual(pair["output"], gen._positive_slant_only(pair["input"]))
        grid = gen.generate(19, 1, difficulty="medium")
        self.assertTrue(gen.semantic_observables(grid)["has_negative_slant"])
        self.assertNotEqual(gen.rule_mirror(grid), gen._positive_slant_only(grid))

    def test_structural_checker_rejects_targeted_impostors(self):
        lawful = gen.generate(1234, 17, difficulty="medium")
        self.assertEqual([], gen.self_check(lawful))

        blank = [[0 for _ in row] for row in lawful]
        singleton = copy.deepcopy(lawful)
        first_color = next(value for row in singleton for value in row if value)
        removed = False
        for row in singleton:
            for column, value in enumerate(row):
                if value == first_color and not removed:
                    row[column] = 0
                    removed = True
                    break
            if removed:
                break

        collinear = [[0] * 8 for _ in range(7)]
        collinear[1][1] = collinear[1][6] = 2

        too_small = [[0] * 8 for _ in range(7)]
        too_small[1][1] = too_small[2][4] = 2

        intersecting_borders = [[0] * 8 for _ in range(7)]
        intersecting_borders[0][0] = intersecting_borders[4][4] = 2
        intersecting_borders[0][4] = intersecting_borders[4][0] = 7

        third_copy = copy.deepcopy(lawful)
        placed = False
        for r, row in enumerate(third_copy):
            for c, value in enumerate(row):
                if value == 0:
                    third_copy[r][c] = first_color
                    placed = True
                    break
            if placed:
                break

        for name, grid in {
            "blank": blank,
            "singleton": singleton,
            "collinear": collinear,
            "too_small": too_small,
            "intersecting_borders": intersecting_borders,
            "third_copy": third_copy,
        }.items():
            with self.subTest(name=name):
                self.assertTrue(gen.self_check(grid))

    def test_difficulty_bands_have_observable_palette_effect(self):
        for index in range(12):
            easy = gen.generate(404, index, difficulty="easy")
            medium = gen.generate(404, index, difficulty="medium")
            hard = gen.generate(404, index, difficulty="hard")
            easy_colors = {v for row in easy for v in row if v}
            hard_colors = {v for row in hard for v in row if v}
            with self.subTest(index=index):
                self.assertTrue(easy_colors and max(easy_colors) <= 4)
                self.assertTrue(hard_colors and min(hard_colors) >= 5)
                self.assertNotEqual(easy, hard)
                self.assertEqual([], gen.self_check(medium))

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
