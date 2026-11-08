from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "01ab62800c73"
ROOT = find_root(__file__)
MOD, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _palette_size(grid):
    return len({value for row in grid for value in row})


def _component_count(grid):
    cells = {(r, c) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c] != 0}
    count = 0
    while cells:
        count += 1
        stack = [cells.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in cells:
                    cells.remove(nxt)
                    stack.append(nxt)
    return count


class GeneratorTests(unittest.TestCase):
    def test_rule_hash_and_python_mirror_match_every_labeled_canonical_pair(self):
        pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 3)
        with canonical_path(ROOT).open(encoding="utf-8") as handle:
            source = next(
                row["program_solution"]
                for row in map(json.loads, handle)
                if row.get("task_id") == TASK
            )
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        for pair in pairs:
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.strict_canonical_like(pair["input"]), [])
            self.assertEqual(MOD.self_check(pair["input"]), [])

    def test_declared_four_step_schedule_covers_each_profile_and_refutes_order_rivals(self):
        expected = set(MOD.SCHEDULE_PROFILES)
        self.assertEqual(MOD.LESSON_SCHEDULE_PERIOD, len(expected))
        for band in (None, "easy", "medium", "hard"):
            for start in range(MOD.LESSON_SCHEDULE_PERIOD):
                profiles = {
                    MOD.schedule_profile(17, start + offset, band)
                    for offset in range(MOD.LESSON_SCHEDULE_PERIOD)
                }
                self.assertEqual(profiles, expected)
            for sample_index in range(24):
                grid = MOD.generate(31, sample_index, difficulty=band)
                self.assertEqual(MOD.self_check(grid), [])
                expected_output = MOD.rule_mirror(grid)
                self.assertNotEqual(MOD.LESSON_COMPETITORS["sort_commands"](grid), expected_output)
                self.assertNotEqual(MOD.LESSON_COMPETITORS["first_command_only"](grid), expected_output)
                self.assertNotEqual(MOD.LESSON_COMPETITORS["last_command_only"](grid), expected_output)

    def test_axis_overrides_are_exact_across_all_bands(self):
        textures = tuple(MOD.HELPFUL_TEXTURES)
        for band in (None, "easy", "medium", "hard"):
            for h in (5, 14):
                for w in (6, 14):
                    for n_ops in (1, 4):
                        for texture in textures:
                            grid = MOD.generate(
                                103,
                                7,
                                difficulty=band,
                                grid_h=h,
                                grid_w=w,
                                n_ops=n_ops,
                                texture=texture,
                            )
                            self.assertEqual(MOD.self_check(grid), [], (band, h, w, n_ops, texture))
                            self.assertEqual(
                                MOD.observe_overrides(grid),
                                {"grid_h": h, "grid_w": w, "n_ops": n_ops, "texture": texture},
                            )

    def test_scalar_validation_unknown_overrides_determinism_and_global_rng(self):
        for value in (True, 1.5, "7", -1):
            with self.assertRaises((TypeError, ValueError), msg=repr(value)):
                MOD.generate(1, value)
        for value in (True, 2.0, "2", 0, 5):
            with self.assertRaises((TypeError, ValueError), msg=repr(value)):
                MOD.generate(1, 2, n_ops=value)
        for bad in (True, 5.0, "5", 4, 15):
            with self.assertRaises((TypeError, ValueError), msg=repr(bad)):
                MOD.generate(1, 2, grid_h=bad)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, unknown_axis=3)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")

        large_seed_grid = MOD.generate(10**15 + 123, 23, difficulty="hard")
        self.assertEqual(MOD.self_check(large_seed_grid), [])

        random.seed(409)
        state = random.getstate()
        first = MOD.generate(19, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(19, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_self_check_rejects_structural_and_semantic_impostors(self):
        cases = [
            [],
            [[]],
            [[True]],
            [[10]],
            [[1, 0], [1]],
            [[0] * 6 for _ in range(5)],
        ]
        bad_header = [[0] * 6 for _ in range(5)]
        bad_header[0][0] = 5
        bad_header[2][2:4] = [7, 7]
        cases.append(bad_header)
        empty_body = [[0] * 6 for _ in range(5)]
        empty_body[0][0:2] = [3, 1]
        cases.append(empty_body)
        solid_square = [[0] * 6 for _ in range(5)]
        solid_square[0][0:2] = [3, 1]
        solid_square[2][2:4] = [7, 7]
        solid_square[3][2:4] = [7, 7]
        cases.append(solid_square)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_default_distribution_covers_profiles_textures_shapes_and_canonical_envelope(self):
        profiles = Counter()
        textures = Counter()
        component_counts = set()
        canvas_shapes = set()
        inputs = set()
        canonical_profiles = {(5, 6, 4), (5, 7, 4)}
        matched_by_band = {band: False for band in (None, "easy", "medium", "hard")}
        for band in matched_by_band:
            for sample_index in range(160):
                grid = MOD.generate(211, sample_index, difficulty=band)
                analysis = MOD._analysis(grid)
                self.assertEqual(analysis["errors"], [], (band, sample_index, analysis))
                profile = MOD.schedule_profile(211, sample_index, band)
                profiles[profile] += 1
                observed = MOD.observe_overrides(grid)
                textures[observed["texture"]] += 1
                component_counts.add(_component_count(grid))
                canvas_shapes.add((len(grid), len(grid[0])))
                inputs.add(tuple(map(tuple, grid)))
                signature = (len(grid), len(grid[0]), _palette_size(grid))
                matched_by_band[band] |= signature in canonical_profiles
        self.assertEqual(set(profiles), set(MOD.SCHEDULE_PROFILES))
        self.assertEqual(set(textures), set(MOD.HELPFUL_TEXTURES))
        self.assertTrue({1, 2}.issubset(component_counts))
        self.assertTrue(all(matched_by_band.values()), matched_by_band)
        self.assertGreater(len(canvas_shapes), 30)
        self.assertGreater(len(inputs), 600)

    def test_default_schedule_has_comfortable_canonical_profile_floor(self):
        canonical_profiles = {(5, 6, 4), (5, 7, 4)}
        for band in (None, "easy", "medium", "hard"):
            hits = 0
            for sample_index in range(80):
                grid = MOD.generate(991, sample_index, difficulty=band)
                signature = (len(grid), len(grid[0]), _palette_size(grid))
                hits += signature in canonical_profiles
            self.assertGreaterEqual(hits, 35, (band, hits))

    def test_canonical_sorting_shortcut_fits_all_labels_but_generated_cases_refute_it(self):
        pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
        rival = MOD.CANONICAL_SHORTCUTS["sort_commands"]
        self.assertTrue(all(rival(pair["input"]) == pair["output"] for pair in pairs))
        counterexample = MOD.generate(0, 0, difficulty="easy")
        self.assertNotEqual(rival(counterexample), MOD.rule_mirror(counterexample))
        self.assertTrue(MOD.SEMANTIC_WITNESSES["ordered_sequence_visible"](counterexample))


if __name__ == "__main__":
    unittest.main()
