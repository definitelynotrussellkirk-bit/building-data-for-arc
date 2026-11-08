"""Authoring-only diagnostic hypotheses for b86607f34b8b.

These Python predictions are rivals, not a source of reference labels. Obtain
actual labels with the supported public ``arcpuzzles apply`` command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TASK_ID = "b86607f34b8b"
RULE_HASH = "6fa3fd6234a81e7be1e1fee075319b9b552a027780935f534fab2fe6e7a76667"


def row_close(cells):
    cells = set(cells)
    result = set()
    for r in {r for r, _ in cells}:
        cs = [c for rr, c in cells if rr == r]
        result.update((r, c) for c in range(min(cs), max(cs) + 1))
    return result


def col_close(cells):
    return {(c, r) for r, c in row_close({(c, r) for r, c in cells})}


def bbox(cells):
    if not cells:
        return set()
    rs, cs = zip(*cells)
    return {(r, c) for r in range(min(rs), max(rs) + 1)
            for c in range(min(cs), max(cs) + 1)}


def fixedpoint(cells):
    previous = set(cells)
    while True:
        current = col_close(row_close(previous))
        if current == previous:
            return current
        previous = current


def predict(grid, rival="reference_mirror"):
    h, w = len(grid), len(grid[0])
    sep = next(r for r, row in enumerate(grid) if all(c == 9 for c in row))
    out = [row[:] if r <= sep else [0] * w for r, row in enumerate(grid)]
    rank = {}
    for column in range(w):
        color, mode = grid[0][column], grid[1][column]
        if not color:
            continue
        cells = {(r, c) for r in range(sep + 1, h) for c in range(w)
                 if grid[r][c] == color}
        priority = {1: 3, 3: 2, 2: 1}.get(mode, 0)
        if mode == 1:
            closed = row_close(cells)
        elif mode == 2:
            closed = col_close(cells)
        elif mode == 3:
            closed = col_close(row_close(cells))
        else:
            closed = row_close(cells) - cells
        if rival == "all_double":
            closed = col_close(row_close(cells))
        elif rival == "all_reverse":
            closed = row_close(col_close(cells))
        elif rival == "all_fixedpoint":
            closed = fixedpoint(cells)
        elif rival == "all_bbox":
            closed = bbox(cells)
        elif rival == "mode3_bbox" and mode == 3:
            closed = bbox(cells)
        elif rival == "mode3_reverse" and mode == 3:
            closed = row_close(col_close(cells))
        elif rival == "mode3_fixedpoint" and mode == 3:
            closed = fixedpoint(cells)
        elif rival == "mode3_union" and mode == 3:
            closed = row_close(cells) | col_close(cells)
        elif rival == "bridge_keeps_seeds" and mode not in (1, 2, 3):
            closed = row_close(cells)
        elif rival == "bridge_blank" and mode not in (1, 2, 3):
            closed = set()
        elif rival == "bridge_column" and mode not in (1, 2, 3):
            closed = col_close(cells) - cells
        for cell in closed:
            key = (priority, color)
            if rival == "color_priority":
                key = (color, priority)
            elif rival == "legend_rightmost_priority":
                key = (column, color)
            elif rival == "lower_color_tie":
                key = (priority, -color)
            elif rival == "legend_rightmost_tie":
                key = (priority, column)
            elif rival == "legend_leftmost_tie":
                key = (priority, -column)
            if cell not in rank or key > rank[cell]:
                rank[cell] = key
                r, c = cell
                out[r][c] = color
    return out


RIVALS = (
    "all_double", "all_reverse", "all_fixedpoint", "all_bbox", "mode3_bbox", "mode3_reverse",
    "mode3_fixedpoint", "mode3_union", "bridge_keeps_seeds", "bridge_blank",
    "bridge_column", "color_priority", "legend_rightmost_priority",
    "lower_color_tie", "legend_rightmost_tie", "legend_leftmost_tie",
)


def board(entries, *, body_h=6, width=11):
    """Entries are (color, mode, body-relative seed coordinates)."""
    grid = [[0] * width for _ in range(body_h + 3)]
    grid[2] = [9] * width
    for j, (color, mode, cells) in enumerate(entries):
        grid[0][3 * j] = color
        grid[1][3 * j] = mode
        for r, c in cells:
            assert grid[r + 3][c] == 0, (r, c)
            grid[r + 3][c] = color
    return grid


def witnesses():
    triangle = {(0, 0), (0, 2), (2, 1)}
    transpose = {(0, 0), (2, 0), (1, 2)}
    corners = {(0, 0), (0, 2), (2, 0), (2, 2)}
    ell = {(0, 0), (0, 2), (2, 0)}
    return {
        "mode1_only_row": board([(2, 1, ell)]),
        "mode2_only_column": board([(2, 2, ell)]),
        "mode3_order": board([(2, 3, triangle)]),
        "mode3_one_pass": board([(2, 3, transpose)]),
        "mode3_filled_interior": board([(2, 3, corners)]),
        "mode4_erases_seeds": board([(2, 4, {(0, 0), (0, 2)})]),
        "row_over_double": board([
            (2, 1, {(1, 0), (1, 2)}),
            (8, 3, corners),
        ]),
        "double_over_column": board([
            (2, 3, corners),
            (8, 2, {(0, 1), (2, 1)}),
        ]),
        "column_over_bridge": board([
            (2, 2, {(0, 1), (2, 1)}),
            (8, 4, {(1, 0), (1, 2)}),
        ]),
        "larger_color_same_mode": board([
            (2, 1, {(0, 0), (0, 3)}),
            (8, 1, {(0, 1), (0, 4)}),
        ]),
        "larger_color_independent_legend_order": board([
            (8, 1, {(0, 1), (0, 4)}),
            (2, 1, {(0, 0), (0, 3)}),
        ]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet_root", type=Path)
    args = parser.parse_args()
    root = args.packet_root.resolve()
    cases = witnesses()
    canonical_path = root / "repo/shared/data/canonical/puzzles.jsonl"
    record = next(json.loads(line) for line in canonical_path.open()
                  if json.loads(line).get("task_id") == TASK_ID)
    assert hashlib.sha256(record["program_solution"].encode()).hexdigest() == RULE_HASH
    tests = record["test"]
    pairs = record["train"] + (tests if isinstance(tests, list) else [tests])
    canonical_fit = {name: [predict(pair["input"], name) == pair["output"]
                            for pair in pairs] for name in RIVALS}
    assertions = {
        "mode1_only_row": [(3, 1, 2), (4, 0, 0)],
        "mode2_only_column": [(4, 0, 2), (3, 1, 0)],
        "mode3_order": [(4, 1, 2), (5, 0, 0)],
        "mode3_one_pass": [(4, 0, 2), (4, 1, 0), (4, 2, 2)],
        "mode3_filled_interior": [(4, 1, 2)],
        "mode4_erases_seeds": [(3, 0, 0), (3, 1, 2), (3, 2, 0)],
        "row_over_double": [(4, 1, 2), (3, 1, 8)],
        "double_over_column": [(4, 1, 2), (3, 1, 2)],
        "column_over_bridge": [(4, 1, 2), (4, 0, 0), (4, 2, 0)],
        "larger_color_same_mode": [(3, 0, 2), (3, 2, 8), (3, 3, 8)],
        "larger_color_independent_legend_order": [(3, 0, 2), (3, 2, 8), (3, 3, 8)],
    }
    report = {
        "task_id": TASK_ID, "rule_hash": RULE_HASH,
        "canonical_profile": {"shape": [9, 11], "palette": [0, 1, 2, 3, 4, 9],
                              "body_colors": [2, 3, 4], "canonical_pairs": len(pairs)},
        "canonical_rival_fit": canonical_fit,
        "witnesses": [
            {"name": name, "input": grid,
             "diagnostic_mirror_output": predict(grid),
             "assertions_global_rc_value": assertions[name],
             "distinguished_rivals": [rival for rival in RIVALS
                                       if predict(grid, rival) != predict(grid)]}
            for name, grid in cases.items()
        ],
        "label_policy": "Diagnostic mirrors are not authority. Actual labels are in racket.json from public apply.",
    }
    out = root / "checks/semantic-review"
    (out / "inputs.json").write_text(json.dumps({"inputs": list(cases.values())}) + "\n")
    (out / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"witnesses": len(cases), "canonical_rival_fit": canonical_fit}, indent=2))


if __name__ == "__main__":
    main()
