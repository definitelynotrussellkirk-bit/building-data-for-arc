from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "a61246736c26"
ROOT = find_root(__file__)
MOD, _SOURCE_PATH, _SOURCE_HASH = load_selected_generator(TASK, root=ROOT)
BASE = "data/base/solutions/training/15660dd6__a61246736c26.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def pairs():
    row = canonical_row()
    return row["train"] + row["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        self.assertEqual(len(pairs()), 3)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)
            self.assertIsNot(generated, MOD._PUBLIC_INPUTS[profile])

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_recolor_semantics_and_output_shape(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(30):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                analysis = MOD._analysis(grid)
                parsed = MOD._source_parse(grid)
                output = analysis["output"]
                size = analysis["tile_size"]
                columns = analysis["column_count"]
                self.assertEqual((len(output), len(output[0])), (size, columns * size + columns - 1))
                for col_index, solid_row in enumerate(analysis["solid_rows"]):
                    solid = parsed["cores"][solid_row][col_index]
                    fill = MOD._solid_color(solid, size)
                    pattern = next(tile[col_index] for tile in parsed["cores"] if MOD._is_pattern(tile[col_index]))
                    start = col_index * (size + 1)
                    frame = analysis["row_colors"][solid_row]
                    for row in range(size):
                        for col in range(size):
                            value = pattern[row][col]
                            expected = frame if value == 1 else fill if value == 2 else value
                            self.assertEqual(output[row][start + col], expected)
                    if col_index + 1 < columns:
                        self.assertTrue(all(output[row][start + size] == 8 for row in range(size)))

    def test_zero_frame_and_permuted_frame_profiles(self):
        zero = MOD._analysis(MOD.generate(7, 11, scene_profile="zero_frame_all"))
        self.assertEqual(zero["solid_rows"], (2, 2, 2))
        self.assertEqual(zero["row_colors"][2], 0)
        self.assertTrue(all(value in (0, 3, 4, 6, 7, 8) for row in zero["output"] for value in row))
        for seed in range(30):
            permuted = MOD._analysis(MOD.generate(seed, seed, scene_profile="permuted_frames"))
            self.assertEqual(set(permuted["row_colors"]), {0, 5, 9})
            self.assertNotEqual(permuted["row_colors"], MOD._STANDARD_FRAMES)

    def test_broad_source_uses_first_pattern_when_copies_differ(self):
        grid = MOD.generate(19, 31, scene_profile="row_cycle_012")
        parsed = MOD._source_parse(grid)
        expected = MOD.rule_mirror(grid)
        size = parsed["size"]
        col_index = 0
        pattern_rows = [row for row in range(3) if MOD._is_pattern(parsed["cores"][row][col_index])]
        later_row = pattern_rows[-1]
        first_row, _ = parsed["row_bands"][later_row]
        first_col, _ = parsed["col_bands"][col_index]
        start_col = first_col + 1
        grid[first_row + 1][start_col + 1] = 8 if grid[first_row + 1][start_col + 1] == 2 else 2
        self.assertTrue(MOD.self_check(grid))
        self.assertEqual(MOD.rule_mirror(grid), expected)
        self.assertEqual(len(MOD.rule_mirror(grid)), size)

    def test_broad_source_uses_first_solid_when_an_extra_solid_is_added(self):
        grid = MOD.generate(29, 37, scene_profile="row_cycle_012")
        expected = MOD.rule_mirror(grid)
        parsed = MOD._source_parse(grid)
        col_index = 0
        solid_row = MOD._analysis(grid)["solid_rows"][col_index]
        later_pattern_row = max(row for row in range(3) if row != solid_row)
        first_row, _ = parsed["row_bands"][later_pattern_row]
        first_col, _ = parsed["col_bands"][col_index]
        start_col = first_col + 1
        tile = MOD._solid_tile(parsed["size"], 7)
        MOD._put_tile(grid, first_row, start_col, tile)
        self.assertTrue(MOD.self_check(grid))
        self.assertEqual(MOD.rule_mirror(grid), expected)

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, input_shapes, output_shapes = set(), set(), set(), set()
        sizes, columns, solid_rows, colors = set(), set(), set(), set()
        for seed in range(3000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            input_shapes.add((len(grid), len(grid[0])))
            output_shapes.add((len(analysis["output"]), len(analysis["output"][0])))
            sizes.add(analysis["tile_size"])
            columns.add(analysis["column_count"])
            solid_rows.update(analysis["solid_rows"])
            colors.update(analysis["fill_colors"])
            colors.update(analysis["row_colors"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2600)
        self.assertGreater(len(outputs), 2600)
        self.assertGreaterEqual(len(input_shapes), 7)
        self.assertGreaterEqual(len(output_shapes), 7)
        self.assertEqual(sizes, {4, 5, 6, 7, 8})
        self.assertEqual(columns, {3, 4})
        self.assertEqual(solid_rows, {0, 1, 2})
        self.assertEqual(colors, {0, 3, 4, 5, 6, 7, 9})

    def test_malformed_and_uncalibrated_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[8] * 12 for _ in range(12)]]
        ragged = MOD.generate(3, 5, scene_profile="row_cycle_120")
        ragged[1].pop()
        cases.append(ragged)
        broken_separator = MOD.generate(7, 9, scene_profile="row_cycle_201")
        broken_separator[0][0] = 1
        cases.append(broken_separator)
        bad_swatch = MOD.generate(11, 13, scene_profile="row_cycle_012")
        bad_swatch[1][0] = 4
        cases.append(bad_swatch)
        no_pattern = MOD.generate(17, 19, scene_profile="row_cycle_012")
        parsed = MOD._source_parse(no_pattern)
        for row_index in range(3):
            first_row, _ = parsed["row_bands"][row_index]
            first_col, _ = parsed["col_bands"][0]
            MOD._put_tile(no_pattern, first_row, first_col + 1, MOD._solid_tile(parsed["size"], 3 + row_index))
        cases.append(no_pattern)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"tile_size": 6}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_rule_hash_and_base_source_are_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads((canonical_path(ROOT).parent.parent / BASE.removeprefix("data/")).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
