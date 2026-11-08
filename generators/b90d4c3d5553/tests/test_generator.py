"""Task-local regression suite; helpers in workspace are independent of production."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HOME/'workspace'))
from reference_probe import (BASES, canonical_pairs, frame, geometry_output,
                             lift, load_generator, observed, witness_input)
gen=load_generator(os.environ.get('GENERATOR_UNDER_TEST'))


@pytest.mark.parametrize('pair',canonical_pairs(),ids=['train0','train1','test0'])
def test_accepts_canonical_frames(pair):
    assert gen.self_check(pair['input']) == []
    assert geometry_output(pair['input']) == pair['output']


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_exact_overrides_in_every_band(band):
    options=dict(grid_h=10,grid_w=14,n_pairs=1,n_noise=0,n_axis=5,n_distractors=4,
                 source_orientation=7,target_orientation=5)
    g=gen.generate(17,9,difficulty=band,**options)
    assert gen.self_check(g) == []
    assert observed(g) == options
    assert gen.observe_overrides(g) == options


@pytest.mark.parametrize('key,value',[
    ('typo',1),('n_pairs',0),('n_pairs',7),('n_noise',-1),('n_noise',5),
    ('n_axis',6),('n_distractors',5),('source_orientation',8),
    ('target_orientation',-1),('grid_h',9),('grid_w',13),('n_pairs',2.5),
    ('grid_h',True),('n_noise','2'),
])
def test_rejects_invalid_overrides(key,value):
    with pytest.raises(ValueError):gen.generate(0,0,**{key:value})


@pytest.mark.parametrize('index',range(64))
def test_all_independent_frame_orientations(index):
    so,to=divmod(index,8)
    g=gen.generate(73,index,grid_h=16,grid_w=18,source_orientation=so,target_orientation=to,
                   n_pairs=3,n_noise=2,n_axis=2,n_distractors=2)
    assert gen.self_check(g) == []
    assert frame(g,(2,3,4))[1:] == BASES[so]
    assert frame(g,(5,6,7))[1:] == BASES[to]
    obs=observed(g)
    assert (obs['n_pairs'],obs['n_noise'],obs['n_axis'],obs['n_distractors']) == (3,2,2,2)
    assert geometry_output(g) != geometry_output(g,strict_pairs=True)


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_distribution_covers_missing_branches(band):
    bases=set();shapes=set();counts=set();axes=set();sides=set()
    for i in range(256):
        g=gen.generate(2100+i,i*11,difficulty=band)
        assert gen.self_check(g) == []
        assert g == gen.generate(2100+i,i*11,difficulty=band)
        stats=observed(g);src=frame(g,(2,3,4))[0];tgt=frame(g,(5,6,7))[0]
        bases.add((stats['source_orientation'],stats['target_orientation']))
        shapes.add((len(g),len(g[0])));counts.add(stats['n_pairs']);axes.add(stats['n_axis'])
        sides.add((tgt[1]>src[1])-(tgt[1]<src[1]))
        original=deepcopy(g);out=geometry_output(g)
        assert g == original
        assert sum(a!=b for rowa,rowb in zip(g,out) for a,b in zip(rowa,rowb)) == 2*stats['n_pairs']+stats['n_axis']
    assert len(bases) >= 60
    assert len(shapes) > 25
    assert counts == set(range(1,7))
    assert max(axes) > 0
    assert {-1,1} <= sides


def test_axis_counterexample_and_canonical_rival_fit():
    assert all(geometry_output(p['input'],strict_pairs=True) == p['output'] for p in canonical_pairs())
    g=witness_input()
    assert gen.self_check(g) == []
    out=geometry_output(g);rival=geometry_output(g,strict_pairs=True)
    assert [(r,c) for r in range(10) for c in range(14) if out[r][c] != rival[r][c]] == [(4,10)]


@pytest.mark.parametrize('mutation',['extra_frame_color','unknown_color','target_marker','erase_frame','remove_pairs'])
def test_validator_rejects_destructive_mutations(mutation):
    g=gen.generate(4,2,n_axis=0,n_distractors=0,n_pairs=2,n_noise=1)
    if mutation=='extra_frame_color':g[0][0]=2
    if mutation=='unknown_color':g[0][0]=9
    if mutation=='target_marker':
        r,c=lift(frame(g,(5,6,7)),(-2,-2));g[r][c]=8
    if mutation=='erase_frame':
        r,c=frame(g,(2,3,4))[0];g[r][c]=0
    if mutation=='remove_pairs':
        src=frame(g,(2,3,4))
        for r,row in enumerate(g):
            for c,value in enumerate(row):
                if value==8:g[r][c]=0
    assert gen.self_check(g)


@pytest.mark.parametrize('g',[None,[],[[]],[[0],[0,1]],[[True]*14 for _ in range(10)]])
def test_malformed_grid_is_diagnostic_not_exception(g):
    assert gen.self_check(g)


def test_keyed_rng_independent_of_python_hash_seed():
    script=("import sys,json;sys.path.insert(0,sys.argv[1]);from reference_probe import load_generator;"
            "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))")
    results=[]
    for seed in ('1','901'):
        env=dict(os.environ,PYTHONHASHSEED=seed,PYTHONDONTWRITEBYTECODE='1')
        results.append(subprocess.check_output([sys.executable,'-B','-c',script,str(HOME/'workspace')],env=env,text=True))
    assert results[0]==results[1]


def test_cache_eviction_and_call_order_do_not_change_pixels():
    before=gen.generate(412,111,difficulty='hard')
    for i in range(200):gen.generate(i,i*3)
    gen._origin_sets.cache_clear()
    gen._target_origins.cache_clear()
    assert gen.generate(412,111,difficulty='hard') == before


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


@pytest.mark.parametrize('turns,reflect',[(r,f) for r in range(4) for f in (False,True)])
def test_global_dihedral_equivariance(turns,reflect):
    def transform(g):
        result=deepcopy(g)
        if reflect:result=[row[::-1] for row in result]
        for _ in range(turns):result=_rot90(result)
        return result
    for i in range(20):
        g=gen.generate(900+i,i,n_axis=2,n_distractors=3)
        changed=transform(g)
        assert gen.self_check(changed) == []
        assert geometry_output(changed) == transform(geometry_output(g))


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs
    status=racket_runtime_status()
    if not status['available']:
        pytest.skip(status['reason'])
    grids=[p['input'] for p in canonical_pairs()]+[witness_input()]
    grids += [gen.generate(319,i,source_orientation=i//8,target_orientation=i%8,n_axis=1,n_distractors=2) for i in range(64)]
    assert racket_outputs(grids) == [geometry_output(g) for g in grids]


def test_semantic_witness_is_a_real_geometry_counterexample():
    for i in range(64):
        g=gen.generate(712,i,n_axis=1,source_orientation=i//8,target_orientation=i%8)
        assert gen.strict_canonical_like(g) == []
        assert gen.SEMANTIC_WITNESSES['self_mirror'](g)
        rival=gen.SEMANTIC_RIVALS['distinct_pairs_only'](g)
        assert rival == geometry_output(g,strict_pairs=True)
        assert rival != geometry_output(g)
