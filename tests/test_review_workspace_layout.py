import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet


def build_workspace(library, tmp_path, *, blind=False):
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(source / 'src', library / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    q = library / 'REVIEW/questions/q.json'
    q.parent.mkdir(parents=True)
    q.write_text(json.dumps(dict(schema='arcpuzzles-review-question-v1', id='q', version=1,
                                owner='ARCpuzzles', text='Why?')))
    result = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'request.zip',
                              workspace_layout=True, reviewer_solve=blind, blind_solve=blind)
    outer = tmp_path / 'relocated' / 'packet'
    with zipfile.ZipFile(result['zip']) as archive:
        archive.extractall(outer)
    return result, outer


def test_workspace_layout_is_hash_bound_and_has_one_source_copy(library, tmp_path):
    built, outer = build_workspace(library, tmp_path)
    assert {p.name for p in outer.iterdir()} == {'START-HERE.md', 'review.py', 'WORK'}
    manifest = json.loads((outer / 'WORK/PACKET-MANIFEST.json').read_text())
    for name, digest in manifest['layout']['entry_files'].items():
        assert hashlib.sha256((outer / name).read_bytes()).hexdigest() == digest
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((outer / 'WORK' / name).read_bytes()).hexdigest() == digest
    assert built['workspace'] == 'WORK'
    assert built['entrypoint'] == 'review.py'
    assert len(list(outer.rglob('generators/aaaa00000003/generator.py'))) == 1
    run = subprocess.run([sys.executable, str(outer / 'review.py'), 'start'], cwd=tmp_path,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    selected = json.loads((outer / 'WORK/ASSIGNMENT.json').read_text())['task_id']
    assert f'WORK/repo/generators/{selected}/' in run.stdout
    assert 'python3 review.py audit' in run.stdout
    assert not (outer / 'ASSIGNMENT.json').exists()
    assert (outer / 'WORK/ASSIGNMENT.json').is_file()
    run = subprocess.run([sys.executable, str(outer / 'review.py'), 'verify'], cwd=tmp_path,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_workspace_blind_first_navigation_and_entry_tampering(library, tmp_path):
    _, outer = build_workspace(library, tmp_path, blind=True)
    command = [sys.executable, str(outer / 'review.py')]
    run = subprocess.run(command + ['start'], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert 'NEXT: python3 review.py blind prepare' in run.stdout
    assert 'WORK/repo/generators/' not in run.stdout
    run = subprocess.run(command + ['duties'], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert 'python3 review.py blind prepare' in run.stdout
    assert 'python3 assignment.py' not in run.stdout
    (outer / 'START-HERE.md').write_text('changed')
    run = subprocess.run(command + ['status'], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode != 0
    assert 'Entry file changed: START-HERE.md' in run.stderr


def test_workspace_omits_resource_guard_and_still_checks_entry_inventory(library, tmp_path):
    guard = library / 'shared/tools/arc_review_guard.py'
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text('raise RuntimeError("retired guard must not run")\n')
    _, outer = build_workspace(library, tmp_path)
    assert not (outer / 'resource_guard.py').exists()
    assert not (outer / 'WORK/repo/shared/tools/arc_review_guard.py').exists()
    command = [sys.executable, str(outer / 'review.py')]
    for action in ('verify', 'start'):
        run = subprocess.run(command + [action], cwd=tmp_path, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    manifest_path = outer / 'WORK/PACKET-MANIFEST.json'
    manifest = json.loads(manifest_path.read_bytes())
    manifest['layout']['entry_files']['unexpected.py'] = hashlib.sha256(b'new').hexdigest()
    (outer / 'unexpected.py').write_bytes(b'new')
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    run = subprocess.run(command + ['status'], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode != 0
    assert 'Invalid workspace entry file inventory' in run.stderr


@pytest.mark.parametrize('kind,command,folder', [
    ('post_repair', 'solve', 'solve'),
    ('blind', 'blind', 'solve-blind'),
])
def test_solve_readme_commands_run_from_outer_workspace_root(
        library, tmp_path, monkeypatch, kind, command, folder):
    from arcpuzzles.review_solve import prepare_solve
    _, outer = build_workspace(library, tmp_path, blind=True)
    started = subprocess.run([sys.executable, str(outer / 'review.py'), 'start'],
                             cwd=outer, capture_output=True, text=True)
    assert started.returncode == 0, started.stderr
    def blocked_generation(*args, **kwargs):
        raise ValueError('Fixture does not need generated labels for navigation')
    monkeypatch.setattr(Catalog, 'generate', blocked_generation)
    prepare_solve(outer / 'WORK', kind=kind)
    readme = (outer / 'WORK' / folder / 'README.md').read_text()
    prefix = f'python3 review.py {command}'
    assert prefix + ' check ' in readme
    assert prefix + ' finish ' in readme
    assert 'python3 solve_episode.py' not in readme
    routed = subprocess.run([sys.executable, str(outer / 'review.py'), command, '--help'],
                            cwd=outer, capture_output=True, text=True)
    assert routed.returncode == 0, routed.stderr


@pytest.mark.parametrize('arguments', [
    ['check', '--stage', 'lint', 'aaaa00000001', '--phase', 'after'],
    ['check', 'aaaa00000001', '--stage', 'lint'],
    ['task-tests', '--phase', 'after', 'aaaa00000001'],
    ['task-tests', '--phase', 'after'],
])
def test_check_alias_preserves_options_and_accepts_explicit_target(tmp_path, monkeypatch, arguments, capsys):
    import importlib.util
    from types import SimpleNamespace
    path = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'
    spec = importlib.util.spec_from_file_location('packet_entry', path)
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    monkeypatch.setattr(entry, 'WORK', tmp_path)
    (tmp_path / 'ASSIGNMENT.json').write_text(json.dumps({'task_id': 'aaaa00000002'}))
    monkeypatch.setattr(entry, 'manifest', lambda: {'generators': {'aaaa00000001': {}, 'aaaa00000002': {}}})
    calls = []
    monkeypatch.setattr(entry.subprocess, 'run', lambda argv, **kw: calls.append((argv, kw)) or SimpleNamespace(returncode=7))
    assert entry.main(arguments) == 7
    argv, kwargs = calls[0]
    index = argv.index('check')
    expected = 'aaaa00000001' if 'aaaa00000001' in arguments else 'aaaa00000002'
    assert argv[index + 1] == expected
    assert argv.count(expected) == 1
    if arguments[0] == 'task-tests':
        assert argv[index + 2:index + 4] == ['--stage', 'task_tests']
    assert kwargs['cwd'] == tmp_path
    assert 'Failed command (cwd=' in capsys.readouterr().err
