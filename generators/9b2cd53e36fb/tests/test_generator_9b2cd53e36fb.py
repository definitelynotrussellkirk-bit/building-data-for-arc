"""Regression tests for edge-hole profiles and floating-hole exactness."""

from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


generator, _, _ = load_selected_generator(
    "9b2cd53e36fb", root=find_root(__file__)
)


def canonical_inputs() -> list[list[list[int]]]:
    return [
        pair["input"]
        for pair in canonical_pairs(
            generator.TASK_ID, root=find_root(__file__), variant=0, labeled_only=True
        )
    ]


def components(grid) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    pending = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0
    }
    found = []
    while pending:
        start = pending.pop()
        component = [start]
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in pending:
                    pending.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        found.append(component)
    return found


def floating_count(grid) -> int:
    h, w = len(grid), len(grid[0])
    return sum(
        all(r not in (0, h - 1) and c not in (0, w - 1) for r, c in cells)
        for cells in components(grid)
    )


def linked_signature(grid):
    h, w = len(grid), len(grid[0])
    signature = []
    for cells in components(grid):
        r1, c1, r2, c2 = generator._bbox(cells)
        edge = generator._edge_of((r1, c1, r2, c2), h, w)
        if edge in ("top", "bottom"):
            signature.append((edge, c2 - c1 + 1, r2 - r1 + 1))
        elif edge in ("left", "right"):
            signature.append((edge, r2 - r1 + 1, c2 - c1 + 1))
    return tuple(sorted(signature))


class EdgeHoleGeneratorTests(unittest.TestCase):
    def test_canonical_inputs_define_all_linked_archetypes(self):
        inputs = canonical_inputs()

        self.assertEqual(4, len(inputs))
        self.assertEqual(
            generator.ARCHETYPES,
            {
                (len(grid), len(grid[0])): linked_signature(grid)
                for grid in inputs
            },
        )

    def test_declared_floating_mode_always_reserves_one_interior_hole(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                grid = generator.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                    texture="floating_hole",
                )
                with self.subTest(band=band, seed=seed):
                    self.assertEqual([], generator.self_check(grid))
                    self.assertGreaterEqual(len(components(grid)), 2)
                    self.assertEqual(1, floating_count(grid))

    def test_requested_eight_holes_include_the_floating_component(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                grid = generator.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                    texture="floating_hole",
                    hole_count=8,
                )
                with self.subTest(band=band, seed=seed):
                    self.assertEqual(8, len(components(grid)))
                    self.assertEqual(1, floating_count(grid))
                    self.assertEqual(
                        {"hole_count": 8, "hole_len": 1, "hole_depth": 1},
                        generator.observe_overrides(grid),
                    )

    def test_floating_replay_is_deterministic(self):
        kwargs = {
            "difficulty": "easy",
            "texture": "floating_hole",
            "hole_count": 8,
        }
        self.assertEqual(
            generator.generate(13, 224, **kwargs),
            generator.generate(13, 224, **kwargs),
        )

    def test_degenerate_fixtures_are_not_advertised_as_ordinary_textures(self):
        valid = {
            item.strip()
            for item in generator.AXES["texture"]["valid"].split("|")
            if item.strip()
        }
        self.assertTrue(valid)
        self.assertTrue(valid.isdisjoint(generator.DEGENERATE_TEXTURES))

    def test_unknown_axes_and_textures_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            generator.generate(1, 0, mystery_axis=3)
        with self.assertRaisesRegex(ValueError, "unknown texture"):
            generator.generate(1, 0, texture="bogus")


if __name__ == "__main__":
    unittest.main()
