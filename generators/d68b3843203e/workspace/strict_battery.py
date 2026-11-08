"""Run the actual strict AFTER battery, preserving source and process receipts.

The packet's arcpuzzles.check API currently passes 'before' unconditionally.
This local wrapper avoids changing shared library code or reusing stale checks.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="d68b3843203e")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    args.out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-strict-after-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(root=REPO), stage, args.task)
        command = ["bash", "scripts/run_generator_battery.sh", args.task, "after", "--fresh"]
        result = run_process(command, stage, timeout=args.timeout)
        result.update({"task_id": args.task, "phase": "after", "runtime_manifest": manifest})
        if (stage / "checks").exists():
            shutil.copytree(stage / "checks", args.out / "checks")
        (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        (args.out / "stdout.log").write_text(result["stdout"])
        (args.out / "stderr.log").write_text(result["stderr"])
        print(result["stdout"], end="")
        print(result["stderr"], file=sys.stderr, end="")
        return 124 if result["timed_out"] else result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
