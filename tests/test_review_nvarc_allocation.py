"""Fresh-file ticket allocation from current metadata; no puzzle review."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import review_nvarc as nv
from arcpuzzles.review_tickets import build_ticket_policy, supplementary_contract
from test_review_nvarc import _archive
from test_review_tickets import _manifest


def _assessment(owner, *, status='completed', digest='a' * 64, file='nvarc_training/a.json'):
    ticket = {'ticket_id': 'ticket-test', 'type': nv.TYPE, 'dataset_id': nv.DATASET,
              'file': file, 'sha256': digest, 'pairs': 30,
              'archive': {'path': nv.ARCHIVE_PATH, 'sha256': nv.ARCHIVE_SHA256}}
    base = 'checks/tickets/ticket-test/nvarc/'
    names = [base + name for name in ['blind.json', 'prediction-locked.json',
             'prediction-lock.json', 'source.json', 'reveal.json']]
    report = {'ticket_id': 'ticket-test', 'type': nv.TYPE, 'status': status,
              'evidence_paths': names if status == 'completed' else []}
    if status == 'completed':
        report['nvarc_review'] = {'file': file, 'sha256': digest, 'verdict': 'ambiguous',
            'rule': 'Synthetic metadata only.', 'predicted_ok': True, 'bad_pairs': [],
            'minutes': 1, 'note': 'Does not qualify labels or resolve any hold.'}
    # Deliberately absent proof payloads: allocation inspects metadata, not labels.
    body = {'schema': 'arcpuzzles-supplementary-assessment-v1', 'ticket': ticket,
            'report': report, 'verification_status': 'reviewer_reported',
            'files': [{'source_member': name} for name in names]}
    p = owner / f'REVIEW/dataset-reviews/{nv.DATASET}/assessments/{digest}/manifest.json'
    p.parent.mkdir(parents=True, exist_ok=True);raw = json.dumps(body).encode();p.write_bytes(raw)
    link = {'path': p.relative_to(owner).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return p, link


def _pointer(owner, links):
    p = owner / f'REVIEW/dataset-reviews/{nv.DATASET}/current.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({'schema': 'arcpuzzles-current-dataset-reviews-v1',
        'dataset_id': nv.DATASET, 'assessments': links, 'files': [links[k] for k in sorted(links)]}))
    return p


def test_only_completed_metadata_consumes_fresh_coverage_and_holds_remain_untouched(tmp_path):
    links = {}
    for n, status in enumerate(['completed', 'blocked', 'unknown']):
        _, links[str(n) * 64] = _assessment(tmp_path, status=status, digest=str(n) * 64,
                                          file=f'nvarc_training/{n}.json')
    _pointer(tmp_path, links)
    hold = tmp_path / f'REVIEW/dataset-reviews/{nv.DATASET}/rubric-adjudication-current.json'
    hold.write_bytes(b'Owner hold deliberately not parsed by allocation.');before = hold.read_bytes()
    assert nv.completed_review_sources(tmp_path) == {'0' * 64: 'nvarc_training/0.json'}
    assert hold.read_bytes() == before


def test_missing_review_pointer_leaves_all_files_fresh(tmp_path):
    assert nv.completed_review_sources(tmp_path) == {}


@pytest.mark.parametrize('defect', ['hash', 'escape', 'dataset', 'identity', 'status', 'proof_names', 'symlink'])
def test_changed_or_unbound_metadata_cannot_silently_change_coverage(tmp_path, defect):
    p, link = _assessment(tmp_path);body = json.loads(p.read_text())
    if defect == 'escape':link['path'] = '../outside.json'
    elif defect == 'symlink':
        other = tmp_path / 'copy.json';other.write_bytes(p.read_bytes());p.unlink();p.symlink_to(other)
    else:
        if defect == 'hash':body['extra'] = 'changed bytes'
        if defect == 'dataset':body['ticket']['dataset_id'] = 'different'
        if defect == 'identity':body['ticket']['sha256'] = 'b' * 64
        if defect == 'status':body['report']['status'] = 'finding'
        if defect == 'proof_names':body['files'] = []
        p.write_text(json.dumps(body))
        if defect != 'hash':link.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
    _pointer(tmp_path, {'a' * 64: link})
    with pytest.raises(ValueError):nv.completed_review_sources(tmp_path)


def _pool(tmp_path, monkeypatch):
    archive = _archive(tmp_path, monkeypatch)
    m, sources = _manifest(tmp_path)
    sources[nv.ARCHIVE_PATH] = archive;m['files'][nv.ARCHIVE_PATH] = nv.ARCHIVE_SHA256
    return m, sources, nv.archive_candidates(archive)


def test_new_pool_skips_completed_source_and_its_byte_identical_aliases(tmp_path, monkeypatch):
    m, sources, rows = _pool(tmp_path, monkeypatch)
    old = build_ticket_policy(m, sources)
    main = {'assignment_id': 'same-main', 'task_id': 't0'}
    frozen = copy.deepcopy(old)
    before = supplementary_contract({**m, 'supplementary_ticket_policy': old}, 'a' * 64, main, bytes(32))
    new = build_ticket_policy(m, sources, nvarc_completed={rows[0]['sha256']: rows[0]['file']})
    candidates = new['candidates'][nv.TYPE]
    # This synthetic archive repeats a source every 18 files: six exact aliases.
    assert len(candidates) == 94
    assert not {'nvarc_training/000.json', 'nvarc_training/018.json', 'nvarc_training/036.json',
                'nvarc_training/054.json', 'nvarc_training/072.json', 'nvarc_training/090.json'} & {r['file'] for r in candidates}
    assert new['nvarc_coverage']['completed_source_sha256'] == [rows[0]['sha256']]
    assert new['weights'] == old['weights']
    assert old == frozen
    assert supplementary_contract({**m, 'supplementary_ticket_policy': old}, 'a' * 64, main, bytes(32)) == before
    m['supplementary_ticket_policy'] = new
    tickets = [t for i in range(120) for t in supplementary_contract(m, 'a' * 64, main,
                i.to_bytes(32, 'big'))['tickets'] if t['type'] == nv.TYPE]
    assert tickets and all(t['sha256'] != rows[0]['sha256'] for t in tickets)


def test_completed_sample_disables_nvarc_without_changing_other_ticket_weights(tmp_path, monkeypatch):
    m, sources, rows = _pool(tmp_path, monkeypatch)
    all_done = {r['sha256']: r['file'] for r in rows}
    new = build_ticket_policy(m, sources, nvarc_completed=all_done)
    assert nv.TYPE not in new['candidates']
    m['supplementary_ticket_policy'] = new
    audit = supplementary_contract(m, 'a' * 64, {'assignment_id': 'same-main'}, bytes(32))
    assert nv.TYPE not in audit['eligible_weights'] and len(audit['tickets']) == 2
    assert new['nvarc_coverage']['remaining_files'] == 0


@pytest.mark.parametrize('completed', [{'f' * 64: 'nvarc_training/000.json'},
    {'not-sha': 'nvarc_training/000.json'}, {'a' * 64: '../escape.json'}, []])
def test_filter_rejects_unbound_completed_identities(tmp_path, monkeypatch, completed):
    m, sources, _ = _pool(tmp_path, monkeypatch)
    with pytest.raises(ValueError):build_ticket_policy(m, sources, nvarc_completed=completed)


def test_native_packet_freezes_fresh_pool_without_shipping_prior_review_context(library, tmp_path, monkeypatch):
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_packet import build_full_packet
    import zipfile
    archive = _archive(tmp_path, monkeypatch)
    rows = nv.archive_candidates(archive)
    target = library / 'var/review/ticket-data/NVARC-CHECK-001.zip'
    target.parent.mkdir(parents=True);target.write_bytes(archive.read_bytes())
    _, link = _assessment(library, digest=rows[0]['sha256'], file=rows[0]['file'])
    _pointer(library, {rows[0]['sha256']: link})
    question = library / 'REVIEW/questions/q.json';question.parent.mkdir(parents=True)
    question.write_text(json.dumps({'schema': 'arcpuzzles-review-question-v1', 'id': 'q',
        'version': 1, 'owner': 'ARCpuzzles', 'text': 'Optional question'}))
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'fresh.zip',
                              supplementary_tickets=True)
    with zipfile.ZipFile(built['zip']) as z:
        m = json.loads(z.read('PACKET-MANIFEST.json'))
        policy = m['supplementary_ticket_policy']
        assert len(policy['candidates'][nv.TYPE]) == 94
        assert policy['nvarc_coverage']['completed_source_sha256'] == [rows[0]['sha256']]
        assert not any('dataset-reviews/' in name for name in z.namelist())
