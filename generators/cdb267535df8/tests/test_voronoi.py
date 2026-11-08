"""Canonical/task regression checks; never use this authoring data in a solve."""
from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = 'cdb267535df8'
ROOT = find_root(__file__)
PATHS = [ROOT/'generators'/TASK/'generator.py',
         ROOT/'puzzle_generators/per_puzzle'/TASK/'generator.py']
SPEC = importlib.util.spec_from_file_location('under_test', next(p for p in PATHS if p.is_file()))
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK, root=ROOT)


def reference_python(grid, *, tie_by_seed=False):
    """Independent per-SEED BFS oracle; does not call generator helpers."""
    h,w=len(grid),len(grid[0]); maps=[]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v in (0,5): continue
            ds={(r,c):0}; q=deque([(r,c)])
            while q:
                x,y=q.popleft()
                for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=a<h and 0<=b<w and grid[a][b]!=5 and (a,b) not in ds:
                        ds[a,b]=ds[x,y]+1;q.append((a,b))
            maps.append((v,ds))
    out=deepcopy(grid)
    for r in range(h):
        for c in range(w):
            if grid[r][c]!=0: continue
            candidates=[(ds[r,c],color) for color,ds in maps if (r,c) in ds]
            if not candidates:continue
            distance=min(d for d,_ in candidates)
            nearest=[color for d,color in candidates if d==distance]
            if len(nearest if tie_by_seed else set(nearest))==1:out[r][c]=nearest[0]
    return out


@pytest.mark.parametrize('pair', PAIRS, ids=lambda p: str(p.get('split','pair')))
def test_accepts_canonical(pair):
    assert gen.self_check(pair['input']) == []


@pytest.mark.parametrize('pair', PAIRS)
def test_canonical_python_oracle(pair):
    assert reference_python(pair['input']) == pair['output']
    # All canonical seeds have distinct colors: tie-by-seed cannot be refuted there.
    assert reference_python(pair['input'], tie_by_seed=True) == pair['output']


def test_correct_rule_pin():
    assert getattr(gen,'RULE_HASH',None) == 'cb6c4f271562'


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_all_defaults_are_voronoi_instances(band):
    for i in range(24):
        g=gen.generate(7300+i,i,difficulty=band)
        assert gen.self_check(g)==[]
        # Isolated colored cells are seeds, not multi-cell contact-chain shapes.
        seeds=[v for row in g for v in row if v not in (0,5)]
        assert 4<=len(seeds)<=6
        assert any(5 in row for row in g)
        assert reference_python(g)!=g


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_exhaustive_joint_integer_override_domain(band):
    # 225 exact joint combinations per band. No omitted interactions.
    for h in range(9,14):
        for w in range(11,16):
            for seeds in range(4,7):
                for colors in range(2,5):
                    axes=dict(grid_h=h,grid_w=w,n_seeds=seeds,n_seed_colors=colors)
                    g=gen.generate(209,h*101+w*13+seeds*3+colors,difficulty=band,**axes)
                    assert gen.observe_overrides(g)==axes
                    assert gen.self_check(g)==[]
                    assert gen._prediction(g)==reference_python(g)


@pytest.mark.parametrize('name,value',[
    ('grid_h',8),('grid_h',14),('grid_w',10),('grid_w',16),
    ('n_seeds',3),('n_seeds',7),('n_seed_colors',1),('n_seed_colors',5),
    ('grid_h',True),('n_seeds',4.0),('n_seed_colors','4'),('unknown',3),
    ('palette_kind','warm'),('texture','all_isolated'),
])
def test_rejects_invalid_or_removed_axes(name,value):
    with pytest.raises(ValueError): gen.generate(17,0,**{name:value})


@pytest.mark.parametrize('grid',[None,[],[[]],[[0],[0,5]],[[False,0],[5,3]],[[0,12],[3,5]]])
def test_validator_handles_malformed_grids(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_cyclic_lessons_and_every_query_holdout(band):
    # 32 consecutive starts include all four schedule residues. The labels
    # here are an independent Python oracle, not a claim of Racket execution.
    pairs=[]
    for i in range(35):
        g=gen.generate(1701,i,difficulty=band)
        answer=reference_python(g)
        assert gen._prediction(g)==answer
        assert g==gen.generate(1701,i,difficulty=band)
        if i%4<2:
            assert gen._tie_by_seed(g)!=answer
            assert gen._first_seed_only(g)!=answer
        pairs.append((g,answer))
    for start in range(32):
        lesson=pairs[start:start+4]
        for query in range(4):
            demos=[p for i,p in enumerate(lesson) if i!=query]
            for name,rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(g)!=answer for g,answer in demos), (start,query,name)


@pytest.mark.parametrize('pair',PAIRS)
def test_declared_canonical_shortcuts_really_fit(pair):
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert rival(pair['input'])==pair['output']


def test_duplicate_seed_tie_is_not_color_tie():
    g=[[0]*11 for _ in range(9)]
    g[1][1]=g[1][3]=2; g[7][8]=4; g[7][9]=6; g[4][5]=5
    assert gen.self_check(g)==[]
    assert reference_python(g)[1][2]==2
    assert gen._tie_by_seed(g)[1][2]==0


def test_unreachable_cells_and_existing_seeds_are_preserved():
    g=[[0]*11 for _ in range(9)]
    for r,c in ((3,4),(3,5),(3,6),(4,4),(4,6),(5,4),(5,5),(5,6)):g[r][c]=5
    g[0][0]=2;g[8][10]=3;g[8][1]=4;g[1][9]=6
    out=reference_python(g)
    assert out[4][5]==0
    assert gen._prediction(g)==out
    assert all(out[r][c]==v for r,row in enumerate(g) for c,v in enumerate(row) if v)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_geometric_and_palette_equivariance(band):
    g=gen.generate(2026,0,difficulty=band)
    out=reference_python(g)
    assert gen._prediction([row[::-1] for row in g])==[row[::-1] for row in out]
    assert gen._prediction(g[::-1])==out[::-1]
    trans=lambda a:[list(row) for row in zip(*a)]
    assert gen._prediction(trans(g))==trans(out)
    perm={0:0,5:5,1:9,2:8,3:7,4:6,6:4,7:3,8:2,9:1}
    recolor=lambda a:[[perm[v] for v in row] for row in a]
    assert gen._prediction(recolor(g))==recolor(out)


def test_exact_axis_provenance_matches_pixels():
    from puzzle_generators.base import set_ctx_observer
    contexts=[]
    set_ctx_observer(contexts.append)
    try:
        for i in range(8):
            g=gen.generate(93,i)
            context=contexts[-1]
            for name,value in gen.observe_overrides(g).items():
                assert context.recorded_draws()[name]==value
    finally:set_ctx_observer(None)
