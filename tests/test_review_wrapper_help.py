"""Wrapper help and misplaced-entry diagnostics run before runtime setup."""
import json
import shlex
import subprocess
import sys

import pytest

from test_review_run_receipt import packet


def call(packet, script, args):
    return subprocess.run([sys.executable, str(packet/script), *args], cwd=packet.parent,
                          text=True, capture_output=True, timeout=10)


@pytest.mark.parametrize('flag', ['--help', '-h'])
@pytest.mark.parametrize('explicit', [False, True])
def test_task_tests_help_is_wrapper_specific_and_does_not_start_runtime(packet, flag, explicit):
    (packet/'WORK/setup_racket.py').write_text('def ensure_racket(): raise RuntimeError("NO SETUP")\n')
    args = ['task-tests', *(['aaaa00000001'] if explicit else []), flag]
    result = call(packet, 'review.py', args)
    assert result.returncode == 0, result.stderr
    assert 'Usage: python3 review.py task-tests' in result.stdout
    assert '--stage task_tests' not in result.stdout
    assert '--phase after --out ../checks/' in result.stdout
    assert 'WORK/repo' in result.stdout and 'new' in result.stdout
    if explicit:
        assert 'task-tests aaaa00000001 --phase after --out ../checks/aaaa00000001-tests' in result.stdout
    assert not (packet/'WORK/checks').exists()


def test_task_tests_help_uses_current_assignment_in_copyable_example(packet):
    (packet/'WORK/ASSIGNMENT.json').write_text(json.dumps({'task_id': 'aaaa00000002'}))
    result = call(packet, 'review.py', ['task-tests', '--help'])
    assert result.returncode == 0
    assert 'task-tests aaaa00000002 --phase after --out ../checks/aaaa00000002-tests' in result.stdout


@pytest.mark.parametrize('prefix', [['review.py'], ['python3', 'review.py'], [sys.executable, './review.py']])
def test_misplaced_outer_entry_reports_runnable_correction_before_setup(packet, prefix):
    (packet/'WORK/setup_racket.py').write_text('def ensure_racket(): raise RuntimeError("NO SETUP")\n')
    result = call(packet, 'WORK/run_with_racket.py', [*prefix, 'task-tests', '--help'])
    assert result.returncode == 2
    assert 'WORK/repo' in result.stderr and 'outer entry point' in result.stderr
    assert 'NO SETUP' not in result.stderr
    corrected = shlex.split(next(line.strip() for line in result.stderr.splitlines() if line.startswith('  ')))
    assert corrected == [sys.executable, str(packet/'review.py'), 'task-tests', '--help']
    replay = subprocess.run(corrected, cwd=packet.parent, capture_output=True, text=True, timeout=10)
    assert replay.returncode == 0, replay.stderr


def test_real_repository_review_script_still_runs(packet):
    (packet/'WORK/repo/review.py').write_text('print("repo-local helper")\n')
    result = call(packet, 'WORK/run_with_racket.py', [sys.executable, 'review.py'])
    assert result.returncode == 0 and result.stdout.strip() == 'repo-local helper'
