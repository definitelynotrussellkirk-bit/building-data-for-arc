"""Two full native builds, without peer audits or weaker acceptance."""
import copy
import json

import pytest

from arcpuzzles.review_full_draw import draw_main, repair_selection_for_seed
from arcpuzzles.review_targets import parametric_target_ids, validate_target_outcomes
from test_review_full_draw import _packet
from test_review_three_targets import contract

POLICY = {'schema': 'arcpuzzles-two-parametric-admissions-v1',
          'roles': ['parametric', 'parametric'],
          'priority': 'finish_and_self_review_each_before_next',
          'peer_work': 'none', 'completion': 'both_native_owner_accepted',
          'demonstration_range': [2, 6], 'training_queries': 4,
          'query_visibility': 'sequential_without_total_count_hint'}


def two_contract():
    c = contract()
    c['assignment_id'] = 'review-test'
    c['repair_targets'] = c['repair_targets'][:2]
    c['work_policy'] = copy.deepcopy(POLICY)
    return c


def reports():
    c = two_contract()
    return c, {'completion_state': 'in_progress', 'repair_targets': [
        {'task_id': t['task_id'], 'outcome': 'blocked', 'summary': 'Work remains',
         'changed_components': [], 'evidence_paths': [], 'remaining_failures': [],
         'parametric_work': {'status': 'blocked', 'summary': 'Needs native build',
                             'prototype_path': None}} for t in c['repair_targets']]}


def test_draw_two_eligible_targets_and_no_peer_work(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=2, work_policy=POLICY,
                     supplementary_tickets=True)
    m = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    assert m['work_policy'] == POLICY
    assert 'supplementary_ticket_policy' not in m
    eligible = set(m['main_draw_policy']['ids'])
    assert set(m['repair_target_policy']['ids']) == eligible
    for seed in range(24):
        selected = repair_selection_for_seed(m, seed.to_bytes(32, 'big'))
        assert len(selected) == 2
        assert len({r['task_id'] for r in selected}) == 2
        assert {r['task_id'] for r in selected} <= eligible
    c = draw_main(packet, bytes(32))
    assert parametric_target_ids(c) == [r['task_id'] for r in c['repair_targets']]
    r = json.loads((packet/'RESULTS.json').read_text())
    assert len(r['repair_targets']) == 2
    assert all(t['parametric_work']['status'] == 'blocked' for t in r['repair_targets'])
    validate_target_outcomes(c, r)
    duties = (packet/'DUTIES.md').read_text()
    for phrase in ['Two accepted', 'self-review', 'four', '2–6', '30x30', 'both']:
        assert phrase in duties
    assert 'Optional help comes last' not in duties
    assert not (packet/'AUDIT_ASSIGNMENT.json').exists()
    assert draw_main(packet, bytes([7])*32) == c


def test_wide_pool_includes_unapproved_bases_and_preserves_issued_draws(library, tmp_path):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    packet = _packet(library, tmp_path, repair_target_count=2, work_policy=POLICY)
    m = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    assert m['main_draw_policy']['schema'] == 'arcpuzzles-main-draw-policy-v5'
    assert m['main_draw_policy']['base_approval_ratio'] == {'unapproved': 4, 'approved': 1}
    assert set(m['main_draw_policy']['ids']) == set(m['main_ids'])
    assert any(not m['generators'][tid]['approved'] for tid in m['main_draw_policy']['ids'])
    selected = [repair_selection_for_seed(m, i.to_bytes(32, 'big')) for i in range(1000)]
    assert {r['task_id'] for rows in selected for r in rows} == set(m['main_ids'])
    # Primary draw has both groups available; second draw gracefully falls back
    # after the fixture's only unapproved target was already selected.
    unapproved = sum(not m['generators'][rows[0]['task_id']]['approved'] for rows in selected)
    assert 750 <= unapproved <= 850
    c = draw_main(packet, bytes(32))
    assert c['base_review_policy'] == m['base_review_policy']
    assert 'unapproved' in (packet/'DUTIES.md').read_text()
    old = copy.deepcopy(m)
    old['main_draw_policy'].update(schema='arcpuzzles-main-draw-policy-v3',
        eligibility_reason='canonical_approved_and_parametric_not_accepted', distribution='uniform')
    with pytest.raises(ValueError, match='eligible'):
        main_selection_for_seed(old, bytes(32))


def test_fast_wide_pool_excludes_already_parametric_but_not_unapproved(library, tmp_path):
    (library/'REVIEW').mkdir(exist_ok=True)
    (library/'REVIEW/parametric-families-current.json').write_text(json.dumps(
        {'families': [{'task_id': 'aaaa00000001'}]}))
    # Fast publishing requires a runtime in production. This fixture exercises
    # the same eligibility helper without fabricating the pinned runtime.
    from arcpuzzles.review_base_preflight import eligible_ids
    rows = {r['id']: r for r in __import__('arcpuzzles').Catalog(library).query()}
    assert eligible_ids(rows, {'aaaa00000001'}, include_unapproved=True) == ['aaaa00000002', 'aaaa00000003']
    assert eligible_ids(rows, {'aaaa00000001'}, include_unapproved=False) == ['aaaa00000002']


def test_issued_v5_with_legacy_focus_label_still_replays(library, tmp_path):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    packet = _packet(library, tmp_path, repair_target_count=2, work_policy=POLICY)
    m = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    before = [main_selection_for_seed(m, i.to_bytes(32, 'big')) for i in range(10)]
    # An early issued v5 packet retained this older annotation label. It never
    # altered the independent inspiration draw or the 4:1 target selection.
    m['authoring_focus_policy']['target_selection'] = 'unchanged_uniform_main'
    assert [main_selection_for_seed(m, i.to_bytes(32, 'big')) for i in range(10)] == before


def test_both_targets_need_parametric_records():
    c, r = reports()
    assert len(validate_target_outcomes(c, r)) == 2
    for slot in range(2):
        bad = copy.deepcopy(r)
        bad['repair_targets'][slot].pop('parametric_work')
        with pytest.raises(ValueError, match='parametric'):
            validate_target_outcomes(c, bad)


def test_complete_requires_both_ready_not_one():
    c, r = reports()
    r['completion_state'] = 'complete'
    with pytest.raises(ValueError, match='ready'):
        validate_target_outcomes(c, r)


def test_legacy_contract_cannot_silently_drop_third_target():
    c, r = reports()
    c.pop('work_policy')
    with pytest.raises(ValueError, match='three'):
        validate_target_outcomes(c, r)


def test_both_native_admissions_run_and_partial_success_is_incomplete(monkeypatch, tmp_path):
    from arcpuzzles import review_parametric_admission as admission
    c, r = reports()
    outcomes = {t['task_id']: t for t in r['repair_targets']}
    seen = []
    def native(catalog, scoped_contract, report, archive, *, withheld_paths=()):
        tid = scoped_contract['task_id']
        seen.append((tid, scoped_contract['generator'], list(withheld_paths)))
        ok = tid == c['task_id']
        return {'task_id': tid, 'status': 'accepted' if ok else 'blocked',
                'objective_met': ok, 'training_admitted': False}
    monkeypatch.setattr(admission, 'admit_main', native)
    second = c['repair_targets'][1]['task_id']
    result = admission.admit_assignment(None, c, outcomes, tmp_path/'return.zip',
                                        withheld_paths={second: ['blocked/path']})
    assert [s[0] for s in seen] == [t['task_id'] for t in c['repair_targets']]
    assert seen[1][1] == c['repair_targets'][1]['generator']
    assert seen[1][2] == ['blocked/path']
    assert result['objective_met'] is False
    assert len(result['targets']) == 2
    assert result['targets'][0]['objective_met'] is True
    assert result['targets'][1]['objective_met'] is False
    assert result['training_admitted'] is False


def test_two_acceptances_required_for_success(monkeypatch, tmp_path):
    from arcpuzzles import review_parametric_admission as admission
    c, r = reports()
    monkeypatch.setattr(admission, 'admit_main', lambda cat, scoped, row, archive, **kw:
                        {'task_id': scoped['task_id'], 'status': 'accepted',
                         'objective_met': True, 'training_admitted': False})
    result = admission.admit_assignment(None, c, {t['task_id']: t for t in r['repair_targets']},
                                        tmp_path/'return.zip')
    assert result['status'] == 'accepted'
    assert result['objective_met'] is True
    assert len(result['targets']) == 2


def test_cli_preserves_explicit_two_builds():
    from arcpuzzles.cli import parser
    args = parser().parse_args(['review', 'pack-full', '--repair-targets', '2', '--out', 'var/send.zip'])
    assert args.repair_targets == 2


def test_two_target_delta_collect_and_integration_preserve_both_blockers(library, tmp_path):
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    packet = _packet(library, tmp_path, repair_target_count=2, work_policy=POLICY)
    c = draw_main(packet, bytes(32))
    result = json.loads((packet/'RESULTS.json').read_text())
    for row in result['repair_targets']:
        home = packet/f"repo/generators/{row['task_id']}/workspace/parametric"
        home.mkdir(parents=True, exist_ok=True)
        (home/'candidate.py').write_text('# unfinished native fixture\n')
        row.update(outcome='prototype', summary='Partial authoring retained',
                   changed_components=['tests_notes'])
    (packet/'RESULTS.json').write_text(json.dumps(result))
    for name in ['REVIEW.md', 'FEEDBACK_TO_CODEX.md']:
        (packet/name).write_text('Partial authoring; native builds not ready.\n')
    built = build_full_return(packet, tmp_path/'review_response_two.zip')
    assert built['intake_summary']['parametric_admission']['required_count'] == 2
    collected = collect_full_returns(library/'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == built['zip_sha256'])
    integrated = integrate_full_candidate(Catalog(library), library/'REVIEW', c['assignment_id'],
                                          receipt['version'], {'tests_notes'}, reviewer_reported=True)
    assert integrated['objective_met'] is False
    admissions = integrated['parametric_admissions']
    assert [r['task_id'] for r in admissions] == [t['task_id'] for t in c['repair_targets']]
    assert all(r['status'] == 'blocked' and 'not ready' in r['blocker'] for r in admissions)
    for row in c['repair_targets']:
        assert (library/f"generators/{row['task_id']}/workspace/parametric/candidate.py").is_file()
        assert (library/f"generators/{row['task_id']}/evidence/parametric-admission-current.json").is_file()


def test_wrong_count_and_foreign_second_ready_paths_are_rejected():
    c, result = reports()
    result['repair_targets'].append(copy.deepcopy(result['repair_targets'][0]))
    with pytest.raises(ValueError, match='exactly 2'):
        validate_target_outcomes(c, result)
    c, result = reports()
    second = result['repair_targets'][1]
    second['parametric_work'] = {'status': 'ready', 'summary': 'Forged cross-target ready',
                                'prototype_path': f"repo/generators/{c['task_id']}/workspace/parametric/adapter.py"}
    second['evidence_paths'] = ['checks/foreign/qualification.json']
    with pytest.raises(ValueError, match='task-local'):
        validate_target_outcomes(c, result)
