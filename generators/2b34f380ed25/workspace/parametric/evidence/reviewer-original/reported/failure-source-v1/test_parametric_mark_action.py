"""Focused tests for the proposed task-local prototype; no production gate changes."""
import importlib.util
from pathlib import Path
import random
import unittest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('panel_parametric', HERE / 'workspace/parametric/prototype.py')
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class ParametricMarkActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P.ensure_tools()
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def apply(self, grid, setting):
        return P.execute(self.bridge, P.program_for(setting), grid)

    def test_default_exact_canonical_source_and_all_six_pairs(self):
        row = P.canonical_record()
        self.assertEqual(P.program_for(), row['program_solution'])
        pairs = row['train'] + row['test']
        self.assertEqual(len(pairs), 6)
        for pair in pairs:
            self.assertEqual(self.apply(pair['input'], P.DEFAULT), pair['output'])

    def test_only_two_partner_expressions_change(self):
        canonical = P.program_for()
        variant = P.program_for('reflection')
        self.assertEqual(variant.replace('(zip-lists lefts (reverse rights))', '(zip-lists lefts rights)').replace('(zip-lists tops (reverse bots))', '(zip-lists tops bots)'), canonical)

    def test_bad_parameters_fail_closed(self):
        for setting in ('flip', '', None, 1, True):
            with self.assertRaises(ValueError):
                P.program_for(setting)
        with self.assertRaises(ValueError):
            P.draw_inputs(True)

    def test_four_columns_distinguish_half_swap_and_reflection(self):
        grid = P.canvas([[2, 3, 6, 8], [8, 6, 3, 2]], vertical=1)
        swap = self.apply(grid, 'half_swap')
        reflect = self.apply(grid, 'reflection')
        self.assertEqual([swap[1][1+4*j] for j in range(4)], [6, 8, 2, 3])
        self.assertEqual([reflect[1][1+4*j] for j in range(4)], [8, 6, 3, 2])
        self.assertNotEqual(swap, reflect)

    def test_four_rows_distinguish_half_swap_and_reflection(self):
        grid = P.canvas([[2, 8], [3, 6], [6, 3], [8, 2]], horizontal=1)
        swap = self.apply(grid, 'half_swap')
        reflect = self.apply(grid, 'reflection')
        self.assertEqual([swap[1+4*j][1] for j in range(4)], [6, 8, 2, 3])
        self.assertEqual([reflect[1+4*j][1] for j in range(4)], [8, 6, 3, 2])

    def test_two_band_ambiguity_is_reported_honestly(self):
        grid = P.canvas([[2, 3], [6, 8]], vertical=0)
        self.assertEqual(self.apply(grid, 'half_swap'), self.apply(grid, 'reflection'))

    def test_fill_and_multicolor_preservation_are_invariant(self):
        grid = P.draw_inputs(17)[2]['input']
        swap = self.apply(grid, 'half_swap')
        self.assertEqual(swap, self.apply(grid, 'reflection'))
        self.assertNotEqual(grid, swap)
        self.assertEqual([line[:9] for line in grid], [line[:9] for line in swap])

    def test_draws_are_fresh_deterministic_bounded_and_rng_local(self):
        state = random.getstate()
        a, b = P.draw_inputs(17), P.draw_inputs(17)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(a, b)
        self.assertIsNot(a[0]['input'], b[0]['input'])
        self.assertNotEqual(a, P.draw_inputs(18))
        self.assertEqual([len(a[i]['input']) for i in (3, 4)], [30, 30])
        self.assertTrue(all(9 <= len(x['input']) <= 30 and 9 <= len(x['input'][0]) <= 30 for x in a))

    def test_fixed_rule_and_public_private_separation(self):
        for setting in P.SETTINGS:
            episode = P.episode(self.bridge, 17, setting)
            self.assertEqual(episode['parameters'], {'mark_action': setting})
            self.assertEqual(len(episode['train']), 3)
            self.assertEqual(len(episode['test']), 2)
            self.assertEqual(episode['rivals']['consistent_settings'], [setting])
            self.assertEqual(episode['rivals']['rival_demo_mismatches'], [0, 1])
            public = P.public_challenge(episode)
            self.assertEqual(set(public), {'train', 'test'})
            self.assertTrue(all(set(x) == {'input'} for x in public['test']))
            self.assertEqual(public['train'], episode['train'])
            public['train'][0]['input'][0][0] = 7
            self.assertNotEqual(public['train'], episode['train'])

    def test_seed_selection_is_once_per_episode(self):
        self.assertEqual({P.select_setting(seed) for seed in range(20)}, set(P.SETTINGS))
        for seed in range(20):
            self.assertEqual(P.select_setting(seed), P.select_setting(seed))


if __name__ == '__main__':
    unittest.main(verbosity=2)
