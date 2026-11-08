"""Bounded controller/pipe diagnosis; no task generation or runtime edits."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

from arcpuzzles.runtime import run_process


def main(root):
    rows = []
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-pass35-') as temp:
        directory = Path(temp)
        child = 'import time; time.sleep(1.0)'
        for name, leaked, timeout, streaming in (
            ('direct_exit', False, 3, True),
            ('inherited_pipe_natural_close', True, 3, True),
            ('inherited_pipe_bounded_timeout_streaming', True, .2, True),
            ('inherited_pipe_bounded_timeout_capture', True, .2, False),
        ):
            code = 'import subprocess,sys; '
            if leaked:
                code += f'subprocess.Popen([sys.executable,"-c",{child!r}]); '
            code += 'print("CHILD_COMPLETED",flush=True)'
            chunks = []; before = time.monotonic()
            result = run_process([sys.executable, '-c', code], directory, timeout=timeout,
                                 on_output=chunks.append if streaming else None)
            elapsed = time.monotonic() - before
            assert result['exit_code'] == 0, result
            assert result['timed_out'] == (timeout == .2), result
            assert result['stdout'].strip() == 'CHILD_COMPLETED', result
            assert elapsed < 5, elapsed
            if name == 'inherited_pipe_natural_close':
                assert elapsed >= .8, elapsed
            rows.append(dict(case=name, elapsed_seconds=elapsed, **result))
        # Exercise the exact current battery child/receipt/wait block with a
        # constant-time stand-in for the checker. No matrix or generator runs.
        controller = root / 'shared/tools/run_generator_battery.sh'
        source = controller.read_text()
        start = source.index("  bash -c '\n    timeout -k")
        end = source.index('  CHILD_PID=""', start) + len('  CHILD_PID=""')
        fragment = source[start:end]
        setup = '''set -m
cmd='printf PASS'; log=stage.log; receipt=stage.receipt
GEN_SHA=fixture; RUN_ID=fixture; cap=2; kill_after=1; TIME_BUDGET=2; code=0
'''
        result = run_process(['bash', '-c', setup + fragment + '\nprintf "CONTROLLER_COMPLETED\\n"'],
                             directory, timeout=5, on_output=lambda text: None)
        receipt = json.loads((directory / 'stage.receipt').read_text())
        assert result['exit_code'] == 0 and not result['timed_out'], result
        assert result['stdout'].strip() == 'CONTROLLER_COMPLETED', result
        assert receipt['exit'] == 0 and receipt['timed_out'] is False, receipt
        rows.append(dict(case='exact_battery_child_receipt_wait_fragment',
                         fragment_sha256=hashlib.sha256(fragment.encode()).hexdigest(),
                         receipt=receipt, **result))
    return dict(status='all_five_bounded_probes_passed', checks=rows,
                limits='Synthetic inherited-pipe behavior is reproducible; it does not identify the cause of the retained reviewer interruption.')


if __name__ == '__main__':
    print(json.dumps(main(Path(sys.argv[1]).resolve()), indent=2))
