from __future__ import annotations

import copy
import random
import unittest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "864b0302e2e6"
GENERATOR, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(
    TASK_ID, root=find_root(__file__)
)


def missing_quadrant(grid: list[list[int]]) -> int:
    if not grid or len(grid) != len(grid[0]) or len(grid) % 2 == 0:
        raise AssertionError("expected an odd square grid")
    q = len(grid) // 2
    origins = ((0, 0), (0, q + 1), (q + 1, 0), (q + 1, q + 1))
    empty = [
        index
        for index, (row0, col0) in enumerate(origins)
        if not any(
            grid[row0 + row][col0 + col] != 0
            for row in range(q)
            for col in range(q)
        )
    ]
    if len(empty) != 1:
        raise AssertionError(f"expected exactly one empty quadrant, got {empty}")
    return empty[0]


class MissingQuadrantOverrideTests(unittest.TestCase):
    def test_each_exact_override_selects_the_visible_empty_quadrant(self):
        for requested in range(4):
            with self.subTest(requested=requested):
                grid = GENERATOR.generate(
                    202_610_24,
                    17,
                    quad_size=5,
                    missing_quad=requested,
                )
                self.assertEqual(missing_quadrant(grid), requested)
                self.assertEqual(GENERATOR.self_check(grid), [])

    def test_invalid_exact_overrides_fail_closed(self):
        for invalid in (-1, 4, True, 1.0):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    GENERATOR.generate(
                        202_610_24,
                        17,
                        quad_size=5,
                        missing_quad=invalid,
                    )

    def test_replay_is_fresh_deterministic_and_global_rng_pure(self):
        state = random.getstate()
        first = GENERATOR.generate(
            77, 9, quad_size=6, missing_quad=2
        )
        second = GENERATOR.generate(
            77, 9, quad_size=6, missing_quad=2
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        changed = copy.deepcopy(first)
        changed[0][0] = 9 if changed[0][0] != 9 else 8
        self.assertNotEqual(changed, second)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
