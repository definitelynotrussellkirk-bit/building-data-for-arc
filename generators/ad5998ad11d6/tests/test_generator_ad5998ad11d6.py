"""Focused semantic tests for generator ad5998ad11d6."""
from __future__ import annotations

import copy
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.runner import _load_generator_module
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "ad5998ad11d6"


class GeneratorAd5998ad11d6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.pairs = canonical_pairs(TASK_ID)

    def test_metadata_and_exact_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "3.1.0")
        self.assertEqual(self.module.RULE_HASH, "2658bcc9cd0f")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        self.assertEqual(
            set(self.module.AXES["scene_profile"]["valid"].split("|")),
            set(self.module.SCENE_PROFILES),
        )

    def test_all_canonical_pairs_are_positive_controls(self) -> None:
        self.assertEqual(len(self.pairs), 6)
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(self.module.solve_python(source), pair["output"])
                self.assertEqual(source, pair["input"])
                self.assertIn(
                    self.module.observe_overrides(source)["scene_profile"],
                    self.module.SCENE_PROFILES,
                )

    def test_every_profile_is_exactly_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile in self.module.SCENE_PROFILES:
                for seed in range(8):
                    with self.subTest(band=band, profile=profile, seed=seed):
                        grid = self.module.generate(
                            seed, seed + 31, difficulty=band, scene_profile=profile
                        )
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )
                        analysis = self.module._analyze(grid)
                        spec = self.module.SCENE_SPECS[profile]
                        self.assertEqual(
                            (analysis["height"], analysis["width"], analysis["enclosed_regions"]),
                            (spec.height, spec.width, spec.enclosed_regions),
                        )

    def test_defaults_are_deterministic_fresh_and_nonidentity(self) -> None:
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                first = self.module.generate(seed, seed + 7, difficulty=band)
                second = self.module.generate(seed, seed + 7, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(a is not b for a, b in zip(first, second)))
                output = self.module.solve_python(first)
                self.assertNotEqual(first, output)
                self.assertIsNot(first, output)
                self.assertTrue(all(a is not b for a, b in zip(first, output)))

    def test_generation_does_not_touch_global_random_state(self) -> None:
        random.seed(20260727)
        before = random.getstate()
        self.module.generate(1234, 8, difficulty="hard")
        self.assertEqual(random.getstate(), before)

    def test_unknown_override_and_bad_profile_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, obsolete_texture="frame")
        with self.assertRaisesRegex(ValueError, "not in options"):
            self.module.generate(0, 0, scene_profile="rectangle")

    def test_schedule_windows_are_semantically_identifiable(self) -> None:
        for band in ("easy", "medium", "hard"):
            for lesson_index in range(12):
                seed = 1000 + lesson_index
                start = lesson_index * 11
                examples = []
                for offset in range(self.module.EXAMPLES_NEEDED + 1):
                    grid = self.module.generate(
                        seed,
                        start + offset,
                        difficulty=band,
                    )
                    examples.append(
                        {"input": grid, "output": self.module.solve_python(grid)}
                    )
                demos = examples[:self.module.EXAMPLES_NEEDED]
                query = examples[self.module.EXAMPLES_NEEDED]
                self.assertEqual(
                    self.module.lesson_identifiable(demos, query), [],
                    msg=f"band={band} seed={seed} start={start}",
                )

    def test_lesson_roles_are_not_locked_to_one_profile_across_seeds(self) -> None:
        """A query/demo role must not reveal one fixed morphology forever."""
        for band in ("easy", "medium", "hard"):
            for role_offset in range(self.module.EXAMPLES_NEEDED + 1):
                observed = {
                    self.module.schedule_profile(seed, role_offset, band)
                    for seed in range(48)
                }
                self.assertGreaterEqual(
                    len(observed),
                    4,
                    msg=f"band={band} role_offset={role_offset} observed={observed}",
                )

    def test_large_profiles_cover_canonical_scale_room_areas(self) -> None:
        """The 20x20 distribution must include the canonical 15/24-cell rooms."""
        observed_sizes = set()
        for profile in ("five_20x20", "eight_20x20"):
            for seed in range(96):
                grid = self.module.generate(
                    20000 + seed,
                    seed * 13 + 5,
                    difficulty="hard",
                    scene_profile=profile,
                )
                sizes = self.module._analyze(grid)["enclosed_sizes"]
                observed_sizes.update(sizes)
                self.assertGreaterEqual(
                    max(sizes),
                    12,
                    msg=f"profile={profile} seed={seed} sizes={sizes}",
                )
        self.assertTrue({15, 24} <= observed_sizes, observed_sizes)

    def test_large_room_cutoff_is_an_executable_refuted_rival(self) -> None:
        self.assertIn("rooms_at_most_eight", self.module.SEMANTIC_RIVALS)
        witness = self.module.SEMANTIC_WITNESSES["canonical_scale_large_rooms"]
        for profile in ("five_20x20", "eight_20x20"):
            grid = self.module.generate(913, 27, scene_profile=profile)
            self.assertTrue(witness(grid), profile)
            self.assertNotEqual(
                self.module.SEMANTIC_RIVALS["rooms_at_most_eight"](grid),
                self.module.solve_python(grid),
            )

    def test_declared_witnesses_and_rivals_are_real(self) -> None:
        fired = {name: 0 for name in self.module.SEMANTIC_WITNESSES}
        for profile in self.module.SCENE_PROFILES:
            for seed in range(24):
                grid = self.module.generate(seed, seed + 9, scene_profile=profile)
                truth = self.module.solve_python(grid)
                for name, witness in self.module.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        fired[name] += 1
                        rivals = self.module.WITNESS_RIVALS[name]
                        self.assertTrue(
                            any(self.module.SEMANTIC_RIVALS[r](grid) != truth for r in rivals)
                        )
        self.assertTrue(all(count > 0 for count in fired.values()), fired)

    def test_census_has_diversity_and_no_public_replay(self) -> None:
        public = {
            json.dumps(pair["input"], separators=(",", ":")) for pair in self.pairs
        }
        seen = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                grid = self.module.generate(seed, seed * 17 + 3, difficulty=band)
                encoded = json.dumps(grid, separators=(",", ":"))
                seen.add(encoded)
                self.assertNotIn(encoded, public)
        self.assertGreater(len(seen), 300)

    def test_mutation_fixtures_are_rejected(self) -> None:
        for name, grid in self.module.mutation_fixtures():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_solver_preserves_input_and_nonzero_cells(self) -> None:
        grid = self.module.generate(812, 4)
        original = copy.deepcopy(grid)
        output = self.module.solve_python(grid)
        self.assertEqual(grid, original)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 0:
                    self.assertEqual(output[r][c], value)


if __name__ == "__main__":
    unittest.main()
