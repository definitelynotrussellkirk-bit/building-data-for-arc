import json
from pathlib import Path

import pytest

from arcpuzzles.review_full_integrate import _merge_rule, integrate_full_candidate, record_full_disposition
from arcpuzzles.review_retention import compact_reviews


def ledger(*rows):
    return b''.join(json.dumps(row).encode() + b'\n' for row in rows)


def test_projected_canonical_delta_preserves_other_owner_rows():
    old = {'task_id': 'selected', 'program_solution': 'old'}
    new = {**old, 'program_solution': 'new'}
    other = {'task_id': 'outside', 'program_solution': 'owner-current'}
    assert _merge_rule(ledger(old), ledger(new), ledger(other, old), 'selected') == ledger(other, new)


def test_projected_rule_rejects_same_task_drift():
    old = {'task_id': 'selected', 'program_solution': 'old'}
    with pytest.raises(ValueError, match='drift|collision'):
        _merge_rule(ledger(old), ledger({**old, 'program_solution': 'new'}),
                    ledger({**old, 'program_solution': 'another repair'}), 'selected')


def test_projected_rule_preserves_variant_order_and_duplicates():
    a = {'task_id': 'selected', 'content_hash': 'a', 'program_solution': 'old'}
    b = {**a, 'content_hash': 'b'}
    other = {'task_id': 'outside'}
    expected = ledger({**a, 'program_solution': 'new'}, other, b, b)
    assert _merge_rule(ledger(a, b, b), ledger({**a, 'program_solution': 'new'}, b, b),
                       ledger(a, other, b, b), 'selected') == expected


def test_compaction_preserves_authored_current_notes_without_decision_diary(library, tmp_path):
    from test_review_full_integrate import _make
    contract, receipt = _make(library, tmp_path, 0, generator=True, notes=True)
    integrate_full_candidate(__import__('arcpuzzles').Catalog(library), library / 'REVIEW',
                             contract['assignment_id'], receipt['version'], {'generator', 'tests_notes'})
    note = library / 'generators' / contract['task_id'] / 'notes.md'
    before = note.read_bytes()
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], receipt['version'],
                            'decision', 'accepted', 'Current source reviewed; authored notes are authoritative.')
    compact_reviews(library, apply=True)
    assert note.read_bytes() == before
    assert b'Current reviewer considerations' not in note.read_bytes()


def test_ticket_reports_and_declared_evidence_survive_archive_disposal(library, tmp_path):
    from test_review_tickets import _ticket_packet, _finish
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import _collect_one
    from arcpuzzles.review_ticket_retention import validate_current_ticket_assessments
    packet, _ = _ticket_packet(library, tmp_path)
    main, tickets = _finish(packet)
    results = json.loads((packet / 'RESULTS.json').read_text())
    evidence = packet / 'checks/ticket/probe.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"bounded": true}\n')
    results['supplementary_tickets'][0]['evidence_paths'] = ['checks/ticket/probe.json']
    (packet / 'RESULTS.json').write_text(json.dumps(results))
    (packet / 'FEEDBACK_TO_CODEX.md').unlink()
    returned = build_full_return(packet, tmp_path / 'review_response_tickets.zip')
    receipt = _collect_one(library / 'REVIEW', Path(returned['zip']))
    assert receipt['validation_status'] == 'accepted'
    record_full_disposition(library / 'REVIEW', main['assignment_id'], receipt['version'],
                            'generator', 'accepted', 'No code changes; retain bounded ticket observations without a source approval.')
    compacted = compact_reviews(library, apply=True)
    assert compacted['archive_independent_validation'] == 'passed'
    assert not Path(receipt['archive_path']).exists()
    validate_current_ticket_assessments(library)
    retained = []
    for path in library.rglob('manifest.json'):
        if 'var' in path.relative_to(library).parts:
            continue
        row = json.loads(path.read_text())
        if row.get('schema') == 'arcpuzzles-supplementary-assessment-v1':
            retained.append(row)
    assert {row['ticket']['ticket_id'] for row in retained} == {t['ticket_id'] for t in tickets['tickets']}
    assert any(item['source_member'] == 'checks/ticket/probe.json' for row in retained for item in row['files'])
    assert all(not json.loads(path.read_text()).get('audits')
               for path in library.glob('generators/*/evidence/review_index.json'))
    requests = json.loads((library / 'REVIEW/suggestions.json').read_text())['items']
    assert not any(row['request_id'].startswith(main['assignment_id']) for row in requests)


def test_optional_question_omission_preserves_existing_shortcut(library, tmp_path):
    from test_review_tickets import _ticket_packet, _finish
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import _collect_one
    packet, _ = _ticket_packet(library, tmp_path, question_id='generator-shortcuts')
    main, _ = _finish(packet)
    note = packet / 'repo/generators' / main['task_id'] / 'notes.md'
    note.write_text('Current authored decision, with no duplicate essay.\n')
    returned = build_full_return(packet, tmp_path / 'review_response_notes.zip')
    receipt = _collect_one(library / 'REVIEW', Path(returned['zip']))
    assert receipt['validation_status'] == 'accepted'
    integrate_full_candidate(Catalog(library), library / 'REVIEW', main['assignment_id'],
                             receipt['version'], {'tests_notes'}, reviewer_reported=True)
    shortcut = library / 'generators' / main['task_id'] / 'counterexamples/current-shortcut.json'
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    existing = {'schema':'arcpuzzles-current-shortcut-v1','task_id':main['task_id'],
                'generator_sha256':main['generator']['generator_sha256'],
                'text':'Existing source-bound witness must remain.', 'files':[]}
    shortcut.write_text(json.dumps(existing))
    before = shortcut.read_bytes()
    compact_reviews(library, apply=True)
    assert shortcut.read_bytes() == before
