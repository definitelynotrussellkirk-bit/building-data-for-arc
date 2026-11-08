"""Advisory curriculum records survive returns without approving teaching claims."""
import hashlib
import json
from pathlib import Path
import zipfile

from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_inbox import build_full_inbox, compile_task_review_index, _receipts
from arcpuzzles.review_curriculum import retained_curriculum
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return, validate_full_return
from arcpuzzles.review_solve_tracker import build_solve_tracker
from arcpuzzles.catalog import Catalog
from test_review_full_return import _draw, _docs


def test_annotation_roundtrip_source_staleness_and_portable_feed(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    supplied = json.loads((packet / 'RESULTS.json').read_text())
    supplied['curriculum'] = {'axes': {
        'contextual_gating': {'status': 'present', 'witness': 'Pair 0 marker selects left; pair 1 selects right.',
                              'rival': 'Always-left disagrees on pair 1.', 'evidence': ['checks/witness.json']},
        'multi_rule_interaction': {'status': 'not_applicable'},
        'task_defined_symbols': {'status': 'present'}}}
    (packet / 'RESULTS.json').write_text(json.dumps(supplied))
    (packet / 'checks').mkdir(exist_ok=True)
    (packet / 'checks/witness.json').write_text('{"seed": 3}\n')
    result = build_full_return(packet, tmp_path / 'review_response_curriculum.zip')
    with zipfile.ZipFile(result['zip']) as archive:
        manifest = json.loads((packet / 'PACKET-MANIFEST.json').read_text())
        validate_full_return(archive, manifest)
        annotation = json.loads(archive.read('INTAKE.json'))['curriculum']
        assert annotation['axes']['contextual_gating']['status'] == 'present'
        assert annotation['axes']['task_defined_symbols']['status'] == 'unknown'
        assert annotation['axes']['sequential_state']['status'] == 'unknown'
        assert annotation['axes']['multi_rule_interaction']['status'] == 'not_applicable'
        assert annotation['verification_status'] == 'reviewer_reported'
        assert annotation['generator_sha256'] == hashlib.sha256(
            (packet / 'repo/generators/aaaa00000003/generator.py').read_bytes()).hexdigest()
        assert annotation['evidence_sha256']['checks/witness.json'] == hashlib.sha256(b'{"seed": 3}\n').hexdigest()
    collect_full_returns(library / 'REVIEW', tmp_path)
    index = compile_task_review_index(library / 'REVIEW', 'aaaa00000003')
    assert index['decisions'] == []
    receipt = _receipts(library / 'REVIEW')[0]
    assert retained_curriculum(receipt, library)['source_status'] == 'current'
    (library / 'generators/aaaa00000003/generator.py').write_text("VERSION = 'later'\n")
    index = compile_task_review_index(library / 'REVIEW', 'aaaa00000003')
    assert index['decisions'] == []
    assert retained_curriculum(receipt, library)['source_status'] == 'stale'
    build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')
    fresh = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'next.zip')
    with zipfile.ZipFile(fresh['zip']) as archive:
        record = json.loads(archive.read('repo/generators/aaaa00000003/evidence/review_index.json'))
        assert record['decisions'] == []  # advisory data belongs to the retained dataset
        assert b'ARC-DESIGN.md' in archive.read('WELCOME.md')
        assert 'ARC-DESIGN.md' in archive.namelist()
    feed = build_solve_tracker(library / 'REVIEW', tmp_path / 'feed')
    with zipfile.ZipFile(feed['export']) as archive:
        rows = [json.loads(line) for line in archive.read('curriculum.jsonl').splitlines()]
        assert len(rows) == 1 and rows[0]['source_status'] == 'stale'
        assert rows[0]['training_admitted'] is False
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['files']['curriculum.jsonl'] == hashlib.sha256(archive.read('curriculum.jsonl')).hexdigest()


def test_missing_annotation_keeps_legacy_return_meaning(library, tmp_path):
    packet = _draw(library, tmp_path)
    _docs(packet)
    result = build_full_return(packet, tmp_path / 'review_response_plain.zip')
    with zipfile.ZipFile(result['zip']) as archive:
        assert 'curriculum' not in json.loads(archive.read('INTAKE.json'))
        assert 'curriculum' not in json.loads(archive.read('RESULTS.json'))
    collect_full_returns(library / 'REVIEW', tmp_path)
    feed = build_solve_tracker(library / 'REVIEW', tmp_path / 'feed')
    with zipfile.ZipFile(feed['export']) as archive:
        assert archive.read('curriculum.jsonl') == b''


def test_claim_binding_is_computed_and_missing_evidence_is_unknown():
    from arcpuzzles.review_curriculum import bind_curriculum
    value = {'generator_sha256': 'forged', 'verification_status': 'verified', 'axes': {
        'sequential_state': {'status': 'present', 'witness': 'Step two follows step one.',
                             'rival': 'Parallel placement differs.', 'evidence': ['not-packaged.json']},
        'contextual_gating': {'status': 'unreviewed'}}}
    result = bind_curriculum(value, task_id='task', generator=b'actual', canonical=b'rule',
                             rule_task_id='authority', evidence={})
    assert result['generator_sha256'] == hashlib.sha256(b'actual').hexdigest()
    assert result['verification_status'] == 'reviewer_reported'
    assert result['axes']['sequential_state']['status'] == 'unknown'
    assert result['axes']['contextual_gating']['status'] == 'unknown'
    assert result['evidence_sha256'] == {} and result['warnings']


def test_rule_file_drift_stales_annotation_without_generator_change(library):
    from arcpuzzles.review_curriculum import bind_curriculum, retained_curriculum
    canonical = library / 'shared/data/canonical/puzzles.jsonl'
    generator = library / 'generators/aaaa00000003/generator.py'
    annotation = bind_curriculum({}, task_id='aaaa00000003', generator=generator.read_bytes(),
                                 canonical=canonical.read_bytes(), rule_task_id='aaaa00000003', evidence={})
    receipt = {'task_id':'aaaa00000003', 'intake_summary':{'curriculum':annotation},
               'assignment_id':'review-test', 'version':1, 'packet_id':'packet', 'zip_sha256':'return'}
    assert retained_curriculum(receipt, library)['source_status'] == 'current'
    canonical.write_bytes(canonical.read_bytes() + b'\n')
    result = retained_curriculum(receipt, library)
    assert result['source_status'] == 'stale'
    assert result['axes'] == annotation['axes']


def test_support_scope_is_explicit_and_missing_or_unknown_scope_stays_unknown():
    from arcpuzzles.review_curriculum import bind_curriculum
    value = {'axes': {
        'contextual_gating': {'status': 'present', 'witness': 'Canonical pair marker changes branch.',
                              'rival': 'Always-left fails.', 'support_scope': 'canonical_only'},
        'sequential_state': {'status': 'unknown', 'support_scope': 'production_lesson'},
        'task_defined_symbols': {'status': 'unknown', 'support_scope': 'not-a-scope'}}}
    result = bind_curriculum(value, task_id='task', generator=b'g', canonical=b'c',
                             rule_task_id='rule', evidence={})
    assert result['axes']['contextual_gating']['support_scope'] == 'canonical_only'
    assert result['axes']['sequential_state']['support_scope'] == 'production_lesson'
    assert result['axes']['multi_rule_interaction']['support_scope'] == 'unknown'
    assert result['axes']['task_defined_symbols']['support_scope'] == 'unknown'
