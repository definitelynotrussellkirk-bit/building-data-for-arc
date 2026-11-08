"""Regression checks for call contracts and finite rotating lesson support."""
from collections import Counter
import unittest

from reviewer_support import find_root, load_selected_generator

GEN, _, _ = load_selected_generator("9c3781759581", root=find_root(__file__))


def expected_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def frequency_shortcut(grid, *, even):
    counts = Counter(v for row in grid for v in row if v != 0)
    eligible = [v for v, n in counts.items() if (n % 2 == 0 if even else n > 1)]
    color = min(eligible or counts, key=lambda v: (counts[v], -v))
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


class LessonContractTests(unittest.TestCase):
    def test_call_arguments_reject_coercions_and_unknown_difficulty(self):
        for seed in (True, False, 1.0, 1.75, "1"):
            with self.subTest(seed=seed), self.assertRaises((TypeError, ValueError)):
                GEN.generate(seed, 0)
        for index in (True, False, 1.0, 1.75, "1", -1):
            with self.subTest(index=index), self.assertRaises((TypeError, ValueError)):
                GEN.generate(17, index)
        for band in (True, False, 0, 1.0, "unknown", [], {}):
            with self.subTest(difficulty=band), self.assertRaises((TypeError, ValueError)):
                GEN.generate(17, 0, difficulty=band)

    def test_marker_frequency_rank_is_not_fixed(self):
        for band in ("easy", "medium", "hard"):
            ranks = set()
            for index in range(24):
                grid = GEN.generate(17, index, difficulty=band)
                counts = Counter(v for row in grid for v in row if v != 0)
                order = sorted(counts, key=lambda v: (counts[v], v), reverse=True)
                ranks.add(order.index(9) + 1)
            with self.subTest(band=band):
                self.assertIn(1, ranks)
                self.assertIn(2, ranks)

    def test_frequency_shortcuts_are_refuted_in_every_demonstration_set(self):
        # Positive refutation is essential: a rival fitting all five pairs
        # would pass an ambiguity-only check. These two rivals fit the original
        # canonical labels and all 48 inputs in the retained v3.0.1 review probe.
        for band in (None, "easy", "medium", "hard"):
            for seed in (0, 17, 20261019):
                for start in range(GEN.LESSON_SCHEDULE_PERIOD):
                    grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(5)]
                    for even in (False, True):
                        refutes = [frequency_shortcut(g, even=even) != expected_crop(g) for g in grids]
                        for query in range(5):
                            with self.subTest(band=band, seed=seed, start=start, even=even, query=query):
                                self.assertTrue(any(refutes[i] for i in range(5) if i != query))

    def test_every_declared_start_supports_all_five_query_positions(self):
        # A finite regression on three seeds. Production Racket census is retained
        # separately; this check is a cheap schedule/semantic-rival smoke test.
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 20261019):
                for start in range(GEN.LESSON_SCHEDULE_PERIOD):
                    grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(5)]
                    labels = [expected_crop(grid) for grid in grids]
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        agrees = [rival(grid) == label for grid, label in zip(grids, labels)]
                        for query in range(5):
                            ambiguous = not agrees[query] and all(
                                agrees[i] for i in range(5) if i != query)
                            with self.subTest(band=band, seed=seed, start=start,
                                              rival=name, query=query):
                                self.assertFalse(ambiguous)


if __name__ == "__main__":
    unittest.main()
