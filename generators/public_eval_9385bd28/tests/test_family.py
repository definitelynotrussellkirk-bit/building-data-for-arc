"""Behavioral checks for the keyed rectangle-composition family."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())


def load(name, base=None):
    base = base or HOME/'workspace/parametric'
    path = base/f'{name}.py'
    assert path.is_file(), f'missing implementation: {path}'
    key = f'keyed_rect_test_{name}_{abs(hash(path))}'
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[key] = mod; spec.loader.exec_module(mod)
    return mod


def originals():
    data = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['9385bd28']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['9385bd28']
    return data['train'] + [dict(pair, output=output) for pair, output in zip(data['test'], gold)]


@pytest.mark.parametrize('index', range(6))
def test_all_official_labels(index):
    pair = originals()[index]
    assert load('engine').solve(pair['input'], 'combine_only') == pair['output']


def test_reverse_key_order_transparency_and_single_object_recolor():
    # Official examples jointly pin reverse row order, transparent zero/background
    # entries, preservation of two fragment markers, and replacement of one square.
    e = load('engine')
    for index in (0, 2, 3, 5):
        pair = originals()[index]
        assert e.solve(pair['input'], 'combine_only') == pair['output']


@pytest.mark.parametrize('seed', [0, 1, 17, 43, 127])
def test_matched_settings_prefixes_teaching_and_stress(seed):
    a = load('adapter')
    base = a.generate(seed, {'finish':'combine_only'}, 6, 4)
    alt = a.generate(seed, {'finish':'highlight_largest_change'}, 6, 4)
    assert [p['input'] for s in ('train','test') for p in base[s]] == [p['input'] for s in ('train','test') for p in alt[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in base[s]}) == 10
    assert a.program({'finish':'combine_only'}).encode() == (HOME/'reference.rkt').read_bytes()
    assert (HOME/'reference.rkt').read_bytes() == (HOME/'workspace/parametric/canonical.rkt').read_bytes()
    for finish, episode in [('combine_only', base), ('highlight_largest_change', alt)]:
        for demos in range(2, 7):
            prefix = a.generate(seed, {'finish':finish}, demos, 4)
            assert prefix['train'] == episode['train'][:demos]
            assert prefix['test'] == episode['test']
        for queries in range(1, 5):
            prefix = a.generate(seed, {'finish':finish}, 2, queries)
            assert prefix['train'] == episode['train'][:2]
            assert prefix['test'] == episode['test'][:queries]
        for rival in a.G.RIVALS:
            assert any(a.G.solve(p['input'], finish, rival=rival) != p['output'] for p in episode['train'][:2]), (finish, rival)
    stress = base['test'][-1]
    assert (len(stress['input']), len(stress['input'][0])) == (30, 30)
    assert all(load('engine').self_check(p['input']) == [] for s in ('train','test') for p in base[s])


def test_causal_counterfactual_uses_raw_box_not_composed_change_component():
    a = load('adapter'); e = load('engine')
    pair = a.generate(17, {'finish':'highlight_largest_change'}, 2, 4)['train'][0]
    info = e.analyze(pair['input'])
    assert info['largest_raw_operation'] != info['largest_changed_component_owner']
    assert e.solve(pair['input'], 'highlight_largest_change', rival='raw_largest_box') != pair['output']


@pytest.mark.parametrize('kwargs', [
    {'seed': True}, {'seed': -1}, {'demos': 1}, {'demos': 7}, {'queries': 0}, {'queries': 5},
    {'queries': True}, {'settings': {}}, {'settings': {'finish':'bad'}},
    {'settings': {'finish':'combine_only','extra':1}},
])
def test_invalid_requests_fail_closed(kwargs):
    a = load('adapter'); args = dict(seed=0, settings={'finish':'combine_only'}, demos=2, queries=4); args.update(kwargs)
    with pytest.raises((ValueError, TypeError)):
        a.generate(**args)


@pytest.mark.parametrize('grid', [[], [[True]], [[0,1],[0]], [[10]], [[0]*31]])
def test_invalid_grids_rejected(grid):
    e = load('engine')
    assert e.self_check(grid)
    with pytest.raises((ValueError, TypeError, IndexError)):
        e.solve(grid, 'combine_only')


def test_public_projection_hides_answers_settings_and_future_queries():
    a = load('adapter')
    full = a.present(17, {'finish':'highlight_largest_change'}, 2, 4, presentation_seed=11)
    one = a.present(17, {'finish':'highlight_largest_change'}, 2, 1, presentation_seed=11)
    assert full['public'][:1] == one['public']
    assert set(full['public'][0]) == {'train','test'} and set(full['public'][0]['test'][0]) == {'input'}
    mutated = copy.deepcopy(full)
    mutated['private']['settings'] = {'finish':'secret'}
    mutated['private']['source_pairs'][0]['output'] = [[9]]
    assert full['public'] == mutated['public']


def test_source_closure_relocates(tmp_path):
    src = HOME/'workspace/parametric'
    for name in ('adapter.py','engine.py','canonical.rkt','highlight.rkt','wrong-intermediate.rkt'):
        shutil.copyfile(src/name, tmp_path/name)
    relocated = load('adapter', tmp_path)
    assert relocated.generate(17, {'finish':'highlight_largest_change'}, 2, 4) == load('adapter').generate(17, {'finish':'highlight_largest_change'}, 2, 4)
