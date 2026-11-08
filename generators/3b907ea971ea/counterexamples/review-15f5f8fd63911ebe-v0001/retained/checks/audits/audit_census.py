#!/usr/bin/env python3
"""Reproduce the two findings-only audit counterexamples."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_lr_symmetric(grid):
    return all(row == row[::-1] for row in grid)


def is_ud_symmetric(grid):
    return grid == grid[::-1]


def kaleidoscope(grid, *, horizontal_flips: bool = True):
    n = len(grid)
    return [
        [
            grid[
                n - 1 - (row % n) if (row // n) % 2 == 0 else row % n
            ][
                n - 1 - (col % n)
                if horizontal_flips and (col // n) % 2 == 0
                else col % n
            ]
            for col in range(3 * n)
        ]
        for row in range(3 * n)
    ]


def exact_match_filter(board, template):
    out = [[0 for _ in row] for row in board]
    th, tw = len(template), len(template[0])
    for top in range(len(board) - th + 1):
        for left in range(len(board[0]) - tw + 1):
            if [row[left:left + tw] for row in board[top:top + th]] == template:
                for dr in range(th):
                    for dc in range(tw):
                        out[top + dr][left + dc] = board[top + dr][left + dc]
    return out


def audit_template_filter():
    module = load("3b907ea971ea")
    per_band = {}
    for band in ("easy", "medium", "hard"):
        matches = 0
        for index in range(600):
            grid = module.generate(20260928, index, difficulty=band)
            divider = next(
                col for col in range(len(grid[0]))
                if all(row[col] == 9 for row in grid)
            )
            board = [row[divider + 1:] for row in grid]
            matches += exact_match_filter(board, module.TEMPLATE) == board
        per_band[band] = {
            "draws": 600,
            "copy_board_matches_exact_match_filter": matches,
        }

    canonical = None
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "3b907ea971ea":
                canonical = row
                break
    pair = canonical["train"][0]
    divider = next(
        col for col in range(len(pair["input"][0]))
        if all(row[col] == 9 for row in pair["input"])
    )
    board = [row[divider + 1:] for row in pair["input"]]
    diffs = [
        {"row": row, "col": col, "board": board[row][col], "answer": pair["output"][row][col]}
        for row in range(len(board))
        for col in range(len(board[0]))
        if board[row][col] != pair["output"][row][col]
    ]
    return {
        "ordinary_census": per_band,
        "canonical_train_0_copy_board_disagreements": diffs,
    }


def audit_kaleidoscope():
    module = load("78ab57735469")
    per_band = {}
    for band in ("easy", "medium", "hard"):
        grids = [module.generate(20260928, index, difficulty=band) for index in range(600)]
        lr = [is_lr_symmetric(grid) for grid in grids]
        ud = [is_ud_symmetric(grid) for grid in grids]
        lr_windows = [
            start for start in range(598) if all(lr[start:start + 3])
        ]
        ud_windows = [
            start for start in range(598) if all(ud[start:start + 3])
        ]
        per_band[band] = {
            "draws": 600,
            "lr_symmetric": sum(lr),
            "ud_symmetric": sum(ud),
            "both_symmetric": sum(a and b for a, b in zip(lr, ud)),
            "three_demo_lr_symmetric_windows": lr_windows,
            "three_demo_ud_symmetric_windows": ud_windows,
        }

    inputs = [module.generate(20260928, index, difficulty="easy") for index in range(417, 421)]
    query_truth = kaleidoscope(inputs[3], horizontal_flips=True)
    query_rival = kaleidoscope(inputs[3], horizontal_flips=False)
    return {
        "ordinary_census": per_band,
        "counterexample_lesson": {
            "seed": 20260928,
            "difficulty": "easy",
            "demo_sample_indices": [417, 418, 419],
            "query_sample_index": 420,
            "demo_inputs": inputs[:3],
            "query_input": inputs[3],
            "demos_all_lr_symmetric": all(is_lr_symmetric(grid) for grid in inputs[:3]),
            "ignore_horizontal_flip_matches_all_demos": all(
                kaleidoscope(grid, horizontal_flips=False)
                == kaleidoscope(grid, horizontal_flips=True)
                for grid in inputs[:3]
            ),
            "query_lr_symmetric": is_lr_symmetric(inputs[3]),
            "query_cells_changed_by_ignored_horizontal_flip": sum(
                a != b
                for truth_row, rival_row in zip(query_truth, query_rival)
                for a, b in zip(truth_row, rival_row)
            ),
        },
    }


def main():
    print(json.dumps({
        "schema": "arcpuzzles-adversarial-audit-census/1",
        "3b907ea971ea": audit_template_filter(),
        "78ab57735469": audit_kaleidoscope(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
