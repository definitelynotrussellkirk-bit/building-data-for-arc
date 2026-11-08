"""Focused regression and adversarial tests for the corner-key crop family.

These checks do not imply owner acceptance; native qualification separately
executes every label through protected Racket.
"""
from collections import Counter
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(path, name):
    sp = importlib.util.spec_from_file_location(name, path)
    assert sp is not None and sp.loader is not None
    module = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(module)
    return module


base = _load(ROOT / 'generator.py', 'corner_base_regression')
family = _load(ROOT / 'workspace/parametric/adapter.py', 'corner_parametric_regression')


def test_base_regression_for_incomplete_draws():
    # Observed defects in version 2.1.1: empty key at (0,3),(30,1),
    # and no distractor at (12,1),(22,3) and others.
    for seed, sample in ((0,3),(30,1),(64,0),(71,3),(12,1),(22,3),(68,0)):
        assert base.self_check(base.generate(seed,sample)) == []


def test_base_difficulties_overrides_and_no_shortcut_returns():
    for difficulty in (None,'easy','medium','hard'):
        for n in (1,2,3):
            for seed in range(22):
                grid=base.generate(seed,seed%4,difficulty=difficulty,n_distractors=n)
                assert base.self_check(grid) == []
                assert len(grid)>1 and len(grid[0])>1
                assert sum(v!=0 for row in grid for v in row)>=8
                corners=[grid[0][0],grid[0][-1],grid[-1][0],grid[-1][-1]]
                assert len([x for x in corners if x])==1
                assert len({v for row in grid for v in row if v}) == 1+n


def test_original_program_is_byte_identical_and_alternate_is_not():
    assert family.program({'view':'isolated'})==family.canonical()
    assert family.program({'view':'context'})!=family.canonical()


def test_input_matched_and_first_two_lessons_distinguish_views():
    for seed in range(75):
        a=family.generate(seed,{'view':'isolated'},demos=2)
        b=family.generate(seed,{'view':'context'},demos=2)
        aa=a['train']+a['test'];bb=b['train']+b['test']
        assert [p['input'] for p in aa]==[p['input'] for p in bb]
        assert all(p['output']!=q['output'] for p,q in zip(aa,bb))
        assert len({repr(p['input']) for p in aa})==6
        assert family.lesson_check(a['train'],a['test'])['survivors']==['isolated']
        assert family.lesson_check(b['train'],b['test'])['survivors']==['context']
        assert len({next(v for v in (g[0][0],g[0][-1],g[-1][0],g[-1][-1]) if v)
                    for g in (p['input'] for p in aa[:2])}) >= 1


def test_independent_counts_and_boundaries():
    for demos in (2,3,4,5,6):
        for view in family.VIEWS:
            ep=family.generate(31,{'view':view},demos=demos,queries=4)
            assert len(ep['train'])==demos and len(ep['test'])==4
            assert len(ep['test'][-1]['input'])==30
            assert len(ep['test'][-1]['input'][0])==30
            assert sum(v!=0 for row in ep['test'][-1]['input'] for v in row)>70
            assert len(ep['test'][0]['input'])==9
            assert len(ep['test'][0]['input'][0])==10
            assert family.lesson_check(ep['train'],ep['test'])['survivors']==[view]


@pytest.mark.parametrize('bad_seed',[-1,True,1.5,'2'])
def test_bad_seed_fails(bad_seed):
    with pytest.raises(ValueError):
        family.generate(bad_seed,{'view':'isolated'})


@pytest.mark.parametrize('bad_count',[0,1,7,True,2.4])
def test_bad_demo_count_fails(bad_count):
    with pytest.raises(ValueError):
        family.generate(3,{'view':'context'},demos=bad_count)


@pytest.mark.parametrize('settings',[{}, {'view':'bad'}, {'view':'isolated','leak':7}, {'view':True}])
def test_bad_settings_fail(settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_corner_validation_and_label_certificate_rejection():
    ep=family.generate(9,{'view':'context'},demos=2)
    assert family.lesson_check(ep['train'],ep['test'])['survivors']==['context']
    wrong=[dict(p) for p in ep['train']]
    wrong[0]['output']=family.transform(wrong[0]['input'],'isolated')
    with pytest.raises(ValueError):
        family.lesson_check(wrong,ep['test'])
    grid=[row[:] for row in ep['train'][0]['input']]
    grid[0][0]=7
    grid[0][-1]=8
    with pytest.raises(ValueError):
        family.transform(grid,'isolated')


def test_crossed_intermediate_and_nuisance_controls():
    # Hold the key-colored bbox fixed, change only nuisance cells outside it.
    g=[[0]*12 for _ in range(10)]
    g[0][0]=4
    for r,c in ((2,2),(2,3),(2,4),(3,4),(4,4),(4,5),(4,6)):
        g[r][c]=4
    g[3][5]=6
    x=[row[:] for row in g];y=[row[:] for row in g]
    x[7][7]=3;y[8][10]=8
    for view in family.VIEWS:
        assert family.transform(x,view)==family.transform(y,view)
    # Hold dimensions and all nonkey colors fixed, vary selected footprint.
    z=[row[:] for row in x];z[2][2]=0;z[5][6]=4
    assert family.transform(z,'context')!=family.transform(x,'context')
    assert family.transform(z,'isolated')!=family.transform(x,'isolated')
    # Change actual embedded content without changing the key-color bbox.
    q=[row[:] for row in x];q[3][5]=7
    assert family.transform(q,'isolated')==family.transform(x,'isolated')
    assert family.transform(q,'context')!=family.transform(x,'context')


def test_racket_executes_claimed_labels_both_settings():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge=RacketBridge()
    try:
        for view in family.VIEWS:
            ep=family.generate(13,{'view':view},demos=2)
            for pair in ep['train']+ep['test']:
                bridge.define_grid('g',pair['input'])
                actual=bridge.eval_text(f'({wrap_rule(ep["program_solution"])} g)')
                assert actual==pair['output'], (view,len(pair['input']))
    finally:
        bridge.shutdown()
