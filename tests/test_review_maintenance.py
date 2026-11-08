import json
from pathlib import Path
import zipfile

import pytest
from arcpuzzles import review_maintenance as m


def initialize(tmp_path):
    review = tmp_path / 'REVIEW'
    evidence = tmp_path / 'outcome.json'
    evidence.write_text('{"tests":"passed"}')
    m.complete(review, str(evidence))
    return review, evidence


def returned(tmp_path, number, *, reverse=False):
    archive = tmp_path / f'{number}-{reverse}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED if reverse else zipfile.ZIP_STORED) as z:
        for name in (['b', 'a'] if reverse else ['a', 'b']):
            z.writestr(name, f'{number}-{name}')
    return dict(validation_status='accepted', archive_path=str(archive))


def test_threshold_content_dedup_and_concurrent_pass_arrivals(tmp_path):
    review, evidence = initialize(tmp_path)
    for i in range(25):
        status = m.record_accepted(review, returned(tmp_path, i))
    assert status == dict(accepted_since_pass=25, interval=25, maintenance_due=True)
    assert m.record_accepted(review, returned(tmp_path, 2, reverse=True)) == status
    path = review / m.NAME
    m.start(review)
    m.record_accepted(review, returned(tmp_path, 26))
    with pytest.raises(ValueError, match='already started'):
        m.start(review)
    with pytest.raises(ValueError, match='nonempty'):
        m.complete(review, str(tmp_path / 'failed-pass'))
    assert json.loads(path.read_text())['accepted_since_pass'] == 26
    state = m.complete(review, str(evidence))
    assert state['accepted_since_pass'] == 1
    assert not state['maintenance_due']
    assert m.record_accepted(review, returned(tmp_path, 2))['accepted_since_pass'] == 1
    with pytest.raises(ValueError, match='Run start'):
        m.complete(review, str(evidence))


def test_rejected_and_failed_write_do_not_advance(tmp_path, monkeypatch):
    review, evidence = initialize(tmp_path)
    receipt = returned(tmp_path, 1)
    before = (review / m.NAME).read_bytes()
    with pytest.raises(ValueError, match='Only accepted'):
        m.record_accepted(review, dict(receipt, validation_status='rejected'))
    original = Path.replace
    def fail(source, target):
        if Path(target).name == m.NAME:
            raise OSError('simulated full disk')
        return original(source, target)
    monkeypatch.setattr(Path, 'replace', fail)
    assert m.notify_accepted(review, receipt)['status'] == 'counter_update_failed'
    assert (review / m.NAME).read_bytes() == before
    monkeypatch.setattr(Path, 'replace', original)
    assert m.record_accepted(review, receipt)['accepted_since_pass'] == 1


def test_unarmed_counter_and_missing_completion_evidence(tmp_path):
    assert m.record_accepted(tmp_path, {})['status'] == 'not_initialized'
    with pytest.raises(ValueError, match='nonempty'):
        m.complete(tmp_path, str(tmp_path / 'absent'))


def test_changed_archive_does_not_advance(tmp_path):
    review, _ = initialize(tmp_path)
    receipt = returned(tmp_path, 3)
    receipt['zip_sha256'] = '0' * 64
    assert m.notify_accepted(review, receipt)['status'] == 'counter_update_failed'
    assert json.loads((review / m.NAME).read_text())['accepted_since_pass'] == 0


def test_status_before_initial_completion_is_nonblocking(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['maintenance', '--review-root', str(tmp_path), 'status'])
    m.main()
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'not_initialized'
    assert result['maintenance_due'] is False
    assert not (tmp_path / m.NAME).exists()
