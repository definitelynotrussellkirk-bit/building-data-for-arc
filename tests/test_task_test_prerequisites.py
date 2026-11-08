"""Missing isolated prerequisites are infrastructure failures before source staging."""
import json
from pathlib import Path
import subprocess
import sys

import pytest
from arcpuzzles import Catalog, runtime

TASK = 'aaaa00000001'


def test_missing_isolated_pytest_is_recorded_before_runtime_staging(library, tmp_path, monkeypatch):
    interpreter = tmp_path / 'without-deps/bin/python'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(interpreter.parents[1])], check=True)
    monkeypatch.setattr(runtime.sys, 'executable', str(interpreter))
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('missing dependencies staged source'))
    out = tmp_path / 'missing'
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=out)
    assert result['status'] == 'infrastructure_failed' and result['passed'] is False
    assert result['test_status'] == 'dependency_missing'
    assert result['missing_dependency'] == 'pytest'
    assert result['test_interpreter'] == str(interpreter)
    assert result['runtime_manifest'] is None and result['runtime_path'] is None
    assert result['test_counts'] is None
    preflight = result['test_prerequisite_preflight']
    assert preflight['python_no_user_site'] is True
    assert set(preflight['missing_dependencies']) == {'pytest', 'numpy', 'PIL'}
    assert '-m venv .venv-review' in result['stderr']
    assert 'pytest>=8' in result['stderr'] and 'numpy>=1.26' in result['stderr']
    assert json.loads((out / 'result.json').read_text())['passed'] is False
    assert not (out / 'RUNTIME_MANIFEST.json').exists()


def test_preflight_matches_isolated_test_interpreter(library, tmp_path, monkeypatch):
    tests = library / f'generators/{TASK}/tests'; tests.mkdir()
    (tests / 'test_isolation.py').write_text(
        'import site, sys\n'
        'def test_isolated():\n'
        ' assert site.ENABLE_USER_SITE is False\n'
        f' assert sys.executable == {sys.executable!r}\n')
    # This inherited path must be removed from both the probe and pytest child.
    monkeypatch.setenv('PYTHONPATH', '/not-the-task-runtime')
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path / 'ok')
    assert result['passed'], result['stderr']
    preflight = result['test_prerequisite_preflight']
    assert preflight['passed'] is True
    assert preflight['test_interpreter'] == sys.executable
    assert preflight['python_no_user_site'] is True
    assert preflight['pythonpath'] is None
    assert set(preflight['dependencies']) == {'pytest', 'numpy', 'PIL'}
    assert result['test_counts']['passed'] == 1


def test_unusable_interpreter_is_infrastructure_failure(library, tmp_path, monkeypatch):
    interpreter = str(tmp_path / 'missing-python')
    monkeypatch.setattr(runtime.sys, 'executable', interpreter)
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('unusable interpreter staged source'))
    result = runtime.check(Catalog(library), TASK, stage='task_tests')
    assert result['status'] == 'infrastructure_failed' and not result['passed']
    assert result['test_status'] == 'prerequisite_failed'
    assert result['test_prerequisite_preflight']['test_interpreter'] == interpreter
    assert result['test_counts'] is None
    assert 'FileNotFoundError' in result['stderr']
