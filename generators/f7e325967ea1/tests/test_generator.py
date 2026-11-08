from copy import deepcopy
import itertools
from pathlib import Path
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HOME/'workspace'))
from probe_support import load_generator, canonical_pairs, midpoint_oracle, transform
gen=load_generator()

@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_exact_controls(band):
    g=gen.generate(17,11,difficulty=band,grid_h=7,grid_w=18,n_distinct_colors=9)
    assert (len(g),len(g[0]))==(7,18)
    assert len({v for row in g for v in row if v})==9
    assert gen.observe_overrides(g)=={'grid_h':7,'grid_w':18,'n_distinct_colors':9}

@pytest.mark.parametrize('key,value',[
    ('typo',1),('grid_h',6),('grid_w',19),('n_distinct_colors',2),
    ('grid_h',True),('grid_w',9.0),('n_distinct_colors','3'),
    ('texture','warm'),('n_chains',2),('chain_len',3),
])
def test_invalid_controls_rejected(key,value):
    with pytest.raises(ValueError):gen.generate(2,4,**{key:value})

@pytest.mark.parametrize('pair',canonical_pairs())
def test_canonical_supported(pair):
    assert callable(getattr(gen,'self_check',None)), 'missing task validator'
    assert gen.self_check(pair['input'])==[]
    assert gen.strict_canonical_like(pair['input'])==[]
    assert midpoint_oracle(pair['input'])==pair['output']

@pytest.mark.parametrize('g',[None,[],[[]],[[0],[0,1]],[[True]],[[10]]])
def test_malformed_diagnostic(g):
    assert callable(getattr(gen,'self_check',None)), 'missing task validator'
    assert gen.self_check(g)

def test_conflicting_target_rejected():
    g=[[0]*5 for _ in range(5)]
    for r,c,v in [(1,1,2),(3,3,2),(1,3,4),(3,1,4)]:g[r][c]=v
    assert callable(getattr(gen,'self_check',None)), 'missing task validator'
    assert any('conflict' in e for e in gen.self_check(g))

def test_pin_and_canonical_shortcuts():
    assert getattr(gen,'RULE_HASH',None)=='003fd587a0a4'
    assert getattr(gen,'CANONICAL_SHORTCUTS',None)
    for name,fn in gen.CANONICAL_SHORTCUTS.items():
        assert all(fn(p['input'])==p['output'] for p in canonical_pairs()),name

@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_every_cyclic_lesson_start_teaches_declared_rivals(band):
    assert getattr(gen,'LESSON_COMPETITORS',None)
    for start in range(3):
        for seed in range(10):
            gs=[gen.generate(seed,start+j,difficulty=band) for j in range(4)]
            demos=[{'input':g,'output':midpoint_oracle(g)} for g in gs[:3]]
            query={'input':gs[3],'output':midpoint_oracle(gs[3])}
            assert gen.lesson_identifiable(demos,query)==[]
            for name,fn in gen.LESSON_COMPETITORS.items():
                assert any(fn(p['input'])!=p['output'] for p in demos),(name,band,seed,start)

@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_lawfulness_determinism_and_diversity(band):
    seen=set();shapes=set();colors=set()
    for i in range(60):
        g=gen.generate(8100+i,i,difficulty=band)
        assert g==gen.generate(8100+i,i,difficulty=band)
        assert gen.self_check(g)==[]
        assert midpoint_oracle(g)!=g
        old=deepcopy(g)
        for fn in gen.LESSON_COMPETITORS.values():fn(g)
        assert g==old
        seen.add(str(g));shapes.add((len(g),len(g[0])))
        colors.update(v for row in g for v in row if v)
    assert len(seen)==60
    assert len(shapes)>4
    assert colors==set(range(1,10))

@pytest.mark.parametrize('rotation,reflect',itertools.product(range(4),(False,True)))
def test_geometric_equivariance(rotation,reflect):
    assert callable(getattr(gen,'self_check',None)), 'missing task validator'
    for i in range(9):
        g=gen.generate(101,i)
        t=transform(g,rotation,reflect)
        assert gen.self_check(t)==[]
        assert midpoint_oracle(t)==transform(midpoint_oracle(g),rotation,reflect)
