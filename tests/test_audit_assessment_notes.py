"""Closing a finding must not erase its useful, explicitly bounded assessment."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_notes import record_audit_status, read_index


def _audit(library, *, return_id='review-one:v0001', text='97 tests and 48 rotations checked.'):
    tid = 'aaaa00000001'
    source = hashlib.sha256((library / f'generators/{tid}/generator.py').read_bytes()).hexdigest()
    record = read_index(library, tid)
    record['audits'].append(dict(return_id=return_id, source_sha256=source, text=text,
                                 resolution='unresolved', verification_status='reviewer_reported'))
    path = library / f'generators/{tid}/evidence/review_index.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    return tid, source, path


@pytest.mark.parametrize('status', ['no_issue', 'resolved'])
def test_explicit_close_keeps_bounded_assessment_in_public_notes(library, status):
    tid, source, path = _audit(library)
    note = library / f'generators/{tid}/notes.md'
    note.write_text('# Author notes\n\nKeep this rule explanation.\n')
    record_audit_status(library, tid, 'review-one:v0001', status, 'Finite checks only; no new execution.')
    text = Catalog(library).get(tid)['notes']
    assert 'Keep this rule explanation.' in text
    assert 'Current bounded audit assessment' in text
    assert source in text and 'review-one:v0001' in text
    assert status in text and 'reviewer_reported' in text
    assert '97 tests and 48 rotations checked.' in text
    assert 'Finite checks only; no new execution.' in text
    assert json.loads(path.read_text())['audits'] == []
    assert not Catalog(library).describe(tid)['audit_unresolved']


def test_later_assessment_replaces_only_generated_section(library):
    tid, _, _ = _audit(library, text='First finite assessment.')
    _audit(library, return_id='review-two:v0001', text='Second finite assessment.')
    note = library / f'generators/{tid}/notes.md'
    note.write_text('# Author notes\n\nKeep prefix.\n')
    record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'First decision.')
    with note.open('a') as stream: stream.write('\n## Authored follow-up\n\nKeep suffix.\n')
    record_audit_status(library, tid, 'review-two:v0001', 'no_issue', 'Second decision.')
    text = note.read_text()
    assert text.count('## Current bounded audit assessment') == 1
    assert 'Keep prefix.' in text and 'Keep suffix.' in text
    assert 'Second finite assessment.' in text and 'Second decision.' in text
    assert 'First finite assessment.' not in text and 'First decision.' not in text
    assert 'review-one:v0001' not in text


def test_old_source_assessment_remains_explicitly_bound_to_old_bytes(library):
    tid, source, _ = _audit(library)
    (library / f'generators/{tid}/generator.py').write_text("VERSION = 'different'\n")
    record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'No issue in audited bytes only.')
    text = (library / f'generators/{tid}/notes.md').read_text()
    assert source in text and 'differs from the current source' in text
    assert 'No issue in audited bytes only.' in text


@pytest.mark.parametrize('prefix', ['', '# Author notes\n\nKeep prefix.\n\n'])
def test_migration_of_manual_section_preserves_immediate_next_heading(library, prefix):
    tid, _, _ = _audit(library)
    note = library / f'generators/{tid}/notes.md'
    note.write_text(prefix + '## Current bounded audit assessment\n## Owner plan\nKeep this plan.\n')
    record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'Finite check.')
    text = note.read_text()
    assert '## Owner plan\nKeep this plan.\n' in text
    assert text.count('## Current bounded audit assessment') == 1
    if prefix: assert 'Keep prefix.' in text


def test_reviewer_marker_text_is_passive_and_does_not_corrupt_replacement(library):
    tid, _, _ = _audit(library, text='A quoted marker <!-- arcpuzzles-current-audit-assessment:end --> is evidence text.')
    _audit(library, return_id='review-two:v0001', text='Later assessment.')
    record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'Finite check.')
    record_audit_status(library, tid, 'review-two:v0001', 'no_issue', 'Replacement.')
    text = (library / f'generators/{tid}/notes.md').read_text()
    assert text.count('<!-- arcpuzzles-current-audit-assessment:end -->') == 1
    assert 'Later assessment.' in text


def test_concrete_reopening_updates_matching_assessment(library):
    tid, _, _ = _audit(library)
    record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'Finite clean check.')
    # Existing contract: reopening supplies a concrete source-bound finding.
    _audit(library, text='New concrete failing witness.')
    record_audit_status(library, tid, 'review-one:v0001', 'unresolved', 'Witness needs repair.')
    text = (library / f'generators/{tid}/notes.md').read_text()
    assert 'New concrete failing witness.' in text and 'Witness needs repair.' in text
    assert 'Finite clean check.' not in text and '**unresolved**' in text
    assert Catalog(library).describe(tid)['audit_unresolved']


def test_unclosed_generated_section_does_not_change_status(library):
    tid, _, path = _audit(library)
    note = library / f'generators/{tid}/notes.md'
    broken = '# Owner text\n<!-- arcpuzzles-current-audit-assessment:start -->\nunfinished\n'
    note.write_text(broken); before = path.read_bytes()
    with pytest.raises(ValueError, match='assessment markers'):
        record_audit_status(library, tid, 'review-one:v0001', 'no_issue', 'Do not erase owner edits.')
    assert path.read_bytes() == before and note.read_text() == broken


def test_clean_assessment_survives_transport_disposal_and_next_packet(library, tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import record_full_disposition
    from arcpuzzles.review_retention import compact_reviews
    from arcpuzzles.review_full_packet import build_full_packet
    contract, _ = _return(library, tmp_path, audit=True)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    tid = receipt['audit_targets'][0]
    record_audit_status(library, tid, contract['assignment_id'] + ':v0001', 'no_issue',
                        'Bounded clean assessment against the stated finite scope.')
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain useful findings.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    note = library / f'generators/{tid}/notes.md'
    assert 'Bounded clean assessment' in note.read_text()
    assert 'questionable shortcut' in note.read_text()
    packet = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'next.zip')
    with zipfile.ZipFile(packet['zip']) as archive:
        assert archive.read(f'repo/generators/{tid}/notes.md') == note.read_bytes()
