"""Peer-audit evidence must retain its identity through isolated and managed checks."""
import json

import pytest

from arcpuzzles import Catalog, check_jobs, runtime
from arcpuzzles.cli import main
from test_check_resume import install_battery
from test_check_rotations import install_native_battery


TASK = 'aaaa00000001'


def install_audit_checkpoint(library):
    install_battery(library)
    script = library / 'shared/tools/run_generator_battery.sh'
    script.write_text(script.read_text().replace('_after_', '_audit_'))


@pytest.mark.parametrize('battery', [False, True])
def test_public_audit_check_retains_strict_failure_and_target_without_approval(library, tmp_path, battery):
    install_native_battery(library)
    checker = library / 'shared/tools/check_generator_override_contract.py'
    checker.write_text('''import json, sys
from pathlib import Path
strict = '--strict-unknown-key' in sys.argv
Path(sys.argv[sys.argv.index('--write-results') + 1]).write_text(
    json.dumps({'status': 'FAIL' if strict else 'PASS_WITH_WARNINGS'}))
print('unknown key accepted by fixture generator')
sys.exit(1 if strict else 0)
''')
    before = {p.relative_to(library): p.read_bytes() for p in library.rglob('*') if p.is_file()}
    out = tmp_path / 'peer-audit'
    mode = ['--battery'] if battery else ['--stage', 'override']
    assert main(['--library', str(library), 'check', TASK, *mode,
                 '--phase', 'audit', '--out', str(out)]) == 1
    result = json.loads((out / 'result.json').read_text())
    assert result['phase'] == 'audit' and result['task_id'] == TASK and result['passed'] is False
    assert result['battery_summary']['phase'] == 'audit'
    assert result['battery_summary']['stages']['override']['status'] == 'failed'
    assert (out / f'checks/{TASK}_audit_override_results.json').is_file()
    assert not list((out / 'checks').glob('*_after_*'))
    if battery:
        assert 'AUDIT CHECK FAILED' in result['stdout']
        assert 'AFTER CHECK FAILED' not in result['stdout']
    assert {p.relative_to(library): p.read_bytes() for p in library.rglob('*') if p.is_file()} == before


def test_public_task_tests_record_audit_not_repair(library, tmp_path):
    tests = library / f'generators/{TASK}/tests'
    tests.mkdir()
    (tests / 'test_selected.py').write_text('''from pathlib import Path
def test_selected_source():
    assert "VERSION = '1.0.0'" in (Path(__file__).parents[1] / 'generator.py').read_text()
''')
    out = tmp_path / 'audit-tests'
    assert main(['--library', str(library), 'check', TASK, '--stage', 'task_tests',
                 '--phase', 'audit', '--out', str(out)]) == 0
    result = json.loads((out / 'result.json').read_text())
    assert result['phase'] == 'audit' and result['task_id'] == TASK and result['passed'] is True
    assert result['test_status'] == 'executed' and result['test_counts']['passed'] == 1
    assert (out / 'checks/task_tests.xml').is_file()


def test_audit_resume_inherits_phase_and_rejects_repair_relabeling(library, tmp_path):
    install_audit_checkpoint(library)
    out = tmp_path / 'audit-battery'
    first = runtime.check(Catalog(library), TASK, full_battery=True, phase='audit', output=out)
    assert first['passed'] is False
    before = (out / 'result.json').read_bytes()
    with pytest.raises(ValueError, match='Phase differs'):
        runtime.check(Catalog(library), TASK, full_battery=True, phase='after', output=out, resume=True)
    assert (out / 'result.json').read_bytes() == before
    resumed = runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True)
    assert resumed['passed'] is True and resumed['phase'] == 'audit'
    assert (out / f'attempts/0001/checks/{TASK}_audit_override.log').read_text().strip() == 'failure'
    assert (out / f'checks/{TASK}_audit_lint.log').read_text().strip() == 'original'


def test_managed_public_audit_check_and_resume_keep_target_phase(library, capsys):
    install_audit_checkpoint(library)
    assert main(['--library', str(library), 'check-run', 'start', TASK,
                 '--phase', 'audit', '--timeout', '10']) == 0
    launched = json.loads(capsys.readouterr().out)
    run_id = launched['run_id']
    failed = check_jobs.wait(library, run_id, seconds=10)
    assert failed['status'] == 'stage_failed' and failed['resumable'] is True
    directory = library / 'var/check-runs' / run_id
    request = json.loads((directory / 'request.json').read_text())
    assert request['phase'] == 'audit' and request['task_id'] == TASK
    check_jobs.resume(library, run_id)
    finished = check_jobs.wait(library, run_id, seconds=10)
    assert finished['status'] == 'completed' and finished['attempt'] == 2
    result = json.loads((directory / 'check/result.json').read_text())
    assert result['phase'] == 'audit' and result['task_id'] == TASK and result['passed'] is True


def test_unsupported_phase_fails_before_creating_output_or_lock(library, tmp_path):
    parent = tmp_path / 'not-created'
    with pytest.raises(ValueError, match='Unknown check phase'):
        runtime.check(Catalog(library), TASK, phase='audit/target', output=parent / 'out')
    assert not parent.exists()
