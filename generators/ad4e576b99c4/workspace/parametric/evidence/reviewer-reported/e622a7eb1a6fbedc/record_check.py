"""Run one bounded check, preserving exact command, outputs and source hashes.

Place this helper under WORK/checks; commands execute from WORK/repo.
Example: python WORK/checks/record_check.py tests-v1 -- python -m pytest ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('label')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.label):
        parser.error('label must be a simple directory name')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or not 1 <= args.timeout <= 600:
        parser.error('supply a command and timeout 1..600 seconds')
    work = Path(__file__).resolve().parents[1]
    repo = work / 'repo'
    out = work / 'checks' / args.label
    out.mkdir(exist_ok=False)
    contract = json.loads((work / 'ASSIGNMENT.json').read_text())
    home = repo / 'generators' / contract['task_id']
    sources = [home / 'generator.py']
    sources += sorted((home / 'workspace' / 'parametric').rglob('*.py'))
    sources += sorted((home / 'tests').glob('test_parametric*.py'))
    hashes = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sources}
    began = time.monotonic()
    proc = subprocess.Popen(command, cwd=repo, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    (out / 'stdout.txt').write_text(stdout)
    (out / 'stderr.txt').write_text(stderr)
    record = dict(argv=command, cwd='repo', executed_cwd=str(repo),
                  exit_code=proc.returncode, timed_out=timed_out,
                  elapsed_seconds=round(time.monotonic() - began, 3),
                  source_sha256=hashes,
                  evidence_paths=['checks/' + args.label + '/' + name for name in ('stdout.txt', 'stderr.txt', 'command.json')],
                  canonical_rule_hash=contract['generator']['rule_hash'])
    (out / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
    results_path = work / 'RESULTS.json'
    results = json.loads(results_path.read_text())
    results.setdefault('verification_commands', []).append(record)
    results_path.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(record, sort_keys=True), flush=True)
    print(stdout[-9000:], end='')
    print(stderr[-4000:], end='')
    return 124 if timed_out else proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
