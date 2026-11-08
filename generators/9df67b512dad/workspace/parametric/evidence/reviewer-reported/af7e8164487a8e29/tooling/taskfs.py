#!/usr/bin/env python3
"""Local command bridge for an explicitly approved private task filesystem.

The server does not create namespaces or mounts. Start it inside an approved
task session. The UNIX socket is private to the current user. No network API.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import socketserver
import subprocess
import sys


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            request = json.loads(self.rfile.readline(1024 * 1024))
            argv = request["argv"]
            if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
                raise ValueError("argv must be a nonempty string list")
            cwd = (self.server.root / request.get("cwd", ".")).resolve()
            if not cwd.is_relative_to(self.server.root):
                raise ValueError("cwd escapes the task filesystem")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(self.server.root / "tmp"))
            env.update(request.get("env", {}))
            with subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, errors="replace", bufsize=1) as process:
                for line in process.stdout:
                    self.wfile.write((json.dumps({"output": line}) + "\n").encode())
                    self.wfile.flush()
                status = process.wait()
            self.wfile.write((json.dumps({"exit_code": status}) + "\n").encode())
        except Exception as error:
            self.wfile.write((json.dumps({"error": str(error), "exit_code": 125}) + "\n").encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--root", required=True)
    run = commands.add_parser("run")
    run.add_argument("--cwd", default=".")
    run.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == "serve":
        root = Path(args.root).resolve(strict=True)
        (root / "tmp").mkdir(exist_ok=True)
        if Path(args.socket).exists():
            raise FileExistsError("Refusing to replace an existing socket")
        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = True
        try:
            with Server(args.socket, Handler) as server:
                os.chmod(args.socket, 0o600)
                server.root = root
                print(json.dumps({"status": "ready", "root": str(root),
                                  "mount_namespace": os.readlink("/proc/self/ns/mnt")}), flush=True)
                server.serve_forever()
        finally:
            Path(args.socket).unlink(missing_ok=True)
    else:
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(args.socket)
            client.sendall((json.dumps({"cwd": args.cwd, "argv": argv}) + "\n").encode())
            with client.makefile("r") as result:
                for line in result:
                    event = json.loads(line)
                    if "output" in event:
                        print(event["output"], end="", flush=True)
                    if "error" in event:
                        print(event["error"], file=sys.stderr)
                    if "exit_code" in event:
                        return event["exit_code"]
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
