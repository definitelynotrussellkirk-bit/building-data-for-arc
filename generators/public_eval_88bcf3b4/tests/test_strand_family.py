"""Behavioral checks: contour extraction, conserved length, role reuse and privacy."""
from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]

def adapter():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(), 'The native strand adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('strand_test_adapter',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

PAIRS=json.loads((HOME/'tests/originals.json').read_text())

@pytest.mark.parametrize('pair',PAIRS['train']+PAIRS['test'])
def test_supplied_originals(pair):
    assert adapter().solve(pair['input'])==pair['output']

def test_single_obstacle_and_boundary_clipping():
    a=adapter();g=PAIRS['train'][0]['input']
    state=a.derive(g)
    assert state['background']==0
    assert len(state['strands'])==1
    s=state['strands'][0]
    assert s['anchor']==[3,4] and s['length']==6
    assert s['contour']==[[2,4]]
    assert a.solve(g)==PAIRS['train'][0]['output']

def test_small_literal_length_extension():
    a=adapter()
    g=[[0]*10 for _ in range(12)]
    for r in range(8,12):g[r][8]=6
    for p in ((8,7),(9,6),(9,5),(10,4),(11,3)):g[p[0]][p[1]]=4
    for r in (4,5):g[r][5]=3
    want=[row[:] for row in g]
    for p in ((8,7),(9,6),(9,5),(10,4),(11,3)):want[p[0]][p[1]]=0
    for p in ((8,7),(7,6),(6,5),(5,4),(4,4)):want[p[0]][p[1]]=4
    assert a.solve(g)==want
    want[3][5]=4;want[2][6]=4
    assert a.solve(g,'plus_two')==want

@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_episode_counts_matched_inputs_and_teaching(seed):
    a=adapter();previous=None
    for value in a.VALUES:
        s={a.PARAMETER:value};full=a.generate(seed,s,6,4)
        inputs=[p['input']for split in ('train','test')for p in full[split]]
        assert len({json.dumps(g)for g in inputs})==10
        assert previous is None or inputs==previous
        previous=inputs
        for d,q in ((2,1),(3,4),(6,2)):
            short=a.generate(seed,s,d,q)
            assert short['train']==full['train'][:d]
            assert short['test']==full['test'][:q]
        assert a.survivors(full['train'][:2],s)==['intended']
        assert all(a.input_errors(g)==[]for g in inputs)
        g=full['test'][3]['input']
        assert len(g)==len(g[0])==30
        assert len(a.derive(g)['strands'])==4
        assert full['program_solution']==a.program(s)
    x=a.generate(seed,{a.PARAMETER:a.VALUES[0]},2,4)
    y=a.generate(seed,{a.PARAMETER:a.VALUES[1]},2,4)
    assert all(p['output']!=q['output']for p,q in zip(x['test'],y['test']))

@pytest.mark.parametrize('bad',[True,-1,2**63,1.0,'1',None])
def test_seed_validation(bad):
    a=adapter()
    with pytest.raises(ValueError):a.generate(bad,a.DEFAULT,2,4)

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,False)])
def test_count_validation(d,q):
    a=adapter()
    with pytest.raises(ValueError):a.generate(0,a.DEFAULT,d,q)

@pytest.mark.parametrize('bad',[{},None,{'strand_extent':'bad'},{'strand_extent':'source','extra':0}])
def test_settings_validation(bad):
    with pytest.raises(ValueError):adapter().program(bad)

@pytest.mark.parametrize('bad',[[],[[]],[[True]],[[1.0]],[[10]],[[0],[0,1]]])
def test_grid_validation(bad):
    with pytest.raises(ValueError):adapter().solve(bad)

def test_canonical_and_public_isolation():
    a=adapter()
    assert a.program(a.DEFAULT)==(HOME/'reference.rkt').read_text()
    episode=a.generate(17,a.DEFAULT,3,4)
    for i in range(4):
        v=a.public_view(episode,i)
        assert set(v)=={'train','test'}and len(v['test'])==1
        assert set(v['test'][0])=={'input'}
        v['test'][0]['input'][0][0]=99
        assert episode['test'][i]['input'][0][0]!=99
    for pseed in range(8):
        assert a.public_turns(17,a.DEFAULT,3,pseed,1)==a.public_turns(17,a.DEFAULT,3,pseed,4)[:1]
    assert len({a.presentation_order(i)[0]for i in range(8)})>1

def test_original_rule_is_rotation_and_palette_equivariant():
    a=adapter()
    for pair in PAIRS['train']+PAIRS['test']:
        for k in range(4):
            g=a._rotate(pair['input'],k);want=a._rotate(pair['output'],k)
            for mirrored in (False,True):
                f=lambda x:[row[::-1]for row in x]if mirrored else x
                palette=lambda x:[[(v*3+1)%10 for v in row]for row in x]
                assert a.solve(palette(f(g)))==palette(f(want))

def test_generated_stationary_cells_survive_and_paths_are_local():
    a=adapter()
    for seed in range(64):
        for stream,indices in (('demo',(0,1)),('query',(0,3))):
            for index in indices:
                g=a.sample(seed,stream,index);state=a.derive(g)
                assert a.input_errors(g)==[]
                assert len(state['strands'])==(4 if index in (1,3) else 1)
                moved={tuple(p)for s in state['strands']for p in s['source_cells']}
                for value in a.VALUES:
                    out=a.solve(g,value)
                    assert all(out[r][c]==v for r,row in enumerate(g)for c,v in enumerate(row)
                               if v!=state['background']and(r,c)not in moved)
                    for record in state['strands']:
                        path=a.trace(record,value,len(g),len(g[0]))
                        assert len(path)<=record['length']+(2 if value=='plus_two'else 0)
                        assert len(path)==len({tuple(p)for p in path})
                        assert all(max(abs(x-y)for x,y in zip(p,q))==1 for p,q in zip(path,path[1:]))
