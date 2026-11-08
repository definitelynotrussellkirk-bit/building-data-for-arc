"""Focused semantic regressions for paired-line generator 05409de4bec8."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "05409de4bec8"
LEGACY_ID = "6cdd2623"
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.05409de4bec8.generator"
)


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_rows() -> list[dict]:
    return [
        row
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    ]


def grounded_rule() -> str:
    tree = ast.parse((ROOT / "solvers/grounded_rules.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == TASK_ID:
                return ast.literal_eval(value)
    raise AssertionError("grounded rule not found")


def cells_of(grid, color):
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def d4_grid(grid, operation):
    height, width = len(grid), len(grid[0])
    if operation < 4:
        out_height, out_width = height, width
    else:
        out_height, out_width = width, height
    output = [[0] * out_width for _ in range(out_height)]
    for row in range(height):
        for col in range(width):
            point = {
                0: (row, col),
                1: (row, width - 1 - col),
                2: (height - 1 - row, col),
                3: (height - 1 - row, width - 1 - col),
                4: (col, row),
                5: (col, height - 1 - row),
                6: (width - 1 - col, row),
                7: (width - 1 - col, height - 1 - row),
            }[operation]
            output[point[0]][point[1]] = grid[row][col]
    return output


class PairedLineGeneratorTests(unittest.TestCase):
    def test_version_hash_and_axis_contract_are_current(self):
        self.assertEqual("4.0.0", GENERATOR.VERSION)
        self.assertEqual("dfbf6efa8173", GENERATOR.RULE_HASH)
        self.assertEqual({"scene_family"}, set(GENERATOR.AXES))

    def test_all_canonical_rows_and_pairs_are_preserved(self):
        rows = canonical_rows()
        self.assertEqual(2, len(rows))
        self.assertEqual({"training", "augmented"}, {row["source"] for row in rows})
        self.assertEqual(8, sum(len(row["train"] + row["test"]) for row in rows))
        for row in rows:
            for pair in row["train"] + row["test"]:
                self.assertEqual([], GENERATOR.self_check(pair["input"]))
                self.assertEqual(pair["output"], GENERATOR.rule_mirror(pair["input"]))
                self.assertEqual("public", GENERATOR.canonical_profile_signature(pair["input"]))

    def test_unique_canonical_profiles_cover_rectangle_and_cross(self):
        pairs = {
            tuple(map(tuple, pair["input"])): pair
            for row in canonical_rows()
            for pair in row["train"] + row["test"]
        }
        self.assertEqual(4, len(pairs))
        facts = [GENERATOR._analyze(pair["input"])["facts"] for pair in pairs.values()]
        self.assertEqual(Counter({False: 3, True: 1}), Counter(f["rectangle"] for f in facts))
        self.assertEqual({(2, 0), (1, 1)}, {
            (len(f["horizontal"]), len(f["vertical"])) for f in facts
        })
        self.assertEqual({2, 3, 6, 8}, {f["target_color"] for f in facts})
        self.assertEqual({(8, 29), (10, 11), (14, 25), (19, 28)}, {
            f["decoy_counts"] for f in facts
        })

    def test_public_and_generalized_overrides_are_exact_and_observable(self):
        for difficulty in ("default", "easy", "medium", "hard"):
            for family in ("public", "generalized"):
                for seed in range(60):
                    grid = GENERATOR.generate(
                        seed, seed * 7, difficulty=difficulty, scene_family=family
                    )
                    self.assertEqual([], GENERATOR.self_check(grid))
                    self.assertEqual(
                        {"scene_family": family}, GENERATOR.observe_overrides(grid)
                    )

    def test_natural_prior_is_calibrated_and_reaches_every_public_d4_signature(self):
        for difficulty in ("easy", "medium", "hard"):
            public = 0
            signatures = set()
            for seed in range(5000):
                grid = GENERATOR.generate(seed, seed * 13, difficulty=difficulty)
                facts = GENERATOR._analyze(grid)["facts"]
                signature = GENERATOR._profile_signature(
                    facts["height"], facts["width"], facts["points"],
                    facts["decoy_counts"],
                )
                if GENERATOR.canonical_profile_signature(grid) == "public":
                    public += 1
                    signatures.add(signature)
            self.assertGreaterEqual(public, 1000)
            self.assertLessEqual(public, 1500)
            self.assertEqual(GENERATOR._PUBLIC_SIGNATURES, signatures)

    def test_generalized_bands_cover_the_declared_envelopes(self):
        expected = {
            "easy": ((10, 15), (15, 21), (8, 18)),
            "medium": ((11, 19), (16, 24), (14, 30)),
            "hard": ((15, 24), (18, 28), (20, 42)),
        }
        expected_branches = {
            "easy": {(2, 0), (0, 2), (1, 1), (1, 0), (0, 1)},
            "medium": {(2, 0), (0, 2), (1, 1), (2, 1), (1, 2), (1, 0), (0, 1)},
            "hard": {(2, 0), (0, 2), (1, 1), (2, 1), (1, 2), (1, 0), (0, 1)},
        }
        for difficulty, (rows, cols, decoys) in expected.items():
            seen_rows, seen_cols, seen_decoys, seen_branches = set(), set(), set(), set()
            for seed in range(3500):
                grid = GENERATOR.generate(
                    seed, seed * 17, difficulty=difficulty,
                    scene_family="generalized",
                )
                facts = GENERATOR._analyze(grid)["facts"]
                seen_rows.add(facts["height"])
                seen_cols.add(facts["width"])
                seen_decoys.update(facts["decoy_counts"])
                seen_branches.add((len(facts["horizontal"]), len(facts["vertical"])))
            self.assertEqual(set(range(rows[0], rows[1] + 1)), seen_rows)
            self.assertEqual(set(range(cols[0], cols[1] + 1)), seen_cols)
            self.assertEqual(set(range(decoys[0], decoys[1] + 1)), seen_decoys)
            self.assertEqual(expected_branches[difficulty], seen_branches)

    def test_generated_palette_counts_and_output_contract(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = GENERATOR.generate(seed, seed * 19, difficulty=difficulty)
                facts = GENERATOR._analyze(grid)["facts"]
                counts = Counter(value for row in grid for value in row)
                self.assertEqual(4, len(counts))
                self.assertEqual(4, counts[facts["target_color"]])
                self.assertEqual(2, len(facts["decoy_counts"]))
                output = GENERATOR.rule_mirror(grid)
                self.assertEqual({0, facts["target_color"]}, {
                    value for row in output for value in row
                })
                self.assertNotEqual(grid, output)

    def test_seed_and_sample_index_are_sensitive(self):
        by_seed = {
            tuple(map(tuple, GENERATOR.generate(seed, 0, difficulty="medium")))
            for seed in range(80)
        }
        by_sample = {
            tuple(map(tuple, GENERATOR.generate(0, sample, difficulty="medium")))
            for sample in range(80)
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
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(snapshot, GENERATOR.generate(31, 47, difficulty="hard"))

    def test_checker_and_mirror_are_input_pure(self):
        grid = GENERATOR.generate(81, 12, difficulty="hard")
        snapshot = copy.deepcopy(grid)
        GENERATOR.self_check(grid)
        GENERATOR.rule_mirror(grid)
        GENERATOR.observe_overrides(grid)
        self.assertEqual(snapshot, grid)

    def test_d4_and_bijective_color_metamorphisms_commute_with_rule(self):
        for seed in range(20):
            source = GENERATOR.generate(
                1200 + seed, seed * 29, difficulty="hard",
                scene_family="generalized",
            )
            expected = GENERATOR.rule_mirror(source)
            for operation in range(8):
                transformed = d4_grid(source, operation)
                self.assertEqual([], GENERATOR.self_check(transformed))
                self.assertEqual(
                    d4_grid(expected, operation), GENERATOR.rule_mirror(transformed)
                )
            recolored = [
                [0 if value == 0 else value % 9 + 1 for value in row]
                for row in source
            ]
            recolored_expected = [
                [0 if value == 0 else value % 9 + 1 for value in row]
                for row in expected
            ]
            self.assertEqual([], GENERATOR.self_check(recolored))
            self.assertEqual(recolored_expected, GENERATOR.rule_mirror(recolored))

    def test_unknown_difficulty_and_override_fail_loudly(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, invented_axis=True)

    def test_checker_rejects_bad_shapes_types_and_dimensions(self):
        self.assertTrue(GENERATOR.self_check([]))
        self.assertTrue(GENERATOR.self_check([[0, 1], [0]]))
        self.assertTrue(GENERATOR.self_check([[True] * 10 for _ in range(10)]))
        self.assertTrue(GENERATOR.self_check([[11] * 10 for _ in range(10)]))
        grid = GENERATOR.generate(4, 9, difficulty="easy", scene_family="generalized")
        self.assertTrue(GENERATOR.self_check(grid[:8]))

    def test_checker_rejects_deleted_or_added_target_cell(self):
        grid = GENERATOR.generate(11, 12, difficulty="medium", scene_family="generalized")
        facts = GENERATOR._analyze(grid)["facts"]
        deleted = copy.deepcopy(grid)
        row, col = facts["points"][0]
        deleted[row][col] = 0
        self.assertTrue(GENERATOR.self_check(deleted))
        added = copy.deepcopy(grid)
        row, col = next(
            (r, c) for r, values in enumerate(added) for c, value in enumerate(values)
            if value == 0
        )
        added[row][col] = facts["target_color"]
        self.assertTrue(GENERATOR.self_check(added))

    def test_checker_rejects_ambiguous_target_and_short_decoy(self):
        grid = GENERATOR.generate(21, 22, difficulty="easy", scene_family="generalized")
        facts = GENERATOR._analyze(grid)["facts"]
        decoy = next(color for color in set(sum(grid, [])) if color not in {0, facts["target_color"]})
        ambiguous = copy.deepcopy(grid)
        for row, col in cells_of(ambiguous, decoy):
            ambiguous[row][col] = 0
        for row, col in ((0, 0), (0, 1), (1, 0), (1, 1)):
            if ambiguous[row][col] == facts["target_color"]:
                ambiguous[row][col] = 0
            ambiguous[row][col] = decoy
        self.assertTrue(GENERATOR.self_check(ambiguous))

        short = copy.deepcopy(grid)
        for row, col in cells_of(short, decoy)[3:]:
            short[row][col] = 0
        self.assertTrue(GENERATOR.self_check(short))

    def test_checker_rejects_extra_palette_color_and_equal_rectangle(self):
        grid = GENERATOR.generate(23, 24, difficulty="medium", scene_family="generalized")
        extra = copy.deepcopy(grid)
        unused = next(color for color in range(1, 10) if color not in set(sum(extra, [])))
        row, col = next(
            (r, c) for r, values in enumerate(extra) for c, value in enumerate(values)
            if value == 0
        )
        extra[row][col] = unused
        self.assertTrue(GENERATOR.self_check(extra))

        equal = [[0] * 12 for _ in range(12)]
        for row, col in ((2, 2), (2, 7), (7, 2), (7, 7)):
            equal[row][col] = 1
        for col in range(10):
            equal[0][col] = 2
            equal[11][col] = 3
        self.assertTrue(GENERATOR.self_check(equal))

    def test_lawful_near_miss_is_generalized_not_public(self):
        public = GENERATOR.generate(101, 33, scene_family="public")
        facts = GENERATOR._analyze(public)["facts"]
        decoy = next(
            color for color in set(sum(public, []))
            if color not in {0, facts["target_color"]} and len(cells_of(public, color)) < 50
        )
        near = copy.deepcopy(public)
        row, col = next(
            (r, c) for r, values in enumerate(near) for c, value in enumerate(values)
            if value == 0
        )
        near[row][col] = decoy
        self.assertEqual([], GENERATOR.self_check(near))
        self.assertEqual("generalized", GENERATOR.canonical_profile_signature(near))

    def test_all_stable_rule_sources_match_the_generator_pin(self):
        rows = canonical_rows()
        hashes = {normalized_hash(row["program_solution"]) for row in rows}
        hashes.add(normalized_hash(grounded_rule()))
        for source, content_hash in (
            ("training", TASK_ID), ("augmented", "3d927549b8b9")
        ):
            path = ROOT / "data/base/solutions" / source / f"{LEGACY_ID}__{content_hash}.json"
            base = json.loads(path.read_text())
            self.assertEqual("rule_body", base["racket_target"]["code_form"])
            hashes.add(normalized_hash(base["racket_target"]["raw_code"]))
            hashes.add(normalized_hash(base["racket_target"]["target_code"]))
            self.assertGreaterEqual(len(base["description_target"]["solution_steps"]), 5)
        self.assertEqual({GENERATOR.RULE_HASH}, hashes)


if __name__ == "__main__":
    unittest.main()
