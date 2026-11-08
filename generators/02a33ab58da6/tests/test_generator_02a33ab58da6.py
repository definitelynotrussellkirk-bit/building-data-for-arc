"""Focused semantic regressions for generator 02a33ab58da6."""
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

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ID = "02a33ab58da6"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.02a33ab58da6.generator"
)


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row():
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def grounded_rule():
    tree = ast.parse((ROOT / "solvers/grounded_rules.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == TASK_ID:
                return ast.literal_eval(value)
    raise AssertionError("grounded rule not found")


class RotateTailGeneratorTests(unittest.TestCase):
    def test_version_hash_and_axes_are_current(self):
        self.assertEqual("4.1.0", gen.VERSION)
        self.assertEqual("74c9a82b96dc", gen.RULE_HASH)
        self.assertEqual({"scene_family"}, set(gen.AXES))

    def test_all_canonical_pairs_pass_checker_and_python_mirror(self):
        row = canonical_row()
        for pair in row["train"] + row["test"]:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_canonical_profiles_capture_counts_lengths_and_directions(self):
        row = canonical_row()
        facts = [gen._analyze(pair["input"])["facts"] for pair in row["train"] + row["test"]]
        self.assertEqual([2, 1, 3, 7], [item["motif_count"] for item in facts])
        self.assertEqual({0, 1, 2, 4, 7}, {move["bar_len"] for item in facts for move in item["moves"]})
        self.assertEqual({1, 2, 3, 4, 5}, {move["tail_len"] for item in facts for move in item["moves"]})
        self.assertEqual(set(gen._DIRECTIONS), {move["direction"] for item in facts for move in item["moves"]})

    def test_all_canonical_inputs_are_complete_public_profiles(self):
        for pair in canonical_row()["train"] + canonical_row()["test"]:
            self.assertEqual("public", gen.canonical_profile_signature(pair["input"]))

    def test_public_override_is_exact_and_observed(self):
        for difficulty in ("default", "easy", "medium", "hard"):
            for seed in range(50):
                grid = gen.generate(seed, 3 * seed, difficulty=difficulty, scene_family="public")
                self.assertEqual([], gen.self_check(grid))
                self.assertEqual({"scene_family": "public"}, gen.observe_overrides(grid))

    def test_generalized_override_is_exact_and_observed(self):
        for difficulty in ("default", "easy", "medium", "hard"):
            for seed in range(50):
                grid = gen.generate(seed, 5 * seed, difficulty=difficulty, scene_family="generalized")
                self.assertEqual([], gen.self_check(grid))
                self.assertEqual({"scene_family": "generalized"}, gen.observe_overrides(grid))

    def test_natural_prior_reaches_every_public_d4_signature_per_band(self):
        for difficulty in ("easy", "medium", "hard"):
            seen = set()
            public = 0
            for seed in range(5000):
                grid = gen.generate(seed, 13 * seed, difficulty=difficulty)
                facts = gen._analyze(grid)["facts"]
                signature = gen._scene_signature_from_facts(facts)
                if signature in gen._PUBLIC_SIGNATURES:
                    public += 1
                    seen.add(signature)
            self.assertEqual(gen._PUBLIC_SIGNATURES, seen)
            self.assertGreaterEqual(public, 1000)
            self.assertLessEqual(public, 1500)

    def test_finite_8x8_public_profile_uses_all_96_layouts_without_repeats(self):
        grids = []
        for variant in range(96):
            matrix_index, placement_rank = divmod(variant, 12)
            _, profile = gen._PUBLIC_PROFILES[1]
            matrix = gen._D4[matrix_index]
            spec = tuple(
                (
                    gen._transform_vector(direction, matrix),
                    gen._transform_vector(turn, matrix),
                    bar_len,
                    tail_len,
                )
                for direction, turn, bar_len, tail_len in profile
            )[0]
            grid = gen._build_single_motif_ranked(8, 8, spec, placement_rank)
            self.assertEqual([], gen.self_check(grid))
            grids.append(tuple(tuple(row) for row in grid))
        self.assertEqual(96, len(set(grids)))

    def test_finite_10x10_public_profile_has_1400_ranked_layouts(self):
        size, profile = gen._PUBLIC_PROFILES[0]
        grids = set()
        for matrix in gen._D4:
            specs = tuple(
                (
                    gen._transform_vector(direction, matrix),
                    gen._transform_vector(turn, matrix),
                    bar_len,
                    tail_len,
                )
                for direction, turn, bar_len, tail_len in profile
            )
            variants = gen._two_motif_variants(size, size, specs)
            self.assertEqual(175, len(variants))
            grids.update(variants)
        self.assertEqual(1400, len(grids))

    def test_generalized_difficulty_bands_have_exact_envelopes(self):
        expected = {
            "easy": ((8, 12), (1, 3), (0, 4), (1, 3)),
            "medium": ((11, 18), (2, 5), (0, 6), (1, 5)),
            "hard": ((16, 24), (4, 8), (0, 7), (1, 6)),
        }
        for difficulty, (dims, counts, bars, tails) in expected.items():
            seen_dims = set()
            seen_counts = set()
            seen_bars = set()
            seen_tails = set()
            for seed in range(3000):
                grid = gen.generate(seed, 17 * seed, difficulty=difficulty, scene_family="generalized")
                facts = gen._analyze(grid)["facts"]
                seen_dims.update((facts["height"], facts["width"]))
                seen_counts.add(facts["motif_count"])
                seen_bars.update(move["bar_len"] for move in facts["moves"])
                seen_tails.update(move["tail_len"] for move in facts["moves"])
            self.assertEqual(set(range(dims[0], dims[1] + 1)), seen_dims)
            self.assertEqual(set(range(counts[0], counts[1] + 1)), seen_counts)
            self.assertEqual(set(range(bars[0], bars[1] + 1)), seen_bars)
            self.assertEqual(set(range(tails[0], tails[1] + 1)), seen_tails)

    def test_all_directions_and_turns_are_generated(self):
        directions = set()
        turns = set()
        for seed in range(1000):
            grid = gen.generate(seed, 19 * seed, difficulty="hard", scene_family="generalized")
            for move in gen._analyze(grid)["facts"]["moves"]:
                directions.add(move["direction"])
                turns.add(move["turn"])
        self.assertEqual(set(gen._DIRECTIONS), directions)
        self.assertEqual(set(gen._DIRECTIONS), turns)

    def test_odd_center_line_uses_executable_up_left_tie_break(self):
        self.assertEqual((-1, 0), gen._turn_toward_center((0, 1), (5, 3), 11, 9))
        self.assertEqual((0, -1), gen._turn_toward_center((1, 0), (3, 4), 9, 9))

    def test_every_generated_scene_visibly_transforms(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = gen.generate(seed, 23 * seed, difficulty=difficulty)
                self.assertNotEqual(grid, gen.rule_mirror(grid))

    def test_seed_and_sample_index_both_change_generation(self):
        seeds = {tuple(map(tuple, gen.generate(seed, 0, difficulty="medium"))) for seed in range(50)}
        samples = {tuple(map(tuple, gen.generate(0, sample, difficulty="medium"))) for sample in range(50)}
        self.assertGreaterEqual(len(seeds), 45)
        self.assertGreaterEqual(len(samples), 45)

    def test_generation_is_deterministic_and_returns_fresh_grids(self):
        first = gen.generate(91, 17, difficulty="hard")
        snapshot = copy.deepcopy(first)
        second = gen.generate(91, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(snapshot, gen.generate(91, 17, difficulty="hard"))

    def test_generation_preserves_process_global_random_state(self):
        random.seed(123456)
        before = random.getstate()
        gen.generate(1, 2, difficulty="hard")
        self.assertEqual(before, random.getstate())

    def test_checker_and_mirror_are_input_pure(self):
        grid = gen.generate(19, 23, difficulty="medium")
        before = copy.deepcopy(grid)
        gen.self_check(grid)
        gen.rule_mirror(grid)
        self.assertEqual(before, grid)

    def test_unknown_difficulty_and_override_fail_loudly(self):
        with self.assertRaises(ValueError):
            gen.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            gen.generate(0, 0, invented=True)

    def test_checker_rejects_empty_ragged_boolean_and_out_of_range(self):
        self.assertTrue(gen.self_check([]))
        self.assertTrue(gen.self_check([[7, 7], [7]]))
        self.assertTrue(gen.self_check([[True] * 8 for _ in range(8)]))
        self.assertTrue(gen.self_check([[11] * 8 for _ in range(8)]))

    def test_checker_rejects_dimensions_outside_envelope(self):
        grid = gen.generate(8, 9, difficulty="easy", scene_family="generalized")
        while len(grid) > 7:
            grid.pop()
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_missing_endpoint_or_pivot(self):
        grid = gen.generate(3, 4, difficulty="easy", scene_family="generalized")
        endpoint = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == gen.GRAY)
        grid[endpoint[0]][endpoint[1]] = gen.FIELD
        self.assertTrue(gen.self_check(grid))
        grid = gen.generate(3, 4, difficulty="easy", scene_family="generalized")
        pivot = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == gen.PIVOT)
        grid[pivot[0]][pivot[1]] = gen.FIELD
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_stray_red_and_destination_collision(self):
        grid = gen.generate(31, 7, difficulty="easy", scene_family="generalized")
        point = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == gen.FIELD)
        grid[point[0]][point[1]] = gen.RED
        self.assertTrue(gen.self_check(grid))
        grid = gen.generate(32, 8, difficulty="easy", scene_family="generalized")
        move = gen._analyze(grid)["facts"]["moves"][0]
        destination = (move["pivot"][0] + move["turn"][0], move["pivot"][1] + move["turn"][1])
        grid[destination[0]][destination[1]] = gen.GRAY
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_minimal_impostors(self):
        probes = [[[gen.FIELD] * 8 for _ in range(8)]]
        for cells in ({(4, 4)}, {(4, 4), (4, 5)}, {(4, 4), (4, 5), (5, 4), (5, 5)}):
            grid = [[gen.FIELD] * 8 for _ in range(8)]
            for row, col in cells:
                grid[row][col] = gen.RED
            probes.append(grid)
        self.assertTrue(all(gen.self_check(grid) for grid in probes))

    def test_lawful_recombination_is_not_a_complete_public_profile(self):
        size, profile = gen._PUBLIC_PROFILES[0]
        specs = list(profile)
        direction, turn, bar_len, _ = specs[0]
        specs[0] = direction, turn, bar_len, 2
        grid = None
        rng = random.Random(8128)
        for _ in range(50):
            candidate = gen._build_scene(rng, size, size, specs)
            if candidate is not None and not gen.self_check(candidate):
                grid = candidate
                break
        self.assertIsNotNone(grid)
        self.assertEqual("generalized", gen.canonical_profile_signature(grid))

    def test_rule_hash_matches_all_authorities(self):
        row = canonical_row()
        base = json.loads((ROOT / "data/base/solutions/training/230f2e48__02a33ab58da6.json").read_text())
        hashes = [
            normalized_hash(row["program_solution"]),
            normalized_hash(base["racket_target"]["raw_code"]),
            normalized_hash(base["racket_target"]["target_code"]),
            normalized_hash(grounded_rule()),
        ]
        self.assertEqual([gen.RULE_HASH] * 4, hashes)

    def test_base_description_is_substantive(self):
        base = json.loads((ROOT / "data/base/solutions/training/230f2e48__02a33ab58da6.json").read_text())
        description = base["description_target"]
        self.assertGreaterEqual(len(description["solution_steps"]), 5)
        self.assertGreaterEqual(len(description["negative_constraints"]), 5)
        self.assertTrue(description["semantic_primitives"])


if __name__ == "__main__":
    unittest.main()
