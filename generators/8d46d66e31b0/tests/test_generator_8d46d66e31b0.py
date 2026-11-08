from __future__ import annotations

import unittest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("8d46d66e31b0", root=ROOT)


def color_two_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    components = []
    while remaining:
        start = remaining.pop()
        component = {start}
        frontier = [start]
        while frontier:
            r, c = frontier.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        components.append(component)
    return components


class Generator8d46d66e31b0Tests(unittest.TestCase):
    def test_retained_seed_uses_one_connected_color_two_template(self):
        grid = generator.generate(0, 2)

        components = color_two_components(grid)

        self.assertEqual(len(components), 1)
        self.assertEqual(generator.self_check(grid), [])

    def test_self_check_rejects_disconnected_color_two_template(self):
        grid = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 0, 0, 5, 5, 5, 5, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]

        errors = generator.self_check(grid)

        self.assertTrue(errors)
        self.assertTrue(any("connected" in error.lower() for error in errors))

    def test_documented_degenerates_remain_allowed(self):
        no_template = generator.generate(3, 4, texture="no_template")
        no_frames = generator.generate(3, 4, texture="no_frames")
        single_cell = generator.generate(3, 4, texture="single_cell_template")

        self.assertEqual(generator.self_check(no_template), [])
        self.assertEqual(generator.self_check(no_frames), [])
        self.assertEqual(generator.self_check(single_cell), [])
        self.assertEqual(len(color_two_components(no_template)), 0)
        self.assertEqual(len(color_two_components(no_frames)), 1)
        self.assertEqual([len(c) for c in color_two_components(single_cell)], [1])

    def test_generated_templates_are_connected_across_bands(self):
        for difficulty in ("easy", None, "hard"):
            for seed in range(30):
                with self.subTest(difficulty=difficulty, seed=seed):
                    grid = generator.generate(
                        seed,
                        seed * 19 + 7,
                        difficulty=difficulty,
                    )
                    self.assertEqual(len(color_two_components(grid)), 1)
                    self.assertEqual(generator.self_check(grid), [])


if __name__ == "__main__":
    unittest.main()
