"""Public filenames use visible content rather than setting-associated ordinals."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import os
import pytest
TASK = Path(__file__).resolve().parents[1].name
SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'
@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location(TASK+'_public_names', SOURCE)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def test_public_name_excludes_hidden_metadata_and_query_answers(proto):
    value={'seed':0,'parameters':{'setting':0},'train':[{'input':[[1]],'output':[[2]]}], 'test':[{'input':[[3]],'output':[[4]]}]}
    name=proto.public_filename(value)
    changed=deepcopy(value);changed['seed']=19;changed['parameters']={'setting':1};changed['test'][0]['output']=[[9]]
    assert proto.public_filename(changed)==name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json',name)
    changed['train'][0]['output']=[[8]]
    assert proto.public_filename(changed)!=name

def test_actual_racket_writer_uses_content_names(proto,tmp_path):
    out=tmp_path/'export'
    if TASK=='f1347e0836ec':
        import subprocess
        result=subprocess.run([sys.executable,str(SOURCE.with_name('build_prototype.py')),'--out-dir',str(out)],capture_output=True,text=True,timeout=90)
        assert result.returncode==0,result.stdout+result.stderr
        files=list(out.glob('challenge-*.json'))
    else:
        proto.write_evidence(out)
        files=list((out/'public').glob('*.json'))
    assert len(files)==2
    capture=os.environ.get("ARCPUZZLES_OWNER_EXPORT_CAPTURE")
    if capture:
        with open(capture,"a") as stream: stream.write(json.dumps({"task_id":TASK,"path":str(out)})+"\n")
    for path in files:
        public=json.loads(path.read_text())
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json',path.name)
        assert proto.public_filename(public)==path.name
        queries=public.get('test',public.get('query'))
        if isinstance(queries,dict):queries=[queries]
        assert all(set(pair)=={'input'} for pair in queries)
