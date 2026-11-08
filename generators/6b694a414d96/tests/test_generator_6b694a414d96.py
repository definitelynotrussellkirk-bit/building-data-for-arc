from __future__ import annotations

from importlib import import_module
import unittest

from reviewer_support import canonical_pairs, find_root


generator = import_module(
    "puzzle_generators.per_puzzle.6b694a414d96.generator"
)


class Generator6b694a414d96Tests(unittest.TestCase):
    def test_all_canonical_pairs_are_positive_controls(self):
        pairs = canonical_pairs(
            generator.TASK_ID,
            root=find_root(__file__),
            labeled_only=True,
        )
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            with self.subTest(
                split=pair["split"],
                pair_index=pair["pair_index"],
            ):
                self.assertEqual(generator.self_check(pair["input"]), [])
                self.assertEqual(
                    generator.rule_mirror(pair["input"]),
                    pair["output"],
                )


    def test_generated_grids_are_valid_in_every_band(self):
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(24):
                grid = generator.generate(700 + sample_index, sample_index, difficulty=difficulty)
                with self.subTest(difficulty=difficulty, sample_index=sample_index):
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertLessEqual(len(grid), 30)
                    self.assertLessEqual(len(grid[0]), 30)
                    self.assertEqual(len({len(row) for row in grid}), 1)
                    self.assertNotEqual(generator.rule_mirror(grid), grid)



    def test_three_slot_schedule_covers_both_orientations_and_second_hop(self):
        self.assertTrue(hasattr(generator, "SCHEDULE_PROFILES"))
        self.assertTrue(hasattr(generator, "schedule_profile"))
        self.assertEqual(
            generator.SCHEDULE_PROFILES,
            ("horizontal", "vertical", "second_hop"),
        )
        self.assertEqual(generator.EXAMPLES_NEEDED, 3)
        for start in range(9):
            observed = {
                generator.schedule_profile(17, start + offset, "medium")
                for offset in range(generator.EXAMPLES_NEEDED)
            }
            self.assertEqual(observed, set(generator.SCHEDULE_PROFILES))

    def test_declared_axes_have_exact_override_support(self):
        cases = {
            "rooms_r": (2, 4),
            "rooms_c": (2, 5),
            "room_h": (2, 5),
            "room_w": (2, 4),
            "wall_color": (1, 9),
        }
        self.assertEqual(set(generator.AXES), set(cases))
        for axis, values in cases.items():
            for value in values:
                grid = generator.generate(
                    90_000 + value,
                    11,
                    difficulty="hard",
                    **{axis: value},
                )
                with self.subTest(axis=axis, value=value):
                    self.assertEqual(generator.self_check(grid), [])
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(observed[axis], value)

    def test_canonical_fitting_transitive_shortcut_is_declared(self):
        self.assertTrue(hasattr(generator, "CANONICAL_SHORTCUTS"))
        self.assertEqual(set(generator.CANONICAL_SHORTCUTS), {"transitive_closure"})
        pairs = canonical_pairs(
            generator.TASK_ID,
            root=find_root(__file__),
            labeled_only=True,
        )
        shortcut = generator.CANONICAL_SHORTCUTS["transitive_closure"]
        self.assertTrue(
            all(shortcut(pair["input"]) == pair["output"] for pair in pairs)
        )

    def test_every_default_window_refutes_every_declared_competitor(self):
        self.assertTrue(hasattr(generator, "LESSON_COMPETITORS"))
        for difficulty in ("easy", "medium", "hard"):
            for start in range(12):
                seed = 120_000 + start
                demos = []
                for offset in range(generator.EXAMPLES_NEEDED):
                    grid = generator.generate(
                        seed,
                        start + offset,
                        difficulty=difficulty,
                    )
                    demos.append(
                        {"input": grid, "output": generator.rule_mirror(grid)}
                    )
                for name, rival in generator.LESSON_COMPETITORS.items():
                    with self.subTest(
                        difficulty=difficulty,
                        start=start,
                        rival=name,
                    ):
                        self.assertFalse(
                            all(
                                rival(pair["input"]) == pair["output"]
                                for pair in demos
                            )
                        )
                self.assertEqual(generator.lesson_identifiable(demos, demos[0]), [])

    def test_second_hop_profile_changes_transitive_closure_answer(self):
        self.assertTrue(hasattr(generator, "SEMANTIC_RIVALS"))
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(18):
                sample_index = next(
                    index
                    for index in range(3)
                    if generator.schedule_profile(seed, index, difficulty)
                    == "second_hop"
                )
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                with self.subTest(difficulty=difficulty, seed=seed):
                    self.assertNotEqual(
                        generator.SEMANTIC_RIVALS["transitive_closure"](grid),
                        generator.rule_mirror(grid),
                    )



if __name__ == "__main__":
    unittest.main()
