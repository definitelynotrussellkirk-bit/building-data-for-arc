#!/usr/bin/env python3
"""Reproduce d93da02d5ee0's ignored-axis and unknown-axis defects."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "d93da02d5ee0"
REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(canonical_json(grid)).hexdigest()


def count_x_shapes(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    count = 0
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color == 0:
                continue
            cells = ((r, c), (r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1))
            if all(grid[rr][cc] == color for rr, cc in cells):
                count += 1
    return count


def sample(gen, overrides: dict[str, Any]) -> dict[str, Any]:
    grid = gen.generate(0, 0, **overrides)
    return {
        "overrides": overrides,
        "grid_hash": grid_hash(grid),
        "shape": [len(grid), len(grid[0])],
        "detected_x_shapes": count_x_shapes(grid),
        "grid": grid,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    gen = load_generator()

    cases = {
        "n_x_low": sample(gen, {"n_x": 1}),
        "n_x_high": sample(gen, {"n_x": 5}),
        "palette_low": sample(gen, {"palette_size": 1, "n_distinct_colors": 1}),
        "palette_high": sample(gen, {"palette_size": 8, "n_distinct_colors": 8}),
    }
    unknown = sample(gen, {"typo_axis": 123})
    generator_sha = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    findings = {
        "n_x_override_ignored": (
            cases["n_x_low"]["grid_hash"] == cases["n_x_high"]["grid_hash"]
            and cases["n_x_low"]["detected_x_shapes"] not in (1, 5)
        ),
        "palette_overrides_ignored": (
            cases["palette_low"]["grid_hash"] == cases["palette_high"]["grid_hash"]
        ),
        "unknown_override_accepted": unknown["grid_hash"] == cases["n_x_low"]["grid_hash"],
    }
    report = {
        "schema": "audit-generator-contract-reproducer-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "generator_version": getattr(gen, "VERSION", None),
        "seed": 0,
        "sample_index": 0,
        "difficulty": None,
        "command": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3",
                "../checks/audit/d93da02d5ee0/reproduce_overrides.py",
                "--out", "../checks/audit/d93da02d5ee0/override-reproducer.json",
            ],
        },
        "cases": cases,
        "unknown_override_case": unknown,
        "findings": findings,
        "all_findings_reproduced": all(findings.values()),
        "documented_domain_note": (
            "n_x=1 and n_x=5, palette_size=1 and 8, and n_distinct_colors=1 and 8 "
            "are all advertised as valid by AXES; typo_axis is not advertised."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "generator_sha256": generator_sha,
        "findings": findings,
        "all_findings_reproduced": report["all_findings_reproduced"],
    }, indent=2, sort_keys=True))
    return 0 if report["all_findings_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
