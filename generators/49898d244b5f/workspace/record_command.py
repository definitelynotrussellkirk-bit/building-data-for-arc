#!/usr/bin/env python3
"""Record an argv command in a new evidence directory using only stdlib.

Usage: record_command.py --cwd PATH --out NEW_DIRECTORY [--timeout SECONDS]
                         [--hash-input FILE ...] -- COMMAND ARGS
Hash-input paths are relative to the child cwd; out is relative to caller cwd.
Writes receipt.json, stdout.log and stderr.log. Exit: child status (signals use
128+signal), 124 timeout, 3 changed input, 2 recorder/launch error. Never reuse
an output directory. On POSIX, timeout kills the child's new process group;
elsewhere cleanup is limited to the direct child. Environment metadata is
allowlisted; the command itself inherits the existing environment unchanged.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ENV_KEYS = ('TMPDIR', 'PYTHONNOUSERSITE', 'PYTHONHASHSEED', 'PYTHONPATH', 'RACKET_PATH')


def diagnostic(exc):
    return {'type': type(exc).__name__, 'message': str(exc)}


def snapshot(path):
    try:
        digest = hashlib.sha256()
        size = 0
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
                size += len(chunk)
        return {'sha256': digest.hexdigest(), 'bytes': size}
    except OSError as exc:
        return {'sha256': None, 'error': diagnostic(exc)}


def stop(process):
    """Kill the entire new group on POSIX, including surviving descendants."""
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    return process.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--timeout', type=float)
    parser.add_argument('--hash-input', action='append', default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if not args.command or args.command[0] != '--' or len(args.command) < 2:
        parser.error('supply -- COMMAND ARGS')
    if args.timeout is not None and (not math.isfinite(args.timeout) or args.timeout <= 0):
        parser.error('--timeout must be finite and positive')
    command = args.command[1:]
    out = Path(args.out).resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        print(f'cannot create new evidence directory: {exc}', file=sys.stderr)
        return 2
    started = time.monotonic()
    cwd = Path(args.cwd).resolve()
    receipt = {
        'schema': 'evidence-command-v1', 'argv': command, 'cwd': str(cwd),
        'started_at': datetime.now(timezone.utc).isoformat(),
        'timeout_seconds': args.timeout, 'timed_out': False,
        'child_exit_code': None, 'exit_code': 2, 'error': None,
        'source_changed': False, 'hash_inputs': [],
        'cleanup_scope': 'process_group' if os.name == 'posix' else 'child',
        'environment': {key: os.environ[key] for key in ENV_KEYS if key in os.environ},
        'recorder': {'executable': sys.executable, 'argv': list(sys.argv),
                     'path': str(Path(__file__).resolve()),
                     'sha256': snapshot(Path(__file__).resolve())['sha256']},
    }
    process = None
    try:
        with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
            for name in args.hash_input:
                path = Path(name)
                path = (cwd / path).resolve() if not path.is_absolute() else path.resolve()
                receipt['hash_inputs'].append({'path': str(path), 'before': snapshot(path)})
            if any(entry['before']['sha256'] is None for entry in receipt['hash_inputs']):
                raise ValueError('cannot hash every input before execution')
            process = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                       start_new_session=os.name == 'posix')
            receipt['child_pid'] = process.pid
            try:
                receipt['child_exit_code'] = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                receipt['timed_out'] = True
                receipt['child_exit_code'] = stop(process)
            child_exit = receipt['child_exit_code']
            receipt['exit_code'] = 124 if receipt['timed_out'] else (
                child_exit if child_exit >= 0 else 128 - child_exit)
    except (Exception, KeyboardInterrupt) as exc:
        receipt['error'] = diagnostic(exc)
        if process is not None:
            receipt['child_exit_code'] = stop(process)
        receipt['exit_code'] = 2
    finally:
        for entry in receipt['hash_inputs']:
            entry['after'] = snapshot(Path(entry['path']))
        receipt['source_changed'] = any(entry['before'] != entry['after']
                                        for entry in receipt['hash_inputs'])
        if receipt['source_changed'] and not receipt['timed_out'] and receipt['child_exit_code'] is not None:
            receipt['exit_code'] = 3
        receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
        receipt['elapsed_seconds'] = round(time.monotonic() - started, 6)
        temporary = out / 'receipt.json.tmp'
        temporary.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        temporary.replace(out / 'receipt.json')
    return receipt['exit_code']


if __name__ == '__main__':
    sys.exit(main())
