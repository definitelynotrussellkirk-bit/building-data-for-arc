from __future__ import annotations

from importlib import import_module
import unittest

from reviewer_support import canonical_pairs, find_root


generator = import_module(
    "puzzle_generators.per_puzzle.27f5eba1051c.generator"
)


class SemanticCurriculum27f5eba1051cTests(unittest.TestCase):
    def test_declared_canonical_shortcuts_fit_every_public_pair(self):
        expected = {
            "bbox_area",
            "row_before_column_ties",
            "color_before_column_ties",
            "group_same_color",
        }
        self.assertEqual(set(generator.CANONICAL_SHORTCUTS), expected)
        pairs = canonical_pairs(generator.TASK_ID, root=find_root(__file__))
        self.assertEqual(len(pairs), 5)
        for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
            with self.subTest(shortcut=name):
                self.assertTrue(
                    all(
                        shortcut(pair["input"]) == pair["output"]
                        for pair in pairs
                    )
                )

    def test_four_slot_schedule_covers_every_semantic_role(self):
        expected = (
            "canonical_linked",
            "column_tie",
            "color_tie",
            "semantic_stress",
        )
        self.assertEqual(generator.SCHEDULE_PROFILES, expected)
        for start in range(12):
            observed = tuple(
                generator.schedule_profile(17, start + offset, "medium")
                for offset in range(generator.EXAMPLES_NEEDED)
            )
            self.assertEqual(set(observed), set(expected))

    def test_semantic_stress_refutes_core_shortcuts(self):
        names = {
            "ascending_area",
            "bbox_area",
            "left_to_right",
            "group_same_color",
            "solid_bbox",
        }
        for band in ("easy", "medium", "hard"):
            for seed in range(12):
                grid = generator.generate(
                    20_000 + seed,
                    seed,
                    difficulty=band,
                    scene_profile="semantic_stress",
                )
                analysis = generator._inspect_scene(grid)
                self.assertEqual(analysis["scene_profile"], "semantic_stress")
                self.assertLess(len(set(analysis["colors"])), 3)
                self.assertIn(0, {value for row in analysis["output"] for value in row})
                authoritative = generator.rule_mirror(grid)
                for name in names:
                    with self.subTest(band=band, seed=seed, rival=name):
                        self.assertNotEqual(
                            generator.SEMANTIC_RIVALS[name](grid),
                            authoritative,
                        )

    def test_tie_profiles_make_both_secondary_keys_answer_bearing(self):
        expectations = {
            "column_tie": {"row_before_column_ties", "color_before_column_ties"},
            "color_tie": {"row_before_column_ties"},
        }
        for profile, rival_names in expectations.items():
            for band in ("easy", "medium", "hard"):
                for seed in range(12):
                    grid = generator.generate(
                        30_000 + seed,
                        seed,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    authoritative = generator.rule_mirror(grid)
                    self.assertEqual(
                        generator._inspect_scene(grid)["scene_profile"],
                        profile,
                    )
                    for name in rival_names:
                        with self.subTest(
                            profile=profile,
                            band=band,
                            seed=seed,
                            rival=name,
                        ):
                            self.assertNotEqual(
                                generator.SEMANTIC_RIVALS[name](grid),
                                authoritative,
                            )

    def test_every_default_four_example_window_refutes_every_competitor(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for start in range(20):
                seed = 40_000 + band_index * 100 + start
                demos = []
                for offset in range(generator.EXAMPLES_NEEDED):
                    grid = generator.generate(
                        seed,
                        start + offset,
                        difficulty=band,
                    )
                    demos.append(
                        {"input": grid, "output": generator.rule_mirror(grid)}
                    )
                for name, rival in generator.LESSON_COMPETITORS.items():
                    with self.subTest(band=band, start=start, rival=name):
                        self.assertFalse(
                            all(
                                rival(pair["input"]) == pair["output"]
                                for pair in demos
                            )
                        )
                self.assertEqual(
                    generator.lesson_identifiable(demos, demos[0]),
                    [],
                )

    def test_witness_claims_name_real_rival_disagreements(self):
        profiles = (
            "column_tie",
            "color_tie",
            "semantic_stress",
        )
        hits = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        for profile in profiles:
            for seed in range(24):
                grid = generator.generate(
                    50_000 + seed,
                    seed,
                    difficulty="hard",
                    scene_profile=profile,
                )
                authoritative = generator.rule_mirror(grid)
                for witness_name, witness in generator.SEMANTIC_WITNESSES.items():
                    if not witness(grid):
                        continue
                    hits[witness_name] += 1
                    rival_names = generator.WITNESS_RIVALS[witness_name]
                    self.assertTrue(
                        any(
                            generator.SEMANTIC_RIVALS[name](grid)
                            != authoritative
                            for name in rival_names
                        ),
                        witness_name,
                    )
        self.assertTrue(all(count > 0 for count in hits.values()), hits)


if __name__ == "__main__":
    unittest.main()
