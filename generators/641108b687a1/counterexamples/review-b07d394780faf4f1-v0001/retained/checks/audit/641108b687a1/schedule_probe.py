#!/usr/bin/env python3
"""Replay all query rotations for 641108b687a1's declared four-profile schedule."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "repo/generators/641108b687a1/generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_641108b687a1", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    gen = load_generator()
    bands = ("easy", "medium", "hard")
    failures = []
    lessons = 0
    rotations = 0
    for band in bands:
        for seed in range(32):
            for start in range(8):
                pairs = []
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    pairs.append({
                        "sample_index": sample_index,
                        "input": grid,
                        "output": gen.rule_mirror(grid),
                    })
                lessons += 1
                for query_offset, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_offset]
                    reasons = gen.lesson_identifiable(demos, query)
                    rotations += 1
                    if reasons:
                        failures.append({
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_offset": query_offset,
                            "reasons": reasons,
                        })
    report = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "bands": list(bands),
        "seed_range": "0..31",
        "start_range": "0..7",
        "lessons": lessons,
        "rotations": rotations,
        "declared_profiles": list(gen.SCHEDULE_PROFILES),
        "failure_count": len(failures),
        "failure_rate_per_rotation": len(failures) / rotations,
        "failures_by_band": {
            band: sum(item["band"] == band for item in failures) for band in bands
        },
        "failures_by_start_index": {
            str(start): sum(item["start"] == start for item in failures)
            for start in range(8)
        },
        "unique_failure_reasons": sorted({
            reason for item in failures for reason in item["reasons"]
        }),
        "first_failures": failures[:12],
        "counterexample_file": "lesson.json",
        "status": "finding" if failures else "pass",
    }
    (HERE / "schedule_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "task_id": report["task_id"],
        "lessons": lessons,
        "rotations": rotations,
        "failure_count": len(failures),
        "status": report["status"],
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
