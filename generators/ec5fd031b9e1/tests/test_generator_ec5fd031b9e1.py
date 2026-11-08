from __future__ import annotations

import json
import random
import unittest
from collections import Counter, deque
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.ec5fd031b9e1 import generator


ROOT = Path(__file__).resolve().parents[1]
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise KeyError(generator.TASK_ID)


def independent_path(grid, start, goal):
    height = len(grid)
    width = len(grid[0])
    parent = {start: None}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for dr, dc in DELTAS:
            neighbor = row + dr, col + dc
            if (
                not 0 <= neighbor[0] < height
                or not 0 <= neighbor[1] < width
                or neighbor in parent
            ):
                continue
            value = grid[neighbor[0]][neighbor[1]]
            if value == 0 or neighbor == goal:
                parent[neighbor] = (row, col)
                queue.append(neighbor)
    if goal not in parent:
        return []
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]


def independent_rule(grid):
    colors = sorted({
        value
        for row in grid
        for value in row
        if value not in (0, 8)
    })
    output = [row[:] for row in grid]
    for color in colors:
        points = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        if len(points) != 2:
            continue
        for row, col in independent_path(grid, points[0], points[1]):
            output[row][col] = color
    return output


def blank_maze(height=9, width=10):
    grid = [[0] * width for _ in range(height)]
    for row in range(height):
        grid[row][0] = grid[row][-1] = 8
    for col in range(width):
        grid[0][col] = grid[-1][col] = 8
    grid[1][2] = 8
    return grid


class Ec5fd031b9e1GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
            self.assertEqual(
                (len(pair["output"]), len(pair["output"][0])),
                (len(grid), len(grid[0])),
            )
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add(
                        (
                            tuple(map(tuple, grid)),
                            tuple(map(tuple, output)),
                        )
                    )
                    signature = generator.canonical_profile_signature(grid)
                    if signature is not None:
                        matches += 1
                        profiles.add(signature)
                self.assertGreaterEqual(matches, 100)
                self.assertLessEqual(matches, 200)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 585)

    def test_forced_dimension_and_pair_boundaries_are_exact(self):
        for height, width in (
            (7, 8),
            (7, 18),
            (16, 8),
            (16, 18),
        ):
            for n_pairs in (1, 3):
                for band in ("easy", "medium", "hard"):
                    grid = generator.generate(
                        height * 101 + width,
                        width * 103 + n_pairs,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        n_pairs=n_pairs,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {
                            "grid_h": height,
                            "grid_w": width,
                            "n_pairs": n_pairs,
                        },
                    )

    def test_rule_is_exact_original_grid_bfs_in_color_order(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(150):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                expected = independent_rule(grid)
                actual = generator.rule_mirror(grid)
                self.assertEqual(actual, expected)
                self.assertEqual(grid, before)

                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                used = set()
                for color, points in features["points"].items():
                    path = independent_path(grid, points[0], points[1])
                    self.assertGreaterEqual(len(path), 4)
                    self.assertFalse(used.intersection(path))
                    used.update(path)
                    self.assertTrue(all(
                        actual[row][col] == color for row, col in path
                    ))
                self.assertEqual(
                    sum(
                        value != before[row][col]
                        for row, values in enumerate(actual)
                        for col, value in enumerate(values)
                    ),
                    sum(len(path) - 2 for path in features["paths"].values()),
                )

    def test_d4_color_relabeling_and_lawful_hybrid(self):
        for index, rows in enumerate(generator._PROFILE_ROWS):
            for transform in range(8):
                colors = (
                    generator._VALID_PALETTE[
                        (index + transform) % len(generator._VALID_PALETTE)
                    ],
                    generator._VALID_PALETTE[
                        (index + transform + 3) % len(generator._VALID_PALETTE)
                    ],
                )
                if colors[0] == colors[1]:
                    self.fail("test palette must be distinct")
                grid = generator._draw_profile(rows, transform, colors)
                self.assertEqual(generator.self_check(grid), [])
                self.assertTrue(generator.is_canonical_profile(grid))
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

        walls = generator._decode_rows(generator._PROFILE_ROWS[0])
        endpoints = generator._decode_rows(generator._PROFILE_ROWS[3])
        hybrid = [
            [8 if walls[row][col] == 8 else 0
             for col in range(len(walls[0]))]
            for row in range(len(walls))
        ]
        for row, values in enumerate(endpoints):
            for col, value in enumerate(values):
                if value not in (0, 8):
                    hybrid[row][col] = value
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertEqual(
            generator.rule_mirror(hybrid),
            independent_rule(hybrid),
        )

    def test_boundaries_removed_controls_and_strict_types(self):
        boundary_calls = (
            {"grid_h": 7},
            {"grid_h": 16},
            {"grid_w": 8},
            {"grid_w": 18},
            {"n_pairs": 1},
            {"n_pairs": 3},
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                for key, value in kwargs.items():
                    self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "7"},
            {"grid_w": 8.0},
            {"n_pairs": True},
            {"grid_h": 6},
            {"grid_h": 17},
            {"grid_w": 7},
            {"grid_w": 19},
            {"n_pairs": 0},
            {"n_pairs": 4},
            {"texture": "no_dots"},
            {"n_walls": 2},
            {"palette_kind": "warm"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_default_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 125)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=16,
                grid_w=8,
                n_pairs=3,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"grid_h": 16, "grid_w": 8, "n_pairs": 3},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            grid_h=10,
            grid_w=11,
            n_pairs=2,
        )
        mutations = []

        border_hole = [row[:] for row in valid]
        border_hole[0][3] = 0
        mutations.append(border_hole)

        no_interior_walls = blank_maze()
        no_interior_walls[1][2] = 0
        no_interior_walls[2][1] = no_interior_walls[2][8] = 1
        mutations.append(no_interior_walls)

        missing_endpoint = [row[:] for row in valid]
        color = min(generator._colored_points(missing_endpoint))
        row, col = generator._colored_points(missing_endpoint)[color][0]
        missing_endpoint[row][col] = 0
        mutations.append(missing_endpoint)

        triple_endpoint = [row[:] for row in valid]
        color = min(generator._colored_points(triple_endpoint))
        for row in range(1, len(triple_endpoint) - 1):
            for col in range(1, len(triple_endpoint[0]) - 1):
                if triple_endpoint[row][col] == 0:
                    triple_endpoint[row][col] = color
                    break
            else:
                continue
            break
        mutations.append(triple_endpoint)

        four_pairs = blank_maze(10, 12)
        for index, color in enumerate((1, 2, 3, 4)):
            row = 2 + index
            four_pairs[row][1] = four_pairs[row][-2] = color
        mutations.append(four_pairs)

        too_close = blank_maze()
        too_close[3][3] = too_close[3][5] = 1
        mutations.append(too_close)

        disconnected = blank_maze()
        for row in range(1, len(disconnected) - 1):
            disconnected[row][4] = 8
        disconnected[3][2] = disconnected[3][7] = 1
        mutations.append(disconnected)

        overlapping = blank_maze()
        overlapping[4][1] = overlapping[4][8] = 1
        overlapping[2][5] = overlapping[6][5] = 2
        mutations.append(overlapping)

        invalid_color = [row[:] for row in valid]
        invalid_color[1][1] = 10
        mutations.append(invalid_color)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        mutations.append([[8] * 8 for _ in range(6)])
        mutations.append([[8] * 7 for _ in range(7)])
        mutations.append([[8] * 8 for _ in range(17)])
        mutations.append([[8] * 19 for _ in range(7)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_pairs_walls_paths_palette_and_diversity(self):
        mean_areas = {}
        mean_pairs = {}
        mean_walls = {}
        palette = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            pair_counts = []
            wall_counts = []
            path_lengths = set()
            pairs = set()
            outputs = set()
            profiles = Counter()
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    )
                )
                outputs.add(tuple(map(tuple, output)))
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                pair_counts.append(features["n_pairs"])
                wall_counts.append(features["interior_walls"])
                palette.update(features["points"])
                for path in features["paths"].values():
                    path_lengths.add(len(path))
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profiles[signature] += 1

            mean_areas[band] = sum(areas) / len(areas)
            mean_pairs[band] = sum(pair_counts) / len(pair_counts)
            mean_walls[band] = sum(wall_counts) / len(wall_counts)
            self.assertGreaterEqual(len(pairs), 585)
            self.assertGreaterEqual(len(outputs), 585)
            self.assertEqual(
                set(profiles),
                generator._CANONICAL_PROFILE_SIGNATURES,
            )
            self.assertGreaterEqual(len(path_lengths), 8)
            self.assertGreaterEqual(max(wall_counts), 10)

        self.assertEqual(palette, set(generator._VALID_PALETTE))
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])
        self.assertLess(mean_pairs["easy"], mean_pairs["medium"])
        self.assertLess(mean_pairs["medium"], mean_pairs["hard"])
        self.assertLess(mean_walls["easy"], mean_walls["medium"])
        self.assertLess(mean_walls["medium"], mean_walls["hard"])

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
