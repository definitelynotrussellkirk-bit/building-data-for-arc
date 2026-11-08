"""Diagnose interpreter-startup sensitivity without changing shared runtime code.

Run through run_with_racket.py from the review packet. All children are stopped
by the existing process-group timeout implementation. This is a diagnostic,
not a replacement passing test or a shared-runtime fix.
"""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import time

from arcpuzzles.runtime import run_process


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("refusing to overwrite existing evidence")
    rows = []
    code = "import time; print('RUN unfinished', flush=True); time.sleep(30)"
    with tempfile.TemporaryDirectory(prefix="runtime-startup-diagnosis-") as tmp:
        for flags, timeout in [((), 0.2), (("-S",), 0.2), ((), 1.0), (("-S",), 1.0)]:
            for streamed in (False, True):
                chunks = []
                start = time.monotonic()
                command = [sys.executable, *flags, "-c", code]
                result = run_process(command, Path(tmp), timeout=timeout,
                                     on_output=chunks.append if streamed else None)
                rows.append({"timeout_seconds": timeout, "streamed": streamed,
                             "actual_cwd": tmp, "argv": command, "result": result,
                             "callback_text": "".join(chunks),
                             "elapsed_seconds": time.monotonic() - start})
    source = Path(inspect.getsourcefile(run_process))
    payload = {"schema": "arcpuzzles-runtime-startup-diagnostic-v1",
               "diagnostic_only": True, "runtime_modified": False,
               "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
               "runtime_path": str(source),
               "runtime_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "python_version": sys.version, "rows": rows,
               "limitation": "Observation in this environment; -S changes startup, not the timeout API contract."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    for row in rows:
        print(json.dumps({"argv": row["argv"], "timeout": row["timeout_seconds"],
                          "streamed": row["streamed"], "stdout": row["result"]["stdout"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
