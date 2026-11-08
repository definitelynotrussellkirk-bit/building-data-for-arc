from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


generator, _, _ = load_selected_generator(
    "306f5b5f899c", root=find_root(__file__)
)


def objects(grid):
    """Return same-color 4-connected ARC objects with normalized cells."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if (rr, cc) in seen or grid[rr][cc] != color:
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                stack.extend(((rr - 1, cc), (rr + 1, cc),
                              (rr, cc - 1), (rr, cc + 1)))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            normalized = {(rr - r0, cc - c0) for rr, cc in cells}
            result.append({
                "color": color,
                "cells": cells,
                "normalized": normalized,
                "top_left": (r0, c0),
                "height": max(rr for rr, _ in normalized) + 1,
                "width": max(cc for _, cc in normalized) + 1,
            })
    return result


def rule_mirror(grid):
    ranked = sorted(
        objects(grid),
        key=lambda obj: (-len(obj["cells"]), obj["top_left"]),
    )
    if len(ranked) < 2:
        raise ValueError("rule requires at least two objects")
    first, second = ranked[:2]
    shape = first["normalized"] | second["normalized"]
    h = max(first["height"], second["height"])
    w = max(first["width"], second["width"])
    return [[8 if (r, c) in shape else 0 for c in range(w)] for r in range(h)]


class LargestObjectUnionGeneratorTests(unittest.TestCase):
    def test_canonical_inputs_are_accepted_and_match_the_rule(self):
        pairs = canonical_pairs(
            generator.TASK_ID, root=find_root(__file__), labeled_only=True
        )
        self.assertEqual(3, len(pairs))
        for pair in pairs:
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual([], generator.self_check(pair["input"]))
                self.assertEqual(pair["output"], rule_mirror(pair["input"]))

    def test_hard_band_can_realize_canonical_7_by_9_with_singleton_distractor(self):
        grid = generator.generate(
            20261024,
            0,
            difficulty="hard",
            grid_h=7,
            grid_w=9,
            n=3,
            palette_kind="default",
            palette_size=3,
            n_distinct_colors=3,
            position_bias="scattered_colored_motifs",
            density="sparse",
        )
        found = objects(grid)
        self.assertEqual((7, 9), (len(grid), len(grid[0])))
        self.assertEqual(3, len(found))
        self.assertIn(1, [len(obj["cells"]) for obj in found])
        self.assertEqual([], generator.self_check(grid))
        self.assertTrue(rule_mirror(grid))

    def test_helpful_texture_is_a_live_palette_alias(self):
        grid = generator.generate(
            1,
            1,
            grid_h=9,
            grid_w=11,
            n=4,
            palette_size=4,
            n_distinct_colors=4,
            texture="warm",
        )
        colors = {value for row in grid for value in row if value != 0}
        self.assertTrue(colors)
        self.assertLessEqual(colors, set(generator.PALETTES["warm"]))

    def test_observer_recovers_exact_object_and_color_counts(self):
        grid = generator.generate(
            29,
            6,
            grid_h=10,
            grid_w=13,
            n=5,
            palette_kind="varied",
            palette_size=5,
            n_distinct_colors=3,
        )
        observed = generator.observe_overrides(grid)
        self.assertEqual(5, observed["n"])
        self.assertEqual(3, observed["n_distinct_colors"])
        self.assertEqual("diagnostic", generator.AXES["palette_size"]["probe"])

    def test_standalone_distinct_color_override_expands_dependent_defaults(self):
        grid = generator.generate(
            0,
            3,
            difficulty="easy",
            n_distinct_colors=5,
        )
        observed = generator.observe_overrides(grid)
        self.assertEqual(5, observed["n_distinct_colors"])
        self.assertEqual(5, observed["n"])
        self.assertEqual([], generator.self_check(grid))

    def test_short_curriculum_has_broad_output_shape_content(self):
        outputs = {
            tuple(tuple(row) for row in generator.rule_mirror(
                generator.generate(seed, seed * 17 + 3, difficulty="medium")
            ))
            for seed in range(64)
        }
        self.assertGreaterEqual(len(outputs), 36)

    def test_unknown_axes_and_textures_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            generator.generate(1, 0, mystery_axis=3)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(1, 0, texture="bogus")


if __name__ == "__main__":
    unittest.main()
