"""Exercise emitted audit artifacts and fail-closed source-bound preflight checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]

def load(name):
    path=HOME/'workspace/parametric'/name
    assert path.exists(),f'Missing tool: {name}'
    spec=importlib.util.spec_from_file_location('_tool_'+str(abs(hash(str(path)))),path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def test_audit_emits_only_single_query_visible_files(tmp_path):
    tool=load('audit_native.py')
    result=tool.audit(2,tmp_path/'audit',racket_seeds=0)
    assert result['status']=='passed' and result['episodes']==4
    assert result['prefix_checks']==80 and result['racket_evaluations']==0
    files=list((tmp_path/'audit/public').glob('*.json'));assert len(files)==16
    for p in files:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==p.stem
        data=json.loads(p.read_bytes());assert set(data)=={'train','test'}
        assert len(data['test'])==1 and set(data['test'][0])=={'input'}
    with pytest.raises(ValueError):tool.audit(1,tmp_path/'audit',racket_seeds=0)

@pytest.mark.parametrize('kind',['bad_status','source_drift','evidence_drift','missing_source','unsafe_path'])
def test_witness_preflight_guard_rejects_invalid_receipts(tmp_path,kind):
    tool=load('authoring_witness.py'); root=tmp_path/'repo';home=root/'generators/public_eval_12345678'
    home.mkdir(parents=True);(home/'reference.rkt').write_text('rule')
    runtime=root/'shared/runtime';runtime.mkdir(parents=True);(runtime/'test.py').write_text('pass')
    (root/'shared/tools').mkdir();(root/'shared/tools/comment_solutions.py').write_text('pass')
    out=tmp_path/'preflight';out.mkdir()
    execution={'racket':{'backend':'racket','protected':True},'episodes':[]}
    originals={'status':'passed','pairs':[{'input':[[1]],'output':[[1]]}]}
    for n,v in [('execution.json',execution),('original-pairs.json',originals)]: (out/n).write_text(json.dumps(v))
    files=[{'path':str(p.relative_to(root)),'sha256':tool.sha(p)} for p in root.rglob('*') if p.is_file()]
    receipt={'schema':'arcpuzzles-public-eval-authoring-preflight-v1','status':'passed',
             'verification_status':'authoring_preflight_not_owner_qualification','owner_accepted':False,
             'task_id':'public_eval_12345678','source_binding':{'task_id':'public_eval_12345678','files':files},
             'programs':{},'evidence_sha256':{n:tool.sha(out/n) for n in ('execution.json','original-pairs.json')}}
    if kind=='bad_status':receipt['owner_accepted']=True
    if kind=='source_drift':(home/'reference.rkt').write_text('changed')
    if kind=='evidence_drift':(out/'execution.json').write_text('{}')
    if kind=='missing_source':receipt['source_binding']['files'].pop()
    if kind=='unsafe_path':receipt['source_binding']['files'][0]['path']='../outside.py'
    path=out/'preflight.json';path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):tool.checked_preflight(root,path)
