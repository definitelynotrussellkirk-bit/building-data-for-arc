"""Regression tests for the October 2026 review repair."""
from __future__ import annotations

import hashlib
import unittest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "b9b63ae52d91"


def _horizontal_rule(grid):
    width = len(grid[0])
    return [
        [
            2 if value == 8 and row[width - 1 - col] == 8 else
            5 if value == 8 else 0
            for col, value in enumerate(row)
        ]
        for row in grid
    ]


def _vertical_rule(grid):
    height = len(grid)
    return [
        [
            2 if value == 8 and grid[height - 1 - row][col] == 8 else
            5 if value == 8 else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def _profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


class ReviewRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module, _, _ = load_selected_generator(
            TASK_ID, root=find_root(__file__)
        )

    def test_seed_and_sample_index_are_strict_nonnegative_integers(self):
        bad_values = (True, False, 1.0, 1.75, "1", -1)
        for name in ("seed", "sample_index"):
            for bad in bad_values:
                kwargs = {"seed": 9, "sample_index": 0}
                kwargs[name] = bad
                with self.subTest(name=name, value=bad):
                    with self.assertRaisesRegex(
                        ValueError, rf"{name} must be a nonnegative integer"
                    ):
                        self.module.generate(**kwargs, difficulty="easy")

    def test_pinned_profile_floor_has_per_band_and_pooled_support(self):
        total = 0
        for band in ("easy", "medium", "hard"):
            hits = 0
            for index in range(20):
                seed = _profile_seed(band, index)
                sample_index = seed % 7919 + index
                grid = self.module.generate(
                    seed, sample_index, difficulty=band
                )
                profile = (
                    len(grid), len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                if profile == (6, 6, 2):
                    hits += 1
            self.assertGreaterEqual(hits, 1, band)
            total += hits
        self.assertGreaterEqual(total, 15)

    def test_semantic_contract_declares_and_proves_horizontal_rival(self):
        self.assertTrue(callable(self.module.strict_canonical_like))
        self.assertIn("horizontal_mirror", self.module.SEMANTIC_RIVALS)
        self.assertIn("horizontal_mirror", self.module.LESSON_COMPETITORS)
        self.assertIn(
            "horizontal_mirror",
            self.module.WITNESS_RIVALS["vertical_not_horizontal"],
        )
        witness = self.module.SEMANTIC_WITNESSES["vertical_not_horizontal"]
        candidate = next(
            self.module.generate(
                8101, index, difficulty="medium",
                scene_family="generalized",
            )
            for index in range(200)
            if _vertical_rule(
                self.module.generate(
                    8101, index, difficulty="medium",
                    scene_family="generalized",
                )
            ) != _horizontal_rule(
                self.module.generate(
                    8101, index, difficulty="medium",
                    scene_family="generalized",
                )
            )
        )
        self.assertEqual(self.module.strict_canonical_like(candidate), [])
        self.assertTrue(witness(candidate))
        self.assertEqual(
            self.module.SEMANTIC_RIVALS["horizontal_mirror"](candidate),
            _horizontal_rule(candidate),
        )
        self.assertNotEqual(_vertical_rule(candidate), _horizontal_rule(candidate))

    def test_lesson_identifiable_detects_horizontal_mirror_ambiguity(self):
        blank = [[0] * 5 for _ in range(5)]
        query_input = [[0] * 5 for _ in range(5)]
        query_input[0][1] = 8
        query_input[4][1] = 8
        demos = [{"input": blank, "output": _vertical_rule(blank)}]
        query = {
            "input": query_input,
            "output": _vertical_rule(query_input),
        }
        reasons = self.module.lesson_identifiable(demos, query)
        self.assertTrue(reasons)
        self.assertIn("horizontal", " ".join(reasons).lower())
        self.assertEqual(
            self.module.lesson_identifiable([query], query), []
        )


if __name__ == "__main__":
    unittest.main()
