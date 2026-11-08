"""Explicit apply must bind the reviewed dry-run and preserve unrelated bytes."""
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.cli import main
from arcpuzzles import authority_sync as sync

TASK = 'aaaa00000001'
PREFIX = 'shared/data/base/solutions/training/'


def _sources(library):
    mapping = {}
    for name in ['first.json', 'second.json']:
        path = library / PREFIX / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'task_id': TASK, 'racket_target': {
            'target_code': '( rule! g )', 'raw_code': '(archival unchanged)'}, 'other': 7}, indent=2) + '\n')
        mapping[(PREFIX + name)[7:]] = TASK
    (library / 'catalog/authority_files.json').write_text(json.dumps(mapping))
    report = sync.propose_selected_sync(Catalog(library), TASK)
    proposal = library.parent / 'reviewed.json'; proposal.write_text(json.dumps(report))
    return proposal, report


def _source_bytes(library):
    return {str(p.relative_to(library)): p.read_bytes()
            for base in ['catalog', 'shared', 'generators']
            for p in (library / base).rglob('*') if p.is_file()}


def _apply(library, proposal):
    return sync.apply_selected_sync(Catalog(library), TASK, proposal)


def test_apply_changes_only_reviewed_selected_fields_and_keeps_recovery_evidence(library):
    proposal, reviewed = _sources(library); before = _source_bytes(library)
    result = _apply(library, proposal)
    assert result['status'] == 'applied' and result['applied'] is True
    assert result['canonical_rule_hash'] == reviewed['canonical_rule_hash']
    after = _source_bytes(library)
    assert {n for n in before if before[n] != after[n]} == {item['path'] for item in reviewed['files']}
    receipt = json.loads((library / result['receipt']).read_text())
    assert receipt['status'] == 'applied' and receipt['task_id'] == TASK
    for item in reviewed['files']:
        name = item['path']; old = json.loads(before[name]); old['racket_target']['target_code'] = '(rule! g)'
        assert json.loads(after[name]) == old
        assert hashlib.sha256(after[name]).hexdigest() == item['new_sha256']
        assert (library / result['recovery_directory'] / 'originals' / name).read_bytes() == before[name]


@pytest.mark.parametrize('drift', ['selected', 'canonical', 'catalog', 'tampered_patch', 'tampered_hash', 'wrong_task'])
def test_stale_or_tampered_proposal_is_refused_before_source_writes(library, drift):
    proposal, report = _sources(library)
    if drift == 'selected':
        p = library / report['files'][0]['path']; p.write_bytes(p.read_bytes() + b' ')
    elif drift == 'canonical':
        p = library / 'shared/data/canonical/puzzles.jsonl'; p.write_bytes(p.read_bytes() + b'\n')
    elif drift == 'catalog':
        p = library / 'catalog/authority_files.json'; p.write_bytes(p.read_bytes() + b'\n')
    else:
        if drift == 'tampered_patch': report['patch'] += 'unreviewed edit\n'
        elif drift == 'tampered_hash': report['files'][0]['new_sha256'] = '0' * 64
        else: report['task_id'] = 'aaaa00000002'
        proposal.write_text(json.dumps(report))
    before = _source_bytes(library)
    with pytest.raises(ValueError, match='proposal|task'):
        _apply(library, proposal)
    assert _source_bytes(library) == before
    assert not (library / 'var/review/authority-sync').exists()


def test_failed_second_write_restores_first_without_changing_other_sources(library, monkeypatch):
    proposal, _ = _sources(library); before = _source_bytes(library)
    replace = sync._replace_file; calls = 0
    def fail_second(path, blob):
        nonlocal calls
        calls += 1
        if calls == 2: raise OSError('injected second write failure')
        return replace(path, blob)
    monkeypatch.setattr(sync, '_replace_file', fail_second)
    with pytest.raises(RuntimeError, match='rolled_back'):
        _apply(library, proposal)
    assert _source_bytes(library) == before
    receipts = list((library / 'var/review/authority-sync').glob('*/receipt.json'))
    assert len(receipts) == 1
    assert json.loads(receipts[0].read_text())['status'] == 'rolled_back'


def test_rollback_preserves_concurrent_change_and_identifies_recovery_needed(library, monkeypatch):
    proposal, report = _sources(library); before = _source_bytes(library)
    first = library / report['files'][0]['path']; replace = sync._replace_file; calls = 0
    def interrupted(path, blob):
        nonlocal calls
        calls += 1
        if calls == 2:
            first.write_bytes(b'concurrent external edit\n')
            raise OSError('injected competing writer')
        return replace(path, blob)
    monkeypatch.setattr(sync, '_replace_file', interrupted)
    with pytest.raises(RuntimeError, match='recovery_required'):
        _apply(library, proposal)
    assert first.read_bytes() == b'concurrent external edit\n'
    second = report['files'][1]['path']; assert (library / second).read_bytes() == before[second]
    receipt = json.loads(next((library / 'var/review/authority-sync').glob('*/receipt.json')).read_text())
    assert receipt['status'] == 'recovery_required'
    assert report['files'][0]['path'] in receipt['conflicts']


def test_cli_apply_is_explicit_and_refuses_existing_output_before_mutation(library, capsys):
    proposal, _ = _sources(library); before = _source_bytes(library)
    existing = library.parent / 'existing.json'; existing.write_text('keep')
    argv = ['--library', str(library), 'authority-sync', TASK, '--selected-only', '--apply', str(proposal)]
    assert main([*argv, '--out', str(existing)]) == 1
    assert _source_bytes(library) == before and existing.read_text() == 'keep'
    assert main(argv) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'applied' and result['applied'] is True


def test_duplicate_keys_in_reviewed_proposal_are_refused(library):
    proposal, _ = _sources(library)
    proposal.write_text(proposal.read_text().replace('"task_id":', '"task_id": "other", "task_id":', 1))
    before = _source_bytes(library)
    with pytest.raises(ValueError, match='Duplicate JSON key'):
        _apply(library, proposal)
    assert _source_bytes(library) == before


def test_prepared_receipt_does_not_claim_zero_changes_if_process_dies(library, monkeypatch):
    proposal, _ = _sources(library); replace = sync._replace_file
    def inspect_prepared(path, blob):
        receipt = json.loads(next((library / 'var/review/authority-sync').glob('*/receipt.json')).read_text())
        assert receipt['status'] == 'prepared'
        assert receipt['applied'] is None  # A forced termination can leave partial writes.
        return replace(path, blob)
    monkeypatch.setattr(sync, '_replace_file', inspect_prepared)
    assert _apply(library, proposal)['status'] == 'applied'
