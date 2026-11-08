"""Owner pending adjudications must not become trainer verdicts on rebuild."""
import hashlib
import json

import pytest

from arcpuzzles.review_ticket_retention import _dataset_verdict_rows
from arcpuzzles import review_nvarc as nv


def fixture_rows(tmp_path, monkeypatch):
    # Native retention tests exercise full report validation; isolate eligibility here.
    monkeypatch.setattr(nv, 'validate_report', lambda *args, **kwargs: None)
    root = tmp_path / 'owner'
    home = root / f'REVIEW/dataset-reviews/{nv.DATASET}'
    home.mkdir(parents=True)
    rows = []
    pointer = {'assessments': {}}
    for n, verdict in enumerate(('trivial', 'ok', 'ok')):
        digest = str(n + 1) * 64
        row = {'file': f'nvarc_training/{n}.json', 'sha256': digest,
               'verdict': verdict, 'rule': 'Synthetic fixture.', 'predicted_ok': True,
               'bad_pairs': [], 'minutes': 1, 'note': ''}
        body = {'ticket': {'type': nv.TYPE, 'dataset_id': nv.DATASET, 'sha256': digest},
                'report': {'status': 'completed', 'nvarc_review': row},
                'verification_status': 'reviewer_reported', 'files': []}
        path = home / f'{n}.json'
        raw = json.dumps(body).encode()
        path.write_bytes(raw)
        pointer['assessments'][digest] = {'path': str(path.relative_to(root)),
                                         'sha256': hashlib.sha256(raw).hexdigest()}
        rows.append(row)
    holds = {'schema': 'arcpuzzles-dataset-rubric-adjudication-v1',
             'file': rows[0]['file'], 'sha256': rows[0]['sha256'],
             'status': 'needs_external_adjudication',
             'additional_rule_writeup_followups': [
                 {'file': rows[1]['file'], 'sha256': rows[1]['sha256'],
                  'status': 'needs_external_rule_clarification'}]}
    path = home / 'rubric-adjudication-current.json'
    path.write_text(json.dumps(holds))
    return root, pointer, rows, path, holds


def test_pending_reviews_omitted_on_every_rebuild_without_changing_reports(tmp_path, monkeypatch):
    root, pointer, rows, path, holds = fixture_rows(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in path.parent.glob('*.json')}
    expected = [rows[2]]
    for _ in range(2):
        assert [json.loads(x) for x in _dataset_verdict_rows(root, pointer, {}).splitlines()] == expected
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_hold_binds_exact_file_and_bytes_and_release_is_explicit(tmp_path, monkeypatch):
    root, pointer, rows, path, holds = fixture_rows(tmp_path, monkeypatch)
    holds['sha256'] = 'a' * 64  # A hold on different bytes must not suppress this report.
    holds['additional_rule_writeup_followups'][0]['status'] = 'resolved'
    path.write_text(json.dumps(holds))
    assert [json.loads(x) for x in _dataset_verdict_rows(root, pointer, {}).splitlines()] == rows
    holds['sha256'] = rows[0]['sha256']
    holds['file'] = 'nvarc_training/wrong.json'
    path.write_text(json.dumps(holds))
    with pytest.raises(ValueError, match='adjudication'):
        _dataset_verdict_rows(root, pointer, {})


@pytest.mark.parametrize('field,value', [('sha256', 'broken'), ('status', 'typo'),
                                        ('schema', 'unknown')])
def test_malformed_adjudication_fails_closed(tmp_path, monkeypatch, field, value):
    root, pointer, rows, path, holds = fixture_rows(tmp_path, monkeypatch)
    holds[field] = value
    path.write_text(json.dumps(holds))
    with pytest.raises(ValueError, match='adjudication'):
        _dataset_verdict_rows(root, pointer, {})
