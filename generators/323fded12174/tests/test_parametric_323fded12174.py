"""Focused semantic and boundary checks for the separate row-ranking family."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

@pytest.fixture(scope='module')
def family():
    path = HOME / 'workspace/parametric/prototype.py'
    assert path.is_file(), 'the separate parametric row-ranking implementation is missing'
    spec = importlib.util.spec_from_file_location('test_row_rank_family', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

FIXTURE = [
    [2,0,2,0,7,0,0,0,0],
    [3,3,3,3,0,0,0,0,0],
    [2,3,3,7,2,3,7,0,0],
    [3,0,7,0,3,0,0,0,0],
    [3,2,2,3,2,0,0,0,0],
    [7,0,0,0,7,0,0,0,0],
]

@pytest.mark.parametrize('setting,order', [('occupancy',[2,4,1,0,3,5]), ('anchor_color',[1,2,3,4,0,5])])
def test_whole_rows_and_stable_ties(family, setting, order):
    assert family.reference(FIXTURE, {'rank_by': setting}) == [FIXTURE[i] for i in order]


def test_zero_does_not_choose_anchor_color(family):
    grid = [row + [0]*6 for row in FIXTURE]
    assert family.self_check(grid) == []
    assert family.reference(grid, {'rank_by':'anchor_color'}) == [grid[i] for i in [1,2,3,4,0,5]]
    assert family.row_facts(grid)['anchor_color'] == 3


def test_default_is_exact_catalog_authority(family):
    from arcpuzzles import Catalog
    sources = {v['program_solution'] for v in Catalog(ROOT).get('323fded12174')['variants']}
    assert sources == {family.program({'rank_by':'occupancy'})}

@pytest.mark.parametrize('seed', [0,17,101])
def test_bank_shared_across_settings_and_request_prefixes(family, seed):
    full = family.generate(seed, {'rank_by':'occupancy'}, demos=6, queries=4)
    alternative = family.generate(seed, {'rank_by':'anchor_color'}, demos=6, queries=4)
    short = family.generate(seed, {'rank_by':'anchor_color'}, demos=3, queries=1)
    for part in ('train','test'):
        assert [p['input'] for p in full[part]] == [p['input'] for p in alternative[part]]
        assert short[part] == alternative[part][:len(short[part])]
    assert any(a['output'] != b['output'] for a,b in zip(full['train'][:3],alternative['train'][:3]))
    inputs = [p['input'] for p in full['train'] + full['test']]
    assert len({tuple(map(tuple,g)) for g in inputs}) == 10
    assert all(not family.self_check(g) for g in inputs)
    assert family.generate(seed, {'rank_by':'anchor_color'}, demos=3, queries=1) == short


def test_minimum_and_substantial_maximum_queries(family):
    e = family.generate(0, {'rank_by':'anchor_color'})
    small, large = e['test'][0]['input'], e['test'][3]['input']
    assert (len(small),len(small[0])) == (3,5)
    assert (len(large),len(large[0])) == (30,30)
    assert sum(v != 0 for row in large for v in row) >= 300
    assert len({tuple(row) for row in large}) == 30
    assert len({sum(v != 0 for v in row) for row in large}) >= 8
    assert all(any(row) and 0 in row for row in large)


def test_core_demonstrates_dependency_and_both_stable_ties(family):
    e = family.generate(17, {'rank_by':'anchor_color'})
    for pair in e['train']:
        g=pair['input']; facts=family.row_facts(g)
        assert max(facts['target_counts']) > facts['target_counts'][facts['anchor_index']]
        assert len(set(facts['target_counts'])) < len(g)
        assert len(set(facts['occupancies'])) < len(g)
        assert g != family.reference(g, {'rank_by':'occupancy'})
    assert any(sum(v==0 for v in p['input'][family.row_facts(p['input'])['anchor_index']]) >
               max(family.row_facts(p['input'])['anchor_counts'].values()) for p in e['train'])

@pytest.mark.parametrize('kwargs', [dict(demos=2),dict(demos=7),dict(demos=True),dict(queries=0),dict(queries=5),dict(queries=1.0)])
def test_rejects_unsupported_counts(family,kwargs):
    with pytest.raises(ValueError):
        family.generate(0, {'rank_by':'occupancy'}, **kwargs)

@pytest.mark.parametrize('seed', [-1,2**63,True,1.0,'0'])
def test_rejects_nonliteral_seed(family,seed):
    with pytest.raises(ValueError):
        family.generate(seed, {'rank_by':'occupancy'})

@pytest.mark.parametrize('settings', [{},{'rank_by':'color'},{'rank_by':True},{'rank_by':'occupancy','extra':0},None])
def test_rejects_unknown_or_ambiguous_settings(family,settings):
    with pytest.raises(ValueError):
        family.program(settings)

@pytest.mark.parametrize('grid', [[],[[1]*5]*2,[[1,2,0,0,0]]*3,[[1,2,3,0,0],[1,2,0,0,0],[1,0,0,0,0]],[[True,2,3,0,0],[1,1,0,0,0],[1,0,0,0,0]]])
def test_grammar_rejects_bad_shapes_tied_anchor_and_ambiguous_mode(family,grid):
    assert family.self_check(grid)


def test_native_racket_literal_and_boundary_labels(family):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    runtime = ROOT / 'shared/runtime'
    with _local_imports(runtime, HOME/'workspace/parametric'):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity['protected'] is True
            for mode,order in [('occupancy',[2,4,1,0,3,5]),('anchor_color',[1,2,3,4,0,5])]:
                settings={'rank_by':mode}
                assert apply(family.program(settings),FIXTURE)==[FIXTURE[i] for i in order]
                e=family.generate(0,settings)
                for pair in e['train']+[e['test'][0],e['test'][3]]:
                    assert apply(e['program_solution'],pair['input'])==pair['output']
        finally:
            bridge.close()
