#!/usr/bin/env python3
"""Diagnose the 200ms streaming-timeout test without modifying shared code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo/'src'))
    from arcpuzzles.runtime import run_process
    rows = []
    startup = {}
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-timeout-probe-') as name:
        cwd = Path(name)
        for label, flags in (('normal_startup', []), ('without_site', ['-S'])):
            times = []
            for _ in range(5):
                start = time.perf_counter()
                completed = subprocess.run([sys.executable, *flags, '-c', "print('ready',flush=True)"],
                                           cwd=cwd, capture_output=True, text=True, timeout=10, check=True)
                times.append(time.perf_counter()-start)
                assert 'ready' in completed.stdout
            startup[label] = {'elapsed_seconds': times, 'median_seconds': statistics.median(times)}
            for timeout in (.2, 1.0):
                chunks = []
                command = [sys.executable, *flags, '-c', "import time; print('RUN unfinished',flush=True); time.sleep(30)"]
                result = run_process(command, cwd, timeout=timeout, on_output=chunks.append)
                rows.append({'label': label, 'timeout_seconds': timeout, 'command': command,
                             'stdout': result['stdout'], 'stderr': result['stderr'],
                             'timed_out': result['timed_out'], 'exit_code': result['exit_code'],
                             'callback_text': ''.join(chunks)})
        report = {'python': sys.version, 'runtime_cwd': name, 'runtime_removed_after_run': True,
                  'shared_runtime_sha256': hashlib.sha256((repo/'src/arcpuzzles/runtime.py').read_bytes()).hexdigest(),
                  'test_path': 'tests/test_review_runtime.py::test_streaming_timeout_retains_progress_and_stops_child',
                  'startup': startup, 'streaming_probes': rows,
                  'scope': 'Diagnostic only; no shared-source changes or altered acceptance thresholds.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
