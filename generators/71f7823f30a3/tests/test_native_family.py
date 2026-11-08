"""Native row-local color selection and reflection contracts."""
import copy
import importlib.util
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('row_mirror_native_test',HOME/'workspace/parametric/native_family.py')
family=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


def fixture():
    return [[0,1,0,1,9,0,2,0,3],
            [0,2,0,0,0,0,0,0,3],
            [2,0,2,9,0,4,0,0,0],
            [0,0,0,0,0,0,0,0,0]]


def test_exact_canonical_default():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    exact={v['program_solution'] for v in Catalog(find_root(HOME)).get('71f7823f30a3')['variants']}
    assert {family.program()}==exact


def test_all_programs_parse_through_native_rule_wrapper():
    from puzzle_generators.rule_wrap import wrap_rule
    for setting in family.SETTINGS:
        assert wrap_rule(family.program(setting)).strip().startswith('(lambda')


def test_selected_color_controls_remote_copy_and_orphans_are_unchanged():
    grid=fixture(); before=copy.deepcopy(grid)
    near=family.python_apply(grid,{'copy_policy':'nearest_color'})
    far=family.python_apply(grid,{'copy_policy':'farthest_color'})
    all_=family.python_apply(grid)
    assert near[0]==[0,1,0,1,9,1,2,1,3]
    assert far[0]==[3,1,0,1,9,0,2,0,3]
    assert all_[0]==[3,1,2,1,9,1,2,1,3]
    assert near[2]==[2,0,2,9,2,4,2,0,0]
    assert near[1]==far[1]==all_[1]==grid[1]
    assert grid==before
    assert near is not grid and near[0] is not grid[0]


@pytest.mark.parametrize('value',[True,-1,2**63,0.0,'0',None])
def test_exact_seed_bounds(value):
    with pytest.raises(ValueError):family.generate(value)


@pytest.mark.parametrize('kwargs',[{'demos':True},{'demos':1},{'demos':7},{'demos':3.0},
                                    {'queries':False},{'queries':0},{'queries':5},{'queries':'4'}])
def test_exact_independent_count_bounds(kwargs):
    with pytest.raises(ValueError):family.generate(0,**kwargs)


@pytest.mark.parametrize('settings',[{'copy_policy':'nearest'},{'copy_policy':False},
                                      {'unknown':'all'},[], 'all',{'copy_policy':None}])
def test_strict_settings(settings):
    with pytest.raises(ValueError):family.generate(0,settings)


def test_input_bank_independent_of_counts_and_settings():
    for seed in (0,1,17,2**63-1):
        baseline=None
        for setting in family.SETTINGS:
            full=family.generate(seed,setting,6,4)
            ins=[p['input'] for split in ('train','test') for p in full[split]]
            assert len({repr(g) for g in ins})==10
            if baseline is None:baseline=ins
            assert ins==baseline
            short=family.generate(seed,setting,2,1)
            assert short['train']==full['train'][:2]
            assert short['test']==full['test'][:1]
            assert full['program_solution']==family.program(setting)
            assert full['meta']['candidate_attempts']==10


def test_demo_only_identification_and_real_size_boundaries():
    for seed in range(8):
        for setting in family.SETTINGS:
            e=family.generate(seed,setting,6,4)
            survivors=[s for s in family.SETTINGS if all(family.python_apply(p['input'],s)==p['output']
                                                        for p in e['train'][:2])]
            assert survivors==[setting]
            assert (len(e['train'][2]['input']),len(e['train'][2]['input'][0]))==(4,7)
            for pair in (e['train'][5],e['test'][3]):
                assert len(pair['input'])==len(pair['output'])==30
                assert all(len(row)==30 for row in pair['input']+pair['output'])
                assert sum(c not in (0,9) for row in pair['input'] for c in row)>=200
                assert all(any(pair['input'][r][c] for r in range(r0,r0+15) for c in range(c0,c0+15))
                           for r0,c0 in ((0,0),(0,15),(15,0),(15,15)))


def test_cores_vary_frequency_rank_and_selected_color_by_row():
    e=family.generate(0,demos=2,queries=4)
    for pair in e['train']:
        info=family.analyze_scene(pair['input'])
        assert len({r['nearest_color'] for r in info['anchored']})>=3
        assert len({r['farthest_color'] for r in info['anchored']})>=3
        assert info['orphan_nonzero']>0
    info=family.analyze_scene(e['train'][1]['input'])
    counts=[{c:sum(s['color']==c for s in row['sources']) for c in {s['color'] for s in row['sources']}}
            for row in info['anchored']]
    for policy in ('nearest_color','farthest_color'):
        assert any(counts[i][row[policy]]>min(counts[i].values()) for i,row in enumerate(info['anchored']))
        assert any(counts[i][row[policy]]<max(counts[i].values()) for i,row in enumerate(info['anchored']))


def test_cores_separate_individual_cues_from_color_mean_and_other_extent():
    from fractions import Fraction
    e=family.generate(0,demos=2,queries=4)
    rows=[r for p in e['train'] for r in family.analyze_scene(p['input'])['anchored']]
    for policy,aggregate,rank in (
        ('nearest_color',lambda ds:Fraction(sum(ds),len(ds)),min),
        ('nearest_color',max,min),
        ('farthest_color',lambda ds:Fraction(sum(ds),len(ds)),max),
        ('farthest_color',min,max),
    ):
        refuted=False
        for row in rows:
            ds={c:[s['distance'] for s in row['sources'] if s['color']==c]
                for c in {s['color'] for s in row['sources']}}
            scores={c:aggregate(v) for c,v in ds.items()}
            if scores[row[policy]]!=rank(scores.values()):refuted=True
        assert refuted,policy


@pytest.mark.parametrize('defect',['duplicate_anchor','occupied_target','out_of_bounds','bool_cell','no_orphans'])
def test_rejects_invalid_grammar(defect):
    g=fixture()
    if defect=='duplicate_anchor':g[0][0]=9
    elif defect=='occupied_target':g[0][5]=4
    elif defect=='out_of_bounds':g[2][8]=4
    elif defect=='bool_cell':g[1][0]=True
    elif defect=='no_orphans':g[1]=g[0][:];g[3]=g[2][:]
    with pytest.raises(ValueError):family.analyze_scene(g)
