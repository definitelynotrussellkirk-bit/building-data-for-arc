from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


generator, _, _ = load_selected_generator(
    "630d6cc550e4", root=find_root(__file__)
)


MAPPING = {
    (0, 0): (0, 2),
    (0, 1): (1, 0),
    (0, 2): (2, 2),
    (1, 0): (2, 1),
    (1, 2): (0, 1),
    (2, 0): (0, 0),
    (2, 1): (1, 2),
    (2, 2): (2, 0),
}


def detect_blocks(grid):
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h - 2)
        for c in range(w - 2)
        if grid[r][c] != 7
        and grid[r + 1][c + 1] == 7
        and grid[r][c + 1] != 7
        and grid[r + 1][c] != 7
    ]


def rule_mirror(grid):
    result = [row[:] for row in grid]
    for r0, c0 in detect_blocks(grid):
        for (dr, dc), (sr, sc) in MAPPING.items():
            result[r0 + dr][c0 + dc] = grid[r0 + sr][c0 + sc]
    return result


def fixed_lattice_rival(grid):
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r0 in range(1, h - 2, 4):
        for c0 in sorted({1, w - 4}):
            if c0 < 0 or c0 + 2 >= w or grid[r0][c0] == 7:
                continue
            for (dr, dc), (sr, sc) in MAPPING.items():
                result[r0 + dr][c0 + dc] = grid[r0 + sr][c0 + sc]
    return result


class RingRotationGeneratorTests(unittest.TestCase):
    def test_canonical_inputs_are_structurally_accepted(self):
        pairs = canonical_pairs(
            generator.TASK_ID, root=find_root(__file__), labeled_only=True
        )
        self.assertEqual(4, len(pairs))
        for pair in pairs:
            with self.subTest(shape=(len(pair["input"]), len(pair["input"][0]))):
                self.assertEqual([], generator.self_check(pair["input"]))
                self.assertEqual(pair["output"], rule_mirror(pair["input"]))

    def test_exact_7x7_corner_layout_realizes_declared_axes(self):
        grid = generator.generate(
            20261024,
            7,
            difficulty="hard",
            grid_h=7,
            grid_w=7,
            block_count=2,
            anchor_corner=True,
            position_bias="alternating",
            asymmetry_force=True,
            palette_kind="broad",
            palette_size=9,
        )
        blocks = detect_blocks(grid)
        self.assertEqual((7, 7), (len(grid), len(grid[0])))
        self.assertEqual(2, len(blocks))
        self.assertTrue(
            any(
                (r, c) in {(0, 0), (0, 4), (4, 0), (4, 4)}
                for r, c in blocks
            )
        )
        self.assertEqual([], generator.self_check(grid))

    def test_single_corner_anchored_block_returns_without_overfilling(self):
        grid = generator.generate(
            0,
            7,
            grid_h=9,
            grid_w=9,
            block_count=1,
            anchor_corner=True,
            position_bias="alternating",
            palette_kind="broad",
            palette_size=8,
        )
        blocks = detect_blocks(grid)
        self.assertEqual(1, len(blocks))
        self.assertIn(blocks[0], {(0, 0), (0, 6), (6, 0), (6, 6)})
        self.assertEqual([], generator.self_check(grid))

    def test_zero_and_repeated_ring_colors_are_representable(self):
        grid = generator.generate(
            17,
            3,
            grid_h=7,
            grid_w=7,
            block_count=2,
            anchor_corner=True,
            palette_kind="broad",
            palette_size=9,
        )
        ring_values = []
        for r0, c0 in detect_blocks(grid):
            ring_values.extend(
                grid[r0 + dr][c0 + dc]
                for dr, dc in generator.RING_3X3
            )
        self.assertIn(0, ring_values)
        self.assertLess(len(set(ring_values)), len(ring_values))

    def test_fixed_lattice_shortcut_is_separated(self):
        grid = generator.generate(
            91,
            4,
            grid_h=7,
            grid_w=7,
            block_count=2,
            anchor_corner=True,
            palette_kind="broad",
            palette_size=9,
        )
        self.assertNotEqual(rule_mirror(grid), fixed_lattice_rival(grid))

    def test_observer_recovers_exact_count_and_palette_axes(self):
        grid = generator.generate(
            23,
            5,
            grid_h=11,
            grid_w=13,
            block_count=4,
            palette_kind="broad",
            palette_size=7,
            position_bias="alternating",
            anchor_corner=True,
            asymmetry_force=True,
        )
        observed = generator.observe_overrides(grid)
        self.assertEqual(4, observed["block_count"])
        self.assertEqual(7, observed["palette_size"])
        self.assertEqual("diagnostic", generator.AXES["anchor_corner"]["probe"])
        self.assertEqual("diagnostic", generator.AXES["asymmetry_force"]["probe"])

    def test_degenerate_fixtures_are_not_advertised_as_ordinary_textures(self):
        valid = {
            item.strip()
            for item in generator.AXES["texture"]["valid"].split("|")
            if item.strip()
        }
        self.assertTrue(valid)
        self.assertTrue(valid.isdisjoint(generator.DEGENERATE_TEXTURES))

    def test_capacity_fallback_realizes_six_blocks_on_7_by_11(self):
        grid = generator.generate(
            24,
            411,
            difficulty="easy",
            grid_h=7,
            grid_w=11,
            block_count=6,
        )
        self.assertEqual((7, 11), (len(grid), len(grid[0])))
        self.assertEqual(6, generator.observe_overrides(grid)["block_count"])
        self.assertEqual([], generator.self_check(grid))

    def test_single_axis_maximum_overrides_remain_realizable(self):
        six = generator.generate(0, 3, difficulty="easy", block_count=6)
        self.assertEqual(6, generator.observe_overrides(six)["block_count"])
        self.assertEqual([], generator.self_check(six))

        nine = generator.generate(0, 3, difficulty="easy", palette_size=9)
        self.assertEqual(9, generator.observe_overrides(nine)["palette_size"])
        self.assertEqual([], generator.self_check(nine))

    def test_unknown_axes_and_textures_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            generator.generate(1, 0, mystery_axis=3)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(1, 0, texture="bogus")


if __name__ == "__main__":
    unittest.main()
