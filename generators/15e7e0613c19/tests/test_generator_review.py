"""Portable source-bound tests for the gallery generator repair."""
from copy import deepcopy
from collections import Counter
import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator('15e7e0613c19', root=ROOT)


class GalleryRepairTests(unittest.TestCase):
    def test_canonical_mirror_all_three_pairs_and_pinned_hash(self):
        self.assertEqual(getattr(GEN, 'RULE_HASH', None), '1f1935df6364')
        pairs = canonical_pairs('15e7e0613c19', root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            original = deepcopy(pair['input'])
            self.assertEqual(GEN.solve_reference(pair['input']), pair['output'])
            self.assertEqual(GEN.self_check(pair['input']), [])
            self.assertEqual(GEN.strict_canonical_like(pair['input']), [])
            self.assertEqual(pair['input'], original)
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                with self.subTest(rival=name):
                    self.assertEqual(rival(pair['input']), pair['output'])

    def test_racket_verified_bbox_counterexample(self):
        # Fixed canonical Racket receipt: 3e34a0b3d6acabfc436c5a79b45c225583f8d38d8900b1643430a5ecbc0f99bb.
        grid = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 4], [0, 0, 0, 0, 0, 0, 0, 0, 0, 4], [0, 0, 0, 0, 0, 0, 0, 0, 0, 4], [0, 0, 0, 0, 6, 0, 0, 0, 0, 4], [0, 0, 2, 0, 0, 0, 0, 0, 0, 4], [0, 0, 2, 0, 0, 0, 0, 0, 0, 0], [0, 0, 2, 2, 0, 0, 0, 0, 0, 0]]
        output = [[6, 0, 2, 0, 0, 4], [0, 0, 2, 0, 0, 4], [0, 0, 2, 2, 0, 4], [0, 0, 0, 0, 0, 4], [0, 0, 0, 0, 0, 4]]
        self.assertEqual(GEN.generate(0, 0, difficulty="medium"), grid)
        self.assertEqual(GEN.self_check(grid), [])
        self.assertEqual(GEN.solve_reference(grid), output)
        self.assertNotEqual(GEN.rival_bbox_area(grid), output)

    def test_malformed_grids_rejected_without_mutation(self):
        cases = [None, [], [[]], [[0], [0, 1]], [[False, 0]], [[1.0, 0]],
                 [[-1, 0]], [[10, 0]], ['00'], [[0] * 31], [[0] * 9 for _ in range(7)],
                 [[2] * 9 for _ in range(7)]]
        for grid in cases:
            original = deepcopy(grid)
            with self.subTest(grid=grid):
                self.assertTrue(GEN.self_check(grid))
                self.assertEqual(grid, original)

    def test_unknown_and_invalid_controls_fail_loudly(self):
        for kwargs in [{'typo': 2}, {'grid_h': 6}, {'grid_w': 17}, {'n': 1},
                       {'n': True}, {'n': 2.0}, {'n': None}, {'palette_size': 1},
                       {'palette_size': 3, 'n_distinct_colors': 4},
                       {'n': 2, 'n_distinct_colors': 4}, {'texture': 'no_motifs'}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                GEN.generate(0, 0, **kwargs)

    def test_exact_controls_including_repeated_color_corners(self):
        for h, w in [(7, 9), (7, 16), (14, 9), (14, 16)]:
            for n in range(2, 6):
                for colors in range(2, n + 2):
                    kwargs = {'grid_h': h, 'grid_w': w, 'n': n,
                              'n_distinct_colors': colors, 'palette_size': colors}
                    grid = GEN.generate(71, n + colors, **kwargs)
                    self.assertEqual(GEN.self_check(grid), [], kwargs)
                    self.assertEqual(GEN.observe_overrides(grid), kwargs)
                    self.assertEqual(GEN.generate(71, n + colors, **kwargs), grid)
                    out = GEN.solve_reference(grid)
                    self.assertLessEqual(max(len(out), len(out[0])), 30)

    def test_default_support_and_deterministic_stress(self):
        all_foreground = set()
        border_hit = False
        broad_shapes = set()
        for band in ['easy', 'medium', 'hard']:
            profiles = Counter()
            for i in range(180):
                grid = GEN.generate(2026, i, difficulty=band)
                original = deepcopy(grid)
                self.assertEqual(GEN.self_check(grid), [], (band, i))
                observed = GEN.observe_overrides(grid)
                profiles[len(grid), len(grid[0]), observed['n_distinct_colors']] += 1
                self.assertEqual(grid, GEN.generate(2026, i, difficulty=band))
                self.assertEqual(grid, original)
                output = GEN.solve_reference(grid)
                self.assertLess(len(output), len(grid), (band, i, "height must shrink"))
                self.assertLess(len(output[0]), len(grid[0]), (band, i, "width must shrink"))
                all_foreground.update(v for row in grid for v in row if v)
                border_hit |= any(grid[0]) or any(grid[-1]) or any(row[0] or row[-1] for row in grid)
                if (len(grid), len(grid[0])) not in {(7, 9), (7, 10), (8, 11)}:
                    broad_shapes.add((len(grid), len(grid[0])))
            for profile in [(7, 9, 4), (7, 10, 4), (8, 11, 4)]:
                self.assertGreater(profiles[profile], 0, (band, profile))
        self.assertEqual(all_foreground, set(range(1, 10)))
        self.assertTrue(border_hit)
        self.assertGreater(len(broad_shapes), 12)

    def test_every_schedule_rotation_teaches_declared_rivals(self):
        fired = Counter()
        for band in ['easy', 'medium', 'hard']:
            for seed in [0, 19, 2026]:
                for start in range(3):
                    pairs = []
                    for index in range(start, start + 6):
                        grid = GEN.generate(seed, index, difficulty=band)
                        pairs.append({'input': grid, 'output': GEN.solve_reference(grid)})
                        for name, witness in GEN.SEMANTIC_WITNESSES.items():
                            if witness(grid):
                                fired[name] += 1
                                self.assertTrue(any(GEN.SEMANTIC_RIVALS[r](grid) != pairs[-1]['output']
                                                    for r in GEN.WITNESS_RIVALS[name]))
                    for query_index in range(6):
                        demos = [p for j, p in enumerate(pairs) if j != query_index]
                        self.assertEqual(GEN.lesson_identifiable(demos, pairs[query_index]), [])
                        for name, rival in GEN.LESSON_COMPETITORS.items():
                            self.assertTrue(any(rival(p['input']) != p['output'] for p in demos),
                                            (band, seed, start, query_index, name))
        self.assertEqual(set(fired), set(GEN.SEMANTIC_WITNESSES))

    def test_ambiguity_hook_detects_a_surviving_competitor(self):
        canonical = canonical_pairs('15e7e0613c19', root=ROOT, labeled_only=True)
        grid = GEN.generate(0, 0)
        query = {'input': grid, 'output': GEN.solve_reference(grid)}
        self.assertTrue(GEN.lesson_identifiable(canonical, query))


if __name__ == '__main__':
    unittest.main()
