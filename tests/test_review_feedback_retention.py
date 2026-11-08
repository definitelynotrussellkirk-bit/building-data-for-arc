"""A disposition survives retirement of its temporary assignment transport."""
import json
import shutil

from arcpuzzles import review_assess, review_notes


def test_recorded_disposition_is_current_before_transport_disposal(tmp_path, monkeypatch):
    root = tmp_path / 'REVIEW'
    assignment = root / 'assignments/review-cpu-fixture'
    assignment.mkdir(parents=True)
    (assignment / 'ASSIGNMENT.json').write_text(json.dumps({'schema': 'fixture'}))
    request_id = 'review-cpu-fixture:v0001:F1'
    (root / 'suggestions.json').write_text(json.dumps({
        'schema': review_notes.REQUEST_SCHEMA,
        'items': [{'request_id': request_id, 'generator_id': 'task-fixture',
                   'status': 'proposed', 'reason': None, 'text': 'Exact dependency probe'}]}))
    monkeypatch.setattr(review_assess, 'assess', lambda *args: {
        'feedback_items': [{'id': 'F1', 'text': 'Exact dependency probe'}]})

    review_assess.record_feedback(root, 'review-cpu-fixture', 1, 'F1',
                                 'implemented', 'Exact isolated interpreter is checked.')
    shutil.rmtree(assignment)
    current = review_notes.compact_suggestions(root)['items'][0]
    assert current['request_id'] == request_id
    assert current['generator_id'] == 'task-fixture'
    assert current['status'] == 'implemented'
    assert current['reason'] == 'Exact isolated interpreter is checked.'
