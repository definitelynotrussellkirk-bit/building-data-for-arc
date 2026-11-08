"""Focused semantic regressions for generator 5751ed9bdf85."""
from __future__ import annotations

import copy
import importlib
import random
import unittest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "5751ed9bdf85"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


class Generator5751ed9bdf85Tests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual(MODULE.RULE_HASH, canonical_rule_hash(TASK_ID))
        pairs = canonical_pairs(TASK_ID)
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.strict_canonical_like(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)

    def test_four_slot_schedule_kills_every_named_rival_from_every_start(self):
        period = len(MODULE.SCHEDULE_PROFILES)
        self.assertEqual(MODULE.EXAMPLES_NEEDED, period)
        for band in ("easy", "medium", "hard"):
            for start in range(period):
                demos = []
                for offset in range(MODULE.EXAMPLES_NEEDED):
                    sample_index = start + offset
                    grid = MODULE.generate(1000 + start, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                query_grid = MODULE.generate(2000 + start, start + period, difficulty=band)
                query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
                self.assertEqual(MODULE.lesson_identifiable(demos, query), [])
                for name, rival in MODULE.LESSON_COMPETITORS.items():
                    self.assertTrue(
                        any(rival(pair["input"]) != pair["output"] for pair in demos),
                        f"{band=} {start=} rival {name!r} survived",
                    )

    def test_generated_roles_and_semantic_witnesses(self):
        pooled = {name: 0 for name in MODULE.SEMANTIC_WITNESSES}
        role_profiles = set()
        for band in ("easy", "medium", "hard"):
            for sample_index in range(40):
                grid = MODULE.generate(700 + sample_index, sample_index, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                facts = MODULE._generated_role_facts(grid)
                self.assertIsNotNone(facts)
                self.assertIn(facts["marker_counts"], ([0, 1, 2], [0, 1, 3]))
                role_profiles.add(tuple(facts["marker_counts"]))
                for name, witness in MODULE.SEMANTIC_WITNESSES.items():
                    pooled[name] += int(witness(grid))
        self.assertEqual(role_profiles, {(0, 1, 2), (0, 1, 3)})
        self.assertTrue(all(count > 0 for count in pooled.values()), pooled)

    def test_exact_overrides_round_trip_at_boundaries(self):
        cases = (
            {
                "grid_h": 10,
                "grid_w": 12,
                "target_slot": "top_left",
                "target_size_rank": "smallest",
                "decoy_color_relation": "distinct",
                "decoy_marker_count": 2,
                "target_color": 1,
            },
            {
                "grid_h": 18,
                "grid_w": 22,
                "target_slot": "bottom",
                "target_size_rank": "largest",
                "decoy_color_relation": "same_as_target",
                "decoy_marker_count": 3,
                "target_color": 9,
            },
            {
                "grid_h": 10,
                "grid_w": 22,
                "target_slot": "top_right",
                "target_size_rank": "middle",
                "decoy_color_relation": "distinct",
                "decoy_marker_count": 3,
                "target_color": 4,
            },
        )
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = MODULE.generate(91 + index, index, difficulty=band, **overrides)
                self.assertEqual(MODULE.observe_overrides(grid), overrides)
                self.assertEqual(
                    MODULE.self_check(grid, difficulty=band, meta={"overrides": overrides}),
                    [],
                )

    def test_unknown_and_invalid_overrides_fail_loudly(self):
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, __override_contract_unknown_axis__=1)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, grid_h=9)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, grid_w=23)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, target_slot="center")
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, target_size_rank="huge")
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, decoy_color_relation="mixed")
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, decoy_marker_count=1)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, decoy_marker_count=4)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, target_color=5)
        with self.assertRaises(ValueError):
            MODULE.generate(0, 0, difficulty="extreme")

    def test_self_check_rejects_targeted_impostors(self):
        grid = MODULE.generate(17, 0, difficulty="medium")
        facts = MODULE._generated_role_facts(grid)
        target = facts["target"]
        decoy = facts["decoy"]

        no_target = copy.deepcopy(grid)
        row, col, _ = target["marker_cells"][0]
        no_target[row][col] = 0

        second_singleton = copy.deepcopy(grid)
        row, col, _ = decoy["marker_cells"][0]
        second_singleton[row][col] = 0

        broken_frame = copy.deepcopy(grid)
        row0, col0, _, _ = target["bbox"]
        broken_frame[row0][col0] = 0

        stray_marker = copy.deepcopy(grid)
        placed = False
        for row in range(len(stray_marker)):
            for col in range(len(stray_marker[0])):
                if stray_marker[row][col] != 0:
                    continue
                inside = False
                for frame in MODULE._analyze_scene(grid)["frames"]:
                    r0, c0, r1, c1 = frame["bbox"]
                    if r0 < row < r1 and c0 < col < c1:
                        inside = True
                        break
                if not inside:
                    stray_marker[row][col] = 9
                    placed = True
                    break
            if placed:
                break
        self.assertTrue(placed)

        for impostor in (no_target, second_singleton, broken_frame, stray_marker):
            self.assertTrue(MODULE.self_check(impostor), impostor)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(20260815)
        state = random.getstate()
        first = MODULE.generate(12345, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(12345, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        snapshot = copy.deepcopy(first)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(snapshot, MODULE.generate(12345, 17, difficulty="hard"))


    def test_odd_marker_shortcut_fits_canonicals_but_each_lesson_window_refutes_it(self):
        odd_marker_rival = MODULE.CANONICAL_SHORTCUTS["odd_marker_count"]
        for pair in canonical_pairs(TASK_ID):
            self.assertEqual(odd_marker_rival(pair["input"]), pair["output"])

        period = len(MODULE.SCHEDULE_PROFILES)
        for band in ("easy", "medium", "hard"):
            for start in range(period):
                demos = []
                marker_counts = []
                disagreements = 0
                for offset in range(MODULE.EXAMPLES_NEEDED):
                    sample_index = start + offset
                    grid = MODULE.generate(3000 + start, sample_index, difficulty=band)
                    expected = MODULE.rule_mirror(grid)
                    demos.append({"input": grid, "output": expected})
                    marker_counts.append(MODULE.observe_overrides(grid)["decoy_marker_count"])
                    disagreements += int(odd_marker_rival(grid) != expected)
                self.assertIn(3, marker_counts, (band, start, marker_counts))
                self.assertGreater(disagreements, 0, (band, start))
                self.assertTrue(
                    any(
                        MODULE.SEMANTIC_WITNESSES[
                            "three_marker_decoy_refutes_odd_count"
                        ](pair["input"])
                        for pair in demos
                    )
                )

    def test_three_marker_decoy_always_leaves_a_fillable_zero(self):
        for band in ("easy", "medium", "hard"):
            for target_slot in MODULE.TARGET_SLOTS:
                for target_size_rank in MODULE.TARGET_SIZE_RANKS:
                    for seed in range(8):
                        grid = MODULE.generate(
                            seed,
                            seed,
                            difficulty=band,
                            target_slot=target_slot,
                            target_size_rank=target_size_rank,
                            decoy_marker_count=3,
                        )
                        facts = MODULE._generated_role_facts(grid)
                        self.assertIsNotNone(facts)
                        self.assertGreater(
                            facts["decoy"]["interior_area"],
                            facts["decoy"]["marker_count"],
                            (band, target_slot, target_size_rank, seed, facts),
                        )
                        self.assertTrue(
                            MODULE.SEMANTIC_WITNESSES[
                                "three_marker_decoy_refutes_odd_count"
                            ](grid),
                            (band, target_slot, target_size_rank, seed),
                        )

    def test_shared_color_profile_refutes_global_color_frequency_shortcut(self):
        grid = MODULE.generate(314, 1, difficulty="medium")
        observed = MODULE.observe_overrides(grid)
        self.assertEqual(observed["decoy_color_relation"], "same_as_target")
        self.assertNotEqual(
            MODULE.CANONICAL_SHORTCUTS["global_unique_marker_color"](grid),
            MODULE.rule_mirror(grid),
        )


if __name__ == "__main__":
    unittest.main()
