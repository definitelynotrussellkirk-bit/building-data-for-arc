"""Focused semantic regressions for generator 24b83272f157."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import random
import unittest

from puzzle_generators.runner import _load_generator_module
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ID = "24b83272f157"
DEGREE_COLORS = {0: 2, 1: 3, 2: 8, 3: 6, 4: 9}


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_pairs():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                pairs = copy.deepcopy(record["train"] + record["test"])
                return record, pairs
    raise AssertionError("canonical task row is missing")


def independent_objects(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current = stack.pop()
                cells.append(current)
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    neighbor = (
                        current[0] + delta_row,
                        current[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            objects.append(tuple(cells))
    return objects


def independent_rule(grid):
    objects = independent_objects(grid)
    neighbors = [set() for _ in objects]
    for first in range(len(objects)):
        for second in range(first + 1, len(objects)):
            distance = min(
                abs(row_a - row_b) + abs(col_a - col_b)
                for row_a, col_a in objects[first]
                for row_b, col_b in objects[second]
            )
            if distance <= 2:
                neighbors[first].add(second)
                neighbors[second].add(first)
    output = [[0 for _ in row] for row in grid]
    for cells, adjacent in zip(objects, neighbors):
        color = DEGREE_COLORS.get(len(adjacent), 9)
        for row, col in cells:
            output[row][col] = color
    return output


class Generator24B83272F157Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_all_canonical_pairs_and_linked_profiles(self):
        _, pairs = canonical_pairs()
        profiles = (
            "public_train_1",
            "public_train_2",
            "public_test_1",
        )
        self.assertEqual(3, len(pairs))
        for pair, profile in zip(pairs, profiles):
            with self.subTest(profile=profile):
                grid = copy.deepcopy(pair["input"])
                analysis = self.module._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual("linked", analysis["facts"]["family"])
                self.assertEqual(
                    profile, analysis["facts"]["linked_profile"]
                )
                self.assertEqual(pair["output"], independent_rule(grid))
                self.assertEqual(pair["output"], self.module.rule_mirror(grid))
                self.assertEqual(pair["input"], grid)

    def test_rule_target_is_pinned(self):
        record, _ = canonical_pairs()
        target = record["program_solution"]
        self.assertEqual("ede817c8e772", normalized_hash(target))
        self.assertEqual(normalized_hash(target), self.module.RULE_HASH)

    def test_forced_families_and_every_profile(self):
        linked_profiles = set()
        generalized_profiles = set()
        degree_values = set()
        for band in ("easy", "medium", "hard"):
            for family in ("linked", "generalized"):
                for sample_index in range(300):
                    grid = self.module.generate(
                        100_000 + sample_index,
                        sample_index * 17 + 5,
                        difficulty=band,
                        scene_family=family,
                    )
                    before = copy.deepcopy(grid)
                    analysis = self.module._analyze(grid)
                    self.assertEqual([], analysis["errors"])
                    facts = analysis["facts"]
                    self.assertEqual(family, facts["family"])
                    self.assertEqual(
                        {"scene_family": family},
                        self.module.observe_overrides(grid),
                    )
                    self.assertEqual(independent_rule(grid), facts["output"])
                    self.assertEqual(before, grid)
                    degree_values.update(facts["degrees"])
                    if family == "linked":
                        linked_profiles.add(facts["linked_profile"])
                    else:
                        generalized_profiles.add(
                            facts["generalized_profile"]
                        )
        self.assertEqual(
            {"public_train_1", "public_train_2", "public_test_1"},
            linked_profiles,
        )
        self.assertEqual(
            set(self.module.GENERAL_PROFILES), generalized_profiles
        )
        self.assertTrue({0, 1, 2, 3, 4}.issubset(degree_values))

    def test_contact_boundary_and_degree_causality(self):
        distance_two = [
            [4 if (row, col) == (2, 1)
             else 7 if (row, col) == (2, 3)
             else 5 if (row, col) == (5, 7)
             else 0
             for col in range(9)]
            for row in range(7)
        ]
        output = independent_rule(distance_two)
        self.assertEqual(3, output[2][1])
        self.assertEqual(3, output[2][3])
        self.assertEqual(2, output[5][7])

        distance_three = copy.deepcopy(distance_two)
        distance_three[2][3] = 0
        distance_three[2][4] = 7
        output = independent_rule(distance_three)
        self.assertEqual(2, output[2][1])
        self.assertEqual(2, output[2][4])

        star = [
            [0 for _ in range(9)]
            for _ in range(9)
        ]
        for (row, col), color in zip(
            ((4, 4), (2, 4), (4, 2), (4, 6), (6, 4), (8, 8)),
            (1, 2, 3, 4, 5, 7),
        ):
            star[row][col] = color
        output = independent_rule(star)
        self.assertEqual(9, output[4][4])
        for row, col in ((2, 4), (4, 2), (4, 6), (6, 4)):
            self.assertEqual(3, output[row][col])
        self.assertEqual(2, output[8][8])

    def test_polyominoes_recolor_whole_objects(self):
        found_repeated_color = False
        for sample_index in range(500):
            grid = self.module.generate(
                222,
                sample_index,
                difficulty="hard",
                scene_family="generalized",
            )
            facts = self.module._analyze(grid)["facts"]
            if facts["generalized_profile"] != "poly_chain":
                continue
            self.assertTrue(any(size > 1 for size in facts["object_sizes"]))
            self.assertEqual(independent_rule(grid), facts["output"])
            for obj, degree in zip(
                facts["components"], facts["degrees"]
            ):
                colors = {
                    facts["output"][row][col] for row, col in obj["cells"]
                }
                self.assertEqual(
                    {DEGREE_COLORS.get(degree, 9)}, colors
                )
            input_colors = [
                obj["color"] for obj in facts["components"]
            ]
            found_repeated_color |= len(input_colors) != len(set(input_colors))
        self.assertTrue(found_repeated_color)

    def test_reflection_rotation_and_color_automorphisms(self):
        grid = copy.deepcopy(canonical_pairs()[1][0]["input"])
        transformed = [
            [9 if value == 2 else 1 if value == 4 else 5 if value == 3
             else 7 if value == 7 else value
             for value in row]
            for row in grid
        ]
        transformed = [list(row) for row in zip(*transformed[::-1])]
        expected = [list(row) for row in zip(*independent_rule(grid)[::-1])]
        self.assertEqual(expected, independent_rule(transformed))

    def test_natural_prior_diversity_and_difficulty(self):
        shape_sets = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            profiles = set()
            inputs = set()
            outputs = set()
            shapes = set()
            for sample_index in range(800):
                grid = self.module.generate(
                    600_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[facts["family"]] += 1
                profiles.add(
                    facts["linked_profile"]
                    or facts["generalized_profile"]
                )
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertGreaterEqual(families["linked"], 180)
            self.assertGreaterEqual(families["generalized"], 480)
            self.assertEqual(10, len(profiles))
            self.assertGreaterEqual(len(inputs), 770)
            # Output colors intentionally discard arbitrary source colors, so
            # output diversity is topology/placement-limited rather than
            # matching the near-perfect input uniqueness.
            self.assertGreaterEqual(len(outputs), 600)
            shape_sets[band] = shapes
        self.assertNotEqual(shape_sets["easy"], shape_sets["medium"])
        self.assertNotEqual(shape_sets["medium"], shape_sets["hard"])

    def test_self_check_rejects_semantic_impostors(self):
        impostors = {
            "all_background": [[0] * 9 for _ in range(7)],
            "full_color": [[4] * 9 for _ in range(7)],
            "one_object": [
                [4 if (row, col) == (2, 2) else 0 for col in range(9)]
                for row in range(7)
            ],
            "all_isolated": [
                [4 if (row, col) in ((0, 0), (3, 3), (6, 6)) else 0
                 for col in range(9)]
                for row in range(7)
            ],
            "same_degree": [
                [4 if (row, col) == (2, 1)
                 else 7 if (row, col) == (2, 3)
                 else 0
                 for col in range(9)]
                for row in range(7)
            ],
            "ragged": [[0] * 9 for _ in range(6)] + [[0] * 8],
            "boolean": [
                [True if (row, col) == (2, 2) else 0
                 for col in range(9)]
                for row in range(7)
            ],
            "bad_value": [
                [10 if (row, col) == (2, 2) else 0
                 for col in range(9)]
                for row in range(7)
            ],
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        second = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        second[0][0] = 9
        third = self.module.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, third)
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, unknown_axis="x")
        with self.assertRaises(ValueError):
            self.module.generate(1, 2, scene_family="wrong")


if __name__ == "__main__":
    unittest.main()
