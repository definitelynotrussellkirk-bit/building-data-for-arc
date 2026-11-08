import json
import pytest
from test_review_full_draw import _packet as _new_packet
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_targets import validate_target_outcomes


def _packet(library, tmp_path, **options):
    """Replay an issued main/two-check manifest, independent of new defaults."""
    from arcpuzzles.review_targets import MAIN_WORK_POLICY
    from arcpuzzles.review_full_packet import canonical_json
    packet = _new_packet(library, tmp_path, **options)
    path = packet / 'PACKET-MANIFEST.json'
    manifest = json.loads(path.read_text())
    manifest['work_policy'] = MAIN_WORK_POLICY
    path.write_bytes(canonical_json(manifest))
    return packet


def test_new_assignment_has_one_parametric_main_and_two_bounded_checks(library,tmp_path):
    packet=_packet(library,tmp_path,repair_target_count=3)
    c=draw_main(packet,bytes(32))
    assert c['work_policy']['effort_percent']==[70,15,15]
    assert c['work_policy']['demonstration_range']==[2,6]
    assert c['work_policy']['training_queries']==4
    duties=(packet/'DUTIES.md').read_text()
    assert '70% / 15% / 15%' in duties
    assert 'MAIN: robust parametric' in duties
    assert 'Do not build or repair parametric variants for the two secondary targets' in duties
    reports=json.loads((packet/'RESULTS.json').read_text())
    assert reports['repair_targets'][0]['parametric_work']['status']=='blocked'
    assert 'parametric_work' not in reports['repair_targets'][1]
    validate_target_outcomes(c,reports)


def test_main_parametric_progress_must_be_reported(library,tmp_path):
    packet=_packet(library,tmp_path,repair_target_count=3)
    c=draw_main(packet,bytes(32));r=json.loads((packet/'RESULTS.json').read_text())
    r['repair_targets'][0].pop('parametric_work',None)
    with pytest.raises(ValueError,match='parametric'):
        validate_target_outcomes(c,r)


def test_peer_parametric_edits_are_outside_new_duties(library,tmp_path):
    from arcpuzzles.review_full_return import _allowed
    packet=_packet(library,tmp_path,repair_target_count=3);c=draw_main(packet,bytes(32))
    main=c['task_id'];peer=c['repair_targets'][1]['task_id']
    assert _allowed(f'repo/generators/{main}/workspace/parametric/prototype.py',c)
    assert not _allowed(f'repo/generators/{peer}/workspace/parametric/prototype.py',c)
    assert _allowed(f'repo/generators/{peer}/generator.py',c)


def test_existing_three_repair_contract_keeps_issued_scope():
    from test_review_three_targets import contract
    from arcpuzzles.review_full_return import _allowed
    c=contract();peer=c['repair_targets'][1]['task_id']
    assert _allowed(f'repo/generators/{peer}/workspace/parametric/prototype.py',c)


def test_completed_main_prototype_must_exist_in_bound_inventory(library,tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_return import build_full_return
    c,_=_return(library,tmp_path,repair_target_count=3)
    work=tmp_path/'packet-0';r=json.loads((work/'RESULTS.json').read_text())
    evidence=work/'checks/main.txt';evidence.parent.mkdir(exist_ok=True);evidence.write_text('unrelated evidence')
    r['repair_targets'][0]['evidence_paths']=['checks/main.txt']
    r['repair_targets'][0]['parametric_work']={'status':'built','summary':'Claim must bind source',
        'prototype_path':f"repo/generators/{c['task_id']}/workspace/parametric/missing.py"}
    (work/'RESULTS.json').write_text(json.dumps(r))
    with pytest.raises(ValueError,match='absent from bound source'):
        build_full_return(work,tmp_path/'missing.zip')


def test_duties_restore_size_reasoning_and_sequential_query_requirements(library,tmp_path):
    packet=_packet(library,tmp_path,repair_target_count=3);draw_main(packet,bytes(32))
    duties=(packet/'DUTIES.md').read_text()
    for phrase in ['ARC-DESIGN.md','30x30','2–6','always four','one query per user turn','no total-count']:
        assert phrase in duties


def test_work_role_policy_cannot_be_stripped_from_return(library,tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_return import build_full_return
    _,_built=_return(library,tmp_path,repair_target_count=3)
    work=tmp_path/'packet-0';c=json.loads((work/'ASSIGNMENT.json').read_text());c.pop('work_policy');(work/'ASSIGNMENT.json').write_text(json.dumps(c))
    with pytest.raises(ValueError,match='work policy differs'):
        build_full_return(work,tmp_path/'stripped.zip')
