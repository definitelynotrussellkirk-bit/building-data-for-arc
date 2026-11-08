from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]


def adapter():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(), 'Missing native path-family adapter'
    spec=importlib.util.spec_from_file_location('_faa_family',p)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m


def test_exact_canonical_and_meaningful_alternative():
    a=adapter()
    assert a.program({'crossing_policy':'reverse_marked'})==(HOME/'reference.rkt').read_text()
    x=a.generate(17,{'crossing_policy':'reverse_marked'},2,4)
    y=a.generate(17,{'crossing_policy':'preserve_visible'},2,4)
    assert [p['input']for s in ('train','test')for p in x[s]]==[p['input']for s in ('train','test')for p in y[s]]
    assert any(p['output']!=q['output']for p,q in zip(x['train'],y['train']))


def test_constructed_geometry_is_recovered_not_guessed():
    a=adapter()
    for seed in range(8):
        for index in (0,1,2,3,4,5,100,101,102,103):
            scene=a.sampler.scene(seed,index)
            recovered={p['color']:p['cells']for p in a.model.recover_paths(scene['input'])}
            assert recovered==scene['paths']
            for mode in a.MODES:
                assert a.model.solve(scene['input'],mode)==scene['outputs'][mode]


def test_counts_prefixes_and_stress():
    a=adapter();setting={'crossing_policy':'reverse_marked'}
    full=a.generate(9,setting,6,4)
    for demos in range(2,7):
        for queries in range(1,5):
            ep=a.generate(9,setting,demos,queries)
            assert ep['train']==full['train'][:demos]
            assert ep['test']==full['test'][:queries]
            assert len(ep['private']['query_bank'])==4
    grids=[p['input']for s in ('train','test')for p in full[s]]
    assert len({json.dumps(g)for g in grids})==10
    g=full['test'][3]['input'];assert len(g)==len(g[0])==30
    assert sum(v!=0 for row in g for v in row)>=100
    assert any(v for v in g[0]) and any(v for v in g[-1])


def test_public_first_turn_hides_every_private_field_and_future_query():
    a=adapter();setting={'crossing_policy':'reverse_marked'}
    ep=a.generate(8,setting,3,4);before=a.public_view(ep,0,13)
    assert set(before)=={'train','test'} and len(before['test'])==1
    assert set(before['test'][0])=={'input'}
    x=copy.deepcopy(ep);x['settings']={};x['program_solution']='hidden';x['seed']=999
    for p in x['train']:p['secret']=9
    for p in x['test']:p['output']=[[9]]
    for p in x['private']['query_bank']:p['output']=[[9]]
    assert a.public_view(x,0,13)==before
    assert a.public_view(a.generate(8,setting,3,1),0,13)==before
    assert {json.dumps(a.public_view(ep,0,s)['test'][0]['input'])for s in range(20)}=={json.dumps(p['input'])for p in ep['test']}


@pytest.mark.parametrize('kind,value',[('seed',True),('seed',-1),('seed',2**63),('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',True)])
def test_reject_bad_counts(kind,value):
    a=adapter();args={'seed':0,'settings':{'crossing_policy':'reverse_marked'},'demos':2,'queries':4};args[kind]=value
    with pytest.raises(ValueError):a.generate(**args)


@pytest.mark.parametrize('setting',[{}, {'crossing_policy':True},{'crossing_policy':'other'},{'crossing_policy':'reverse_marked','extra':0}])
def test_reject_unknown_settings(setting):
    with pytest.raises(ValueError):adapter().program(setting)


def test_minimum_prefix_includes_long_gap_and_multiturn_tail():
    a=adapter()
    for seed in range(8):
        scene=a.sampler.scene(seed,0);g=scene['input']
        holes=set().union(*scene['paths'].values())-{(r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v}
        assert any(all((r+k*dr,c+k*dc)in holes for k in range(3))for r,c in holes for dr,dc in ((0,1),(1,0)))
        scene=a.sampler.scene(seed,1)
        rec=next(p for p in a.model.recover_paths(scene['input'])if p['color']==scene['marked_color'])
        removed=rec['cells']-a.model.routed_cells(scene['input'],rec)
        assert len({r for r,c in removed})>=3 and len({c for r,c in removed})>=3


def test_minimum_prefix_rejects_finite_query_changing_rivals():
    a=adapter()
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(), 'Missing reusable path shortcut audit'
    audit=a.local('audit')
    for seed in range(8):
        for mode in a.MODES:
            ep=a.generate(seed,{'crossing_policy':mode},2,4)
            guesses=[audit.rivals(p['input'],mode)for p in ep['train']+ep['test']]
            for name in guesses[0]:
                if all(guesses[i][name]==p['output']for i,p in enumerate(ep['train'])):
                    assert all(guesses[2+i][name]==p['output']for i,p in enumerate(ep['test'])),(seed,mode,name)
