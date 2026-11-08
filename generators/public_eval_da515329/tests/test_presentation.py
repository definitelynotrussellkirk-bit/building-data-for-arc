from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'

def load(name):
    p=BASE/(name+'.py')
    assert p.is_file(), 'missing '+name
    spec=importlib.util.spec_from_file_location('_edb_test_'+name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_projection_shuffle_prefix_and_private_invariance():
    m=load('adapter');p=load('presentation')
    ep=m.generate(17,{'turn':'clockwise'},2,4);first=set()
    for seed in range(32):
        rows=p.project(ep,source_seed=17,presentation_seed=seed,limit=4)
        assert p.project(ep,source_seed=17,presentation_seed=seed,limit=1)==rows[:1]
        first.add(rows[0]['source_index'])
        for row in rows:
            v=json.loads(row['bytes'])
            assert set(v)=={'train','test'} and len(v['test'])==1
            assert set(v['test'][0])=={'input'}
            assert all(set(x)=={'input','output'} for x in v['train'])
            assert row['id']==hashlib.sha256(row['bytes']).hexdigest()
        changed=copy.deepcopy(ep);changed['settings']='PRIVATE';changed['program_solution']='PRIVATE'
        for pair in changed['train']:pair['metadata']='PRIVATE'
        for pair in changed['test']:pair['output']=[[9]];pair['metadata']='PRIVATE'
        assert p.project(changed,source_seed=17,presentation_seed=seed,limit=4)==rows
    assert first=={0,1,2,3}

def test_writer_rejects_duplicate_before_creation(tmp_path):
    m=load('adapter');p=load('presentation')
    rows=p.project(m.generate(0,{'turn':'clockwise'},2,4),source_seed=0,presentation_seed=0,limit=4)
    with pytest.raises(ValueError):p.write_batch(rows+rows,tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
    p.write_batch(rows,tmp_path/'ok')
    assert len(list((tmp_path/'ok').glob('*.json')))==4
    with pytest.raises(FileExistsError):p.write_batch(rows,tmp_path/'ok')

@pytest.mark.parametrize('where',['root','train','test'])
def test_writer_rejects_private_fields_with_correct_hash(tmp_path,where):
    m=load('adapter');p=load('presentation')
    rows=p.project(m.generate(0,{'turn':'clockwise'},2,4),source_seed=0,presentation_seed=0,limit=1)
    v=json.loads(rows[0]['bytes'])
    target=v if where=='root' else v[where][0]
    target['secret']='PRIVATE'
    raw=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
    rows[0]['bytes']=raw;rows[0]['id']=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):p.write_batch(rows,tmp_path/'bad')
    assert not (tmp_path/'bad').exists()

@pytest.mark.parametrize('args',[{'limit':True},{'limit':0},{'limit':5},{'source_seed':True},{'presentation_seed':-1}])
def test_bad_presentation_controls(args):
    m=load('adapter');p=load('presentation');ep=m.generate(0,{'turn':'clockwise'},2,4)
    kw={'source_seed':0,'presentation_seed':0,'limit':4};kw.update(args)
    with pytest.raises(ValueError):p.project(ep,**kw)



def test_writer_materializes_one_pass_iterables(tmp_path):
    m=load('adapter');p=load('presentation')
    rows=p.project(m.generate(0,{'turn':'clockwise'},2,4),source_seed=0,presentation_seed=0,limit=4)
    p.write_batch(iter(rows),tmp_path/'streamed')
    actual={x.name:x.read_bytes() for x in (tmp_path/'streamed').iterdir()}
    assert actual=={row['id']+'.json':row['bytes'] for row in rows}
