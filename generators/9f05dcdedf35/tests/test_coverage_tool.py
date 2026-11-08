"""Offline retained-census coverage tests: no generator/answer imports or draws."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'workspace/canonical_distinction_coverage.py'
SPEC = importlib.util.spec_from_file_location('canonical_distinction_coverage_tested', SOURCE)
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)
TASK = 'synthetic123'
GENERATOR = 'a' * 64
WRONG = 'LESSON_COMPETITORS:wrong'
AGREEMENT = 'SEMANTIC_RIVALS:agreement'
FIELDS = ('requested', 'materialized', 'materialization_errors', 'pairs', 'ambiguous',
          'hook_warnings', 'scoring_errors', 'rotations', 'ambiguous_rotations',
          'rotation_hook_warnings', 'rotation_scoring_errors')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def refresh(census):
    """Build consistent synthetic census counts/hashes after intentional mutations."""
    total = dict.fromkeys(FIELDS, 0)
    all_inputs = set()
    for band in census['sampler']['bands']:
        rows = [r for r in census['lessons'] if r['band'] == band]
        counts = dict.fromkeys(FIELDS, 0)
        unique = set()
        rivals = {name: {} for name in census['rivals']}
        for row in rows:
            row['instance_sha256'] = digest(row['instance'])
            pairs = row['instance']['train'] + row['instance']['test']
            rotations = row['rotations']
            counts['requested'] += 1
            counts['materialized'] += 1
            counts['pairs'] += len(pairs)
            counts['ambiguous'] += int(row['ambiguous'])
            counts['hook_warnings'] += int(bool(row['warnings']))
            counts['scoring_errors'] += int(bool(row['errors']))
            counts['rotations'] += len(rotations)
            counts['ambiguous_rotations'] += sum(int(r['ambiguous']) for r in rotations)
            counts['rotation_hook_warnings'] += sum(int(bool(r['warnings'])) for r in rotations)
            counts['rotation_scoring_errors'] += sum(int(bool(r['errors'])) for r in rotations)
            unique.update(digest(pair['input']) for pair in pairs)
            for name, status in row['rivals'].items():
                rivals[name][status] = rivals[name].get(status, 0) + 1
        all_inputs.update(unique)
        census['per_band'][band] = {**counts, 'unique_inputs': len(unique), 'rivals': rivals}
        for key in FIELDS:
            total[key] += counts[key]
    census['summary'] = {**total, 'unique_inputs': len(all_inputs)}
    census['unique_inputs'] = len(all_inputs)
    return census


def census(status='refuted', rotate=True):
    manifest = {'schema': 'arcpuzzles-runtime-v1', 'task_id': TASK,
                'files': [{'library_path': f'generators/{TASK}/generator.py',
                           'runtime_path': f'puzzle_generators/per_puzzle/{TASK}/generator.py',
                           'sha256': GENERATOR}]}
    result = {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': TASK,
              'status': 'no_ambiguity_found', 'production_status': 'no_ambiguity_found',
              'rotation_status': 'no_ambiguity_found' if rotate else 'not_requested',
              'rotation_policy': 'require', 'errors': [], 'contract': 'rivals',
              'generator_sha256': GENERATOR, 'controller_sha256': 'b' * 64,
              'rule_source_sha256': 'c' * 64, 'rule_callable_sha256': 'd' * 64,
              'rule_task_id': TASK, 'rule_file': 'data/canonical/puzzles.jsonl',
              'runtime_manifest': manifest,
              'runtime_manifest_sha256': hashlib.sha256((json.dumps(manifest, indent=2) + '\n').encode()).hexdigest(),
              'execution': {'exit_code': 0, 'timed_out': False},
              'rivals': [WRONG, AGREEMENT], 'canonical_pairs': 2,
              'canonical_rival_fit': {WRONG: {'pairs': 2, 'fits': 0, 'errors': [], 'status': 'refuted'},
                                      AGREEMENT: {'pairs': 2, 'fits': 2, 'errors': [], 'status': 'fits_all'}},
              'sampler': {'task_id': TASK, 'per_band': 1, 'bands': ['easy', 'hard'],
                          'n_demos': 2, 'n_queries': 1, 'rotate_query': rotate,
                          'enumerate_schedule_period': False},
              'lessons': [], 'per_band': {}}
    for band in result['sampler']['bands']:
        instance = {'task_id': TASK, 'rule_task_id': TASK, 'rule_file': result['rule_file'],
                    'seed': 17, 'sample_index': 0,
                    'train': [{'input': [[1]], 'output': [[1]]}, {'input': [[2]], 'output': [[2]]}],
                    'test': [{'input': [[3]], 'output': [[3]]}]}
        def score(s):
            return {'rivals': {WRONG: s, AGREEMENT: 'survived_all'},
                    'ambiguous': s == 'ambiguous', 'warnings': [], 'errors': [], 'contract': 'rivals'}
        row = {'band': band, 'index': 0, 'seed': 17, 'sample_index': 0, 'instance': instance,
               **score(status), 'rotations': []}
        if rotate:
            for query in range(3):
                s = ('ambiguous' if query == 2 else 'refuted') if status == 'ambiguous' else status
                row['rotations'].append({'query_index': query,
                                         'train_indices': [i for i in range(3) if i != query], **score(s)})
        result['lessons'].append(row)
    if status == 'ambiguous':
        result.update(status='ambiguous', production_status='ambiguous', rotation_status='ambiguous')
        result['execution']['exit_code'] = 1
    return refresh(result)


def analyze(value, bands=('easy', 'hard'), task=TASK, generator=GENERATOR):
    return tool.analyze_census(value, required_bands=bands,
                               expected_task_id=task, expected_generator_sha256=generator)


def test_refuted_sets_cover_bands_without_fabricating_exact_unique_inputs():
    result = analyze(census())
    assert result['status'] == 'covered'
    for band in ('easy', 'hard'):
        row = result['coverage'][WRONG][band]
        assert row['refuting_lesson_count'] == 1
        assert row['refuting_set_count'] == 3
        assert row['refuting_observation_count'] == 4
        assert row['unique_input_refuting_count'] is None
        assert row['unique_input_refuting_lower_bound'] == 1
        assert row['confirmed_input_hashes'] == []
        assert all(len(w['candidate_input_hashes']) == 2 for w in row['evidence'])
        assert all(w['instance_sha256'] for w in row['evidence'])
    assert result['canonical_fitting_rivals'] == [AGREEMENT]


def test_all_survived_is_missing_canonical_distinction_despite_no_ambiguity():
    result = analyze(census('survived_all'))
    assert result['status'] == 'missing_distinction'
    assert {(x['rival'], x['band']) for x in result['missing_distinctions']} == {(WRONG, 'easy'), (WRONG, 'hard')}
    assert result['coverage'][WRONG]['easy']['unique_input_refuting_count'] == 0
    assert result['coverage'][WRONG]['easy']['unique_input_refuting_lower_bound'] == 0


def test_single_query_ambiguity_identifies_exact_input_and_is_not_identifiability_pass():
    result = analyze(census('ambiguous'))
    assert result['status'] == 'covered'
    assert result['input_census_status'] == 'ambiguous'
    assert result['coverage'][WRONG]['easy']['confirmed_input_hashes'] == [digest([[3]])]
    assert result['coverage'][WRONG]['easy']['unique_input_refuting_count'] == 1
    assert result['universal_induction_claimed'] is False


def test_coverage_is_required_in_each_explicit_band():
    value = census(rotate=False)
    value['lessons'][1]['rivals'][WRONG] = 'survived_all'
    result = analyze(refresh(value))
    assert result['status'] == 'missing_distinction'
    assert result['missing_distinctions'] == [{'rival': WRONG, 'band': 'hard'}]


@pytest.mark.parametrize('mutation', [
    lambda j: j.update(status='incomplete'),
    lambda j: j['execution'].update(timed_out=True),
    lambda j: j['execution'].update(exit_code=2),
    lambda j: j['errors'].append('worker failed'),
    lambda j: j['summary'].update(materialization_errors=1),
    lambda j: j['lessons'].pop(),
    lambda j: j['lessons'].append(deepcopy(j['lessons'][0])),
    lambda j: j['lessons'][0]['errors'].append('scoring failed'),
    lambda j: j['lessons'][0]['rivals'].update({WRONG: 'unknown'}),
    lambda j: j['lessons'][0]['rivals'].update({'LESSON_COMPETITORS:undeclared': 'refuted'}),
    lambda j: j['canonical_rival_fit'].pop(WRONG),
    lambda j: j['canonical_rival_fit'][WRONG].update(status='fits_all'),
    lambda j: j['canonical_rival_fit'][WRONG]['errors'].append('rival failed'),
    lambda j: j['lessons'][0]['instance']['test'][0].pop('output'),
    lambda j: j['lessons'][0]['instance']['train'][0].update(input=[[10]]),
    lambda j: j['lessons'][0]['instance'].update(rule_task_id='wrongtask'),
    lambda j: j['lessons'][0].update(instance_sha256='e' * 64),
    lambda j: j.update(runtime_manifest_sha256='f' * 64),
    lambda j: j.update(generator_sha256='e' * 64),
    lambda j: j.pop('rule_source_sha256'),
    lambda j: j.pop('controller_sha256'),
    lambda j: j['sampler'].update(per_band=2),
    lambda j: j['lessons'][0]['rotations'].pop(),
    lambda j: j['lessons'][0]['rotations'][0].update(train_indices=[0, 1]),
    lambda j: j['lessons'][0]['rotations'][0]['rivals'].update({WRONG: 'survived_all'}),
])
def test_missing_corrupt_partial_or_errored_evidence_is_incomplete(mutation):
    value = census()
    mutation(value)
    result = analyze(value)
    assert result['status'] == 'incomplete'
    assert result['errors']


def test_required_bands_and_external_source_pin_cannot_be_omitted_or_changed():
    assert analyze(census(), bands=())['status'] == 'incomplete'
    assert analyze(census(), bands=('medium',))['status'] == 'incomplete'
    assert analyze(census(), task='wrongtask')['status'] == 'incomplete'
    assert analyze(census(), generator='f' * 64)['status'] == 'incomplete'


def test_cli_offline_json_exit_codes(tmp_path):
    input_path = tmp_path / 'census.json'
    args = [sys.executable, str(SOURCE), str(input_path), '--required-bands', 'easy', 'hard',
            '--expected-task-id', TASK, '--expected-generator-sha256', GENERATOR]
    for value, code, status in [(census(), 0, 'covered'), (census('survived_all'), 1, 'missing_distinction'),
                                ({'schema': 'bad'}, 2, 'incomplete')]:
        input_path.write_text(json.dumps(value))
        run = subprocess.run(args, capture_output=True, text=True)
        assert run.returncode == code
        assert json.loads(run.stdout)['status'] == status


def test_missing_rule_identity_cannot_pass_even_if_instances_repeat_it():
    value = census()
    value['rule_task_id'] = None
    for row in value['lessons']:
        row['instance']['rule_task_id'] = None
    assert analyze(refresh(value))['status'] == 'incomplete'


def test_schedule_flag_must_be_boolean():
    value = census()
    value['sampler']['enumerate_schedule_period'] = 0
    assert analyze(value)['status'] == 'incomplete'


def test_schedule_completion_requires_bound_actual_starts():
    value = census()
    value['sampler'].update(enumerate_schedule_period=True, schedule_seed=17)
    value['schedule_coverage'] = {'status': 'complete_fixed_seed', 'contract': 'LESSON_SCHEDULE_PERIOD',
                                 'period': 1, 'seed': 17, 'bands': ['easy', 'hard'],
                                 'generator_sha256': GENERATOR, 'rule_source_sha256': 'c' * 64,
                                 'expected_lessons': 2, 'expected_rotations': 6}
    for row in value['lessons']:
        row['instance']['sampling'] = {'requested_start': 0}
    assert analyze(refresh(value))['status'] == 'covered'
    value['lessons'][0]['instance']['sampling']['requested_start'] = 1
    assert analyze(refresh(value))['status'] == 'incomplete'


def test_repeated_inputs_do_not_inflate_unique_candidate_set_count():
    value = census()
    value['sampler']['per_band'] = 2
    for row in list(value['lessons']):
        duplicate = deepcopy(row)
        duplicate.update(index=1, sample_index=1, seed=18)
        duplicate['instance'].update(sample_index=1, seed=18)
        value['lessons'].append(duplicate)
    result = analyze(refresh(value))
    assert result['status'] == 'covered'
    evidence = result['coverage'][WRONG]['easy']
    assert evidence['refuting_lesson_count'] == 2
    assert evidence['refuting_observation_count'] == 8
    assert evidence['refuting_set_count'] == 3
    assert evidence['unique_input_refuting_lower_bound'] == 1
    assert evidence['unique_input_refuting_count'] is None
