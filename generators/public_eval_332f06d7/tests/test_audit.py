from pathlib import Path
import hashlib
import importlib.util
import sys
import pytest
BASE=Path(__file__).resolve().parents[1]/'workspace/parametric'

def audit():
    assert (BASE/'audit.py').is_file(), 'Source-bound audit missing'
    spec=importlib.util.spec_from_file_location('_motion_audit_test',BASE/'audit.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def test_witness_requires_live_protected_identity():
    a=audit()
    for identity in ({},{'backend':'python','protected':True},{'backend':'racket','protected':False}):
        with pytest.raises(ValueError):a.make_witness({},identity,{})
    w=a.make_witness({}, {'backend':'racket','protected':True,'binary_sha256':'abc'}, {})
    assert w['racket']=={'backend':'racket','protected':True}
    assert w['runtime_identity']['binary_sha256']=='abc'

def test_source_drift_and_escape_are_rejected(tmp_path):
    a=audit();p=tmp_path/'source.py';p.write_text('original')
    binding={'files':[{'path':'source.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
    a.assert_binding(tmp_path,binding);p.write_text('changed')
    with pytest.raises(ValueError):a.assert_binding(tmp_path,binding)
    with pytest.raises(ValueError):a.assert_binding(tmp_path,{'files':[{'path':'../escape','sha256':'0'*64}]})

def test_two_demo_teaching_rejects_query_changing_rivals():
    a=audit()
    for seed in (0,1,4,17):
        for mode in a.MODES:
            ep=a.adapter.generate(seed,{a.PARAMETER:mode},2,4)
            preds=[a.rivals(p['input'],mode) for p in ep['train']+ep['test']]
            for name in preds[0]:
                if all(preds[i][name]==ep['train'][i]['output'] for i in range(2)):
                    assert all(preds[2+i][name]==p['output'] for i,p in enumerate(ep['test'])),(seed,mode,name)
