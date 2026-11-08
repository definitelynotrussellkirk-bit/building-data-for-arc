"""Reject malformed public call arguments before any random draw."""
import unittest

from reviewer_support import find_root, load_selected_generator


class TestCallContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator, _, _ = load_selected_generator(
            "1b2b9283b4ab", root=find_root(__file__))

    def test_seed_must_be_an_integer(self):
        for value in (True, False, 1.0, 1.75, "1", None):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.generator.generate(value, 0, difficulty="easy")

    def test_index_must_be_a_nonnegative_integer(self):
        for value in (True, False, 1.0, "1", -1, None):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.generator.generate(17, value, difficulty="easy")

    def test_difficulty_must_be_a_supported_band_or_none(self):
        for value in (True, False, 0, 1.0, "__invalid_difficulty__", [], {}):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.generator.generate(17, 0, difficulty=value)

    def test_valid_calls_include_negative_integer_seeds_and_none_band(self):
        for seed in (-17, 0, 17):
            for difficulty in (None, "easy", "medium", "hard"):
                with self.subTest(seed=seed, difficulty=difficulty):
                    grid = self.generator.generate(seed, 0, difficulty=difficulty)
                    self.assertEqual(self.generator.self_check(grid), [])
