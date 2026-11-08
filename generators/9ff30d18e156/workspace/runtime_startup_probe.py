"""Diagnose child-startup assumptions without changing shared timeout policy.

Run through packet_root/run_with_racket.py so repository imports are available.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from arcpuzzles.runtime import run_process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    records = []
    for options in ([], ['-S']):
        for _ in range(3):
            argv = [sys.executable, *options, '-c', "print('READY',flush=True)"]
            start = time.monotonic()
            result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
            records.append({'probe':'startup', 'argv':argv, 'elapsed_seconds':time.monotonic()-start,
                            'exit_code':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr})
    with tempfile.TemporaryDirectory(prefix='arc-startup-probe-') as directory:
        for options, timeout in (([], .2), ([], 1.0), (['-S'], .2)):
            chunks = []
            result = run_process([sys.executable, *options, '-c',
                                  "import time; print('RUN unfinished',flush=True); time.sleep(30)"],
                                 Path(directory), timeout=timeout, on_output=chunks.append)
            records.append({'probe':'streaming_timeout', 'timeout_seconds':timeout,
                            'callback_chunks':chunks, **result})
    args.out.write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(records, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
