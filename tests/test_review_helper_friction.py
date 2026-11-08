"""Packet ergonomics with source and evidence boundaries unchanged."""
import importlib.util
import json
from pathlib import Path
import pytest
from test_parametric_promotion import candidate
from test_review_qualified_projection import qualified, EXPORTER
from arcpuzzles import review_witness

@pytest.fixture
def entry(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'
    spec = importlib.util.spec_from_file_location('friction_entry', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path / 'packet')
    monkeypatch.setattr(module, 'WORK', tmp_path / 'packet/WORK')
    monkeypatch.setattr(module, 'manifest', lambda: {})
    def forbidden(*a, **kw): pytest.fail('Path diagnostics must not install or launch anything')
    monkeypatch.setattr(module.subprocess, 'run', forbidden)
    return module

def test_paths_are_independent_of_invocation_directory(entry, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert entry.main(['paths']) == 0
    row = json.loads(capsys.readouterr().out)
    assert row['payload_cwd'] == str(entry.WORK / 'repo')
    assert row['receipt_root'] == str(entry.WORK)
    assert row['examples']['payload_output'] == '../checks/NAME'
    assert row['examples']['launcher_receipt'] == 'checks/NAME/command.json'
    assert row['runtime_selected'] is False
    assert not entry.WORK.exists()

def test_receipt_coordinate_error_has_copy_ready_example(entry):
    with pytest.raises(ValueError, match='--receipt checks/NAME/command.json'):
        entry.run_receipt_path('../checks/probe/command.json')

def test_verify_can_save_receipt_outside_bundle(qualified, tmp_path, monkeypatch, capsys):
    root, _, q, _, _ = qualified
    bundle = tmp_path/'bundle'; EXPORTER.export_qualified(q, bundle, library=root)
    original = EXPORTER.verify_export
    monkeypatch.setattr(EXPORTER, 'verify_export', lambda p: original(p, library=root))
    out = tmp_path/'checks/verified.json'
    assert EXPORTER.main(['verify', '--bundle', str(bundle), '--out', str(out)]) == 0
    row = json.loads(out.read_text())
    assert row == json.loads(capsys.readouterr().out)
    assert row['status'] == 'verified_projection' and row['racket_replayed'] is False
    assert original(bundle, library=root)['status'] == 'verified_projection'
    before = out.read_bytes()
    assert EXPORTER.main(['verify', '--bundle', str(bundle), '--out', str(out)]) == 1
    assert out.read_bytes() == before

@pytest.mark.parametrize('location', ['public', 'private', 'symlink'])
def test_verify_receipt_cannot_modify_bundle(qualified, tmp_path, monkeypatch, location):
    root, _, q, _, _ = qualified
    bundle = tmp_path/'bundle'; EXPORTER.export_qualified(q, bundle, library=root)
    original = EXPORTER.verify_export
    monkeypatch.setattr(EXPORTER, 'verify_export', lambda p: original(p, library=root))
    if location == 'symlink':
        alias = tmp_path/'alias'; alias.symlink_to(bundle/'private', target_is_directory=True)
        out = alias/'verified.json'
    else: out = bundle/location/'verified.json'
    assert EXPORTER.main(['verify', '--bundle', str(bundle), '--out', str(out)]) == 1
    assert not out.exists()
    assert original(bundle, library=root)['status'] == 'verified_projection'

def test_tampered_projection_writes_no_success_receipt(qualified, tmp_path, monkeypatch):
    root, _, q, _, _ = qualified
    bundle = tmp_path/'bundle'; EXPORTER.export_qualified(q, bundle, library=root)
    next((bundle/'public').iterdir()).write_text('{}')
    original = EXPORTER.verify_export
    monkeypatch.setattr(EXPORTER, 'verify_export', lambda p: original(p, library=root))
    out = tmp_path/'not-written.json'
    assert EXPORTER.main(['verify', '--bundle', str(bundle), '--out', str(out)]) == 1
    assert not out.exists()

def test_witness_template_settings_selector_and_private_context(qualified, tmp_path):
    root, _, q, _, execution = qualified; out = tmp_path/'draft.json'
    result = review_witness.write_template(root, q, out, settings={'side': 'left'})
    draft = json.loads(out.read_text())
    assert draft['cases'][0]['episode_index'] == 0 and result['status'] == 'draft_only'
    assert draft['selected_case']['settings'] == {'side': 'left'}
    assert draft['selected_case']['program_sha256'] == execution['episodes'][0]['program_sha256']
    assert draft['selected_case']['input'] == execution['episodes'][0]['test'][0]['input']
    assert draft['receipt_alternatives'][0]['settings'] == {'side': 'right'}
    assert draft['receipt_alternatives'][0]['counterfactual_checked'] is False
    assert draft['cases'][0]['counterfactual_program'] == ''

@pytest.mark.parametrize('setting', [{'side':'absent'}, {'side': True}, {}, ['left']])
def test_unknown_or_partial_settings_leave_no_template(qualified, tmp_path, setting):
    root, _, q, _, _ = qualified
    with pytest.raises(ValueError, match='settings|setting'):
        review_witness.write_template(root, q, tmp_path/'absent.json', settings=setting)
    assert not (tmp_path/'absent.json').exists()

def test_witness_selector_cli(qualified, tmp_path):
    root, _, q, _, _ = qualified; out = tmp_path/'cli.json'
    assert review_witness.main(['--library', str(root), 'template', '--qualification', str(q),
        '--settings', '{"side":"left"}', '--out', str(out)]) == 0
    assert json.loads(out.read_text())['cases'][0]['episode_index'] == 0

@pytest.mark.parametrize('alternate', [{'side':'left'}, {'side':'absent'}, {}, ['right']])
def test_bad_alternate_setting_does_not_write_template(qualified, tmp_path, alternate):
    root, _, q, _, _ = qualified
    with pytest.raises(ValueError, match='setting'):
        review_witness.write_template(root, q, tmp_path/'no-draft.json', settings={'side':'left'},
                                      counterfactual_settings=alternate)
    assert not (tmp_path/'no-draft.json').exists()


def test_paths_command_runs_from_relocated_packet(tmp_path):
    import hashlib
    import shutil
    import subprocess
    import sys
    source = Path(__file__).resolve().parents[1]/'src/arcpuzzles/review_workspace_files/review.py'
    packet = tmp_path/'elsewhere/packet'; work = packet/'WORK'; work.mkdir(parents=True)
    shutil.copy2(source, packet/'review.py')
    (packet/'START-HERE.md').write_text('fixture')
    manifest = {'layout': {'workspace':'WORK','entry_files':{
        name:hashlib.sha256((packet/name).read_bytes()).hexdigest() for name in ('review.py','START-HERE.md')}}}
    (work/'PACKET-MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, separators=(',',':')))
    result = subprocess.run([sys.executable, str(packet/'review.py'), 'paths'],
                            cwd=tmp_path, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    row = json.loads(result.stdout)
    assert row['payload_cwd'] == str(work/'repo')
    assert not (work/'.review').exists() and not (work/'ASSIGNMENT.json').exists()


def test_noncanonical_safe_evidence_paths_already_supported():
    from test_review_two_parametric import reports
    from arcpuzzles.review_targets import validate_target_outcomes
    contract, results = reports()
    for i, row in enumerate(results['repair_targets']):
        home = 'repo/generators/'+row['task_id']+'/workspace/parametric/'
        qualification = f'checks/custom-version-{i}/qualification.json'
        witness = f'checks/different-place-{i}/witness.json'
        row.update(outcome='prototype', evidence_paths=[qualification,witness])
        row['parametric_work'] = dict(status='ready', summary='Source-bound candidate',
            prototype_path=home+'adapter.py', promotion_path=home+'promotion.json',
            inventory_path=home+'evidence/manifest.json', qualification_path=qualification,
            sequential_dependency=dict(step_a='A',intermediate='I',step_b='B',why_b_depends_on_a='A to B',witness_path=witness))
    assert len(validate_target_outcomes(contract,results)) == 2
