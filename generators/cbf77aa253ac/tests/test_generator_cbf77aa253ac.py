from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "cbf77aa253ac"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
BASES = {
    "training": "base/solutions/training/5b692c0f__cbf77aa253ac.json",
    "augmented": "base/solutions/augmented/5b692c0f__389182a9e669.json",
}


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


class GeneratorTests(unittest.TestCase):
    def test_all_six_canonical_occurrences_and_three_public_lessons_exact(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        occurrences = canonical_pairs(TASK, root=ROOT)
        self.assertEqual(len(occurrences), 6)
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in occurrences}), 3)
        for pair in occurrences:
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
        training_variant = next(i for i, row in enumerate(rows) if row["source"] == "training")
        training_pairs = canonical_pairs(TASK, root=ROOT, variant=training_variant)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, training_pairs):
            grid = MOD.generate(17, 31, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 23, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])
                    changed = sum(a != b for row_a, row_b in zip(grid, analysis["output"]) for a, b in zip(row_a, row_b))
                    self.assertGreaterEqual(changed / (len(grid) * len(grid[0])), 0.01)

    def test_profiles_isolate_every_rule_branch(self):
        for seed in range(120):
            analyses = {
                profile: MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile))
                for profile in MOD.GENERAL_PROFILES
            }
            for name in ("horizontal_above_dense", "horizontal_below_dense", "horizontal_tie_above"):
                self.assertTrue(analyses[name]["plans"][0]["horizontal"])
            for name in ("vertical_left_dense", "vertical_right_dense", "vertical_tie_left", "guide_span_tie_vertical"):
                self.assertFalse(analyses[name]["plans"][0]["horizontal"])
            self.assertTrue(analyses["horizontal_above_dense"]["plans"][0]["choose_negative"])
            self.assertFalse(analyses["horizontal_below_dense"]["plans"][0]["choose_negative"])
            self.assertTrue(analyses["vertical_left_dense"]["plans"][0]["choose_negative"])
            self.assertFalse(analyses["vertical_right_dense"]["plans"][0]["choose_negative"])
            for name in ("horizontal_tie_above", "vertical_tie_left"):
                plan = analyses[name]["plans"][0]
                self.assertEqual(plan["negative_count"], plan["positive_count"])
                self.assertTrue(plan["choose_negative"])
            tie = analyses["guide_span_tie_vertical"]["plans"][0]
            self.assertEqual(tie["row_span"], tie["col_span"])
            self.assertFalse(tie["horizontal"])
            rounding = analyses["irregular_guide_rounding"]["plans"][0]
            self.assertFalse(MOD._straight(rounding["guide"]))
            axis_values = [r for r, _ in rounding["guide"]]
            self.assertEqual(rounding["axis"], MOD._avg_round(axis_values))
            self.assertGreater(len(analyses["multicolor_payload"]["plans"][0]["payload_colors"]), 1)
            axis_plan = analyses["payload_on_axis"]["plans"][0]
            self.assertTrue(any(r == axis_plan["axis"] for r, _ in axis_plan["payload"]))
            self.assertTrue(analyses["clipped_reflection"]["clipped"])
            self.assertEqual(len(analyses["unaffected_decoys"]["ignored_components"]), 2)
            self.assertEqual(len(analyses["multiple_components"]["plans"]), 2)

    def test_exact_clear_restore_reflect_and_unaffected_components(self):
        grid = [[0] * 11 for _ in range(10)]
        cells = {
            (4, 2, 4), (4, 3, 4), (4, 4, 4), (4, 5, 4), (4, 6, 4),
            (3, 3, 7), (2, 3, 7), (3, 4, 7), (5, 5, 7), (6, 5, 9),
        }
        for row, col, value in cells:
            grid[row][col] = value
        grid[0][9] = 4
        grid[0][10] = 4
        grid[9][9] = 2
        grid[9][10] = 2
        before = [row[:] for row in grid]
        output = MOD.rule_mirror(grid)
        self.assertEqual(grid, before)
        expected = [row[:] for row in grid]
        for row, col, value in cells:
            if value != 4:
                expected[row][col] = 0
        for row, col in ((2, 3), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6)):
            value = grid[row][col]
            expected[row][col] = value
            expected[8 - row][col] = value
        self.assertEqual(output, expected)
        self.assertEqual(output[0][9:], [4, 4])
        self.assertEqual(output[9][9:], [2, 2])

    def test_distribution_and_freshness(self):
        profiles = Counter()
        inputs, outputs, shapes, colors = set(), set(), set(), set()
        axes, guide_sizes, payload_sizes = set(), set(), set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 37, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            colors.update(value for row in grid for value in row)
            for plan in analysis["plans"]:
                axes.add(plan["axis"])
                guide_sizes.add(len(plan["guide"]))
                payload_sizes.add(len(plan["payload"]))
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2300)
        self.assertGreater(len(outputs), 2200)
        self.assertGreater(len(shapes), 110)
        self.assertEqual(colors, set(range(10)))
        self.assertGreater(len(axes), 20)
        self.assertGreaterEqual(len(guide_sizes), 6)
        self.assertGreaterEqual(len(payload_sizes), 6)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)]]
        guide_only = [[0] * 8 for _ in range(8)]
        guide_only[2][2:5] = [4, 4, 4]
        cases.append(guide_only)
        too_small = [[0] * 8 for _ in range(8)]
        too_small[2][2:4] = [4, 4]
        too_small[3][2] = 7
        cases.append(too_small)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknown_overrides_and_global_rng_purity(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "noise"}, {"palette_size": 4}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(109)
        state = random.getstate()
        first = MOD.generate(13, 19, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(13, 19, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_both_base_sources_are_exactly_synced(self):
        rows = canonical_rows()
        sources = {row["source"]: row["program_solution"] for row in rows}
        self.assertEqual(len(set(sources.values())), 1)
        source = next(iter(sources.values()))
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        for source_name, relative in BASES.items():
            base = json.loads((canonical_path(ROOT).parent.parent / relative).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], sources[source_name])
            self.assertEqual(base["racket_target"]["target_code"], sources[source_name])


if __name__ == "__main__":
    unittest.main()
