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
    value["task_id"]=TASK
    name=proto.public_filename(value)
    changed=deepcopy(value);changed['seed']=19;changed['parameters']={'setting':1};changed['test'][0]['output']=[[9]]
    assert proto.public_filename(changed)==name
    assert proto.public_challenge(changed)==proto.public_challenge(value)
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json',name)
    changed['train'][0]['output']=[[8]]
    assert proto.public_filename(changed)!=name

def test_actual_racket_writer_uses_content_names(proto,tmp_path):
    out=tmp_path/'export'
    if TASK=='0b8ba9bb3c63':
        proto.write_evidence(out,seeds=[11],beam_axes='all')
        files=list(out.glob('*.challenge.json'))+list(out.glob('challenge-*.json'))
        assert len(files)==3
    else:
        if TASK=='22e428cda452': proto.materialize(out)
        elif TASK=='db95939a5dd0': proto.build_racket_evidence(out)
        elif TASK=='b8d6fabb411e': proto.build_evidence(0,out)
        elif TASK=='7944933e200f': proto.build_evidence(out)
        else: proto.materialize(out,seed=0)
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
