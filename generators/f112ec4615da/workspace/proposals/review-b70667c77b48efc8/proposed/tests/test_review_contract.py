from __future__ import annotations

import unittest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
)


TASK_ID = "f112ec4615da"
ROOT = find_root(__file__)
generator, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID,
    root=ROOT,
)


class StrictCallContractTests(unittest.TestCase):
    def test_seed_and_sample_index_require_plain_integers(self):
        invalid_seeds = (True, False, 1.0, 1.75, "1", None)
        for seed in invalid_seeds:
            with self.subTest(seed=seed):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(seed, 0)

        invalid_indices = (True, False, -1, 1.0, 1.75, "1", None)
        for sample_index in invalid_indices:
            with self.subTest(sample_index=sample_index):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, sample_index)

        self.assertEqual(generator.self_check(generator.generate(-7, 0)), [])
        self.assertEqual(generator.self_check(generator.generate(7, 3)), [])


class SemanticContractTests(unittest.TestCase):
    def test_declared_global_color_rank_shortcut_fits_every_canonical_pair(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 7)
        self.assertIn(
            "global_min_else_max",
            generator.CANONICAL_SHORTCUTS,
        )
        shortcut = generator.CANONICAL_SHORTCUTS["global_min_else_max"]
        for pair in pairs:
            with self.subTest(
                split=pair["split"],
                pair_index=pair["pair_index"],
            ):
                self.assertEqual(shortcut(pair["input"]), pair["output"])

    def test_every_generated_scene_refutes_the_declared_shortcut(self):
        shortcut = generator.SEMANTIC_RIVALS["global_min_else_max"]
        witness = generator.SEMANTIC_WITNESSES[
            "position_priority_refutes_global_color_rank"
        ]
        self.assertEqual(
            generator.WITNESS_RIVALS[
                "position_priority_refutes_global_color_rank"
            ],
            ["global_min_else_max"],
        )
        self.assertNotIn(
            "position_priority_refutes_global_color_rank",
            generator.BRANCH_WITNESSES,
        )
        self.assertEqual(
            set(generator.BRANCH_WITNESSES),
            {
                "all_zero_outcome_present",
                "tl_outcome_present",
                "br_outcome_present",
                "bl_outcome_present",
                "tr_outcome_present",
            },
        )

        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                grid = generator.generate(
                    seed,
                    seed * 41 + 13,
                    difficulty=band,
                )
                with self.subTest(band=band, seed=seed):
                    self.assertEqual(generator.strict_canonical_like(grid), [])
                    self.assertTrue(witness(grid))
                    self.assertNotEqual(
                        shortcut(grid),
                        generator.rule_mirror(grid),
                    )

    def test_lesson_hook_rejects_bad_labels_and_surviving_rival(self):
        pairs = []
        for index in range(generator.EXAMPLES_NEEDED + 1):
            grid = generator.generate(991, index, difficulty="medium")
            pairs.append(
                {"input": grid, "output": generator.rule_mirror(grid)}
            )
        demos = pairs[:-1]
        query = pairs[-1]
        self.assertEqual(generator.lesson_identifiable(demos, query), [])

        bad_demo = [dict(pair) for pair in demos]
        bad_demo[0] = {
            "input": demos[0]["input"],
            "output": [[0]],
        }
        self.assertTrue(generator.lesson_identifiable(bad_demo, query))

        canonical = canonical_pairs(TASK_ID, root=ROOT)
        ambiguous_demos = canonical[: generator.EXAMPLES_NEEDED]
        generated_query = pairs[-1]
        reasons = generator.lesson_identifiable(
            ambiguous_demos,
            generated_query,
        )
        self.assertTrue(
            any("global_min_else_max" in reason for reason in reasons),
            reasons,
        )


if __name__ == "__main__":
    unittest.main()
