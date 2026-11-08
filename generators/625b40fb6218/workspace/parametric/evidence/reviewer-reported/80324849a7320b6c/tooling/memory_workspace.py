#!/usr/bin/env python3
"""Bounded command transport for an ALREADY CONFINED memory-backed workspace.

This helper does not create a sandbox. Launch its server inside the intended
bwrap confinement; expose only its mode-0600 Unix socket to the client.
Requests: {"argv": ["python", "script.py"], "cwd": "/tmp/work", "timeout": 120}
Control requests: {"op": "ping"} and {"op": "shutdown"}.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time

MAX_REQUEST = 8 * 1024 * 1024
MAX_OUTPUT = 8 * 1024 * 1024
MAX_RESPONSE = 6 * MAX_OUTPUT + 16384
MAX_TIMEOUT = 600


def encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode() + b"\n"


def terminate(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_request(request):
    if not isinstance(request, dict):
        raise ValueError("Request must be an object")
    if set(request) - {"op", "argv", "cwd", "timeout"}:
        raise ValueError("Unknown request fields")
    if request.get("op", "exec") != "exec":
        raise ValueError("Unknown operation")
    argv = request.get("argv")
    if (not isinstance(argv, list) or not argv or len(argv) > 4096
            or any(not isinstance(x, str) or "\0" in x for x in argv)
            or not argv[0]):
        raise ValueError("argv must be a nonempty string list without NUL bytes")
    cwd = request.get("cwd", "/tmp")
    if not isinstance(cwd, str) or not os.path.isabs(cwd) or "\0" in cwd:
        raise ValueError("cwd must be an absolute path without NUL bytes")
    timeout = request.get("timeout", 120)
    if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or not 0 < timeout <= MAX_TIMEOUT):
        raise ValueError("timeout must be greater than zero and at most 600 seconds")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR="/tmp")
    began = time.monotonic()
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True, shell=False)
    chunks = {"stdout": [], "stderr": []}
    lock = threading.Lock()
    retained = 0
    exceeded = threading.Event()

    def drain(name, pipe):
        nonlocal retained
        try:
            while True:
                block = pipe.read(65536)
                if not block:
                    break
                with lock:
                    keep = min(len(block), MAX_OUTPUT - retained)
                    if keep:
                        chunks[name].append(block[:keep])
                        retained += keep
                    if keep < len(block):
                        exceeded.set()
                if exceeded.is_set():
                    terminate(process)
        finally:
            pipe.close()

    pumps = [threading.Thread(target=drain, args=(name, getattr(process, name)), daemon=True)
             for name in ("stdout", "stderr")]
    for pump in pumps:
        pump.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate(process)
        process.wait()
    finally:
        # A shell can exit while its children still own the output pipes.
        terminate(process)
        for pump in pumps:
            pump.join(timeout=2)
    with lock:
        stdout = b"".join(chunks["stdout"]).decode("utf-8", errors="replace")
        stderr = b"".join(chunks["stderr"]).decode("utf-8", errors="replace")
    return {"returncode": process.returncode, "stdout": stdout, "stderr": stderr,
            "timed_out": timed_out, "output_limit_exceeded": exceeded.is_set(),
            "elapsed_seconds": round(time.monotonic() - began, 6)}


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, path, jobs):
        self.slots = threading.BoundedSemaphore(jobs)
        super().__init__(path, Handler)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise ValueError("Request missing newline or exceeds 8 MiB")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ValueError("Request must be an object")
            op = request.get("op", "exec")
            if op in {"ping", "shutdown"}:
                if set(request) != {"op"}:
                    raise ValueError("Control requests only accept op")
                response = {"ok": True, "op": op}
                if op == "shutdown":
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
            elif self.server.slots.acquire(blocking=False):
                try:
                    response = run_request(request)
                finally:
                    self.server.slots.release()
            else:
                response = {"error": "Server busy; retry after an active command finishes"}
        except Exception as exc:
            response = {"error": f"{type(exc).__name__}: {exc}"}
        try:
            self.wfile.write(encode(response))
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            pass


def serve(path, jobs):
    path = Path(path).absolute()
    # Refuse existing sockets too: do not steal another server's endpoint.
    if path.exists() or path.is_symlink():
        raise ValueError(f"Socket path already exists: {path}")
    previous_umask = os.umask(0o077)
    server = None
    try:
        server = Server(str(path), jobs)
        os.chmod(path, 0o600)
    finally:
        os.umask(previous_umask)
    try:
        print(json.dumps({"ready": True, "socket": str(path), "pid": os.getpid()}), flush=True)
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
        path.unlink(missing_ok=True)


def client(path):
    raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
    if len(raw) > MAX_REQUEST:
        raise ValueError("Request exceeds 8 MiB")
    request = json.loads(raw)
    payload = encode(request)
    if len(payload) > MAX_REQUEST:
        raise ValueError("Encoded request exceeds 8 MiB")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(MAX_TIMEOUT + 45)
        connection.connect(str(path))
        connection.sendall(payload)
        with connection.makefile("rb") as reader:
            response = reader.readline(MAX_RESPONSE + 1)
    if not response or len(response) > MAX_RESPONSE or not response.endswith(b"\n"):
        raise ValueError("Incomplete or oversized response")
    json.loads(response)
    sys.stdout.buffer.write(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("server", "client"))
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8:
        parser.error("--jobs must be between 1 and 8")
    if args.command == "server":
        serve(args.socket, args.jobs)
    else:
        client(args.socket)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        raise SystemExit(2)
