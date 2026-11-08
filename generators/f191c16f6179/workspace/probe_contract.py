#!/usr/bin/env python3
"""Probe joint exact controls from returned pixels, in a library or runtime.

Example (packet root):
  python3 review.py run python3 generators/f191c16f6179/workspace/probe_contract.py \
      --full-grid --seeds 2 --out ../checks/joint-controls.json

This task-local authoring probe does not label examples or claim lesson quality.
The shared lesson-census command remains the Racket-backed lesson check.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root

TASK = "f191c16f6179"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-grid", action="store_true", help="All heights/widths 5..16 instead of boundaries")
    parser.add_argument("--seeds", type=int, default=2, help="Consecutive seeds starting at zero")
    parser.add_argument("--starts", type=int, default=3, help="Sample indices starting at zero")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")
    if args.out.exists():
        parser.error("--out must be a new file; preserve earlier results")
    root = find_root(__file__)
    source = next(path for path in (
        root / "generators" / TASK / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ) if path.is_file())
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("probed_diagonal_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    dims = list(range(5, 17)) if args.full_grid else [5, 16]
    bands = ["easy", "medium", "hard"]
    total = len(bands) * len(dims)**2 * 5 * args.seeds * args.starts
    report = {
        "schema": "arcpuzzles-task-joint-controls-v1", "task_id": TASK,
        "generator_sha256": source_hash, "rule_hash": getattr(gen, "RULE_HASH", None),
        "argv": sys.argv, "cwd": str(Path.cwd()),
        "scope": {"bands": bands, "heights": dims, "widths": dims,
                  "pairs": [1, 2, 3, 4, 5], "seed_range": [0, args.seeds-1],
                  "sample_index_range": [0, args.starts-1]},
        "requested": total, "completed": 0, "passed": 0,
        "failure_counts": {}, "first_failures": [],
        "guarded_inputs": 0, "unique_inputs": 0,
        "label_verification": "not_performed", "status": "running",
    }
    errors, seen = Counter(), set()
    start_time = time.monotonic()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    def checkpoint():
        report["failure_counts"] = dict(errors)
        report["unique_inputs"] = len(seen)
        report["elapsed_seconds"] = round(time.monotonic()-start_time, 3)
        report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        args.out.write_text(json.dumps(report, indent=2) + "\n")

    for band, h, w, pairs, seed, index in itertools.product(
            bands, dims, dims, range(1, 6), range(args.seeds), range(args.starts)):
        case = {"difficulty": band, "grid_h": h, "grid_w": w, "pairs": pairs,
                "seed": seed, "sample_index": index}
        failures = []
        grid = None
        try:
            grid = gen.generate(seed, index, difficulty=band, grid_h=h, grid_w=w, pairs=pairs)
            rectangular = (isinstance(grid, list) and len(grid) == h and
                           all(isinstance(row, list) and len(row) == w for row in grid))
            if not rectangular:
                failures.append("wrong_shape")
            else:
                if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
                    failures.append("invalid_cell")
                counts = Counter(cell for row in grid for cell in row if cell)
                if sum(count == 2 for count in counts.values()) != pairs:
                    failures.append("wrong_realized_pair_count")
                report["guarded_inputs"] += int(any(count == 3 for count in counts.values()))
                seen.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
                if gen.self_check(grid, difficulty=band):
                    failures.append("self_check_rejected")
                if gen.observe_overrides(grid) != {"grid_h": h, "grid_w": w, "pairs": pairs}:
                    failures.append("observer_mismatch")
        except Exception as exc:
            failures.append(type(exc).__name__)
            case["exception"] = str(exc)
        report["completed"] += 1
        if failures:
            errors.update(failures)
            if len(report["first_failures"]) < 20:
                report["first_failures"].append({"case": case, "failures": failures, "grid": grid})
        else:
            report["passed"] += 1
        if report["completed"] % 500 == 0:
            checkpoint()
            print(f"{report['completed']}/{total} draws; {report['passed']} passed", flush=True)
    report["status"] = "passed" if not errors else "failed"
    checkpoint()
    if not report["source_unchanged"]:
        report["status"] = "source_changed_during_run"
        checkpoint()
    print(json.dumps({key: report[key] for key in (
        "status", "requested", "completed", "passed", "failure_counts",
        "unique_inputs", "source_unchanged", "elapsed_seconds")}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
