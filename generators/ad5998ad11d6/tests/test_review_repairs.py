"""Regression tests for the October 2026 review contract repairs."""
from __future__ import annotations

import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "ad5998ad11d6"
ROOT = find_root(__file__)


class ReviewRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module, cls.source, cls.source_sha256 = load_selected_generator(
            TASK_ID, root=ROOT
        )
        cls.pairs = canonical_pairs(TASK_ID, root=ROOT)

    def test_generate_rejects_nonliteral_or_out_of_domain_controls(self) -> None:
        invalid_calls = (
            {"seed": True, "sample_index": 0, "difficulty": "easy"},
            {"seed": 1.0, "sample_index": 0, "difficulty": "easy"},
            {"seed": "1", "sample_index": 0, "difficulty": "easy"},
            {"seed": 1, "sample_index": False, "difficulty": "easy"},
            {"seed": 1, "sample_index": 1.0, "difficulty": "easy"},
            {"seed": 1, "sample_index": "1", "difficulty": "easy"},
            {"seed": 1, "sample_index": -1, "difficulty": "easy"},
            {"seed": 1, "sample_index": 0, "difficulty": True},
            {"seed": 1, "sample_index": 0, "difficulty": 0},
            {"seed": 1, "sample_index": 0, "difficulty": 1.0},
            {"seed": 1, "sample_index": 0, "difficulty": "__invalid_difficulty__"},
        )
        for kwargs in invalid_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    self.module.generate(**kwargs)

    def test_canonical_shortcuts_are_exactly_the_canonical_fitting_rivals(self) -> None:
        self.assertEqual(
            set(self.module.CANONICAL_SHORTCUTS),
            {"rectangular_rooms_only"},
        )
        rival = self.module.CANONICAL_SHORTCUTS["rectangular_rooms_only"]
        for index, pair in enumerate(self.pairs):
            with self.subTest(index=index):
                self.assertEqual(rival(pair["input"]), pair["output"])

    def test_noncanonical_rivals_remain_lesson_competitors(self) -> None:
        self.assertEqual(
            set(self.module.LESSON_COMPETITORS),
            set(self.module.SEMANTIC_RIVALS),
        )
        self.assertTrue(
            set(self.module.LESSON_COMPETITORS)
            > set(self.module.CANONICAL_SHORTCUTS)
        )


if __name__ == "__main__":
    unittest.main()
