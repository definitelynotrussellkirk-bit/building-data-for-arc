#!/usr/bin/env python3
"""Run the task-local independent oracle against canonical Racket authority."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import reference_probe as probe


def grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def build_cases(module):
    cases: list[tuple[str, list[list[int]]]] = []
    for index, pair in enumerate(probe.canonical_pairs()):
        cases.append((f"canonical-{index}", pair["input"]))

    # Even-width object whose floored midpoint is column 1 and is uniquely
    # nearest to the marker at column 0.
    midpoint = [
        [6, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 5, 5, 0, 0, 0],
        [0, 5, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    cases.append(("integer-midpoint", midpoint))

    for band_name, difficulty in (
        ("default", None),
        ("easy", "easy"),
        ("medium", "medium"),
        ("hard", "hard"),
    ):
        for sample_index in range(12):
            cases.append(
                (
                    f"{band_name}-{sample_index}",
                    module.generate(0, sample_index, difficulty=difficulty),
                )
            )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    module = probe.load_generator()
    cases = build_cases(module)
    grids = [grid for _, grid in cases]
    expected = [probe.reference_output(grid) for grid in grids]
    actual = probe.racket_outputs(grids)
    mismatches = []
    retained = []
    for (name, grid), oracle, racket in zip(cases, expected, actual):
        retained.append({"name": name, "input_sha256": grid_hash(grid)})
        if oracle != racket:
            mismatches.append(
                {
                    "name": name,
                    "input": grid,
                    "oracle": oracle,
                    "racket": racket,
                }
            )

    generator_path = probe.ROOT / "generators" / probe.TASK / "generator.py"
    report = {
        "schema": "424c822d69f3-racket-parity-v1",
        "task_id": probe.TASK,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "case_count": len(cases),
        "mismatches": mismatches,
        "cases": retained,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("task_id", "generator_sha256", "rule_hash", "case_count")}, indent=2))
    print("mismatches:", len(mismatches))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
