"""Compressed full authoring reports must restore exactly and remain retainable."""
from copy import deepcopy
import gzip
import hashlib
import json
import zipfile

import pytest

from arcpuzzles.cli import main
from arcpuzzles import lesson_census as controller
from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies
from test_census_companion import report


@pytest.mark.parametrize('status,exit_code', [('no_ambiguity_found', 0), ('ambiguous', 1), ('error', 2)])
def test_gzip_cli_preserves_complete_report_exit_and_existing_retention_contract(library, tmp_path, monkeypatch, capsys, status, exit_code):
    full = report(); full['task_id'] = 'aaaa00000001'; full['status'] = status
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: deepcopy(full))
    out = tmp_path / 'checks' / 'full census.json'
    argv = ['--library', str(library), 'lesson-census', full['task_id'], '--gzip', '--out', str(out)]
    assert main(argv) == exit_code
    console = json.loads(capsys.readouterr().out)
    compressed = out.with_suffix('.json.gz')
    assert not out.exists() and compressed.is_file()
    payload = compressed.read_bytes()
    raw = gzip.decompress(payload)
    assert json.loads(raw) == full and raw.endswith(b'\n')
    assert payload[4:8] == b'\0' * 4  # fixed gzip timestamp
    companion = json.loads(out.with_suffix('.summary.json').read_text())
    manifest_path = out.with_suffix('.compression.json')
    manifest = json.loads(manifest_path.read_text())
    assert manifest['schema'] == 'arcpuzzles-evidence-gzip-v1'
    entry, = manifest['files']
    assert entry['path'] == out.name and entry['compressed_path'] == compressed.name
    assert entry['raw_size'] == len(raw) and entry['compressed_size'] == len(payload)
    assert entry['raw_sha256'] == hashlib.sha256(raw).hexdigest()
    assert entry['compressed_sha256'] == hashlib.sha256(payload).hexdigest()
    assert companion['full_report']['sha256'] == entry['raw_sha256']
    assert companion['full_report']['bytes'] == len(raw)
    assert companion['full_report']['compressed_path'] == str(compressed.resolve())
    assert companion['full_report']['compressed_sha256'] == entry['compressed_sha256']
    assert companion['full_report']['compression_manifest'] == str(manifest_path.resolve())
    assert companion['status'] == status and companion['summary'] == full['summary']
    assert console['out'] == str(compressed) and console['compression_manifest'] == str(manifest_path)
    assert console['status'] == status
    # The actual shared retention reader follows the manifest; no restore script.
    members = {f'checks/{p.name}': p.read_bytes() for p in out.parent.iterdir()}
    selected, rows = _compressed_dependencies({f'checks/{manifest_path.name}'}, set(members), members.__getitem__)
    assert f'checks/{compressed.name}' in selected
    _verify_compressed_dependencies(rows, members.__getitem__)
    # No gzip filename or path-dependent timestamp: the same report compresses identically elsewhere.
    another = tmp_path / 'elsewhere' / 'other.json'
    assert main([*argv[:-1], str(another)]) == exit_code
    assert another.with_suffix('.json.gz').read_bytes() == payload


@pytest.mark.parametrize('reserved', ['census.json', 'census.json.gz', 'census.summary.json', 'census.compression.json'])
@pytest.mark.parametrize('symlink', [False, True])
def test_compressed_output_collision_refuses_before_generation(library, tmp_path, monkeypatch, reserved, symlink):
    home = tmp_path / 'outputs'; home.mkdir()
    out = home / 'census.json'; collision = home / reserved
    if symlink:
        collision.symlink_to(tmp_path / 'missing')
    else:
        collision.write_text('keep')
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: pytest.fail('collision started census'))
    assert main(['--library', str(library), 'lesson-census', 'aaaa00000001', '--gzip', '--out', str(out)]) == 1
    assert set(p.name for p in home.iterdir()) == {reserved}
    assert collision.is_symlink() if symlink else collision.read_text() == 'keep'


def test_compressed_census_rejects_non_json_logical_name_before_generation(library, tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: pytest.fail('invalid path started census'))
    assert main(['--library', str(library), 'lesson-census', 'aaaa00000001', '--gzip', '--out', str(tmp_path / 'out.json.gz')]) == 1
    assert not (tmp_path / 'out.json.gz').exists()


def test_full_report_above_return_limit_can_be_returned_as_native_gzip(library, tmp_path, monkeypatch):
    from arcpuzzles.review_full_return import build_full_return, validate_full_return
    from arcpuzzles.review_return import MAX_EXPANDED
    from test_review_full_collect import _return

    contract, _ = _return(library, tmp_path)
    home = tmp_path / 'packet-0'
    full = report(); full['task_id'] = contract['task_id']; full['status'] = 'no_ambiguity_found'
    full['runtime_manifest']['files'][0]['unrelated'] = 'x' * (MAX_EXPANDED + 1)
    monkeypatch.setattr(controller, 'lesson_census', lambda *a, **k: deepcopy(full))
    out = home / 'checks' / 'census.json'
    assert main(['--library', str(library), 'lesson-census', full['task_id'], '--gzip', '--out', str(out)]) == 0
    assert len(gzip.decompress(out.with_suffix('.json.gz').read_bytes())) > MAX_EXPANDED
    (home / 'FEEDBACK_TO_CODEX.md').write_text('## F1: Full source-bound compressed report\n\nKeep `checks/census.compression.json`.\n')
    returned = build_full_return(home, tmp_path / 'compressed-return.zip')
    with zipfile.ZipFile(tmp_path / 'compressed-return.zip') as archive:
        checked = validate_full_return(archive, json.loads((home / 'PACKET-MANIFEST.json').read_text()))
    assert checked['assignment_id'] == contract['assignment_id']
    assert returned['zip_sha256']
