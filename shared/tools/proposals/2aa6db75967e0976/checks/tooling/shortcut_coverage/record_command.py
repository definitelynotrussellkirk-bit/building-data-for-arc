"""Keep bounded diagnostic commands, logs, and failures in this tool's tree."""
import json
from pathlib import Path
import shlex
import subprocess
import sys

out = Path(__file__).resolve().parent / "receipts"
out.mkdir(exist_ok=True)
label, *argv = sys.argv[1:]
cwd = Path.cwd().resolve()
result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
stdout = out / (label + ".stdout.txt")
stderr = out / (label + ".stderr.txt")
stdout.write_text(result.stdout)
stderr.write_text(result.stderr)
work = out
while work.name != "WORK" and work.parent != work:
    work = work.parent
receipt = {"argv": argv, "command": shlex.join(argv), "cwd": str(cwd), "exit_code": result.returncode,
           "stdout_log": str(stdout.relative_to(work)), "stderr_log": str(stderr.relative_to(work))}
(out / (label + ".json")).write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
sys.exit(result.returncode)
