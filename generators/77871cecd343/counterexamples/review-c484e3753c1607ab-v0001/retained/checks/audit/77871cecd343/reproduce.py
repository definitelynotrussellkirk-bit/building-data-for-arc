#!/usr/bin/env python3
"""Reproduce a current default-schedule shortcut for audit target 77871cecd343."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from math import lcm
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
for entry in (REPO / "shared" / "runtime", REPO / "shared"):
    sys.path.insert(0, str(entry))
from reviewer_support import canonical_pairs  # noqa: E402

TASK_ID = "77871cecd343"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_77871cecd343", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def axes(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(f"expected one full 9 row/column, got {rows=} {cols=}")
    return rows[0], cols[0]


def source_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def build_lookup(module):
    lookup = {}
    phase_rows = []
    for band, profiles in module._DIFFICULTY_DIMS.items():
        if band is None:
            continue
        period = lcm(len(profiles), len(module._AXES_OFFSETS))
        for sample_index in range(period):
            h, w = profiles[sample_index % len(profiles)]
            row_offset, col_offset = module._AXES_OFFSETS[sample_index % len(module._AXES_OFFSETS)]
            key = (h, w, row_offset)
            lookup.setdefault(key, set()).add(col_offset)
            phase_rows.append((band, sample_index, key, col_offset))
    ambiguous = {str(key): sorted(values) for key, values in lookup.items() if len(values) != 1}
    return {key: next(iter(values)) for key, values in lookup.items() if len(values) == 1}, phase_rows, ambiguous


def rival(grid, lookup):
    actual_r, actual_c = axes(grid)
    h, w = len(grid), len(grid[0])
    center_c = w // 2
    if all(grid[r][center_c] == 9 for r in range(h)):
        guessed_c = center_c
    else:
        key = (h, w, actual_r - h // 2)
        guessed_c = center_c + lookup[key]
    out = deepcopy(grid)
    for r, c in source_cells(grid):
        for rr, cc in (
            (r, 2 * guessed_c - c),
            (2 * actual_r - r, c),
            (2 * actual_r - r, 2 * guessed_c - c),
        ):
            if 0 <= rr < h and 0 <= cc < w and rr != actual_r and cc != actual_c:
                out[rr][cc] = 8
    return out, guessed_c


def main() -> int:
    module = load_generator()
    lookup, phase_rows, ambiguous_lookup = build_lookup(module)
    phase_matches = sum(lookup.get(key) == col for _, _, key, col in phase_rows)
    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    canonical_fit = 0
    for pair in canonical:
        predicted, _ = rival(pair["input"], lookup)
        canonical_fit += int(predicted == pair["output"])

    grid = json.loads((HERE / "input.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    racket_output = receipt["results"][0]["output"]
    rival_output, guessed_col = rival(grid, lookup)
    actual_r, actual_c = axes(grid)
    differences = [
        {"row": r, "col": c, "racket": racket_output[r][c], "rival": rival_output[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if racket_output[r][c] != rival_output[r][c]
    ]
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding_id": "A-77871-dimension-row-lookup",
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "rival": {
            "name": "dimension_and_row_offset_predict_vertical_axis",
            "definition": "Detect the visible horizontal cross row, but infer the vertical cross offset from (grid_h, grid_w, row_offset) using the default schedule correlation; use the visible center column only on centered canonical cases.",
        },
        "canonical_fit": {"fits": canonical_fit, "pairs": len(canonical)},
        "default_schedule_fit": {
            "fits": phase_matches,
            "phases": len(phase_rows),
            "ambiguous_lookup_keys": ambiguous_lookup,
        },
        "production_witness": {
            "seed": 7787199,
            "sample_index": 1,
            "difficulty": "medium",
            "overrides": {"grid_w": 9},
            "self_check": module.self_check(grid),
            "observed": module.observe_overrides(grid),
            "actual_axis": [actual_r, actual_c],
            "rival_guessed_axis_col": guessed_col,
            "input": grid,
            "racket_output": racket_output,
            "rival_output": rival_output,
            "differing_cells": differences,
        },
        "apply_provenance": {
            key: receipt.get(key)
            for key in (
                "schema", "task_id", "rule_task_id", "reference", "rule_file",
                "executed_rule_hash", "generator_sha256", "rule_hash_matches_catalog",
            )
        },
        "conclusion": "The wrong lookup rule fits every labeled canonical pair and every default schedule phase, but fails a lawful exact grid-width override; defaults therefore retain a second-order axis correlation not covered by declared competitors.",
    }
    (HERE / "rival.json").write_text(json.dumps(rival_output, indent=2) + "\n")
    (HERE / "counterexample.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_fit": f"{canonical_fit}/{len(canonical)}",
        "default_schedule_fit": f"{phase_matches}/{len(phase_rows)}",
        "differences": len(differences),
        "generator_sha256": report["generator_sha256"],
    }, sort_keys=True))
    return 0 if canonical_fit == len(canonical) and phase_matches == len(phase_rows) and differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
