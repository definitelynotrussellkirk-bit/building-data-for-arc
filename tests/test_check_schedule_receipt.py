"""Receipt bytes and population are explicit inputs to portable check/resume."""
import hashlib
import gzip
import json
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main
from test_check_rotations import install_native_battery

TASK = 'aaaa00000001'


def compressed_receipt(tmp_path, raw=b'{"retained": true}\n'):
    payload = gzip.compress(raw, mtime=0)
    packed = tmp_path / 'census with spaces.json.gz'
    packed.write_bytes(payload)
    manifest = tmp_path / 'census with spaces.compression.json'
    entry = {'path': packed.name[:-3], 'compressed_path': packed.name,
             'raw_size': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
             'compressed_size': len(payload), 'compressed_sha256': hashlib.sha256(payload).hexdigest()}
    manifest.write_text(json.dumps({'schema': 'arcpuzzles-evidence-gzip-v1',
                                  'compression': 'gzip', 'files': [entry]}) + '\n')
    return packed, manifest, raw


def install_receipt_gate(library):
    install_native_battery(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text('''import json, sys
from pathlib import Path
path = Path(sys.argv[sys.argv.index('--schedule-census') + 1])
assert json.loads(path.read_text()) == {'retained': True}
assert sys.argv[sys.argv.index('--schedule-seed') + 1] == '31'
Path(sys.argv[sys.argv.index('--json-out') + 1]).write_text(json.dumps({'audits': [{'status': 'PASS'}]}))
print('source-bound receipt was forwarded')
''')


@pytest.mark.parametrize('battery', [False, True])
def test_public_receipt_is_copied_and_bound_to_result(library, tmp_path, battery):
    install_receipt_gate(library)
    receipt = tmp_path / 'receipt with spaces.json'
    raw = b'{"retained": true}\n'
    receipt.write_bytes(raw)
    out = tmp_path / 'out'
    mode = ['--battery'] if battery else ['--stage', 'semantic_gate']
    assert main(['--library', str(library), 'check', TASK, *mode,
                 '--schedule-census', str(receipt), '--schedule-seed', '31', '--out', str(out)]) == 0
    result = json.loads((out / 'result.json').read_text())
    assert result['settings']['schedule_census_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['settings']['schedule_seed'] == 31
    assert (out / 'checks/schedule-census-input.json').read_bytes() == raw
    assert receipt.read_bytes() == raw
    assert 'source-bound receipt was forwarded' in (out / f'checks/{TASK}_before_semantic_gate.log').read_text()
    assert result['battery_summary']['schedule_census_sha256'] == hashlib.sha256(raw).hexdigest()


def test_resume_refuses_changed_receipt_before_overwriting_evidence(library, tmp_path):
    install_receipt_gate(library)
    receipt = tmp_path / 'receipt.json'
    receipt.write_text('{"retained": true}')
    out = tmp_path / 'out'
    runtime.check(Catalog(library), TASK, full_battery=True, output=out, schedule_census=receipt, schedule_seed=31)
    before = (out / 'result.json').read_bytes()
    receipt.write_text('{"retained": false}')
    with pytest.raises(ValueError, match='Settings differ'):
        runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True,
                      schedule_census=receipt, schedule_seed=31)
    assert (out / 'result.json').read_bytes() == before


@pytest.mark.parametrize('options', [{'stage': 'lint'}, {'stage': 'task_tests'},
                                     {'stage': 'semantic_gate', 'schedule_seed': True},
                                     {'stage': 'semantic_gate', 'schedule_seed': -1}])
def test_invalid_schedule_request_cannot_stage(library, monkeypatch, options):
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('invalid request staged'))
    with pytest.raises(ValueError, match='schedule|seed'):
        runtime.check(Catalog(library), TASK, schedule_census=Path('never-read.json'), **options)


def test_native_receipt_changed_at_same_path_cannot_reuse_marker(library, tmp_path):
    install_receipt_gate(library)
    root = tmp_path / 'independent'
    runtime.prepare_runtime(Catalog(library), root, TASK)
    (root / 'receipt.json').write_text('{"retained": true}')
    argv = ['bash', 'scripts/run_generator_battery.sh', TASK, 'before', 'semantic_gate',
            '--schedule-census', 'receipt.json', '--schedule-seed', '31']
    first = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    (root / 'receipt.json').write_text('{"retained": false}')
    second = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    assert second.returncode != 0
    assert 'SKIP  semantic_gate' not in second.stdout


def test_audit_preset_forwards_receipt_to_semantic_stage(library, tmp_path):
    from test_check_audit_preset import install_tests
    install_receipt_gate(library)
    install_tests(library)
    receipt = tmp_path / 'receipt.json'
    receipt.write_text('{"retained": true}')
    result = runtime.check(Catalog(library), TASK, stage='audit', output=tmp_path / 'audit',
                           schedule_census=receipt, schedule_seed=31)
    assert result['passed'] and result['audit_stages']['task_tests']['passed']
    assert result['audit_stages']['semantic_gate']['passed']
    assert '--schedule-census' in result['audit_stages']['semantic_gate']['command']


@pytest.mark.parametrize('battery', [False, True])
@pytest.mark.parametrize('input_kind', ['gzip', 'manifest'])
def test_compressed_receipt_is_verified_then_forwarded_as_exact_json(library, tmp_path, battery, input_kind):
    install_receipt_gate(library)
    packed, manifest, raw = compressed_receipt(tmp_path)
    source = packed if input_kind == 'gzip' else manifest
    snapshots = {p: p.read_bytes() for p in (packed, manifest)}
    out = tmp_path / 'out'
    result = runtime.check(Catalog(library), TASK, stage='semantic_gate', full_battery=battery,
                           schedule_census=source, schedule_seed=31, output=out)
    assert result['passed'], result['stdout'] + result['stderr']
    assert (out / 'checks/schedule-census-input.json').read_bytes() == raw
    assert result['settings']['schedule_census_sha256'] == hashlib.sha256(raw).hexdigest()
    transport = result['settings']['schedule_census_transport']
    assert transport['format'] == 'arcpuzzles-evidence-gzip-v1'
    assert transport['manifest_sha256'] == hashlib.sha256(snapshots[manifest]).hexdigest()
    assert transport['compressed_sha256'] == hashlib.sha256(snapshots[packed]).hexdigest()
    assert (out / 'checks/schedule-census-source/MANIFEST.json').read_bytes() == snapshots[manifest]
    assert (out / 'checks/schedule-census-source' / packed.name).read_bytes() == snapshots[packed]
    assert all(p.read_bytes() == data for p, data in snapshots.items())


@pytest.mark.parametrize('damage', ['compressed_hash', 'compressed_size', 'raw_hash', 'raw_size',
                                   'bad_path', 'bool_size', 'multi_file', 'missing_manifest', 'truncated_gzip'])
def test_bad_compressed_receipt_is_rejected_before_staging(library, tmp_path, monkeypatch, damage):
    packed, manifest, _ = compressed_receipt(tmp_path)
    data = json.loads(manifest.read_bytes()); row = data['files'][0]
    if damage == 'compressed_hash': row['compressed_sha256'] = '0' * 64
    elif damage == 'compressed_size': row['compressed_size'] += 1
    elif damage == 'raw_hash': row['raw_sha256'] = '0' * 64
    elif damage == 'raw_size': row['raw_size'] -= 1
    elif damage == 'bad_path': row['path'] = '../outside.json'; row['compressed_path'] = '../outside.json.gz'
    elif damage == 'bool_size': row['raw_size'] = True
    elif damage == 'multi_file': data['files'].append(dict(row))
    elif damage == 'truncated_gzip':
        raw = packed.read_bytes()[:-4]; packed.write_bytes(raw)
        row.update(compressed_size=len(raw), compressed_sha256=hashlib.sha256(raw).hexdigest())
    manifest.write_text(json.dumps(data))
    if damage == 'missing_manifest': manifest.unlink()
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('Invalid gzip receipt staged'))
    with pytest.raises(ValueError, match='receipt|manifest|compressed|gzip|size|path|file'):
        runtime.check(Catalog(library), TASK, stage='semantic_gate', schedule_census=packed,
                      schedule_seed=31, output=tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_same_raw_receipt_does_not_hide_changed_transport_on_resume(library, tmp_path):
    install_receipt_gate(library)
    packed, manifest, _ = compressed_receipt(tmp_path)
    out = tmp_path / 'out'
    runtime.check(Catalog(library), TASK, full_battery=True, output=out,
                  schedule_census=packed, schedule_seed=31)
    original = (out / 'result.json').read_bytes()
    manifest.write_text(json.dumps(json.loads(manifest.read_bytes()), indent=2))
    with pytest.raises(ValueError, match='Settings differ'):
        runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True,
                      schedule_census=packed, schedule_seed=31)
    assert (out / 'result.json').read_bytes() == original


def test_prepare_runtime_cannot_overwrite_a_different_mapped_receipt_reader(library, tmp_path):
    source = library / 'shared/tools/receipt_input.py'
    source.parent.mkdir(parents=True)
    source.write_text('raise AssertionError("mapped library source")\n')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': 'shared/tools/receipt_input.py', 'target': 'scripts/receipt_input.py'})
    mapping.write_text(json.dumps(rows))
    stage = tmp_path / 'stage'
    with pytest.raises(ValueError, match='receipt reader'):
        runtime.prepare_runtime(Catalog(library), stage, TASK)
    assert (stage / 'scripts/receipt_input.py').read_bytes() == source.read_bytes()
