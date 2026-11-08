"""Optional receipts describe launcher completion without changing payload status."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def packet(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'src/arcpuzzles'
    outer = tmp_path / 'packet'
    work = outer / 'WORK'
    (work / 'repo').mkdir(parents=True)
    shutil.copy(source / 'review_workspace_files/review.py', outer / 'review.py')
    shutil.copy(source / 'review_full_packet_files/run_with_racket.py', work / 'run_with_racket.py')
    # Avoid downloading or invoking a runtime: the probe only needs Python.
    (work / 'setup_racket.py').write_text('from pathlib import Path\ndef ensure_racket(): return Path("/fixture/racket")\n')
    (outer / 'START-HERE.md').write_text('fixture\n')
    manifest = {'layout': {'workspace': 'WORK', 'entry_files': {
        name: hashlib.sha256((outer / name).read_bytes()).hexdigest()
        for name in ['START-HERE.md', 'review.py']}}}
    (work / 'PACKET-MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    return outer


def invoke(packet, arguments):
    return subprocess.run([sys.executable, str(packet / 'review.py'), 'run', *arguments],
                          cwd=packet.parent, text=True, capture_output=True, timeout=10)


@pytest.mark.parametrize('code', [0, 7])
def test_receipt_is_terminal_and_preserves_payload_status_and_streams(packet, code):
    probe = ('import os, pathlib, sys; '
             'assert not pathlib.Path("../checks/probe/command.json").exists(); '
             'print(os.getcwd()); print("probe stderr", file=sys.stderr); '
             f'sys.exit({code})')
    payload = [sys.executable, '-c', probe, '--receipt', 'payload-owned-option']
    result = invoke(packet, ['--receipt', 'checks/probe/command.json', *payload])
    assert result.returncode == code, result.stderr
    assert result.stdout.strip() == str(packet / 'WORK/repo')
    assert 'probe stderr' in result.stderr
    row = json.loads((packet / 'WORK/checks/probe/command.json').read_text())
    assert row['schema'] == 'arcpuzzles-run-command-v1'
    assert row['status'] == 'completed'
    assert row['returncode'] == code
    assert row['payload']['argv'] == payload
    assert row['payload']['expected_cwd'] == str(packet / 'WORK/repo')
    assert row['delegated']['cwd'] == str(packet / 'WORK')
    assert row['delegated']['argv'][1] == str(packet / 'WORK/run_with_racket.py')
    assert row['invocation']['cwd'] == str(packet.parent)
    assert row['evidence_directory'] == 'checks/probe'
    assert row['elapsed_seconds'] >= 0
    assert not list((packet / 'WORK/checks/probe').glob('*.tmp'))


@pytest.mark.parametrize('target', ['../escape.json', '/tmp/escape.json', 'repo/source.json', 'checks/../source.json'])
def test_unsafe_receipt_path_prevents_child_execution(packet, target):
    result = invoke(packet, ['--receipt', target, sys.executable, '-c', 'print("CHILD RAN")'])
    assert result.returncode == 2
    assert 'CHILD RAN' not in result.stdout
    assert 'receipt' in result.stderr.lower()


@pytest.mark.parametrize('kind', ['existing', 'symlink'])
def test_receipt_refuses_existing_evidence_and_symlink_paths(packet, kind):
    checks = packet / 'WORK/checks'
    checks.mkdir()
    if kind == 'existing':
        (checks / 'command.json').write_text('retained evidence')
        target = 'checks/command.json'
    else:
        (checks / 'linked').symlink_to(packet.parent, target_is_directory=True)
        target = 'checks/linked/command.json'
    result = invoke(packet, ['--receipt', target, sys.executable, '-c', 'print("CHILD RAN")'])
    assert result.returncode == 2
    assert 'CHILD RAN' not in result.stdout
    if kind == 'existing':
        assert (checks / 'command.json').read_text() == 'retained evidence'


def test_receipt_publication_conflict_does_not_overwrite_or_change_exit(packet):
    probe = 'from pathlib import Path; Path("../checks/command.json").write_text("other writer"); raise SystemExit(7)'
    result = invoke(packet, ['--receipt', 'checks/command.json', sys.executable, '-c', probe])
    assert result.returncode == 7
    assert (packet / 'WORK/checks/command.json').read_text() == 'other writer'
    assert 'receipt' in result.stderr.lower()
    assert 'not written' in result.stderr.lower()


def test_run_without_receipt_keeps_existing_execution(packet):
    result = invoke(packet, [sys.executable, '-c', 'print("unchanged"); raise SystemExit(7)'])
    assert result.returncode == 7
    assert result.stdout.strip() == 'unchanged'
    assert not (packet / 'WORK/checks').exists()


def test_setup_failure_receipt_does_not_claim_payload_started(packet):
    (packet / 'WORK/setup_racket.py').write_text('def ensure_racket(): raise RuntimeError("setup unavailable")\n')
    result = invoke(packet, ['--receipt', 'checks/setup.json', sys.executable, '-c', 'print("CHILD RAN")'])
    assert result.returncode == 1
    assert 'CHILD RAN' not in result.stdout
    row = json.loads((packet / 'WORK/checks/setup.json').read_text())
    assert row['returncode'] == 1
    assert 'execs the payload after setup' in row['exit_scope']
    assert 'expected_cwd' in row['payload']
    assert 'cwd' not in row['payload']


@pytest.mark.parametrize('flag', ['--help', '-h'])
def test_run_help_explains_controller_paths_without_launching(packet, flag):
    (packet / 'WORK/run_with_racket.py').write_text('raise RuntimeError("launcher must not run")')
    result = invoke(packet, [flag])
    assert result.returncode == 0, result.stderr
    assert '--receipt checks/NAME/command.json' in result.stdout
    assert 'relative to WORK' in result.stdout
    assert 'WORK/repo' in result.stdout
    assert '../checks/NAME' in result.stdout
    assert not (packet / 'WORK/checks').exists()


def test_payload_help_remains_delegated(packet):
    result = invoke(packet, [sys.executable, '-c', 'import sys; print(sys.argv[1])', '--help'])
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '--help'


@pytest.mark.parametrize('command, code', [('export', 0), ('verify', 7)])
def test_preview_receipt_records_actual_command_cwd_and_exit(packet, command, code):
    (packet / 'WORK/preview_public.py').write_text(
        'import os, sys\nprint(os.getcwd())\nprint(sys.argv[1:])\n'
        f'raise SystemExit({code})\n')
    result = subprocess.run(
        [sys.executable, str(packet / 'review.py'), 'preview-public',
         '--receipt', 'checks/preview-command.json', command, '--fixture'],
        cwd=packet.parent, text=True, capture_output=True, timeout=10)
    assert result.returncode == code, result.stderr
    assert str(packet / 'WORK/repo') in result.stdout
    assert "['" + command + "', '--fixture']" in result.stdout
    row = json.loads((packet / 'WORK/checks/preview-command.json').read_text())
    assert row['returncode'] == code
    assert row['delegated']['cwd'] == str(packet / 'WORK/repo')
    assert row['delegated']['argv'][1:] == [str(packet / 'WORK/preview_public.py'), command, '--fixture']
    assert row['payload']['argv'] == row['delegated']['argv']
    assert row['exit_scope'] == 'preview_public.py'
    assert 'setup' not in ' '.join(row['limits'])


@pytest.mark.parametrize('target', ['checks/../source.json', 'repo/source.json'])
def test_preview_unsafe_receipt_prevents_execution(packet, target):
    (packet / 'WORK/preview_public.py').write_text('print("CHILD RAN")\n')
    result = subprocess.run(
        [sys.executable, str(packet / 'review.py'), 'preview-public',
         '--receipt', target, 'export'],
        cwd=packet.parent, text=True, capture_output=True, timeout=10)
    assert result.returncode == 2
    assert 'CHILD RAN' not in result.stdout


@pytest.mark.parametrize('options', [
    ['--timeout', '2', '--receipt', 'checks/bounded.json'],
    ['--receipt', 'checks/bounded.json', '--timeout', '2'],
])
def test_explicit_timeout_preserves_payload_arguments_and_records_budget(packet, options):
    result = invoke(packet, [*options, sys.executable, '-c',
                            'import sys; print(sys.argv[1:])', '--timeout', 'payload-value'])
    assert result.returncode == 0, result.stderr
    assert "['--timeout', 'payload-value']" in result.stdout
    row = json.loads((packet / 'WORK/checks/bounded.json').read_text())
    assert row['timeout_seconds'] == 2
    assert row['timed_out'] is False


@pytest.mark.parametrize('budget', ['0', '-1', 'nan', 'inf', 'nonsense'])
def test_invalid_timeout_never_launches_payload(packet, budget):
    result = invoke(packet, ['--timeout', budget, sys.executable, '-c', 'print("CHILD RAN")'])
    assert result.returncode == 2
    assert 'CHILD RAN' not in result.stdout
    assert 'timeout' in result.stderr.lower()


def test_timeout_receipt_and_group_cleanup(packet):
    probe = ('import subprocess, sys, time; '
             'subprocess.Popen([sys.executable, "-c", '
             '"import time; from pathlib import Path; time.sleep(1); Path(\'late-child\').write_text(\'bad\')"]); '
             'print("started", flush=True); time.sleep(10)')
    result = invoke(packet, ['--timeout', '0.3', '--receipt', 'checks/timeout.json', sys.executable, '-c', probe])
    assert result.returncode == 124, result.stderr
    assert 'started' in result.stdout
    row = json.loads((packet / 'WORK/checks/timeout.json').read_text())
    assert row['status'] == 'timed_out'
    assert row['timed_out'] is True
    assert row['timeout_seconds'] == 0.3
    assert row['returncode'] == 124
    import time
    time.sleep(1.1)
    assert not (packet / 'WORK/repo/late-child').exists()
