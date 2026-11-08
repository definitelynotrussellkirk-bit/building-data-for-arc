"""Falling-ray routing, lesson quality, count boundaries, and privacy."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]


def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('_falling_ray_under_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.mark.parametrize('split,index',[('train',i) for i in range(6)]+[('test',0),('test',1)])
def test_all_official_labels(split,index):
    a=adapter();pair=json.loads((HOME/'tests/originals.json').read_text())[split][index]
    assert a.solve(pair['input'],'split')==pair['output']


def test_hand_case_split_and_closest_exit():
    a=adapter()
    g=[[7]*9 for _ in range(9)]
    g[0][4]=g[1][4]=6
    for c in range(2,7):g[4][c]=2
    for c in range(0,4):g[7][c]=2
    split=a.solve(g,'split');near=a.solve(g,'closest_exit')
    assert split[3][1:8]==[6]*7
    assert split[4][1]==split[4][7]==6
    assert near[3][1:5]==[6]*4 and near[3][5:8]==[7]*3
    assert near[4][1]==6 and near[4][7]==7
    assert split!=near


@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_generation_prefix_teaching_and_30x30(seed):
    a=adapter();banks=[];outputs=[]
    for mode in a.VALUES:
        st={a.PARAMETER:mode};full=a.generate(seed,st,6,4);small=a.generate(seed,st,2,1)
        assert small['train']==full['train'][:2]
        assert small['test']==full['test'][:1]
        assert a.survivors(full['train'][:2],st)==['intended']
        inputs=[p['input'] for split in ('train','test') for p in full[split]]
        assert len({json.dumps(g) for g in inputs})==10
        assert all(a.input_errors(g)==[] for g in inputs)
        assert len(full['test'][3]['input'])==len(full['test'][3]['input'][0])==30
        banks.append(inputs);outputs.append([p['output'] for p in full['test']])
    assert banks[0]==banks[1]
    assert any(x!=y for x,y in zip(*outputs))


@pytest.mark.parametrize('args',[
    (True,{'routing_mode':'split'},2,4),(-1,{'routing_mode':'split'},2,4),(2**63,{'routing_mode':'split'},2,4),
    (0,{},2,4),(0,{'routing_mode':'split','x':1},2,4),(0,{'routing_mode':'bad'},2,4),
    (0,{'routing_mode':'split'},1,4),(0,{'routing_mode':'split'},7,4),(0,{'routing_mode':'split'},True,4),
    (0,{'routing_mode':'split'},2,0),(0,{'routing_mode':'split'},2,5)])
def test_invalid_requests(args):
    with pytest.raises(ValueError):adapter().generate(*args)


@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1,2],[3]],[[10]],[[7]*31],[[7,7],[7,7]],[[6,7],[7,2]]])
def test_invalid_grids(g):
    with pytest.raises(ValueError):adapter().solve(g,'split')


def test_public_privacy_and_shuffle():
    a=adapter();st={a.PARAMETER:'split'};episode=a.generate(17,st,2,4);view=a.public_view(episode,0)
    bad=copy.deepcopy(episode);bad.update(settings={'secret':1},program_solution='SECRET')
    bad['test'][0]['output']=[[9]];bad['test'][1:]=[{'input':[[8]],'output':[[9]]}]
    assert a.public_view(bad,0)==view
    assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    for pseed in range(8):
        assert a.public_turns(17,st,2,pseed,1)==a.public_turns(17,st,2,pseed,4)[:1]
    assert len({json.dumps(a.public_turns(17,st,2,i,1)) for i in range(8)})>1


def test_exact_canonical_and_production_generator():
    a=adapter();assert a.program({'routing_mode':'split'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    spec=importlib.util.spec_from_file_location('_production_ray',HOME/'generator.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.RULE_TASK_ID=='ee_36a08778'
    for i in range(4):assert module.self_check(module.generate(17,i,difficulty='hard'))==[]


def test_default_presentation_does_not_fix_source_query_zero():
    a=adapter();seen=set();st={a.PARAMETER:'split'}
    for seed in range(10):
        bank=a.generate(seed,st,2,4)['test']
        visible=a.public_turns(seed,st,2,0,1)[0]['test'][0]['input']
        seen.add(next(i for i,p in enumerate(bank) if p['input']==visible))
    assert len(seen)>1


def test_teaching_search_skips_rejected_candidate_seed_119():
    a = adapter()
    episode = a.generate(119, {a.PARAMETER: 'split'}, 2, 4)
    assert len(episode['train']) == 2
    assert a.survivors(episode['train'], {a.PARAMETER: 'split'}) == ['intended']
