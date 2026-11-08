"""Portable regressions; oracle uses pixel flood-fill independently of the sampler."""
from collections import deque
from itertools import product
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '28ba67946524'
ROOT = find_root(__file__)
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
if not SOURCE.exists():
    SOURCE = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('reviewed_contact_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def graph(grid, *, diagonal_contacts=False):
    h,w = len(grid),len(grid[0])
    owner = {}; components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r,c) in owner:
                continue
            i = len(components); cells = []; queue = deque([(r,c)]); owner[r,c] = i
            while queue:
                p = queue.popleft(); cells.append(p)
                for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)):
                    y,x=q
                    if 0 <= y < h and 0 <= x < w and q not in owner and grid[y][x] == grid[r][c]:
                        owner[q]=i; queue.append(q)
            components.append((grid[r][c],cells))
    neighbors = [set() for _ in components]
    offsets = [(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1)
               if (dr or dc) and (diagonal_contacts or abs(dr)+abs(dc)==1)]
    for (r,c),i in owner.items():
        for dr,dc in offsets:
            j = owner.get((r+dr,c+dc))
            if j is not None and j != i: neighbors[i].add(j)
    seed = next(i for i,(color,_) in enumerate(components) if color == 1)
    distances = {seed:0}; queue=deque([seed])
    while queue:
        i=queue.popleft()
        for j in neighbors[i]:
            if j not in distances: distances[j]=distances[i]+1;queue.append(j)
    return components,neighbors,distances


def oracle(grid, *, diagonal_contacts=False):
    components,_,distances=graph(grid,diagonal_contacts=diagonal_contacts)
    result=[[0]*len(grid[0]) for _ in grid]
    for i,d in distances.items():
        if d==2:
            for r,c in components[i][1]: result[r][c]=8
    return result


def two_edge_walk_output(grid):
    """Wrong shortcut: keep every nonseed endpoint of a two-edge walk."""
    components,neighbors,distances=graph(grid)
    seed=next(i for i,d in distances.items() if d==0)
    selected={j for i in neighbors[seed] for j in neighbors[i] if j != seed}
    result=[[0]*len(grid[0]) for _ in grid]
    for i in selected:
        for r,c in components[i][1]: result[r][c]=8
    return result


def observed(grid):
    components,_,distances=graph(grid)
    return {'grid_h':len(grid),'grid_w':len(grid[0]),
            'chain_len':max(distances.values()),'n_distractors':len(components)-len(distances)}


def test_canonical_support_and_oracle():
    pairs=canonical_pairs(TASK,root=ROOT)
    assert len(pairs)==3
    for p in pairs:
        assert gen.self_check(p['input'])==[]
        assert oracle(p['input'])==p['output']
    assert gen.RULE_HASH=='88eede4e9a69'


@pytest.mark.parametrize('bad', [[],[[]],[[1,2],[3]],[[1,2.0,3]],[[1,2,13]],
    [[True,2,3]],[[1,2,3,0,1]],[[0,2,3]],[[1,2,0,3]]])
def test_validator_rejects_malformed_or_ambiguous_seed(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('kwargs', [dict(typo=2),dict(chain_len=True),dict(chain_len=3.5),
    dict(n_distractors='2'),dict(grid_h=7),dict(chain_len=7),dict(n_distractors=0)])
def test_invalid_overrides_raise(kwargs):
    with pytest.raises(ValueError): gen.generate(17,0,difficulty='easy',**kwargs)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_joint_boundary_overrides_are_exact(band):
    for h,w,length,distractors,index in product((8,18),(10,20),(3,6),(1,4),(0,1)):
        controls=dict(grid_h=h,grid_w=w,chain_len=length,n_distractors=distractors)
        grid=gen.generate(17,index,difficulty=band,**controls)
        assert gen.self_check(grid)==[]
        assert observed(grid)==controls
        assert gen.observe_overrides(grid)==controls
        assert grid==gen.generate(17,index,difficulty=band,**controls)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_branch_witness_is_real_and_refutes_every_declared_rival(band):
    for seed in range(12):
        grid=gen.generate(seed,1,difficulty=band)
        components,neighbors,distances=graph(grid)
        targets=[i for i,d in distances.items() if d==2]
        assert len(targets)>=2
        assert sum(len(neighbors[i]) for i in distances)//2 >= len(distances)  # cycle
        assert any(components[j][0] in {components[i][0] for i in targets}
                   for j in range(len(components)) if j not in distances)
        expected=oracle(grid)
        assert oracle(grid,diagonal_contacts=True)!=expected
        for name,rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid)!=expected, name


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_branch_refutes_two_edge_walk_without_shortest_distance_filter(band):
    for seed in range(12):
        grid=gen.generate(seed,1,difficulty=band)
        _,neighbors,distances=graph(grid)
        source=next(i for i,d in distances.items() if d==0)
        two_edge={j for i in neighbors[source] for j in neighbors[i] if j != source}
        assert any(distances[j] < 2 for j in two_edge), seed
        assert two_edge_walk_output(grid) != oracle(grid), seed


def test_declared_two_edge_walk_rival_matches_independent_probe():
    rival=gen.LESSON_COMPETITORS['two_edge_walk']
    witness=gen.SEMANTIC_WITNESSES['shorter_two_step_endpoint']
    for band in ('easy','medium','hard'):
        for seed in range(12):
            grid=gen.generate(seed,1,difficulty=band)
            assert rival(grid)==two_edge_walk_output(grid)
            assert witness(grid)


def test_curriculum_probe_reports_the_actual_declared_rivals(tmp_path,monkeypatch):
    source=ROOT/'generators'/TASK/'workspace'/'probe_curriculum.py'
    spec=importlib.util.spec_from_file_location('reviewed_contact_probe',source)
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    out=tmp_path/'probe.json'
    monkeypatch.setattr(sys,'argv',['probe_curriculum.py','--out',str(out),
                                   '--seeds','1','--samples','2'])
    assert probe.main()==0
    report=json.loads(out.read_text())
    assert report['cyclic_windows']['declared_rivals']==sorted(gen.LESSON_COMPETITORS)
    assert report['cyclic_windows']['scope']==(
        f"independent Python oracle; overlapping windows; "
        f"{len(gen.LESSON_COMPETITORS)} declared rivals only")


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_three_demos_identify_declared_rivals_for_all_cyclic_starts_and_rotations(band):
    assert gen.LESSON_COMPETITORS
    for seed in (0,1,17,42):
        for start in range(4):
            grids=[gen.generate(seed,start+i,difficulty=band) for i in range(4)]
            pairs=[{'input':g,'output':oracle(g)} for g in grids]
            for q in range(4):
                demos=[p for i,p in enumerate(pairs) if i!=q]
                for name,rival in gen.LESSON_COMPETITORS.items():
                    assert (any(rival(p['input'])!=p['output'] for p in demos)
                            or rival(pairs[q]['input'])==pairs[q]['output']), (seed,start,q,name)
                assert gen.lesson_identifiable(demos,pairs[q])==[]


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    assert gen.CANONICAL_SHORTCUTS
    for name,rival in gen.CANONICAL_SHORTCUTS.items():
        for p in canonical_pairs(TASK,root=ROOT): assert rival(p['input'])==p['output'],name


def test_schedule_does_not_depend_on_seed_or_band():
    for seed,band in product((0,42),('easy','medium','hard')):
        assert [gen.schedule_profile(seed,i,band) for i in range(4)]==['path','branch_cycle']*2
