from __future__ import annotations

from collections import Counter
import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root
import random
import unittest


ROOT = find_root(__file__)
TASK_ID = "27a915a2c9b3"
generator = import_module(
    "puzzle_generators.per_puzzle.27a915a2c9b3.generator"
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


class Generator27a915a2c9b3Tests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        rows = canonical_rows()
        self.assertTrue(rows)
        seen = set()
        observed = []
        for row in rows:
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    signature = (frozen(pair["input"]), frozen(pair["output"]))
                    if signature in seen:
                        continue
                    seen.add(signature)
                    source = copy.deepcopy(pair["input"])
                    before = copy.deepcopy(source)
                    analysis = generator._inspect_scene(source)
                    self.assertIsNotNone(analysis)
                    self.assertEqual(generator.self_check(source), [])
                    self.assertEqual(generator.rule_mirror(source), pair["output"])
                    self.assertEqual(source, before)
                    observed.append(analysis["scene_profile"])
        self.assertEqual(len(seen), 4)
        self.assertEqual(set(observed), set(generator._PUBLIC_SPECS))

    def test_rule_hash_and_base_sources_match_canonical_program(self):
        programs = {
            row["program_solution"]
            for row in canonical_rows()
        }
        self.assertEqual(len(programs), 1)
        program = programs.pop()
        digest = hashlib.sha256(program.encode()).hexdigest()
        self.assertEqual(generator.RULE_HASH, digest[:12])
        paths = (
            ROOT / "data/base/solutions/training/a04b2602__27a915a2c9b3.json",
            ROOT / "data/base/solutions/augmented/a04b2602__726b7171b72a.json",
        )
        for path in paths:
            record = json.loads(path.read_text())
            self.assertEqual(record["racket_target"]["raw_code"], program)
            self.assertEqual(record["racket_target"]["target_code"], program)

    def test_every_profile_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(24):
                    grid = generator.generate(
                        seed,
                        seed * 37 + 11,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._inspect_scene(grid)
                    self.assertIsNotNone(analysis)
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        generator.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": {"scene_profile": profile}},
                        ),
                        [],
                    )

    def test_exact_profiles_preserve_complete_linked_signatures(self):
        for profile, spec in generator._PUBLIC_SPECS.items():
            expected = generator._spec_signature(spec)
            positions = set()
            for seed in range(160):
                grid = generator.generate(
                    3_000 + seed,
                    seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                analysis = generator._inspect_scene(grid)
                self.assertEqual(analysis["signature"], expected)
                self.assertEqual(analysis["scene_profile"], profile)
                positions.add(
                    tuple(
                        sorted(
                            rectangle["bbox"]
                            for rectangle in analysis["rectangles"]
                        )
                    )
                )
            self.assertGreaterEqual(len(positions), 2)

    def test_default_distribution_covers_profiles_and_extremes(self):
        expected_shapes = {
            (20, 20),
            (10, 17),
            (16, 27),
        }
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            shapes = set()
            rectangle_counts = set()
            marker_counts = set()
            external_counts = set()
            distinct = set()
            for index in range(1_000):
                grid = generator.generate(
                    20_000 + band_index,
                    index,
                    difficulty=band,
                )
                analysis = generator._inspect_scene(grid)
                self.assertIsNotNone(analysis)
                profiles[analysis["scene_profile"]] += 1
                shapes.add(analysis["shape"])
                rectangle_counts.add(analysis["rectangle_count"])
                marker_counts.add(analysis["interior_count"])
                external_counts.add(analysis["external_count"])
                distinct.add(frozen(grid))
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertGreaterEqual(min(profiles.values()), 70)
            self.assertTrue(expected_shapes <= shapes)
            self.assertEqual(rectangle_counts, {2, 3})
            self.assertIn(4, marker_counts)
            self.assertIn(18, marker_counts)
            self.assertEqual(min(external_counts), 6)
            self.assertEqual(max(external_counts), 13)
            self.assertGreaterEqual(len(distinct), 995)

    def test_generalized_profile_never_claims_a_public_signature(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(320):
                grid = generator.generate(
                    seed,
                    50_000 + seed,
                    difficulty=band,
                    scene_profile="generalized",
                )
                analysis = generator._inspect_scene(grid)
                self.assertEqual(analysis["scene_profile"], "generalized")
                self.assertNotIn(
                    analysis["signature"],
                    generator._EXACT_SIGNATURES,
                )

    def test_rule_mirror_uses_only_inside_markers_and_is_input_pure(self):
        grid = [[0 for _ in range(8)] for _ in range(6)]
        for row in range(4):
            for col in range(4):
                grid[row][col] = 3
        grid[0][3] = 2
        grid[1][1] = 2
        grid[0][4] = 2
        grid[5][7] = 2
        before = copy.deepcopy(grid)
        output = generator.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[0][3], 2)
        self.assertEqual(output[1][1], 2)
        self.assertEqual(output[0][4], 1)
        self.assertEqual(output[5][7], 2)
        self.assertEqual(output[0][0], 1)
        self.assertEqual(output[5][0], 0)

    def test_generated_output_changes_exact_halo_union(self):
        for profile in generator.SCENE_PROFILES:
            for seed in range(80):
                grid = generator.generate(
                    seed,
                    70_000 + seed,
                    difficulty="hard",
                    scene_profile=profile,
                )
                analysis = generator._inspect_scene(grid)
                interior = set(analysis["interior_markers"])
                height, width = analysis["shape"]
                expected_changed = {
                    (row, col)
                    for marker_row, marker_col in interior
                    for row in range(
                        max(0, marker_row - 1),
                        min(height, marker_row + 2),
                    )
                    for col in range(
                        max(0, marker_col - 1),
                        min(width, marker_col + 2),
                    )
                    if (row, col) not in interior
                }
                output = generator.rule_mirror(grid)
                changed = {
                    (row, col)
                    for row in range(height)
                    for col in range(width)
                    if grid[row][col] != output[row][col]
                }
                self.assertEqual(changed, expected_changed)
                self.assertTrue(
                    all(output[row][col] == 1 for row, col in changed)
                )
                self.assertTrue(
                    all(output[row][col] == 2 for row, col in interior)
                )

    def test_strict_checker_rejects_nearest_destructive_mutations(self):
        grid = generator.generate(
            77,
            91,
            difficulty="medium",
            scene_profile="three_rect_dense_20x20",
        )
        analysis = generator._inspect_scene(grid)
        mutations = []

        wrong_color = copy.deepcopy(grid)
        wrong_color[0][0] = 9
        mutations.append(wrong_color)

        hole = copy.deepcopy(grid)
        rectangle = analysis["rectangles"][0]
        hole_cell = next(iter(rectangle["component"]))
        hole[hole_cell[0]][hole_cell[1]] = 0
        mutations.append(hole)

        too_few_external = copy.deepcopy(grid)
        for row, col in list(analysis["external_markers"])[5:]:
            too_few_external[row][col] = 0
        mutations.append(too_few_external)

        split_component = copy.deepcopy(grid)
        top, bottom, left, right = analysis["rectangles"][0]["bbox"]
        split_row = (top + bottom) // 2
        for col in range(left, right + 1):
            split_component[split_row][col] = 0
        mutations.append(split_component)

        malformed = [row[:] for row in grid]
        malformed[0] = malformed[0][:-1]
        mutations.append(malformed)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_generation_is_deterministic_fresh_and_global_rng_isolated(self):
        random.seed(271_915)
        state = random.getstate()
        first = generator.generate(123, 456, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(123, 456, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_invalid_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            generator.generate(0, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(0, 0, unknown_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(0, 0, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.rule_mirror([[0, 2], [3]])
        with self.assertRaises(ValueError):
            generator.rule_mirror([[False]])


if __name__ == "__main__":
    unittest.main()
