#!/usr/bin/env python3
"""Diagnose short subprocess deadlines without modifying the runtime/test.

Authoring-only probe. A completed run means evidence was captured, not that the
repository test passes. Normal startup is compared with Python's -S mode; -S is
an explanatory control, NOT a proposed production change.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('refusing to overwrite evidence')
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / 'src'))
    from arcpuzzles.runtime import run_process
    source = repo / 'src/arcpuzzles/runtime.py'
    cases = []
    for isolated in (False, True):
        for deadline in (.2, 2.0):
            for repeat in range(3):
                argv = [sys.executable] + (['-S'] if isolated else []) + [
                    '-c', "import time; print('RUN unfinished',flush=True); time.sleep(30)"]
                chunks = []
                start = time.monotonic()
                result = run_process(argv, repo, timeout=deadline, on_output=chunks.append)
                cases.append({'argv': argv, 'cwd': str(repo), 'skip_site': isolated,
                              'deadline_seconds': deadline, 'repeat': repeat,
                              'elapsed_seconds': round(time.monotonic() - start, 6),
                              'timed_out': result['timed_out'], 'exit_code': result['exit_code'],
                              'stdout': result['stdout'], 'stderr': result['stderr'],
                              'callback_text': ''.join(chunks),
                              'startup_message_captured': result['stdout'] == 'RUN unfinished\n'})
    report = {'kind': 'runtime-startup-diagnostic-not-a-test-pass',
              'runtime_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'command': {'cwd': str(Path.cwd()), 'argv': [sys.executable, *sys.argv]},
              'cases': cases}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'startup_messages_captured':
                      sum(case['startup_message_captured'] for case in cases)}))


if __name__ == '__main__':
    main()
