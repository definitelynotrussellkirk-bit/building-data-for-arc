import copy
import json
import importlib.util
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]

def tools():
    path=HOME/'workspace/parametric/authoring_tools.py'
    assert path.is_file(), 'Reproducible authoring/export utility missing'
    spec=importlib.util.spec_from_file_location('quadrant_tools_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_export_is_visible_only_and_enumeration_independent(tmp_path):
    m=tools()
    episodes=[m.adapter.generate(seed,s,2,4) for seed in [0,17] for s in m.adapter.SETTINGS]
    one=tmp_path/'a';two=tmp_path/'b'
    m.write_views(episodes,one)
    altered=copy.deepcopy(list(reversed(episodes)))
    for e in altered:
        e['seed']=987;e['settings']={'private':'value'};e['program_solution']='secret'
        for p in e['test']:p['output']=[[9]]
    m.write_views(altered,two)
    first={p.name:p.read_bytes() for p in (one/'public').iterdir()}
    second={p.name:p.read_bytes() for p in (two/'public').iterdir()}
    assert len(first)==16 and first==second
    manifest=json.loads((one/'private/manifest.json').read_text())
    listed=[row['path'] for row in manifest['public_files']]
    assert listed==sorted(listed)

def test_duplicate_export_refuses_without_destination(tmp_path):
    m=tools();e=m.adapter.generate(0,m.adapter.SETTINGS[0],2,4);dest=tmp_path/'duplicate'
    with pytest.raises(ValueError,match='Duplicate'):m.write_views([e,e],dest)
    assert not dest.exists()

def test_existing_destination_untouched(tmp_path):
    m=tools();dest=tmp_path/'old';dest.mkdir();(dest/'keep').write_text('untouched')
    with pytest.raises(FileExistsError):m.write_views([m.adapter.generate(0,m.adapter.SETTINGS[0],2,4)],dest)
    assert (dest/'keep').read_text()=='untouched' and len(list(dest.iterdir()))==1

def test_future_query_invariance():
    m=tools();e=m.adapter.generate(17,m.adapter.SETTINGS[1],2,4)
    view=m.visible_bytes(e,0)
    e['test'][1:] = [{'input':[[0]],'output':[[1]]}]
    e['test'][0]['output']=[[8]]
    assert m.visible_bytes(e,0)==view


@pytest.mark.parametrize('field,value', [('task_id','wrong'),('schema','wrong'),('training_admitted',True),('public_files',[]),('limits','altered')])
def test_export_verifier_rejects_any_manifest_change(tmp_path,monkeypatch,field,value):
    m=tools();e=m.adapter.generate(0,m.adapter.SETTINGS[0],2,4)
    receipt={'task_id':m.TASK,'source_binding':{'files':[]}}
    execution={'episodes':[e]}
    # This test owns the bundle verifier; shared source validation is a separate
    # boundary exercised by the real preflight/export integration checks.
    monkeypatch.setattr(m,'verified',lambda path:(receipt,execution))
    preflight=tmp_path/'preflight.json';preflight.write_text('{}')
    dest=tmp_path/'bundle';m.export(preflight,dest)
    assert m.verify_export(preflight,dest)['status']=='passed'
    path=dest/'private/manifest.json';manifest=json.loads(path.read_text());manifest[field]=value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='manifest'):m.verify_export(preflight,dest)
