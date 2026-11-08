"""Behavioral regressions for section-frequency teaching and public controls."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import product
import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_HASH = load_selected_generator("0ee358bd9d75", root=ROOT)


def independent_outputs(grid):
    """Parse pixel separators and score five plausible rival selectors."""
    height, width = len(grid), len(grid[0])
    rows = [-1] + [r for r in range(height) if not any(grid[r])] + [height]
    cols = [-1] + [c for c in range(width)
                   if not any(grid[r][c] for r in range(height))] + [width]
    answers = {name: [] for name in ("mode", "first", "last", "min", "max", "rarest")}
    for a, b in zip(rows, rows[1:]):
        output_rows = {name: [] for name in answers}
        for c, d in zip(cols, cols[1:]):
            values = [grid[r][col] for r in range(a + 1, b)
                      for col in range(c + 1, d) if grid[r][col] != 0]
            counts = Counter(values)
            assert counts, "empty section"
            mode = max(counts, key=counts.get)
            assert sum(count == counts[mode] for count in counts.values()) == 1
            selectors = {"mode": mode, "first": values[0], "last": values[-1],
                         "min": min(values), "max": max(values),
                         "rarest": min(counts, key=lambda color: (counts[color], color))}
            for name, value in selectors.items():
                output_rows[name].append(value)
        for name in answers:
            answers[name].append(output_rows[name])
    return answers


def colored_components(grid):
    """Count four-connected, same-color objects outside the modal background."""
    background = Counter(color for row in grid for color in row).most_common(1)[0][0]
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row)
              if color != background}
    count = 0
    while unseen:
        first = unseen.pop()
        color = grid[first[0]][first[1]]
        stack = [first]
        count += 1
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


class ReviewContractTests(unittest.TestCase):
    def test_default_morphology_avoids_excessive_color_fragmentation(self):
        canonical = [colored_components(pair["input"])
                     for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)
                     if pair["split"] == "train"]
        canonical_median = sorted(canonical)[len(canonical) // 2]
        for seeds in (range(1, 101), range(50001, 50101)):
            counts = [colored_components(GEN.generate(seed, seed, difficulty=band))
                      for band in ("easy", "medium", "hard") for seed in seeds]
            median = sorted(counts)[len(counts) // 2]
            self.assertLessEqual(median, 3 * canonical_median,
                                 (seeds.start, median, canonical_median))

    def test_integer_controls_reject_coercion(self):
        controls = {"grid_h": 12, "grid_w": 12, "row_divider_count": 1,
                    "col_divider_count": 1, "n_output_colors": 2}
        for name, lawful in controls.items():
            for invalid in (True, False, float(lawful), lawful + 0.75, str(lawful)):
                with self.subTest(name=name, invalid=invalid):
                    with self.assertRaises((TypeError, ValueError)):
                        GEN.generate(0, 0, **{name: invalid})

    def test_seed_index_and_difficulty_reject_coercion(self):
        for name in ("seed", "sample_index"):
            for invalid in (True, False, 1.0, 1.75, "1"):
                args = {"seed": 0, "sample_index": 0, name: invalid}
                with self.subTest(name=name, invalid=invalid):
                    with self.assertRaises((TypeError, ValueError)):
                        GEN.generate(**args)
        with self.assertRaises(ValueError):
            GEN.generate(0, -1)
        for invalid in (False, 0, "", "HARD"):
            with self.subTest(difficulty=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(0, 0, difficulty=invalid)

    def test_density_rejects_nonfinite_and_non_numeric_values(self):
        for invalid in (True, False, "0.5", float("nan"), float("inf"), 0.24, 0.83):
            with self.subTest(value=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(0, 0, fill_density=invalid)

    def test_default_lessons_refute_rivals_after_every_single_pair_holdout(self):
        for band, seed, start in product(("easy", "medium", "hard"), range(12), range(3)):
            grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            scored = [independent_outputs(grid) for grid in grids]
            for query in range(4):
                for rival in ("first", "last", "min", "max", "rarest"):
                    refuted = any(item[rival] != item["mode"] for index, item in enumerate(scored)
                                  if index != query)
                    self.assertTrue(refuted, (band, seed, start, query, rival))

    def test_canonical_profiles_are_preserved_and_noisy_inputs_are_not_strict(self):
        self.assertTrue(callable(getattr(GEN, "strict_canonical_like", None)))
        for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
            self.assertTrue(GEN.strict_canonical_like(pair["input"]))
            self.assertEqual(independent_outputs(pair["input"])["mode"], pair["output"])
        for band in ("easy", "medium", "hard"):
            self.assertTrue(GEN.strict_canonical_like(GEN.generate(0, 0, difficulty=band)))
            self.assertFalse(GEN.strict_canonical_like(GEN.generate(0, 1, difficulty=band)))

    def test_declared_rivals_are_pure_and_match_independent_pixel_readout(self):
        self.assertTrue(hasattr(GEN, "CANONICAL_SHORTCUTS"))
        names = {"first_nonzero": "first", "last_nonzero": "last", "minimum_color": "min",
                 "maximum_color": "max", "least_frequent": "rarest"}
        for seed in range(6):
            grid = GEN.generate(seed, 1)
            before = deepcopy(grid)
            expected = independent_outputs(grid)
            for name, selector in names.items():
                rival = GEN.CANONICAL_SHORTCUTS[name]
                self.assertEqual(rival(grid), expected[selector])
                self.assertEqual(rival(grid), expected[selector])
                self.assertEqual(grid, before)

    def test_exact_boundary_controls_preserve_domain(self):
        for band, size, style in product(("easy", "medium", "hard"), (8, 30),
                                         ("single_color", "dominant_noise")):
            grid = GEN.generate(14, 2, difficulty=band, grid_h=size, grid_w=size,
                                row_divider_count=1, col_divider_count=1,
                                n_output_colors=4, section_style=style)
            self.assertEqual((len(grid), len(grid[0])), (size, size))
            self.assertEqual(GEN.self_check(grid, meta={"overrides": {"section_style": style}}), [])
            self.assertEqual(len(set(sum(independent_outputs(grid)["mode"], []))), 4)

    def test_infeasible_controls_name_the_actual_axes(self):
        for overrides in ({"grid_h": 8, "row_divider_count": 3},
                          {"grid_w": 8, "col_divider_count": 3},
                          {"row_divider_count": 1, "col_divider_count": 1,
                           "n_output_colors": 9}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError) as caught:
                    GEN.generate(0, 0, **overrides)
                axes = set(getattr(caught.exception, "incompatible_axes", ()))
                self.assertGreaterEqual(len(axes), 2)
                self.assertTrue(axes <= set(overrides))


if __name__ == "__main__":
    unittest.main()
