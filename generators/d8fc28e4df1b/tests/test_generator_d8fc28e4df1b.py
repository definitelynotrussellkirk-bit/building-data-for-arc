"""Focused semantic regressions for generator d8fc28e4df1b."""
from __future__ import annotations

from collections import Counter
import copy
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "d8fc28e4df1b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]
BANDS = ("easy", "medium", "hard")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _pairs():
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


class GeneratorD8fc28e4df1bTests(unittest.TestCase):
    def test_all_canonical_pairs_are_accepted_and_linked_exactly(self):
        pairs = _pairs()
        self.assertEqual(3, len(pairs))
        signatures = set()
        counts = set()
        for pair in pairs:
            source = pair["input"]
            self.assertEqual([], MODULE.self_check(source))
            signature = MODULE.canonical_profile_signature(source)
            signatures.add(signature)
            counts.add(MODULE._count_vector(source))
            expected = [[8 if bit == "1" else 0 for bit in MODULE._winner_mask(MODULE._count_vector(source))]]
            self.assertEqual(expected, pair["output"])
        expected_signatures = {
            (7, (3, 7, 7, 7), MODULE._CANONICAL_TEMPLATE, (1, 2, 1)),
            (8, (3, 8, 8, 8), MODULE._CANONICAL_TEMPLATE, (3, 2, 1)),
            (8, (3, 8, 8, 8), MODULE._CANONICAL_TEMPLATE, (2, 3, 1)),
        }
        self.assertEqual(expected_signatures, signatures)
        self.assertEqual({(1, 2, 1), (3, 2, 1), (2, 3, 1)}, counts)

    def test_default_census_is_lawful_and_exercises_semantic_branches(self):
        official = {
            (h, (3, w, w, w), MODULE._CANONICAL_TEMPLATE, counts)
            for h, w, counts in MODULE._CANONICAL_PROFILES
        }
        for band_index, band in enumerate(BANDS):
            masks = Counter()
            rotations = Counter()
            palettes = Counter()
            heights = Counter()
            widths = Counter()
            motif_sizes = Counter()
            maxima = Counter()
            linked = Counter()
            inputs = set()
            for i in range(240):
                grid = MODULE.generate(
                    10_000 * (band_index + 1) + i,
                    i * 17 + 5,
                    difficulty=band,
                )
                self.assertEqual([], MODULE.self_check(grid, difficulty=band))
                observed = MODULE.observe_overrides(grid)
                masks[observed["winner_mask"]] += 1
                palettes[observed["palette_kind"]] += 1
                heights[observed["panel_h"]] += 1
                widths[observed["candidate_w"]] += 1
                motif_sizes[observed["motif_cells"]] += 1
                maxima[observed["max_count"]] += 1
                inputs.add(_freeze(grid))
                signature = MODULE.canonical_profile_signature(grid)
                if signature in official:
                    linked[signature] += 1
                panels, _ = MODULE._split_panels(grid)
                template = MODULE._crop_nonzero(panels[0])
                for panel in panels[1:]:
                    for rotation, _row, _col in MODULE._match_locations(panel, template):
                        rotations[rotation] += 1
            with self.subTest(band=band):
                self.assertEqual(set(MODULE.WINNER_MASKS), set(masks))
                self.assertEqual({0, 1, 2, 3}, set(rotations))
                self.assertEqual(set(MODULE.PALETTE_KINDS), set(palettes))
                self.assertGreaterEqual(len(linked), 3)
                self.assertGreaterEqual(sum(linked.values()), 45)
                self.assertGreaterEqual(len(inputs), 230)
                self.assertTrue(set(heights).issubset({7, 8, 9}))
                self.assertTrue(set(widths).issubset({7, 8}))
                self.assertTrue(set(motif_sizes).issubset({5, 6, 7}))
                self.assertTrue(set(maxima).issubset({1, 2, 3}))

    def test_explicit_override_observations_are_exact_at_boundaries(self):
        cases = (
            {
                "panel_h": 7,
                "candidate_w": 7,
                "motif_cells": 5,
                "max_count": 1,
                "winner_mask": "100",
                "palette_kind": "classic",
            },
            {
                "panel_h": 9,
                "candidate_w": 8,
                "motif_cells": 7,
                "max_count": 3,
                "winner_mask": "111",
                "palette_kind": "novel",
            },
            {
                "panel_h": 8,
                "candidate_w": 7,
                "motif_cells": 6,
                "max_count": 2,
                "winner_mask": "011",
                "palette_kind": "cool",
            },
        )
        for index, overrides in enumerate(cases):
            for band in BANDS:
                with self.subTest(index=index, band=band):
                    grid = MODULE.generate(80_000 + index, 31 + index, difficulty=band, **overrides)
                    self.assertEqual(overrides, MODULE.observe_overrides(grid))
                    self.assertEqual([], MODULE.self_check(grid, difficulty=band, meta={"overrides": overrides}))

    def test_sample_index_schedule_reaches_singletons_then_ties(self):
        observed = []
        seed = 91_000
        for sample_index in range(7):
            grid = MODULE.generate(
                seed,
                sample_index,
                difficulty="medium",
            )
            observed.append(MODULE.observe_overrides(grid)["winner_mask"])
        expected = [
            MODULE.WINNER_MASKS[(seed + sample_index) % len(MODULE.WINNER_MASKS)]
            for sample_index in range(7)
        ]
        self.assertEqual(expected, observed)

    def test_structural_checker_rejects_four_nearest_impostors(self):
        base = copy.deepcopy(_pairs()[0]["input"])
        mutations = []

        missing_separator = copy.deepcopy(base)
        for row in missing_separator:
            row[3] = 0
        mutations.append(missing_separator)

        blank_template = copy.deepcopy(base)
        for row in blank_template:
            row[:3] = [0, 0, 0]
        mutations.append(blank_template)

        blank_candidates = copy.deepcopy(base)
        for row in blank_candidates:
            for start, width in ((4, 7), (12, 7), (20, 7)):
                row[start:start + width] = [0] * width
        mutations.append(blank_candidates)

        one_color_template = copy.deepcopy(base)
        for row in one_color_template:
            for col in range(3):
                if row[col] == 7:
                    row[col] = 2
        mutations.append(one_color_template)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(MODULE.self_check(mutation))

    def test_cross_profile_recombination_is_lawful_but_not_official(self):
        recombined = copy.deepcopy(_pairs()[0]["input"])
        new_row = [0] * len(recombined[0])
        for separator in (3, 11, 19):
            new_row[separator] = 9
        recombined.append(new_row)
        self.assertTrue(MODULE.self_check(recombined))
        official = {
            (h, (3, w, w, w), MODULE._CANONICAL_TEMPLATE, counts)
            for h, w, counts in MODULE._CANONICAL_PROFILES
        }
        self.assertNotIn(MODULE.canonical_profile_signature(recombined), official)

    def test_generated_lessons_rebut_the_densest_candidate_shortcut(self):
        for band in BANDS:
            for seed in range(80):
                grid = MODULE.generate(120_000 + seed, seed * 9 + 4, difficulty=band)
                panels, _ = MODULE._split_panels(grid)
                densities = [
                    sum(value not in (0, 9) for row in panel for value in row)
                    for panel in panels[1:]
                ]
                maximum = max(densities)
                density_mask = "".join("1" if value == maximum else "0" for value in densities)
                true_mask = MODULE.observe_overrides(grid)["winner_mask"]
                self.assertNotEqual(density_mask, true_mask)

    def test_absent_replacement_recombination_is_rejected(self):
        mutation = copy.deepcopy(_pairs()[0]["input"])
        remaining_colors = {value for row in mutation for value in row}
        replacement = next(color for color in range(1, 9) if color not in remaining_colors)
        for row in mutation:
            for col in range(3):
                if row[col] == 7:
                    row[col] = replacement
        self.assertNotIn(replacement, {value for row in mutation for value in row[4:]})
        self.assertTrue(MODULE.self_check(mutation))

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(20260724)
        state = random.getstate()
        first = MODULE.generate(101, 203, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MODULE.generate(101, 203, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = MODULE.generate(101, 203, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
