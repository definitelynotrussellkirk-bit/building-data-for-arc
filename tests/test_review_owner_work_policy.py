"""Owner defaults apply only to new two-target builds, with explicit overrides."""
import json
from pathlib import Path
import pytest
from arcpuzzles.catalog import Catalog
from arcpuzzles import review_full_packet as packet
from arcpuzzles.review_targets import TWO_WORK_POLICY
from arcpuzzles.review_public_creation import PUBLIC_WORK_POLICY


def test_owner_default_and_explicit_override(tmp_path):
    current=tmp_path/'full-packet-current.json'
    old={'packet_id':'issued-old','work_policy':PUBLIC_WORK_POLICY}
    current.write_text(json.dumps(old))
    assert packet._owner_work_policy(tmp_path,2,None) is None
    old['default_work_policy']=TWO_WORK_POLICY
    current.write_text(json.dumps(old)); before=current.read_bytes()
    assert packet._owner_work_policy(tmp_path,2,None)==TWO_WORK_POLICY
    assert packet._owner_work_policy(tmp_path,2,PUBLIC_WORK_POLICY)==PUBLIC_WORK_POLICY
    assert packet._owner_work_policy(tmp_path,1,None) is None
    assert packet._owner_work_policy(tmp_path,3,None) is None
    assert current.read_bytes()==before
    old['default_work_policy']={'schema':'typo'};current.write_text(json.dumps(old))
    with pytest.raises(ValueError,match='default_work_policy'):
        packet._owner_work_policy(tmp_path,2,None)


@pytest.mark.parametrize('explicit,expected',[(None,False),(PUBLIC_WORK_POLICY,True)])
def test_builder_default_skips_creation_queue_but_explicit_public_keeps_it(library,tmp_path,monkeypatch,explicit,expected):
    from arcpuzzles import review_public_creation
    review=library/'REVIEW';review.mkdir(exist_ok=True)
    (review/'full-packet-current.json').write_text(json.dumps({'default_work_policy':TWO_WORK_POLICY}))
    calls=[]
    monkeypatch.setattr(review_public_creation,'creation_queue',lambda *a,**kw:calls.append(True) or [])
    class ReachedSourceAssembly(Exception): pass
    def stop(*args,**kwargs): raise ReachedSourceAssembly
    monkeypatch.setattr(packet,'_source_files',stop)
    with pytest.raises(ReachedSourceAssembly):
        packet._build_full_packet(Catalog(library),review,tmp_path/'not-written.zip',
            repair_target_count=2,work_policy=explicit,selection_size=None)
    assert bool(calls) is expected
    assert not (tmp_path/'not-written.zip').exists()
