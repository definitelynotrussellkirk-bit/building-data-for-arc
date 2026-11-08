"""Public source-bound regressions for the repaired half-swap curriculum.

These tests use selected-source loading and public canonical authoring data.
They are review tests, never blind-solve code or training admission evidence.
"""
from pathlib import Path
import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "2b34f380ed25"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
RIVAL_NAMES = {
    "geometric_reflection",
    "vertical_reflection",
    "horizontal_reflection",
    "ignore_unbalanced_marks",
}
BANDS = ("easy", "medium", "hard")
ORIGINAL_PROFILES = {
    "public_1", "public_2", "public_3", "public_4", "public_5", "public_6",
    "fill_uniform_panel", "multicolor_preserve_plus_fill",
    "vertical_swap_two", "vertical_swap_four",
    "horizontal_swap_two", "horizontal_swap_four",
    "unbalanced_vertical_plus_fill", "unbalanced_horizontal_plus_fill",
    "row_split_mixed", "four_panel_mixed",
}


def macro_block(grid, top, left):
    """Read one visible solid 3x3 block; independent of generator extraction."""
    return [row[left:left + 3] for row in grid[top:top + 3]]


def accepts_strict(grid):
    result = GEN.strict_canonical_like(grid)
    if isinstance(result, bool):
        return result
    if isinstance(result, list):
        return result == []
    raise AssertionError("strict_canonical_like must return bool or a reason list")


class ReviewContractTests(unittest.TestCase):
    def test_review_contract_declares_real_canonical_fitting_rivals(self):
        self.assertEqual(GEN.VERSION, "3.1.0")
        self.assertEqual(GEN.EXAMPLES_NEEDED, 5)
        self.assertEqual(GEN.LESSON_SCHEDULE_PERIOD, 3)
        pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 6)
        for registry_name in (
            "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"
        ):
            registry = getattr(GEN, registry_name)
            self.assertTrue(RIVAL_NAMES <= set(registry), registry_name)
            for name in sorted(RIVAL_NAMES):
                self.assertTrue(callable(registry[name]), (registry_name, name))
                for index, pair in enumerate(pairs):
                    with self.subTest(registry=registry_name, rival=name, canonical=index):
                        self.assertEqual(registry[name](pair["input"]), pair["output"])
        for index, pair in enumerate(pairs):
            with self.subTest(canonical=index):
                self.assertTrue(accepts_strict(pair["input"]))
                self.assertEqual(GEN.rule_mirror(pair["input"]), pair["output"])

    def test_seed_and_sample_index_require_exact_integers(self):
        for bad in (True, False, 1.0, 1.5, "1", None):
            with self.subTest(argument="seed", value=bad):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(bad, 0)
            with self.subTest(argument="sample_index", value=bad):
                with self.assertRaises((TypeError, ValueError)):
                    GEN.generate(1, bad)
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, -1)
        grid = GEN.generate(-7, 0)
        self.assertEqual(GEN.self_check(grid), [])
        self.assertEqual(grid, GEN.generate(-7, 0))

    def test_strict_domain_rejects_malformed_and_nonmacro_inputs(self):
        self.assertTrue(callable(getattr(GEN, "strict_canonical_like", None)))
        invalid = ([], [[]], [[True]], [[1.0]], [[10]], [[1], [1, 2]],
                   [[0] * 9 for _ in range(9)], [[1] * 9 for _ in range(9)])
        for grid in invalid:
            with self.subTest(grid=grid):
                self.assertFalse(accepts_strict(grid))

    def test_forced_profiles_stay_observable_and_lawful(self):
        self.assertEqual(set(GEN.SCENE_PROFILES), ORIGINAL_PROFILES)
        self.assertEqual(len(GEN.SCENE_PROFILES), 16)
        with self.assertRaises(ValueError):
            GEN.generate(19, 7, scene_profile="wide_swap_mixed")
        for profile in GEN.SCENE_PROFILES:
            with self.subTest(profile=profile):
                grid = GEN.generate(19, 7, scene_profile=profile)
                self.assertEqual(GEN.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(GEN.self_check(grid), [])
                self.assertTrue(accepts_strict(grid))
                if profile == "four_panel_mixed":
                    self.assertEqual((len(grid), len(grid[0])), (27, 27))
                    for name in ("vertical_reflection", "horizontal_reflection"):
                        self.assertNotEqual(GEN.SEMANTIC_RIVALS[name](grid), GEN.rule_mirror(grid), name)
                if profile == "row_split_mixed":
                    # Existing explicit override keeps its original 4x2
                    # vertical-swap-plus-fill scene, regardless of lane residue.
                    self.assertEqual((len(grid), len(grid[0])), (19, 9))
                    output = GEN.rule_mirror(grid)
                    for top in (1, 5):
                        self.assertEqual(macro_block(output, top, 1), macro_block(grid, top, 5))
                        self.assertEqual(macro_block(output, top, 5), macro_block(grid, top, 1))
                    lower_values = [output[top][left] for top in (11, 15) for left in (1, 5)]
                    self.assertEqual(len(set(lower_values)), 1)
                    self.assertNotIn(lower_values[0], (0, 1))
                    self.assertTrue(any(grid[top][left] == 1 for top in (11, 15) for left in (1, 5)))

    def test_wide_scene_refutes_each_reflection_axis(self):
        self.assertTrue(RIVAL_NAMES <= set(getattr(GEN, "SEMANTIC_RIVALS", {})))
        # One scene must distinguish both axes; testing separate scenes would
        # permit an axis-specific shortcut to survive a lesson rotation.
        for band in BANDS:
            for seed in (0, 19):
                with self.subTest(band=band, seed=seed):
                    # Strengthening an existing four-panel family preserves
                    # every public profile identity and action signature.
                    grid = GEN.generate(seed, 0, difficulty=band)
                    self.assertEqual(GEN.observe_overrides(grid), {"scene_profile": "four_panel_mixed"})
                    self.assertEqual((len(grid), len(grid[0])), (27, 27))
                    self.assertEqual(GEN.self_check(grid), [])
                    self.assertTrue(accepts_strict(grid))
                    expected = GEN.rule_mirror(grid)
                    # Top-right exchanges two-column halves; bottom-left
                    # exchanges two-row halves, retaining partner order.
                    for top in (1, 5):
                        for left, source_left in ((11, 19), (15, 23), (19, 11), (23, 15)):
                            self.assertEqual(macro_block(expected, top, left),
                                             macro_block(grid, top, source_left))
                    for top, source_top in ((11, 19), (15, 23), (19, 11), (23, 15)):
                        for left in (1, 5):
                            self.assertEqual(macro_block(expected, top, left),
                                             macro_block(grid, source_top, left))
                    # The other two panel actions remain fill and preserve.
                    filled = [expected[top][left] for top in (1, 5) for left in (1, 5)]
                    self.assertEqual(len(set(filled)), 1)
                    self.assertNotIn(filled[0], (0, 1))
                    for top in (11, 15, 19, 23):
                        for left in (11, 15, 19, 23):
                            self.assertEqual(macro_block(expected, top, left), macro_block(grid, top, left))
                    for name in ("geometric_reflection", "vertical_reflection", "horizontal_reflection"):
                        self.assertNotEqual(GEN.SEMANTIC_RIVALS[name](grid), expected, name)

    def test_every_unbalanced_scene_actually_teaches_mark_suppresses_fill(self):
        self.assertTrue(RIVAL_NAMES <= set(getattr(GEN, "SEMANTIC_RIVALS", {})))
        for band in BANDS:
            for seed in (0, 19, 260):
                for profile in ("unbalanced_vertical_plus_fill", "unbalanced_horizontal_plus_fill"):
                    with self.subTest(band=band, seed=seed, profile=profile):
                        grid = GEN.generate(seed, 11, difficulty=band, scene_profile=profile)
                        self.assertEqual(GEN.self_check(grid), [])
                        self.assertTrue(accepts_strict(grid))
                        expected = GEN.rule_mirror(grid)
                        self.assertNotEqual(
                            GEN.SEMANTIC_RIVALS["ignore_unbalanced_marks"](grid), expected
                        )

    def test_consecutive_lessons_refute_all_rivals_in_every_query_rotation(self):
        self.assertTrue(RIVAL_NAMES <= set(getattr(GEN, "LESSON_COMPETITORS", {})))
        self.assertTrue(callable(getattr(GEN, "strict_canonical_like", None)))
        context_profiles = ORIGINAL_PROFILES
        for band in BANDS:
            for seed in (0, 19):
                for start in range(3):
                    grids = [GEN.generate(seed, start + offset, difficulty=band)
                             for offset in range(6)]
                    expected = [GEN.rule_mirror(grid) for grid in grids]
                    profiles = [GEN.observe_overrides(grid)["scene_profile"] for grid in grids]
                    for offset, (grid, profile) in enumerate(zip(grids, profiles)):
                        residue = (start + offset) % 3
                        with self.subTest(band=band, seed=seed, start=start, offset=offset):
                            self.assertEqual(GEN.self_check(grid), [])
                            self.assertTrue(accepts_strict(grid))
                            if residue == 0:
                                self.assertEqual(profile, "four_panel_mixed")
                                self.assertEqual((len(grid), len(grid[0])), (27, 27))
                                for name in ("vertical_reflection", "horizontal_reflection"):
                                    self.assertNotEqual(GEN.SEMANTIC_RIVALS[name](grid),
                                                        expected[offset], name)
                            elif residue == 1:
                                self.assertIn(profile, {"unbalanced_vertical_plus_fill", "unbalanced_horizontal_plus_fill"})
                            else:
                                self.assertIn(profile, context_profiles)
                    for query in range(6):
                        demos = [index for index in range(6) if index != query]
                        for name in sorted(RIVAL_NAMES):
                            with self.subTest(band=band, seed=seed, start=start,
                                              query=query, rival=name):
                                rival = GEN.LESSON_COMPETITORS[name]
                                self.assertTrue(
                                    any(rival(grids[index]) != expected[index] for index in demos),
                                    "rival survives all five demos after query rotation",
                                )


if __name__ == "__main__":
    unittest.main()
