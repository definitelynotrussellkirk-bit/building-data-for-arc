#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "c2996845ede0"
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=REPO)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def components(grid: list[list[int]]) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    stack.append(q)
        result.append({"size": len(cells), "colors": sorted({grid[r][c] for r, c in cells}), "cells": sorted(cells)})
    return sorted(result, key=lambda row: (row["size"], row["cells"]))


def generate(overrides: dict[str, object]) -> dict[str, object]:
    try:
        grid = GEN.generate(20261021, 7, difficulty="medium", **overrides)
    except Exception as exc:
        return {"overrides": overrides, "status": "rejected", "exception": type(exc).__name__, "message": str(exc)}
    return {
        "overrides": overrides,
        "status": "accepted",
        "grid_sha256": digest(grid),
        "shape": [len(grid), len(grid[0])],
        "component_sizes": [row["size"] for row in components(grid)],
        "self_check": GEN.self_check(grid),
        "grid": grid,
    }


pairs = []
for axis, left, right in [
    ("big_size", 4, 8),
    ("n_small", 1, 6),
    ("palette_kind", "warm", "cool"),
    ("position_bias", "big_left_small_right", "big_right_small_left"),
    ("texture", "warm", "cool"),
]:
    a, b = generate({axis: left}), generate({axis: right})
    pairs.append({
        "axis": axis,
        "left": a,
        "right": b,
        "outputs_identical": a.get("grid_sha256") == b.get("grid_sha256") and a.get("status") == "accepted",
    })

unknown = generate({"typo_axis": 123})
invalid_scalar = generate({"grid_h": 8.0})

degenerates = []
for name in GEN.DEGENERATE_TEXTURES:
    grid = GEN.generate(1, 0, texture=name)
    degenerates.append({
        "texture": name,
        "grid_sha256": digest(grid),
        "components": components(grid),
        "self_check": GEN.self_check(grid),
        "grid": grid,
    })

semantic_hooks = {
    name: hasattr(GEN, name)
    for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
}
report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(REPO)),
    "generator_sha256": SOURCE_SHA256,
    "findings": [
        "advertised overrides are accepted but do not affect generation",
        "unknown overrides and coercible non-integer controls are accepted",
        "equal_size and symmetric_big are declared degenerates inside the ordinary texture domain and pass self_check",
        "no semantic teaching contract is declared",
    ],
    "command": ["PYTHONPATH=shared/runtime:src", "python3", "../checks/audit/c2996845ede0/reproduce_contract_defects.py"],
    "cwd": "repo",
    "dead_axis_pairs": pairs,
    "unknown_override": unknown,
    "invalid_scalar": invalid_scalar,
    "degenerates": degenerates,
    "semantic_hooks": semantic_hooks,
}
out = HERE.with_name("contract_defects_reproducer.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
# Save one supported apply input for the dead-axis witness.
input_grid = next(pair["left"]["grid"] for pair in pairs if pair["axis"] == "big_size")
HERE.with_name("dead_big_size_input.json").write_text(json.dumps(input_grid, indent=2) + "\n")
print(out)
print(json.dumps({
    "dead_axes": [p["axis"] for p in pairs if p["outputs_identical"]],
    "unknown_override_status": unknown["status"],
    "equal_size_self_check": next(d["self_check"] for d in degenerates if d["texture"] == "equal_size"),
    "generator_sha256": SOURCE_SHA256,
}, sort_keys=True))
