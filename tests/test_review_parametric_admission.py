"""A completed new round means native acceptance, never a prototype claim."""
import copy
import json

import pytest

from arcpuzzles import Catalog
from arcpuzzles.review_full_draw import draw_main, main_selection_for_seed
from arcpuzzles.review_targets import validate_target_outcomes
from test_review_full_draw import _packet
from test_review_three_targets import contract

POLICY = {'schema': 'arcpuzzles-parametric-main-admission-v1',
          'roles': ['parametric_main', 'adversarial_check', 'adversarial_check'],
          'priority': 'finish_main_then_peers_with_remaining_time',
    'peer_work': 'optional_unverified_help', 'peer_integration': 'owner_checked_only',
          'completion': 'native_owner_accepted',
          'demonstration_range': [2, 6], 'training_queries': 4,
          'query_visibility': 'sequential_without_total_count_hint'}


def test_new_packet_draws_only_approved_unaccepted_main_with_two_peers(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=3, work_policy=POLICY)
    manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_text())
    assert manifest['work_policy'] == POLICY
    eligible = manifest['main_draw_policy']['ids']
    expected = sorted(tid for tid in manifest['main_ids'] if manifest['generators'][tid]['approved'])
    assert eligible == expected
    assert manifest['main_draw_policy']['eligibility_reason'] == 'canonical_approved_and_parametric_not_accepted'
    for seed in range(12):
        tid, _ = main_selection_for_seed(manifest, seed.to_bytes(32, 'big'))
        assert tid in eligible
    c = draw_main(packet, bytes(32))
    assert len(c['repair_targets']) == 3
    assert c['task_id'] in eligible
    result = json.loads((packet / 'RESULTS.json').read_text())
    assert result['repair_targets'][0]['parametric_work']['status'] == 'blocked'
    assert all('parametric_work' not in r for r in result['repair_targets'][1:])
    validate_target_outcomes(c, result)


def reports():
    c = contract(); c['work_policy'] = POLICY
    rows = [{'task_id': r['task_id'], 'outcome': 'blocked', 'summary': 'Work remains',
             'changed_components': [], 'evidence_paths': [], 'remaining_failures': []}
            for r in c['repair_targets']]
    rows[0]['parametric_work'] = {'status': 'blocked', 'summary': 'Need native adapter', 'prototype_path': None}
    return c, {'completion_state': 'blocked', 'repair_targets': rows}


def test_blocked_retained_but_not_complete():
    c, result = reports()
    validate_target_outcomes(c, result)
    result['completion_state'] = 'complete'
    with pytest.raises(ValueError, match='native|ready'):
        validate_target_outcomes(c, result)


def test_new_policy_requires_native_deliverable_not_built_metadata():
    c, result = reports()
    row = result['repair_targets'][0]
    row['parametric_work'] = {'status': 'built', 'summary': 'Prototype claim',
                             'prototype_path': f"repo/generators/{c['task_id']}/workspace/parametric/"}
    row['evidence_paths'] = ['checks/probe.json']
    with pytest.raises(ValueError, match='ready|native'):
        validate_target_outcomes(c, result)


def test_legacy_main_and_three_policy_outcomes_keep_old_contract():
    from arcpuzzles.review_targets import MAIN_WORK_POLICY, WORK_POLICY
    for policy in (MAIN_WORK_POLICY, WORK_POLICY):
        c, result = reports(); c['work_policy'] = policy
        if policy == WORK_POLICY:
            for row in result['repair_targets'][1:]:
                row['parametric_work'] = copy.deepcopy(result['repair_targets'][0]['parametric_work'])
        result['completion_state'] = 'complete'
        validate_target_outcomes(c, result)


def test_native_bridge_runs_real_protected_qualification_acceptance_and_rejects_drift(library, tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path
    import shutil
    import zipfile
    from arcpuzzles import parametric_promotion as promotion
    from arcpuzzles.review_parametric_admission import admit_main
    from test_parametric_worker import _contract, TID
    if shutil.which('racket') is None:
        pytest.skip('Real Racket required for native admission')
    source = Path(__file__).resolve().parents[1]
    runtime = library / 'shared/runtime'
    runtime.mkdir(parents=True)
    shutil.copytree(source / 'shared/runtime/arc_repl', runtime / 'arc_repl',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (runtime / 'puzzle_generators').mkdir()
    for name in ('__init__.py', 'base.py', 'rule_wrap.py'):
        shutil.copy2(source / 'shared/runtime/puzzle_generators' / name, runtime / 'puzzle_generators' / name)
    (library / 'shared/tools').mkdir()
    shutil.copy2(source / 'shared/tools/comment_solutions.py', library / 'shared/tools/comment_solutions.py')
    identity = '(rule! (lambda (g) g))'
    path = library / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['program_solution'] = identity
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['reviewed_rule_hash'] = hashlib.sha256(identity.encode()).hexdigest()[:12]
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    native = _contract(library, default_program=identity)
    native.update(schema='arcpuzzles-parametric-adapter-v1', limits={'demos': [2, 6], 'queries': [1, 4]})
    home = library / f'generators/{TID}/workspace/parametric'
    (home / 'promotion.json').write_text(json.dumps(native))
    (home / 'evidence').mkdir()
    live = Catalog(library).describe(TID)
    (home / 'evidence/manifest.json').write_text(json.dumps({
        'task_id': TID, 'generator_sha256': live['generator_sha256'],
        'canonical_rule_hash': live['rule_hash'], 'verification_status': 'reviewer_reported',
        'files': [{'path': native['adapter'], 'sha256': hashlib.sha256((home / 'adapter.py').read_bytes()).hexdigest()}]}))
    archive_path = tmp_path / 'ready.zip'
    c = {'task_id': TID, 'assignment_id': 'review-test', 'work_policy': POLICY}
    progress = {'status': 'ready', 'summary': 'Real protected qualification',
                'promotion_path': f'repo/generators/{TID}/workspace/parametric/promotion.json',
                'inventory_path': f'repo/generators/{TID}/workspace/parametric/evidence/manifest.json',
                'qualification_path': 'checks/main/qualification.json'}
    # Exercise the actual source-bound return -> intake -> integrate -> admission path.
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    packet = _packet(library, tmp_path, repair_target_count=3, work_policy=POLICY)
    drawn = draw_main(packet, bytes(32))
    assert drawn['task_id'] == TID
    edited_home = packet / f'repo/generators/{TID}/workspace/parametric'
    with (edited_home / 'adapter.py').open('a') as stream:
        stream.write('\n# reviewer source improvement\n')
    inv_path = edited_home / 'evidence/manifest.json'
    inventory = json.loads(inv_path.read_text())
    inventory['files'][0]['sha256'] = hashlib.sha256((edited_home / 'adapter.py').read_bytes()).hexdigest()
    inv_path.write_text(json.dumps(inventory))
    qualification = promotion.qualify(Catalog(packet / 'repo'), TID, tmp_path / 'reviewer-qualification')
    # This transport fixture tests source/evidence binding, not the semantic depth of the toy rule.
    dependency = {'step_a': 'fixture A', 'intermediate': 'fixture intermediate',
                  'step_b': 'fixture B', 'why_b_depends_on_a': 'fixture causal claim, owner review required',
                  'witness_path': 'checks/main/dependency.json'}
    progress['sequential_dependency'] = dependency
    witness = dict(schema='arcpuzzles-sequential-dependency-witness-v1',
                   source_binding=qualification['source_binding'], racket={'backend': 'racket', 'protected': True},
                   **{k: v for k, v in dependency.items() if k != 'witness_path'},
                   cases=[{'input': [[1, 2, 9]], 'settings': {'side': 'normal'}, 'intermediate_value': 1,
                           'program': identity, 'output': [[1, 2, 9]], 'ablation': 'wrong_intermediate',
                           'counterfactual_program': '(rule! (flip-lr g))', 'counterfactual_output': [[9, 2, 1]]}])
    with zipfile.ZipFile(archive_path, 'w') as archive:
        archive.write(qualification['receipt'], 'checks/main/qualification.json')
        archive.write(tmp_path / 'reviewer-qualification/execution.json', 'checks/main/execution.json')
        archive.writestr('checks/main/dependency.json', json.dumps(witness))
    for name in ('REVIEW.md', 'FEEDBACK_TO_CODEX.md'):
        (packet / name).write_text('Native ready main; remaining-time peers unrun.\n')
    (packet / 'checks/main').mkdir(parents=True)
    (packet / 'checks/main/dependency.json').write_text(json.dumps(witness))
    shutil.copy2(qualification['receipt'], packet / 'checks/main/qualification.json')
    shutil.copy2(tmp_path / 'reviewer-qualification/execution.json', packet / 'checks/main/execution.json')
    reports = json.loads((packet / 'RESULTS.json').read_text())
    reports.update(completion_state='complete', stopping_reason='Native main ready for owner replay')
    main = reports['repair_targets'][0]
    main.update(outcome='prototype', changed_components=['tests_notes'], evidence_paths=['checks/main/qualification.json', 'checks/main/execution.json', 'checks/main/dependency.json'])
    main['parametric_work'] = dict(progress, prototype_path=f'repo/generators/{TID}/workspace/parametric/')
    (packet / 'RESULTS.json').write_text(json.dumps(reports))
    witness_file = packet / 'checks/main/dependency.json'
    witness_file.unlink()
    with pytest.raises(ValueError, match='unpackaged evidence'):
        build_full_return(packet, tmp_path / 'review_response_missing_witness.zip')
    witness_file.write_text(json.dumps(witness))
    qfile = packet / 'checks/main/qualification.json'
    original = qfile.read_bytes()
    forged = json.loads(original); forged['execution']['sha256'] = '0' * 64
    qfile.write_text(json.dumps(forged))
    with pytest.raises(ValueError, match='execution evidence hash differs'):
        build_full_return(packet, tmp_path / 'review_response_forged.zip')
    qfile.write_bytes(original)
    returned = build_full_return(packet, tmp_path / 'review_response_native.zip')
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    assert receipt['validation_status'] == 'accepted', receipt
    integrated = integrate_full_candidate(Catalog(library), library / 'REVIEW', drawn['assignment_id'],
                                          receipt['version'], {'tests_notes'}, reviewer_reported=True)
    assert (home / 'adapter.py').read_bytes() == (edited_home / 'adapter.py').read_bytes()
    result = integrated['parametric_admission']
    assert integrated['objective_met'] is True and integrated['completion_status'] == 'accepted'
    assert result['status'] == 'accepted', result
    assert result['sequential_dependency']['owner_execution']['evaluations'] == 2
    assert result['objective_met'] is True
    assert result['training_admitted'] is False
    assert promotion.status(Catalog(library), TID)['status'] == 'accepted'
    forged_archive = tmp_path / 'forged-witness.zip'
    false_witness = copy.deepcopy(witness)
    false_witness['cases'][0]['counterfactual_program'] = identity
    with zipfile.ZipFile(archive_path) as original_archive, zipfile.ZipFile(forged_archive, 'w') as target_archive:
        for name in original_archive.namelist():
            target_archive.writestr(name, json.dumps(false_witness).encode() if name == 'checks/main/dependency.json'
                                   else original_archive.read(name))
    denied = admit_main(Catalog(library), c, {'parametric_work': progress}, forged_archive)
    assert denied['objective_met'] is False
    assert 'executed Racket outputs differ' in denied['blocker']
    # Self-consistent protected replay must still bind to the actual adapter's setting map.
    forged_map_archive = tmp_path / 'forged-program-map.zip'
    unrelated_witness = copy.deepcopy(witness)
    reverse = '(rule! (flip-lr g))'
    unrelated_witness['cases'][0].update(program=reverse, output=[[9, 2, 1]],
        counterfactual_program=identity, counterfactual_output=[[1, 2, 9]])
    with zipfile.ZipFile(archive_path) as original_archive, zipfile.ZipFile(forged_map_archive, 'w') as target_archive:
        for name in original_archive.namelist():
            raw = original_archive.read(name)
            if name == 'checks/main/qualification.json':
                report = json.loads(raw)
                report['programs']['{"side":"normal"}'] = hashlib.sha256(reverse.encode()).hexdigest()
                raw = json.dumps(report).encode()
            elif name == 'checks/main/dependency.json':
                raw = json.dumps(unrelated_witness).encode()
            target_archive.writestr(name, raw)
    accepts = []
    original_accept = promotion.accept
    def counted_accept(*args, **kwargs):
        accepts.append(True)
        return original_accept(*args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(promotion, 'accept', counted_accept)
        denied = admit_main(Catalog(library), c, {'parametric_work': progress}, forged_map_archive)
    assert denied['objective_met'] is False
    assert 'program map differs' in denied['blocker']
    assert denied['sequential_dependency']['owner_execution']['evaluations'] == 2
    assert accepts == []
    # Real accepted sources are excluded from the next main draw, peers remain eligible.
    from arcpuzzles.review_full_packet import build_full_packet
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'next.zip', repair_target_count=3)
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
    assert manifest['work_policy'] == POLICY
    assert TID not in manifest['main_draw_policy']['ids']
    assert manifest['main_draw_policy']['excluded'][TID] == 'parametric_already_accepted'
    with (home / 'adapter.py').open('a') as handle:
        handle.write('\n# changed after qualification\n')
    manifest_path = home / 'evidence/manifest.json'
    inventory = json.loads(manifest_path.read_text())
    inventory['files'][0]['sha256'] = hashlib.sha256((home / 'adapter.py').read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(inventory))
    result = admit_main(Catalog(library), c, {'parametric_work': progress}, archive_path)
    assert result['status'] == 'blocked' and result['objective_met'] is False
    assert 'exact integrated live source binding' in result['blocker'] and result['next_action']
    assert promotion.status(Catalog(library), TID)['status'] == 'stale'


def test_integrated_blocked_main_cannot_silently_complete(library, tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    c, built = _return(library, tmp_path, repair_target_count=3, state='blocked', work_policy=POLICY)
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    row = next(r for r in collected['receipts'] if r['zip_sha256'] == built['zip_sha256'])
    result = integrate_full_candidate(Catalog(library), library / 'REVIEW', c['assignment_id'],
                                     row['version'], set(), reviewer_reported=True)
    assert result['objective_met'] is False
    assert result['completion_status'] == 'repair_needed'
    assert result['parametric_admission']['status'] == 'blocked'
    assert result['parametric_admission']['next_action']


def test_no_eligible_main_fails_packet_construction(library, tmp_path):
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        row['train_safety'] = 'unverified'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    with pytest.raises(ValueError, match='No eligible main'):
        _packet(library, tmp_path, repair_target_count=3, work_policy=POLICY)


def test_new_policy_unverified_peer_repairs_remain_proposals(library, tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    before = {p: p.read_bytes() for p in (library / 'generators').glob('*/generator.py')}
    c, built = _return(library, tmp_path, repair_target_count=3, state='blocked',
                       edit=True, work_policy=POLICY)
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    row = next(r for r in collected['receipts'] if r['zip_sha256'] == built['zip_sha256'])
    result = integrate_full_candidate(Catalog(library), library / 'REVIEW', c['assignment_id'],
                                     row['version'], {'generator'}, reviewer_reported=True)
    for peer in c['repair_targets'][1:]:
        tid = peer['task_id']; path = library / f'generators/{tid}/generator.py'
        assert path.read_bytes() == before[path]
        disposition = next(r for r in result['targets'] if r['task_id'] == tid)
        assert disposition['disposition'] == 'needs_evidence'
        assert tid not in {r['task_id'] for r in result['approval']['approved']}
    main = library / f"generators/{c['task_id']}/generator.py"
    assert main.read_bytes() != before[main]
    assert result['objective_met'] is False


def test_outer_status_separates_ready_report_from_owner_acceptance(tmp_path, monkeypatch):
    import test_review_main_role_status as old
    monkeypatch.setattr(old, 'POLICY', POLICY)
    outer = old.workspace(tmp_path, policy_at=('manifest', 'contract'))
    (outer / 'WORK/RESULTS.json').write_text(json.dumps({'repair_targets': [
        {'task_id': old.IDS[0], 'outcome': 'prototype', 'summary': 'Native qualified',
         'parametric_work': {'status': 'ready'}, 'evidence_paths': ['checks/main/qualification.json']}]}))
    output = old.status(outer, tmp_path)
    assert 'MAIN FIRST' in output
    assert output.count('Optional remaining-time peer help:') == 2
    assert 'parametric=ready' in output
    assert 'Ready is reviewer-reported; owner native qualification and acceptance are still required' in output


def test_ready_main_requires_named_sequential_dependency():
    c, result = reports()
    tid = c['task_id']; home = f'repo/generators/{tid}/workspace/parametric/'
    result['completion_state'] = 'complete'
    row = result['repair_targets'][0]
    row['evidence_paths'] = ['checks/main/qualification.json']
    row['parametric_work'] = {'status': 'ready', 'summary': 'Incomplete dependency record',
        'prototype_path': home, 'promotion_path': home + 'promotion.json',
        'inventory_path': home + 'evidence/manifest.json', 'qualification_path': 'checks/main/qualification.json'}
    with pytest.raises(ValueError, match='sequential'):
        validate_target_outcomes(c, result)
