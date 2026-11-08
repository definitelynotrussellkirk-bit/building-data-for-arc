#!/usr/bin/env python3
"""Exhaustively verify bounded consecutive lesson windows and query rotations.

This task-local tool checks the selected generator's declared competitors using
its Python semantic mirror. It is a schedule/teaching-contract probe, not an
independent Racket authority check and not a proof against undeclared rivals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK_ID = "113d9bb402d3"


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(*, seeds, starts, bands, root=None):
    root = find_root(__file__) if root is None else Path(root).resolve()
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pair_count = gen.EXAMPLES_NEEDED + 1
    failures = []
    profiles = Counter()
    windows = 0
    rotations = 0
    unique_inputs = set()

    for band in bands:
        for seed in seeds:
            for start in starts:
                pairs = []
                for offset in range(pair_count):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    output = gen.rule_mirror(grid)
                    pairs.append({"input": grid, "output": output})
                    profiles[gen.schedule_profile(seed, sample_index, band)] += 1
                    unique_inputs.add(hashlib.sha256(
                        json.dumps(grid, separators=(",", ":")).encode()
                    ).hexdigest())
                windows += 1
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    findings = gen.lesson_identifiable(demos, query)
                    rotations += 1
                    if findings:
                        failures.append({
                            "band": band,
                            "seed": seed,
                            "start_sample_index": start,
                            "query_index": query_index,
                            "sample_indices": list(range(start, start + pair_count)),
                            "findings": findings,
                            "profiles": [
                                gen.schedule_profile(seed, start + offset, band)
                                for offset in range(pair_count)
                            ],
                        })
    return {
        "schema": "113d9bb402d3-teaching-schedule-probe-v1",
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "generator_path": source_path.relative_to(root).as_posix(),
        "generator_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "declared_schedule_period": gen.LESSON_SCHEDULE_PERIOD,
        "declared_profiles": list(gen.SCHEDULE_PROFILES),
        "examples_needed": gen.EXAMPLES_NEEDED,
        "scope": {
            "bands": list(bands),
            "seeds": list(seeds),
            "start_sample_indices": list(starts),
            "query_policy": "hold out every position in every consecutive window",
        },
        "counts": {
            "windows": windows,
            "query_rotations": rotations,
            "ambiguous_rotations": len(failures),
            "unique_inputs": len(unique_inputs),
            "emitted_profiles": dict(sorted(profiles.items())),
        },
        "failures": failures,
        "limits": [
            "checks only declared LESSON_COMPETITORS",
            "uses the generator's Python rule_mirror rather than independent Racket labels",
            "finite seed and start ranges do not prove all-seed identifiability",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(16)))
    parser.add_argument("--start-count", type=int, default=64)
    parser.add_argument(
        "--band", action="append", choices=("easy", "medium", "hard"),
        dest="bands",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.start_count < 1:
        parser.error("--start-count must be positive")
    if args.out.exists():
        parser.error("--out must not already exist")
    report = verify(
        seeds=tuple(args.seeds),
        starts=range(args.start_count),
        bands=tuple(args.bands or ("easy", "medium", "hard")),
    )
    _write_json(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
