"""Focused semantic regressions for cross-zone generator 08f1d9bdd2ef."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "08f1d9bdd2ef"
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def layout_path(relative: str) -> Path:
    rel = Path(relative)
    candidates = (ROOT / rel, ROOT / "shared" / rel, ROOT / "shared/runtime" / rel)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing portable runtime source: {relative}")


def canonical_row() -> dict:
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def grounded_rule() -> str:
    tree = ast.parse(layout_path("solvers/grounded_rules.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == TASK_ID:
                return ast.literal_eval(value)
    raise AssertionError("grounded rule not found")


def independent_transform(grid):
    height, width = len(grid), len(grid[0])
    sep_rows = [
        row for row in range(height)
        if all(grid[row][col] == 8 for col in range(width))
    ]
    sep_cols = [
        col for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    output = [[0] * width for _ in range(height)]
    colors = {(0, 1): 2, (1, 0): 4, (1, 1): 6, (1, 2): 3, (2, 1): 1}
    for row in range(height):
        for col in range(width):
            if row in sep_rows or col in sep_cols:
                output[row][col] = 8
                continue
            row_band = int(row > sep_rows[0]) + int(row > sep_rows[1])
            col_band = int(col > sep_cols[0]) + int(col > sep_cols[1])
            output[row][col] = colors.get((row_band, col_band), 0)
    return output


class CrossZoneGeneratorTests(unittest.TestCase):
    def test_version_hash_and_axis_contract_are_current(self):
        self.assertEqual("4.0.0", GENERATOR.VERSION)
        self.assertEqual("99b51630ed1d", GENERATOR.RULE_HASH)
        self.assertEqual({"scene_family"}, set(GENERATOR.AXES))

    def test_every_canonical_pair_is_valid_public_and_exact(self):
        row = canonical_row()
        self.assertEqual(2, len(row["train"]))
        self.assertEqual(1, len(row["test"]))
        for pair in row["train"] + row["test"]:
            self.assertEqual([], GENERATOR.self_check(pair["input"]))
            self.assertEqual("public", GENERATOR.canonical_profile_signature(pair["input"]))
            self.assertEqual(pair["output"], GENERATOR.rule_mirror(pair["input"]))
            self.assertEqual(pair["output"], independent_transform(pair["input"]))

    def test_complete_public_profile_set_contains_all_official_d4_orbits(self):
        self.assertEqual(20, len(GENERATOR._PUBLIC_PROFILES))
        for base in GENERATOR._PUBLIC_BASE_PROFILES:
            for transform in range(8):
                profile = GENERATOR._transform_spec(*base, transform)
                self.assertIn(profile, GENERATOR._PUBLIC_SIGNATURES)

    def test_public_and_generalized_overrides_are_exact_and_observable(self):
        for difficulty in ("default", "easy", "medium", "hard"):
            for family in ("public", "generalized"):
                for seed in range(50):
                    grid = GENERATOR.generate(
                        seed, seed * 7, difficulty=difficulty, scene_family=family
                    )
                    self.assertEqual([], GENERATOR.self_check(grid))
                    self.assertEqual(
                        {"scene_family": family}, GENERATOR.observe_overrides(grid)
                    )

    def test_curriculum_schedule_is_calibrated_and_covers_every_public_profile(self):
        for difficulty in ("easy", "medium", "hard"):
            public = 0
            styles = set()
            for sample_index in range(5000):
                grid = GENERATOR.generate(0, sample_index, difficulty=difficulty)
                facts = GENERATOR._analyze(grid)["facts"]
                if GENERATOR.canonical_profile_signature(grid) == "public":
                    public += 1
                    styles.add((
                        GENERATOR._order_style(facts["row_band_sizes"]),
                        GENERATOR._order_style(facts["col_band_sizes"]),
                    ))
            self.assertEqual(1250, public)
            self.assertEqual(GENERATOR._PUBLIC_STYLE_PAIRS, styles)

    def test_generalized_candidate_space_covers_declared_shape_envelopes(self):
        for difficulty, (minimum, maximum) in GENERATOR._BAND_DIMENSIONS.items():
            heights, widths = set(), set()
            blocks, _total = GENERATOR._CANDIDATES[(difficulty, "generalized")]
            for row_triples, col_triples, _count in blocks:
                heights.update(sum(triple) + 2 for triple in row_triples)
                widths.update(sum(triple) + 2 for triple in col_triples)
            expected = set(range(minimum, maximum + 1))
            self.assertEqual(expected, heights)
            self.assertEqual(expected, widths)

    def test_every_generated_output_obeys_the_positional_color_contract(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(250):
                grid = GENERATOR.generate(seed, seed * 19, difficulty=difficulty)
                output = GENERATOR.rule_mirror(grid)
                self.assertEqual(independent_transform(grid), output)
                self.assertEqual({0, 1, 2, 3, 4, 6, 8}, {
                    value for row in output for value in row
                })
                self.assertNotEqual(grid, output)

    def test_all_band_sizes_are_positive_and_observed(self):
        for seed in range(500):
            grid = GENERATOR.generate(seed, seed + 3, difficulty="hard")
            facts = GENERATOR._analyze(grid)["facts"]
            self.assertGreaterEqual(min(facts["row_band_sizes"]), 1)
            self.assertGreaterEqual(min(facts["col_band_sizes"]), 1)

    def test_seed_and_sample_index_are_sensitive(self):
        by_seed = {
            tuple(map(tuple, GENERATOR.generate(seed, 0, difficulty="medium")))
            for seed in range(100)
        }
        by_sample = {
            tuple(map(tuple, GENERATOR.generate(0, sample, difficulty="medium")))
            for sample in range(100)
        }
        self.assertGreaterEqual(len(by_seed), 75)
        self.assertGreaterEqual(len(by_sample), 75)

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(99173)
        state = random.getstate()
        first = GENERATOR.generate(31, 47, difficulty="hard")
        snapshot = copy.deepcopy(first)
        second = GENERATOR.generate(31, 47, difficulty="hard")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertEqual(snapshot, GENERATOR.generate(31, 47, difficulty="hard"))

    def test_checker_mirror_and_observer_are_input_pure(self):
        grid = GENERATOR.generate(81, 12, difficulty="hard")
        snapshot = copy.deepcopy(grid)
        GENERATOR.self_check(grid)
        GENERATOR.rule_mirror(grid)
        GENERATOR.observe_overrides(grid)
        self.assertEqual(snapshot, grid)

    def test_unknown_difficulty_and_override_fail_loudly(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, invented_axis=True)

    def test_checker_rejects_bad_shapes_types_and_dimensions(self):
        self.assertTrue(GENERATOR.self_check([]))
        self.assertTrue(GENERATOR.self_check([[0, 8], [0]]))
        self.assertTrue(GENERATOR.self_check([[True] * 8 for _ in range(8)]))
        self.assertTrue(GENERATOR.self_check([[11] * 8 for _ in range(8)]))
        self.assertTrue(GENERATOR.self_check([[0] * 4 for _ in range(4)]))

    def test_checker_rejects_extra_or_missing_palette_colors(self):
        grid = GENERATOR.generate(4, 9, difficulty="easy", scene_family="generalized")
        extra = copy.deepcopy(grid)
        row, col = next(
            (r, c) for r, values in enumerate(extra) for c, value in enumerate(values)
            if value == 0
        )
        extra[row][col] = 5
        self.assertTrue(GENERATOR.self_check(extra))
        self.assertTrue(GENERATOR.self_check([[0] * 8 for _ in range(8)]))

    def test_checker_rejects_deleted_or_added_divider(self):
        grid = GENERATOR.generate(11, 12, difficulty="medium", scene_family="generalized")
        facts = GENERATOR._analyze(grid)["facts"]
        deleted = copy.deepcopy(grid)
        deleted[facts["sep_rows"][0]][0] = 0
        self.assertTrue(GENERATOR.self_check(deleted))
        added = copy.deepcopy(grid)
        new_row = next(row for row in range(len(added)) if row not in facts["sep_rows"])
        added[new_row] = [8] * len(added[0])
        self.assertTrue(GENERATOR.self_check(added))

    def test_checker_rejects_zero_area_zones(self):
        grid = GENERATOR._build_scene(8, 9, (0, 3), (2, 6))
        self.assertTrue(GENERATOR.self_check(grid))
        grid = GENERATOR._build_scene(8, 9, (2, 3), (2, 6))
        self.assertTrue(GENERATOR.self_check(grid))

    def test_rule_hash_and_all_live_sources_are_synchronized(self):
        row = canonical_row()
        base = json.loads(
            layout_path("data/base/solutions/training/272f95fa__08f1d9bdd2ef.json").read_text()
        )
        sources = {
            row["program_solution"],
            base["racket_target"]["raw_code"],
            base["racket_target"]["target_code"],
            grounded_rule(),
        }
        self.assertEqual(1, len(sources))
        self.assertEqual({GENERATOR.RULE_HASH}, {normalized_hash(source) for source in sources})

    def test_obsolete_divergence_inventories_no_longer_name_task(self):
        names = (
            "rule_source_divergence.json",
            "rule_source_divergence_semantic.json",
        )
        try:
            paths = [layout_path(f"data/derived/{name}") for name in names]
        except FileNotFoundError:
            self.skipTest("global derived inventories are not part of the portable task runtime")
        for inventory in paths:
            rows = json.loads(inventory.read_text())
            self.assertNotIn(TASK_ID, {row.get("task_id") for row in rows})


if __name__ == "__main__":
    unittest.main()
