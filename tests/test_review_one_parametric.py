"""One full build with deep self-review, preserving issued multi-target contracts."""
import json
import pytest
from arcpuzzles.review_full_draw import draw_main, repair_selection_for_seed
from arcpuzzles.review_targets import parametric_target_ids, validate_target_outcomes
from test_review_full_draw import _packet

POLICY = {'schema': 'arcpuzzles-one-parametric-admission-v1', 'roles': ['parametric'],
          'priority': 'build_then_deep_adversarial_repair', 'peer_work': 'none',
          'completion': 'native_owner_accepted', 'demonstration_range': [2, 6],
          'training_queries': 4, 'query_visibility': 'sequential_without_total_count_hint'}

def test_one_native_draw_and_honest_result(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=1, work_policy=POLICY,
                     supplementary_tickets=True, reviewer_solve=True, blind_solve=True)
    m = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    assert m['work_policy'] == POLICY
    assert m['repair_target_policy']['count'] == 1
    assert 'supplementary_ticket_policy' not in m
    for seed in range(12):
        assert len(repair_selection_for_seed(m, seed.to_bytes(32, 'big'))) == 1
    c = draw_main(packet, bytes(32))
    assert len(c['repair_targets']) == 1 and parametric_target_ids(c) == [c['task_id']]
    r = json.loads((packet/'RESULTS.json').read_text())
    validate_target_outcomes(c, r)
    r['completion_state'] = 'complete'
    with pytest.raises(ValueError, match='ready'):
        validate_target_outcomes(c, r)
    assert not (packet/'AUDIT_ASSIGNMENT.json').exists()
    assert 'blind_solve' not in c and 'reviewer_solve' not in c
    duties = (packet/'DUTIES.md').read_text()
    assert 'Deep adversarial self-review' in duties and 'crossed controls' in duties
    assert 'partial intermediate' in duties and 'No peer' in duties
    assert draw_main(packet, bytes([7])*32) == c

def test_single_owner_default_and_explicit_two_fallback(tmp_path):
    from arcpuzzles.review_full_packet import _owner_work_policy
    from arcpuzzles.review_targets import TWO_WORK_POLICY
    (tmp_path/'full-packet-current.json').write_text(json.dumps({'default_work_policy': POLICY}))
    assert _owner_work_policy(tmp_path, 1, None) == POLICY
    assert _owner_work_policy(tmp_path, 2, None) == TWO_WORK_POLICY

def test_cli_defaults_to_one_focused_build():
    from arcpuzzles.cli import parser
    assert parser().parse_args(['review','pack-full','--out','var/send.zip']).repair_targets == 1

@pytest.mark.parametrize('policy_at', [('manifest',),('contract',),('manifest','contract')])
def test_outer_status_exposes_only_one_deep_review(tmp_path, policy_at):
    from test_review_main_role_status import workspace, status
    outer = workspace(tmp_path, policy_at=())
    for name in policy_at:
        path = outer/'WORK'/('PACKET-MANIFEST.json' if name == 'manifest' else 'ASSIGNMENT.json')
        value = json.loads(path.read_text());value['work_policy'] = POLICY
        if name == 'contract':value['repair_targets'] = value['repair_targets'][:1]
        path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    cpath=outer/'WORK/ASSIGNMENT.json';c=json.loads(cpath.read_text());c['repair_targets']=c['repair_targets'][:1];cpath.write_text(json.dumps(c))
    output = status(outer,tmp_path)
    assert 'ONLY TARGET:' in output and 'deep adversarial self-review' in output
    assert 'Optional remaining-time peer' not in output and 'Robustness check' not in output
    assert 'Two audits:' not in output

def test_owner_admission_runs_once_and_does_not_activate_training(monkeypatch,tmp_path):
    from arcpuzzles import review_parametric_admission as admission
    c={'work_policy': POLICY,'task_id':'target','generator':{},'assignment_id':'review-test'}
    calls=[]
    def fake(cat,contract,row,archive,**kwargs):
        calls.append(contract['task_id'])
        return {'task_id':contract['task_id'],'status':'accepted','objective_met':True,'training_admitted':False}
    monkeypatch.setattr(admission,'admit_main',fake)
    result=admission.admit_assignment(None,c,{'target':{}},tmp_path/'return.zip')
    assert calls==['target'] and result['objective_met'] is True and result['training_admitted'] is False

def test_invalid_owner_policy_cannot_fall_back_to_legacy_single(tmp_path):
    from arcpuzzles.review_full_packet import _owner_work_policy
    (tmp_path/'full-packet-current.json').write_text(json.dumps({'default_work_policy': {**POLICY,'roles':[]}}))
    with pytest.raises(ValueError,match='default_work_policy'):
        _owner_work_policy(tmp_path,1,None)
