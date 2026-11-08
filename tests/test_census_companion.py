"""Compact authoring evidence must keep failures without becoming a gate receipt."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from arcpuzzles import lesson_census as controller
from arcpuzzles.cli import main

ROOT = Path(__file__).resolve().parents[1]


def worker():
    spec = importlib.util.spec_from_file_location('companion_worker', ROOT / 'shared/tools/lesson_census.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lesson(index=0):
    instance = {'train': [{'input': [[1]], 'output': [[1]]}],
                'test': [{'input': [[2]], 'output': [[2]]}],
                'sampling': {'accepted_pairs': [{'split': 'train', 'sample_index': index + 1},
                                               {'split': 'test', 'sample_index': index + 3}]}}
    return {'band': 'easy', 'index': index, 'seed': 17, 'sample_index': index,
            'instance_sha256': worker().digest(instance), 'instance': instance,
            'rivals': {'wrong': 'refuted'}, 'ambiguous': False,
            'warnings': [], 'errors': [], 'rotations': []}


def report():
    return {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': 'x', 'status': 'ambiguous',
            'production_status': 'no_ambiguity_found', 'rotation_status': 'ambiguous',
            'rotation_policy': 'require', 'generator_sha256': 'a' * 64,
            'declared_rule_hash': 'rulepin', 'rule_source_sha256': 'b' * 64,
            'rule_callable_sha256': 'c' * 64, 'runtime_manifest_sha256': 'd' * 64,
            'controller_sha256': 'e' * 64, 'execution': {'exit_code': 1, 'timed_out': False},
            'sampler': {'bands': ['easy'], 'n_demos': 1, 'n_queries': 1, 'rotate_query': True},
            'summary': {'requested': 300, 'materialized': 300, 'rotations': 600, 'ambiguous_rotations': 19},
            'errors': [], 'canonical_rival_fit': {'wrong': {'status': 'fits_all'}},
            'lessons': [lesson(i) for i in range(300)],
            'runtime_manifest': {'files': [{'unrelated': 'x' * 500_000}]}}


def compact(full):
    return controller.census_companion(full, full_report_sha256='f' * 64,
                                       full_report_path='full.json', invocation=['arcpuzzles', 'lesson-census', 'x'])


def test_cached_rival_predictions_become_exact_ambiguity_witnesses():
    tool = worker()
    original = {'train': [{'input': [[1]], 'output': [[1]]}],
                'test': [{'input': [[2]], 'output': [[2]]}]}
    calls = []
    def wrong(grid):
        calls.append(grid[0][0])
        grid[0][0] = 1
        return grid
    before = deepcopy(original)
    cache = {}
    scored = tool.score_lesson(SimpleNamespace(), {'wrong': wrong}, original, prediction_cache=cache)
    witness = scored.get('rival_witnesses', {}).get('wrong')
    assert witness == {'query_index': 0, 'input': [[2]], 'expected_output': [[2]], 'rival_output': [[1]]}
    witness['input'][0][0] = 9
    assert original == before
    rotations = tool.score_rotations(SimpleNamespace(), {'wrong': wrong}, original, prediction_cache=cache)
    assert rotations[1]['rival_witnesses']['wrong']['input'] == [[2]]
    assert calls == [1, 2]  # exporting evidence must not call the rival again


def test_every_failing_rotation_recipe_and_first_exact_witness_survive():
    full = report()
    for i in range(19):
        full['lessons'][i]['rotations'] = [{'query_index': 1, 'train_indices': [0], 'ambiguous': True,
            'rivals': {'wrong': 'ambiguous'}, 'errors': [], 'warnings': [],
            'rival_witnesses': {'wrong': {'query_index': 0, 'input': [[2]], 'expected_output': [[2]], 'rival_output': [[1]]}}}]
    before = deepcopy(full)
    result = compact(full)
    assert result['schema'] == 'arcpuzzles-lesson-census-companion-v1'
    assert result['summary'] == full['summary'] and result['status'] == 'ambiguous'
    assert result['full_report']['sha256'] == 'f' * 64
    assert result['source_binding']['generator_sha256'] == 'a' * 64
    assert result['source_binding']['runtime_manifest_sha256'] == 'd' * 64
    assert [r['recipe']['sample_index'] for r in result['findings']] == list(range(19))
    assert all(r['query_index'] == 1 and r['train_indices'] == [0] for r in result['findings'])
    assert result['findings'][0]['recipe']['accepted_pairs'] == full['lessons'][0]['instance']['sampling']['accepted_pairs']
    w = result['first_witnesses']['declared:wrong']
    assert w['instance'] == full['lessons'][0]['instance']
    assert w['query_index'] == 1 and w['prediction']['rival_output'] == [[1]]
    assert result['training_admitted'] is False
    assert full == before and 'runtime_manifest' not in result
    assert len(json.dumps(result)) < len(json.dumps(full)) / 8
    with pytest.raises(ValueError):
        worker().validate_retained_census(result)  # never a full rescore/schedule receipt


def test_errors_hooks_and_advisory_searches_are_kept_separate_from_verdict():
    full = report(); full['status'] = 'no_ambiguity_found'; full['rotation_policy'] = 'diagnostic'
    full['lessons'] = [lesson(2), lesson(3), lesson(4)]
    full['lessons'][0]['errors'] = ['materializer failed']
    full['lessons'][0].pop('instance')
    full['lessons'][1]['warnings'] = ['weak demonstrations']
    full['lessons'][2]['searched_rivals'] = {'provider_status': 'error', 'truncated': True,
        'errors': ['provider failed'], 'candidates': {'provider:x': {'status': 'ambiguous', 'origin': 'independent_provider', 'witness': {'train': [], 'test': []}}, 'bad': {'status': 'error', 'error': 'boom'}}}
    result = compact(full)
    assert result['status'] == full['status']
    assert result['rotation_policy'] == 'diagnostic'
    assert len(result['findings']) == 3
    assert result['findings'][0]['errors'] == ['materializer failed']
    assert result['findings'][1]['warnings'] == ['weak demonstrations']
    assert result['findings'][2]['searched_rivals']['truncated'] is True
    assert result['first_witnesses']['searched:provider:x']['basis'] == 'advisory_search'


def test_partial_and_legacy_reports_do_not_gain_counts_or_predictions():
    partial = compact({'schema': 'arcpuzzles-lesson-census-v1', 'task_id': 'x', 'status': 'error',
                       'errors': ['worker interrupted'], 'execution': {'timed_out': True, 'exit_code': -15}})
    assert 'summary' not in partial and partial['status'] == 'error'
    assert partial['errors'] == ['worker interrupted']
    full = report(); full['lessons'] = [lesson()]
    full['lessons'][0].update(ambiguous=True, rivals={'old': 'ambiguous'})
    witness = compact(full)['first_witnesses']['declared:old']
    assert witness['instance'] == full['lessons'][0]['instance']
    assert witness['prediction_status'] == 'not_recorded' and 'prediction' not in witness


def test_rescore_keeps_original_draw_and_current_rival_bindings_distinct():
    full = report(); full['schema'] = 'arcpuzzles-lesson-rescore-v1'
    full['input_generator_sha256'] = '1' * 64; full['rival_generator_sha256'] = '2' * 64
    full['retained_runtime_manifest_sha256'] = '3' * 64
    full['input_census_sha256'] = '4' * 64
    result = compact(full)
    assert result['source_binding']['input_generator_sha256'] == '1' * 64
    assert result['source_binding']['rival_generator_sha256'] == '2' * 64
    assert result['source_binding']['input_census_sha256'] == '4' * 64


@pytest.mark.parametrize('status,expected', [('no_ambiguity_found', 0), ('ambiguous', 1), ('error', 2)])
def test_cli_automatically_writes_hash_bound_companion_without_changing_exit(library, tmp_path, monkeypatch, status, expected):
    full = report(); full['task_id'] = 'aaaa00000001'; full['status'] = status
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: deepcopy(full))
    out = tmp_path / 'census.json'
    assert main(['--library', str(library), 'lesson-census', full['task_id'], '--out', str(out)]) == expected
    companion = out.with_suffix('.summary.json')
    assert companion.is_file()
    saved = json.loads(companion.read_text())
    assert saved['full_report']['sha256'] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert saved['full_report']['bytes'] == out.stat().st_size
    assert saved['full_report']['path'] == str(out.resolve())
    assert saved['invocation']['argv'][-2:] == ['--out', str(out)]
    assert json.loads(out.read_text()) == full


@pytest.mark.parametrize('dangling_symlink', [False, True])
def test_existing_companion_refuses_before_generating_or_writing(library, tmp_path, monkeypatch, dangling_symlink):
    out = tmp_path / 'census.json'; summary = out.with_suffix('.summary.json')
    if dangling_symlink:
        summary.symlink_to(tmp_path / 'missing.json')
    else:
        summary.write_text('keep')
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: pytest.fail('collision started a census'))
    assert main(['--library', str(library), 'lesson-census', 'aaaa00000001', '--out', str(out)]) == 1
    assert not out.exists()
    assert summary.is_symlink() if dangling_symlink else summary.read_text() == 'keep'
