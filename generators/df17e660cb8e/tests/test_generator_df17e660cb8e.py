"""Focused semantic and regression tests for Ordered Waypoint Path."""
from __future__ import annotations

import copy
import random
import unittest
from collections import deque
from scripts.canonical_profile_gate import canonical_pairs as load_canonical_pairs

from puzzle_generators.per_puzzle.df17e660cb8e import generator
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    return load_canonical_pairs(generator.TASK_ID)


def marker_positions(grid):
    return {
        value: (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (2, 3, 4, 5, 6)
    }


def shortest_count(grid, start, goal):
    distance = {start: 0}
    counts = {start: 1}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in CARDINAL:
            nxt = row + delta_row, col + delta_col
            if not (
                0 <= nxt[0] < len(grid)
                and 0 <= nxt[1] < len(grid[0])
                and grid[nxt[0]][nxt[1]] != 8
            ):
                continue
            candidate = distance[(row, col)] + 1
            if nxt not in distance:
                distance[nxt] = candidate
                counts[nxt] = counts[(row, col)]
                queue.append(nxt)
            elif distance[nxt] == candidate:
                counts[nxt] += counts[(row, col)]
    return counts.get(goal, 0)


def assert_unique_waypoint_legs(testcase, grid):
    positions = marker_positions(grid)
    order = [2, 4, 5] + ([6] if 6 in positions else []) + [3]
    for first, second in zip(order, order[1:]):
        testcase.assertEqual(
            shortest_count(grid, positions[first], positions[second]),
            1,
            f"leg {first}->{second} must have exactly one shortest path",
        )


class OrderedWaypointGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_canonical_pairs_are_accepted_and_match_rule(self):
        self.assertEqual(len(self.pairs), 4)
        for pair in self.pairs:
            before = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(pair["input"]), [])
            self.assertEqual(generator.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(pair["input"], before)
            assert_unique_waypoint_legs(self, pair["input"])

    def test_generated_distribution_has_unique_intended_legs(self):
        seen_shapes = set()
        seen_counts = set()
        seen_orientations = set()
        row_major_killed = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for offset in range(160):
                seed = band_index * 100_000 + offset
                sample_index = offset * 13 + band_index
                grid = generator.generate(seed, sample_index, difficulty=band)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.strict_canonical_like(grid), [])
                assert_unique_waypoint_legs(self, grid)
                observed = generator.observe_overrides(grid)
                seen_shapes.add((observed["grid_h"], observed["grid_w"]))
                seen_counts.add(observed["n_intermediates"])
                seen_orientations.add(observed["orientation"])
                intended = generator.rule_mirror(grid)
                row_major_killed += (
                    generator.LESSON_COMPETITORS[
                        "visit checkpoints in row-major order"
                    ](grid)
                    != intended
                )
        self.assertGreaterEqual(len(seen_shapes), 20)
        self.assertEqual(seen_counts, {2, 3})
        self.assertEqual(seen_orientations, set(generator.ORIENTATIONS))
        self.assertGreater(row_major_killed, 0)

    def test_four_scene_lesson_falsifies_all_named_shortcuts(self):
        for seed in (11, 97, 10_003):
            pairs = []
            for sample_index in range(5):
                grid = generator.generate(seed, sample_index, difficulty="hard")
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            self.assertEqual(generator.lesson_identifiable(pairs[:4], pairs[4]), [])

    def test_override_boundaries_are_exact(self):
        for height in (9, 15):
            for width in (11, 19):
                for count in (2, 3):
                    for orientation in generator.ORIENTATIONS:
                        grid = generator.generate(
                            123,
                            456,
                            difficulty="medium",
                            grid_h=height,
                            grid_w=width,
                            n_intermediates=count,
                            orientation=orientation,
                        )
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {
                                "grid_h": height,
                                "grid_w": width,
                                "n_intermediates": count,
                                "orientation": orientation,
                            },
                        )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="expert")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, unknown_axis=7)
        with self.assertRaises((TypeError, ValueError)):
            generator.generate(1, 2, grid_h=True)

    def test_structural_and_semantic_impostors_are_rejected(self):
        grid = generator.generate(80_001, 17, difficulty="hard")
        positions = marker_positions(grid)
        zero = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 0
        )

        missing_marker = copy.deepcopy(grid)
        missing_marker[positions[4][0]][positions[4][1]] = 0
        duplicate_marker = copy.deepcopy(grid)
        duplicate_marker[zero[0]][zero[1]] = 4
        prepainted_route = copy.deepcopy(grid)
        prepainted_route[zero[0]][zero[1]] = 7
        broken_border = copy.deepcopy(grid)
        broken_border[0][1] = 0

        for impostor in (
            missing_marker,
            duplicate_marker,
            prepainted_route,
            broken_border,
        ):
            self.assertTrue(generator.self_check(impostor))

        alternate = None
        for row in range(1, len(grid) - 1):
            for col in range(1, len(grid[0]) - 1):
                if grid[row][col] != 8:
                    continue
                candidate = copy.deepcopy(grid)
                candidate[row][col] = 0
                if any(
                    "shortest paths" in message
                    for message in generator.self_check(candidate)
                ):
                    alternate = candidate
                    break
            if alternate is not None:
                break
        self.assertIsNotNone(alternate, "expected a one-cell ambiguity mutation")
        self.assertTrue(generator.self_check(alternate))

    def test_determinism_and_global_rng_purity(self):
        random.seed(91_337)
        expected = [random.random() for _ in range(6)]
        random.seed(91_337)
        first = generator.generate(1234, 5678, difficulty="hard")
        observed = [random.random() for _ in range(6)]
        second = generator.generate(1234, 5678, difficulty="hard")
        self.assertEqual(first, second)
        self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
