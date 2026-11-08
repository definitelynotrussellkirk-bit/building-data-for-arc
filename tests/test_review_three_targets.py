import copy
import pytest
from arcpuzzles.review_targets import (assignment_targets, target_ids, rule_task_ids,
    target_for_path, validate_target_outcomes)


def contract():
    rows = [{'task_id': str(i)*12, 'generator': {'rule_task_id': str(i)*12}} for i in range(1, 4)]
    return {'schema': 'arcpuzzles-full-assignment-v3', 'task_id': rows[0]['task_id'],
            'generator': rows[0]['generator'], 'repair_targets': rows}


def test_target_contract_and_legacy_normalization():
    c = contract()
    assert len(assignment_targets(c)) == 3
    assert rule_task_ids(c) == target_ids(c)
    assert target_for_path('repo/generators/' + c['task_id'] + '/tests/x.py', c) == c['repair_targets'][0]
    assert target_for_path('repo/shared/foo.py', c) is None
    assert target_for_path('repo/generators/' + c['task_id'] + '/../other.py', c) is None
    old = dict(c, schema='arcpuzzles-full-assignment-v2')
    old.pop('repair_targets')
    assert target_ids(old) == [c['task_id']]
    assert validate_target_outcomes(old, {}) == []


@pytest.mark.parametrize('kind', ['duplicate', 'primary', 'count'])
def test_bad_targets_rejected(kind):
    c = contract()
    if kind == 'duplicate': c['repair_targets'][2] = c['repair_targets'][1]
    if kind == 'primary': c['repair_targets'].reverse()
    if kind == 'count': c['repair_targets'].pop()
    with pytest.raises(ValueError): assignment_targets(c)


def test_outcomes_exact_and_honest():
    c = contract()
    rows = [{'task_id': tid, 'outcome': outcome, 'summary': 'Recorded scope',
             'changed_components': [], 'evidence_paths': [], 'remaining_failures': []}
            for tid, outcome in zip(target_ids(c), ['repaired', 'prototype', 'blocked'])]
    assert validate_target_outcomes(c, {'repair_targets': rows}) == rows
    for mutation in ('missing', 'duplicate', 'summary', 'component'):
        bad = copy.deepcopy(rows)
        if mutation == 'missing': bad.pop()
        if mutation == 'duplicate': bad[2] = bad[1]
        if mutation == 'summary': bad[0]['summary'] = ' '
        if mutation == 'component': bad[0]['changed_components'] = ['shared']
        with pytest.raises(ValueError): validate_target_outcomes(c, {'repair_targets': bad})


def test_three_draw_freezes_union_and_suppresses_tickets(library, tmp_path):
    from test_review_full_draw import _packet
    from arcpuzzles.review_full_draw import draw_main, main_selection_for_seed
    import json
    packet = _packet(library, tmp_path, repair_target_count=3, supplementary_tickets=True)
    manifest = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    assert 'supplementary_ticket_policy' not in manifest
    seed = bytes(32)
    drawn = draw_main(packet, seed)
    assert drawn['task_id'] == main_selection_for_seed(manifest, seed)[0]
    assert len(set(target_ids(drawn))) == 3
    for tid in target_ids(drawn):
        path = f'repo/generators/{tid}/generator.py'
        assert path in drawn['baseline_sha256']
        assert (packet/'.review/baseline'/path).read_bytes() == (packet/path).read_bytes()
    duties = (packet/'DUTIES.md').read_text()
    assert '--battery' not in duties
    assert 'three' in duties.lower()
    assert 'repair_targets' in duties
    assert draw_main(packet, bytes([1])*32) == drawn


def test_three_draw_recovers_after_late_baseline_failure(library, tmp_path, monkeypatch):
    from test_review_full_draw import _packet
    import arcpuzzles.review_full_draw as draw
    packet = _packet(library, tmp_path, repair_target_count=3)
    original = draw._copy_draw_baseline
    counter = 0
    def fail_late(*args, **kwargs):
        nonlocal counter
        counter += 1
        if counter == 3: raise OSError('Injected interruption')
        return original(*args, **kwargs)
    monkeypatch.setattr(draw, '_copy_draw_baseline', fail_late)
    with pytest.raises(OSError): draw.draw_main(packet, bytes(32))
    import json
    pending = json.loads((packet/'.review/pending-main-draw.json').read_text())['contract']
    assert len(target_ids(pending)) == 3
    monkeypatch.setattr(draw, '_copy_draw_baseline', original)
    assert draw.draw_main(packet) == pending
    assert not (packet/'.review/pending-main-draw.json').exists()


def test_generic_ids_are_equal_assignment_targets():
    c = contract()
    c['repair_targets'][1]['task_id'] = 'generic_waypoint_route_gen2'
    assert 'generic_waypoint_route_gen2' in target_ids(c)


def test_uniform_three_repair_draw_keeps_all_500_primary_positions():
    from arcpuzzles.review_full_draw import repair_selection_for_seed
    from arcpuzzles.review_targets import POLICY_SCHEMA
    ids = sorted([f'{i:012x}' for i in range(499)] + ['generic_waypoint_route_gen2'])
    manifest = {'main_ids': ids, 'generators': {tid: {'rule_task_id': tid} for tid in ids},
                'main_draw_policy': {'schema': 'arcpuzzles-main-draw-policy-v2',
                                     'distribution': 'uniform', 'ids': ids},
                'repair_target_policy': {'schema': POLICY_SCHEMA, 'count': 3,
                                        'distribution': 'uniform_without_replacement', 'ids': ids}}
    observed = []
    for i in range(500):
        rows = repair_selection_for_seed(manifest, i.to_bytes(32, 'big'))
        assert len({r['task_id'] for r in rows}) == 3
        observed.append(rows[0]['task_id'])
    assert observed == ids


def test_blind_excludes_all_three_repairs():
    from arcpuzzles.review_full_draw import repair_selection_for_seed, blind_id_for_seed
    from arcpuzzles.review_targets import POLICY_SCHEMA
    ids = [str(i)*12 for i in range(1, 5)]
    manifest = {'main_ids': ids, 'all_ids': ids,
                'generators': {tid: {'approved': True} for tid in ids},
                'repair_target_policy': {'schema': POLICY_SCHEMA, 'count': 3,
                                        'distribution': 'uniform_without_replacement', 'ids': ids}}
    for i in range(10):
        seed = i.to_bytes(32, 'big')
        assigned = [r['task_id'] for r in repair_selection_for_seed(manifest, seed)]
        assert blind_id_for_seed(manifest, assigned[0], seed) not in assigned


def test_three_draw_preserves_explicit_postrepair_solve_duty(library, tmp_path):
    from test_review_full_draw import _packet
    from arcpuzzles.review_full_draw import draw_main
    packet = _packet(library, tmp_path, repair_target_count=3, reviewer_solve=True)
    draw_main(packet, bytes(32))
    text = (packet/'DUTIES.md').read_text()
    assert 'python3 solve_episode.py prepare' in text
    assert 'Record one row per target' in text

@pytest.mark.parametrize('claim', ['missing', 'phantom'])
def test_three_return_requires_exact_rule_change_reporting(library, tmp_path, claim):
    import json
    from test_review_full_collect import _return
    from arcpuzzles.review_full_return import build_full_return
    c, _ = _return(library, tmp_path, repair_target_count=3)
    work = tmp_path/'packet-0'
    result = json.loads((work/'RESULTS.json').read_text())
    if claim == 'missing':
        path = work/'repo/shared/data/canonical/puzzles.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        next(row for row in rows if row['task_id'] == c['generator']['rule_task_id'])['review_probe'] = 'changed'
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    else:
        result['repair_targets'][0]['outcome'] = 'repaired'
        result['repair_targets'][0]['changed_components'] = ['racket']
        (work/'RESULTS.json').write_text(json.dumps(result))
    with pytest.raises(ValueError, match='components differ'):
        build_full_return(work, tmp_path/'other.zip')


def test_three_return_rejects_alternate_patch_member(library, tmp_path):
    import json, zipfile, hashlib
    from test_review_full_collect import _return
    from arcpuzzles.review_full_return import validate_full_return
    _, built = _return(library, tmp_path, repair_target_count=3, edit=True)
    with zipfile.ZipFile(built['zip']) as z:
        payload = {n:z.read(n) for n in z.namelist() if n != 'INTAKE.json'}
    payload['patches/other.patch'] = payload.pop('patches/source.patch')
    results = json.loads(payload['RESULTS.json'])
    results['artifacts'] = [a for a in results['artifacts'] if a['path'] != 'INTAKE.json']
    next(a for a in results['artifacts'] if a['path'] == 'patches/source.patch')['path'] = 'patches/other.patch'
    payload['RESULTS.json'] = json.dumps(results).encode()
    target = tmp_path/'alternate.zip'
    with zipfile.ZipFile(target,'w') as z:
        for n,b in payload.items(): z.writestr(n,b)
    manifest = json.loads((tmp_path/'packet-0/PACKET-MANIFEST.json').read_text())
    with zipfile.ZipFile(target) as z, pytest.raises(ValueError, match='one patches/source.patch'):
        validate_full_return(z,manifest)
