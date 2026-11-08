"""Real subprocess regressions for the portable command evidence recorder."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'workspace' / 'record_command.py'


def run_record(tmp_path, command, *, extra=(), env=None, out=None):
    destination = out or tmp_path / 'evidence'
    argv = [sys.executable, str(SCRIPT), '--cwd', str(tmp_path),
            '--out', str(destination), *extra, '--', *command]
    result = subprocess.run(argv, capture_output=True, env=env, timeout=8)
    receipt = destination / 'receipt.json'
    return result, json.loads(receipt.read_text()) if receipt.exists() else None


def test_real_output_argv_cwd_nonzero_exit_and_safe_environment(tmp_path):
    # Catch shell execution, merged/lost streams, exit laundering and env leaks.
    literal = 'literal $HOME `no-execution` ; argument'
    command = [sys.executable, '-c',
               'import os,sys; print(os.getcwd()); print(sys.argv[1]); '
               'sys.stderr.buffer.write(b"error\\x00bytes\\n"); sys.exit(7)', literal]
    env = dict(os.environ, TMPDIR=str(tmp_path), PYTHONHASHSEED='17',
               RECORD_TEST_TOKEN='never-record-this-secret')
    result, receipt = run_record(tmp_path, command, env=env)
    assert result.returncode == 7
    assert receipt['child_exit_code'] == receipt['exit_code'] == 7
    assert receipt['argv'] == command
    assert receipt['cwd'] == str(tmp_path)
    assert receipt['timed_out'] is False
    assert (tmp_path / 'evidence/stdout.log').read_bytes() == (
        str(tmp_path) + '\n' + literal + '\n').encode()
    assert (tmp_path / 'evidence/stderr.log').read_bytes() == b'error\x00bytes\n'
    assert receipt['environment']['TMPDIR'] == str(tmp_path)
    assert set(receipt['environment']) <= {
        'TMPDIR', 'PYTHONNOUSERSITE', 'PYTHONHASHSEED', 'PYTHONPATH', 'RACKET_PATH'}
    assert 'never-record-this-secret' not in json.dumps(receipt)
    assert receipt['recorder']['executable'] == sys.executable
    assert receipt['recorder']['argv'][0] == str(SCRIPT)
    assert receipt['recorder']['sha256'] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()


def test_stdout_streams_before_the_command_exits(tmp_path):
    # Catch capture_output buffering instead of direct streaming to evidence.
    out = tmp_path / 'evidence'
    argv = [sys.executable, str(SCRIPT), '--cwd', str(tmp_path), '--out', str(out),
            '--', sys.executable, '-c',
            'import time; print("ready",flush=True); time.sleep(1)']
    process = subprocess.Popen(argv)
    try:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if (out / 'stdout.log').exists() and (out / 'stdout.log').read_bytes() == b'ready\n':
                break
            time.sleep(0.01)
        assert process.poll() is None
        assert (out / 'stdout.log').read_bytes() == b'ready\n'
        assert process.wait(timeout=3) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_existing_output_directory_is_never_overwritten_or_executed(tmp_path):
    # Catch clobbering evidence or running a command despite rejected output.
    out = tmp_path / 'evidence'
    out.mkdir()
    sentinel = out / 'receipt.json'
    sentinel.write_text('{"original": true}')
    result, receipt = run_record(tmp_path, [sys.executable, '-c',
                                          'open("executed","w").write("bad")'], out=out)
    assert result.returncode != 0
    assert receipt == {'original': True}
    assert not (tmp_path / 'executed').exists()
    assert sorted(p.name for p in out.iterdir()) == ['receipt.json']


@pytest.mark.skipif(os.name != 'posix', reason='POSIX process-group cleanup')
def test_timeout_kills_child_and_descendant_without_false_success(tmp_path):
    # Catch killing only the direct child while its descendants keep running.
    descendant = 'import time; time.sleep(1); open("survived","w").write("bad")'
    command = [sys.executable, '-c',
               'import subprocess,sys,time; '
               f'subprocess.Popen([sys.executable,"-c",{descendant!r}]); '
               'print("spawned",flush=True); time.sleep(30)']
    result, receipt = run_record(tmp_path, command, extra=['--timeout', '0.3'])
    assert result.returncode == receipt['exit_code'] == 124
    assert receipt['timed_out'] is True
    assert receipt['child_exit_code'] < 0
    assert receipt['cleanup_scope'] == 'process_group'
    assert (tmp_path / 'evidence/stdout.log').read_bytes() == b'spawned\n'
    time.sleep(1.1)
    assert not (tmp_path / 'survived').exists()


def test_source_change_cannot_report_a_successful_verification(tmp_path):
    # Catch child exit0 passing evidence whose input changed mid-command.
    source = tmp_path / 'source.py'
    source.write_bytes(b'before\n')
    command = [sys.executable, '-c', 'open("source.py","wb").write(b"after\\n")']
    result, receipt = run_record(tmp_path, command, extra=['--hash-input', 'source.py'])
    assert result.returncode == receipt['exit_code'] == 3
    assert receipt['child_exit_code'] == 0
    assert receipt['source_changed'] is True
    entry = receipt['hash_inputs'][0]
    assert entry['path'] == str(source)
    assert entry['before']['sha256'] == hashlib.sha256(b'before\n').hexdigest()
    assert entry['after']['sha256'] == hashlib.sha256(b'after\n').hexdigest()


def test_missing_executable_leaves_a_valid_failure_receipt(tmp_path):
    # Catch launch exceptions that omit evidence or report success.
    result, receipt = run_record(tmp_path, [str(tmp_path / 'absent-executable')])
    assert result.returncode == receipt['exit_code'] == 2
    assert receipt['child_exit_code'] is None
    assert receipt['error']['type'] == 'FileNotFoundError'
    assert receipt['timed_out'] is False
    assert (tmp_path / 'evidence/stdout.log').exists()
    assert (tmp_path / 'evidence/stderr.log').exists()


def test_unchanged_multiple_inputs_retain_matching_hashes(tmp_path):
    # Catch hashing only one of repeated controls or resolving files at caller cwd.
    for name, content in [('a', b'one'), ('b', b'two')]:
        (tmp_path / name).write_bytes(content)
    result, receipt = run_record(tmp_path, [sys.executable, '-c', 'pass'],
                                 extra=['--hash-input', 'a', '--hash-input', 'b'])
    assert result.returncode == 0
    assert receipt['source_changed'] is False
    assert len(receipt['hash_inputs']) == 2
    assert all(entry['before'] == entry['after'] for entry in receipt['hash_inputs'])


def test_missing_hash_input_fails_before_running_command(tmp_path):
    # Catch silently unchecked inputs that make a later success claim unbound.
    result, receipt = run_record(tmp_path, [sys.executable, '-c',
                                          'open("executed","w").write("bad")'],
                                 extra=['--hash-input', 'absent'])
    assert result.returncode == receipt['exit_code'] == 2
    assert receipt['child_exit_code'] is None
    assert receipt['hash_inputs'][0]['before']['error']['type'] == 'FileNotFoundError'
    assert not (tmp_path / 'executed').exists()
