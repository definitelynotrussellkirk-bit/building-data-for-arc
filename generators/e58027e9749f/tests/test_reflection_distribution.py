"""Regressions for exact controls, canonical support and shortcut exposure."""
import unittest
import json
from reviewer_support import canonical_pairs, find_root, load_selected_generator


def realized(grid):
    cells = [(r, c, value) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    above = any(r < c for r, c, _ in cells)
    below = any(r > c for r, c, _ in cells)
    side = "mixed" if above and below else "above_diagonal" if above else "below_diagonal"
    return {"size": len(grid), "cell_count": len(cells),
            "n_distinct_colors": len({value for _, _, value in cells}), "position_bias": side}


class ReflectionDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = find_root(__file__)
        cls.gen, _, _ = load_selected_generator("e58027e9749f", root=cls.root)

    def test_global_size_control_is_honored_in_every_difficulty(self):
        for band in ("easy", "medium", "hard"):
            for size in (4, 5, 7, 18):
                with self.subTest(band=band, size=size):
                    grid = self.gen.generate(17, 0, difficulty=band, size=size)
                    self.assertEqual((len(grid), len(grid[0])), (size, size))

    def test_exact_joint_controls_are_observable(self):
        for side in ("above_diagonal", "below_diagonal", "mixed"):
            for band in ("easy", "medium", "hard"):
                forced = dict(size=6, cell_count=5, n_distinct_colors=3, position_bias=side)
                with self.subTest(side=side, band=band):
                    grid = self.gen.generate(41, 9, difficulty=band, **forced)
                    self.assertEqual(realized(grid), forced)
                    self.assertEqual(self.gen.observe_overrides(grid), forced)
                    self.assertEqual(self.gen.self_check(grid), [])

    def test_high_palette_request_adapts_unforced_cell_count(self):
        for band in ("easy", "medium", "hard"):
            grid = self.gen.generate(2, 0, difficulty=band, n_distinct_colors=9)
            self.assertEqual(realized(grid)["n_distinct_colors"], 9)
            self.assertGreaterEqual(realized(grid)["cell_count"], 9)

    def test_unknown_controls_are_rejected(self):
        with self.assertRaises((TypeError, ValueError, KeyError)):
            self.gen.generate(0, 0, typo_size=9)

    def test_impossible_joint_controls_are_explicit(self):
        cases = [dict(size=4, cell_count=7),
                 dict(cell_count=1, n_distinct_colors=2),
                 dict(cell_count=1, position_bias="mixed"),
                 dict(size=4, n_distinct_colors=9)]
        for forced in cases:
            with self.subTest(forced=forced):
                with self.assertRaises(ValueError) as caught:
                    self.gen.generate(0, 0, **forced)
                self.assertGreaterEqual(len(caught.exception.incompatible_axes), 2)
                self.assertTrue(set(caught.exception.incompatible_axes) <= set(forced))

    def test_noninteger_override_coercion_is_rejected(self):
        for axis, invalid in (("size", True), ("size", 6.0), ("cell_count", "3"),
                              ("n_distinct_colors", False)):
            with self.subTest(axis=axis, invalid=invalid):
                with self.assertRaises((ValueError, TypeError)):
                    self.gen.generate(0, 0, **{axis: invalid})

    def test_identity_arguments_reject_malformed_scalars(self):
        cases = [("seed", value) for value in (True, False, 1.0, 1.75, "1", None)]
        cases += [("sample_index", value) for value in (True, False, 1.0, 1.75, "1", -1, None)]
        cases += [("difficulty", value) for value in (True, False, 0, 1.0, "__invalid_difficulty__", [])]
        for axis, value in cases:
            args = dict(seed=0, sample_index=0, difficulty="easy")
            args[axis] = value
            with self.subTest(axis=axis, value=value):
                with self.assertRaises((ValueError, TypeError)):
                    self.gen.generate(**args)
                with self.assertRaises((ValueError, TypeError)):
                    self.gen.schedule_profile(**args)

    def test_single_cell_control_adapts_an_unforced_mixed_schedule(self):
        for seed, index in ((0, 1), (1, 0)):
            self.assertEqual(self.gen.schedule_profile(seed, index), "mixed")
            grid = self.gen.generate(seed, index, cell_count=1)
            self.assertEqual(realized(grid)["cell_count"], 1)
            self.assertIn(realized(grid)["position_bias"], ("above_diagonal", "below_diagonal"))
            self.assertEqual(self.gen.self_check(grid), [])

    def test_validator_rejects_invalid_scalars_including_background(self):
        for bad in (True, False, 0.0, 3.0, "0", None, [], {}):
            grid = [[0] * 5 for _ in range(5)]
            grid[0][3] = 2
            grid[4][4] = bad
            with self.subTest(bad=bad):
                self.assertTrue(self.gen.self_check(grid))

    def test_validator_accepts_lower_sources_but_rejects_conflicting_pairs(self):
        grid = [[0] * 5 for _ in range(5)]
        grid[3][0] = 2
        self.assertEqual(self.gen.self_check(grid), [])
        grid[0][3] = 4
        self.assertTrue(self.gen.self_check(grid))

    def test_retained_lower_source_counterexample_refutes_canonical_shortcut(self):
        _, source_path, source_hash = load_selected_generator("e58027e9749f", root=self.root)
        case = json.loads((self.root / "generators/e58027e9749f/counterexamples/upper_only_below_source.json").read_text())
        self.assertEqual(source_hash, case["generator_sha256"])
        grid = self.gen.generate(0, 0, size=5, cell_count=1,
                                 n_distinct_colors=1, position_bias="below_diagonal")
        self.assertEqual(grid, case["input"])
        self.assertEqual(self.gen.self_check(grid), [])
        rival = self.gen.CANONICAL_SHORTCUTS["upper_only"]
        self.assertEqual(rival(grid), case["rival_output"])
        self.assertNotEqual(rival(grid), case["racket_output"])
        for pair in canonical_pairs("e58027e9749f", root=self.root):
            self.assertEqual(rival(pair["input"]), pair["output"])

    def test_four_pair_windows_keep_a_mixed_demo_after_every_rotation(self):
        for seed in (0, 1, 17, 101):
            for band in ("easy", "medium", "hard"):
                for start in range(8):
                    rows = [realized(self.gen.generate(seed, start+i, difficulty=band))
                            for i in range(4)]
                    self.assertGreaterEqual(sum(row["position_bias"] == "mixed" for row in rows), 2)
                    for query in range(4):
                        self.assertTrue(any(row["position_bias"] == "mixed"
                                            for i, row in enumerate(rows) if i != query))

    def test_no_default_draw_has_occupied_transpose_targets(self):
        for seed in range(30):
            for band in ("easy", "medium", "hard"):
                grid = self.gen.generate(seed, seed % 7, difficulty=band)
                self.assertEqual(self.gen.self_check(grid), [])
                self.assertTrue(all(r != c and grid[c][r] == 0
                                    for r, row in enumerate(grid) for c, value in enumerate(row) if value))

    def test_canonical_pairs_are_accepted_by_the_semantic_domain(self):
        for pair in canonical_pairs("e58027e9749f", root=self.root):
            self.assertEqual(self.gen.strict_canonical_like(pair["input"]), [])

    def test_every_band_retains_canonical_profile_support(self):
        profiles = {(len(pair["input"]), len(pair["input"][0]),
                     len({v for row in pair["input"] for v in row}))
                    for pair in canonical_pairs("e58027e9749f", root=self.root)}
        for band in ("easy", "medium", "hard"):
            hits = 0
            for seed in range(80):
                grid = self.gen.generate(seed, 0, difficulty=band)
                hits += (len(grid), len(grid[0]), len({v for row in grid for v in row})) in profiles
            self.assertGreaterEqual(hits, 8, band)

    def test_same_seed_and_index_reproduce_exactly(self):
        for band in ("easy", "medium", "hard"):
            self.assertEqual(self.gen.generate(812, 7, difficulty=band),
                             self.gen.generate(812, 7, difficulty=band))


if __name__ == "__main__":
    unittest.main()
