"""Fast delivery keeps source/hash checks; historical graph and runtime replay are deferred."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles import Catalog
from arcpuzzles import cli
from arcpuzzles import review_full_packet as packet
from test_review_full_packet import _questions


def build(library, output, **kwargs):
    return packet.build_full_packet(Catalog(library), library / 'REVIEW', output, **kwargs)


def test_fast_atomically_replaces_and_binds_all_bytes(library, tmp_path, monkeypatch):
    _questions(library)
    output = tmp_path / 'send.zip'; output.write_bytes(b'previous delivery')
    private_cache = library/'var/review/public-coverage-cache'
    private_cache.mkdir(parents=True)
    (private_cache/'owner.key').write_bytes(b'private-cache-key')
    (private_cache/'current.json').write_text('{}')
    current = library / 'REVIEW/full-packet-current.json'
    current.write_text(json.dumps({'current_generation_smoke': {'old': True},
                                  'latest_combined_packet_check': {'status': 'passed'},
                                  'build_receipt_sha256': 'stale', 'share_copy': '/stale.zip'}))
    replace = packet.os.replace
    observed = []
    def watch(source, target):
        if Path(target) == output:
            assert output.read_bytes() == b'previous delivery'
            assert zipfile.is_zipfile(source)
            observed.append(True)
        return replace(source, target)
    monkeypatch.setattr(packet.os, 'replace', watch)
    result = build(library, output, fast=True)
    assert observed == [True]
    with zipfile.ZipFile(output) as z:
        manifest = json.loads(z.read('PACKET-MANIFEST.json'))
        assert not any('public-coverage-cache' in name or name.endswith('/owner.key') for name in z.namelist())
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
    value = json.loads(current.read_text())
    assert value['zip_sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert value['share_copy'] == str(output)
    assert value['current_artifact_verified'] is False
    assert value['current_generation_smoke'] is None
    assert value['latest_combined_packet_check']['deep_validation'] == 'pending'
    assert value['build_receipt_sha256'] == hashlib.sha256(Path(result['receipt']).read_bytes()).hexdigest()
    assert 'pinned_racket_archive' not in result['release_verification']['included']


def test_fast_uses_local_pinned_racket_without_network(library, tmp_path, monkeypatch):
    _questions(library)
    local = library / 'var/review' / packet.RACKET_ARCHIVE_NAME
    local.parent.mkdir(parents=True); local.write_bytes(b'pinned fixture')
    monkeypatch.setattr(packet, 'RACKET_ARCHIVE_SHA256', hashlib.sha256(local.read_bytes()).hexdigest())
    result = build(library, tmp_path / 'fast.zip', fast=True)
    with zipfile.ZipFile(result['zip']) as z:
        assert z.read('vendor/' + packet.RACKET_ARCHIVE_NAME) == local.read_bytes()
    assert 'pinned_racket_archive' in result['release_verification']['included']
    local.write_bytes(b'corrupt fixture')
    with pytest.raises(ValueError, match='SHA-256'):
        build(library, tmp_path / 'bad.zip', fast=True)


def test_fast_defers_historical_graph_but_strict_default_still_rejects(library, tmp_path):
    _questions(library)
    folder = library / 'generators/aaaa00000001/workspace/parametric/evidence'
    folder.mkdir(parents=True)
    (folder / 'manifest.json').write_text(json.dumps({'files': [{
        'path': 'generators/aaaa00000001/workspace/parametric/evidence/missing.zip', 'sha256': '0' * 64}]}))
    result = build(library, tmp_path / 'fast.zip', fast=True)
    assert result['release_verification']['deep_validation'] == 'pending'
    with pytest.raises((ValueError, FileNotFoundError), match='evidence|inventory|dependency'):
        build(library, tmp_path / 'strict.zip')


def test_fast_owner_comparison_reuses_frozen_projection_policy_and_still_detects_drift(library, tmp_path):
    from arcpuzzles.review_packet_verify import _compare_owner
    _questions(library)
    folder = library / 'generators/aaaa00000001/workspace/parametric/evidence'
    folder.mkdir(parents=True)
    (folder / 'manifest.json').write_text(json.dumps({'files': [{
        'path': 'generators/aaaa00000001/workspace/parametric/evidence/missing.zip', 'sha256': '0' * 64}]}))
    result = build(library, tmp_path / 'fast-owner-check.zip', fast=True)
    with zipfile.ZipFile(result['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
    checked = _compare_owner(library, manifest)
    assert checked['status'] == 'passed'
    assert checked['historical_evidence_graph'] == 'deferred'
    (library / 'generators/aaaa00000001/generator.py').write_text('# actual source drift\n')
    with pytest.raises(ValueError, match='Owner source differs'):
        _compare_owner(library, manifest)


def test_owner_comparison_binds_bundled_python_wheels_and_rejects_corruption(library, tmp_path, monkeypatch):
    from arcpuzzles import review_python_wheels
    from arcpuzzles.review_packet_verify import _compare_owner
    _questions(library)
    wheel = library / 'var/review/python-wheels/example.whl'
    wheel.parent.mkdir(parents=True); wheel.write_bytes(b'wheel fixture')
    monkeypatch.setattr(review_python_wheels, 'WHEELS', {'example.whl': {
        'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(), 'bytes': wheel.stat().st_size}})
    result = build(library, tmp_path / 'with-wheels.zip', fast=True)
    with zipfile.ZipFile(result['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
    assert _compare_owner(library, manifest)['status'] == 'passed'
    wheel.write_bytes(b'corrupt wheel')
    with pytest.raises(ValueError, match='SHA/size|Owner source differs'):
        _compare_owner(library, manifest)


def test_fast_still_rejects_missing_runtime_without_replacing_delivery(library, tmp_path):
    _questions(library)
    output = tmp_path / 'send.zip'; output.write_bytes(b'previous delivery')
    path = library / 'catalog/runtime_files.json'
    rows = json.loads(path.read_text())
    rows.append({'path': 'shared/runtime/missing.py', 'target': 'missing.py'})
    path.write_text(json.dumps(rows))
    with pytest.raises(FileNotFoundError, match='runtime'):
        build(library, output, fast=True)
    assert output.read_bytes() == b'previous delivery'
    assert not (library / 'REVIEW/packet-rotation.json').exists()


def test_fast_source_drift_preserves_previous_zip_and_rotation(library, tmp_path, monkeypatch):
    _questions(library)
    output = tmp_path / 'send.zip'; output.write_bytes(b'previous delivery')
    original = packet.canonical_json
    def mutate_after_inventory(value):
        if isinstance(value, dict) and value.get('schema') == packet.SCHEMA:
            source = next((library / 'var/review/packet-projections').glob('*/generators/aaaa00000001/generator.py'))
            source.write_text('changed during build\n')
        return original(value)
    monkeypatch.setattr(packet, 'canonical_json', mutate_after_inventory)
    with pytest.raises(RuntimeError, match='Source changed'):
        build(library, output, fast=True)
    assert output.read_bytes() == b'previous delivery'
    assert not (library / 'REVIEW/packet-rotation.json').exists()
    assert not list(tmp_path.glob('.packet-*.zip'))


def test_cli_fast_is_opt_in_and_strict_output_conflicts_remain(library, tmp_path):
    _questions(library)
    assert cli.parser().parse_args(['review', 'pack-full', '--out', 'x.zip']).fast is False
    assert cli.parser().parse_args(['review', 'pack-full', '--out', 'x.zip', '--fast']).fast is True
    output = tmp_path / 'send.zip'; output.write_bytes(b'previous delivery')
    with pytest.raises(FileExistsError):
        build(library, output)
    assert output.read_bytes() == b'previous delivery'


def test_routine_fast_requires_offline_runtime_before_projection(library, tmp_path, monkeypatch):
    _questions(library)
    def unexpected(*args, **kwargs):
        pytest.fail('Missing required runtime must fail before source projection')
    monkeypatch.setattr(packet, '_source_files', unexpected)
    with pytest.raises(ValueError, match='Racket.*--racket-archive'):
        build(library, tmp_path / 'send.zip', fast=True, repair_target_count=3)
    assert not (tmp_path / 'send.zip').exists()


def test_fast_eligibility_snapshot_keeps_approval_boundary(library, tmp_path, monkeypatch):
    from arcpuzzles import parametric_promotion
    _questions(library)
    local = library / 'var/review' / packet.RACKET_ARCHIVE_NAME
    local.parent.mkdir(parents=True); local.write_bytes(b'pinned fixture')
    monkeypatch.setattr(packet, 'RACKET_ARCHIVE_SHA256', hashlib.sha256(local.read_bytes()).hexdigest())
    index = library / 'REVIEW/parametric-families-current.json'
    index.write_text(json.dumps({'families': [{'task_id': 'aaaa00000001'}]}))
    before = index.read_bytes()
    def unexpected(*args, **kwargs):
        pytest.fail('Fast eligibility should not deeply revalidate acceptances')
    monkeypatch.setattr(parametric_promotion, 'status', unexpected)
    result = build(library, tmp_path / 'fast.zip', fast=True, repair_target_count=3)
    with zipfile.ZipFile(result['zip']) as z:
        manifest = json.loads(z.read('PACKET-MANIFEST.json'))
    assert manifest['main_draw_policy']['ids'] == ['aaaa00000002']
    assert manifest['main_draw_policy']['excluded']['aaaa00000003'] == 'canonical_not_approved'
    assert index.read_bytes() == before
    assert not list((library / 'generators').glob('*/parametric/accepted.json'))
