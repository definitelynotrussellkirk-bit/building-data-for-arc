"""Issued v1 evaluation-focus policies remain reproducible and source-bound."""
import copy
import hashlib
import json
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_priority import build_parametric_priority
from arcpuzzles.review_full_collect import _reproduce
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_packet import build_full_packet, canonical_json


def official(root, *, split, original, tid=None):
    if tid:
        path = root / 'shared/data/canonical/puzzles.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        row = next(row for row in rows if row['task_id'] == tid)
        color = int(tid[-2:], 16) + 4
        row.update(train=[{'input': [[color]], 'output': [[2]]}],
                   test=[{'input': [[color + 1]], 'output': [[4]]}])
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        challenge = {'train': row['train'], 'test': [{'input': row['test'][0]['input']}]}
    else:
        challenge = {'train': [{'input': [[9, 0]], 'output': [[0, 9]]}],
                     'test': [{'input': [[0, 8]]}]}
    path = root / f'shared/data/raw/arc-agi_{split}_challenges.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.loads(path.read_text()) if path.exists() else {}
    raw[original] = challenge
    path.write_text(json.dumps(raw))


def packet(root, tmp_path):
    path = root / 'REVIEW/questions/q.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'schema': 'arcpuzzles-review-question-v1', 'id': 'q',
                                'version': 1, 'owner': 'ARCpuzzles', 'text': 'Why?'}))
    built = build_full_packet(Catalog(root), root / 'REVIEW', tmp_path / 'request.zip')
    outer = tmp_path / 'packet'
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
        archive.extractall(outer)
    # Deliberately freeze a v1 policy: new packets draw uniformly, while these
    # tests protect already-issued weighted assignments and their return replay.
    priority = manifest['parametric_priority']
    manifest['main_ids'] = sorted(set(priority['main_ids']) | {
        tid for parent in priority['evaluation_focus']['anchors'] for tid in parent['main_ids']})
    manifest['main_draw_policy'] = {'schema': 'arcpuzzles-main-draw-policy-v1',
        'normal_ids': priority['main_ids'] or manifest['main_ids'],
        'evaluation_focus': priority['evaluation_focus']}
    raw = canonical_json(manifest)
    (outer/'PACKET-MANIFEST.json').write_bytes(raw)
    legacy = tmp_path/'legacy-request.zip'
    with zipfile.ZipFile(built['zip']) as src, zipfile.ZipFile(legacy, 'w') as dest:
        for info in src.infolist():
            dest.writestr(info, raw if info.filename == 'PACKET-MANIFEST.json' else src.read(info.filename))
    built.update(zip=str(legacy), packet_id=hashlib.sha256(raw).hexdigest())
    return built, outer, manifest


def selections(manifest, count=10000):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    return [(index.to_bytes(32, 'big'),
             main_selection_for_seed(manifest, index.to_bytes(32, 'big')))
            for index in range(count)]


def test_unmapped_evaluation_tasks_still_receive_an_inspiration_assignment(library, tmp_path):
    official(library, split='training', original='0123abcd', tid='aaaa00000001')
    official(library, split='evaluation', original='89abcdef')
    # Query answers must never be consulted to establish the authoring focus.
    (library / 'shared/data/raw/arc-agi_evaluation_solutions.json').write_text('not JSON')
    built, outer, manifest = packet(library, tmp_path)
    pairs = selections(manifest)
    focused = [(seed, result) for seed, result in pairs if result[1] is not None]
    assert 900 <= len(focused) <= 1100
    assert all(result[0] == 'aaaa00000001' for _, result in pairs)
    seed, (_, expected_focus) = focused[0]
    contract = draw_main(outer, seed)
    assert contract['authoring_focus'] == expected_focus
    assert expected_focus['source_task_id'] == '89abcdef'
    assert expected_focus['mode'] == 'inspired_extension'
    assert expected_focus['relationship_verified'] is False
    assert expected_focus['training_admitted'] is False
    assert '89abcdef' in (outer / 'DUTIES.md').read_text()
    assert 'parameter' in (outer / 'DUTIES.md').read_text()
    assert draw_main(outer, bytes(32)) == contract
    with zipfile.ZipFile(built['zip']) as archive:
        _reproduce(contract, manifest, archive)
        forged = copy.deepcopy(contract)
        forged['authoring_focus']['source_task_id'] = 'deadbeef'
        with pytest.raises(ValueError, match='focus|reproduced'):
            _reproduce(forged, manifest, archive)
        del forged['authoring_focus']
        with pytest.raises(ValueError, match='focus|reproduced'):
            _reproduce(forged, manifest, archive)


def test_focus_selects_related_generator_even_when_it_is_outside_normal_tier(library, tmp_path):
    official(library, split='training', original='0123abcd', tid='aaaa00000001')
    official(library, split='evaluation', original='89abcdef', tid='aaaa00000003')
    built, outer, manifest = packet(library, tmp_path)
    normal, focused = [], []
    for seed, (tid, focus) in selections(manifest, 200):
        (focused if focus else normal).append((seed, tid, focus))
    assert normal and focused
    assert all(tid == 'aaaa00000001' for _, tid, _ in normal)
    assert all(tid == 'aaaa00000003' for _, tid, _ in focused)
    assert set(manifest['main_ids']) == {'aaaa00000001', 'aaaa00000003'}
    seed, _, _ = focused[0]
    contract = draw_main(outer, seed)
    assert contract['authoring_focus']['mode'] == 'direct_related'
    assert contract['authoring_focus']['relationship_verified'] is True
    with zipfile.ZipFile(built['zip']) as archive:
        _reproduce(contract, manifest, archive)


def test_parameterization_precedes_revisiting_completed_evaluation_prototypes(library):
    official(library, split='evaluation', original='89abcdef', tid='aaaa00000001')
    # A reviewed second descendant of the same public challenge.
    priority = build_parametric_priority(Catalog(library))
    origin = priority['related_generators']['aaaa00000001']['origins'][0]
    path = library / 'shared/data/derived/official_generator_lineage.jsonl'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'generator_id': 'aaaa00000002', 'mapping_status': 'verified',
        'source_split': 'evaluation', 'source_task_id': '89abcdef', 'relationship': 'semantic_variant',
        'source_hashes': {'challenge_sha256': origin['challenge_sha256']}}) + '\n')
    row = Catalog(library).describe('aaaa00000001')
    home = library / 'generators/aaaa00000001/workspace/parametric/evidence'
    home.mkdir(parents=True)
    program = home / 'program.rkt'
    program.write_text('(rule! g)')
    (home / 'manifest.json').write_text(json.dumps({'task_id': row['id'],
        'generator_sha256': row['generator_sha256'], 'canonical_rule_hash': row['rule_hash'],
        'verification_status': 'reviewer_reported', 'parameters': {'color': [1, 2]},
        'files': [{'path': program.relative_to(library).as_posix(),
                   'sha256': hashlib.sha256(program.read_bytes()).hexdigest()}]}))
    anchor = build_parametric_priority(Catalog(library))['evaluation_focus']['anchors'][0]
    assert anchor['main_ids'] == ['aaaa00000002']
    assert anchor['selected_tier'] == 'approved_need_parameters'


def test_all_public_evaluation_origins_can_be_selected_even_without_descendants(library, tmp_path):
    official(library, split='evaluation', original='89abcdef')
    official(library, split='evaluation', original='0123abcd')
    _, _, manifest = packet(library, tmp_path)
    focus = [focus for _, (_, focus) in selections(manifest, 2000) if focus]
    assert {item['source_task_id'] for item in focus} == {'0123abcd', '89abcdef'}
    assert all(item['mode'] == 'inspired_extension' for item in focus)


def test_legacy_packet_draw_mapping_remains_unchanged():
    from arcpuzzles.review_full_draw import main_selection_for_seed
    manifest = {'main_ids': ['a', 'b', 'c']}
    assert main_selection_for_seed(manifest, (4).to_bytes(32, 'big')) == ('b', None)


def test_no_evaluation_challenges_means_normal_priority_without_invented_origins(library, tmp_path):
    _, _, manifest = packet(library, tmp_path)
    assert all(tid == 'aaaa00000003' and focus is None
               for _, (tid, focus) in selections(manifest, 50))
