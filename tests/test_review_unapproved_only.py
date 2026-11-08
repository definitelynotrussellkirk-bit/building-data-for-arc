import json

import pytest

from arcpuzzles.review_full_draw import repair_selection_for_seed
from test_review_full_draw import _packet
from test_review_two_parametric import POLICY


def owner_scope(library, *, two_unapproved=True):
    review = library / 'REVIEW'
    review.mkdir(exist_ok=True)
    (review / 'full-packet-current.json').write_text(json.dumps({
        'default_work_policy': POLICY,
        'default_base_target_scope': 'unapproved_only',
    }))
    if two_unapproved:
        path = library / 'catalog/puzzles.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[1]['train_safety'] = 'unverified'
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def test_new_packet_never_assigns_approved_base(library, tmp_path):
    owner_scope(library)
    packet = _packet(library, tmp_path, repair_target_count=2)
    manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_text())
    for seed in range(100):
        draws = repair_selection_for_seed(manifest, seed.to_bytes(32, 'big'))
        assert {row['task_id'] for row in draws} == {'aaaa00000002', 'aaaa00000003'}


def test_short_unapproved_pool_does_not_fall_back_to_approved(library, tmp_path):
    owner_scope(library, two_unapproved=False)
    with pytest.raises(ValueError, match='eligible|Not enough generators'):
        _packet(library, tmp_path, repair_target_count=2)


def test_rotation_uses_budget_for_unapproved_roots(library, tmp_path):
    owner_scope(library)
    packet = _packet(library, tmp_path, repair_target_count=2, selection_size=2,
                     focus_ids=['aaaa00000001'])
    manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_text())
    assert set(manifest['selection']['selected_ids']) == {'aaaa00000002', 'aaaa00000003'}


def test_approved_runtime_dependency_is_not_a_draw_target(library, tmp_path):
    owner_scope(library)
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]['runtime_dependencies'] = ['aaaa00000001']
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    packet = _packet(library, tmp_path, repair_target_count=2, selection_size=3)
    manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_text())
    assert 'aaaa00000001' in manifest['selection']['dependency_ids']
    assert 'aaaa00000001' not in manifest['main_draw_policy']['ids']
