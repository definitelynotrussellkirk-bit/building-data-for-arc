from pathlib import Path
import copy
import importlib.util
import json
import pytest

P=Path(__file__).resolve().parents[1]/'workspace/parametric'

def load(name):
    path=P/(name+'.py')
    assert path.is_file(), 'missing '+name
    spec=importlib.util.spec_from_file_location('_plus_'+name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj

def test_presentation_implementation_exists():
    assert (P/'presentation.py').is_file()

def test_full_bank_shuffle_prefix_and_privacy():
    a=load('adapter');m=load('presentation');ep=a.generate(17,{'selection':'all'},2,4)
    first=set()
    for seed in range(32):
        bank=m.project(ep,source_seed=17,presentation_seed=seed,limit=4)
        assert len(bank)==4
        one=m.project(ep,source_seed=17,presentation_seed=seed,limit=1)
        assert one==bank[:1]
        first.add(one[0]['source_index'])
        for row in bank:
            value=json.loads(row['bytes'])
            assert set(value)=={'train','test'} and len(value['test'])==1
            assert set(value['test'][0])=={'input'}
            assert value['test'][0]['input']==ep['test'][row['source_index']]['input']
        changed=copy.deepcopy(ep);changed.update(seed='private',settings='private',program_solution='private')
        for pair in changed['test']:pair['output']=[[9]];pair['future_hint']='private'
        assert m.project(changed,source_seed=17,presentation_seed=seed,limit=4)==bank
    assert first=={0,1,2,3}

def test_public_identity_and_duplicate_rejection(tmp_path):
    import hashlib
    a=load('adapter');m=load('presentation');ep=a.generate(9,{'selection':'all'},2,4)
    rows=m.project(ep,source_seed=9,presentation_seed=0,limit=4)
    path=tmp_path/'bad'
    with pytest.raises(ValueError):m.write_batch(rows+rows,path)
    assert not path.exists()
    path=tmp_path/'good';m.write_batch(rows,path)
    for row in rows:
        assert row['id']==hashlib.sha256(row['bytes']).hexdigest()
        assert (path/(row['id']+'.json')).read_bytes()==row['bytes']
    with pytest.raises(FileExistsError):m.write_batch(rows,path)

@pytest.mark.parametrize('updates',[{'limit':0},{'limit':True},{'limit':5},{'source_seed':True},{'presentation_seed':-1}])
def test_bad_presentation_controls(updates):
    a=load('adapter');m=load('presentation');ep=a.generate(0,{'selection':'all'},2,4)
    args={'source_seed':0,'presentation_seed':0,'limit':1};args.update(updates)
    with pytest.raises(ValueError):m.project(ep,**args)

def test_partial_bank_rejected():
    a=load('adapter');m=load('presentation');ep=a.generate(0,{'selection':'all'},2,1)
    with pytest.raises(ValueError):m.project(ep,source_seed=0,presentation_seed=0,limit=1)

@pytest.mark.parametrize('leak',['settings','answer','future_queries'])
def test_writer_rejects_private_fields_even_with_correct_hash(tmp_path,leak):
    import hashlib
    a=load('adapter');m=load('presentation');ep=a.generate(7,{'selection':'all'},2,4)
    row=m.project(ep,source_seed=7,presentation_seed=0,limit=1)[0]
    value=json.loads(row['bytes']);value[leak]='PRIVATE'
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    row={'bytes':raw,'id':hashlib.sha256(raw).hexdigest(),'source_index':0}
    with pytest.raises(ValueError,match='public'):m.write_batch([row],tmp_path/'leaky')
    assert not (tmp_path/'leaky').exists()
