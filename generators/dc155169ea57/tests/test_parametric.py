"""Proposed capacity prototype only; canonical generator coverage stays separate."""
from __future__ import annotations

import importlib.util
import hashlib
import io
from contextlib import redirect_stdout
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
from pathlib import Path

import unittest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / 'workspace' / 'parametric' / 'prototype.py'


def load_prototype():
    assert PROTOTYPE.is_file(), 'Task-local capacity prototype is not implemented yet'
    spec = importlib.util.spec_from_file_location('dc155169ea57_parametric', PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def grid(*rows):
    return [[int(cell) for cell in row] for row in rows]


class ParametricPrototypeTests(unittest.TestCase):
    prototype = None
    oracle = None

    def setUp(self):
        if self.__class__.prototype is None:
            self.__class__.prototype = load_prototype()
            self.__class__.oracle = self.__class__.prototype.RuleOracle()
            self.__class__.oracle.__enter__()

    @classmethod
    def tearDownClass(cls):
        if cls.oracle is not None:
            cls.oracle.__exit__(None, None, None)

    # A >= boundary, a bounding-box-width shortcut, or stopping at the last cell
    # would change these hand-derived outputs.
    def test_threshold_and_lowest_support_with_tail(self):
        prototype, oracle = self.prototype, self.oracle
        source = grid('8888888', '8111888', '8188888', '8118888', '8188888',
                      '8888888', '2222222', '8888888', '8888888', '8888888', '8888888')
        expected = {
            1: grid('8888888', '8888888', '8888888', '8111888', '8188888',
                    '8118888', '2122222', '8888888', '8888888', '8888888', '8888888'),
            2: grid('8888888', '8888888', '8888888', '8888888', '8888888',
                    '8111888', '2122222', '8118888', '8188888', '8888888', '8888888'),
            3: grid('8888888', '8888888', '8888888', '8888888', '8888888',
                    '8888888', '2888222', '8111888', '8188888', '8118888', '8188888'),
        }
        for capacity, output in expected.items():
            assert oracle.apply(prototype.materialize_rule(capacity), source) == output
            assert prototype.rule_mirror(source, capacity) == output


    # Joining disconnected shapes by column would move the bar to the wrong row.
    def test_disconnected_same_column_components_fall_independently(self):
        prototype, oracle = self.prototype, self.oracle
        source = grid('8118888', '8888888', '8188888', '8188888', '8888888',
                      '2222222', '8888888', '8888888', '8888888', '8888888')
        expected = grid('8888888', '8888888', '8888888', '8888888', '8118888',
                        '2822222', '8888888', '8888888', '8188888', '8188888')
        assert oracle.apply(prototype.materialize_rule(1), source) == expected
        assert prototype.rule_mirror(source, 1) == expected


    def test_default_reproduces_exact_canonical_authority(self):
        prototype, oracle = self.prototype, self.oracle
        assert prototype.materialize_rule() == prototype.canonical_program()
        assert prototype.catalog_rule_hash(prototype.materialize_rule()) == 'c0f1818b0fb2'
        assert prototype.sha256_text(prototype.materialize_rule()) == '2def524a1836b8bbbbf304e452ba7cfadf72ac353419ed428326edfcc2b167e6'
        pairs = canonical_pairs('dc155169ea57', root=find_root(__file__))
        assert len(pairs) == 4
        for pair in pairs:
            assert oracle.apply(prototype.materialize_rule(), pair['input']) == pair['output']


    def test_invalid_capacity_rejected(self):
        for capacity in [True, 0, 4, 1.0, '2']:
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                self.prototype.materialize_rule(capacity)


    def test_invalid_counts_fail_explicitly(self):
        for demo_count, query_count in [(1, 4), (0, 4), (2, 0), (True, 4), (2, 65)]:
            with self.subTest(counts=(demo_count, query_count)), self.assertRaises(ValueError):
                self.prototype.build_episode(seed=17, demo_count=demo_count, query_count=query_count)


    def test_complete_four_query_episode_without_public_leakage(self):
        prototype, oracle = self.prototype, self.oracle
        for capacity in (1, 2, 3):
            episode = prototype.build_episode(seed=17, barrier_capacity=capacity,
                                              demo_count=2, query_count=4, oracle=oracle)
            challenge = episode['public']
            assert set(challenge) == {'train', 'test'}
            assert len(challenge['train']) == 2
            assert len(challenge['test']) == 4
            assert all(set(pair) == {'input', 'output'} for pair in challenge['train'])
            assert all(set(pair) == {'input'} for pair in challenge['test'])
            inputs = [pair['input'] for pair in challenge['train'] + challenge['test']]
            assert len({json.dumps(value) for value in inputs}) == 6
            assert len(episode['private']['query_outputs']) == 4
            assert episode['private']['parameters'] == {'barrier_capacity': capacity}
            assert episode['private']['rival_fit']['surviving_rivals'] == []
            assert len(episode['private']['per_query_checks']) == 4
            assert all(check['identified_from_demonstrations'] for check in episode['private']['per_query_checks'])
            for pair, output in zip(challenge['test'], episode['private']['query_outputs']):
                assert output == oracle.apply(prototype.materialize_rule(capacity), pair['input'])



    def test_seed_replay_and_independent_counts(self):
        prototype, oracle = self.prototype, self.oracle
        first = prototype.build_episode(seed=19, barrier_capacity=None,
                                        demo_count=3, query_count=2, oracle=oracle)
        again = prototype.build_episode(seed=19, barrier_capacity=None,
                                        demo_count=3, query_count=2, oracle=oracle)
        assert first == again
        assert len(first['public']['train']) == 3
        assert len(first['public']['test']) == 2
        assert first['private']['selection'] == 'seeded_once'


    def test_evidence_export_retains_hashes_counts_and_content_addressed_public_names(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / 'episode-evidence'
            args = SimpleNamespace(out=str(output), seed=17, capacity=[1, 2],
                                   sample_capacity=False, demo_count=2, query_count=4)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(self.prototype.run(args), 0)
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(len(manifest['episodes']), 2)
            self.assertEqual(len(manifest['canonical_checks']), 4)
            self.assertEqual(manifest['racket_grid_executions'], 45)
            for entry in manifest['files']:
                path = output / entry['path']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
            public_paths = []
            for episode in manifest['episodes']:
                path = output / episode['public_path']
                public = json.loads(path.read_text())
                public_id = public_challenge_id(public)
                self.assertEqual(episode['public_id'], public_id)
                self.assertEqual(path.name, f'challenge-{public_id}.json')
                self.assertEqual(path.read_bytes(), public_challenge_bytes(public))
                self.assertEqual(set(public), {'train', 'test'})
                self.assertEqual(len(public['test']), 4)
                self.assertTrue(all(set(pair) == {'input'} for pair in public['test']))
                public_paths.append(episode['public_path'])
            self.assertEqual(public_paths, sorted(public_paths))
            self.assertFalse(any('episode-' in path for path in public_paths))

    def test_public_identifier_depends_only_on_visible_challenge_bytes(self):
        prototype, oracle = self.prototype, self.oracle
        episode = prototype.build_episode(seed=17, barrier_capacity=2,
                                          demo_count=2, query_count=4, oracle=oracle)
        public = episode['public']
        expected = public_challenge_id(public)
        private_mutation = json.loads(json.dumps(episode))
        private_mutation['private']['seed'] = 999999
        private_mutation['private']['parameters']['barrier_capacity'] = 3
        private_mutation['private']['query_outputs'] = list(reversed(
            private_mutation['private']['query_outputs']))
        self.assertEqual(prototype.public_export_id(private_mutation['public']), expected)
        visible_mutation = json.loads(json.dumps(public))
        visible_mutation['test'][0]['input'][0][0] = 7
        self.assertNotEqual(prototype.public_export_id(visible_mutation), expected)

    def test_demonstrations_refute_bounding_box_capacity_shortcut(self):
        prototype, oracle = self.prototype, self.oracle
        # Independent Racket construction of the reviewer's concrete rival:
        # bbox width gates floor passage; blocked objects retain canonical support.
        for capacity in (2, 3):
            with self.subTest(capacity=capacity):
                episode = prototype.build_episode(seed=17, barrier_capacity=capacity,
                                                  demo_count=2, query_count=4, oracle=oracle)
                rival = prototype.replace_once(prototype.materialize_rule(capacity),
                                               f'(> (row-count rr) {capacity})',
                                               '(> (row-count rr) 1)')
                rival = prototype.replace_once(rival, '(null? wide-rows)',
                                               f'(<= (+ (- cmax cmin) 1) {capacity})')
                refutations = [index for index, pair in enumerate(episode['public']['train'])
                               if oracle.apply(rival, pair['input']) != pair['output']]
                self.assertTrue(refutations, 'Bounding-box rival must be rejected by demonstrations alone')
                inventory = {row['name']: row for row in episode['private']['rival_fit']['rivals']}
                self.assertIn('bounding_box_capacity', inventory)
                self.assertEqual(inventory['bounding_box_capacity']['program'], rival)
                self.assertEqual(inventory['bounding_box_capacity']['refuted_by_demo'], refutations)
        # For capacity 1, four-connected width-1 components are vertical bars;
        # this criterion is equivalent, so it must not be required-refuted.
        self.assertNotIn('bounding_box_capacity', prototype.rival_programs(1))
        staircase = grid('8118888', '8811888', '8881188', '8888888',
                         '2222222', '8888888', '8888888', '8888888')
        equivalent = prototype.replace_once(prototype.materialize_rule(1), '(null? wide-rows)',
                                            '(<= (+ (- cmax cmin) 1) 1)')
        self.assertEqual(oracle.apply(equivalent, staircase),
                         oracle.apply(prototype.materialize_rule(1), staircase))

    def test_rivals_cannot_borrow_query_answers(self):
        prototype, oracle = self.prototype, self.oracle
        episode = prototype.build_episode(seed=17, barrier_capacity=2,
                                          demo_count=2, query_count=4, oracle=oracle)
        # The fit API accepts demonstrations only. A query label has no argument.
        fit = prototype.fit_rivals(episode['public']['train'], 2, oracle)
        assert fit == episode['private']['rival_fit']
        assert fit['surviving_rivals'] == []
        assert all(row['refuted_by_demo'] for row in fit['rivals'])
        # Missing teaching examples must be surfaced as ambiguity, never guessed.
        empty = prototype.fit_rivals([], 2, oracle)
        assert empty['surviving_rivals']

if __name__ == '__main__':
    unittest.main()
