#!/usr/bin/env python3
"""Reproduce the ordered-vs-rotated query coverage audit for ffe1da16c912."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "ffe1da16c912"


def find_work(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "repo" / "generators" / TASK / "generator.py").is_file():
            return candidate
    raise RuntimeError("could not locate WORK root")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    if args.starts < 1:
        raise SystemExit("--starts must be positive")

    work = find_work(Path(__file__).resolve())
    runtime = work / "repo" / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    source = work / "repo" / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    rows = []
    omissions = 0
    for start in range(args.starts):
        positions = [module.schedule_profile(0, start + offset, "medium")[0] for offset in range(4)]
        for query_index in range(4):
            query_position = positions[query_index]
            demo_positions = sorted({value for i, value in enumerate(positions) if i != query_index})
            unseen = query_position not in demo_positions
            omissions += int(unseen)
            rows.append({
                "sample_start": start,
                "query_index": query_index,
                "matched_indices": positions,
                "demo_positions": demo_positions,
                "query_position": query_position,
                "position_unseen_in_demos": unseen,
            })

    rotations = len(rows)
    report = {
        "schema": "ffe1da16c912-rotation-schedule-analysis-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "starts_checked": args.starts,
        "rotations_checked": rotations,
        "position_omission_rotations": omissions,
        "omission_rate": omissions / rotations,
        "rows": rows,
        "interpretation": (
            "Because match_index = sample_index mod 3, every four-pair window has positions a,b,c,a. "
            "Query rotations at b or c leave no demonstration of the held-out position; the ordered "
            "fourth-query policy remains safe."
        ),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(json.dumps({k: report[k] for k in ("task_id", "starts_checked", "rotations_checked", "position_omission_rotations", "omission_rate")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
