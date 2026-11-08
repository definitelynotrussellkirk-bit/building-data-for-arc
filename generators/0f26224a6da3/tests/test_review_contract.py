"""Regression tests for review-82548b4b24894693; run explicitly, not root discovery."""
from __future__ import annotations
import copy
import importlib.util
import json
import sys
from pathlib import Path
import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('reviewed_singletons', HERE.parents[1] / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
DIRS = ((-1,0),(1,0),(0,-1),(0,1))


def active(g):
    h,w=len(g),len(g[0])
    return [(r,c) for r in range(h) for c in range(w) if g[r][c] and
            all(not(0 <= r+dr < h and 0 <= c+dc < w) or g[r+dr][c+dc]==0 for dr,dc in DIRS)]


def test_default_distribution_not_a_modulo_three_lattice():
    grids=[gen.generate(19,i) for i in range(60)]
    assert any(any(r%3!=1 or c%3!=1 for r,c in active(g)) for g in grids)


def test_default_distribution_has_border_sources():
    grids=[gen.generate(19,i) for i in range(60)]
    assert any(any(r in (0,len(g)-1) or c in (0,len(g[0])-1) for r,c in active(g)) for g in grids)


@pytest.mark.parametrize('kind,pool',[('warm',{2,4,6,7,9}),('cool',{1,3,5,8}),('primary',{1,2,4})])
def test_palette_control_is_effective(kind,pool):
    for i in range(12):
        g=gen.generate(17,i,palette_kind=kind)
        assert {v for row in g for v in row if v} <= pool


def test_unknown_override_rejected():
    with pytest.raises(ValueError,match='unknown'):
        gen.generate(19,0,typo_axis=True)


@pytest.mark.parametrize('g',[
    [[0]*7 for _ in range(7)], [[1]*7 for _ in range(7)], [[]],
    [[0]*7 for _ in range(6)]+[[0]*6+[10]],
    [[0]*7 for _ in range(6)]+[[0]*6+[True]],
    [[0]*7 for _ in range(6)]+[[0]*6+[1.5]],
])
def test_malformed_or_rule_hiding_rejected(g):
    assert gen.self_check(g)


def test_conflicting_expansion_fronts_rejected():
    g=[[0]*7 for _ in range(7)];g[2][2]=2;g[2][4]=3
    assert gen.self_check(g), 'different-color sources share a blank target'


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_seeded_defaults_validate_and_do_not_mutate(band):
    for seed in range(10):
        for i in range(9):
            g=gen.generate(seed,i,difficulty=band)
            assert gen.self_check(g)==[]
            before=copy.deepcopy(g)
            assert gen.generate(seed,i,difficulty=band)==g
            assert len(active(g))>=2
            assert g==before


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_complete_three_demo_windows_refute_declared_rivals(band):
    assert hasattr(gen,'LESSON_COMPETITORS'), 'no semantic competitor contract'
    for seed in range(5):
        for start in range(3):
            demos=[{'input':gen.generate(seed,start+i,difficulty=band)} for i in range(3)]
            for d in demos:d['output']=gen.rule_mirror(d['input'])
            query={'input':gen.generate(seed,start+3,difficulty=band)}
            assert gen.lesson_identifiable(demos,query)==[]
            assert all(any(fn(d['input'])!=d['output'] for d in demos) for fn in gen.LESSON_COMPETITORS.values())


def test_canonical_shortcuts_fit_all_three_canonical_pairs():
    assert hasattr(gen,'CANONICAL_SHORTCUTS')
    rows=[json.loads(s) for s in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
    row=next(r for r in rows if r['task_id']==gen.TASK_ID)
    pairs=row['train']+row['test']
    assert len(pairs)==3
    for p in pairs:
        assert gen.self_check(p['input'])==[]
        assert gen.strict_canonical_like(p['input'])==[]
        assert gen.rule_mirror(p['input'])==p['output']
        for name,fn in gen.CANONICAL_SHORTCUTS.items():
            assert fn(p['input'])==p['output'],name


@pytest.mark.parametrize('scene',['interior','edge_distractor','diagonal_distractor'])
def test_boundary_override_dimensions_and_source_count(scene):
    for h,w in [(7,7),(7,15),(15,7),(15,15)]:
        for n in [2,5]:
            for seed in range(3):
                g=gen.generate(seed,0,grid_h=h,grid_w=w,n_cells=n,scene=scene)
                assert (len(g),len(g[0]))==(h,w)
                assert len(active(g))==n
                assert gen.self_check(g)==[]
                assert gen.observe_overrides(g)['n_cells']==n


@pytest.mark.parametrize('ov',[
    {'grid_h':6},{'grid_w':16},{'n_cells':1},{'n_cells':6},
    {'grid_h':7.5},{'n_cells':True},{'palette_kind':'bogus'},{'scene':'bogus'},
    {'texture':'warm','palette_kind':'cool'},
])
def test_invalid_override_is_loud(ov):
    with pytest.raises(ValueError):gen.generate(0,0,**ov)


def test_degenerates_are_explicit_and_rejected_for_training():
    for name in gen.DEGENERATE_TEXTURES:
        assert gen.self_check(gen.generate(0,0,texture=name)),name


def test_query_only_disagreement_is_identifiability_failure():
    assert hasattr(gen,'lesson_identifiable')
    demos=[{'input':gen.generate(8,i,scene='interior')} for i in range(3)]
    for d in demos:d['output']=gen.rule_mirror(d['input'])
    query={'input':gen.generate(8,4,scene='edge_distractor')}
    assert gen.lesson_identifiable(demos,query)
