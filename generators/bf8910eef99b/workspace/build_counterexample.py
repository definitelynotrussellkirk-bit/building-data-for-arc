"""Build the retained complete-stamp clipping counterexample with Racket truth."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import (RIVALS, load_generator, oracle_output, racket_outputs,
                             witness_input)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    generator_path = Path(args.generator or Path(__file__).resolve().parents[1] / "generator.py")
    grid = witness_input()
    if module.self_check(grid):
        raise AssertionError(module.self_check(grid))
    racket = racket_outputs([grid])[0]
    independent = oracle_output(grid)
    rival = RIVALS["complete_stamps_only"](grid)
    if racket != independent or rival == racket:
        raise AssertionError("counterexample does not separate authority and rival")
    report = {
        "schema": "bf8910eef99b-counterexample-v1",
        "task_id": "bf8910eef99b",
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "input": grid,
        "racket_output": racket,
        "independent_python_output": independent,
        "rival_name": "complete_stamps_only",
        "rival_output": rival,
        "validator_errors": module.self_check(grid),
        "claim": "The canonical rule keeps the visible part of a clipped 2x2 stamp; the rival drops that stamp entirely.",
        "command": "python3 run_with_racket.py python3 generators/bf8910eef99b/workspace/build_counterexample.py --out ../checks/counterexample.json",
        "working_directory": "WORK",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
