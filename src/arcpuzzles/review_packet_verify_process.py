"""Bounded command receipts for the maintainer's cold packet check."""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def run_command(argv, *, cwd, env, timeout, log_root, name, max_output_bytes=8 * 1024 * 1024):
    if (os.name != 'posix' or not math.isfinite(timeout) or timeout <= 0
            or type(max_output_bytes) is not int or max_output_bytes < 1
            or not re.fullmatch('[A-Za-z0-9_-]+', name)):
        raise ValueError('A POSIX command, finite positive timeout, output limit and simple log name are required')
    paths = {k: Path(log_root) / (name + '.' + k) for k in ('stdout', 'stderr')}
    started = time.monotonic();failure = None;process = None
    with paths['stdout'].open('xb') as stdout, paths['stderr'].open('xb') as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                if time.monotonic() - started >= timeout:
                    failure = 'timeout';break
                if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > max_output_bytes:
                    failure = 'output_limit';break
                time.sleep(.02)
        finally:
            if process is not None:
                # These are our own process group and newly created log files.
                # File-backed output also avoids waiting on orphaned pipe handles.
                try:os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait(timeout=5)
    if sum(p.stat().st_size for p in paths.values()) > max_output_bytes:
        failure = failure or 'output_limit'
    def asset(path):
        with path.open('rb') as f:digest = hashlib.file_digest(f, 'sha256').hexdigest()
        return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}
    return {'argv': list(argv), 'cwd': str(cwd), 'exit_code': process.returncode,
            'timed_out': failure == 'timeout', 'failure': failure,
            'elapsed_seconds': time.monotonic() - started,
            **{kind: asset(path) for kind, path in paths.items()}}
