from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest
from reviewer_support import find_root

ROOT=find_root(Path(__file__))
HOME=ROOT/'generators/public_eval_291dc1e1'

def load(name,path):
    assert path.is_file(), f'Missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def source(): return load('strip_source_test',HOME/'generator.py')
def adapter(): return load('strip_adapter_test',HOME/'workspace/parametric/adapter.py')

def original_pairs():
    ch=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['291dc1e1']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['291dc1e1']
    grid=lambda g:[[int(v) for v in row] for row in g]
    return [(grid(p['input']),grid(p['output'])) for p in ch['train']]+[(grid(p['input']),grid(o)) for p,o in zip(ch['test'],gold)]

@pytest.mark.parametrize('index',range(5))
def test_original_labels(index):
    g=source();inp,out=original_pairs()[index]
    assert g.solve(inp)==out
    assert g.self_check(inp)==[]


def hand_scene():
    # Horizontal, two lanes, widths 4,2,6,2,4,2. Walk is 0 -> 2 -> 5 -> exit.
    g=[[8]*17 for _ in range(9)]
    g[0]=[0]+[1]*16
    for r in range(1,9):g[r][0]=2
    for r,c,w,color in [(2,2,4,3),(2,7,2,4),(2,10,6,5),(6,2,2,6),(6,5,4,7),(6,10,2,9)]:
        for rr in (r,r+1):g[rr][c:c+w]=[color]*w
    return g


def test_stateful_walk_hand_case():
    gen=source();g=hand_scene()
    canonical=[]
    for color,w in [(3,4),(4,2),(5,6),(6,2),(7,4),(9,2)]:
        row=[8]*((6-w)//2)+[color]*w+[8]*((6-w)//2)
        canonical.extend([row[:],row[:]])
    assert gen.solve(g)==canonical
    assert gen.walk_indices(gen.decode(g)['tiles'])==[0,2,5]
    expected=[p for i in [0,2,5] for p in canonical[2*i:2*i+2]]
    assert gen.solve(g,'width_walk')==expected
    assert gen.solve(g,'width_walk',rival='fixed_first_stride')!=expected

@pytest.mark.parametrize('mode',['canonical','width_walk'])
@pytest.mark.parametrize('demos',range(2,7))
@pytest.mark.parametrize('queries',range(1,5))
def test_counts_prefixes_matched_inputs(mode,demos,queries):
    a=adapter();g=source();s={'mode':mode}
    e=a.generate(17,s,demos,queries);full=a.generate(17,s,6,4)
    assert len(e['train'])==demos and len(e['test'])==queries
    assert e['train']==full['train'][:demos] and e['test']==full['test'][:queries]
    assert e['program_solution']==a.program(s)
    other=a.generate(17,{'mode':'canonical'},demos,queries)
    for split in ('train','test'):
        assert [p['input'] for p in e[split]]==[p['input'] for p in other[split]]
        for p in e[split]:
            assert g.self_check(p['input'])==[]
            assert g.solve(p['input'],mode)==p['output']
            g.grid(p['output'])
    inputs=[json.dumps(p['input']) for split in ('train','test') for p in e[split]]
    assert len(set(inputs))==len(inputs)

@pytest.mark.parametrize('seed',[0,1,17,43,103])
@pytest.mark.parametrize('mode',['canonical','width_walk'])
def test_minimum_teaching_and_boundary(seed,mode):
    a=adapter();g=source();e=a.generate(seed,{'mode':mode},2,4)
    assert g.teaching_failures(e,mode)==[]
    assert any(g.solve(p['input'],'canonical')!=g.solve(p['input'],'width_walk') for p in e['train'])
    big=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    d=g.decode(big['input'])
    assert len(d['tiles'])==15
    assert sum(v!=8 for row in big['input'] for v in row)>160
    boxes=d['boxes']
    assert max(b[2] for b in boxes)-min(b[0] for b in boxes)>=25
    assert max(b[3] for b in boxes)-min(b[1] for b in boxes)>=25
    assert len(g.solve(big['input']))==30
    assert any(len(p['output'][0])>=24 for p in e['test'])

@pytest.mark.parametrize('bad',[[[True]],[[1.0]],[[10]],[[-1]],[],[[]],[[0],[0,1]],[[0]*31]])
def test_invalid_grid(bad):
    g=source()
    with pytest.raises(ValueError):g.solve(bad)
    assert g.self_check(bad)

@pytest.mark.parametrize('settings',[{}, {'mode':'bad'},{'mode':True},{'mode':'canonical','extra':1}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):adapter().program(settings)

@pytest.mark.parametrize('demos,queries',[(1,4),(7,4),(True,4),(2,0),(2,5),(2,True),(2,1.0)])
def test_invalid_counts(demos,queries):
    with pytest.raises(ValueError):adapter().generate(0,{'mode':'canonical'},demos,queries)


def test_default_local_resource_and_no_global_rng(monkeypatch,tmp_path):
    a=adapter();expected=(HOME/'reference.rkt').read_text()
    assert (HOME/'workspace/parametric/canonical.rkt').read_text()==expected
    assert a.program({'mode':'canonical'})==expected
    before=random.getstate();s={'mode':'canonical'};e=a.generate(9,s,2,4)
    assert random.getstate()==before and s=={'mode':'canonical'}
    assert e==a.generate(9,s,2,4)
    monkeypatch.setattr(a,'HOME',tmp_path/'unavailable-home')
    assert a.program({'mode':'canonical'})==expected


def test_literal_reference_authority():
    from arcpuzzles.review_public_creation import validate_reference_id
    assert validate_reference_id(HOME/'generator.py','291dc1e1')=='ee_291dc1e1'


def test_public_first_turn_and_private_invariance():
    a=adapter();e=a.generate(43,{'mode':'width_walk'},3,4);one=a.generate(43,{'mode':'width_walk'},3,1)
    visible=a.public_bytes(e,0)
    assert visible==a.public_bytes(one,0)
    changed=copy.deepcopy(e);changed['program_solution']='secret';changed['settings']={'secret':True}
    for pair in changed['test']:pair['output']={'secret':True}
    changed['test'][1:]=[{'invalid_future':True}]
    assert a.public_bytes(changed,0)==visible
    assert json.loads(visible)=={'train':e['train'],'test':[{'input':e['test'][0]['input']}]}
    changed['test'][0]['input'][0][0]=(changed['test'][0]['input'][0][0]+1)%10
    assert a.public_bytes(changed,0)!=visible


def test_presentation_not_fixed():
    a=adapter();orders={tuple(a.generate(i,{'mode':'canonical'},2,4)['query_source_indices']) for i in range(16)}
    assert len(orders)>5 and any(o[0]!=0 for o in orders)


def test_verifier_rejects_stale_source(tmp_path):
    import hashlib
    verify=load('strip_verify_test',HOME/'workspace/parametric/verify.py')
    path=tmp_path/'source.py';path.write_text('a=1\n')
    binding={'files':[{'path':'source.py','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]}
    verify.check_binding(tmp_path,binding);path.write_text('a=2\n')
    with pytest.raises(ValueError,match='Source binding'):verify.check_binding(tmp_path,binding)


def test_shape_changing_causal_difference_counts_extra_cells():
    verify=load('shape_difference_'+HOME.name,HOME/'workspace/parametric/verify.py')
    assert hasattr(verify,'grid_difference'), 'Causal audit must account for different output shapes'
    result=verify.grid_difference([[1,2]],[[1,3],[4,5]])
    assert result == {'output_shape':[1,2], 'counterfactual_shape':[2,2],
                      'overlap_changed_cells':1,'missing_or_extra_cells':2,'changed_cells':3}
    assert verify.grid_difference([[1,2],[3,4]],[[1,2],[3,4]])['changed_cells']==0


def test_native_resource_closure_without_parent_reference(tmp_path):
    import shutil
    local=tmp_path/'generators'/HOME.name
    resources=local/'workspace/parametric';resources.mkdir(parents=True)
    shutil.copy2(HOME/'generator.py',local/'generator.py')
    for file in (HOME/'workspace/parametric').iterdir():
        if file.is_file() and file.suffix in ('.py','.rkt','.json'):
            shutil.copy2(file,resources/file.name)
    assert not (local/'reference.rkt').exists()
    local_adapter=load('closed_adapter_'+HOME.name,resources/'adapter.py')
    contract=json.loads((resources/'promotion.json').read_text())
    for mode in contract['parameters']['mode']:
        episode=local_adapter.generate(17,{'mode':mode},2,4)
        assert len(episode['test'])==4
        assert episode['program_solution']==local_adapter.program({'mode':mode})
    assert local_adapter.program(contract['default'])==(HOME/'reference.rkt').read_text()


def test_one_strip_minimum_is_total():
    g=source();inp=[[0,1,1,1,1],[2,8,8,8,8],[2,8,3,4,8],[2,8,5,6,8],[2,8,8,8,8]]
    assert g.self_check(inp)==[]
    assert g.solve(inp)==[[3,4],[5,6]]
    assert g.solve(inp,'width_walk')==[[3,4],[5,6]]


def test_structural_invalid_inputs_and_too_many_objects():
    g=source()
    hole=hand_scene();hole[2][3]=8
    bad_header=hand_scene();bad_header[0][3]=3
    too_many=[[8]*14 for _ in range(14)];too_many[0]=[0]+[1]*13
    for r in range(1,14):too_many[r][0]=2
    for i in range(4):
        for j in range(4):
            for dr in range(2):
                for dc in range(2):too_many[1+3*i+dr][1+3*j+dc]=3
    for inp in [hole,bad_header,too_many]:
        assert g.self_check(inp)
        with pytest.raises(ValueError):g.solve(inp)


def test_walk_rejects_zero_stride():
    with pytest.raises(ValueError):source().walk_indices([[[3,3],[3,3]]],[0])
