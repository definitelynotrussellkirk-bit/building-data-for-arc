"""Regression guards for authoring evidence rather than editable success flags."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]

def tool(name):
    path=HOME/'workspace/parametric'/f'{name}.py'
    assert path.is_file(), f'{name} not implemented'
    spec=importlib.util.spec_from_file_location('_2ba387bc_'+name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m

def test_all_named_rivals_are_rejected_by_two_demonstrations():
    a=tool('audit_native')
    for seed in range(8):
        for setting in ('row','column'):
            e=a.adapter.generate(seed,{'order_axis':setting},2,4)
            assert a.teaching_check(e,setting)==[]

def test_preflight_verifier_rejects_an_unqualified_success_flag(tmp_path):
    t=tool('authoring_witness');p=tmp_path/'preflight.json'
    p.write_text(json.dumps({'status':'passed','owner_accepted':True}))
    with pytest.raises(ValueError):t.verify_preflight(tmp_path,p)

def test_preflight_verifier_refuses_changed_execution_receipt(tmp_path):
    t=tool('authoring_witness');p=tmp_path/'preflight.json'
    p.write_text(json.dumps({'schema':'arcpuzzles-public-eval-authoring-preflight-v1',
        'status':'passed','verification_status':'authoring_preflight_not_owner_qualification',
        'owner_accepted':False,'task_id':HOME.name,'evidence_sha256':{'execution.json':'0'*64,'original-pairs.json':'0'*64}}))
    (tmp_path/'execution.json').write_text('{}')
    (tmp_path/'original-pairs.json').write_text('{}')
    with pytest.raises(ValueError):t.verify_preflight(tmp_path,p)
