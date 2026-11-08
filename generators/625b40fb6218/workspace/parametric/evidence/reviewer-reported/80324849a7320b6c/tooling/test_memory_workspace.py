"""Focused protocol and resource-bound regressions; standard library only."""
from pathlib import Path
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
HELPER = HERE / "memory_workspace.py"


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="transport-test-", dir=HERE)
        cls.sock = Path(cls.temp.name) / "test.sock"
        cls.server = subprocess.Popen(
            [sys.executable, "-B", str(HELPER), "server", "--socket", str(cls.sock)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ready = json.loads(cls.server.stdout.readline())
        if not ready.get("ready"):
            raise RuntimeError("Server did not become ready")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.request({"op": "shutdown"})
            cls.server.wait(timeout=5)
        finally:
            if cls.server.poll() is None:
                cls.server.kill()
                cls.server.wait()
            cls.server.stdout.close()
            cls.server.stderr.close()
            cls.temp.cleanup()

    @classmethod
    def request(cls, value):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
            channel.settimeout(10)
            channel.connect(str(cls.sock))
            channel.sendall(json.dumps(value).encode() + b"\n")
            with channel.makefile("rb") as stream:
                return json.loads(stream.readline())

    def test_ping_and_private_socket(self):
        self.assertEqual(self.request({"op": "ping"}), {"ok": True, "op": "ping"})
        self.assertEqual(stat.S_IMODE(self.sock.stat().st_mode), 0o600)

    def test_exec_client_stdout_stderr_and_environment(self):
        request = {"argv": [sys.executable, "-c",
                   "import os,sys; print(os.getcwd()); print(os.environ['TMPDIR']); "
                   "print(os.environ['PYTHONDONTWRITEBYTECODE']); print('err',file=sys.stderr)"],
                   "cwd": self.temp.name}
        completed = subprocess.run(
            [sys.executable, "-B", str(HELPER), "client", "--socket", str(self.sock)],
            input=json.dumps(request), capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], self.temp.name + "\n/tmp\n1\n")
        self.assertEqual(result["stderr"], "err\n")

    def test_rejects_bad_request_and_timeout(self):
        for request in ({"argv": "echo hello"}, {"argv": ["echo"], "timeout": True},
                        {"argv": ["echo"], "timeout": 601},
                        {"argv": ["echo"], "cwd": "relative"},
                        {"op": "ping", "argv": ["echo"]}):
            with self.subTest(request=request):
                self.assertIn("error", self.request(request))

    def test_timeout_kills_process_group(self):
        result = self.request({"argv": [sys.executable, "-c", "import time; time.sleep(30)"],
                               "timeout": 0.1})
        self.assertTrue(result["timed_out"])
        self.assertLess(result["returncode"], 0)
        self.assertLess(result["elapsed_seconds"], 5)

    def test_output_bound_terminates_flood(self):
        result = self.request({"argv": [sys.executable, "-c",
                               "import sys,time; sys.stdout.buffer.write(b'x'*(9*1024*1024)); "
                               "sys.stdout.flush(); time.sleep(30)"], "timeout": 5})
        self.assertTrue(result["output_limit_exceeded"])
        self.assertLessEqual(len(result["stdout"]) + len(result["stderr"]), 8*1024*1024)
        self.assertFalse(result["timed_out"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
