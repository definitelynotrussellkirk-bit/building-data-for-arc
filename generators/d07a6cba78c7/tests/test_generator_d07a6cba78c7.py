from __future__ import annotations

import copy
import random
import unittest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "d07a6cba78c7"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]


class GeneratorD07A6CBA78C7Tests(unittest.TestCase):
    def test_rule_hash_and_canonical_inputs(self):
        self.assertEqual(gen.RULE_HASH, "cf17e3a900c7")
        canonical = _canonical_inputs()
        self.assertEqual(len(canonical), 3)
        for grid in canonical:
            self.assertEqual(gen.self_check(grid), [])

    def test_exact_override_axes_and_observer(self):
        cases = [
            {"grid_h": 5},
            {"grid_h": 8},
            {"grid_w": 7},
            {"grid_w": 10},
            {"marker_row": 0},
            {"marker_row": 7},
            {"palette_size": 2},
            {"palette_size": 8},
            {"grid_h": 8, "grid_w": 10, "marker_row": 7, "palette_size": 8},
            {"grid_h": 5, "grid_w": 7, "marker_row": 0, "palette_size": 2},
        ]
        for band in ("easy", "medium", "hard"):
            for i, overrides in enumerate(cases):
                grid = gen.generate(1000 + i, 0, difficulty=band, **overrides)
                self.assertEqual(gen.self_check(grid), [])
                observed = gen.observe_overrides(grid)
                for key, value in overrides.items():
                    self.assertEqual(observed[key], value, (band, overrides, observed))
        with self.assertRaises(ValueError):
            gen.generate(1, 0, grid_h=5, marker_row=7)
        with self.assertRaises(TypeError):
            gen.generate(1, 0, not_an_axis=1)

    def test_determinism_fresh_returns_and_global_random_state(self):
        random.seed(81357)
        state_before = random.getstate()
        first = gen.generate(1234, 9, difficulty="hard")
        state_after = random.getstate()
        second = gen.generate(1234, 9, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_default_distribution_is_lawful_and_marker_position_varies(self):
        positions = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = gen.generate(seed, seed, difficulty=band)
                self.assertEqual(gen.self_check(grid), [], (band, seed))
                facts = gen.semantic_observables(grid)
                positions.add(facts["marker_row"])
                self.assertTrue(facts["payload_rows_unique"])
                self.assertTrue(facts["all_payload_rows_nonempty"])
        self.assertEqual(positions, set(range(8)))

    def test_canonical_profile_prior_and_equal_density_shortcut_witnesses(self):
        canonical_rates = {}
        equal_density_witnesses = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            matches = 0
            draws = 500
            for seed in range(10000 + band_index * draws, 10000 + (band_index + 1) * draws):
                grid = gen.generate(seed, seed, difficulty=band)
                facts = gen.semantic_observables(grid)
                strict = (
                    (facts["grid_h"], facts["grid_w"]) in gen._CANONICAL_PROFILES
                    and facts["palette_size"] in (5, 6)
                    and facts["nonmarker_rows_monochrome"]
                )
                matches += int(strict)
                counts = facts["payload_nonzero_counts"]
                if len(set(counts)) == 1:
                    equal_density_witnesses += 1
            rate = matches / draws
            canonical_rates[band] = rate
            self.assertGreaterEqual(rate, 0.20, canonical_rates)
            self.assertLessEqual(rate, 0.48, canonical_rates)
        self.assertGreater(equal_density_witnesses, 500)

    def test_self_check_rejects_minimal_and_task_specific_mutations(self):
        control = gen.generate(77, 1, difficulty="medium", grid_h=6, grid_w=8)
        self.assertEqual(gen.self_check(control), [])
        marker = gen.observe_overrides(control)["marker_row"]

        mutations = {}
        no_marker = copy.deepcopy(control)
        no_marker[marker][0] = 0
        mutations["no_marker"] = no_marker

        two_markers = copy.deepcopy(control)
        two_markers[(marker + 1) % len(two_markers)][0] = 6
        mutations["two_markers"] = two_markers

        payload_magenta = copy.deepcopy(control)
        payload_magenta[marker][1] = 6
        mutations["payload_magenta"] = payload_magenta

        empty_selected = copy.deepcopy(control)
        empty_selected[marker][1:] = [0] * (len(empty_selected[0]) - 1)
        mutations["empty_selected"] = empty_selected

        duplicate_row = copy.deepcopy(control)
        duplicate_row[(marker + 1) % len(duplicate_row)][1:] = list(duplicate_row[marker][1:])
        mutations["duplicate_payload_row"] = duplicate_row

        singleton = [[0] * 7 for _ in range(5)]
        singleton[2][0] = 6
        mutations["singleton_marker_only"] = singleton

        solid = [[1] * 7 for _ in range(5)]
        solid[2][0] = 6
        mutations["solid_one_color"] = solid

        for name, grid in mutations.items():
            self.assertTrue(gen.self_check(grid), name)


if __name__ == "__main__":
    unittest.main()
