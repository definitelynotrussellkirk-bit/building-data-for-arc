"""Catch packet-root-looking output paths before launching a check."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def packet(tmp_path):
    outer = tmp_path / 'packet'
    work = outer / 'WORK'
    (work / 'repo').mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'
    shutil.copyfile(source, outer / 'review.py')
    (outer / 'START-HERE.md').write_text('fixture\n')
    # Record delegation only: no check, runtime setup, or generator executes.
    (work / 'run_with_racket.py').write_text(
        'import json, sys\nfrom pathlib import Path\n'
        'Path("delegated.json").write_text(json.dumps(sys.argv[1:]))\n')
    (work / 'ASSIGNMENT.json').write_text(json.dumps({'task_id': 'aaaa00000001'}))
    manifest = {'layout': {'workspace': 'WORK', 'entry_files': {
        name: hashlib.sha256((outer / name).read_bytes()).hexdigest()
        for name in ['START-HERE.md', 'review.py']}}}
    (work / 'PACKET-MANIFEST.json').write_text(json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    return outer


def invoke(packet, command, options):
    return subprocess.run([sys.executable, str(packet / 'review.py'), command, *options],
                          cwd=packet.parent, capture_output=True, text=True, timeout=10)


@pytest.mark.parametrize('command', ['check', 'task-tests'])
@pytest.mark.parametrize('style', ['separate', 'equals'])
@pytest.mark.parametrize('target', ['WORK/checks/probe', './WORK/checks/probe',
                                   'elsewhere/../WORK/checks/probe', 'checks/probe', './checks/probe', 'elsewhere/../checks/probe', 'absolute'])
def test_nested_work_output_rejected_before_delegation(packet, command, style, target):
    if target == 'absolute':
        target = str(packet / 'WORK/repo/WORK/checks/probe')
    options = ['--out', target] if style == 'separate' else ['--out=' + target]
    result = invoke(packet, command, options)
    assert result.returncode == 2, result.stderr
    assert '../checks/' in result.stderr
    assert 'WORK/repo' in result.stderr
    assert not (packet / 'WORK/delegated.json').exists()
    assert not (packet / 'WORK/repo/WORK').exists()


@pytest.mark.parametrize('command', ['check', 'task-tests'])
@pytest.mark.parametrize('target', ['../checks/probe', 'var/checks/probe', 'absolute'])
def test_valid_output_path_passed_through_unchanged(packet, command, target):
    if target == 'absolute':
        target = str(packet / 'WORK/checks/probe')
    result = invoke(packet, command, ['--out', target])
    assert result.returncode == 0, result.stderr
    delegated = json.loads((packet / 'WORK/delegated.json').read_text())
    assert delegated[-2:] == ['--out', target]
    assert delegated[1:5] == ['-m', 'arcpuzzles', 'check', 'aaaa00000001']
    if command == 'task-tests':
        assert delegated[5:7] == ['--stage', 'task_tests']
