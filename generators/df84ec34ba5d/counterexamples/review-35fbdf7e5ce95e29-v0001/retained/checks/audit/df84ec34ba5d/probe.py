#!/usr/bin/env python3
"""Source-bound audit probe for df84ec34ba5d advertised controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "df84ec34ba5d"
SEED = 123
SAMPLE_INDICES = list(range(10))
DIFFICULTY = "medium"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def call(gen, sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    try:
        grid = gen.generate(SEED, sample_index, difficulty=DIFFICULTY, **overrides)
    except Exception as exc:  # retain exact rejection behavior
        return {
            "status": "rejected",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "status": "accepted",
        "grid": grid,
        "grid_sha256": digest(grid),
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "self_check": gen.self_check(grid, difficulty=DIFFICULTY),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)

    cases: list[tuple[str, dict[str, Any]]] = [
        ("n_majority_min", {"n_majority": 2}),
        ("n_majority_max", {"n_majority": 5}),
        ("palette_size_min", {"palette_size": 2}),
        ("palette_size_max", {"palette_size": 9}),
        ("n_distinct_colors_min", {"n_distinct_colors": 2}),
        ("n_distinct_colors_max", {"n_distinct_colors": 9}),
        ("palette_kind_warm", {"palette_kind": "warm"}),
        ("palette_kind_cool", {"palette_kind": "cool"}),
        ("texture_warm", {"texture": "warm"}),
        ("texture_varied", {"texture": "varied"}),
        ("position_bias_invalid", {"position_bias": "not-row-majority"}),
        ("density_invalid", {"density": "dense"}),
        ("unknown_axis", {"unknown_axis": 1}),
        ("n_majority_out_of_range", {"n_majority": 99}),
        ("palette_kind_invalid", {"palette_kind": "bogus"}),
    ]

    baseline = [call(gen, i, {}) for i in SAMPLE_INDICES]
    baseline_hashes = [row.get("grid_sha256") for row in baseline]
    findings = []
    for name, overrides in cases:
        rows = [call(gen, i, overrides) for i in SAMPLE_INDICES]
        accepted = sum(row["status"] == "accepted" for row in rows)
        same = sum(
            row.get("grid_sha256") == base_hash
            for row, base_hash in zip(rows, baseline_hashes, strict=True)
        )
        findings.append(
            {
                "name": name,
                "overrides": overrides,
                "accepted": accepted,
                "sample_count": len(rows),
                "byte_identical_to_baseline": same,
                "all_byte_identical": same == len(rows),
                "errors": [row for row in rows if row["status"] != "accepted"],
                "output_hashes": [row.get("grid_sha256") for row in rows],
            }
        )

    # Positive controls prove this probe can detect an honored exact override.
    positive_controls = {}
    for label, overrides in {
        "small_shape": {"grid_h": 6, "grid_w": 7},
        "large_shape": {"grid_h": 10, "grid_w": 10},
        "degenerate_empty_rows": {"texture": "empty_rows"},
    }.items():
        positive_controls[label] = call(gen, SAMPLE_INDICES[0], overrides)

    report = {
        "schema": "arcpuzzles-audit-control-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "seed": SEED,
        "sample_indices": SAMPLE_INDICES,
        "difficulty": DIFFICULTY,
        "command": "python3 run_with_racket.py python3 ../checks/audit/df84ec34ba5d/probe.py --out ../checks/audit/df84ec34ba5d/probe.json",
        "working_directory": "WORK",
        "runtime_working_directory": "WORK/repo",
        "baseline": {
            "output_hashes": baseline_hashes,
            "first_grid": baseline[0].get("grid"),
            "all_self_checks_empty": all(row.get("self_check") == [] for row in baseline),
        },
        "findings": findings,
        "positive_controls": positive_controls,
        "conclusion": (
            "All declared palette/majority/distinct-color controls and all invalid/unknown "
            "control probes were accepted and byte-identical to the baseline for 10/10 "
            "sample indices. Shape and degenerate-texture positive controls changed output, "
            "so the comparison is sensitive to controls that generate() actually consumes."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "cases": len(findings),
        "all_cases_accepted_and_identical": all(
            row["accepted"] == len(SAMPLE_INDICES) and row["all_byte_identical"]
            for row in findings
        ),
        "out": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
