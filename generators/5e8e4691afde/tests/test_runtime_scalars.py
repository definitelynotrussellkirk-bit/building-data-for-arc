"""Public recipe scalar regressions; runnable with stdlib unittest."""
from __future__ import annotations

import unittest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator("5e8e4691afde", root=ROOT)


class RuntimeScalarTests(unittest.TestCase):
    def test_retained_33_invalid_recipe_calls_are_rejected(self):
        for difficulty in (None, "easy", "hard"):
            for field, values in (
                ("seed", (True, False, 1.0, 1.75, "1")),
                ("sample_index", (True, False, 1.0, 1.75, "1", -1)),
            ):
                for value in values:
                    with self.subTest(difficulty=difficulty, field=field, value=value):
                        arguments = dict(seed=0, sample_index=0, difficulty=difficulty)
                        arguments[field] = value
                        with self.assertRaises((TypeError, ValueError)):
                            GENERATOR.generate(**arguments)

    def test_missing_container_and_integer_subclass_values_rejected(self):
        class IntegerSubclass(int):
            pass

        for field in ("seed", "sample_index"):
            for value in (None, [], {}, IntegerSubclass(1)):
                with self.subTest(field=field, value=value):
                    arguments = dict(seed=0, sample_index=0)
                    arguments[field] = value
                    with self.assertRaises((TypeError, ValueError)):
                        GENERATOR.generate(**arguments)

    def test_valid_signed_seeds_and_nonnegative_indices(self):
        for seed in (-1, 0, 1, 2**100):
            for index in (0, 1, 2**100):
                with self.subTest(seed=seed, index=index):
                    grid = GENERATOR.generate(seed, index, scene_profile="public_train_1")
                    self.assertEqual(GENERATOR.self_check(grid), [])


if __name__ == "__main__":
    unittest.main()
