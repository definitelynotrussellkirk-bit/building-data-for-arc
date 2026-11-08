"""Prototype export checks; these do not assert canonical-generator approval."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PROBE_PATH = Path(__file__).resolve().parents[1] / 'workspace/parametric/probe.py'


def load_probe():
    assert PROBE_PATH.is_file(), 'The task-local replay/export probe is missing'
    spec = importlib.util.spec_from_file_location('_25e78410d5bb_export_test', PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {'seed': 17, 'settings': {'retention': 'all'}, 'program_solution': 'private',
            'private_metadata': {'answer_hint': 'private'},
            'train': [{'input': [[1, 0]], 'output': [[1, 1]]}],
            'test': [{'input': [[2, 0]], 'output': [[2, 2]]},
                     {'input': [[3, 0]], 'output': [[3, 3]]}]}


def test_export_identity_uses_exact_visible_bytes_only():
    probe = load_probe()
    value = episode()
    expected = (b'{"test":[{"input":[[2,0]]},{"input":[[3,0]]}],'
                b'"train":[{"input":[[1,0]],"output":[[1,1]]}]}\n')
    item, = probe.build_export_plan([value])
    assert item['public_bytes'] == expected
    assert item['public_id'] == hashlib.sha256(expected).hexdigest()
    altered = deepcopy(value)
    altered.update(seed=999, settings={'retention': 'largest_filled_component'},
                   program_solution='different private text', private_metadata={'hidden': True})
    for pair in altered['test']:
        pair['output'] = [[9]]
    other, = probe.build_export_plan([altered])
    assert other['public_id'] == item['public_id']
    assert other['public_bytes'] == item['public_bytes']


def test_first_turn_uses_only_demos_and_first_query_input():
    probe = load_probe()
    value = episode()
    expected = (b'{"test":[{"input":[[2,0]]}],'
                b'"train":[{"input":[[1,0]],"output":[[1,1]]}]}\n')
    assert probe.first_turn_bytes(value) == expected
    value['test'][0]['output'] = [[9]]
    value['test'][1] = {'input': [[8, 8, 8]], 'output': [[7]]}
    value['future_turn_count'] = 200
    assert probe.first_turn_bytes(value) == expected
    value['test'] = value['test'][:1]
    assert probe.first_turn_bytes(value) == expected


def test_duplicate_visible_payloads_are_rejected_despite_private_differences():
    probe = load_probe()
    first = episode()
    second = deepcopy(first)
    second['seed'] = 999
    second['test'][0]['output'] = [[9]]
    with pytest.raises(ValueError, match='duplicate public'):
        probe.build_export_plan([first, second])


def test_writer_sorts_public_ids_and_keeps_certificates_private(tmp_path):
    probe = load_probe()
    a = episode()
    b = deepcopy(a)
    b['train'][0]['output'] = [[4, 4]]
    plan = probe.build_export_plan([a, b])
    destination = tmp_path / 'export'
    certificates = [{'public_id': item['public_id'], 'settings': {'retention': 'all'},
                     'seed': 17, 'reference_labels_verified': 3} for item in plan]
    summary = {'status': 'passed', 'scope': 'unit fixture only'}
    probe.write_export(destination, plan, certificates, summary)
    rows = (destination / 'public.jsonl').read_bytes().splitlines(keepends=True)
    ids = [hashlib.sha256(row).hexdigest() for row in rows]
    assert ids == sorted(ids)
    assert len(ids) == 2
    for public_id, raw in zip(ids, rows):
        assert (destination / 'public' / (public_id + '.json')).read_bytes() == raw
        public = json.loads(raw)
        assert set(public) == {'train', 'test'}
        assert all(set(pair) == {'input'} for pair in public['test'])
    assert len((destination / 'episodes.private.jsonl').read_text().splitlines()) == 2
    assert len((destination / 'certificates.private.jsonl').read_text().splitlines()) == 2
    assert json.loads((destination / 'summary.private.json').read_text())['status'] == 'passed'


def test_writer_refuses_existing_destination_without_modifying_it(tmp_path):
    probe = load_probe()
    destination = tmp_path / 'existing'
    destination.mkdir()
    marker = destination / 'keep.txt'
    marker.write_text('existing user data')
    with pytest.raises(FileExistsError):
        probe.write_export(destination, probe.build_export_plan([episode()]), [], {})
    assert list(destination.iterdir()) == [marker]
    assert marker.read_text() == 'existing user data'


def test_named_rival_surviving_all_demos_is_rejected_even_if_queries_agree():
    """Actual protected replay must reject an underidentified named rival."""
    probe = load_probe()
    identity = '(rule! (lambda (g) g))'
    nines = '(rule! (lambda (g) (map (lambda (row) (map (lambda (cell) 9) row)) g)))'
    rival = '(rule! (lambda (g) (if (= (length g) 1) g (reverse g))))'

    def evaluate(grid, retention='all', rival=None):
        if retention != 'all':
            return [[9 for _ in row] for row in grid]
        return deepcopy(list(reversed(grid)) if rival and len(grid) != 1 else grid)

    adapter = SimpleNamespace(program=lambda settings: identity if settings['retention'] == 'all' else nines)
    programs = SimpleNamespace(evaluate=evaluate, rivals_for=lambda retention: ('reverse_multirow',),
                               rival_program=lambda name, retention: rival)
    value = {'seed': 0, 'settings': {'retention': 'all'}, 'program_solution': identity,
             'program_sha256': hashlib.sha256(identity.encode()).hexdigest(),
             'train': [{'input': [[1, 0]], 'output': [[1, 0]]}],
             'test': [{'input': [[2, 0]], 'output': [[2, 0]]}]}
    with probe._local_runtime():
        replay = probe.ProtectedReplay()
        try:
            with pytest.raises(ValueError, match='Named rival survives demonstrations'):
                probe._check_episode(value, adapter, programs, replay)
        finally:
            replay.close()
