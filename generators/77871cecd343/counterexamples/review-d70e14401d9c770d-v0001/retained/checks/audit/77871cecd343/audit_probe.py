#!/usr/bin/env python3
"""Reproduce the size/row-offset shortcut for audit target 77871cecd343."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

TASK_ID = "77871cecd343"
GENERATOR_SHA256 = "5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca"
RULE_HASH = "1bad9bf6a465"

OFFSETS = (
    (0, 0), (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
)
DIMS = {
    "easy": ((9, 9), (9, 11), (11, 9), (11, 11), (13, 9), (9, 13)),
    "medium": ((9, 9), (9, 11), (11, 9), (11, 11), (13, 11), (11, 13)),
    "hard": ((9, 9), (9, 11), (11, 9), (13, 13), (15, 13), (13, 15)),
}
GROUP_A = {(9, 9), (11, 11), (13, 13)}
GROUP_B = {(9, 11), (13, 9), (13, 11), (15, 13)}
GROUP_C = {(11, 9), (9, 13), (11, 13), (13, 15)}
COL_LOOKUP = {
    "A": {-1: 1, 0: 0, 1: -1},
    "B": {-1: -1, 0: -1, 1: 0},
    "C": {-1: 0, 0: 1, 1: 1},
}


def normalize_grid(grid):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in grid]


def axes(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(f"expected one full 9 row and column, got {rows=} {cols=}")
    return rows[0], cols[0]


def source_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def _reflect(grid, guessed_r, guessed_c):
    actual_r, actual_c = axes(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, c in source_cells(grid):
        for rr, cc in (
            (r, 2 * guessed_c - c),
            (2 * guessed_r - r, c),
            (2 * guessed_r - r, 2 * guessed_c - c),
        ):
            if 0 <= rr < h and 0 <= cc < w and rr != actual_r and cc != actual_c:
                out[rr][cc] = 8
    return out


def inferred_col_offset(height, width, row_offset):
    dims = (height, width)
    if dims in GROUP_A:
        group = "A"
    elif dims in GROUP_B:
        group = "B"
    elif dims in GROUP_C:
        group = "C"
    else:
        raise ValueError(f"dimension pair {dims} is outside the audited default support")
    return COL_LOOKUP[group][row_offset]


def size_row_shortcut(grid):
    """Wrong rule: detect the 9-row, but infer a noncentral 9-column from size."""
    actual_r, _ = axes(grid)
    h, w = len(grid), len(grid[0])
    center_c = w // 2
    # This visible special case makes every canonical centered cross fit.
    if all(grid[r][center_c] == 9 for r in range(h)):
        guessed_c = center_c
    else:
        row_offset = actual_r - h // 2
        guessed_c = center_c + inferred_col_offset(h, w, row_offset)
    return _reflect(grid, actual_r, guessed_c)


def parse_apply(path):
    payload = json.loads(path.read_text())
    return payload, payload["results"][0]["output"]


def canonical_pairs(packet_root):
    ledger = packet_root / "repo/shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            pairs = list(row["train"])
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [
                {"input": normalize_grid(pair["input"]), "output": normalize_grid(pair["output"])}
                for pair in pairs + list(test)
            ]
    raise KeyError(TASK_ID)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.packet_root.resolve()
    evidence = root / "checks/audit/77871cecd343"
    episode = json.loads((evidence / "episode.jsonl").read_text().splitlines()[0])
    witness = episode["train"][0]
    input_grid = witness["input"]
    apply_payload, racket_output = parse_apply(evidence / "racket.json")
    rival_output = size_row_shortcut(input_grid)
    canonical = canonical_pairs(root)
    canonical_fits = sum(size_row_shortcut(pair["input"]) == pair["output"] for pair in canonical)

    default_schedule = {}
    for band, profiles in DIMS.items():
        checked = matched = 0
        for sample_index in range(54):  # lcm(6 dimension phases, 9 offset phases)
            height, width = profiles[sample_index % len(profiles)]
            row_offset, col_offset = OFFSETS[sample_index % len(OFFSETS)]
            checked += 1
            if col_offset == 0 or inferred_col_offset(height, width, row_offset) == col_offset:
                matched += 1
        default_schedule[band] = {"phases_checked": checked, "lookup_matches": matched}

    actual_r, actual_c = axes(input_grid)
    guessed_c = len(input_grid[0]) // 2 + inferred_col_offset(
        len(input_grid), len(input_grid[0]), actual_r - len(input_grid) // 2
    )
    diffs = [
        {"row": r, "col": c, "racket": expected, "rival": predicted}
        for r, (expected_row, rival_row) in enumerate(zip(racket_output, rival_output))
        for c, (expected, predicted) in enumerate(zip(expected_row, rival_row))
        if expected != predicted
    ]
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding_id": "A-7787-1",
        "generator_sha256": GENERATOR_SHA256,
        "rule_hash": RULE_HASH,
        "canonical_fit": {"fits": canonical_fits, "pairs": len(canonical)},
        "default_schedule_source_check": default_schedule,
        "production_witness": {
            "seed": 7787199,
            "sample_index": 1,
            "difficulty": "medium",
            "overrides": {"grid_w": 9},
            "accepted_with_zero_rejections": not episode.get("rejections"),
            "observed_axes": {
                "grid_h": len(input_grid),
                "grid_w": len(input_grid[0]),
                "axis_row": actual_r,
                "axis_col": actual_c,
                "row_offset": actual_r - len(input_grid) // 2,
                "col_offset": actual_c - len(input_grid[0]) // 2,
                "guessed_axis_col": guessed_c,
                "shape_cells": len(source_cells(input_grid)),
            },
            "input": input_grid,
            "racket_output": racket_output,
            "rival_output": rival_output,
            "differing_cells": diffs,
        },
        "apply_provenance": {
            key: apply_payload.get(key)
            for key in (
                "schema", "task_id", "rule_task_id", "reference", "rule_file",
                "executed_rule_hash", "rule_text_sha256", "generator_sha256",
                "rule_hash_matches_catalog",
            )
        },
        "rival": {
            "name": "size_row_shortcut",
            "definition": (
                "Use the visible full color-9 row, but when the vertical divider is off center, "
                "infer its column offset from canvas dimensions and row offset using the default schedule correlation."
            ),
        },
        "conclusion": (
            "The rival fits every labeled canonical pair and every source-level default schedule phase, "
            "but disagrees with the selected Racket output on a valid advertised grid_w override."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.out.parent / "rival.json").write_text(json.dumps(rival_output, indent=2) + "\n")
    print(json.dumps({
        "canonical_fit": f"{canonical_fits}/{len(canonical)}",
        "default_phases": sum(v["phases_checked"] for v in default_schedule.values()),
        "default_matches": sum(v["lookup_matches"] for v in default_schedule.values()),
        "differing_cells": len(diffs),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if canonical_fits == len(canonical) and all(v["lookup_matches"] == v["phases_checked"] for v in default_schedule.values()) and diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
