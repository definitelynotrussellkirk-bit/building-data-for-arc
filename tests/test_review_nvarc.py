import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles import review_nvarc as nv
from arcpuzzles.review_tickets import build_ticket_policy, supplementary_contract
from test_review_tickets import _manifest


def _archive(tmp_path, monkeypatch):
    path = tmp_path / 'sample.zip'
    files = []
    with zipfile.ZipFile(path, 'w') as z:
        for n in range(100):
            name = f'nvarc_training/{n:03d}.json'
            raw = json.dumps([{'input': [[i % 10]], 'output': [[(i + 1) % 10]]}
                              for i in range(13 + n % 18)]).encode()
            z.writestr('puzzles/' + name, raw)
            files.append({'file': name, 'sha256': hashlib.sha256(raw).hexdigest(),
                          'subset': 'nvarc_training', 'seed_tasks': [str(n)], 'pairs': 13 + n % 18})
        z.writestr('MANIFEST.json', json.dumps({'files': files, 'sample_seed': 17}))
    monkeypatch.setattr(nv, 'ARCHIVE_SHA256', hashlib.sha256(path.read_bytes()).hexdigest())
    return path


def _packet(tmp_path, monkeypatch):
    from arcpuzzles.review_full_packet import canonical_json
    archive = _archive(tmp_path, monkeypatch)
    m, sources = _manifest(tmp_path)
    sources[nv.ARCHIVE_PATH] = archive
    m['files'][nv.ARCHIVE_PATH] = nv.ARCHIVE_SHA256
    m['supplementary_ticket_policy'] = build_ticket_policy(m, sources)
    main = {'assignment_id': 'review-test', 'seed': '1' * 64, 'task_id': 't0'}
    packet_id = hashlib.sha256(canonical_json(m)).hexdigest()
    contracts = (supplementary_contract(m, packet_id, main, i.to_bytes(32, 'big')) for i in range(1000))
    audit = next(c for c in contracts if any(t['type'] == nv.TYPE for t in c['tickets']))
    target = tmp_path / nv.ARCHIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read_bytes())
    (tmp_path / 'PACKET-MANIFEST.json').write_bytes(canonical_json(m))
    (tmp_path / 'ASSIGNMENT.json').write_text(json.dumps(main))
    (tmp_path / 'AUDIT_ASSIGNMENT.json').write_text(json.dumps(audit))
    return m, audit, next(t for t in audit['tickets'] if t['type'] == nv.TYPE)


def test_hash_pinned_pool_and_legacy_contract_unchanged(tmp_path, monkeypatch):
    m, sources = _manifest(tmp_path)
    old = build_ticket_policy(m, sources)
    old_contract = supplementary_contract({**m, 'supplementary_ticket_policy': old}, 'a'*64,
                                         {'assignment_id': 'r'}, bytes(32))
    archive = _archive(tmp_path, monkeypatch)
    sources[nv.ARCHIVE_PATH] = archive;m['files'][nv.ARCHIVE_PATH] = nv.ARCHIVE_SHA256
    new = build_ticket_policy(m, sources)
    assert old['schema'].endswith('v1') and new['schema'].endswith('v3')
    assert new['weights'][nv.TYPE] == 1 and sum(old['weights'].values()) == 100
    assert len(new['candidates'][nv.TYPE]) == 100
    assert supplementary_contract({**m, 'supplementary_ticket_policy': old}, 'a'*64,
                                 {'assignment_id': 'r'}, bytes(32)) == old_contract
    archive.write_bytes(b'changed')
    with pytest.raises(ValueError, match='archive hash'):
        build_ticket_policy(m, sources)


def test_frozen_five_weight_policy_keeps_exact_legacy_contract(tmp_path, monkeypatch):
    from copy import deepcopy
    from arcpuzzles.review_tickets import TICKET_POLICY
    m, sources = _manifest(tmp_path); archive = _archive(tmp_path, monkeypatch)
    sources[nv.ARCHIVE_PATH] = archive; m['files'][nv.ARCHIVE_PATH] = nv.ARCHIVE_SHA256
    legacy = deepcopy(build_ticket_policy(m, sources))
    legacy.update(schema='arcpuzzles-supplementary-ticket-policy-v2',
                  weight_basis=TICKET_POLICY['weight_basis'])
    legacy['weights'][nv.TYPE] = 5
    m['supplementary_ticket_policy'] = legacy
    contract = supplementary_contract(m, 'a'*64, {'assignment_id':'r','task_id':'t0'}, bytes(32))
    digest = hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest == '43585c82f8d4e99cd68c5a00ac9768a3307853f44652e00fc80896fa9cd9a28f'


def test_blind_prediction_lock_and_reveal_are_stable(tmp_path, monkeypatch):
    _, _, ticket = _packet(tmp_path, monkeypatch)
    prepared = nv.prepare(tmp_path)
    blind = json.loads((tmp_path / prepared['blind_path']).read_text())
    assert len(blind['train']) == 4 and set(blind['test'][0]) == {'input'}
    assert 'remaining_pairs' not in blind and 'source' not in blind
    assert nv.prepare(tmp_path) == prepared
    prediction = tmp_path / 'prediction.json'
    prediction.write_text(json.dumps({'rule': 'Synthetic test rule.', 'predicted_output': [[5]]}))
    proof = nv.reveal(tmp_path, prediction)
    assert nv.reveal(tmp_path, prediction) == proof
    assert proof['predicted_ok'] is True
    prediction.write_text(json.dumps({'rule': 'Edited after reveal.', 'predicted_output': [[5]]}))
    with pytest.raises(ValueError, match='prediction changed'):
        nv.reveal(tmp_path, prediction)
    assert ticket['file'] == blind['file'] and ticket['sha256'] == blind['sha256']


@pytest.mark.parametrize('mutation', ['blind', 'archive'])
def test_mutated_blind_or_source_is_rejected_before_prediction(tmp_path, monkeypatch, mutation):
    _, _, _ = _packet(tmp_path, monkeypatch)
    prepared = nv.prepare(tmp_path)
    path = tmp_path / (prepared['blind_path'] if mutation == 'blind' else nv.ARCHIVE_PATH)
    path.write_text('{}')
    prediction = tmp_path / 'prediction.json'
    prediction.write_text(json.dumps({'rule': 'Unrevealed.', 'predicted_output': [[5]]}))
    with pytest.raises(ValueError, match='blind|archive hash'):
        nv.reveal(tmp_path, prediction)
    assert not list(tmp_path.glob('.review/nvarc/*/prediction.json'))


def test_completed_report_requires_exact_bound_proof(tmp_path, monkeypatch):
    from arcpuzzles.review_tickets import validate_ticket_reports
    _, audit, ticket = _packet(tmp_path, monkeypatch)
    nv.prepare(tmp_path)
    prediction = tmp_path / 'prediction.json'
    prediction.write_text(json.dumps({'rule': 'Synthetic test rule.', 'predicted_output': [[5]]}))
    proof = nv.reveal(tmp_path, prediction)
    reports = [{'ticket_id': t['ticket_id'], 'type': t['type'], 'status': 'unknown',
                'summary': 'Not attempted.', 'evidence_paths': [], 'elapsed_minutes': None}
               for t in audit['tickets']]
    report = next(r for r in reports if r['type'] == nv.TYPE)
    report.update(status='completed', evidence_paths=proof['evidence_paths'], nvarc_review={
        'file': ticket['file'], 'sha256': ticket['sha256'], 'verdict': 'ok',
        'rule': 'Synthetic test rule.', 'predicted_ok': True, 'bad_pairs': [],
        'minutes': 1.5, 'note': 'Synthetic fixture only.'})
    names = set(proof['evidence_paths'])
    read = lambda name: (tmp_path / name).read_bytes()
    validate_ticket_reports(audit, reports, names, read_member=read)
    report['nvarc_review']['sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='NVARC'):
        validate_ticket_reports(audit, reports, names, read_member=read)
    report['nvarc_review']['sha256'] = ticket['sha256']
    source = tmp_path / next(p for p in proof['evidence_paths'] if p.endswith('/source.json'))
    source.write_bytes(source.read_bytes() + b' ')
    with pytest.raises(ValueError, match='source hash'):
        validate_ticket_reports(audit, reports, names, read_member=read)


@pytest.mark.parametrize('bundle', [False, True])
def test_outcome_survives_return_intake_and_compaction(library, tmp_path, monkeypatch, bundle):
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_packet import build_full_packet
    from arcpuzzles.review_full_draw import draw_main, draw_audit
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import _collect_one
    from arcpuzzles.review_full_integrate import record_full_disposition
    from arcpuzzles.review_retention import compact_reviews
    from arcpuzzles.review_ticket_retention import validate_current_ticket_assessments
    archive = _archive(tmp_path, monkeypatch)
    target = library / 'var/review/ticket-data/NVARC-CHECK-001.zip'
    target.parent.mkdir(parents=True);target.write_bytes(archive.read_bytes())
    questions = library / 'REVIEW/questions';questions.mkdir(parents=True)
    (questions / 'q.json').write_text(json.dumps({'schema': 'arcpuzzles-review-question-v1',
        'id': 'q', 'version': 1, 'owner': 'ARCpuzzles', 'text': 'Optional question'}))
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'request.zip',
                              supplementary_tickets=True)
    packet = tmp_path / 'packet';packet.mkdir()
    with zipfile.ZipFile(built['zip']) as z:
        assert nv.ARCHIVE_PATH in z.namelist()
        assert sum(n.startswith('review-data/') for n in z.namelist()) == 1
        z.extractall(packet)
    main = draw_main(packet, bytes(32))
    manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_bytes())
    seed = next(i.to_bytes(32, 'big') for i in range(1000) if any(t['type'] == nv.TYPE
        for t in supplementary_contract(manifest, built['packet_id'], main, i.to_bytes(32, 'big'))['tickets']))
    audit = draw_audit(packet, seed)
    ticket = next(t for t in audit['tickets'] if t['type'] == nv.TYPE)
    nv.prepare(packet)
    prediction = packet / 'prediction.json'
    prediction.write_text(json.dumps({'rule': 'Synthetic fixture rule.', 'predicted_output': [[5]]}))
    proof = nv.reveal(packet, prediction)
    result = json.loads((packet / 'RESULTS.json').read_bytes())
    result.update(completion_state='complete', stopping_reason='Synthetic test complete.')
    for row in result['supplementary_tickets']:
        row['summary'] = 'Synthetic test observation.'
        if row['type'] == nv.TYPE:
            row.update(status='completed', evidence_paths=proof['evidence_paths'], nvarc_review={
                'file': ticket['file'], 'sha256': ticket['sha256'], 'verdict': 'ok',
                'rule': 'Synthetic fixture rule.', 'predicted_ok': True, 'bad_pairs': [],
                'minutes': 1, 'note': 'Synthetic fixture only.'})
    (packet / 'RESULTS.json').write_text(json.dumps(result))
    (packet / 'REVIEW.md').write_text('Synthetic fixture, unchanged production.\n')
    returned = build_full_return(packet, tmp_path / 'review_response_nvarc.zip', bundle_evidence=bundle)
    receipt = _collect_one(library / 'REVIEW', Path(returned['zip']))
    assert receipt['validation_status'] == 'accepted', receipt
    received = next(r for r in receipt['supplementary_tickets'] if r['ticket']['type'] == nv.TYPE)
    assert received['report']['nvarc_review']['rule'] == 'Synthetic fixture rule.'
    assert not receipt['audit_targets']
    record_full_disposition(library / 'REVIEW', main['assignment_id'], 1,
                            'decision', 'deferred', 'Retain synthetic dataset outcome.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    retained = validate_current_ticket_assessments(library)
    pointer = json.loads((library / f'REVIEW/dataset-reviews/{nv.DATASET}/current.json').read_bytes())
    assert set(pointer['assessments']) == {ticket['sha256']}
    body = json.loads((library / pointer['files'][0]['path']).read_bytes())
    assert body['report']['nvarc_review'] == received['report']['nvarc_review']
    assert body['training_admitted'] is False and body['audit_resolution_changed'] is False
    assert any(p.endswith('prediction-locked.json') for p in retained)
    consumer = library / 'var/review/nvarc-check/verdicts.jsonl'
    assert [json.loads(line) for line in consumer.read_text().splitlines()] == [received['report']['nvarc_review']]


def test_unknown_dataset_assessment_stays_pending_in_derived_consumer(tmp_path, monkeypatch):
    from arcpuzzles.review_ticket_retention import prepare_ticket_retention
    from test_review_ticket_retention import _row
    _, audit, ticket = _packet(tmp_path, monkeypatch)
    report = {'ticket_id': ticket['ticket_id'], 'type': nv.TYPE, 'status': 'unknown',
              'summary': 'Insufficient time; no verdict.', 'evidence_paths': [], 'elapsed_minutes': None}
    rows = [{'ticket': ticket, 'report': report}, _row('allocation_quality')]
    owner = tmp_path / 'owner';owner.mkdir()
    receipt = {'assignment_id': 'r', 'version': 1, 'zip_sha256': 'c' * 64, 'validation_status': 'accepted'}
    result = prepare_ticket_retention(owner, receipt, rows, set(), lambda _: None)
    consumer = owner / 'var/review/nvarc-check/verdicts.jsonl'
    assert dict(result['plans'])[consumer] == b''
