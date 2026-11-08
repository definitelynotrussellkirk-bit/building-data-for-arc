"""The combined audit keeps independent stage outcomes on one immutable source."""
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main
from test_check_rotations import install_native_battery

TASK = 'aaaa00000001'


def install_tests(library, body='assert True'):
    home = library / f'generators/{TASK}/tests'
    home.mkdir()
    (home / 'test_selected.py').write_text('from pathlib import Path\nimport time\ndef test_selected():\n    ' + body + '\n')


def read_result(output):
    return json.loads((output / 'result.json').read_text())


def assert_audit_summary(result, output, *, verdict, complete):
    summary = result['audit_summary']
    assert summary['schema'] == 'arcpuzzles-audit-preset-summary-v1'
    assert summary['expected_stages'] == ['task_tests', 'semantic_gate']
    assert summary['preset_complete'] is complete
    assert summary['verdict'] == verdict
    assert summary['passed'] is (result['passed'] is True)
    assert summary['controller_status'] == result['status']
    pins = {row['sha256'] for row in result['runtime_manifest']['files']
            if row['library_path'] == f'generators/{TASK}/generator.py'}
    assert pins == {summary['generator_sha256']}
    assert set(summary['stages']) == {'task_tests', 'semantic_gate'}
    path = output / f'checks/{TASK}_audit_summary.json'
    assert json.loads(path.read_text()) == summary
    assert read_result(output)['audit_summary'] == summary
    assert path.relative_to(output).as_posix() in result['evidence_sha256']


def test_public_preset_runs_both_stages_on_one_source_without_changing_owner(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    original = {p.relative_to(library): p.read_bytes() for p in library.rglob('*') if p.is_file()}
    out = tmp_path / 'audit'
    assert main(['--library', str(library), 'check', TASK, '--stage', 'audit', '--out', str(out)]) == 0
    result = read_result(out)
    assert result['phase'] == 'audit' and result['passed'] is True
    assert result['audit_stages']['task_tests']['test_counts']['passed'] == 1
    assert result['audit_stages']['semantic_gate']['passed'] is True
    assert result['battery_summary']['phase'] == 'audit'
    assert (out / 'checks/task_tests.xml').is_file()
    assert (out / f'checks/{TASK}_audit_semantic_gate.log').is_file()
    assert not list((out / 'checks').glob('*_after_*'))
    assert_audit_summary(result, out, verdict='passed', complete=True)
    # The full twelve-stage report remains separate and honestly incomplete.
    assert result['battery_summary']['verdict'] == 'incomplete'
    assert result['battery_summary']['counts']['total'] == 12
    assert {p.relative_to(library): p.read_bytes() for p in library.rglob('*') if p.is_file()} == original


def test_failed_task_tests_do_not_hide_the_semantic_result(library, tmp_path):
    install_native_battery(library)
    install_tests(library, 'assert False, "retained task regression"')
    out = tmp_path / 'audit'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False and result['timed_out'] is False
    assert result['audit_stages']['task_tests']['test_counts']['failed'] == 1
    assert result['audit_stages']['semantic_gate']['passed'] is True
    assert 'retained task regression' in result['stdout']
    assert_audit_summary(result, out, verdict='failed', complete=True)


def test_missing_tests_cannot_count_as_a_passing_audit(library, tmp_path):
    install_native_battery(library)
    out = tmp_path / 'audit'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False
    assert result['audit_stages']['task_tests']['test_status'] == 'no_tests'
    assert result['audit_stages']['semantic_gate']['passed'] is True
    assert_audit_summary(result, out, verdict='failed', complete=True)


def test_no_semantic_contract_is_advisory_not_a_passing_audit(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text(
        'import json, sys\nfrom pathlib import Path\n'
        'Path(sys.argv[sys.argv.index("--json-out") + 1]).write_text('
        'json.dumps({"audits": [{"status": "NO_CONTRACT"}]}))\n')
    out = tmp_path / 'no-contract'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False
    assert result['audit_stages']['task_tests']['passed'] is True
    assert result['audit_stages']['semantic_gate']['exit_code'] == 0
    assert result['audit_stages']['semantic_gate']['passed'] is False
    assert result['audit_stages']['semantic_gate']['semantic_status'] == 'advisory'
    assert_audit_summary(result, out, verdict='failed', complete=True)


def test_all_skipped_tests_are_incomplete_evidence_not_a_passing_audit(library, tmp_path):
    install_native_battery(library)
    install_tests(library, '__import__("pytest").skip("fixture has no executed assertion")')
    out = tmp_path / 'skipped'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False
    assert result['audit_stages']['task_tests']['test_counts']['skipped'] == 1
    assert result['audit_stages']['task_tests']['passed'] is False
    assert result['audit_stages']['semantic_gate']['passed'] is True
    assert_audit_summary(result, out, verdict='failed', complete=True)


def test_rotation_requirement_reaches_only_the_semantic_stage(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    out = tmp_path / 'strict-audit'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out,
                           require_rotations_identifiable=True)
    assert result['passed'] is False
    assert result['audit_stages']['task_tests']['passed'] is True
    assert result['audit_stages']['semantic_gate']['passed'] is False
    assert result['battery_summary']['require_rotations_identifiable'] is True


def test_task_test_cannot_change_the_source_later_scored_by_semantic_gate(library, tmp_path):
    install_native_battery(library)
    install_tests(library, '(Path(__file__).parents[1] / "generator.py").write_text("changed = True\\n")')
    out = tmp_path / 'changed'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False and result['status'] == 'source_changed'
    assert result['audit_stages']['task_tests']['passed'] is True
    assert result['audit_stages']['semantic_gate']['status'] == 'not_run'
    assert f'generators/{TASK}/generator.py' in result['changed_runtime_sources']
    assert not (out / f'checks/{TASK}_audit_semantic_gate.log').exists()
    assert_audit_summary(result, out, verdict='source_changed', complete=False)


def test_first_stage_timeout_prevents_second_stage_and_keeps_partial_evidence(library, tmp_path):
    install_native_battery(library)
    install_tests(library, 'time.sleep(10)')
    out = tmp_path / 'timed-out'
    result = runtime.check(Catalog(library), TASK, stage='audit', timeout=2, output=out)
    assert result['passed'] is False and result['timed_out'] is True
    assert result['audit_stages']['task_tests']['timed_out'] is True
    assert result['audit_stages']['semantic_gate']['status'] == 'not_run'
    assert not (out / f'checks/{TASK}_audit_semantic_gate.log').exists()
    assert_audit_summary(result, out, verdict='incomplete', complete=False)


def test_semantic_timeout_keeps_completed_task_test_evidence(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text('import time\ntime.sleep(10)\n')
    out = tmp_path / 'semantic-timeout'
    result = runtime.check(Catalog(library), TASK, stage='audit', timeout=2, output=out)
    assert result['passed'] is False and result['timed_out'] is True
    assert result['audit_stages']['task_tests']['test_counts']['passed'] == 1
    assert result['audit_stages']['semantic_gate']['timed_out'] is True
    assert (out / 'checks/task_tests.xml').is_file()
    assert_audit_summary(result, out, verdict='incomplete', complete=False)


def test_semantic_source_edits_invalidate_an_otherwise_passing_audit(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text(
        'from pathlib import Path\n'
        f'Path("puzzle_generators/per_puzzle/{TASK}/generator.py").write_text("changed=True\\n")\n'
        'print("PASS")\n')
    out = tmp_path / 'semantic-changed'
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    assert result['passed'] is False and result['status'] == 'source_changed'
    assert result['audit_stages']['task_tests']['passed'] is True
    assert result['audit_stages']['semantic_gate']['passed'] is True
    assert f'puzzle_generators/per_puzzle/{TASK}/generator.py' in result['changed_runtime_sources']
    assert_audit_summary(result, out, verdict='source_changed', complete=True)


def test_interruption_retains_first_stage_and_never_claims_a_pass(library, tmp_path):
    install_native_battery(library)
    install_tests(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text(
        'import time\nprint("interrupt-fixture", flush=True)\ntime.sleep(10)\n')
    out = tmp_path / 'interrupted'

    def interrupt(chunk):
        if 'RUN   semantic_gate' in chunk:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        runtime.check(Catalog(library), TASK, stage='audit', output=out, on_output=interrupt)
    result = read_result(out)
    assert result['status'] == 'interrupted' and result['passed'] is not True
    assert result['audit_stages']['task_tests']['test_counts']['passed'] == 1
    assert result['audit_stages']['semantic_gate']['passed'] is not True
    assert result['audit_stages']['task_tests']['status'] == 'completed'
    assert result['audit_stages']['semantic_gate']['status'] == 'interrupted'
    assert (out / 'checks/task_tests.xml').is_file()
    assert_audit_summary(result, out, verdict='interrupted', complete=False)


@pytest.mark.parametrize('options', [dict(phase='after'), dict(full_battery=True), dict(resume=True)])
def test_conflicting_audit_modes_fail_before_creating_output(library, tmp_path, options):
    out = tmp_path / 'not-created' / 'audit'
    with pytest.raises(ValueError, match='audit|resume'):
        runtime.check(Catalog(library), TASK, stage='audit', output=out, **options)
    assert not out.parent.exists()


@pytest.mark.parametrize('retain_output', [False, True])
def test_missing_prerequisites_have_a_nonpassing_preset_summary(library, tmp_path, monkeypatch, retain_output):
    monkeypatch.setattr(runtime.sys, 'executable', str(tmp_path / 'missing-python'))
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('unusable interpreter staged source'))
    out = tmp_path / 'missing' if retain_output else None
    result = runtime.check(Catalog(library), TASK, stage='audit', output=out)
    summary = result['audit_summary']
    assert summary['verdict'] == 'infrastructure_failed'
    assert summary['preset_complete'] is False and summary['passed'] is False
    assert summary['expected_stages'] == ['task_tests', 'semantic_gate']
    assert summary['completed_stages'] == []
    assert summary['generator_sha256'] is None and summary['runtime_manifest_sha256'] is None
    if out is not None:
        assert read_result(out)['audit_summary'] == summary
