"""Replay joint shape/count/size controls from the selected source.

Run through run_with_racket.py from WORK, so the portable public helpers are
available. This checks input construction, not Racket labels or teachability.
Every failure retains the exact grid, requested controls and replay coordinates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator

TASK_ID = "f9cd85012aa8"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def observe(grid):
    """Count pixels and same-color 4-components independently of generator hooks."""
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) for r in grid):
        raise ValueError("grid must be a nonempty list of row lists")
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be Python integer colors 0..9")
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    component_colors = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack = [start]
        while stack:
            r, c = stack.pop()
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in pending and grid[p[0]][p[1]] == color:
                    pending.remove(p)
                    stack.append(p)
        component_colors.append(color)
    return {
        "grid_h": len(grid), "grid_w": width,
        "shape_size": sum(v == 6 for row in grid for v in row),
        "n_distractor": sum(v != 6 for v in component_colors),
        "target_components": component_colors.count(6),
    }


def write_report(path, report):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--band", choices=("easy", "medium", "hard"), action="append")
    parser.add_argument("--grid-h", type=int, action="append")
    parser.add_argument("--grid-w", type=int, action="append")
    parser.add_argument("--shape-size", type=int, action="append")
    parser.add_argument("--distractors", type=int, action="append")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new path; previous evidence is never overwritten")
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK_ID, root=root)
    seeds = args.seed or [0, 7]
    bands = args.band or ["easy", "medium", "hard"]
    controls = list(product(args.grid_h or [5, 20], args.grid_w or [6, 24],
                            args.shape_size or range(3, 11), args.distractors or range(5)))
    report = {
        "schema": "f9cd85012aa8-joint-controls-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "source_path": str(source),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "input controls only; no reference labels or semantic verdict",
        "seeds": seeds, "bands": bands, "sample_indices": [0, len(controls)-1],
        "controls_per_seed_band": len(controls),
        "expected_draws": len(controls) * len(seeds) * len(bands),
        "status": "running", "completed": 0, "passed": 0, "failed": 0,
        "rows": [], "failures": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    unique_inputs = set()
    failure_types = Counter()
    write_report(args.out, report)
    for seed, band in product(seeds, bands):
        for index, (h, w, size, distractors) in enumerate(controls):
            requested = dict(grid_h=h, grid_w=w, shape_size=size, n_distractor=distractors)
            row = {"seed": seed, "sample_index": index, "difficulty": band,
                   "requested": requested, "errors": []}
            grid = None
            try:
                grid = module.generate(seed, index, difficulty=band, **requested)
                row["input_sha256"] = digest(grid)
                unique_inputs.add(row["input_sha256"])
                actual = observe(grid)
                row["observed"] = actual
                for name, value in requested.items():
                    if actual[name] != value:
                        row["errors"].append(f"{name}: requested {value}, observed {actual[name]}")
                if actual["target_components"] != 1:
                    row["errors"].append("expected one target component")
                domain_errors = module.self_check(grid, difficulty=band)
                if domain_errors:
                    row["errors"].append(f"self_check: {domain_errors}")
                if module.generate(seed, index, difficulty=band, **requested) != grid:
                    row["errors"].append("identical call produced a different grid")
                observer = getattr(module, "observe_overrides", None)
                if observer is None:
                    row["errors"].append("missing observe_overrides")
                else:
                    declared = observer(grid)
                    for name, value in requested.items():
                        if type(declared.get(name)) is not int or declared.get(name) != value:
                            row["errors"].append(f"observe_overrides mismatch for {name}")
            except Exception as exc:
                row["errors"].append(f"{type(exc).__name__}: {exc}")
            row["passed"] = not row["errors"]
            report["completed"] += 1
            report["passed" if row["passed"] else "failed"] += 1
            report["rows"].append(row)
            if not row["passed"]:
                failure = dict(row, input=grid)
                report["failures"].append(failure)
                failure_types.update(error.split(":", 1)[0] for error in row["errors"])
            if report["completed"] % 40 == 0:
                write_report(args.out, report)
    report.update(status="failed" if report["failed"] else "passed",
                  unique_inputs=len(unique_inputs), failure_types=dict(failure_types),
                  finished_utc=datetime.now(timezone.utc).isoformat())
    write_report(args.out, report)
    print(json.dumps({k: report[k] for k in ("status", "completed", "passed", "failed",
                                             "unique_inputs", "generator_sha256")}))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
