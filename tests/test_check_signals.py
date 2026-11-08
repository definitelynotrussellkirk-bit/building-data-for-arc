"""Real foreground controllers and isolated process sessions, never corpus gates."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

import pytest

from test_check_rotations import install_native_battery

TASK = 'aaaa00000001'
SOURCE = Path(__file__).resolve().parents[1] / 'src'


def wait_until(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.03)
    pytest.fail('disposable controller did not reach the expected state')


def live(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z'
    except FileNotFoundError:
        return False


@pytest.mark.parametrize('signum', [signal.SIGTERM, signal.SIGINT])
@pytest.mark.parametrize('stage', ['lint', 'selfcheck'])
def test_foreground_signal_stops_stage_tree_checkpoints_and_resumes(library, tmp_path, signum, stage):
    install_native_battery(library)
    fixture = tmp_path / 'signal fixture'; fixture.mkdir()
    # GNU timeout and Bash job control create additional process groups in the
    # stage's session. Both descendants must stop, even with TERM ignored.
    filename = 'lint_generator.py' if stage == 'lint' else 'generator_selfcheck.py'
    (library / 'shared/tools' / filename).write_text('''
import json, os, signal, subprocess, sys, time
from pathlib import Path
root = Path(os.environ['CHECK_SIGNAL_FIXTURE'])
if (root / 'resume').exists():
    print('PASS recovered selfcheck'); sys.exit(0)
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c',
    'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(90)'])
(root / 'pids.json').write_text(json.dumps([os.getpid(), child.pid]))
print('fixture stage alive', flush=True)
time.sleep(90)
''')
    out = tmp_path / 'check output'
    args = [sys.executable, '-m', 'arcpuzzles', '--library', str(library), 'check', TASK,
            '--battery', '--phase', 'after', '--timeout', '90', '--compact-results', '--out', str(out)]
    env = dict(os.environ, PYTHONPATH=str(SOURCE), CHECK_SIGNAL_FIXTURE=str(fixture))
    controller = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pids = []
    try:
        wait_until(lambda: (fixture / 'pids.json').exists())
        pids = json.loads((fixture / 'pids.json').read_text())
        assert all(live(pid) for pid in pids)
        controller.send_signal(signum)
        stdout, stderr = controller.communicate(timeout=12)
        result = json.loads((out / 'result.json').read_text())
        assert controller.returncode == 128 + signum, (stdout, stderr)
        assert result['status'] == 'interrupted'
        assert result['interruption_signal'] == signum
        wait_until(lambda: not any(live(pid) for pid in pids))
        assert result['battery_summary']['verdict'] == 'interrupted'
        assert result['battery_summary']['stages'][stage]['status'] == 'interrupted'
        if stage == 'selfcheck':
            assert result['battery_summary']['stages']['lint']['status'] == 'green'
        assert result['battery_summary']['counts']['running'] == 0
        assert result['child_cleanup']['session_empty'] is True
        assert shlex.join(result['resume_argv']) in stderr
        assert '--compact-results' in result['resume_argv']
        (fixture / 'resume').touch()
        retry = subprocess.run(result['resume_argv'], env=env, capture_output=True, text=True, timeout=25)
        assert retry.returncode == 0, retry.stderr
        if stage == 'selfcheck':
            assert 'SKIP  lint' in retry.stderr
        assert json.loads((out / 'attempts/0001/result.json').read_text())['status'] == 'interrupted'
    finally:
        # Clean only the exact disposable processes created by this fixture,
        # including red-test failures against the old controller.
        if controller.poll() is None:
            controller.kill()
        for pid in pids:
            if live(pid):
                os.kill(pid, signal.SIGKILL)
        controller.communicate(timeout=5)


def test_timeout_stops_nested_process_groups(tmp_path):
    from arcpuzzles.runtime import run_process
    marker = tmp_path / 'pid'
    command = [sys.executable, '-c',
               'import subprocess,sys,time; from pathlib import Path; '
               'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(90)"],start_new_session=False,process_group=0); '
               'Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(90)', str(marker)]
    pid = None
    try:
        result = run_process(command, tmp_path, timeout=.5)
        pid = int(marker.read_text())
        assert result['timed_out'] is True
        wait_until(lambda: not live(pid))
    finally:
        if pid and live(pid):
            os.kill(pid, signal.SIGKILL)


def test_status_distinguishes_live_child_after_unclean_controller_loss(library, tmp_path, capsys):
    from arcpuzzles import runtime
    from arcpuzzles.cli import main
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(90)'], start_new_session=True)
    out = tmp_path / 'unclean'; out.mkdir()
    # A departed controller plus a distinct, still-live child session.
    dead = subprocess.Popen([sys.executable, '-c', 'pass']); dead.wait()
    record = {'status': 'running', 'stage': 'battery', 'task_id': TASK,
              'controller': {'pid': dead.pid, 'birth': 'departed'},
              'child_process': {'session': child.pid}}
    saved = out / 'result.json'; saved.write_text(json.dumps(record))
    before = saved.read_bytes()
    try:
        assert main(['--library', str(library), 'check-status', '--out', str(out)]) == 0
        status = json.loads(capsys.readouterr().out)
        assert status['status'] == 'controller_lost_child_alive'
        assert status['resumable'] is False
        assert [p['pid'] for p in status['live_session_processes']] == [child.pid]
        with pytest.raises(ValueError, match='unclean or unknown child liveness'):
            runtime.check(runtime.Catalog(library), TASK, output=out, full_battery=True, resume=True)
        assert saved.read_bytes() == before and live(child.pid)
        child.terminate(); child.wait(timeout=3)
        assert runtime.check_status(out)['status'] == 'parent_interrupted_unclean'
        assert runtime.check_status(out)['resumable'] is False
    finally:
        if child.poll() is None:
            child.kill(); child.wait()


def test_status_rejects_pid_reuse_and_legacy_liveness_unknown(tmp_path):
    from arcpuzzles import runtime
    out = tmp_path / 'status'; out.mkdir()
    path = out / 'result.json'
    path.write_text(json.dumps({'stage': 'battery', 'status': 'running',
                               'controller': {'pid': os.getpid(), 'birth': 'wrong-birth'}}))
    assert runtime.check_status(out)['status'] == 'parent_interrupted_unclean'
    path.write_text(json.dumps({'stage': 'battery', 'status': 'running'}))
    assert runtime.check_status(out)['status'] == 'liveness_unknown'
    path.write_text(json.dumps({'stage': 'battery', 'status': 'running',
                               'controller': runtime._process_identity(os.getpid())}))
    assert runtime.check_status(out)['status'] == 'running'


def test_inconsistent_proc_view_is_unknown_not_confirmed_death(tmp_path, monkeypatch):
    from arcpuzzles import runtime, check_jobs
    real_read = Path.read_text
    def mismatched(path, *args, **kwargs):
        raw = real_read(path, *args, **kwargs)
        if path == Path('/proc/self/stat'):
            return str(os.getpid() + 1) + ' ' + raw.split(' ', 1)[1]
        return raw
    monkeypatch.setattr(Path, 'read_text', mismatched)
    assert runtime._process_table_supported() is False
    assert runtime._session_processes(os.getsid(0)) is None
    out = tmp_path / 'ordinary'; out.mkdir()
    (out / 'result.json').write_text(json.dumps({'stage': 'battery', 'status': 'running',
                                               'controller': {'pid': os.getpid(), 'birth': 'old-view'}}))
    assert runtime.check_status(out)['status'] == 'liveness_unknown'
    run_id = 'd' * 32
    directory = tmp_path / 'var/check-runs' / run_id; directory.mkdir(parents=True)
    state = directory / 'state.json'
    state.write_text(json.dumps({'status': 'running', 'pid': os.getpid(), 'pid_birth': 'old-view'}))
    original = state.read_bytes()
    status = check_jobs.status(tmp_path, run_id)
    assert status['status'] == 'liveness_unknown' and status['resumable'] is False
    assert status['run_id'] == run_id and status['directory'] == str(directory)
    assert state.read_bytes() == original
    state.write_text(json.dumps({'status': 'stage_failed', 'exit_code': 1, 'resumable': True}))
    assert check_jobs.status(tmp_path, run_id)['status'] == 'stage_failed'


def test_signal_scope_restores_handlers_and_leaves_embedding_handlers_alone():
    from arcpuzzles import runtime
    original = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    with pytest.raises(runtime.CheckInterrupted):
        with runtime._check_signals():
            os.kill(os.getpid(), signal.SIGTERM)
    assert {sig: signal.getsignal(sig) for sig in original} == original
    def handler(signum, frame):
        pass
    try:
        signal.signal(signal.SIGTERM, handler)
        with runtime._check_signals():
            assert signal.getsignal(signal.SIGTERM) is handler
    finally:
        signal.signal(signal.SIGTERM, original[signal.SIGTERM])


def test_signal_scope_does_not_install_handlers_in_worker_threads():
    from concurrent.futures import ThreadPoolExecutor
    from arcpuzzles import runtime
    original = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    def scope():
        with runtime._check_signals():
            return {sig: signal.getsignal(sig) for sig in original}
    with ThreadPoolExecutor(max_workers=1) as executor:
        assert executor.submit(scope).result() == original


def test_signal_before_child_exits_preserves_committed_receipts(library, tmp_path):
    from arcpuzzles import Catalog, runtime
    install_native_battery(library)
    out = tmp_path / 'between stages'
    def interrupt(chunk):
        if 'PASS  lint' in chunk:
            raise KeyboardInterrupt('between-stage stop')
    with pytest.raises(KeyboardInterrupt):
        runtime.check(Catalog(library), TASK, full_battery=True, phase='after', output=out, on_output=interrupt)
    result = json.loads((out / 'result.json').read_text())
    assert result['battery_summary']['stages']['lint']['status'] == 'green'
    assert result['battery_summary']['counts']['running'] == 0
    assert runtime.check_status(out)['resumable'] is True


def test_resume_recipe_retains_policy_environment_and_schedule_copy(library, tmp_path, monkeypatch):
    from arcpuzzles import Catalog, runtime
    from test_check_resume import install_battery
    install_battery(library)
    monkeypatch.setenv('PYTHONHASHSEED', '23')
    monkeypatch.setenv('RACKET_PATH', 'fixture-racket')
    schedule = tmp_path / 'schedule.json'; schedule.write_text('{"fixture": "retained input"}')
    out = tmp_path / 'policy recipe'
    first = runtime.check(Catalog(library), TASK, full_battery=True, phase='after', output=out,
                          schedule_census=schedule, schedule_seed=13,
                          require_rotations_identifiable=True, full_results=True)
    assert first['passed'] is False
    argv = first['resume_argv']
    assert '--require-rotations-identifiable' in argv and '--full-results' in argv
    assert 'PYTHONHASHSEED=23' in argv and 'RACKET_PATH=fixture-racket' in argv
    assert argv[argv.index('--schedule-census') + 1] == str(out / 'checks/schedule-census-input.json')
    assert argv[argv.index('--schedule-seed') + 1] == '13'
    schedule.unlink()
    retry = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    assert retry.returncode == 0, retry.stderr
    final = json.loads((out / 'result.json').read_text())
    assert final['settings'] == first['settings'] and final['passed'] is True


def test_run_process_selected_racket_precedes_python_environment_launcher(tmp_path, monkeypatch):
    from arcpuzzles import runtime
    python_bin = tmp_path / 'python bin'; python_bin.mkdir()
    (python_bin / 'python3').symlink_to(sys.executable)
    shadow = python_bin / 'racket'
    shadow.write_text('#!/bin/sh\nexit 77\n'); shadow.chmod(0o755)
    selected_bin = tmp_path / 'selected racket bin'; selected_bin.mkdir()
    selected = selected_bin / 'racket'
    selected.write_text('#!/bin/sh\nexit 0\n'); selected.chmod(0o755)
    monkeypatch.setattr(runtime.sys, 'executable', str(python_bin / 'python3'))
    result = runtime.run_process(['/bin/sh', '-c', 'command -v racket; command -v python3'], tmp_path,
                                 extra_env={'RACKET_PATH': str(selected)})
    assert result['exit_code'] == 0
    assert result['stdout'].splitlines() == [str(selected), str(python_bin / 'python3')]


def test_resume_recipe_restores_pinned_racket_for_path_consuming_gates(library, tmp_path, monkeypatch):
    """Resume after a real Racket stage, from an environment with another PATH."""
    import shutil
    from arcpuzzles import Catalog, runtime
    binary = shutil.which(os.environ.get('RACKET_PATH', 'racket'))
    assert binary, 'This qualification requires the declared Racket runtime'
    install_native_battery(library)
    pinned = tmp_path / 'pinned racket bin'; pinned.mkdir()
    executable = pinned / 'racket'
    executable.write_text('#!/bin/sh\nexec ' + shlex.quote(binary) + ' "$@"\n')
    executable.chmod(0o755)
    monkeypatch.setenv('RACKET_PATH', str(executable))
    tools = library / 'shared/tools'
    (tools / 'rule_smoke.py').write_text('''import os,subprocess
assert subprocess.check_output([os.environ['RACKET_PATH'], '-e', '(add1 41)'], text=True).strip() == '42'
print('real pinned Racket stage passed')
''')
    (tools / 'generator_defect_lint.py').write_text('''import os,shutil,subprocess
assert shutil.which('racket') == os.environ['RACKET_PATH'], 'PATH selected another Racket'
assert subprocess.check_output(['racket', '-e', '(add1 41)'], text=True).strip() == '42'
print('resumed PATH-consuming Racket gate passed')
''')
    out = tmp_path / 'interrupted with pinned racket'
    def interrupt(chunk):
        if 'PASS  rule_smoke' in chunk:
            raise KeyboardInterrupt('after real Racket stage')
    with pytest.raises(KeyboardInterrupt):
        runtime.check(Catalog(library), TASK, full_battery=True, phase='after',
                      output=out, on_output=interrupt)
    first = json.loads((out / 'result.json').read_text())
    assert first['status'] == 'interrupted'
    assert first['battery_summary']['stages']['rule_smoke']['status'] == 'green'
    # No shell expansion or the caller's PATH may supply the missing pin.
    env = dict(os.environ, PATH='/usr/bin:/bin')
    retry = subprocess.run(first['resume_argv'], env=env, capture_output=True, text=True, timeout=25)
    assert retry.returncode == 0, retry.stderr
    final = json.loads((out / 'result.json').read_text())
    assert final['passed'] and final['settings'] == first['settings']
    assert 'SKIP  rule_smoke' in retry.stderr
    assert 'resumed PATH-consuming Racket gate passed' in (out / f'checks/{TASK}_after_defect_lint.log').read_text()
