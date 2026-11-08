"""Bounded POSIX subprocess lifecycle for verifier and kernel orchestration.

Does not treat a process group as a security sandbox. Designed for controlled
program-synthesis candidates and trusted harness commands, not hostile code.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import os
import signal
import subprocess
import tempfile
import time


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    seconds: float
    failure: str | None
    pid: int


def run_bounded(command: list[str], *, timeout: float, env: dict | None = None,
                cwd: str | None = None, input_text: str = "",
                max_output_bytes: int = 4 * 1024 * 1024) -> ProcessResult:
    """Enforce a deadline even when the child never writes a newline.

    Redirect output to temporary files so communicate() cannot allocate an
    unbounded in-memory capture. Poll and kill on combined output quota; this
    permits small polling overshoot and is not a strict disk-space quota.
    """
    if os.name != "posix":
        raise RuntimeError("POSIX process groups required; refusing reduced isolation")
    if not math.isfinite(timeout) or timeout <= 0 or max_output_bytes < 1:
        raise ValueError("timeout and output quota must be finite and positive")
    started = time.monotonic()
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(input_text.encode()); inp.seek(0)
        process = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err,
                                   env=env, cwd=cwd, start_new_session=True)
        failure = None
        try:
            while process.poll() is None:
                if time.monotonic() - started >= timeout:
                    failure = "timeout"
                    break
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > max_output_bytes:
                    failure = "output_limit"
                    break
                time.sleep(0.01)
        finally:
            # Also clean up leftover same-group children after a normal exit.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > max_output_bytes:
            failure = failure or "output_limit"
        out.seek(0); err.seek(0)
        stdout = out.read(max_output_bytes).decode("utf-8", errors="replace")
        stderr = err.read(max_output_bytes).decode("utf-8", errors="replace")
    return ProcessResult(process.returncode, stdout, stderr, time.monotonic() - started, failure, process.pid)
