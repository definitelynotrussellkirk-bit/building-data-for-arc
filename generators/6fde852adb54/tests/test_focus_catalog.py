"""Focused tests for the proposed d8e07eb2-inspired catalog extension."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
SOURCE = HERE.parents[1] / 'workspace/parametric/focus_catalog.py'
spec = importlib.util.spec_from_file_location('focus_catalog', SOURCE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class FocusCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = m.RacketOracle()
        cls.episodes = {mode: m.generate_episode(seed=17, alignment_mode=mode,
                         n_train=3, n_test=4, oracle=cls.oracle) for mode in m.ALIGNMENTS}

    @classmethod
    def tearDownClass(cls):
        print('RACKET_TEST_EVALUATIONS=' + str(cls.oracle.evaluations))
        cls.oracle.close()

    def test_01_numeric_and_parameter_validation(self):
        for name, values in {'seed': [True, 1.0, '2', -1, 2**64],
              'n_train': [False, 1.0, '3', 0, 17], 'n_test': [True, 2.5, '4', 0, 17],
              'max_attempts': [True, 1.0, '3', 0, 4097]}.items():
            for value in values:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    m.generate_episode(oracle=self.oracle, **{name: value})
        for value in [None, 1, True, 'diagonal']:
            with self.assertRaises(ValueError):
                m.materialize_program(value)

    def test_02_rule_changes_and_declared_partial_boundary(self):
        rng = random.Random(71)
        for scenario in ['row', 'column', 'mixed', 'partial']:
            grid, info = m.sample_scene(rng, scenario)
            for mode in m.ALIGNMENTS:
                out = m.python_apply(grid, mode)
                expected = scenario in ({'row', 'column'} if mode == 'row_or_column'
                           else {'row'} if mode == 'row_only' else {'column'})
                self.assertEqual(out[-1], [3 if expected else 2] * len(out[0]))
                self.assertEqual(out, self.oracle.apply(mode, grid))
        self.assertEqual(len(set(m.materialize_program(k) for k in m.MODELS)), len(m.MODELS))

    def test_03_public_five_examples_and_unpatched_discrepancy(self):
        result = m.analyze_public(self.oracle)
        self.assertEqual(result['exact_train_matches'], [False, True, True, True, True])
        self.assertEqual([len(x['differences']) for x in result['train']], [9, 0, 0, 0, 0])
        self.assertEqual({(d[0], d[1]) for d in result['train'][0]['differences']},
                         {(r, c) for r in range(1, 4) for c in range(7, 10)})
        self.assertEqual(result['train'][0]['header_input_coordinates'], [[1,3],[1,1],[1,0],[1,2]])
        self.assertEqual(result['train'][0]['header_output_coordinates'], [[1,3],[2,1],[1,0],[1,2]])
        self.assertEqual([p['output_sha256'] for p in result['test_hypotheses']], [
            '640ac61bac7bc004320f62e6b2f9c57e323548743e571d19246cb7896e99ca94',
            'e1597882191b79b7822bc2ac72c6e6705604a4f79b5521698aa8aa38ef6568ac'])

    def test_04_reproducibility_and_distinct_queries(self):
        for mode, episode in self.episodes.items():
            again = m.generate_episode(seed=17, alignment_mode=mode, n_train=3, n_test=4, oracle=self.oracle)
            self.assertEqual(episode, again)
            pairs = episode['train'] + episode['test']
            self.assertEqual((len(episode['train']), len(episode['test'])), (3, 4))
            self.assertEqual(len({m.grid_digest(p['input']) for p in pairs}), 7)
            for pair in pairs:
                self.assertEqual(pair['output'], self.oracle.apply(mode, pair['input']))

    def test_05_counts_and_explicit_insufficient_demonstrations(self):
        for count in [1, 2]:
            with self.assertRaises(m.InsufficientDemonstrations):
                m.generate_episode(seed=5, n_train=count, n_test=4, oracle=self.oracle)
        for mode in ['row_only', 'column_only']:
            ep = m.generate_episode(seed=101, alignment_mode=mode, n_train=1, n_test=2, oracle=self.oracle)
            self.assertEqual((len(ep['train']), len(ep['test'])), (1, 2))
            self.assertEqual(ep['certificate']['surviving_models'], [mode])

    def test_06_certificate_has_demo_only_eliminations(self):
        for mode, ep in self.episodes.items():
            cert = ep['certificate']
            self.assertEqual(cert['surviving_models'], [mode])
            self.assertEqual(len(cert['queries']), 4)
            self.assertEqual(set(cert['eliminated_models']), set(m.MODELS) - {mode})
            self.assertTrue(all(row['demonstration_indices'] for row in cert['eliminated_models'].values()))
            self.assertTrue(all(q['prediction_agreement'] for q in cert['queries']))
        default = self.episodes['row_or_column']
        abbreviated = copy.deepcopy(default)
        abbreviated['train'] = abbreviated['train'][:2]
        self.assertIn('any_complete_count', m.certify(abbreviated, self.oracle)['surviving_models'])

    def test_07_query_answers_and_private_metadata_not_certificate_inputs(self):
        ep = copy.deepcopy(self.episodes['row_or_column'])
        original = m.certify(ep, self.oracle)
        ep['seed'] = 999
        ep['params'] = {'alignment_mode': 'nonsense'}
        for p in ep['test']:
            p['output'] = [[9]]
        self.assertEqual(m.certify(ep, self.oracle), original)

    def test_08_public_bytes_ids_and_sorted_export(self):
        episodes = list(self.episodes.values())
        with tempfile.TemporaryDirectory() as td:
            manifest = m.write_export(episodes, Path(td) / 'batch', self.oracle)
            self.assertEqual(manifest['public_ids'], sorted(manifest['public_ids']))
            for ep in episodes:
                cid = m.public_challenge_id(ep)
                actual = (Path(td) / 'batch/public' / (cid + '.json')).read_bytes()
                self.assertEqual(actual, m.public_challenge_bytes(ep))
                public = json.loads(actual)
                self.assertEqual(set(public), {'train', 'test'})
                self.assertTrue(all(set(p) == {'input'} for p in public['test']))
                self.assertEqual(set(public['train'][0]), {'input','output'})
            mutated = copy.deepcopy(episodes[0])
            mutated['seed'] = 999
            mutated['params'] = {'alignment_mode': 'different'}
            mutated['certificate'] = {'private': True}
            mutated['test'][0]['output'] = [[0]]
            self.assertEqual(m.public_challenge_id(mutated), m.public_challenge_id(episodes[0]))
            self.assertEqual(m.public_challenge_bytes(mutated), m.public_challenge_bytes(episodes[0]))

    def test_09_duplicate_visible_export_rejected_before_write(self):
        ep = self.episodes['row_only']
        other = copy.deepcopy(ep)
        other['seed'] = 12345
        other['test'][0]['output'] = [[1]]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'rejected'
            with self.assertRaises(ValueError):
                m.write_export([ep, other], out, self.oracle)
            self.assertFalse(out.exists())

    def test_10_bounded_retry_exhaustion(self):
        fixed = m.sample_scene(random.Random(33), 'column')
        with mock.patch.object(m, 'sample_scene', return_value=fixed) as sampler:
            with self.assertRaises(m.SamplingExhausted) as error:
                m.generate_episode(seed=33, alignment_mode='row_only', n_train=1, n_test=1,
                                   max_attempts=3, oracle=self.oracle)
            self.assertEqual(sampler.call_count, 3)
            self.assertIn('3', str(error.exception))

    def test_11_malformed_grid_rejection(self):
        inp = self.episodes['row_only']['train'][0]['input']
        for bad in [[], [[True]], [[8],[8,8]], [[10]], [[8]*22 for _ in range(30)]]:
            with self.assertRaises(ValueError):
                m.python_apply(bad)
        mutated = copy.deepcopy(inp)
        mutated[1][2] = 3
        with self.assertRaises(ValueError):
            m.python_apply(mutated)

    def test_12_header_to_catalog_dependency_intervention(self):
        witness = m.dependency_witness(self.episodes['row_or_column'], self.oracle)
        before, after = witness['before'], witness['after']
        self.assertEqual(before['input'][:5], after['input'][:5])
        self.assertEqual(set(before['output'][-1]), {3})
        self.assertEqual(set(after['output'][-1]), {2})
        self.assertNotEqual(witness['before_coordinates'], witness['after_coordinates'])
        self.assertEqual(m.python_apply(after['input']), after['output'])

    def test_13_private_numeric_labels_and_untrusted_certificate(self):
        original = self.episodes['row_only']
        for bad_type in ('float', 'bool'):
            ep = copy.deepcopy(original)
            output = ep['test'][0]['output']
            if bad_type == 'float':
                output[0][0] = float(output[0][0])
            else:
                r,c = next((r,c) for r,row in enumerate(output) for c,v in enumerate(row) if v in (0,1))
                output[r][c] = bool(output[r][c])
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / 'bad'
                with self.assertRaises(ValueError):
                    m.write_export([ep], out, self.oracle)
                self.assertFalse(out.exists())
        ep = copy.deepcopy(original)
        ep['certificate'] = {'surviving_models':['made_up'], 'uses_query_answers':True}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'good'
            m.write_export([ep], out, self.oracle)
            private = json.loads((out / 'private' / (m.public_challenge_id(ep)+'.json')).read_text())
            self.assertEqual(private['certificate'], m.certify(ep,self.oracle))
            self.assertFalse(private['certificate']['uses_query_answers'])

    def test_14_real_cli(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'cli'
            completed = subprocess.run([sys.executable, str(SOURCE), '--seed', '61', '--settings',
                'row_only', '--train', '1', '--test', '1', '--out', str(out)],
                text=True, capture_output=True, timeout=120)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads((out / 'export.json').read_text())
            self.assertEqual(len(receipt['public_ids']), 1)
            self.assertGreaterEqual(receipt['racket_evaluations'], len(m.MODELS) * 2)
            self.assertTrue(receipt['runtime']['protected'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
