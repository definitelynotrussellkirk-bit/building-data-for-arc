"""Behavioral tests for the separate denser/sparser authoring prototype."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

PROTO = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'


class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROTO.is_file():
            cls.prototype = None
            return
        spec = importlib.util.spec_from_file_location('cbf77_parametric', PROTO)
        cls.prototype = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.prototype)
        cls.bridge = cls.prototype.RacketBridge(timeout=10)

    @classmethod
    def tearDownClass(cls):
        if cls.prototype is not None:
            cls.bridge.close()

    def setUp(self):
        self.assertIsNotNone(self.prototype, 'parametric prototype is not implemented')
        self.p = self.prototype

    def test_default_is_exact_canonical_and_variant_only_changes_comparisons(self):
        original = self.p.canonical_program()
        self.assertEqual(self.p.program_for('denser'), original)
        expected = original.replace('(>= above below)', '(<= above below)').replace('(>= left right)', '(<= left right)')
        self.assertEqual(self.p.program_for('sparser'), expected)
        self.assertNotEqual(original, expected)

    def test_default_executes_every_canonical_pair(self):
        receipt = self.p.check_canonical(self.bridge)
        self.assertGreaterEqual(receipt['pair_count'], 3)
        self.assertEqual(receipt['matched'], receipt['pair_count'])

    def test_simple_witness_has_hand_computed_outputs(self):
        grid = [[0] * 11 for _ in range(9)]
        guide = {(4, c) for c in range(2, 9)}
        above = {(3, 3), (3, 4), (2, 4), (3, 5), (2, 5)}
        below = {(5, 7), (6, 7)}
        for r, c in guide: grid[r][c] = 4
        for r, c in above | below: grid[r][c] = 7
        for setting, side in [('denser', above), ('sparser', below)]:
            expected = [[0] * 11 for _ in range(9)]
            for r, c in guide: expected[r][c] = 4
            for r, c in side | {(8-r, c) for r, c in side}: expected[r][c] = 7
            self.assertEqual(self.p.execute(self.bridge, self.p.program_for(setting), grid), expected)

    def test_setting_draw_is_deterministic_without_global_rng_changes(self):
        before = random.getstate()
        selections = [self.p.select_setting(i) for i in range(32)]
        self.assertEqual(selections, [self.p.select_setting(i) for i in range(32)])
        self.assertEqual(set(selections), {'denser', 'sparser'})
        self.assertEqual(random.getstate(), before)

    def test_sampler_is_deterministic_distinct_and_parameter_independent(self):
        before = random.getstate()
        a = self.p.sample_inputs(17)
        self.assertEqual(a, self.p.sample_inputs(17))
        self.assertNotEqual(a, self.p.sample_inputs(18))
        grids = a['train'] + a['test']
        self.assertEqual(len({json.dumps(g) for g in grids}), 8)
        self.assertEqual(random.getstate(), before)

    def test_sampler_covers_both_orientations_and_sides_and_modal_conflict(self):
        for seed in (0, 1, 17, 42, 2**64 - 1):
            sampled = self.p.sample_inputs(seed)
            for split in ('train', 'test'):
                seen = set()
                for grid in sampled[split]:
                    analysis = self.p.base._analysis(grid)
                    self.assertEqual(analysis['errors'], [])
                    self.assertEqual(len(analysis['plans']), 1)
                    plan = analysis['plans'][0]
                    seen.add((plan['orientation'], plan['choose_negative']))
                    self.assertGreater(min(plan['negative_count'], plan['positive_count']), 0)
                    self.assertNotEqual(plan['negative_count'], plan['positive_count'])
                    index = 0 if plan['horizontal'] else 1
                    negative_total = sum(cell[index] < plan['axis'] for cell in plan['payload'])
                    positive_total = sum(cell[index] > plan['axis'] for cell in plan['payload'])
                    self.assertNotEqual(negative_total > positive_total, plan['choose_negative'])
                    for setting in self.p.SETTINGS:
                        out, clipped = self.p.python_prediction(grid, setting, with_clipped=True)
                        self.assertEqual(clipped, [])
                        self.assertNotEqual(out, grid)
                self.assertEqual(len(seen), 4)

    def test_separate_demo_and_query_counts(self):
        for demos, queries in ((4, 1), (6, 8), (12, 4)):
            sampled = self.p.sample_inputs(17, demo_count=demos, query_count=queries)
            self.assertEqual(len(sampled['train']), demos)
            self.assertEqual(len(sampled['test']), queries)
            self.assertEqual(len({json.dumps(g) for g in sampled['train'] + sampled['test']}), demos + queries)

    def test_invalid_seed_count_and_setting_values_rejected(self):
        for seed in (True, False, -1, 2**64, 1.0, '1', None):
            with self.subTest(seed=seed), self.assertRaises(ValueError): self.p.sample_inputs(seed)
            with self.subTest(draw_seed=seed), self.assertRaises(ValueError): self.p.select_setting(seed)
        for key, values in {'demo_count': [True, 3, 13, 4.0, '4'], 'query_count': [False, 0, 9, 4.0, '4'], 'attempt_limit': [True, 0, 513, '1']}.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.p.sample_inputs(17, **{key: value})
        for setting in ('other', '', True, None, 1):
            with self.subTest(setting=setting), self.assertRaises(ValueError): self.p.program_for(setting)

    def test_retry_exhaustion_is_explicit(self):
        fixed = self.p.sample_inputs(17)['train'][0]
        with patch.object(self.p, '_draw_input', return_value=deepcopy(fixed)):
            with self.assertRaisesRegex(ValueError, 'distinct'):
                self.p.sample_inputs(17, attempt_limit=2)

    def test_two_complete_racket_labelled_episodes_and_shortcut_certificates(self):
        self.episodes = [self.p.build_episode(17, side_policy=s, bridge=self.bridge) for s in self.p.SETTINGS]
        for ep in self.episodes:
            self.assertEqual(len(ep['train']), 4)
            self.assertEqual(len(ep['test']), 4)
            self.assertEqual(ep['certificate']['survivors'], ['setting:' + ep['side_policy']])
            self.assertEqual(ep['certificate']['query_identifiable'], [True] * 4)
            self.assertIn('horizontal_only', ep['certificate']['demo_mismatches'])
            self.assertTrue(ep['certificate']['demo_mismatches']['total_payload'])
            for pair in ep['train'] + ep['test']:
                self.assertEqual(pair['output'], self.p.execute(self.bridge, ep['program'], pair['input']))
        for split in ('train', 'test'):
            for a, b in zip(self.episodes[0][split], self.episodes[1][split]):
                self.assertEqual(a['input'], b['input'])
                self.assertNotEqual(a['output'], b['output'])

    def test_certificate_survivors_use_only_demonstrations(self):
        same = [[1]]; different = [[2]]
        predictions = {'chosen': [same, same, same], 'rival': [same, same, different]}
        cert = self.p.lesson_certificate(predictions, 2, 'chosen')
        self.assertEqual(cert['survivors'], ['chosen', 'rival'])
        self.assertEqual(cert['query_identifiable'], [False])
        predictions['rival'][2] = same
        again = self.p.lesson_certificate(predictions, 2, 'chosen')
        self.assertEqual(cert['survivors'], again['survivors'])
        self.assertEqual(again['query_identifiable'], [True])

    def test_public_identity_ignores_all_private_metadata_and_query_outputs(self):
        ep = self.p.build_episode(23, side_policy='denser', bridge=self.bridge)
        other = deepcopy(ep)
        other.update(seed=999, side_policy='sparser', program='private unrelated program', certificate={})
        for pair in other['test']: pair['output'] = [[9]]
        self.assertEqual(self.p.public_challenge_bytes(ep), self.p.public_challenge_bytes(other))
        self.assertEqual(self.p.public_challenge_id(ep), self.p.public_challenge_id(other))
        public = json.loads(self.p.public_challenge_bytes(ep))
        self.assertEqual(set(public), {'train', 'test'})
        self.assertTrue(all(set(p) == {'input'} for p in public['test']))
        self.assertTrue(all(set(p) == {'input', 'output'} for p in public['train']))

    def test_writer_sorts_public_ids_hashes_exact_bytes_and_rejects_duplicates(self):
        episodes = [self.p.build_episode(31, side_policy=s, bridge=self.bridge) for s in self.p.SETTINGS]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'export'
            manifest = self.p.write_batch(list(reversed(episodes)), out)
            ids = [row['public_id'] for row in manifest['episodes']]
            self.assertEqual(ids, sorted(ids))
            for row in manifest['episodes']:
                raw = (out / row['public_path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['public_id'])
                self.assertEqual(Path(row['public_path']).name, row['public_id'] + '.json')
            with self.assertRaises(FileExistsError): self.p.write_batch(episodes, out)
            dup = Path(tmp) / 'duplicate'
            with self.assertRaisesRegex(ValueError, 'duplicate'): self.p.write_batch([episodes[0], episodes[0]], dup)
            self.assertFalse(dup.exists())

    def test_grid_validation_rejects_bool_and_non_arc_shapes_before_execution(self):
        for grid in ([[True]], [[1.0]], [[-1]], [[10]], [], [[]], [[0], [0, 1]], [[0] * 31]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.p.execute(self.bridge, self.p.program_for('denser'), grid)

    def test_duplicate_visible_payload_with_different_private_data_is_rejected(self):
        episode = {'train': [{'input': [[0]], 'output': [[1]]}],
                   'test': [{'input': [[2]], 'output': [[3]]}], 'seed': 1}
        other = deepcopy(episode)
        other['seed'] = 2
        other['test'][0]['output'] = [[9]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'export'
            with self.assertRaisesRegex(ValueError, 'duplicate public challenge'):
                self.p.write_batch([episode, other], out)
            self.assertFalse(out.exists())

    def test_ties_decoys_and_canvas_boundary_execute_both_policies(self):
        grid = [[0] * 30 for _ in range(30)]
        for c in range(2, 9): grid[1][c] = 4
        grid[0][3] = grid[0][4] = 7
        grid[2][6] = grid[3][6] = 7
        grid[29][29] = 9
        outputs = [self.p.execute(self.bridge, self.p.program_for(s), grid) for s in self.p.SETTINGS]
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0][29][29], 9)
        self.assertEqual(outputs[0], self.p.base.rule_mirror(grid))


if __name__ == '__main__':
    unittest.main(verbosity=2)
