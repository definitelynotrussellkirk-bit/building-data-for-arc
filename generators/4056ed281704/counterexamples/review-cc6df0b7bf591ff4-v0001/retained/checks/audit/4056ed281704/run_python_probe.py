from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess

work = Path("/tmp/arc_review_121953_mount/WORK")
out = work / "checks/audit/4056ed281704"
exe = work / ".venv/bin/python"
argv = [str(exe), str(out / "probe.py")]
env = dict(os.environ)
env["TMPDIR"] = "/tmp/arc_review_121953_mount/tmp"
env["PYTHONPATH"] = str(work / "repo/shared/runtime")
env["PYTHONDONTWRITEBYTECODE"] = "1"
started = datetime.now(timezone.utc).isoformat()
result = subprocess.run(argv, cwd=work / "repo", env=env, capture_output=True, text=True, timeout=60)
(out / "probe.stdout.txt").write_text(result.stdout)
(out / "probe.stderr.txt").write_text(result.stderr)
receipt = {
    "kind": "bounded_python_public_helper_audit",
    "task_id": "4056ed281704",
    "argv": argv, "cwd": str(work / "repo"),
    "environment": {k:env[k] for k in ("TMPDIR", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
    "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
    "exit_code": result.returncode,
    "stdout": "checks/audit/4056ed281704/probe.stdout.txt",
    "stderr": "checks/audit/4056ed281704/probe.stderr.txt",
    "probe_sha256": hashlib.sha256((out / "probe.py").read_bytes()).hexdigest(),
    "generator_sha256": hashlib.sha256((work / "repo/generators/4056ed281704/generator.py").read_bytes()).hexdigest(),
}
with (out / "probe-command.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result.stdout)
if result.stderr:
    print(result.stderr)
print("exit_code=" + str(result.returncode))
raise SystemExit(result.returncode)
