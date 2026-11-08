#!/usr/bin/env python3
"""Audit the default lesson schedule for task f6b9f647b109.

This is a task-local reviewer tool.  It verifies factor support, four-demo
sliding-window coverage, canonical-size anchors, and query recombination using
actual generated grids rather than trusting the schedule table alone.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

TASK_ID = "f6b9f647b109"


def _load_generator() -> ModuleType:
    workspace = Path(__file__).resolve().parent
    repo = workspace.parents[2]
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    path = workspace.parent / "generator.py"
    name = f"schedule_audit_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def audit_schedule(*, seed: int = 271828, difficulty: str = "medium") -> dict[str, Any]:
    gen = _load_generator()
    period = len(gen.SCHEDULE_PROFILES)
    rows: list[dict[str, Any]] = []
    for sample_index in range(period):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        observed = dict(gen.observe_overrides(grid))
        observed.update(
            sample_index=sample_index,
            profile=gen.schedule_profile(seed, sample_index, difficulty=difficulty),
            canonical_size=not bool(gen.strict_canonical_like(grid)),
        )
        rows.append(observed)

    violations: list[str] = []
    if len(set(row["profile"] for row in rows)) != period:
        violations.append("schedule profiles are not unique over one declared period")

    expected_pairs = {
        (major_axis, distance_profile)
        for major_axis in gen.MAJOR_AXES
        for distance_profile in gen.DISTANCE_PROFILES
    }
    support: dict[str, list[list[str]]] = {}
    for direction in gen.DIRECTIONS:
        pairs = {
            (row["major_axis"], row["distance_profile"])
            for row in rows
            if row["direction"] == direction
        }
        support[direction] = [list(pair) for pair in sorted(pairs)]
        if pairs != expected_pairs:
            violations.append(
                f"direction {direction!r} realizes {sorted(pairs)}, expected {sorted(expected_pairs)}"
            )

    windows: list[dict[str, Any]] = []
    for start in range(period):
        demo_rows = [rows[(start + offset) % period] for offset in range(gen.EXAMPLES_NEEDED)]
        query = rows[(start + gen.EXAMPLES_NEEDED) % period]
        directions = {row["direction"] for row in demo_rows}
        major_axes = {row["major_axis"] for row in demo_rows}
        distances = {row["distance_profile"] for row in demo_rows}
        anchors = sum(bool(row["canonical_size"]) for row in demo_rows)
        same_direction = [row for row in demo_rows if row["direction"] == query["direction"]]
        recombined = (
            len(same_direction) == 1
            and (
                same_direction[0]["major_axis"],
                same_direction[0]["distance_profile"],
            )
            != (query["major_axis"], query["distance_profile"])
        )
        window = {
            "start": start,
            "directions": sorted(directions),
            "major_axes": sorted(major_axes),
            "distance_profiles": sorted(distances),
            "canonical_size_anchors": anchors,
            "query_recombined": recombined,
        }
        windows.append(window)
        if directions != set(gen.DIRECTIONS):
            violations.append(f"window {start}: missing direction coverage")
        if major_axes != set(gen.MAJOR_AXES):
            violations.append(f"window {start}: missing major-axis coverage")
        if distances != set(gen.DISTANCE_PROFILES):
            violations.append(f"window {start}: missing distance-profile coverage")
        if anchors < 2:
            violations.append(f"window {start}: only {anchors} canonical-size anchors")
        if not recombined:
            violations.append(f"window {start}: query repeats the demo profile for its direction")

    return {
        "schema": "f6b9f647b109-schedule-audit-v1",
        "status": "PASS" if not violations else "FAIL",
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "period": period,
        "support_by_direction": support,
        "rows": rows,
        "windows": windows,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=271828)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--json", action="store_true", help="emit the complete JSON report")
    args = parser.parse_args()

    report = audit_schedule(seed=args.seed, difficulty=args.difficulty)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['task_id']}: {report['status']} — period={report['period']}")
        for direction, pairs in report["support_by_direction"].items():
            rendered = ", ".join(f"{axis}/{distance}" for axis, distance in pairs)
            print(f"  {direction}: {rendered}")
        anchor_counts = [window["canonical_size_anchors"] for window in report["windows"]]
        print(
            "  sliding windows: "
            f"min anchors={min(anchor_counts)}, "
            f"query recombination={sum(w['query_recombined'] for w in report['windows'])}/{len(report['windows'])}"
        )
        for violation in report["violations"]:
            print(f"  FAIL: {violation}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
