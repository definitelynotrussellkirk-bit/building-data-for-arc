#!/usr/bin/env python3
"""Probe exact sampler controls; the Python structural oracle is not labels.

Enumerate heights/widths 5..24 and requested target counts 1..12. The sampler's
documented construction capacity is floor(height/3)*floor(width/3), not a bound
on mathematically lawful shared-arm inputs under the rule. This checks sampler
construction, self_check and deterministic replay, without importing Racket.
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


TASK_ID = "1e99030a2d90"
REPLAY_CASES = {(5, 5, 1), (5, 24, 8), (24, 5, 8),
                (9, 9, 9), (11, 10, 6), (24, 24, 12)}


def locate_root():
    """Bootstrap reviewer_support in either library or copied-runtime layout."""
    for ancestor in Path(__file__).resolve().parents:
        for runtime in (ancestor / "shared" / "runtime", ancestor):
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                from reviewer_support import find_root
                return find_root(__file__)
    raise FileNotFoundError("reviewer_support.py not found in this probe's tree")


def structural_centers(grid):
    """Independent set intersection of red coordinates, restricted to blanks."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("empty/non-sequence grid")
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        raise ValueError("empty/non-sequence row")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        raise ValueError("invalid ARC integer cell")
    red = {(r, c) for r, row in enumerate(grid)
           for c, value in enumerate(row) if value == 2}
    blank = {(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 0}
    return (blank & {(r + 1, c) for r, c in red}
            & {(r - 1, c) for r, c in red}
            & {(r, c + 1) for r, c in red}
            & {(r, c - 1) for r, c in red})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path,
                        help="alternate source, e.g. an original baseline")
    parser.add_argument("--band", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--sample-index", type=int, default=9)
    parser.add_argument("--out", type=Path, required=True, help="compact JSON report")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing report: {args.out}")
    started = time.perf_counter()
    failures = Counter()
    examples = []
    counts = Counter(successful=0, expected_rejected=0, error=0)
    replays = {}

    def record(kind, axes, detail):
        failures[kind] += 1
        if len(examples) < 30:
            examples.append({"kind": kind, "axes": axes, "detail": str(detail)[:500]})

    root = locate_root()
    default_source = root / "generators" / TASK_ID / "generator.py"
    if not default_source.is_file():
        default_source = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    source = (args.generator or default_source).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("exact_controls_selected_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for height, width, requested in itertools.product(range(5, 25), range(5, 25), range(1, 13)):
        axes = {"grid_h": height, "grid_w": width, "n_diamonds": requested}
        impossible = requested > (height // 3) * (width // 3)
        issues_before = sum(failures.values())
        try:
            grid = module.generate(args.seed, args.sample_index, difficulty=args.band, **axes)
        except Exception as exc:
            incompatible = getattr(exc, "incompatible_axes", ())
            if isinstance(incompatible, str):
                incompatible = (incompatible,)
            try:
                covered = set(axes).issubset(set(incompatible))
            except TypeError:
                covered = False
            if impossible and isinstance(exc, ValueError) and covered:
                counts["expected_rejected"] += 1
            else:
                record("rejection_contract" if impossible else "unexpected_exception", axes,
                       f"{type(exc).__name__}: {exc}; incompatible_axes={incompatible!r}")
                counts["error"] += 1
            continue
        if impossible:
            record("sampler_capacity_exceeded_accepted", axes, "construction capacity exceeded without ValueError")
        try:
            centers = structural_centers(grid)
            actual = (len(grid), len(grid[0]), len(centers))
            if actual != (height, width, requested):
                record("inexact_controls", axes, f"actual height,width,centers={actual}")
            check = module.self_check(grid, difficulty=args.band)
            if check:
                record("self_check", axes, repr(check))
        except Exception as exc:
            record("structural_or_self_check_exception", axes, f"{type(exc).__name__}: {exc}")
        if (height, width, requested) in REPLAY_CASES:
            replays[(height, width, requested)] = grid
        counts["error" if sum(failures.values()) != issues_before else "successful"] += 1

    replay_passed = 0
    for case in sorted(REPLAY_CASES):
        axes = dict(zip(("grid_h", "grid_w", "n_diamonds"), case))
        if case not in replays:
            record("replay_missing_initial_grid", axes, "initial feasible draw failed")
            continue
        try:
            replay = module.generate(args.seed, args.sample_index, difficulty=args.band, **axes)
            if replay == replays[case]:
                replay_passed += 1
            else:
                record("nondeterministic_replay", axes, "same arguments produced a different grid")
        except Exception as exc:
            record("replay_exception", axes, f"{type(exc).__name__}: {exc}")

    report = {
        "schema_version": 1, "task_id": TASK_ID,
        "oracle": "Python structural red-coordinate intersection; not authoritative output labels",
        "generator_path": str(source), "generator_sha256": digest,
        "arguments": {"band": args.band, "seed": args.seed, "sample_index": args.sample_index},
        "enumeration": {"grid_h": [5, 24], "grid_w": [5, 24], "n_diamonds": [1, 12]},
        "sampler_capacity_contract": "floor(grid_h/3)*floor(grid_w/3); disjoint construction support, not a Racket-rule feasibility bound",
        "total_cases": sum(counts.values()), "case_counts": dict(counts),
        "replay_cases": len(REPLAY_CASES), "replay_passed": replay_passed,
        "failure_count": sum(failures.values()), "failures_by_kind": dict(failures),
        "failure_examples": examples, "failure_examples_limit": 30,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("passed", "total_cases", "case_counts", "replay_passed",
                       "failure_count", "elapsed_seconds")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
