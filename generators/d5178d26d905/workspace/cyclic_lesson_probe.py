#!/usr/bin/env python3
"""Audit every query rotation of consecutive four-example lesson windows.

The production census keeps the fourth pair as query.  This task-local probe
rotates each of the four pairs into the query slot and requires the other three
to refute every declared lesson competitor.  It uses the independent oracle in
reference_probe.py rather than production rule_mirror output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import load_generator, pair


def _sha_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def run(starts: int = 30) -> dict[str, Any]:
    gen = load_generator()
    bands = (None, "easy", "medium", "hard")
    checks = 0
    unique_inputs: set[str] = set()
    failures: list[dict[str, Any]] = []
    per_band: dict[str, dict[str, int]] = {}

    for band in bands:
        label = "default" if band is None else band
        band_checks = 0
        for start in range(starts):
            seed = 9100 + start
            examples = [
                pair(gen.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            unique_inputs.update(_sha_json(item["input"]) for item in examples)
            for query_index, query in enumerate(examples):
                demos = [
                    item for index, item in enumerate(examples)
                    if index != query_index
                ]
                reasons = gen.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(item["input"]) == item["output"] for item in demos)
                ]
                checks += 1
                band_checks += 1
                if reasons or survivors:
                    failures.append(
                        {
                            "band": label,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                            "survivors": survivors,
                            "profiles": [
                                gen.schedule_profile(seed, start + offset, band)
                                for offset in range(4)
                            ],
                        }
                    )
        per_band[label] = {"rotations_checked": band_checks}

    return {
        "schema": "d5178d26d905-cyclic-lesson-probe-v1",
        "generator_version": gen.VERSION,
        "starts_per_band": starts,
        "per_band": per_band,
        "rotations_checked": checks,
        "unique_input_hashes": len(unique_inputs),
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "failures": failures,
        "passed": not failures,
        "limitations": [
            "Finite declared-rival probe, not a proof of universal induction.",
            "Uses the independent Python oracle; Racket parity is covered by the battery.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=30)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.starts)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("passed", "rotations_checked", "unique_input_hashes")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
