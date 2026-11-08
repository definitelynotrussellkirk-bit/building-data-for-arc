"""Portable regressions for the selected sampler's observable contract.

Run through review.py run, or the packet's isolated task_tests stage.
Canonical pairs are authoring data and must stay closed during a solve.
"""
import hashlib
import json
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "75ba893e1e36"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def colors(grid):
    return {v for row in grid for v in row}


def asymmetric(grid):
    return any(row != row[::-1] for row in grid)


class GeneratorContractTests(unittest.TestCase):
    def test_canonical_inputs_remain_accepted(self):
        pairs = canonical_pairs(TASK, root=ROOT)
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            with self.subTest(split=pair["split"], index=pair["pair_index"]):
                self.assertEqual(GEN.self_check(pair["input"]), [])

    def test_rule_pin_matches_canonical_authority(self):
        with canonical_path(ROOT).open() as source:
            rule = next(json.loads(line)["program_solution"] for line in source
                        if json.loads(line).get("task_id") == TASK)
        expected = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
        self.assertEqual(getattr(GEN, "RULE_HASH", None), expected)

    def test_requested_palette_count_is_realized(self):
        # Baseline seed 3 claimed three colors but returned only 5 and 7.
        for seed in range(100):
            with self.subTest(seed=seed):
                grid = GEN.generate(seed, 0, palette_size=3)
                self.assertEqual(len(colors(grid)), 3)
                self.assertTrue(asymmetric(grid))

    def test_explicit_shape_and_custom_palette_pass_public_domain(self):
        for h, w, palette in ((4, 5, [1, 2, 3]), (1, 2, [0, 9]),
                              (15, 7, [2, 4, 6]), (3, 3, [5, 7])):
            with self.subTest(h=h, w=w, palette=palette):
                grid = GEN.generate(17, 0, grid_h=h, grid_w=w,
                                    palette_size=len(palette), palette=palette)
                self.assertEqual((len(grid), len(grid[0])), (h, w))
                self.assertEqual(colors(grid), set(palette))
                self.assertEqual(GEN.self_check(grid), [])

    def test_palette_without_count_infers_its_length(self):
        for palette in ([1, 9], [0, 2, 8]):
            for seed in range(8):
                with self.subTest(palette=palette, seed=seed):
                    grid = GEN.generate(seed, 0, palette=palette)
                    self.assertEqual(colors(grid), set(palette))

    def test_impossible_joint_shape_and_palette_is_structured_rejection(self):
        for kwargs in ({"grid_h": 1, "grid_w": 2, "palette_size": 3},
                       {"grid_h": 1, "grid_w": 2, "palette": [0, 2, 8]}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError) as error:
                    GEN.generate(0, 0, **kwargs)
                self.assertEqual(set(kwargs), set(getattr(error.exception, "incompatible_axes", ())))

    def test_partial_shape_overrides_choose_feasible_free_dimensions(self):
        # Independent review: v2 draft chose width=2 for seed4/index1/h=1,
        # then rejected a feasible 3-color request. A free axis must adapt.
        requests = ({"grid_h": 1, "palette_size": 3},
                    {"grid_w": 2, "palette_size": 3},
                    {"grid_h": 1, "palette": [0, 2, 8]},
                    {"grid_w": 2, "palette": [0, 2, 8]},
                    {"palette_size": 3})
        for band in ("easy", "medium", "hard"):
            for index in (0, 1):
                for seed in (*range(32), 125):
                    for kwargs in requests:
                        with self.subTest(band=band, index=index, seed=seed, kwargs=kwargs):
                            grid = GEN.generate(seed, index, difficulty=band, **kwargs)
                            self.assertEqual(len(colors(grid)), 3)
                            self.assertEqual(GEN.self_check(grid), [])
                            for axis, actual in (("grid_h", len(grid)), ("grid_w", len(grid[0]))):
                                if axis in kwargs:
                                    self.assertEqual(actual, kwargs[axis])
                            if "palette" in kwargs:
                                self.assertEqual(colors(grid), set(kwargs["palette"]))

    def test_invalid_scalar_and_enum_values_are_rejected(self):
        invalid = [
            {"grid_h": True}, {"grid_h": 3.9}, {"grid_h": "3"},
            {"grid_w": 3.0}, {"grid_w": "3"}, {"grid_w": 1},
            {"grid_h": 0}, {"grid_h": 16}, {"grid_w": 8},
            {"palette_size": 2.9}, {"palette_size": True}, {"palette_size": 1},
            {"palette": [True, 7]}, {"palette": [5, 10]},
            {"palette": [5, 5]}, {"palette": [5, 7.0]},
            {"palette": "578"}, {"palette": [5, 7], "palette_size": 3},
            {"texture": "typo"}, {"bg_density": "0.5"},
            {"bg_density": float("nan")}, {"bg_density": 1.0},
            {"noise_overlay": -0.1}, {"noise_overlay": True},
            {"noise_overlay": float("inf")}, {"lr_asymmetric": "false"},
            {"lr_asymmetric": False}, {"unknown_typo": 7},
        ]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(0, 0, **kwargs)
        for seed, index, difficulty in ((True, 0, None), (1.5, 0, None),
                                        (0, -1, None), (0, 0.5, None),
                                        (0, 0, True), (0, 0, "typo")):
            with self.subTest(seed=seed, index=index, difficulty=difficulty):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(seed, index, difficulty=difficulty)

    def test_retired_controls_fail_with_migration_guidance(self):
        for kwargs in ({"left_edge_kind": "matching", "lr_asymmetric": True},
                       {"left_edge_kind": "blank"}, {"row_pattern": "row_distinct"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, "retired"):
                    GEN.generate(1, 0, **kwargs)
        for name in ("monochrome", "lr_symmetric", "single_col"):
            with self.subTest(texture=name):
                with self.assertRaisesRegex(ValueError, "make_degenerate"):
                    GEN.generate(1, 0, texture=name)

    def test_density_and_noise_have_causal_effect_without_texture_override(self):
        for axis, value in (("bg_density", 0.95), ("noise_overlay", 0.3)):
            differing = sum(GEN.generate(seed, 0) != GEN.generate(seed, 0, **{axis: value})
                            for seed in range(32))
            with self.subTest(axis=axis):
                self.assertGreater(differing, 0, "declared control is bypassed")

    def test_helpful_textures_keep_exact_constraints(self):
        for band in ("easy", "medium", "hard"):
            for texture in GEN.HELPFUL_TEXTURES:
                for count in (2, 3):
                    for seed in range(8):
                        with self.subTest(band=band, texture=texture, count=count, seed=seed):
                            grid = GEN.generate(seed, 0, difficulty=band,
                                                texture=texture, palette_size=count)
                            self.assertEqual(len(colors(grid)), count)
                            self.assertTrue(asymmetric(grid))
                            self.assertEqual(GEN.self_check(grid), [])

    def test_actual_observations_equal_returned_pixels(self):
        observer = getattr(GEN, "observe_overrides", None)
        self.assertTrue(callable(observer), "exact axes need a pixel observer")
        for seed in range(10):
            grid = GEN.generate(seed, 0, grid_h=4, grid_w=6, palette_size=3)
            actual = observer(grid)
            self.assertEqual(actual["grid_h"], len(grid))
            self.assertEqual(actual["grid_w"], len(grid[0]))
            self.assertEqual(actual["palette_size"], len(colors(grid)))

    def test_negative_fixtures_are_separate_and_rejected(self):
        maker = getattr(GEN, "make_degenerate", None)
        self.assertTrue(callable(maker), "negative fixtures need their own explicit API")
        for name in ("lr_symmetric", "monochrome", "single_col"):
            with self.subTest(name=name):
                grid = maker(name, seed=17)
                self.assertTrue(GEN.self_check(grid))
                self.assertTrue(grid and grid[0])
                self.assertTrue(all(type(v) is int and 0 <= v <= 9 for row in grid for v in row))

    def test_malformed_grids_return_reasons_without_crashing(self):
        for grid in (None, [], [[]], [[5, 7], [8]], [[True, 7]],
                     [[5, "7"]], [[5, 10]], [5, 7]):
            with self.subTest(grid=grid):
                self.assertTrue(GEN.self_check(grid))

    def test_lawful_minimal_pattern_is_not_banned_to_silence_generic_lint(self):
        # This performs a visible, nontrivial LR reflection under the authority.
        self.assertEqual(GEN.self_check([[7, 7, 5], [7, 7, 5], [5, 5, 5]]), [])

    def test_none_controls_are_the_same_as_absent(self):
        kwargs = {axis: None for axis in GEN.AXES}
        self.assertEqual(GEN.generate(17, 0), GEN.generate(17, 0, **kwargs))

    def test_width_witnesses_survive_duplicate_filtering(self):
        # Public sampler rejects duplicate pairs. Draft period2 loses the second
        # witness at seed305/easy; raw-candidate counts alone missed the defect.
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 305):
                for start in range(4):
                    with self.subTest(band=band, seed=seed, start=start):
                        accepted, seen = [], set()
                        for index in range(start, start + 24):
                            grid = GEN.generate(seed, index, difficulty=band)
                            key = tuple(tuple(row) for row in grid)
                            if key not in seen:
                                seen.add(key)
                                accepted.append(grid)
                            if len(accepted) == 4:
                                break
                        self.assertEqual(len(accepted), 4)
                        self.assertGreaterEqual(sum(len(g[0]) != 3 for g in accepted), 2)

    def test_default_schedule_teaches_width_generalization(self):
        strict = getattr(GEN, "strict_canonical_like", None)
        self.assertTrue(callable(strict))
        for band in ("easy", "medium", "hard"):
            grids = [GEN.generate(17, i, difficulty=band) for i in range(20)]
            self.assertGreaterEqual(sum(not strict(grid) for grid in grids), 5)
            for start in range(17):
                window = grids[start:start+4]
                self.assertGreaterEqual(sum(len(g[0]) != 3 for g in window), 2)
            for i, grid in enumerate(grids):
                self.assertEqual(grid, GEN.generate(17, i, difficulty=band))


if __name__ == "__main__":
    unittest.main()
