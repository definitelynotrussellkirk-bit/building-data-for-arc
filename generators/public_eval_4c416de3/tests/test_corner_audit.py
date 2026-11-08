import importlib.util
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]

def load():
    path=HOME/'workspace/parametric/audit.py';assert path.is_file(),'Reusable audit required'
    spec=importlib.util.spec_from_file_location('corner_audit_test',path)
    obj=importlib.util.module_from_spec(spec);sys.modules[spec.name]=obj;spec.loader.exec_module(obj)
    return obj

@pytest.mark.parametrize('seed',[0,1,14,17,43,63])
def test_two_demos_reject_query_changing_rivals(seed):
    audit=load();a=audit.adapter
    for mode in audit.MODES:
        ep=a.generate(seed,{audit.PARAMETER:mode},2,4)
        predictions=[audit.rivals(p['input'],mode)for p in ep['train']+ep['test']]
        for name in predictions[0]:
            if all(predictions[i][name]==p['output']for i,p in enumerate(ep['train'])):
                assert all(predictions[i+2][name]==p['output']for i,p in enumerate(ep['test'])),(seed,mode,name)

def test_witness_contract_rejects_unprotected_runtime():
    a=load()
    with pytest.raises(ValueError):a.make_witness({}, {'backend':'racket','protected':False}, {})
    w=a.make_witness({}, {'backend':'racket','protected':True,'extra':'attestation'}, {})
    assert w['racket']=={'backend':'racket','protected':True}
    assert w['runtime_identity']['extra']=='attestation'
