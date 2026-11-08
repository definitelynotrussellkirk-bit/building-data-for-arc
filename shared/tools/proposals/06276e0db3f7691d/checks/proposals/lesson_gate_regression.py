#!/usr/bin/env python3
"""Literal-grid regression; patches only a TemporaryDirectory worker copy."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / 'repo'
SOURCE = REPO / 'src/arcpuzzles/worker.py'
# This is the existing helper that prepare_runtime maps to reviewer_support.py.
sys.path.insert(0, str(REPO / 'shared/runtime'))


def episode():
    return {'train': [{'input': [[1]], 'output': [[2]]},
                      {'input': [[3]], 'output': [[4]]}],
            'test': [{'input': [[5]], 'output': [[6]]}]}


def true_rule(grid):
    return [[grid[0][0] + 1]]


def rival(grid):
    return [[8]] if grid == [[5]] else true_rule(grid)


class Regression(unittest.TestCase):
    def check(self, module, lesson=None, automatic=False, minimum=None):
        lesson = episode() if lesson is None else lesson
        before = deepcopy(lesson)
        try:
            return WORKER.lesson_check(module, lesson, {'demonstration_policy': {
                'automatic': automatic, 'declared_minimum': minimum}})
        finally:
            self.assertEqual(lesson, before, 'materialized labels must remain untouched')

    def test_undeclared_preserved(self):
        self.assertEqual(self.check(SimpleNamespace())['status'], 'not_declared')

    def test_hook_only_preserved(self):
        self.assertEqual(self.check(SimpleNamespace(lesson_identifiable=lambda d, q: []))['status'],
                         'passed_declared_hook')

    def test_hook_error_preserved(self):
        def hook(d, q):
            q['input'][0][0] = 9
            return []
        self.assertEqual(self.check(SimpleNamespace(lesson_identifiable=hook))['status'],
                         'diagnostic_unsupported')

    def test_minimum_policy_preserved(self):
        module = SimpleNamespace()
        self.assertEqual(self.check(module, minimum=3)['status'], 'diagnostic_unsupported')
        with self.assertRaisesRegex(ValueError, 'Automatic lesson unsupported'):
            self.check(module, automatic=True, minimum=3)

    def test_competitor_automatic_rejects(self):
        with self.assertRaisesRegex(ValueError, 'Automatic lesson unsupported'):
            self.check(SimpleNamespace(LESSON_COMPETITORS={'alternate': rival}), automatic=True)

    def test_shortcut_automatic_rejects(self):
        with self.assertRaisesRegex(ValueError, 'CANONICAL_SHORTCUTS:alternate'):
            self.check(SimpleNamespace(CANONICAL_SHORTCUTS={'alternate': rival}), automatic=True)

    def test_explicit_is_diagnostic(self):
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'alternate': rival}))
        self.assertEqual(result['status'], 'diagnostic_unsupported')
        self.assertIn('fits every demo', result['queries'][0]['reasons'][0])
        self.assertEqual(result['rivals']['LESSON_COMPETITORS:alternate'], 'ambiguous')
        self.assertFalse(result['hook_declared'])
        self.assertEqual(result['contract'], 'rivals_only')

    def test_refuted_by_second_demo_is_accepted(self):
        def second_demo_refutes(g):
            return [[8]] if g in ([[3]], [[5]]) else true_rule(g)
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'alternate': second_demo_refutes}), automatic=True)
        self.assertEqual(result['status'], 'passed_declared_rivals')
        self.assertEqual(result['rivals']['LESSON_COMPETITORS:alternate'], 'refuted')

    def test_query_agreement_is_accepted(self):
        result = self.check(SimpleNamespace(CANONICAL_SHORTCUTS={'agree': true_rule}), automatic=True)
        self.assertEqual(result['status'], 'passed_declared_rivals')
        self.assertEqual(result['rivals']['CANONICAL_SHORTCUTS:agree'], 'survived_all')
        self.assertEqual(result['reasons'], [])

    def test_every_query_is_scored(self):
        lesson = episode()
        lesson['test'].append({'input': [[7]], 'output': [[8]]})
        def last_query(g):
            return [[9]] if g == [[7]] else true_rule(g)
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'last': last_query}), lesson)
        self.assertEqual(result['queries'][0]['reasons'], [])
        self.assertIn('query 1:', result['reasons'][0])

    def test_declaration_errors_are_visible(self):
        for invalid in (None, [], {'bad': 4}, {4: true_rule}):
            with self.subTest(invalid=repr(invalid)):
                result = self.check(SimpleNamespace(LESSON_COMPETITORS=invalid))
                self.assertEqual(result['status'], 'diagnostic_unsupported')
                self.assertIn('LESSON_COMPETITORS:', result['reasons'][0])
                with self.assertRaises(ValueError):
                    self.check(SimpleNamespace(LESSON_COMPETITORS=invalid), automatic=True)

    def test_mutation_is_visible(self):
        def mutates(g):
            g[0][0] += 1
            return g
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'mutates': mutates}))
        self.assertEqual(result['status'], 'diagnostic_unsupported')
        self.assertIn('mutated its input', result['reasons'][0])

    def test_exception_is_visible(self):
        def raises(g):
            raise RuntimeError('fixture failure')
        result = self.check(SimpleNamespace(CANONICAL_SHORTCUTS={'raises': raises}))
        self.assertEqual(result['status'], 'diagnostic_unsupported')
        self.assertIn('RuntimeError: fixture failure', result['reasons'][0])

    def test_malformed_prediction_is_visible(self):
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'bad': lambda g: None}))
        self.assertEqual(result['status'], 'diagnostic_unsupported')
        self.assertEqual(result['rivals']['LESSON_COMPETITORS:bad'], 'error')

    def test_visible_nondeterminism_is_visible(self):
        calls = []
        def inconsistent(g):
            calls.append(None)
            return [[2]] if len(calls) % 2 else [[9]]
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={'stateful': inconsistent}))
        self.assertEqual(result['status'], 'diagnostic_unsupported')
        self.assertIn('inconsistent predictions', result['reasons'][0])

    def test_hook_and_rivals_are_both_kept(self):
        module = SimpleNamespace(LESSON_COMPETITORS={'alternate': rival},
                                 lesson_identifiable=lambda d, q: ['hook finding'])
        result = self.check(module)
        self.assertEqual(result['contract'], 'hook_and_rivals')
        self.assertTrue(result['hook_declared'])
        self.assertEqual(len(result['queries'][0]['reasons']), 2)
        self.assertIn('hook finding', result['reasons'][0])

    def test_both_contracts_pass_provenance(self):
        result = self.check(SimpleNamespace(CANONICAL_SHORTCUTS={'agree': true_rule},
                                            lesson_identifiable=lambda d, q: []))
        self.assertEqual(result['status'], 'passed_declared_hook')
        self.assertEqual(result['contract'], 'hook_and_rivals')

    def test_empty_declaration_is_no_executable_contract(self):
        result = self.check(SimpleNamespace(LESSON_COMPETITORS={}))
        self.assertEqual(result['status'], 'not_declared')
        self.assertEqual(result['rivals'], {})
        self.assertEqual(result['contract'], 'none')

    def test_semantic_rivals_are_outside_lesson_contract(self):
        self.assertEqual(self.check(SimpleNamespace(SEMANTIC_RIVALS={'alternate': rival}))['status'],
                         'not_declared')


def main():
    global WORKER
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('original', 'patched'), required=True)
    mode = parser.parse_args().mode
    before = SOURCE.read_bytes()
    with tempfile.TemporaryDirectory(prefix='lesson-gate-proposal-') as directory:
        root = Path(directory)
        worker = root / 'src/arcpuzzles/worker.py'
        worker.parent.mkdir(parents=True)
        worker.write_bytes(before)
        if mode == 'patched':
            subprocess.run(['patch', '--batch', '-p1', '-i', str(HERE / 'lesson_gate.patch')],
                           cwd=root, check=True, capture_output=True, text=True)
        spec = importlib.util.spec_from_file_location('proposal_worker', worker)
        WORKER = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(WORKER)
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Regression))
    assert SOURCE.read_bytes() == before, 'source unexpectedly changed'
    print(f'mode={mode}; tests={result.testsRun}; failures={len(result.failures)}; errors={len(result.errors)}; '
          f'worker_sha256={hashlib.sha256(before).hexdigest()}; source_unchanged=true')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
