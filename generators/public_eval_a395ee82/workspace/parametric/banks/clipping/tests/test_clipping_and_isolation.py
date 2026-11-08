"""Catch cache poisoning, whole-tile clipping shortcuts, and public metadata leaks."""
import copy
import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/'workspace/parametric'
spec=importlib.util.spec_from_file_location('a395_clipping_tests',P/'union.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

def test_cached_bank_is_not_mutable_by_caller():
    expected=u.generate(97,{'rule':'ink'},2,4)
    bank=u.inputs(97);bank[0][0][0]=(bank[0][0][0]+1)%10
    assert u.generate(97,{'rule':'ink'},2,4)==expected

def test_minimum_lesson_contains_partial_tile_not_whole_tile_rejection():
    for seed in range(16):
        for mode in u.OPTIONS:
            episode=u.generate(seed,{'rule':mode},2,4)
            assert any(u.clipping_predict(p['input'],mode,'drop_partial')!=p['output'] for p in episode['train'])
            assert any(u.clipping_predict(p['input'],mode,'wrap')!=p['output'] for p in episode['train'])

def test_clipped_query_four_boundaries_are_covered():
    edges=set()
    for seed in range(32):
        g=u.clipped_scene(seed,6)
        d=u.one.inspect(g);r,c=d['origin'];h,w=d['shape']
        if r==1:edges.add('top')
        if c==1:edges.add('left')
        if r==len(g)-h-1:edges.add('bottom')
        if c==len(g[0])-w-1:edges.add('right')
        assert u.one.solve(g)==u.two.solve(g)
    assert edges=={'top','left','bottom','right'}

def test_public_projection_invariant_to_private_fields():
    e=u.generate(9,{'rule':'holes'},2,4)
    baseline=u.public_turn(e,0)
    e['settings']={'spoiler':'anything'};e['program_solution']='answer';e['private']={'future':e['test'][1:]}
    for p in e['train']:p['private']='secret'
    for p in e['test']:p['output']=[[9]];p['hidden']='secret'
    assert u.public_turn(e,0)==baseline
    assert set(baseline)=={'train','test'}
    assert set(baseline['test'][0])=={'input'}
    baseline['train'][0]['input'][0][0]=10
    assert all(0<=x<=9 for row in e['train'][0]['input'] for x in row)

@pytest.mark.parametrize('index',[-1,True,1.0,4])
def test_public_index_fails_closed(index):
    with pytest.raises(ValueError):u.public_turn(u.generate(0,{'rule':'ink'},2,4),index)
