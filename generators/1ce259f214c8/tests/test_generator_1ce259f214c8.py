"""Focused regressions for the XOR-panels generator repair."""
from __future__ import annotations

import importlib
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.1ce259f214c8.generator"
)


def canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise AssertionError("canonical task missing")


def canonical_inputs():
    return [pair["input"] for pair in canonical_pairs()]


class XorPanelsGeneratorTests(unittest.TestCase):
    def test_rule_hash_is_pinned(self):
        self.assertEqual("8b24eb18c704", GEN.RULE_HASH)

    def test_every_canonical_input_is_accepted_and_has_all_relations(self):
        for grid in canonical_inputs():
            self.assertEqual([], GEN.self_check(grid))
            facts = GEN.analyze_scene(grid)["facts"]
            self.assertGreater(facts["overlap"], 0)
            self.assertGreater(facts["left_only"], 0)
            self.assertGreater(facts["right_only"], 0)

    def test_color_axis_contract_matches_the_runtime_exclusions(self):
        self.assertEqual("1..9 (≠5)", GEN.AXES["left_color"]["valid"])
        self.assertEqual("1..9 (≠5)", GEN.AXES["right_color"]["valid"])
        expected = [
            {"left_color": color, "right_color": color}
            for color in (1, 2, 3, 4, 6, 7, 8, 9)
        ]
        self.assertEqual(expected, GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS)

    def test_all_declared_boundary_overrides_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            grid = GEN.generate(
                17,
                23,
                difficulty=band,
                grid_h=9,
                half_w=8,
                left_color=1,
                right_color=9,
            )
            self.assertEqual(
                {"grid_h": 9, "half_w": 8, "left_color": 1, "right_color": 9},
                GEN.observe_overrides(grid),
            )
        with self.assertRaises(ValueError):
            GEN.generate(0, 0, grid_h=3)
        with self.assertRaises(ValueError):
            GEN.generate(0, 0, left_color=4, right_color=4)
        with self.assertRaises(ValueError):
            GEN.generate(0, 0, texture="varied")

    def test_ordinary_draws_always_disambiguate_global_boolean_rules(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = GEN.generate(seed, seed * 13 + 7, difficulty=band)
                self.assertEqual([], GEN.self_check(grid))
                facts = GEN.analyze_scene(grid)["facts"]
                self.assertTrue(
                    all(
                        facts[key] > 0
                        for key in ("overlap", "left_only", "right_only")
                    )
                )

    def test_canonical_geometry_prior_is_present_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            hits = 0
            for seed in range(240):
                facts = GEN.analyze_scene(
                    GEN.generate(seed, 0, difficulty=band)
                )["facts"]
                hits += bool(facts["inset_canonical_geometry"])
            self.assertGreaterEqual(hits, 55, (band, hits))

    def test_schedule_is_one_third_canonical_and_every_five_slots_cover_three_corner_phases(self):
        self.assertEqual(("canonical", "generalized"), GEN.SCHEDULE_PROFILES)
        self.assertEqual(5, GEN.EXAMPLES_NEEDED)
        for band in ("easy", "medium", "hard"):
            for seed in (0, 1, 17, 99991):
                profiles = [
                    GEN.schedule_profile(seed, index, difficulty=band)
                    for index in range(18)
                ]
                phases = [
                    GEN.schedule_corner_phase(seed, index, difficulty=band)
                    for index in range(18)
                ]
                self.assertEqual(6, profiles.count("canonical"), (band, seed, profiles))
                self.assertEqual(12, profiles.count("generalized"), (band, seed, profiles))
                for index, (profile, phase) in enumerate(zip(profiles, phases)):
                    self.assertEqual(profile == "generalized", phase in (0, 1, 2), (index, profile, phase))
                for start in range(18):
                    window_profiles = [profiles[(start + offset) % 18] for offset in range(5)]
                    window_phases = [phases[(start + offset) % 18] for offset in range(5)]
                    self.assertLessEqual(window_profiles.count("canonical"), 2)
                    self.assertEqual(
                        {0, 1, 2},
                        {phase for phase in window_phases if phase is not None},
                        (band, seed, start, window_profiles, window_phases),
                    )

    def test_scheduled_generalized_draws_realize_their_corner_relation_phase(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(12):
                for sample_index in range(18):
                    profile = GEN.schedule_profile(seed, sample_index, difficulty=band)
                    phase = GEN.schedule_corner_phase(seed, sample_index, difficulty=band)
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    facts = GEN.analyze_scene(grid)["facts"]
                    if profile == "canonical":
                        self.assertIsNone(phase)
                        self.assertTrue(facts["inset_canonical_geometry"])
                        self.assertEqual(0, facts["border_xor"])
                    else:
                        self.assertIn(phase, (0, 1, 2))
                        self.assertEqual(
                            list(GEN.CORNER_RELATION_PHASES[phase]),
                            facts["corner_relations"],
                        )

    def test_all_regional_shortcuts_fit_every_canonical_pair(self):
        self.assertEqual(70, len(GEN.REGIONAL_LESSON_COMPETITORS))
        for name, rival in GEN.REGIONAL_LESSON_COMPETITORS.items():
            for pair in canonical_pairs():
                self.assertEqual(pair["output"], rival(pair["input"]), name)

    def test_any_five_consecutive_draws_refute_all_declared_lesson_competitors(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(12):
                for start in range(18):
                    demos = []
                    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                        grid = GEN.generate(seed, sample_index, difficulty=band)
                        demos.append({"input": grid, "output": GEN._xor_output(grid)})
                    query_grid = GEN.generate(
                        seed, start + GEN.EXAMPLES_NEEDED, difficulty=band
                    )
                    query = {
                        "input": query_grid,
                        "output": GEN._xor_output(query_grid),
                    }
                    self.assertEqual([], GEN.lesson_identifiable(demos, query))
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        self.assertTrue(
                            any(
                                rival(pair["input"]) != pair["output"]
                                for pair in demos
                            ),
                            (band, seed, start, name),
                        )

    def test_empty_border_shortcut_fits_every_canonical_pair(self):
        rival = GEN.CANONICAL_SHORTCUTS["empty_output_border"]
        for pair in canonical_pairs():
            self.assertEqual(pair["output"], rival(pair["input"]))

    def test_self_check_rejects_targeted_near_misses(self):
        control = GEN.generate(
            1,
            2,
            grid_h=5,
            half_w=5,
            left_color=2,
            right_color=3,
        )
        self.assertEqual([], GEN.self_check(control))
        half = 5

        missing_divider = [row[:] for row in control]
        missing_divider[0][half] = 0

        disconnected = [row[:] for row in control]
        left_color = GEN.analyze_scene(control)["facts"]["left_color"]
        for r in range(5):
            for c in range(5):
                if disconnected[r][c] == 0 and all(
                    abs(r - rr) + abs(c - cc) > 1
                    for rr in range(5)
                    for cc in range(5)
                    if disconnected[rr][cc] == left_color
                ):
                    disconnected[r][c] = left_color
                    break
            else:
                continue
            break

        same_colors = [row[:] for row in control]
        right_color = GEN.analyze_scene(control)["facts"]["right_color"]
        for r in range(5):
            for c in range(half + 1, 11):
                if same_colors[r][c] == right_color:
                    same_colors[r][c] = left_color

        no_overlap = [[0] * 11 for _ in range(5)]
        for r in range(5):
            no_overlap[r][5] = 5
        no_overlap[1][1] = no_overlap[1][2] = 2
        no_overlap[2][2] = 2
        no_overlap[3][2] = 2
        no_overlap[1][9] = no_overlap[1][10] = 3
        no_overlap[2][9] = 3
        no_overlap[3][9] = 3

        for bad in (missing_divider, disconnected, same_colors, no_overlap):
            self.assertTrue(GEN.self_check(bad))

    def test_deterministic_fresh_returns_and_global_rng_preservation(self):
        random.seed(12345)
        before = random.getstate()
        a = GEN.generate(99, 7, difficulty="hard")
        after = random.getstate()
        b = GEN.generate(99, 7, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(a, b)
        self.assertIsNot(a, b)
        self.assertIsNot(a[0], b[0])
        a[0][0] = 9 if a[0][0] != 9 else 8
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
