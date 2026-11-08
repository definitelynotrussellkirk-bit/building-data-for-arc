"""Regressions for real canonical-set/source binding review findings.

Receipt envelopes below are synthetic unit fixtures; grids and canonical
identities come from this checkout's actual canonical record.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest
from reviewer_support import canonical_path, find_root

SCRIPT = Path(__file__).resolve().parents[1] / 'workspace' / 'check_output_profile_support.py'
spec = importlib.util.spec_from_file_location('profile_integrity_tool', SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
LEDGER = canonical_path(root=find_root(__file__))
RAW = LEDGER.read_bytes()
RECORD = next(row for line in RAW.splitlines() if (row := json.loads(line)).get('task_id') == '8738d400fb96')
PAIRS = [('train', i, p) for i, p in enumerate(RECORD['train'])] + [('test', 0, RECORD['test'])]
CALLABLE = '15fd3ebc54dc1b3e9d052920e62ebf5e4a8ada40b7f18fb86d8b4107e8dbd557'
PROGRAM = hashlib.sha256(RECORD['program_solution'].encode()).hexdigest()
LEDGER_SHA = hashlib.sha256(RAW).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def canonical_receipt():
    pairs = [deepcopy(p) for _, _, p in PAIRS] + [deepcopy(PAIRS[0][2]), deepcopy(PAIRS[1][2])]
    results = [{'index': i, **p, 'valid_output': True, 'error': None,
                'input_sha256': digest(p['input']), 'output_sha256': digest(p['output'])}
               for i, p in enumerate(pairs)]
    return {'schema': 'task-output-profile-observations-v1', 'task_id': '8738d400fb96',
            'role': 'canonical', 'adapter': tool.ADAPTER, 'rule_callable_sha256': CALLABLE,
            'executed_rule_hash': 'fc4e32aa0363', 'expected_pairs': 5, 'expected_apply_results': 7,
            'execution': {'exit_code': 0, 'timed_out': False}, 'label_generator_sha256': 'a'*64,
            'ledger_sha256': LEDGER_SHA, 'canonical_program_sha256': PROGRAM,
            'samples': [{'split': split, 'pair_index': i, 'result_index': j}
                        for j, (split, i, _) in enumerate(PAIRS)],
            'apply_receipt': {'schema': 'arcpuzzles-apply-v1', 'task_id': '8738d400fb96',
                              'reference': 'canonical', 'rule_text_sha256': CALLABLE,
                              'executed_rule_hash': 'fc4e32aa0363', 'generator_sha256': 'a'*64,
                              'rule_hash_matches_catalog': True, 'results': results}}


def census():
    pairs = [deepcopy(PAIRS[i][2]) for i in (0, 4, 3)]
    instance = {'task_id': '8738d400fb96', 'rule_task_id': '8738d400fb96',
                'rule_file': 'data/canonical/puzzles.jsonl', 'train': pairs[:2], 'test': pairs[2:]}
    manifest = {'task_id': '8738d400fb96', 'files': [
        {'library_path': 'generators/8738d400fb96/generator.py', 'sha256': 'a'*64},
        {'library_path': 'shared/data/canonical/puzzles.jsonl', 'runtime_path': 'data/canonical/puzzles.jsonl', 'sha256': LEDGER_SHA}]}
    return {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': '8738d400fb96',
            'rule_task_id': '8738d400fb96', 'rule_file': instance['rule_file'],
            'generator_sha256': 'a'*64, 'rule_callable_sha256': CALLABLE,
            'rule_source_sha256': PROGRAM, 'declared_rule_hash': 'fc4e32aa0363',
            'runtime_manifest': manifest,
            'runtime_manifest_sha256': hashlib.sha256((json.dumps(manifest, indent=2)+'\n').encode()).hexdigest(),
            'status': 'no_contract', 'production_status': 'no_contract', 'rotation_status': 'not_requested',
            'errors': [], 'execution': {'timed_out': False, 'exit_code': 0},
            'sampler': {'bands': ['easy'], 'n_demos': 2, 'n_queries': 1, 'per_band': 1, 'rotate_query': False},
            'summary': {'requested': 1, 'materialized': 1, 'materialization_errors': 0,
                        'scoring_errors': 0, 'rotation_scoring_errors': 0, 'pairs': 3, 'rotations': 0},
            'lessons': [{'band': 'easy', 'index': 0, 'instance': instance,
                         'instance_sha256': digest(instance), 'errors': [], 'rotations': []}]}


@pytest.mark.parametrize('damage', ['subset', 'extra_fixture_mapping', 'identity', 'ledger', 'program'])
def test_canonical_receipt_cannot_change_the_authoritative_pair_set(damage):
    c = canonical_receipt()
    if damage == 'subset': c['samples'] = c['samples'][:3]; c['expected_pairs'] = 3
    elif damage == 'extra_fixture_mapping': c['samples'][-2]['result_index'] = 5; c['samples'][-1]['result_index'] = 6
    elif damage == 'identity': c['samples'][-1]['split'] = 'train'; c['samples'][-1]['pair_index'] = 0
    elif damage == 'ledger': c['ledger_sha256'] = 'f'*64
    else: c['canonical_program_sha256'] = 'f'*64
    with pytest.raises(ValueError): tool.analyze(c, census(), tool.ADAPTER)


@pytest.mark.parametrize('field', ['rule_source_sha256', 'declared_rule_hash', 'manifest_ledger'])
def test_census_rule_and_ledger_fields_must_match_retained_sources(field):
    data = census()
    if field == 'manifest_ledger':
        data['runtime_manifest']['files'][1]['sha256'] = 'f'*64
        data['runtime_manifest_sha256'] = hashlib.sha256((json.dumps(data['runtime_manifest'], indent=2)+'\n').encode()).hexdigest()
    else: data[field] = 'f'*(12 if field == 'declared_rule_hash' else 64)
    with pytest.raises(ValueError): tool.analyze(canonical_receipt(), data, tool.ADAPTER)


def test_complete_canonical_mapping_can_include_unmapped_public_fixtures():
    result = tool.analyze(canonical_receipt(), census(), tool.ADAPTER)
    assert result['canonical_profile_counts'] == {'full': 3, 'empty': 1, 'partial': 1}
    assert result['status'] == 'observed_support_in_each_band'
