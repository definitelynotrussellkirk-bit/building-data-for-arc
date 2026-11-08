"""Dependency diagnostics work without a packet and do not install or select Python."""
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

ENTRY = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'


def invoke(python, directory, env=None):
    return subprocess.run([str(python), str(ENTRY), 'python-check'], cwd=directory,
                          env=env, capture_output=True, text=True, timeout=20)


def test_empty_venv_reports_missing_dependencies_despite_user_site(tmp_path):
    path = tmp_path / 'venv'
    venv.EnvBuilder(with_pip=False).create(path)
    userbase = tmp_path / 'users'
    site = userbase / f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
    site.mkdir(parents=True)
    for name in ('pytest', 'numpy', 'PIL'):
        (site / f'{name}.py').write_text('__version__ = "99.0.0"\n')
    result = invoke(path / 'bin/python', tmp_path, dict(os.environ, PYTHONUSERBASE=str(userbase)))
    assert result.returncode == 1, result.stderr
    row = json.loads(result.stdout)
    assert row['ready'] is False
    assert row['python'] == str(path / 'bin/python')
    assert row['user_site_enabled'] is False
    assert all(not item['ok'] for item in row['dependencies'])
    assert not (tmp_path / 'WORK').exists()


def test_preinstalled_interpreter_reports_import_versions(tmp_path):
    path = tmp_path / 'venv'
    venv.EnvBuilder(with_pip=False).create(path)
    site = path / f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
    for name, version in [('pytest', '9.0.2'), ('numpy', '2.3.5'), ('PIL', '12.3.0')]:
        (site / f'{name}.py').write_text(f'__version__ = {version!r}\n')
    result = invoke(path / 'bin/python', tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    row = json.loads(result.stdout)
    assert row['ready'] is True
    assert row['user_site_enabled'] is False
    assert {item['module'] for item in row['dependencies']} == {'pytest', 'numpy', 'PIL'}
    assert all(item['version'] and item['path'] for item in row['dependencies'])
