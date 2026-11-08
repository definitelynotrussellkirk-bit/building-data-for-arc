import json
from pathlib import Path

from arcpuzzles.review_notes import compact_task_state, compact_suggestions, audit_state
from arcpuzzles.review_full_inbox import build_full_inbox
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.catalog import Catalog


def test_compact_state_drops_history_keeps_open_old_source_findings(library, tmp_path):
    tid = 'aaaa00000001'
    home = library / 'generators' / tid
    legacy = {'schema': 'arcpuzzles-task-review-index-v2', 'task_id': tid,
              'decisions': [{'return_id': 'old:v0001', 'source_sha256': 'old',
                             'text': 'obsolete narrative', 'review': 'green log', 'archive_path': '/gone.zip'}],
              'audits': [{'return_id': 'old:v0001', 'source_sha256': 'old',
                          'text': 'Open exact counterexample', 'archive_path': '/gone.zip'},
                         {'return_id': 'closed:v0001', 'source_sha256': 'old', 'text': 'Closed finding'}]}
    (home / 'evidence').mkdir(exist_ok=True)
    (home / 'evidence/review_index.json').write_text(json.dumps(legacy))
    (home / 'evidence/audit_dispositions.jsonl').write_text(json.dumps(
        {'return_id': 'closed:v0001', 'source_sha256': 'old', 'status': 'resolved', 'reason': 'Fixed by focused test'})+'\n')
    current = compact_task_state(library, tid, apply=True)
    assert current['schema'] == 'arcpuzzles-task-review-current-v1'
    assert current['decisions'] == []
    assert len(current['audits']) == 1
    assert current['audits'][0]['source_sha256'] == 'old'
    assert audit_state(library, tid)['audit_unresolved']
    assert 'archive_path' not in json.dumps(current)
    assert 'obsolete narrative' not in json.dumps(current)
    assert not (home / 'evidence/audit_dispositions.jsonl').exists()
    # No historical assignments/ZIPs: inbox must retain this current task finding.
    inbox = build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')
    assert json.loads(Path(inbox['json']).read_text())['counts']['audit_groups'] == 1
    assert audit_state(library, tid)['audit_unresolved']


def test_tool_requests_are_current_rows_not_events(library):
    root = library / 'REVIEW'
    root.mkdir(exist_ok=True)
    rows = [{'event':'suggestion','event_id':'1','request_id':'r:F1','generator_id':'g',
             'text':'Useful helper','source_sha256':'old'},
            {'event':'disposition','event_id':'2','request_id':'r:F1','status':'accepted','reason':'Useful'},
            {'event':'disposition','event_id':'3','request_id':'r:F1','status':'implemented','reason':'Tool exists'}]
    (root / 'suggestions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    result = compact_suggestions(root, apply=True)
    assert len(result['items']) == 1
    assert result['items'][0]['status'] == 'implemented'
    assert 'event_id' not in json.dumps(result)
    assert not (root / 'suggestions.jsonl').exists()
    assert compact_suggestions(root)['items'] == result['items']


def test_resolved_current_audit_is_not_resurrected_by_pending_receipt(library, tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_notes import record_audit_status
    contract, _ = _return(library, tmp_path, audit=True)
    received = collect_full_returns(library / 'REVIEW', tmp_path)
    build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')
    target = received['receipts'][0]['audit_targets'][0]
    record_audit_status(library, target, contract['assignment_id'] + ':v0001',
                        'resolved', 'Focused witness now passes at the selected source.')
    build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')
    assert audit_state(library, target)['audits'] == []
    assert not (library / f'generators/{target}/evidence/audit_dispositions.jsonl').exists()


def test_replaying_feedback_does_not_overwrite_current_request_edit(library):
    from arcpuzzles.review_notes import append_suggestions
    root = library / 'REVIEW'
    events = [{'event':'suggestion','request_id':'r:F1','text':'Portable helper'},
              {'event':'disposition','request_id':'r:F1','status':'accepted','reason':'Useful'}]
    assert append_suggestions(root, events) == 1
    path = root / 'suggestions.json'
    current = json.loads(path.read_text())
    current['items'][0].update(status='implemented', reason='Measured helper test passes')
    path.write_text(json.dumps(current))
    assert append_suggestions(root, events) == 0
    assert json.loads(path.read_text())['items'][0]['status'] == 'implemented'
    assert not (root / 'suggestions.jsonl').exists()


def test_current_decision_identity_requires_exact_selected_source(library):
    import hashlib
    tid = 'aaaa00000001'
    digest = hashlib.sha256((library / f'generators/{tid}/generator.py').read_bytes()).hexdigest()
    approval = library / 'REVIEW/approvals/current.json'
    approval.parent.mkdir(parents=True)
    approval.write_text(json.dumps({'generator_sha256':digest,'return_id':'r:v0001',
                                   'verification_status':'reviewer_reported','rule_hash':'rule'}))
    catalog = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in catalog.read_text().splitlines()]
    for row in rows:
        if row['id'] == tid:
            row.update(approval_receipt='REVIEW/approvals/current.json', reviewed_generator_sha256=digest)
    catalog.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    state = compact_task_state(library, tid, apply=True)
    assert state['decisions'][0]['return_id'] == 'r:v0001'
    assert state['decisions'][0]['verification_status'] == 'reviewer_reported'
    (library / f'generators/{tid}/generator.py').write_text('unreviewed new bytes\n')
    assert compact_task_state(library, tid)['decisions'] == []
