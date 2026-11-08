from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
PAIRS=json.loads((HOME/'tests/originals.json').read_text())

def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'adapter missing'
    spec=importlib.util.spec_from_file_location('_panel_partition_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('pair',PAIRS['train']+PAIRS['test'])
def test_official_pairs(pair):
    assert adapter().solve(pair['input'],'second_in_marked')==pair['output']

def test_vertical_partition_composes_both_sources_and_boundary():
    a=adapter(); bg=0; frame=9
    p0=[[0,0,1,0,0],[0,0,1,0,0],[2,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]]
    p1=[[3,0,4,0,0],[0,3,4,0,0],[3,0,4,0,0],[0,3,4,0,0],[3,0,4,0,0]]
    p2=[[0,0,5,0,6],[0,0,5,6,0],[0,0,5,0,6],[0,0,5,6,0],[0,0,5,0,6]]
    g=a.join_panels([p0,p1,p2,[[bg]*5 for _ in range(5)]],frame)
    out=a.solve(g,'second_in_marked')
    parts=a.split_panels(out)
    assert parts[3]==[[3,0,4,0,6],[0,3,4,6,0],[3,0,4,0,6],[0,3,4,6,0],[3,0,4,0,6]]
    swapped=a.solve(g,'third_in_marked')
    assert swapped!=out

@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_episode_contract(seed):
    a=adapter();matched=None
    for value in a.VALUES:
        full=a.generate(seed,{a.PARAMETER:value},6,4)
        inputs=[p['input'] for s in ('train','test') for p in full[s]]
        assert len(inputs)==10 and len({json.dumps(g) for g in inputs})==10
        assert matched is None or matched==inputs
        matched=inputs
        assert a.survivors(full['train'][:2],value)==['intended']
        assert full['program_solution']==a.program({a.PARAMETER:value})
        assert len(full['test'][3]['input'])==30
        assert len(full['test'][3]['input'][0])>=29
        for d,q in ((2,1),(3,4),(6,2)):
            short=a.generate(seed,{a.PARAMETER:value},d,q)
            assert short['train']==full['train'][:d]
            assert short['test']==full['test'][:q]
    x=a.generate(seed,{a.PARAMETER:a.VALUES[0]},2,4)
    y=a.generate(seed,{a.PARAMETER:a.VALUES[1]},2,4)
    assert all(p['output']!=q['output'] for p,q in zip(x['test'],y['test']))

def test_canonical_bytes_and_public_projection():
    a=adapter()
    assert a.program(a.DEFAULT)==(HOME/'reference.rkt').read_text()==(HOME/'workspace/parametric/canonical.rkt').read_text()
    e=a.generate(17,a.DEFAULT,3,4)
    for i in range(4):
        view=a.public_view(e,i)
        assert set(view)=={'train','test'} and len(view['test'])==1
        assert set(view['test'][0])=={'input'}
    for pseed in range(8):
        assert a.public_turns(17,a.DEFAULT,3,pseed,1)==a.public_turns(17,a.DEFAULT,3,pseed,4)[:1]

@pytest.mark.parametrize('bad',[True,-1,2**63,1.0,'1',None])
def test_seed_validation(bad):
    with pytest.raises(ValueError):adapter().generate(bad,adapter().DEFAULT,2,4)

@pytest.mark.parametrize('bad',[{},None,{'source_assignment':'bad'},{'source_assignment':'second_in_marked','x':1}])
def test_settings_validation(bad):
    with pytest.raises(ValueError):adapter().program(bad)

def test_reusable_audit_structural_smoke():
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(),'reusable audit tool missing'
    spec=importlib.util.spec_from_file_location('_panel_audit_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=module.structural([0])
    assert report['status']=='passed'
    assert report['episodes']>=4 and report['public_views']>=8
    counter=module.counterfactual_program()
    assert counter!=adapter().program(adapter().DEFAULT)
