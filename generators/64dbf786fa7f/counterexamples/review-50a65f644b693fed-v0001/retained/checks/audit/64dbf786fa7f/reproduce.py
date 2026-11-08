#!/usr/bin/env python3
"""Reproduce the 64dbf786fa7f advertised-axis and validator defects."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
TASK = "64dbf786fa7f"
GENERATOR = REPO / "generators" / TASK / "generator.py"
EXPECTED_SHA256 = "0eed2115fe04a809bef67ec9d3aaae52e28f23847b7469942131cd5e5d69506a"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_sha(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def canonical_dimensions() -> list[list[int]]:
    dims: list[list[int]] = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK:
            continue
        for pair in row.get("train", []) + row.get("test", []):
            grid = pair["input"]
            dims.append([len(grid), len(grid[0])])
        break
    return dims


def main() -> int:
    module = load_module()
    source_sha = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert source_sha == EXPECTED_SHA256, (source_sha, EXPECTED_SHA256)

    variants = []
    controls = (
        [("palette_kind", v) for v in ("default", "warm", "cool", "varied")]
        + [("texture", v) for v in ("default", "warm", "cool", "varied")]
        + [("n_distinct_colors", v) for v in (3, 9)]
    )
    for key, value in controls:
        grid = module.generate(12345, 7, difficulty="medium", **{key: value})
        variants.append({"key": key, "value": value, "grid_sha256": grid_sha(grid)})
    unique_variant_outputs = sorted({row["grid_sha256"] for row in variants})
    assert len(unique_variant_outputs) == 1, unique_variant_outputs

    declared_valid_rejection = None
    try:
        module.generate(1, 0, difficulty="hard", grid_h=23)
    except Exception as exc:  # exact exception is evidence
        declared_valid_rejection = {"type": type(exc).__name__, "message": str(exc)}
    assert declared_valid_rejection and declared_valid_rejection["type"] == "ValueError"

    unknown_override = module.generate(1, 0, difficulty="hard", bogus=1)
    assert unknown_override

    bypass_grid = [[9]]
    bypass_errors = module.self_check(bypass_grid, difficulty="easy", meta={"texture": "no_one"})
    assert bypass_errors == [], bypass_errors

    dims = canonical_dimensions()
    assert [7, 8] in dims

    report = {
        "schema": "audit-reproducer-v1",
        "task_id": TASK,
        "generator_sha256": source_sha,
        "status": "reproduced",
        "finding": "advertised override contract is false and degenerate metadata bypasses validation",
        "seed": 12345,
        "sample_index": 7,
        "difficulty": "medium",
        "variant_outputs": variants,
        "unique_variant_outputs": len(unique_variant_outputs),
        "declared_valid_grid_h_23_hard": declared_valid_rejection,
        "unknown_override_bogus": {
            "accepted": True,
            "grid_shape": [len(unknown_override), len(unknown_override[0])],
        },
        "degenerate_meta_bypass": {
            "grid": bypass_grid,
            "difficulty": "easy",
            "meta": {"texture": "no_one"},
            "self_check_errors": bypass_errors,
        },
        "canonical_input_dimensions": dims,
        "domain_note": (
            "The inert-control and unknown-key cases are within the documented AXES API. "
            "The 1x1 bypass grid is validator-accepted only and is outside the documented generator domain."
        ),
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
