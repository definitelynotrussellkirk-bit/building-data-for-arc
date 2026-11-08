"""Focused semantic regressions for generator 6fde852adb54."""
from __future__ import annotations
from reviewer_support import find_root as _arc_review_root0, canonical_path as _arc_review_canonical0, load_selected_generator as _arc_review_generator0

import ast
import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path


ROOT = _arc_review_root0(__file__)
TASK_ID = "6fde852adb54"
TASK_ROOT = ROOT / "generators" / TASK_ID
gen = _arc_review_generator0(TASK_ID, root=ROOT)[0]


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    return next(
        json.loads(line)
        for line in (_arc_review_canonical0(_arc_review_root0(__file__))).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def grounded_rule() -> str:
    tree = ast.parse((ROOT / "solvers/grounded_rules.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == TASK_ID:
                return ast.literal_eval(value)
    raise AssertionError("grounded rule not found")


def event_types(grid):
    facts = gen._parse(grid)["facts"]
    result = []
    for col, is_tip in zip(facts["mover_cols"], facts["tip_mask"]):
        hits = [
            row for row in range(3, facts["height"])
            if grid[row][col] == facts["obstacle"]
        ]
        if is_tip:
            result.append("tip_stop" if hits else "tip_floor")
        elif hits and hits[-1] >= facts["height"] - 2:
            component = next(
                cells for cells in facts["obstacle_components"]
                if (hits[-1], col) in cells
            )
            counts = Counter(cell_col for _, cell_col in component)
            result.append("body_line" if set(counts.values()) == {1} else "body_blob")
        else:
            result.append("body_floor")
    return tuple(result)


class ColumnGravityGeneratorTests(unittest.TestCase):
    def test_version_hash_and_axes_are_current(self):
        self.assertEqual("4.0.0", gen.VERSION)
        self.assertEqual("4a2e9b9f15bf", gen.RULE_HASH)
        self.assertEqual({"scene_family"}, set(gen.AXES))

    def test_all_canonical_pairs_pass_checker_and_python_oracle(self):
        row = canonical_row()
        for pair in row["train"] + row["test"]:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_all_canonical_inputs_have_exact_public_signature(self):
        row = canonical_row()
        signatures = {
            gen.canonical_profile_signature(pair["input"])
            for pair in row["train"] + row["test"]
        }
        self.assertEqual({"public_exact"}, signatures)

    def test_compact_public_catalog_reconstructs_canonical_inputs(self):
        expected = [pair["input"] for pair in canonical_row()["train"] + canonical_row()["test"]]
        actual = [
            gen._draw_public(index, False, gen._EXACT_ROLES)
            for index in range(len(gen._PUBLIC_SCENES))
        ]
        self.assertEqual(expected, actual)

    def test_public_horizontal_reflections_are_lawful(self):
        for index in range(len(gen._PUBLIC_SCENES)):
            grid = gen._draw_public(index, True, gen._EXACT_ROLES)
            self.assertEqual([], gen.self_check(grid))
            self.assertNotEqual(grid, gen.rule_mirror(grid))

    def test_public_override_is_exact_and_observed(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(20):
                grid = gen.generate(seed, 3 * seed, difficulty=difficulty, scene_family="public")
                self.assertEqual("public", gen.observe_overrides(grid)["scene_family"])

    def test_generalized_override_is_exact_and_observed(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(20):
                grid = gen.generate(seed, 5 * seed, difficulty=difficulty, scene_family="generalized")
                self.assertEqual("generalized", gen.observe_overrides(grid)["scene_family"])

    def test_unknown_difficulty_and_override_fail_loudly(self):
        self.assertEqual([], gen.self_check(gen.generate(0, 0, difficulty="default")))
        with self.assertRaises(ValueError):
            gen.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            gen.generate(0, 0, invented=True)

    def test_seed_and_sample_index_both_change_generation(self):
        seed_stream = {
            tuple(map(tuple, gen.generate(seed, 0, difficulty="medium")))
            for seed in range(50)
        }
        sample_stream = {
            tuple(map(tuple, gen.generate(0, sample, difficulty="medium")))
            for sample in range(50)
        }
        self.assertGreaterEqual(len(seed_stream), 45)
        self.assertGreaterEqual(len(sample_stream), 45)

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

    def test_checker_and_oracle_are_input_pure(self):
        grid = gen.generate(19, 23, difficulty="medium")
        before = copy.deepcopy(grid)
        gen.self_check(grid)
        self.assertEqual(before, grid)
        gen.rule_mirror(grid)
        self.assertEqual(before, grid)

    def test_normal_stream_keeps_substantial_public_prior(self):
        for difficulty in ("easy", "medium", "hard"):
            counts = Counter(
                gen.observe_overrides(gen.generate(seed, 17 * seed, difficulty=difficulty))["scene_family"]
                for seed in range(1000)
            )
            self.assertGreaterEqual(counts["public"], 180)
            self.assertLessEqual(counts["public"], 320)

    def test_exact_color_public_prior_clears_five_percent_floor(self):
        for difficulty in ("easy", "medium", "hard"):
            exact = sum(
                gen.canonical_profile_signature(gen.generate(900_000 + seed, 17 * seed, difficulty=difficulty))
                == "public_exact"
                for seed in range(2000)
            )
            self.assertGreaterEqual(exact, 100)

    def test_every_public_profile_is_reached_in_every_band(self):
        expected = {
            gen._role_normalized(gen._draw_public(index, reflected, gen._EXACT_ROLES))
            for index in range(4)
            for reflected in (False, True)
        }
        for difficulty in ("easy", "medium", "hard"):
            seen = set()
            for seed in range(5000):
                grid = gen.generate(seed, 13 * seed, difficulty=difficulty)
                if gen.observe_overrides(grid)["scene_family"] == "public":
                    seen.add(gen._role_normalized(grid))
            self.assertEqual(expected, seen)

    def test_generalized_dimension_bands_are_distinct(self):
        ranges = {
            "easy": (14, 16),
            "medium": (16, 20),
            "hard": (20, 24),
        }
        for difficulty, (minimum, maximum) in ranges.items():
            dimensions = set()
            for seed in range(500):
                grid = gen.generate(seed, seed, difficulty=difficulty, scene_family="generalized")
                dimensions.add((len(grid), len(grid[0])))
            self.assertTrue(all(minimum <= h <= maximum and minimum <= w <= maximum for h, w in dimensions))
            self.assertIn((minimum, minimum), dimensions)
            self.assertIn((maximum, maximum), dimensions)

    def test_all_five_landing_event_types_are_generated(self):
        seen = set()
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(1000):
                grid = gen.generate(seed, 19 * seed, difficulty=difficulty)
                seen.update(event_types(grid))
        self.assertEqual({"tip_stop", "tip_floor", "body_floor", "body_line", "body_blob"}, seen)

    def test_all_tip_masks_are_generated(self):
        seen = set()
        for seed in range(3000):
            grid = gen.generate(seed, 11 * seed, difficulty="hard", scene_family="generalized")
            seen.add(gen._parse(grid)["facts"]["tip_mask"])
        self.assertEqual(set(gen._TIP_MASKS["hard"]), seen)

    def test_every_generated_output_changes(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = gen.generate(seed, 7 * seed, difficulty=difficulty)
                self.assertNotEqual(grid, gen.rule_mirror(grid))

    def test_checker_rejects_empty_ragged_boolean_and_out_of_range(self):
        self.assertTrue(gen.self_check([]))
        self.assertTrue(gen.self_check([[7, 7], [7]]))
        self.assertTrue(gen.self_check([[True] * 14 for _ in range(14)]))
        self.assertTrue(gen.self_check([[11] * 14 for _ in range(14)]))

    def test_checker_rejects_dimensions_outside_envelope(self):
        grid = gen.generate(8, 9, difficulty="easy", scene_family="generalized")
        self.assertTrue(gen.self_check(grid[:-1] if len(grid) == 14 else grid[:13]))

    def test_checker_rejects_noncontiguous_top_mover(self):
        grid = gen._draw_public(0, False, gen._EXACT_ROLES)
        grid[0][14] = 7
        grid[0][12] = 9
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_missing_tip(self):
        grid = gen._draw_public(1, False, gen._EXACT_ROLES)
        for col in range(5, 8):
            grid[2][col] = 9
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_extra_body_or_tip_cells(self):
        grid = gen._draw_public(1, False, gen._EXACT_ROLES)
        grid[4][0] = 9
        self.assertTrue(gen.self_check(grid))
        grid = gen._draw_public(1, False, gen._EXACT_ROLES)
        grid[4][0] = 1
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_too_close_tip_stopper(self):
        grid = gen._draw_public(1, False, gen._EXACT_ROLES)
        grid[3][6] = 5
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_three_color_and_obstacle_free_impostors(self):
        grid = gen._draw_public(1, False, gen._EXACT_ROLES)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 5:
                    grid[row][col] = 7
        self.assertTrue(gen.self_check(grid))

    def test_checker_rejects_minimal_impostors(self):
        background = 7
        probes = []
        probes.append([[background] * 14 for _ in range(14)])
        for cells in ({(7, 7)}, {(7, 7), (7, 8)}, {(7, 7), (7, 8), (8, 7), (8, 8)}):
            grid = [[background] * 14 for _ in range(14)]
            for row, col in cells:
                grid[row][col] = 5
            probes.append(grid)
        self.assertTrue(all(gen.self_check(grid) for grid in probes))

    def test_role_normalization_is_palette_invariant(self):
        first = gen._draw_public(2, True, gen._EXACT_ROLES)
        second = gen._draw_public(2, True, (0, 2, 4, 8))
        self.assertEqual(gen._role_normalized(first), gen._role_normalized(second))

    def test_canonical_near_miss_recombination_is_not_public(self):
        grid = gen._draw_public(0, False, gen._EXACT_ROLES)
        facts = gen._parse(grid)["facts"]
        for col, is_tip in zip(facts["mover_cols"], (0, 0, 1)):
            grid[2][col] = 1 if is_tip else 9
        self.assertEqual([], gen.self_check(grid))
        self.assertEqual("generalized", gen.canonical_profile_signature(grid))

    def test_rule_hash_matches_portable_authorities(self):
        """Bind the selected canonical rule to task-local retained source.

        Copied task-test snapshots deliberately omit the repository-wide base
        solution and grounded-rule trees, so this check uses only authorities
        guaranteed to travel with the task and its selected runtime.
        """
        canonical = canonical_row()["program_solution"]
        retained = (TASK_ROOT / "workspace/parametric/canonical.rkt").read_text()
        self.assertEqual(canonical, retained)
        self.assertEqual(gen.RULE_HASH, normalized_hash(canonical))
        self.assertEqual(gen.RULE_HASH, normalized_hash(retained))

    def test_source_local_description_is_substantive(self):
        description = "\n".join((gen.__doc__ or "", gen.SUMMARY, *gen.INVARIANTS))
        self.assertIn("independently", description)
        self.assertIn("bottom", description)
        self.assertIn("component", description)
        self.assertGreaterEqual(len(gen.INVARIANTS), 5)

    def test_source_local_rule_explanation_is_present(self):
        description = "\n".join((gen.__doc__ or "", gen.SUMMARY))
        self.assertIn("independently", description)
        self.assertIn("bottom", description)
        self.assertIn("component", description)


if __name__ == "__main__":
    unittest.main()
