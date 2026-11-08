"""Shortest-path selection, capacity, topology, and single-query privacy."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]

def adapter():
    p=HOME/'workspace/parametric/adapter.py';assert p.is_file(),'native adapter has not been implemented'
    s=importlib.util.spec_from_file_location('collection_under_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('split,index',[('train',i) for i in range(3)]+[('test',i) for i in range(2)])
def test_original_labels(split,index):
    a=adapter();p=json.loads((HOME/'tests/originals.json').read_text())[split][index]
    assert a.solve(p['input'],'nearest')==p['output']

def test_walls_capacity_and_center_slot():
    a=adapter()
    p=json.loads((HOME/'tests/originals.json').read_text())['train'][1]
    out=a.solve(p['input'],'nearest')
    assert out[5][5]==9 and out[0][6]==9 and out[1][6]==7
    assert sum(v==9 for r in out for v in r)==sum(v==9 for r in p['input'] for v in r)
    p=json.loads((HOME/'tests/originals.json').read_text())['train'][0]
    out=a.solve(p['input'],'nearest')
    assert out[5][5]==2 and out[1][8]==9 and out[8][7]==7

def test_zero_reachable_is_identity():
    a=adapter();g=[[6]*7 for _ in range(7)]
    for r in range(2,5):
        for c in range(2,5):g[r][c]=3
    g[3][3]=2;g[0][0]=9
    assert a.solve(g,'nearest')==g and a.solve(g,'farthest')==g

@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_prefix_teaching_and_queries(seed):
    a=adapter();banks=[];outputs=[]
    for order in ('nearest','farthest'):
        st={'collection_order':order};e=a.generate(seed,st,6,4);small=a.generate(seed,st,2,1)
        assert small['train']==e['train'][:2] and small['test']==e['test'][:1]
        assert a.survivors(e['train'][:2],st)==['intended']
        inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
        assert len({json.dumps(g) for g in inputs})==10
        assert all(a.input_errors(g)==[] for g in inputs)
        assert len(e['test'][3]['input'])==len(e['test'][3]['input'][0])==30
        banks.append(inputs);outputs.append([p['output'] for p in e['test']])
        for sp in ('train','test'):
            for p in e[sp]:assert sum(v==9 for r in p['input'] for v in r)==sum(v==9 for r in p['output'] for v in r)
    assert banks[0]==banks[1] and all(x!=y for x,y in zip(*outputs))

@pytest.mark.parametrize('args',[(True,{'collection_order':'nearest'},2,4),(-1,{'collection_order':'nearest'},2,4),(2**63,{'collection_order':'nearest'},2,4),(0,{},2,4),(0,{'collection_order':'nearest','secret':1},2,4),(0,{'collection_order':'bad'},2,4),(0,{'collection_order':'nearest'},1,4),(0,{'collection_order':'nearest'},7,4),(0,{'collection_order':'nearest'},True,4),(0,{'collection_order':'nearest'},2,0),(0,{'collection_order':'nearest'},2,5)])
def test_invalid_requests(args):
    with pytest.raises(ValueError):adapter().generate(*args)

@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1,2],[3]],[[10]],[[0]*31],[[7,7],[7,7]]])
def test_invalid_grid_or_missing_marker(g):
    with pytest.raises(ValueError):adapter().solve(g,'nearest')

def test_public_privacy_and_shuffle():
    a=adapter();st={'collection_order':'nearest'};e=a.generate(17,st,2,4);v=a.public_view(e,0)
    bad=copy.deepcopy(e);bad.update(settings={'secret':1},program_solution='SECRET')
    bad['test'][0]['output']=[[9]];bad['test'][1:]=[{'input':[[8]],'output':[[9]]}]
    assert a.public_view(bad,0)==v
    assert set(v)=={'train','test'} and set(v['test'][0])=={'input'}
    for seed in range(8):assert a.public_turns(17,st,2,seed,1)==a.public_turns(17,st,2,seed,4)[:1]
    assert len({json.dumps(a.public_turns(17,st,2,i,1)) for i in range(8)})>1

def test_exact_canonical_and_production():
    a=adapter();assert a.program({'collection_order':'nearest'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    s=importlib.util.spec_from_file_location('maze_generator',HOME/'generator.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert m.RULE_TASK_ID=='ee_dd6b8c4b'
    for i in range(4):assert m.self_check(m.generate(17,i,difficulty='hard'))==[]

def test_default_presentation_varies_across_source_seeds():
    a=adapter();seen=set();st={'collection_order':'nearest'}
    for seed in range(8):
        bank=a.generate(seed,st,2,4)['test']
        current=a.public_turns(seed,st,2,0,1)[0]['test'][0]['input']
        seen.add(next(i for i,p in enumerate(bank) if p['input']==current))
    assert len(seen)>1, 'default presentation always starts at the same source ordinal'

def test_interior_sealed_tokens_not_only_corner_exceptions():
    a=adapter()
    for seed in (0,17,43):
        for i in range(4):
            g=a.sample(seed,'query',i);state=a.derive(g)
            assert any(0<r<len(g)-1 and 0<c<len(g[0])-1 for r,c in state['unreachable'])
