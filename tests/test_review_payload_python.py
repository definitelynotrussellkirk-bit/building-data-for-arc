"""Bare Python payloads follow the outer wrapper, even without venv activation."""
import json
import os
from pathlib import Path
import subprocess
import venv

import pytest

from test_review_run_receipt import packet  # Same real outer/inner launchers.


@pytest.fixture
def runtime(packet, tmp_path):
    environment = packet / 'WORK/.venv'
    venv.EnvBuilder(with_pip=False).create(environment)
    python = environment / 'bin/python'
    hostile = tmp_path / 'hostile-bin'
    hostile.mkdir()
    for name in ('python', 'python3', 'ordinary-command'):
        path = hostile / name
        path.write_text('#!/bin/sh\nprintf "PATH command: %s\\n" "$0"\nexit 23\n')
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(hostile))
    env.pop('VIRTUAL_ENV', None)
    return python, hostile, env


def invoke(packet, runtime, payload):
    python, _, env = runtime
    return subprocess.run(
        [str(python), str(packet / 'review.py'), 'run',
         '--receipt', 'checks/probe/command.json', *payload],
        cwd=packet.parent, env=env, text=True, capture_output=True, timeout=10)


def receipt(packet):
    return json.loads((packet / 'WORK/checks/probe/command.json').read_text())


@pytest.mark.parametrize('name', ['python', 'python3'])
@pytest.mark.parametrize('code', [0, 7])
def test_bare_python_uses_wrapper_venv_and_records_resolved_payload(packet, runtime, name, code):
    python, _, _ = runtime
    probe = ('import json, os, sys; '
             'print(json.dumps([sys.executable, sys.prefix, os.getcwd()])); '
             'print("payload stderr", file=sys.stderr); '
             f'sys.exit({code})')
    payload = [name, '-c', probe]
    result = invoke(packet, runtime, payload)
    assert result.returncode == code, result.stderr
    assert json.loads(result.stdout) == [str(python), str(python.parent.parent), str(packet / 'WORK/repo')]
    assert 'payload stderr' in result.stderr
    row = receipt(packet)
    assert row['invocation']['argv'][-3:] == payload
    assert row['payload']['argv'] == [str(python), '-c', probe]
    assert row['delegated']['argv'][-3:] == row['payload']['argv']
    assert row['returncode'] == code
    assert row['invocation']['cwd'] == str(packet.parent)


@pytest.mark.parametrize('kind', ['absolute-python', 'relative-python', 'non-python'])
def test_explicit_paths_and_non_python_commands_keep_resolution(packet, runtime, kind):
    _, hostile, _ = runtime
    if kind == 'absolute-python':
        command = str(hostile / 'python3')
    elif kind == 'relative-python':
        path = packet / 'WORK/repo/python'
        path.write_bytes((hostile / 'python').read_bytes())
        path.chmod(0o755)
        command = './python'
    else:
        command = 'ordinary-command'
    result = invoke(packet, runtime, [command])
    assert result.returncode == 23, result.stderr
    assert result.stdout.startswith('PATH command: ')
    row = receipt(packet)
    assert row['payload']['argv'] == [command]
    assert row['delegated']['argv'][-1] == command
    assert row['returncode'] == 23


def test_changed_outer_source_is_rejected_before_payload(packet, runtime):
    with (packet / 'review.py').open('a') as stream:
        stream.write('\n# changed after manifest binding\n')
    result = invoke(packet, runtime, ['python', '-c', 'print("PAYLOAD RAN")'])
    assert result.returncode == 2
    assert 'Entry file changed: review.py' in result.stderr
    assert 'PAYLOAD RAN' not in result.stdout
    assert not (packet / 'WORK/checks').exists()
