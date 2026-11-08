from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
SOURCE = REPO / "generators/7c5679e5672f/generator.py"

spec = importlib.util.spec_from_file_location("audit_7c5679e5672f", SOURCE)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def observe(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_cells": sum(value == 3 for row in grid for value in row),
        "marker_count": sum(value in mod._MARKER_COLORS for row in grid for value in row),
        "marker_codes": sorted({value for row in grid for value in row if value in mod._MARKER_COLORS}),
        "self_check": mod.self_check(grid),
    }


all_codes = []
for seed in range(20):
    sample_index = seed * 7
    grid = mod.generate(seed, sample_index, texture="all_codes")
    all_codes.append({
        "seed": seed,
        "sample_index": sample_index,
        "observation": observe(grid),
        "input": grid if seed == 0 else None,
    })

invalid_domain_calls = []
for overrides in (
    {"grid_h": 8, "grid_w": 8, "shape_size": 5, "n_markers": 6},
    {"grid_h": 24, "grid_w": 24, "shape_size": 5, "n_markers": 6},
):
    try:
        grid = mod.generate(0, 1, **overrides)
    except Exception as exc:  # evidence captures the public failure surface
        invalid_domain_calls.append({
            "seed": 0,
            "sample_index": 1,
            "overrides": overrides,
            "exception": {"type": type(exc).__name__, "message": str(exc)},
        })
    else:
        invalid_domain_calls.append({
            "seed": 0,
            "sample_index": 1,
            "overrides": overrides,
            "observation": observe(grid),
        })

conflicting = {"texture": "one_marker", "grid_h": 24, "grid_w": 24, "shape_size": 5, "n_markers": 6}
conflicting_grid = mod.generate(0, 1, **conflicting)

report = {
    "schema": "arcpuzzles-audit-contract-probe-v1",
    "task_id": "7c5679e5672f",
    "generator_path": "repo/generators/7c5679e5672f/generator.py",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(mod, "RULE_HASH", None),
    "advertised_axes": mod.AXES,
    "command": {
        "cwd": "packet_root",
        "argv": [
            "env", "PYTHONPATH=repo/shared/runtime", "python3",
            "checks/audit/7c5679e5672f/probe.py",
        ],
    },
    "all_codes": {
        "draws": len(all_codes),
        "draws_missing_at_least_one_code": sum(
            row["observation"]["marker_codes"] != [1, 2, 4, 5] for row in all_codes
        ),
        "samples": all_codes,
    },
    "advertised_domain_failures": invalid_domain_calls,
    "texture_override_conflict": {
        "seed": 0,
        "sample_index": 1,
        "overrides": conflicting,
        "observation": observe(conflicting_grid),
        "input": conflicting_grid,
    },
}

out = Path(__file__).with_name("override-reproducer.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(out)
