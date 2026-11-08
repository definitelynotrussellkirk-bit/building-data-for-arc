"""Focused semantic regressions for generator 51481963f4a3."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES

TASK_ID = "51481963f4a3"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT / "data/base/solutions/training/2a5f8217__51481963f4a3.json"
)


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _normalized_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current[0] + drow, current[1] + dcol
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            row0 = min(point[0] for point in cells)
            col0 = min(point[1] for point in cells)
            shape = tuple(
                sorted((point[0] - row0, point[1] - col0) for point in cells)
            )
            objects.append((color, tuple(sorted(cells)), shape))
    return objects


def _oracle(grid):
    objects = _components(grid)
    templates = {
        shape: color for color, _, shape in objects if color != 1
    }
    output = copy.deepcopy(grid)
    for color, cells, shape in objects:
        if color == 1:
            for row, col in cells:
                output[row][col] = templates[shape]
    return output


class Generator51481963f4a3Tests(unittest.TestCase):
    def test_all_canonical_pairs_match_independent_oracle_and_profiles(self):
        row = _canonical_row()
        expected_profiles = (
            "three_bijection",
            "single_match",
            "four_bijection",
            "five_shared_color",
        )
        profiles = []
        for pair in list(row["train"]) + list(row["test"]):
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(_oracle(source), pair["output"])
            self.assertEqual(source, before)
            profiles.append(MODULE.observe_overrides(source)["scene_profile"])
        self.assertEqual(tuple(profiles), expected_profiles)

    def test_every_forced_profile_is_exact_and_effectful_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                seen = set()
                size_patterns = set()
                for seed in range(40):
                    grid = MODULE.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(
                        MODULE.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        MODULE.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": {"scene_profile": profile}},
                        ),
                        [],
                    )
                    self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
                    self.assertNotEqual(grid, MODULE.rule_mirror(grid))
                    seen.add(tuple(map(tuple, grid)))
                    info = MODULE._analyze_scene(grid)
                    sizes = tuple(sorted(
                        obj["size"] for obj in info["templates"]
                    ))
                    size_patterns.add(sizes)
                    if profile == "two_bijection":
                        self.assertEqual(len(set(sizes)), 1)
                    elif profile != "single_match":
                        self.assertGreaterEqual(len(set(sizes)), 2)
                self.assertGreaterEqual(len(seen), 35)
                if profile == "single_match":
                    self.assertEqual(
                        {sizes[0] for sizes in size_patterns},
                        {2, 3, 4, 5, 6},
                    )
                elif profile == "two_bijection":
                    self.assertEqual(
                        {sizes[0] for sizes in size_patterns},
                        {3, 4, 5, 6},
                    )
                else:
                    self.assertGreaterEqual(len(size_patterns), 10)

    def test_linked_semantic_census_covers_shortcut_resistant_branches(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(811, 977, scene_profile=profile)
            info = MODULE._analyze_scene(grid)
            self.assertEqual(info["errors"], [])
            template_shapes = [obj["shape"] for obj in info["templates"]]
            query_shapes = [obj["shape"] for obj in info["queries"]]
            self.assertEqual(len(template_shapes), len(set(template_shapes)))
            self.assertEqual(set(template_shapes), set(query_shapes))
            if len(template_shapes) > 1:
                sizes = Counter(obj["size"] for obj in info["templates"])
                self.assertGreaterEqual(max(sizes.values()), 2)
            if profile == "five_shared_color":
                colors = Counter(obj["color"] for obj in info["templates"])
                self.assertEqual(sorted(colors.values()), [1, 1, 1, 2])
            if profile == "repeated_query":
                queries = Counter(query_shapes)
                self.assertEqual(sorted(queries.values()), [1, 1, 2])

    def test_default_distribution_covers_all_profiles_and_remains_diverse(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(480):
                grid = MODULE.generate(seed, seed * 29 + 5, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertGreaterEqual(min(profiles.values()), 55)
            self.assertGreaterEqual(len(inputs), 470)
            self.assertGreaterEqual(len(outputs), 450)

    def test_self_check_rejects_targeted_impostors(self):
        canonical = _canonical_row()["train"][1]["input"]

        nonzero_background = [
            [9 if value == 0 else value for value in row]
            for row in canonical
        ]

        touching_components = copy.deepcopy(canonical)
        touching_components[2][4] = 1

        unused_template = MODULE.generate(
            101, 103, scene_profile="three_bijection"
        )
        absent_color = next(
            color
            for color in range(2, 10)
            if all(color not in row for row in unused_template)
        )
        placed = False
        for row in range(1, len(unused_template) - 1):
            for col in range(1, len(unused_template[0]) - 1):
                if unused_template[row][col] != 0:
                    continue
                if all(
                    unused_template[row + drow][col + dcol] == 0
                    for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    unused_template[row][col] = absent_color
                    placed = True
                    break
            if placed:
                break
        self.assertTrue(placed)

        invalid_color = copy.deepcopy(canonical)
        invalid_color[0][0] = 10
        boolean_cell = copy.deepcopy(canonical)
        boolean_cell[0][0] = True
        ragged = copy.deepcopy(canonical)
        ragged[0].pop()

        for mutation in (
            nonzero_background,
            touching_components,
            unused_template,
            invalid_color,
            boolean_cell,
            ragged,
        ):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_profile_meta_mismatch_is_rejected(self):
        grid = MODULE.generate(7, 11, scene_profile="single_match")
        self.assertTrue(
            MODULE.self_check(
                grid,
                meta={"overrides": {"scene_profile": "two_bijection"}},
            )
        )

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(71, 89, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(71, 89, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        snapshot = copy.deepcopy(first)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(snapshot, MODULE.generate(71, 89, difficulty="hard"))

    def test_checker_and_mirror_are_input_pure(self):
        grid = MODULE.generate(17, 19, difficulty="medium")
        before = copy.deepcopy(grid)
        MODULE.self_check(grid)
        MODULE.observe_overrides(grid)
        MODULE.rule_mirror(grid)
        self.assertEqual(grid, before)

    def test_invalid_difficulty_and_overrides_fail_loudly(self):
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, scene_profile="unknown")
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, n_templates=3)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, texture="no_templates")

    def test_shape_catalog_uses_disjoint_d4_orbits(self):
        orbits = [
            {MODULE._transform_shape(shape, code) for code in range(8)}
            for shape in MODULE._SHAPE_CATALOG
        ]
        for left in range(len(orbits)):
            for right in range(left):
                self.assertFalse(orbits[left] & orbits[right])

    def test_rule_hash_matches_every_authority(self):
        canonical = _canonical_row()["program_solution"]
        base = json.loads(BASE_PATH.read_text())
        authorities = (
            canonical,
            GROUNDED_RULES[TASK_ID],
            base["racket_target"]["raw_code"],
            base["racket_target"]["target_code"],
        )
        self.assertTrue(all(_normalized_hash(source) == MODULE.RULE_HASH for source in authorities))
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)


if __name__ == "__main__":
    unittest.main()
