"""Concrete leakage and identity regressions for the reviewer export tool."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json

import pytest


@pytest.fixture
def exporter():
    path = Path(__file__).resolve().parents[1] / 'workspace/parametric/verify_evidence.py'
    assert path.is_file(), 'The reusable reviewer export/evidence tool is missing'
    spec = importlib.util.spec_from_file_location('_dc91_export_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def episode():
    return {'settings': {'mode': 'private'}, 'seed': 123,
            'program': 'secret-reference',
            'train': [{'input': [[1]], 'output': [[2]]},
                      {'input': [[3]], 'output': [[4]]}],
            'test': [{'input': [[5]], 'output': [[6]]},
                     {'input': [[7]], 'output': [[8]]},
                     {'input': [[9]], 'output': [[0]]},
                     {'input': [[1, 1]], 'output': [[2, 2]]}]}


def test_public_projection_excludes_all_controller_metadata(exporter, episode):
    public = json.loads(exporter.visible_bytes(episode))
    assert set(public) == {'train', 'test'}
    assert public['train'] == episode['train']
    assert public['test'] == [{'input': pair['input']} for pair in episode['test']]


def test_private_changes_do_not_change_public_identity(exporter, episode, tmp_path):
    first = exporter.write_public(episode, tmp_path)
    changed = copy.deepcopy(episode)
    changed.update(settings={'mode': 'other'}, seed=987, program='other-program')
    changed['test'][0]['output'] = [[9, 9]]
    second = exporter.write_public(changed, tmp_path)
    assert first == second
    assert len(list(tmp_path.iterdir())) == 1


def test_first_turn_matches_single_query_evaluation(exporter, episode):
    single = copy.deepcopy(episode)
    single['test'] = single['test'][:1]
    first = exporter.visible_bytes(episode, query_index=0)
    assert first == exporter.visible_bytes(single, query_index=0)
    assert json.loads(first)['test'] == [{'input': [[5]]}]


@pytest.mark.parametrize('index', [-1, 4, True, 1.0])
def test_invalid_query_projection_is_rejected(exporter, episode, index):
    with pytest.raises(ValueError):
        exporter.visible_bytes(episode, query_index=index)


def test_boolean_arc_cells_are_rejected(exporter, episode):
    episode['test'][0]['input'] = [[True]]
    with pytest.raises(ValueError):
        exporter.visible_bytes(episode)


@pytest.mark.parametrize('change', ['answer', 'setting', 'duplicate', 'whitespace', 'wrong_name'])
def test_saved_public_verifier_rejects_corruption(exporter, episode, tmp_path, change):
    public = json.loads(exporter.visible_bytes(episode))
    if change == 'answer':
        public['test'][0]['output'] = [[6]]
    elif change == 'setting':
        public['settings'] = {'mode': 'all'}
    elif change == 'duplicate':
        public['test'][1]['input'] = public['test'][0]['input']
    raw = (json.dumps(public, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if change == 'whitespace':
        raw = json.dumps(public, indent=2).encode()
    name = '0' * 64 if change == 'wrong_name' else hashlib.sha256(raw).hexdigest()
    path = tmp_path / (name + '.json')
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        exporter.verify_public_file(path)


@pytest.mark.parametrize('invalid', ['failed', 'foreign_task', 'stale_source', 'foreign_program'])
def test_witness_rejects_unqualified_or_stale_bindings(exporter, tmp_path, invalid):
    settings = {'mode': 'blue_count_threshold'}
    current_program = exporter._load('adapter').program(settings)
    qualification = {'schema': 'arcpuzzles-parametric-qualification-v1',
                     'status': 'qualified', 'task_id': exporter.TASK,
                     'source_binding': {'stale': 'binding'},
                     'contract': {}, 'programs': []}
    if invalid == 'failed':
        qualification['status'] = 'failed'
    elif invalid == 'foreign_task':
        qualification['task_id'] = 'unrelated_task'
    elif invalid == 'foreign_program':
        qualification['programs'] = [{'settings': settings, 'program_sha256': '0' * 64}]
    report = {'status': 'passed', 'racket': {'backend': 'racket', 'protected': True},
              'causal_case': {'settings': settings, 'program': current_program}}
    qpath, rpath = tmp_path / 'qualification.json', tmp_path / 'report.json'
    qpath.write_text(json.dumps(qualification))
    rpath.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        exporter.witness(qpath, rpath, tmp_path / 'witness.json')
    assert not (tmp_path / 'witness.json').exists()
