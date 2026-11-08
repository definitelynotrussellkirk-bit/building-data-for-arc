"""No general bypass: exact task, authority and discrepancy are required."""
import copy
from pathlib import Path
import pytest
from arcpuzzles.review_public_assumption import validate_authority, check_discrepancies, DISPUTED

ROOT=Path(__file__).resolve().parents[1]

def rows():
    return [dict(split=split,index=i,differences=[dict(row=r,col=c,derived=a,original=b)for r,c,a,b in DISPUTED] if split=='train' and i==0 else [])for split,count in [('train',5),('test',2)]for i in range(count)]

def test_exact_authorized_source():
    home,item,parent,program,decision_hash=validate_authority(ROOT)
    assert item['public_task_id']=='d8e07eb2' and len(parent['train'])==5
    assert len(decision_hash)==64

@pytest.mark.parametrize('task',['public_eval_00000000','public_eval_d8e07eb3','d8e07eb2'])
def test_other_tasks_rejected(task):
    with pytest.raises(ValueError,match='only for'):validate_authority(ROOT,task)

def test_only_exact_discrepancy_is_authorized():
    check_discrepancies(rows())
    for mutation in ('missing','extra','changed','wrong_pair','all_pass'):
        r=rows()
        if mutation=='missing':r[0]['differences'].pop()
        if mutation=='extra':r[1]['differences']=[dict(row=0,col=0,derived=1,original=2)]
        if mutation=='changed':r[0]['differences'][0]['derived']=4
        if mutation=='wrong_pair':r[0]['differences'],r[1]['differences']=r[1]['differences'],r[0]['differences']
        if mutation=='all_pass':r[0]['differences']=[]
        with pytest.raises(ValueError,match='nine-cell'):check_discrepancies(r)

def test_tampered_rule_rejected(tmp_path):
    import shutil
    home=tmp_path/'generators/public_eval_d8e07eb2';home.mkdir(parents=True)
    shutil.copytree(ROOT/'generators/public_eval_d8e07eb2/workspace',home/'workspace')
    shutil.copytree(ROOT/'shared/data/raw',tmp_path/'shared/data/raw')
    (home/'reference.rkt').write_text('(lambda (g) g)')
    with pytest.raises(ValueError,match='different reference'):validate_authority(tmp_path)

def test_assumed_coverage_is_explicit_and_source_bound(monkeypatch):
    from arcpuzzles.review_public_assumption import verified_assumed_coverage
    from arcpuzzles import parametric_promotion as native
    assert verified_assumed_coverage(ROOT)==['d8e07eb2']
    monkeypatch.setattr(native,'status',lambda *a,**kw:{'status':'stale','acceptance_sha256':'changed'})
    assert verified_assumed_coverage(ROOT)==[]

def test_changed_parent_metadata_rejected_before_execution(tmp_path):
    import json
    home=tmp_path/'generators/public_eval_d8e07eb2/workspace';home.mkdir(parents=True)
    target=json.loads((ROOT/'generators/public_eval_d8e07eb2/workspace/public-parent.json').read_text())
    target['source_record_sha256']='0'*64
    (home/'public-parent.json').write_text(json.dumps(target))
    with pytest.raises(ValueError,match='exact original'):validate_authority(tmp_path)
