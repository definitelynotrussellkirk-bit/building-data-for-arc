import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter not yet implemented'
    spec=importlib.util.spec_from_file_location('jigsaw_446ef5d2',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def pairs():
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['446ef5d2']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['446ef5d2']
    return data['train']+[{'input':p['input'],'output':g} for p,g in zip(data['test'],gold)]

@pytest.mark.parametrize('index',range(4))
def test_original_label(index):
    p=pairs()[index]
    assert load().predict(p['input'],'assembly')==p['output']

@pytest.mark.parametrize('demos',[2,3,6])
@pytest.mark.parametrize('queries',[1,2,4])
def test_counts_matched_and_prefix(demos,queries):
    a=load();assert hasattr(a,'generate'),'generation not implemented'
    base=a.generate(17,{'mode':'assembly'},6,4)
    alt=a.generate(17,{'mode':'largest_region'},demos,queries)
    assert len(alt['train'])==demos and len(alt['test'])==queries
    assert [p['input'] for p in alt['train']]==[p['input'] for p in base['train'][:demos]]
    assert [p['input'] for p in alt['test']]==[p['input'] for p in base['test'][:queries]]
    assert len({json.dumps(p['input']) for sp in ('train','test') for p in alt[sp]})==demos+queries
    assert any(len(p['input'])==len(p['input'][0])==30 for p in base['test'])
    for p in alt['train']+alt['test']:assert a.predict(p['input'],'largest_region')==p['output']

def test_canonical_resource():
    a=load();assert hasattr(a,'program'),'program API absent'
    assert a.program({'mode':'assembly'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (HOME/'workspace/parametric/canonical.rkt').read_bytes()==(HOME/'reference.rkt').read_bytes()

def test_public_whitelist():
    from copy import deepcopy
    a=load();assert hasattr(a,'generate'),'generation absent'
    ep=a.generate(0,{'mode':'largest_region'},2,4);view=a.public_turn(ep,0)
    changed=deepcopy(ep);changed['settings']={'canary':'secret'};changed['program_solution']='secret'
    changed['train'][0]['secret']='secret';changed['test'][0]['output']=[[True]]
    changed['test'][0]['secret']='secret'
    changed['test'][1:]=[{'input':[[9]],'output':[[8]]}]
    assert a.public_turn(changed,0)==view
    assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    assert all(set(p)=={'input','output'} for p in view['train'])

def test_nonrectangular_fragment_profile():
    a=load();scene=a.core.bank(0)[1];pieces=scene['certificate']['pieces']
    assert any(len(p)<(max(r for r,c in p)-min(r for r,c in p)+1)*(max(c for r,c in p)-min(c for r,c in p)+1) for p in pieces)

def test_base_is_standalone_and_drift_checked(tmp_path):
    import shutil
    assert (HOME/'generator.py').is_file(),'portable ordinary generator absent'
    shutil.copy2(HOME/'generator.py',tmp_path/'generator.py')
    spec=importlib.util.spec_from_file_location('standalone_446',tmp_path/'generator.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    grid=m.generate(seed=17,sample_index=0,difficulty='medium')
    assert m.self_check(grid,difficulty='medium')==[]
    assert load().predict(grid,'assembly')==m.predict(grid,'assembly')

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()

@pytest.mark.parametrize('seed',[17,43])
def test_stress_protected_racket(evaluator,seed):
    a=load();scene=a.core.bank(seed)[9]
    assert len(scene['input'])==len(scene['input'][0])==30
    assert len(scene['certificate']['pieces'])==9
    for mode in a.PARAMETERS['mode']:
        assert evaluator(a.program({'mode':mode}),scene['input'])==scene[mode]

def load_public_io():
    path=HOME/'workspace/parametric/public_io.py';assert path.is_file(),'public verifier absent'
    spec=importlib.util.spec_from_file_location('public_io_446',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.mark.parametrize('damage',['answer','setting','future','boolean','duplicate','id','noncanonical','duplicate_key'])
def test_public_verifier_rejects_corruption(damage):
    from copy import deepcopy
    import hashlib
    io=load_public_io();a=load();view=a.public_turn(a.generate(17,{'mode':'assembly'},2,4),0)
    raw=io.encode(view);assert io.validate(raw,hashlib.sha256(raw).hexdigest())==view
    broken=deepcopy(view)
    if damage=='answer':broken['test'][0]['output']=[[8]]
    if damage=='setting':broken['settings']={'mode':'assembly'}
    if damage=='future':broken['test'].append({'input':[[1]]})
    if damage=='boolean':broken['test'][0]['input'][0][0]=True
    if damage=='duplicate':broken['test'][0]['input']=broken['train'][0]['input']
    raw=(json.dumps(broken,sort_keys=True,separators=(',',':'))+'\n').encode()
    identity=hashlib.sha256(raw).hexdigest()
    if damage=='id':identity='0'*64
    if damage=='noncanonical':raw=raw.rstrip();identity=hashlib.sha256(raw).hexdigest()
    if damage=='duplicate_key':raw=b'{"test":[],"test":[],"train":[]}\n';identity=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):io.validate(raw,identity)

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'seed':2**63},{'demos':1},{'demos':7},{'demos':True},{'queries':0},{'queries':5},{'queries':True}])
def test_strict_counts(kwargs):
    a=load();args=dict(seed=0,settings={'mode':'assembly'},demos=2,queries=4);args.update(kwargs)
    with pytest.raises(ValueError):a.generate(**args)

@pytest.mark.parametrize('settings',[{}, {'mode':True},{'mode':'none'},{'mode':'assembly','extra':0}])
def test_strict_setting(settings):
    with pytest.raises(ValueError):load().program(settings)

@pytest.mark.parametrize('grid',[[],[[]],[[True]],[[1.0]],[[10]],[[0],[0,1]],[[0]*31]])
def test_strict_grid(grid):
    with pytest.raises(ValueError):load().solve(grid)

def load_verifier():
    path=HOME/'workspace/parametric/verify.py';assert path.is_file(),'source-bound verifier absent'
    spec=importlib.util.spec_from_file_location('verify_446',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_verifier_rejects_stale_binding(tmp_path):
    import hashlib
    v=load_verifier();p=tmp_path/'source.py';p.write_text('a=1\n')
    receipt={'source_binding':{'files':[{'path':'source.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
    v.check_binding(tmp_path,receipt)
    p.write_text('a=2\n')
    with pytest.raises(ValueError):v.check_binding(tmp_path,receipt)

def test_difference_counts_shape_changes():
    v=load_verifier()
    assert v.difference([[1,2]],[[1,2],[3,4]])=={'overlap_changed':0,'shape_only_cells':2,'changed_cells':2,'shape_changed':True}
    assert v.difference([[1,2]],[[1,3]])['changed_cells']==1

def test_returned_metadata_cannot_mutate_cached_scene():
    from copy import deepcopy
    a=load();ep=a.generate(17,{'mode':'assembly'},2,4);expected=deepcopy(ep)
    ep['private']['profiles'][0]['caller_added']='CANARY'
    assert a.generate(17,{'mode':'assembly'},2,4)==expected
