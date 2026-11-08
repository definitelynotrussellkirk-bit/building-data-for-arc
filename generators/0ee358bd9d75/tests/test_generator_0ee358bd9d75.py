"""Focused regressions for the 780d0b14 linked-section generator."""

from __future__ import annotations

from collections import Counter
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_pairs as public_canonical_pairs
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "0ee358bd9d75", root=ROOT
)


def canonical_pairs():
    for pair in public_canonical_pairs(generator.TASK_ID, root=ROOT):
        yield pair["input"], pair["output"]


def independent_signature(grid):
    """Returned-grid-only strict extractor, independent of generator helpers."""
    h, w = len(grid), len(grid[0])
    zero_rows = [r for r in range(h) if all(value == 0 for value in grid[r])]
    zero_cols = [
        c for c in range(w) if all(grid[r][c] == 0 for r in range(h))
    ]
    row_bounds = [-1, *zero_rows, h]
    col_bounds = [-1, *zero_cols, w]
    row_sizes = tuple(
        right - left - 1 for left, right in zip(row_bounds, row_bounds[1:])
    )
    col_sizes = tuple(
        right - left - 1 for left, right in zip(col_bounds, col_bounds[1:])
    )
    modes = []
    for row_index in range(len(row_sizes)):
        for col_index in range(len(col_sizes)):
            cells = [
                grid[r][c]
                for r in range(row_bounds[row_index] + 1, row_bounds[row_index + 1])
                for c in range(col_bounds[col_index] + 1, col_bounds[col_index + 1])
            ]
            counts = Counter(value for value in cells if value != 0)
            if len(counts) != 1:
                return None
            density = sum(counts.values()) / len(cells)
            if not 0.53 <= density <= 0.88:
                return None
            modes.append(next(iter(counts)))
    labels = {}
    pattern = []
    for value in modes:
        labels.setdefault(value, len(labels))
        pattern.append(labels[value])
    return h, w, row_sizes, col_sizes, tuple(pattern)


class LinkedSectionGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())
        cls.unique_inputs = {
            tuple(tuple(row) for row in source): (source, target)
            for source, target in cls.pairs
        }

    def test_all_canonical_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 8)
        self.assertEqual(len(self.unique_inputs), 4)
        extracted = {
            independent_signature(source)
            for source, _ in self.unique_inputs.values()
        }
        self.assertEqual(extracted, generator._CANONICAL_SIGNATURES)
        for source, expected in self.pairs:
            before = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), expected)
            self.assertEqual(
                generator.canonical_profile_signature(source),
                independent_signature(source),
            )
            self.assertEqual(source, before)

    def test_default_prior_reaches_every_profile_on_main_and_disjoint_ranges(self):
        for seed_start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                counts = Counter()
                for offset in range(600):
                    seed = seed_start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                    )
                    module_signature = generator.canonical_profile_signature(grid)
                    independent = independent_signature(grid)
                    self.assertEqual(module_signature, independent)
                    if independent in generator._CANONICAL_SIGNATURES:
                        counts[independent] += 1
                with self.subTest(seed_start=seed_start, band=band, counts=counts):
                    self.assertGreaterEqual(sum(counts.values()), 150)
                    self.assertLessEqual(sum(counts.values()), 250)
                    self.assertEqual(set(counts), set(generator._CANONICAL_SIGNATURES))

    def test_exact_axes_are_recovered_from_minimum_and_maximum_draws(self):
        cases = (
            {
                "grid_h": 8,
                "grid_w": 8,
                "row_divider_count": 1,
                "col_divider_count": 1,
                "n_output_colors": 1,
                "section_style": "single_color",
                "fill_density": 0.25,
            },
            {
                "grid_h": 30,
                "grid_w": 30,
                "row_divider_count": 3,
                "col_divider_count": 3,
                "n_output_colors": 9,
                "section_style": "dominant_noise",
                "fill_density": 0.82,
            },
        )
        for band in ("easy", "medium", "hard"):
            for seed, overrides in enumerate(cases):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 19 + 1,
                        difficulty=band,
                        **overrides,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                self.assertEqual(len(grid), overrides["grid_h"])
                self.assertEqual(len(grid[0]), overrides["grid_w"])
                for key in (
                    "row_divider_count",
                    "col_divider_count",
                    "n_output_colors",
                ):
                    self.assertEqual(observed[key], overrides[key])
                    self.assertEqual(captured[-1].axis_value(key), overrides[key])
                self.assertEqual(
                    generator.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": overrides},
                    ),
                    [],
                )

    def test_large_output_palette_is_reachable_without_other_overrides(self):
        for band in ("easy", "medium", "hard"):
            grid = generator.generate(
                91,
                17,
                difficulty=band,
                n_output_colors=9,
            )
            self.assertEqual(generator.observe_overrides(grid)["n_output_colors"], 9)
            self.assertEqual(generator.self_check(grid), [])

    def test_incompatible_exact_combinations_reject_loudly(self):
        with self.assertRaisesRegex(ValueError, "incompatible"):
            generator.generate(
                0,
                0,
                row_divider_count=1,
                col_divider_count=1,
                n_output_colors=9,
            )
        with self.assertRaisesRegex(ValueError, "incompatible"):
            generator.generate(0, 0, grid_h=8, row_divider_count=3)

    def test_plausible_recombination_is_not_an_official_profile(self):
        source, _ = next(
            pair
            for pair in self.unique_inputs.values()
            if len(pair[0]) == 18
        )
        changed = [row[:] for row in source]
        divider_columns = (6, 13)
        for c in range(len(changed[0])):
            if c not in divider_columns:
                changed[7][c] = (4, 8, 3)[sum(c > divider for divider in divider_columns)]
        changed[8] = [0] * len(changed[0])
        signature = independent_signature(changed)
        self.assertIsNotNone(signature)
        self.assertNotIn(signature, generator._CANONICAL_SIGNATURES)

    def test_self_check_rejects_nearest_structural_impostors(self):
        source, _ = next(
            pair
            for pair in self.unique_inputs.values()
            if len(pair[0]) == 18
        )
        self.assertEqual(generator.self_check(source), [])

        all_background = [[0] * len(source[0]) for _ in source]
        self.assertTrue(generator.self_check(all_background))

        singleton = [[0] * len(source[0]) for _ in source]
        singleton[4][4] = 2
        self.assertTrue(generator.self_check(singleton))

        edge_divider = [row[:] for row in source]
        edge_divider[0] = [0] * len(source[0])
        self.assertTrue(generator.self_check(edge_divider))

        missing_divider = [row[:] for row in source]
        for c in range(len(missing_divider[0])):
            if c not in (6, 13):
                missing_divider[7][c] = (4, 8, 3)[sum(c > divider for divider in (6, 13))]
        self.assertTrue(generator.self_check(missing_divider))

        tied_mode = [row[:] for row in source]
        colored = [
            (r, c)
            for r in range(7)
            for c in range(6)
            if tied_mode[r][c] == 4
        ]
        for r, c in colored[:15]:
            tied_mode[r][c] = 9
        tied_mode[colored[15][0]][colored[15][1]] = 0
        self.assertTrue(generator.self_check(tied_mode))

    def test_global_counts_and_first_colored_cell_are_not_answer_shortcuts(self):
        # The first official grid has two equal 7x6 sections.  Swapping their
        # complete contents preserves dimensions, dividers, and the global
        # color histogram while swapping two output entries; global counts
        # therefore cannot predict the answer arrangement.
        source, _ = next(
            pair
            for pair in self.unique_inputs.values()
            if len(pair[0]) == 18
        )
        swapped = [row[:] for row in source]
        for r in range(7):
            left = swapped[r][0:6]
            middle = swapped[r][7:13]
            swapped[r][0:6] = middle
            swapped[r][7:13] = left
        self.assertEqual(
            Counter(value for row in source for value in row),
            Counter(value for row in swapped for value in row),
        )
        self.assertEqual(generator.self_check(swapped), [])
        self.assertNotEqual(generator.rule_mirror(source), generator.rule_mirror(swapped))

        # In the generalized branch, locate a section whose first row-major
        # colored cell is a distractor.  The output must be its more frequent
        # color, explicitly refuting a first-cell/marker-as-answer shortcut.
        witness = None
        for seed in range(200):
            grid = generator.generate(
                seed,
                seed * 31 + 7,
                difficulty="hard",
                section_style="dominant_noise",
                n_output_colors=4,
            )
            info = generator._analysis(grid)
            output = generator.rule_mirror(grid)
            for index, section in enumerate(info["sections"]):
                r0, r1, c0, c1 = section["span"]
                first = next(
                    grid[r][c]
                    for r in range(r0, r1)
                    for c in range(c0, c1)
                    if grid[r][c] != 0
                )
                mode = output[index // len(info["col_spans"])][
                    index % len(info["col_spans"])
                ]
                if first != mode:
                    witness = first, mode
                    break
            if witness is not None:
                break
        self.assertIsNotNone(witness)

    def test_determinism_fresh_returns_and_global_rng_preservation(self):
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    first = generator.generate(seed, seed * 13 + 2, difficulty=band)
                finally:
                    base.set_ctx_observer(None)
                second = generator.generate(seed, seed * 13 + 2, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(left is not right for left, right in zip(first, second)))
                observed = generator.observe_overrides(first)
                for key, value in observed.items():
                    self.assertEqual(captured[-1].axis_value(key), value)
                expected = second[0][0]
                first[0][0] = (first[0][0] + 1) % 10
                replay = generator.generate(seed, seed * 13 + 2, difficulty=band)
                self.assertEqual(replay[0][0], expected)
        self.assertEqual(random.getstate(), state)

    def test_rule_hash_is_pinned_to_every_canonical_row(self):
        hashes = set()
        import hashlib

        with canonical_path(ROOT).open() as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == generator.TASK_ID:
                    normalized = " ".join(row["program_solution"].split())
                    hashes.add(hashlib.sha256(normalized.encode()).hexdigest()[:12])
        self.assertEqual(hashes, {generator.RULE_HASH})

        authorities = []
        for relative in (
            "data/base/solutions/training/780d0b14__0ee358bd9d75.json",
            "data/base/solutions/augmented/780d0b14__359f43cf57fc.json",
        ):
            record = json.loads((canonical_path(ROOT).parent.parent / Path(relative).relative_to("data")).read_text())
            authorities.append(record["racket_target"]["target_code"])
        from solvers.grounded_rules import GROUNDED_RULES

        authorities.append(GROUNDED_RULES[generator.TASK_ID])
        authority_hashes = {
            hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
            for rule in authorities
        }
        self.assertEqual(authority_hashes, {generator.RULE_HASH})


if __name__ == "__main__":
    unittest.main()
