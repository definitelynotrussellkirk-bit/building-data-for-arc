"""Metadata-only old-public-return repair; no runtime jobs or catalog mutations."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import review_public_compatibility as compat

PID='1234abcd'
TID='public_eval_'+PID
RID='ee_'+PID


def sha(raw):return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def source(tmp_path):
    root=tmp_path/'library';home=root/'generators'/TID;home.mkdir(parents=True)
    code=('#!/usr/bin/env python3\n# coding: utf-8\n"""Module docstring µ."""\n'
          'from __future__ import annotations\n'
          'PROGRAM = "(rule! (lambda (g) g))"\n'
          'def sample(seed):\n    return [[seed % 10]]\n').encode()
    path=home/'generator.py';path.write_bytes(code);path.chmod(0o644)
    resource=home/'reference.rkt';resource.write_text('(rule! (lambda (g) g))')
    binding={'task_id':TID,'files':[{'path':path.relative_to(root).as_posix(),'sha256':sha(code)},
             {'path':resource.relative_to(root).as_posix(),'sha256':sha(resource.read_bytes())}],
             'extra_report_metadata':{'preserved':True}}
    return root,path,resource,binding


def test_missing_literal_repair_preserves_all_original_bytes_and_future_imports(source):
    root,path,resource,binding=source;before=path.read_bytes();rule=resource.read_bytes()
    repair=compat.repair_reference_id(root,TID,PID)
    after=path.read_bytes();edit=repair['edit'];offset=edit['offset']
    assert after[:offset]+after[offset+len(edit['after'].encode()):]==before
    assert after.index(b'from __future__')<after.index(b'RULE_TASK_ID')<after.index(b'PROGRAM')
    compile(after,str(path),'exec')
    assert resource.read_bytes()==rule and path.stat().st_mode & 0o777==0o644
    assert repair['before_sha256']==sha(before) and repair['after_sha256']==sha(after)
    assert repair['approval_granted'] is False
    assert (root/repair['receipt_path']).is_file()
    assert not (root/'catalog').exists()


def test_only_descriptive_literal_value_is_replaced(source):
    root,path,_,_=source
    before=b"RULE_TASK_ID: str = 'public_eval_1234abcd' # retained comment\nPROGRAM='untouched'\n"
    path.write_bytes(before)
    receipt=compat.repair_reference_id(root,TID,PID)
    assert path.read_bytes()==before.replace(b"'public_eval_1234abcd'",b"'ee_1234abcd'")
    assert receipt['edit']['kind']=='replace_descriptive_literal'


@pytest.mark.parametrize('code',[
    "RULE_TASK_ID='ee_'+'1234abcd'\n",
    "RULE_TASK_ID='ee_00000000'\n",
    "RULE_TASK_ID='public_eval_1234abcd'\nRULE_TASK_ID='public_eval_1234abcd'\n",
    "RULE_TASK_ID=OTHER='public_eval_1234abcd'\n",
    "if True:\n    RULE_TASK_ID='public_eval_1234abcd'\n",
    "from somewhere import RULE_TASK_ID\n",
    "RULE_TASK_ID: str\n",
])
def test_ambiguous_computed_wrong_or_multiple_declarations_are_never_changed(source,code):
    root,path,_,_=source;path.write_text(code)
    with pytest.raises(ValueError):compat.repair_reference_id(root,TID,PID)
    assert path.read_text()==code
    assert not (path.parent/'evidence/owner-reference-compatibility').exists()


def test_accepted_source_is_never_repaired_and_valid_literal_is_a_noop(source):
    root,path,_,_=source;before=path.read_bytes()
    accepted=path.parent/'parametric/accepted.json';accepted.parent.mkdir();accepted.write_text('{}')
    with pytest.raises(ValueError,match='accepted artifact'):compat.repair_reference_id(root,TID,PID)
    assert path.read_bytes()==before
    path.write_text("RULE_TASK_ID='ee_1234abcd'\n")
    assert compat.repair_reference_id(root,TID,PID) is None


def test_foreign_namespace_and_symlinked_source_or_receipt_are_refused(source,tmp_path):
    root,path,_,_=source;before=path.read_bytes()
    with pytest.raises(ValueError,match='namespace'):compat.repair_reference_id(root,'other_family',PID)
    target=tmp_path/'foreign.py';target.write_bytes(before);path.unlink();path.symlink_to(target)
    with pytest.raises(ValueError,match='symlink|escapes'):compat.repair_reference_id(root,TID,PID)
    path.unlink();path.write_bytes(before)
    outside=tmp_path/'evidence';outside.mkdir();(path.parent/'evidence').symlink_to(outside)
    with pytest.raises(ValueError,match='symlink|escapes'):compat.repair_reference_id(root,TID,PID)
    assert path.read_bytes()==before and not list(outside.iterdir())


def test_idempotent_rebinding_requires_retained_exact_reversible_proof(source):
    root,path,resource,binding=source;original=copy.deepcopy(binding)
    receipt=compat.repair_reference_id(root,TID,PID)
    rebound=compat.rebind_source_binding(root,TID,PID,binding,receipt)
    assert binding==original
    expected=copy.deepcopy(original);expected['files'][0]['sha256']=sha(path.read_bytes())
    assert rebound==expected
    assert compat.repair_reference_id(root,TID,PID) is None
    assert compat.rebind_source_binding(root,TID,PID,binding)==rebound
    (root/receipt['receipt_path']).unlink()
    with pytest.raises(ValueError,match='regular file'):
        compat.rebind_source_binding(root,TID,PID,binding)


def test_non_generator_source_drift_blocks_compatibility_rebinding(source):
    root,path,resource,binding=source
    receipt=compat.repair_reference_id(root,TID,PID)
    resource.write_text('(rule! (lambda (g) (reverse g)))')
    with pytest.raises(ValueError,match='non-generator'):
        compat.rebind_source_binding(root,TID,PID,binding,receipt)


def test_arbitrary_code_change_cannot_hide_behind_metadata_receipt(source):
    root,path,_,binding=source
    receipt=compat.repair_reference_id(root,TID,PID)
    path.write_bytes(path.read_bytes().replace(b'seed % 10',b'(seed + 1) % 10'))
    proof_path=root/receipt['receipt_path'];proof=json.loads(proof_path.read_text())
    # Even a rewritten after hash cannot make the inverse recover the reviewed bytes.
    proof['after_sha256']=sha(path.read_bytes());proof_path.write_text(json.dumps(proof))
    with pytest.raises(ValueError,match='metadata-only'):
        compat.rebind_source_binding(root,TID,PID,binding)


def test_receipt_failure_rolls_back_the_generator(source,monkeypatch):
    root,path,_,_=source;before=path.read_bytes();original=compat._atomic
    def fail_proof(target,raw,mode=0o644):
        if target.suffix=='.json':raise OSError('simulated receipt failure')
        return original(target,raw,mode)
    monkeypatch.setattr(compat,'_atomic',fail_proof)
    with pytest.raises(OSError,match='receipt failure'):compat.repair_reference_id(root,TID,PID)
    assert path.read_bytes()==before


@pytest.mark.parametrize('raw',[b'# only a comment',b'\xef\xbb\xbf"""doc"""\nfrom __future__ import annotations\nX=1\n',b'"""doc"""\r\nfrom __future__ import annotations\r\nX=1\r\n'])
def test_encoding_headers_and_line_endings_remain_reversible(source,raw):
    root,path,_,_=source;path.write_bytes(raw)
    receipt=compat.repair_reference_id(root,TID,PID)
    edit=receipt['edit'];after=path.read_bytes();offset=edit['offset']
    assert after[:offset]+edit['before'].encode()+after[offset+len(edit['after'].encode()):]==raw
    compile(after,str(path),'exec')
