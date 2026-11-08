#!/usr/bin/env python3
"""Prepare a fresh selected runtime and retain an exact probe process receipt.

Invoke through review.py run so the packet supplies its Python/Racket runtime.
The output directory must be new. No generator or shared source is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(f"Output must be new: {out}")
    out.mkdir(parents=True)
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    probe = Path(__file__).resolve().with_name("probe.py")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-canonical-review-") as temp:
        runtime = Path(temp)
        manifest = prepare_runtime(Catalog(repo), runtime, "7a37505e7bd0")
        (out / "RUNTIME_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        argv = [sys.executable, str(probe), "--repo", str(repo), "--runtime",
                str(runtime), "--out", str(out / "results")]
        result = subprocess.run(argv, cwd=repo, text=True, capture_output=True)
    (out / "stdout.log").write_text(result.stdout)
    (out / "stderr.log").write_text(result.stderr)
    receipt = {"argv": argv, "cwd": str(repo), "rc": result.returncode,
               "wrapper_payload_argv": list(sys.orig_argv),
               "elapsed_seconds": time.monotonic() - start,
               "probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
               "stdout": "stdout.log", "stderr": "stderr.log",
               "runtime_manifest": "RUNTIME_MANIFEST.json",
               "runtime_retention": "Temporary copied runtime removed after execution; complete source manifest and labelled evidence retained."}
    (out / "command.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
