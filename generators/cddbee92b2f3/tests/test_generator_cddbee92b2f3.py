from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "cddbee92b2f3"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
BASE = "shared/data/base/solutions/banks/cc07013acae1/E70__cddbee92b2f3.json"


def canonical_row():
    return next(
        row
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK
    )


def public_pairs():
    row = canonical_row()
    test = row["test"]
    pairs = row["train"] + ([test] if isinstance(test, dict) else test)
    return [
        {
            "input": [[int(value) for value in line] for line in pair["input"]] if pair["input"] and isinstance(pair["input"][0], str) else pair["input"],
            "output": [[int(value) for value in line] for line in pair["output"]] if pair["output"] and isinstance(pair["output"][0], str) else pair["output"],
        }
        for pair in pairs
    ]


class GeneratorTests(unittest.TestCase):
    def test_all_public_pairs_exact(self):
        pairs = public_pairs()
        self.assertEqual(len(pairs), 5)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs):
            grid = MOD.generate(17, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
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
                    self.assertGreaterEqual(analysis["changed"] / (len(grid) * len(grid[0])), 0.01)

    def test_profiles_witness_every_selection_and_write_branch(self):
        for seed in range(100):
            grids = {profile: MOD.generate(seed, seed * 7, scene_profile=profile) for profile in MOD.GENERAL_PROFILES}
            analyses = {profile: MOD._analysis(grid) for profile, grid in grids.items()}
            self.assertNotEqual(analyses["offset_axis"]["guide_col"], len(analyses["offset_axis"]["output"][0]) // 2)
            self.assertGreaterEqual(len({grids["multicolor_pattern"][r][c] for r, c in analyses["multicolor_pattern"]["sources"]}), 5)
            clustered = analyses["clustered_shape"]["sources"]
            self.assertTrue(any(abs(r - rr) + abs(c - cc) == 1 for r, c in clustered for rr, cc in clustered if (r, c) != (rr, cc)))
            edge = analyses["edge_rows"]
            self.assertTrue({0, len(edge["output"]) - 1}.issubset({r for r, _ in edge["sources"]}))
            preserved_grid = grids["existing_right_preserved"]
            preserved = analyses["existing_right_preserved"]
            right = {(r, c) for r, row in enumerate(preserved_grid) for c, value in enumerate(row) if c > preserved["guide_col"] and value != 0 and c not in preserved["guides"]}
            self.assertTrue(right)
            self.assertTrue(right.isdisjoint(preserved["targets"]))
            overwritten_grid = grids["existing_right_overwritten"]
            overwritten = analyses["existing_right_overwritten"]
            occupied_targets = {(r, c) for r, c in overwritten["targets"] if overwritten_grid[r][c] != 0}
            self.assertTrue(occupied_targets)
            self.assertTrue(any(overwritten_grid[r][c] != overwritten["output"][r][c] for r, c in occupied_targets))
            self.assertTrue(analyses["out_of_bounds_sources"]["out_of_bounds_sources"])
            self.assertEqual(len(analyses["multiple_guides_first"]["guides"]), 2)
            literal = grids["literal_five_ignored"]
            literal_analysis = analyses["literal_five_ignored"]
            self.assertTrue(any(literal[r][c] == 5 for r in range(len(literal)) for c in range(literal_analysis["guide_col"])))
            self.assertGreaterEqual(len({literal_analysis["guide_col"] - c for _, c in analyses["near_and_far_sources"]["sources"]}), 3)
            self.assertGreaterEqual(len(analyses["dense_pattern"]["sources"]), 10)

    def test_exact_first_guide_preservation_overwrite_clipping_and_five_filter(self):
        grid = [[0] * 13 for _ in range(7)]
        for row in range(7):
            grid[row][4] = 5
            grid[row][8] = 5
        grid[1][0] = 2
        grid[2][1] = 3
        grid[3][2] = 4
        grid[4][3] = 6
        grid[5][2] = 5
        grid[6][11] = 9
        before = [row[:] for row in grid]
        output = MOD.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[1][8], 2)
        self.assertEqual(output[2][7], 3)
        self.assertEqual(output[3][6], 4)
        self.assertEqual(output[4][5], 6)
        self.assertEqual(output[5][6], 0)
        self.assertEqual(output[6][11], 9)
        self.assertTrue(all(output[row][4] == 5 for row in range(7)))

        no_guide = [[0, 2, 0], [3, 0, 4]]
        self.assertEqual(MOD.rule_mirror(no_guide), no_guide)
        self.assertTrue(MOD.self_check(no_guide))

    def test_distribution(self):
        profiles = Counter()
        inputs, outputs, shapes, axes, source_counts = set(), set(), set(), set(), set()
        colors = set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            axes.add(analysis["guide_col"])
            source_counts.add(len(analysis["sources"]))
            colors.update(value for row in grid for value in row)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2350)
        self.assertGreater(len(outputs), 2350)
        self.assertGreater(len(shapes), 100)
        self.assertEqual(colors, set(range(10)))
        self.assertGreater(len(axes), 8)
        self.assertGreater(len(source_counts), 7)

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)]]
        guide_only = [[0] * 8 for _ in range(8)]
        for row in range(8):
            guide_only[row][4] = 5
        cases.append(guide_only)
        too_few = [row[:] for row in guide_only]
        too_few[1][3] = 2
        too_few[3][2] = 3
        cases.append(too_few)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "noise"}, {"grid_h": 10}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(83)
        state = random.getstate()
        first = MOD.generate(4, 5, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(4, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_source_hash_and_base_sync(self):
        source = canonical_row()["program_solution"]
        expected_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, expected_hash)
        base = json.loads((ROOT / BASE).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
