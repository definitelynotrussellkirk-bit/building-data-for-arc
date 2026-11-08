"""Source regressions for exact overrides and canonical shortcut declarations."""
from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "42a152269589"


def _load_generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


def _canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert pairs, "canonical labeled population must be available"
    return pairs


class TestReviewContracts(unittest.TestCase):
    def test_integer_overrides_reject_coercions_and_out_of_range(self):
        gen = _load_generator()
        for axis, valid, bounds in (("grid_h", 10, (10, 10)), ("grid_w", 12, (10, 13)), ("n_pieces", 4, (3, 5))):
            invalid_values = {
                "bool": True,
                "integral_float": float(valid),
                "fractional_float": valid + 0.75,
                "string": str(valid),
                "below": bounds[0] - 1,
                "above": bounds[1] + 1,
            }
            for kind, value in invalid_values.items():
                with self.subTest(axis=axis, kind=kind, supplied=value):
                    with self.assertRaises((TypeError, ValueError)):
                        gen.generate(313, 2, difficulty="hard", **{axis: value})

    def test_valid_exact_integers_and_none_sentinel_remain_supported(self):
        gen = _load_generator()
        grid = gen.generate(313, 2, difficulty="hard", grid_h=10, grid_w=12, n_pieces=4)
        self.assertEqual(gen.observe_overrides(grid), {"grid_h": 10, "grid_w": 12, "n_pieces": 4})
        self.assertEqual(gen.self_check(grid), [])
        self.assertEqual(gen.generate(313, 2, difficulty="hard", grid_w=None), gen.generate(313, 2, difficulty="hard"))

    def test_malformed_call_arguments_are_rejected_in_every_control_band(self):
        gen = _load_generator()
        invalid = {
            "seed": (True, False, 1.0, 1.75, "1"),
            "sample_index": (True, False, 1.0, 1.75, "1", -1),
            "difficulty": (True, False, 0, 1.0, "__invalid_difficulty__"),
        }
        for band in ("easy", None, "hard"):
            for argument, values in invalid.items():
                for value in values:
                    with self.subTest(argument=argument, value=value, value_type=type(value).__name__, band=band):
                        kwargs = {"seed": 991, "sample_index": 0, "difficulty": band}
                        kwargs[argument] = value
                        with self.assertRaises((TypeError, ValueError)):
                            gen.generate(**kwargs)

    def test_documented_call_arguments_remain_supported(self):
        gen = _load_generator()
        # Seeds are unrestricted integers; only sample_index must be nonnegative.
        for band in (None, "easy", "medium", "hard"):
            for seed, index in ((0, 0), (-7, 1), (2**80, 2)):
                with self.subTest(seed=seed, index=index, band=band):
                    grid = gen.generate(seed, index, difficulty=band)
                    self.assertEqual(gen.self_check(grid), [])

    def test_every_declared_canonical_shortcut_fits_every_labeled_variant(self):
        gen = _load_generator()
        pairs = _canonical_pairs()
        mismatches = {
            name: [i for i, pair in enumerate(pairs) if shortcut(pair["input"]) != pair["output"]]
            for name, shortcut in gen.CANONICAL_SHORTCUTS.items()
        }
        self.assertTrue(all(not indexes for indexes in mismatches.values()), mismatches)


if __name__ == "__main__":
    unittest.main()
