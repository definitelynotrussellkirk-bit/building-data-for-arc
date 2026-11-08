from __future__ import annotations

import unittest
from reviewer_support import find_root, load_selected_generator, canonical_pairs

generator, SOURCE, SOURCE_HASH = load_selected_generator("dc155169ea57", root=find_root(__file__))

def projection_overlap(grid):
    line = next(r for r, row in enumerate(grid) if all(x == 2 for x in row))
    comps = generator._components(grid, 1, below=line)
    projections = [set(c for _, c in comp) for comp in comps]
    return any(a & b for i, a in enumerate(projections) for b in projections[i + 1:])

class TeachingContractTests(unittest.TestCase):
    def test_production_teaches_disconnected_projection_overlap(self):
        for band in ("easy", "medium", "hard"):
            grids = [generator.generate(17, i, difficulty=band) for i in range(20)]
            self.assertGreaterEqual(sum(map(projection_overlap, grids)), 10, band)
            self.assertTrue(all(not generator.self_check(g) for g in grids))

    def test_invalid_scalars_and_unknown_keys_reject(self):
        calls = [((True, 0), {}), ((1.0, 0), {}), (("1", 0), {}),
                 ((1, -1), {}), ((1, False), {}), ((1, 1.5), {}),
                 ((1, 0), {"difficulty": "expert"}),
                 ((1, 0), {"grid_h": 7.75}), ((1, 0), {"grid_w": "7"}),
                 ((1, 0), {"n_shapes": True}), ((1, 0), {"bogus": 1}),
                 ((1, 0), {"thin_frac": 10 ** 1000}), ((1, 0), {"thin_frac": True}), ((1, 0), {"thin_frac": float("nan")})]
        for args, kw in calls:
            with self.subTest(args=args, kw=kw):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(*args, **kw)

    def test_narrow_all_wide_default_remains_feasible(self):
        for i in range(15):
            grid = generator.generate(i, i, difficulty="hard", grid_w=7, thin_frac=0.0)
            self.assertEqual(len(grid[0]), 7)
            self.assertEqual(generator.self_check(grid), [])
            line = generator.observe_overrides(grid)["line_row"]
            comps = generator._components(grid, 1, below=line)
            self.assertTrue(all(generator._has_wide_row(c) for c in comps))

    def test_every_cyclic_lesson_and_rotation_refutes_projection_rival(self):
        rivals = getattr(generator, "LESSON_COMPETITORS", {})
        self.assertIn("projection_groups", rivals)
        for required in ("lowest_cell", "highest_support", "max_width"):
            self.assertIn(required, rivals)
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 1001):
                for start in range(4):
                    grids = [generator.generate(seed, start + i, difficulty=band) for i in range(4)]
                    self.assertEqual(len({str(g) for g in grids}), 4)
                    for name, rival in rivals.items():
                        separating = [rival(g) != generator.rule_mirror(g) for g in grids]
                        self.assertGreaterEqual(sum(separating), 2, (band, seed, start, name))
                        for query in range(4):
                            self.assertTrue(any(flag for i, flag in enumerate(separating) if i != query))

    def test_witness_slots_teach_all_confirmed_support_row_distinctions(self):
        # Independent rival: thin components still pass; wide bounding boxes
        # stop above the line. This must be refuted on both scheduled slots.
        def support_rival(grid, mode):
            line = next(r for r, row in enumerate(grid) if all(v == 2 for v in row))
            groups = generator._components(grid, 1, below=line)
            out = [row[:] for row in grid]
            holes = set()
            for shape in groups:
                for r, c in shape:
                    out[r][c] = 8
            for shape in groups:
                rows = {}
                for r, c in shape:
                    rows[r] = rows.get(r, 0) + 1
                is_wide = any(count > 1 for count in rows.values())
                wide_rows = [r for r, count in rows.items() if count > 1]
                anchor = max(rows)
                if is_wide and mode == "highest_support":
                    anchor = min(wide_rows)
                elif is_wide and mode == "max_width":
                    widest = max(rows.values())
                    anchor = max(r for r in wide_rows if rows[r] == widest)
                shift = (line - 1 if is_wide else len(grid) - 1) - anchor
                if not is_wide:
                    holes.update(c for r, c in shape)
                for r, c in shape:
                    out[r + shift][c] = 1
            for c in holes:
                out[line][c] = 8
            return out
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 14290206):
                for index in (0, 2):
                    grid = generator.generate(seed, index, difficulty=band)
                    for mode in ("lowest_cell", "highest_support", "max_width"):
                        with self.subTest(band=band, seed=seed, index=index, mode=mode):
                            self.assertNotEqual(generator.rule_mirror(grid), support_rival(grid, mode))

    def test_declared_shortcut_fits_all_canonical_pairs(self):
        rivals = getattr(generator, "CANONICAL_SHORTCUTS", {})
        self.assertIn("projection_groups", rivals)
        for name, rival in rivals.items():
            for pair in canonical_pairs(generator.TASK_ID, root=find_root(__file__)):
                self.assertEqual(rival(pair["input"]), pair["output"], name)

    def test_literal_disconnected_witness(self):
        grid = [[8] * 9 for _ in range(9)]
        grid[5] = [2] * 9
        grid[0][2] = 1
        grid[2][2:4] = [1, 1]
        expected = [[8] * 9 for _ in range(9)]
        expected[5] = [2, 2, 8, 2, 2, 2, 2, 2, 2]
        expected[4][2:4] = [1, 1]
        expected[8][2] = 1
        self.assertEqual(generator.rule_mirror(grid), expected)
        self.assertEqual(generator.self_check(grid), [])

if __name__ == "__main__":
    unittest.main()
