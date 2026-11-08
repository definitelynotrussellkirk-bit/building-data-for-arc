import copy
import importlib.util
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]

def load():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'Native adapter missing'
    spec=importlib.util.spec_from_file_location('corner_adapter_test',path)
    obj=importlib.util.module_from_spec(spec);sys.modules[spec.name]=obj;spec.loader.exec_module(obj)
    return obj

@pytest.mark.parametrize('seed',[0,1,14,17,43])
def test_independent_counts_matched_inputs_and_stress(seed):
    a=load();eps=[a.generate(seed,{'copy_extent':mode},6,4)for mode in ('full','outside')]
    assert all(p['input']==q['input']for s in ('train','test')for p,q in zip(eps[0][s],eps[1][s]))
    assert all(eps[0]['train'][i]['output']!=eps[1]['train'][i]['output']for i in (0,1))
    for ep in eps:
        inputs=[p['input']for s in ('train','test')for p in ep[s]]
        assert len({str(g)for g in inputs})==10
        assert len(ep['private']['query_bank'])==4
        assert (len(ep['test'][3]['input']),len(ep['test'][3]['input'][0]))==(30,30)
        d=a.model.analyze(ep['test'][3]['input'])
        assert len(d['groups'])>=12 and len(d['corners'])==16
        for demos in (2,3,6):
            for queries in (1,4):
                sub=a.generate(seed,ep['settings'],demos,queries)
                assert sub['train']==ep['train'][:demos] and sub['test']==ep['test'][:queries]
                assert sub['program_solution']==a.program(ep['settings'])

@pytest.mark.parametrize('demos,queries',[(True,4),(1,4),(7,4),(3,0),(3,5),(3,True)])
def test_reject_invalid_counts(demos,queries):
    with pytest.raises(ValueError):load().generate(0,{'copy_extent':'full'},demos,queries)

@pytest.mark.parametrize('settings',[{}, {'copy_extent':'nonsense'}, {'copy_extent':True}, {'copy_extent':'full','extra':1}])
def test_reject_invalid_settings(settings):
    with pytest.raises(ValueError):load().program(settings)

def test_exact_default():
    a=load();assert a.program({'copy_extent':'full'})==(HOME/'reference.rkt').read_text()

def test_public_is_current_query_only_and_hides_metadata():
    a=load();ep=a.generate(17,{'copy_extent':'full'},2,4)
    view=a.public_view(ep,0,13);original=copy.deepcopy(view)
    assert set(view)=={'train','test'} and len(view['test'])==1
    assert set(view['test'][0])=={'input'}
    for p in ep['train']:p['private_marker']='secret'
    for p in ep['private']['query_bank']:p['output']=[[9]]
    ep['settings']={'secret':True};ep['program_solution']='secret';ep['seed']=-1
    assert a.public_view(ep,0,13)==original
    view['train'][0]['input'][0][0]=99
    assert a.public_view(ep,0,13)==original

def test_presentation_uses_entire_query_bank_before_prefix():
    a=load();s={'copy_extent':'full'};long=a.generate(17,s,2,4);short=a.generate(17,s,2,1)
    assert a.public_view(long,0,13)==a.public_view(short,0,13)
    firsts={str(a.public_view(long,0,p)['test'][0]['input'])for p in range(16)}
    assert len(firsts)>1

def test_two_close_frames_do_not_create_false_cross_corners():
    # Seed 15 / index 4 previously placed corners at (11,11) and (12,12),
    # creating two false crossings and stealing cells from the full exemplar.
    a=load();g=a.sample_input(15,4);d=a.model.analyze(g)
    assert len(d['corners'])==8 and len(d['groups'])==8
