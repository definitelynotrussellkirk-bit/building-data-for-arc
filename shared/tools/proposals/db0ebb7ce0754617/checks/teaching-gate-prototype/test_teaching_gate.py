"""Targeted policy checks using the retained real census schema."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from teaching_gate import evaluate


FOLDER = Path(__file__).resolve().parent
WORK = FOLDER.parents[1]


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(gzip.decompress((WORK / 'checks' / 'lesson-census-final.json.gz').read_bytes()))
        cls.source = (WORK / 'repo' / 'generators' / cls.report['task_id'] / 'generator.py').read_bytes()
        cls.rule = cls.report['declared_rule_hash']

    def test_real_complete_census_passes(self):
        result = evaluate(self.report, self.source, self.rule, require_rotations=True)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['counts']['production_lessons'], 300)
        self.assertEqual(result['counts']['query_rotations'], 1200)

    def test_required_failures_are_detected(self):
        rival = self.report['rivals'][0]
        mutations = {
            'missing_contract': lambda r: r.update(contract='none', rivals=[]),
            'missing_canonical_compatible_rivals': lambda r: r.update(canonical_rival_fit={}),
            'incomplete_census': lambda r: r['lessons'].pop(),
            'census_errors': lambda r: r['errors'].append('deliberate test diagnostic'),
            'top_level_error_verdict': lambda r: r.update(status='error'),
            'incomplete_rival_inventory': lambda r: r['rivals'].pop(),
            'production_survivor': lambda r: r['lessons'][0]['rivals'].update({rival: 'survived_all'}),
            'rotation_survivor': lambda r: r['lessons'][0]['rotations'][0]['rivals'].update({rival: 'survived_all'}),
            'missing_rival_score': lambda r: r['lessons'][0]['rivals'].pop(rival),
            'missing_rotation': lambda r: r['lessons'][0]['rotations'].pop(),
            'incorrect_rule_hash': lambda r: r.update(declared_rule_hash='000000000000'),
        }
        for name, change in mutations.items():
            with self.subTest(name=name):
                report = deepcopy(self.report)
                change(report)
                result = evaluate(report, self.source, self.rule, require_rotations=True)
                self.assertEqual(result['status'], 'fail')
                self.assertTrue(result['failures'])

    def test_exact_survivor_identity_is_preserved(self):
        report = deepcopy(self.report)
        rival = report['rivals'][0]
        lesson = report['lessons'][0]
        lesson['rivals'][rival] = 'survived_all'
        result = evaluate(report, self.source, self.rule, require_rotations=True)
        failure = next(x for x in result['failures'] if x['code'] == 'rival_not_refuted')
        self.assertEqual(failure['lesson_id'], {'band': lesson['band'], 'index': lesson['index']})
        self.assertEqual(failure['rival_id'], rival)
        self.assertEqual(failure['recorded_status'], 'survived_all')

    def test_source_mismatch_rejects(self):
        result = evaluate(self.report, self.source + b'\n# source change\n', self.rule, require_rotations=True)
        self.assertEqual(result['status'], 'fail')
        self.assertIn('generator_source_mismatch', {x['code'] for x in result['failures']})


if __name__ == '__main__':
    unittest.main()
