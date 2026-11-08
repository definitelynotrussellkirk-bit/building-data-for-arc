"""New packets require the full parametric deliverable for every assigned home."""
import json

import pytest

from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_return import _allowed, build_full_return
from arcpuzzles.review_targets import validate_target_outcomes, validate_work_policy
from test_review_full_draw import _packet


SCHEMA = 'arcpuzzles-three-parametric-targets-v1'


def test_all_three_draws_have_equal_parametric_duties(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=3)
    contract = draw_main(packet, bytes(32))
    policy = contract['work_policy']
    assert policy['schema'] == SCHEMA
    assert policy['roles'] == ['parametric', 'parametric', 'parametric']
    assert 'effort_percent' not in policy
    assert policy['demonstration_range'] == [2, 6]
    assert policy['training_queries'] == 4
    results = json.loads((packet / 'RESULTS.json').read_text())
    assert all(row['parametric_work']['status'] == 'blocked' for row in results['repair_targets'])
    duties = (packet / 'DUTIES.md').read_text()
    for phrase in ['all three', 'adversarial', '30x30', 'one query per user turn', 'always four']:
        assert phrase in duties
    assert '70%' not in duties
    for row in contract['repair_targets']:
        assert _allowed(f"repo/generators/{row['task_id']}/workspace/parametric/adapter.py", contract)
    validate_target_outcomes(contract, results)


@pytest.mark.parametrize('index', [0, 1, 2])
def test_each_target_requires_its_parametric_outcome(library, tmp_path, index):
    packet = _packet(library, tmp_path, repair_target_count=3)
    contract = draw_main(packet, bytes(32))
    results = json.loads((packet / 'RESULTS.json').read_text())
    results['repair_targets'][index].pop('parametric_work', None)
    with pytest.raises(ValueError, match='parametric'):
        validate_target_outcomes(contract, results)


def test_second_target_cannot_claim_first_targets_prototype(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=3)
    contract = draw_main(packet, bytes(32))
    results = json.loads((packet / 'RESULTS.json').read_text())
    row = results['repair_targets'][1]
    row['evidence_paths'] = ['checks/second.json']
    row['parametric_work'] = {'status': 'built', 'summary': 'Cross-target claim',
        'prototype_path': f"repo/generators/{contract['task_id']}/workspace/parametric/adapter.py"}
    with pytest.raises(ValueError, match='task-local'):
        validate_target_outcomes(contract, results)


def test_last_completed_artifact_must_exist_in_bound_source(library, tmp_path):
    from test_review_full_collect import _return
    contract, _ = _return(library, tmp_path, repair_target_count=3)
    work = tmp_path / 'packet-0'
    results = json.loads((work / 'RESULTS.json').read_text())
    row = results['repair_targets'][2]
    evidence = work / 'checks/last.txt'
    evidence.parent.mkdir(exist_ok=True)
    evidence.write_text('Bound evidence, missing implementation')
    row['evidence_paths'] = ['checks/last.txt']
    row['parametric_work'] = {'status': 'built', 'summary': 'Missing artifact',
        'prototype_path': f"repo/generators/{row['task_id']}/workspace/parametric/missing.py"}
    (work / 'RESULTS.json').write_text(json.dumps(results))
    with pytest.raises(ValueError, match='absent from bound source'):
        build_full_return(work, tmp_path / 'missing-last.zip')


def test_issued_main_policy_still_validates_and_restricts_peers():
    from test_review_three_targets import contract
    c = contract()
    old = {'schema': 'arcpuzzles-parametric-main-two-checks-v1',
           'effort_percent': [70, 15, 15],
           'roles': ['parametric_main', 'robustness_check', 'robustness_check'],
           'demonstration_range': [2, 6], 'training_queries': 4,
           'query_visibility': 'sequential_without_total_count_hint'}
    c['work_policy'] = old
    validate_work_policy(c, {'work_policy': old})
    assert not _allowed(f"repo/generators/{c['repair_targets'][1]['task_id']}/workspace/parametric/a.py", c)


def test_outer_status_exposes_three_full_parametric_targets(tmp_path, monkeypatch):
    import test_review_main_role_status as old
    monkeypatch.setattr(old, 'POLICY', {'schema': SCHEMA,
        'roles': ['parametric', 'parametric', 'parametric']})
    outer = old.workspace(tmp_path, policy_at=('manifest', 'contract'))
    output = old.status(outer, tmp_path)
    assert output.count('Parametric target ') == 3
    assert 'each target' in output
    assert '70%' not in output
    assert 'No parametric work on the two peers' not in output


def test_outer_before_draw_explains_full_checklist(tmp_path, monkeypatch):
    import test_review_main_role_status as old
    monkeypatch.setattr(old, 'POLICY', {'schema': SCHEMA,
        'roles': ['parametric', 'parametric', 'parametric']})
    outer = old.workspace(tmp_path, policy_at=('manifest',), assigned=False)
    assert 'three full parametric targets' in old.status(outer, tmp_path)


def test_status_reports_target_progress_without_dumping_artifacts(tmp_path, monkeypatch):
    import test_review_main_role_status as old
    monkeypatch.setattr(old, 'POLICY', {'schema': SCHEMA,
        'roles': ['parametric', 'parametric', 'parametric']})
    outer = old.workspace(tmp_path, policy_at=('manifest', 'contract'))
    (outer / 'WORK/RESULTS.json').write_text(json.dumps({'repair_targets': [
        {'task_id': old.IDS[0], 'outcome': 'prototype',
         'parametric_work': {'status': 'built'}, 'summary': 'Matched Racket variants',
         'private_answer': 'DO_NOT_DUMP', 'evidence_paths': ['checks/first/result.json']},
        {'task_id': old.IDS[1], 'outcome': 'blocked',
         'parametric_work': {'status': 'blocked'}, 'summary': 'Needs a lawful sampler'}]}))
    output = old.status(outer, tmp_path)
    assert 'Reported progress:' in output
    assert f'{old.IDS[0]}: prototype; parametric=built' in output
    assert 'checks/first/result.json' in output
    assert 'Needs a lawful sampler' in output
    assert 'DO_NOT_DUMP' not in output


def test_status_survives_unfinished_result_json(tmp_path, monkeypatch):
    import test_review_main_role_status as old
    monkeypatch.setattr(old, 'POLICY', {'schema': SCHEMA,
        'roles': ['parametric', 'parametric', 'parametric']})
    outer = old.workspace(tmp_path, policy_at=('manifest', 'contract'))
    (outer / 'WORK/RESULTS.json').write_text('{')
    assert 'RESULTS.json is unreadable' in old.status(outer, tmp_path)


@pytest.mark.parametrize('extra', [{'summary': 'Legacy optional author metadata'},
    {'status': 'built', 'prototype_path': 'legacy-optional-path.py'}])
def test_legacy_without_work_policy_keeps_optional_metadata_uninterpreted(library, tmp_path, extra):
    from arcpuzzles.review_full_packet import canonical_json
    packet = _packet(library, tmp_path, repair_target_count=3)
    manifest_path = packet / 'PACKET-MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.pop('work_policy')
    manifest_path.write_bytes(canonical_json(manifest))
    draw_main(packet, bytes(32))
    for name in ('REVIEW.md', 'DECISIONS.md', 'QUESTION_ANSWER.md', 'FEEDBACK_TO_CODEX.md'):
        (packet / name).write_text(name + '\n')
    path = packet / 'RESULTS.json'
    result = json.loads(path.read_text())
    result.update(completion_state='complete', stopping_reason='Legacy scope complete')
    result['repair_targets'][1]['parametric_work'] = extra
    path.write_text(json.dumps(result))
    built = build_full_return(packet, tmp_path / 'legacy.zip')
    assert built['repair_outcomes'][1]['parametric_work'] == extra
