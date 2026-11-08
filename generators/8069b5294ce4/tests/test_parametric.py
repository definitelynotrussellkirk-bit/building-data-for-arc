"""Prototype-only regressions: selection, curriculum, requests and public masking."""
import copy
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root

TASK = '8069b5294ce4'

def adapter():
    path = find_root(__file__) / f'generators/{TASK}/workspace/parametric/adapter.py'
    assert path.is_file(), 'native parametric adapter is missing'
    spec = importlib.util.spec_from_file_location('graph_radius_adapter_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_two_hop_selection_depends_on_transitive_graph_not_one_hop():
    a = adapter()
    grid = [[1,1,2,2,3,3,4,4,0], [0]*9, [0,0,0,0,0,0,0,0,7]]
    assert a.claim(grid, 'two_hops') == [[1,8,0],[8,1,8],[0,8,1]]
    assert a.claim(grid, 'whole_cluster') == [[1,8,0,0],[8,1,8,0],[0,8,1,8],[0,0,8,1]]
    assert a.claim(grid, 'one_hop') == [[1,8],[8,1]]


def test_seed_settings_counts_fail_closed():
    a = adapter()
    for kwargs in ({'seed': True}, {'seed': -1}, {'demos': 1}, {'demos': 7},
                   {'demos': 2.0}, {'queries': 0}, {'queries': 5}, {'queries': True},
                   {'settings': {}}, {'settings': {'selection': 'typo'}},
                   {'settings': {'selection': 'two_hops', 'extra': 1}}):
        args = dict(seed=0, settings={'selection':'two_hops'}, demos=3, queries=4)
        args.update(kwargs)
        with pytest.raises(ValueError):
            a.generate(**args)


@pytest.mark.parametrize('seed', [0, 17, 63])
def test_paired_inputs_count_independence_and_no_duplicates(seed):
    a = adapter()
    e2 = a.generate(seed, {'selection':'two_hops'}, 2, 4)
    e6 = a.generate(seed, {'selection':'two_hops'}, 6, 4)
    ec = a.generate(seed, {'selection':'whole_cluster'}, 2, 4)
    assert e2['train'] == e6['train'][:2]
    assert e2['test'] == e6['test']
    assert [p['input'] for p in e2['train']+e2['test']] == [p['input'] for p in ec['train']+ec['test']]
    assert a.generate(seed, {'selection':'two_hops'}, 2, 1)['test'] == e2['test'][:1]
    assert len({str(p['input']) for p in e6['train']+e6['test']}) == 10
    assert a.teaching_check(e2) == []
    assert a.teaching_check(ec) == []


def test_substantive_boundary_scene():
    a = adapter()
    g = a.generate(17, {'selection':'two_hops'}, 3, 4)['test'][3]['input']
    assert len(g) == len(g[0]) == 30
    assert sum(v != 0 for row in g for v in row) >= 200
    assert all(any(edge) for edge in (g[0],g[-1],[r[0] for r in g],[r[-1] for r in g]))
    info = a.analyze(g)
    assert max(info['distances'].values()) >= 3
    assert len(info['objects']) >= 9


def test_public_turn_has_no_private_or_future_fields():
    a = adapter()
    e = a.generate(0, {'selection':'two_hops'}, 3, 4)
    p = a.public_turn(e, 0)
    assert set(p) == {'train', 'test'} and len(p['test']) == 1
    assert set(p['test'][0]) == {'input'}
    private_changed = copy.deepcopy(e)
    private_changed['settings'] = {'leak':'bad'}
    private_changed['program_solution'] = 'bad'
    for q in private_changed['test']:
        q['output'] = [[9]]
    private_changed['test'][1]['input'] = [[8]]
    assert a.public_turn(private_changed, 0) == p
    assert a.public_turn(a.generate(0, {'selection':'two_hops'}, 3, 1), 0) == p
    p['train'][0]['input'][0][0] = 99
    assert a.public_turn(e, 0)['train'][0]['input'][0][0] != 99
    for index in (-1, 4, True):
        with pytest.raises(ValueError): a.public_turn(e,index)

@pytest.mark.parametrize('seed', [54,61])
def test_largest_area_shortcut_is_refuted_at_two_demonstrations(seed):
    a = adapter()
    e = a.generate(seed, {'selection':'whole_cluster'}, 2, 4)
    info = a.analyze(e['train'][0]['input'])
    selected = sum(len(info['objects'][i]['cells']) for i in info['distances'])
    outside = sum(len(o['cells']) for i,o in enumerate(info['objects']) if i not in info['distances'])
    assert outside > selected, 'first lesson must put more area outside the blue cluster'
    assert a.teaching_check(e) == []
