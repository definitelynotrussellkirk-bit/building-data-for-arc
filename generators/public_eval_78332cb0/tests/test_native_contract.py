"""Reusable source/visibility/relocation checks for native public families."""
from pathlib import Path
import copy, hashlib, importlib.util, json, shutil, subprocess, sys
import pytest
HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'
def load(name):
    sp=importlib.util.spec_from_file_location('_contract_'+HOME.name+'_'+name,BASE/(name+'.py'))
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);return mod

def sample():
    a=load('adapter');key=next(iter(a.PARAMETERS));return a,a.generate(17,{key:a.PARAMETERS[key][-1]},2,4)

@pytest.mark.parametrize('kind',range(9))
def test_corrupt_public_views_rejected(kind):
    a,e=sample();io=load('public_io');v=a.public_turn(e);raw=io.encode(v)
    if kind==0:v['settings']={'private':1}
    elif kind==1:v['test'][0]['output']=[[1]]
    elif kind==2:v['test'].append({'input':[[1]]})
    elif kind==3:v['test'][0]['input']=[[True]]
    elif kind==4:v['test'][0]['input']=[[1.0]]
    elif kind==5:v['test'][0]['input']=v['train'][0]['input']
    elif kind==6:v['train'][0]['input']=[[1],[1,2]]
    elif kind==7:
        with pytest.raises(ValueError):io.validate(raw,'0'*64)
        return
    elif kind==8:
        with pytest.raises(ValueError):io.validate(raw+b' ',hashlib.sha256(raw+b' ').hexdigest())
        return
    with pytest.raises(ValueError):io.encode(v)

def test_verifier_rejects_stale_source(tmp_path):
    v=load('verify');p=tmp_path/'source.py';p.write_text('pass')
    r={'status':'passed','source_binding':{'files':[{'path':'source.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
    v.verify_binding(tmp_path,r);p.write_text('different')
    with pytest.raises(ValueError):v.verify_binding(tmp_path,r)

def test_verifier_shape_difference_not_silent():
    v=load('verify');assert v.differences([[1]],[[1,2],[3,4]])['changed_cells']==3

def test_receipt_wrong_identity_rejected():
    v=load('verify')
    with pytest.raises(ValueError):v.verify_receipt_identity({'status':'passed'},HOME.name,{})

@pytest.mark.parametrize('closure',['native','ordinary'])
def test_isolated_resource_closure(tmp_path,closure):
    if closure=='native':
        for name in ['adapter.py','engine.py','canonical.rkt']:shutil.copy(BASE/name,tmp_path/name)
        script="""import importlib.util,pathlib,json
p=pathlib.Path('adapter.py').resolve();s=importlib.util.spec_from_file_location('isolated',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
k=next(iter(m.PARAMETERS))
for mode in m.PARAMETERS[k]:
 for d in range(2,7):
  for q in range(1,5):
   e=m.generate(43,{k:mode},d,q);assert len(e['train'])==d and len(e['test'])==q;assert e['program_solution']==m.program({k:mode})
print('40 isolated native jobs passed')
"""
    else:
        shutil.copy(HOME/'generator.py',tmp_path/'generator.py')
        script="""import importlib.util,pathlib
p=pathlib.Path('generator.py').resolve();s=importlib.util.spec_from_file_location('isolated',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for i in range(10):
 e=m.generate(seed=43,sample_index=i,difficulty='hard');assert not m.self_check(e['input'])
print('10 isolated ordinary profiles passed')
"""
    result=subprocess.run([sys.executable,'-I','-c',script],cwd=tmp_path,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
