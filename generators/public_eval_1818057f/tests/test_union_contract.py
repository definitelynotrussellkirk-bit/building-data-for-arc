from pathlib import Path
import importlib.util,json,shutil,sys
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
BASE=HOME/'workspace/parametric'
def load(path):
    spec=importlib.util.spec_from_file_location('union_contract_'+str(path),path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def test_active_union_uses_declared_closure(tmp_path):
    contract=json.loads((BASE/'promotion.json').read_text())
    for name in [contract['adapter'],*contract['resources']]:
        dest=tmp_path/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    a=load(tmp_path/contract['adapter']);episode=a.generate(17,contract['default'],3,4)
    assert episode['program_solution']==(HOME/'reference.rkt').read_text()
    assert len(episode['train'])==3 and len(episode['test'])==4
    assert len({json.dumps(p['input'])for p in episode['train']+episode['test']})==7
    with pytest.raises(ValueError):a.generate(17,contract['default'],2,4)

def test_active_union_keeps_prefixes_and_private_projection():
    a=load(BASE/'adapter.py');contract=json.loads((BASE/'promotion.json').read_text());full=a.generate(1,contract['default'],6,4)
    for d in range(3,7):
        for q in range(1,5):
            e=a.generate(1,contract['default'],d,q);assert e['train']==full['train'][:d] and e['test']==full['test'][:q]
    full['secret']='private'
    for p in full['train']+full['test']:p['secret']='private'
    view=a.public_view(full,0);assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    assert all(set(p)=={'input','output'}for p in view['train'])
