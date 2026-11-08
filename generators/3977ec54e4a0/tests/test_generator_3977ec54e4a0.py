"""Focused regressions for the 896d5239 chevron-distribution repair."""
from __future__ import annotations

import copy
import hashlib
import importlib
import random
import unittest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "3977ec54e4a0"


def load_generator():
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def binary_grid(h=12, w=12):
    return [[(r + c) % 2 for c in range(w)] for r in range(h)]


class ChevronGeneratorRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.pairs = canonical_pairs(TASK_ID)

    def test_all_canonical_pairs_are_owned_and_solved(self):
        self.assertEqual(8, len(self.pairs))
        signatures = set()
        for pair in self.pairs:
            source = copy.deepcopy(pair["input"])
            self.assertEqual([], self.generator.self_check(source))
            self.assertEqual(pair["output"], self.generator.rule_mirror(source))
            self.assertEqual(pair["input"], source, "rule mirror mutated input")
            signatures.add(self.generator.canonical_profile_signature(source))
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)
        self.assertEqual(4, len(signatures))

    def test_profile_prior_reaches_every_complete_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {sig: 0 for sig in self.generator._CANONICAL_SIGNATURES}
            for seed in range(400):
                grid = self.generator.generate(seed, seed * 17 + 3, difficulty=band)
                signature = self.generator.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 80)
                self.assertTrue(all(value > 0 for value in counts.values()))

    def test_exact_axes_are_observable_and_unknown_axes_reject(self):
        cases = (
            dict(grid_h=12, grid_w=12, chevron_count=1,
                 max_depth=1, asymmetric_arms=False),
            dict(grid_h=22, grid_w=22, chevron_count=4,
                 max_depth=3, asymmetric_arms=True),
            dict(grid_h=15, grid_w=18, chevron_count=3,
                 max_depth=2, asymmetric_arms=False),
        )
        for index, overrides in enumerate(cases):
            grid = self.generator.generate(
                900 + index,
                1200 + index,
                difficulty="easy",
                **overrides,
            )
            with self.subTest(overrides=overrides):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual(overrides, self.generator.observe_overrides(grid))
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.generator.generate(1, 2, typo_axis=3)
        with self.assertRaisesRegex(ValueError, "requires max_depth"):
            self.generator.generate(1, 2, max_depth=1, asymmetric_arms=True)

    def test_asymmetric_axis_controls_exact_arm_masks(self):
        """The bool axis describes geometry, not merely unequal marker counts."""
        for requested in (False, True):
            for seed in range(24):
                grid = self.generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty="hard",
                    grid_h=22,
                    grid_w=22,
                    chevron_count=4,
                    max_depth=3,
                    asymmetric_arms=requested,
                )
                chevrons, errors = self.generator._decode_grid(grid)
                with self.subTest(requested=requested, seed=seed):
                    self.assertEqual([], errors)
                    actual = any(
                        chevron.left_mask != chevron.right_mask
                        for chevron in chevrons
                    )
                    self.assertEqual(requested, actual)

    def test_placement_accepts_close_components_when_oracle_keeps_them_separate(self):
        """Do not replace the oracle's aligned-near relation with Chebyshev distance."""

        class PreferredApexRng:
            def __init__(self, *apices):
                self.apices = iter(apices)

            def shuffle(self, candidates):
                desired = next(self.apices)
                candidates.sort(key=lambda candidate: candidate[:2] != desired)

        descriptor = (0, 1, (True,), (True,))
        placed = self.generator._place_descriptors(
            12,
            12,
            [descriptor, descriptor],
            PreferredApexRng((2, 2), (3, 6)),
        )

        self.assertEqual([(2, 2), (3, 6)], [item.apex for item in placed])
        first, second = placed
        self.assertFalse(
            any(
                self.generator._near(a, b)
                for a in first.markers
                for b in second.markers
            )
        )

    def test_semantic_witnesses_refute_named_executable_rivals(self):
        expected = {
            "down_chevron": "omit_down",
            "up_chevron": "omit_up",
            "right_chevron": "omit_right",
            "left_chevron": "omit_left",
            "depth_three": "cap_depth_two",
            "asymmetric_arms": "symmetric_only",
            "multiple_chevrons": "first_component_only",
            "missing_interior_arm_markers": "complete_arms_only",
        }
        self.assertEqual(set(expected.values()), set(self.generator.SEMANTIC_RIVALS))
        self.assertEqual(
            {witness: [rival] for witness, rival in expected.items()},
            self.generator.WITNESS_RIVALS,
        )
        self.assertEqual(
            set(self.generator.SEMANTIC_RIVALS),
            set(self.generator.LESSON_COMPETITORS),
        )

        fired = {name: 0 for name in expected}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for sample_index in range(40):
                grid = self.generator.generate(
                    51000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                authoritative = self.generator.rule_mirror(grid)
                for witness, rival in expected.items():
                    if self.generator.SEMANTIC_WITNESSES[witness](grid):
                        fired[witness] += 1
                        self.assertNotEqual(
                            authoritative,
                            self.generator.SEMANTIC_RIVALS[rival](grid),
                            (band, sample_index, witness, rival),
                        )
        self.assertTrue(all(fired.values()), fired)

        # These are pedagogical competitors, not alleged canonical shortcuts.
        for rival, solve in self.generator.SEMANTIC_RIVALS.items():
            self.assertTrue(
                any(solve(pair["input"]) != pair["output"] for pair in self.pairs),
                rival,
            )

    def test_every_cyclic_three_example_window_refutes_lesson_competitors(self):
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                seed = int(
                    hashlib.sha256(
                        f"lesson-census:v1:{TASK_ID}:{band}:{start}".encode()
                    ).hexdigest()[:8],
                    16,
                )
                demos = []
                for sample_index in range(start, start + 3):
                    grid = self.generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                    )
                    demos.append((grid, self.generator.rule_mirror(grid)))
                for rival, solve in self.generator.LESSON_COMPETITORS.items():
                    with self.subTest(band=band, start=start, rival=rival):
                        self.assertTrue(
                            any(solve(grid) != output for grid, output in demos),
                            "competitor survives every demonstration",
                        )

    def test_census_overlap_counterexample_refutes_omit_up(self):
        """Every scheduled orientation needs exclusive output evidence."""
        seed = 3184089087
        demos = []
        for sample_index in range(39, 42):
            grid = self.generator.generate(seed, sample_index, difficulty="medium")
            demos.append((grid, self.generator.rule_mirror(grid)))
        self.assertTrue(
            any(
                self.generator.SEMANTIC_RIVALS["omit_up"](grid) != output
                for grid, output in demos
            ),
            "lesson-census medium start 39 lets omit_up survive",
        )

    def test_three_slot_schedule_is_declared_and_canonically_grounded(self):
        expected = {"orientation_01", "orientation_23", "canonical"}
        self.assertEqual(expected, set(self.generator.SCHEDULE_PROFILES))
        for band in ("easy", "medium", "hard"):
            for start in range(6):
                profiles = {
                    self.generator.schedule_profile(7, start + offset, band)
                    for offset in range(3)
                }
                self.assertEqual(expected, profiles)
            for sample_index in (2, 5, 8, 11):
                grid = self.generator.generate(83, sample_index, difficulty=band)
                self.assertEqual([], self.generator.strict_canonical_like(grid))

    def test_deterministic_fresh_returns_and_global_rng_preservation(self):
        state = random.getstate()
        first = self.generator.generate(77, 31, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(77, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        third = self.generator.generate(77, 31, difficulty="hard")
        self.assertEqual(second, third)

    def test_plausible_recombination_is_lawful_but_not_official(self):
        # Start from the 15x12 official profile.  Add the two missing k=1 arm
        # markers to its small down chevron, recombining that dimension/profile
        # with the full-depth-2 morphology from a different official input.
        grid = copy.deepcopy(self.pairs[0]["input"])
        grid[13][3] = 3
        grid[13][5] = 3
        signature = self.generator.canonical_profile_signature(grid)
        self.assertEqual([], self.generator.self_check(grid))
        self.assertIsNotNone(signature)
        self.assertNotIn(signature, self.generator._CANONICAL_SIGNATURES)
        self.assertTrue(self.generator.strict_canonical_like(grid))
        self.assertEqual(len(grid), len(self.generator.rule_mirror(grid)))

    def test_minimal_impostors_and_ambiguous_marker_sets_are_rejected(self):
        probes = {}
        probes["all_background"] = binary_grid()
        probes["singleton"] = binary_grid()
        probes["singleton"][5][5] = 3
        probes["short_line"] = binary_grid()
        probes["short_line"][5][4:7] = [3, 3, 3]
        probes["solid_2x2"] = binary_grid()
        for r in (5, 6):
            for c in (5, 6):
                probes["solid_2x2"][r][c] = 3
        probes["off_arm_extra"] = binary_grid()
        for r, c in ((3, 6), (5, 4), (5, 8), (4, 6)):
            probes["off_arm_extra"][r][c] = 3

        for name, grid in probes.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))


if __name__ == "__main__":
    unittest.main()
