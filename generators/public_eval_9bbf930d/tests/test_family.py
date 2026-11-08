import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

TASK='public_eval_9bbf930d'
ROOT=find_root(__file__)
HOME=ROOT/'generators'/TASK

def load(path):
    assert path.is_file(), f'Missing implementation: {path.name}'
    name='test_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod

@pytest.fixture
def gen(): return load(HOME/'generator.py')
@pytest.fixture
def adapter(): return load(HOME/'workspace/parametric/adapter.py')

def originals():
    raw=ROOT/'shared/data/raw'
    item=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['9bbf930d']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['9bbf930d']
    return item['train']+[dict(input=p['input'],output=g) for p,g in zip(item['test'],gold)]

@pytest.mark.parametrize('index',range(4))
def test_all_original_labels(gen,index):
    pair=originals()[index]
    to_grid=lambda g:[[int(v) for v in row] for row in g]
    assert gen.solve(to_grid(pair['input']))==to_grid(pair['output'])

@pytest.mark.parametrize('seed',[0,17,43,2**63-1])
def test_counts_prefixes_and_setting_neutral_inputs(adapter,seed):
    big=adapter.generate(seed,{'guide_update':'local'},6,4)
    small=adapter.generate(seed,{'guide_update':'local'},2,1)
    up=adapter.generate(seed,{'guide_update':'entry'},6,4)
    assert small['train']==big['train'][:2]
    assert small['test']==big['test'][:1]
    inputs=lambda e:[p['input'] for split in ('train','test') for p in e[split]]
    assert inputs(big)==inputs(up)
    assert len({json.dumps(g) for g in inputs(big)})==10
    assert big['program_solution']==(HOME/'reference.rkt').read_text()
    assert big['train'][:2]!=up['train'][:2]
    assert all(x['output']!=y['output'] for x,y in zip(big['test'],up['test']))
    assert len(big['test'][3]['input'])==len(big['test'][3]['input'][0])==30

@pytest.mark.parametrize('guide_update',['local','entry'])
def test_marker_conservation_and_two_demo_rivals(gen,adapter,guide_update):
    e=adapter.generate(11,{'guide_update':guide_update},2,4)
    assert adapter.surviving_rules(e['train'],guide_update)==['intended']
    for p in e['train']+e['test']:
        assert gen.self_check(p['input'])==[]
        assert sum(v==6 for row in p['input'] for v in row)==sum(v==6 for row in p['output'] for v in row)
        assert any(v==7 for row in p['output'] for v in row)

@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(-1,2,4),(2**63,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,False),(0,2,0),(0,2,5)])
def test_invalid_counts(adapter,seed,demos,queries):
    with pytest.raises(ValueError):adapter.generate(seed,{'guide_update':'local'},demos,queries)

@pytest.mark.parametrize('settings',[{}, {'guide_update':'sideways'}, {'guide_update':True}, {'guide_update':'local','extra':0},None])
def test_invalid_settings(adapter,settings):
    with pytest.raises(ValueError):adapter.program(settings)

def test_standalone_generator_contract(gen):
    from arcpuzzles.parametric_worker import _grid
    result=gen.generate(7,3,difficulty='hard')
    assert isinstance(result,dict)
    g,meta=result['input'],result['metadata']
    assert _grid(result['input'])==g
    assert gen.self_check(g,meta=meta)==[]
    assert result==gen.generate(7,3,difficulty='hard')

@pytest.mark.parametrize('bad',[[],[[True]],[[1.0]],[[0],[0,0]],[[10]],[[0]*31]])
def test_numeric_grid_validation(gen,bad):
    with pytest.raises(ValueError):gen.solve(bad)

def test_sequential_public_projection_is_private_invariant(adapter,tmp_path):
    import copy
    audit=load(HOME/'workspace/parametric/self_audit.py')
    episode=adapter.generate(17,{'guide_update':'local'},2,4)
    one,private=audit.project_episode(episode,source_seed=17,presentation_seed=3,turns=1)
    full,all_private=audit.project_episode(episode,source_seed=17,presentation_seed=3,turns=4)
    assert one==full[:1]
    assert set(one[0])=={'train','test'}
    assert list(one[0]['test'][0])==['input']
    changed=copy.deepcopy(episode)
    changed['settings']={'secret':'not visible'};changed['program_solution']='different secret'
    for p in changed['test']:p['output']=[[9]]
    other,_=audit.project_episode(changed,source_seed=17,presentation_seed=3,turns=1)
    assert other==one
    orders={tuple(audit.project_episode(episode,source_seed=17,presentation_seed=k,turns=4)[1]['source_indices']) for k in range(16)}
    assert len(orders)>1
    audit.write_exports([{'seed':17,'settings':{'guide_update':'local'},'episode':episode}],tmp_path/'export')
    files=list((tmp_path/'export/public').glob('*.json'));assert len(files)==4
    for p in files:assert hashlib.sha256(p.read_bytes()).hexdigest()==p.stem
    with pytest.raises(FileExistsError):audit.write_exports([],tmp_path/'export')
    with pytest.raises(ValueError):audit.project_episode(dict(episode,test=episode['test'][:1]),source_seed=17)
    with pytest.raises(ValueError):audit.write_exports([{'seed':17,'settings':{},'episode':episode}]*2,tmp_path/'duplicate')
    assert not (tmp_path/'duplicate').exists()
