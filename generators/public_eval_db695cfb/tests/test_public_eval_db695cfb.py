"""Diagonal signal completion, trigger gating, parametric branches, and privacy."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]


def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'native adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('diagonal_signal_under_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.mark.parametrize('split,index',[('train',i) for i in range(5)]+[('test',0)])
def test_all_official_labels(split,index):
    a=adapter();pair=json.loads((HOME/'tests/originals.json').read_text())[split][index]
    assert a.solve(pair['input'],'both_edges')==pair['output']


def test_trigger_requires_membership_in_derived_signal_segment():
    a=adapter();g=[[5]*9 for _ in range(9)]
    g[1][1]=g[7][7]=1
    g[4][4]=6      # on the segment: branches
    g[1][6]=6      # off the segment: remains isolated
    out=a.solve(g,'both_edges')
    assert all(out[r][8-r]==6 for r in range(9))
    assert out[1][6]==6
    assert out[0][7]==5 and out[2][5]==5
    assert all(out[k][k] in (1,6) for k in range(1,8))


def test_forward_edge_setting_uses_same_trigger_but_one_sided_branch():
    a=adapter();g=[[8]*9 for _ in range(9)]
    g[1][1]=g[7][7]=1;g[4][4]=6
    both=a.solve(g,'both_edges')
    forward=a.solve(g,'forward_edge')
    assert both!=forward
    assert all(both[r][8-r]==6 for r in range(9))
    assert all(forward[r][8-r]==6 for r in range(4,9))
    assert forward[3][5]==8


@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_matched_prefix_stable_teachable_family(seed):
    a=adapter();banks=[];outputs=[]
    for value in a.VALUES:
        st={a.PARAMETER:value};full=a.generate(seed,st,6,4);small=a.generate(seed,st,2,1)
        assert small['train']==full['train'][:2]
        assert small['test']==full['test'][:1]
        assert a.survivors(full['train'][:2],st)==['intended']
        inputs=[p['input'] for split in ('train','test') for p in full[split]]
        assert len({json.dumps(g,sort_keys=True) for g in inputs})==10
        assert all(a.input_errors(g)==[] for g in inputs)
        assert len(full['test'][3]['input'])==len(full['test'][3]['input'][0])==30
        banks.append(inputs);outputs.append([p['output'] for p in full['test']])
    assert banks[0]==banks[1]
    assert all(x!=y for x,y in zip(outputs[0],outputs[1]))


def test_stress_query_has_multiple_triggers_and_substantive_change():
    a=adapter();g=a.sample(17,'query',3);state=a.derive(g)
    assert len(g)==len(g[0])==30
    assert len(state['triggers'])>=3
    assert len(state['segments'])>=1
    for value in a.VALUES:
        out=a.solve(g,value)
        assert sum(x!=y for r,s in zip(g,out) for x,y in zip(r,s))>=40


@pytest.mark.parametrize('args',[
    (True,{'beam_reach':'both_edges'},2,4),(-1,{'beam_reach':'both_edges'},2,4),
    (2**63,{'beam_reach':'both_edges'},2,4),(0,{},2,4),
    (0,{'beam_reach':'both_edges','secret':1},2,4),(0,{'beam_reach':'bad'},2,4),
    (0,{'beam_reach':'both_edges'},1,4),(0,{'beam_reach':'both_edges'},7,4),
    (0,{'beam_reach':'both_edges'},2,0),(0,{'beam_reach':'both_edges'},2,5),
])
def test_invalid_requests(args):
    with pytest.raises(ValueError):adapter().generate(*args)


@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1,2],[3]],[[10]],[[0]*31],[[5,5],[5,5]]])
def test_invalid_grid_or_missing_signal(g):
    with pytest.raises(ValueError):adapter().solve(g,'perpendicular')


def test_public_projection_masks_all_private_state_and_stop_count():
    a=adapter();st={a.PARAMETER:'both_edges'};episode=a.generate(17,st,2,4);visible=a.public_view(episode,0)
    corrupt=copy.deepcopy(episode);corrupt.update(settings={'secret':1},program_solution='SECRET')
    corrupt['test'][0]['output']=[[9]];corrupt['test'][1:]=[{'input':[[8]],'output':[[9]]}]
    assert a.public_view(corrupt,0)==visible
    assert set(visible)=={'train','test'} and set(visible['test'][0])=={'input'}
    for pseed in range(8):
        assert a.public_turns(17,st,2,pseed,1)==a.public_turns(17,st,2,pseed,4)[:1]
    assert len({json.dumps(a.public_turns(17,st,2,pseed,1)) for pseed in range(8)})>1


def test_exact_canonical_program_and_production_surface():
    a=adapter();raw=(HOME/'reference.rkt').read_text()
    assert a.program({a.PARAMETER:'both_edges'})==raw
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    spec=importlib.util.spec_from_file_location('diagonal_generator',HOME/'generator.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.RULE_TASK_ID=='ee_db695cfb'
    for i in range(4):assert module.self_check(module.generate(17,i,difficulty='hard'))==[]
