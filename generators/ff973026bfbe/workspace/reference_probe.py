"""Independent oracle and repeatable probes for ff973026bfbe.

This module is task-local test tooling.  It does not replace the canonical
Racket authority; its small Python rules make shortcut counterexamples and
sampling defects easy to inspect and reproduce.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK = "ff973026bfbe"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK, root=find_root(__file__), labeled_only=True)


def _copy(grid):
    return [list(row) for row in grid]


def intended_output(grid):
    """Independent spelling of the selected Racket rule."""
    out = _copy(grid)
    mark_rows = {r for r, row in enumerate(grid) if 1 in row}
    mark_cols = {c for c, value in enumerate(grid[0]) if value == 2}
    for r in mark_rows:
        for c in mark_cols:
            out[r][c] = 3
    return out


def left_border_rows_only(grid):
    """Canonical-fitting shortcut: only blue cells in column 0 mark rows."""
    out = _copy(grid)
    rows = {r for r, row in enumerate(grid) if row[0] == 1}
    cols = {c for c, value in enumerate(grid[0]) if value == 2}
    for r in rows:
        for c in cols:
            out[r][c] = 3
    return out


def all_red_columns(grid):
    """Canonical-fitting shortcut: every red cell marks its column."""
    out = _copy(grid)
    rows = {r for r, row in enumerate(grid) if 1 in row}
    cols = {c for row in grid for c, value in enumerate(row) if value == 2}
    for r in rows:
        for c in cols:
            out[r][c] = 3
    return out


def observed(grid):
    blue = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    neutral = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 2, 3)
    ]
    neutral_colors = {value for _, _, value in neutral}
    if blue and all(c == 0 for _, c in blue):
        row_mode = "border"
    elif blue and all(c > 0 for _, c in blue):
        row_mode = "scattered"
    else:
        row_mode = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_marks": len(blue),
        "n_col_marks": sum(r == 0 for r, _ in red),
        "n_red_decoys": sum(r != 0 for r, _ in red),
        "n_neutral": len(neutral),
        "row_marker_mode": row_mode,
        "distractor_color": next(iter(neutral_colors)) if len(neutral_colors) == 1 else None,
    }


def off_border_witness():
    g = [[0] * 8 for _ in range(7)]
    g[0][2] = g[0][5] = 2
    g[2][4] = 1
    g[6][7] = 4
    return g


def off_top_red_witness():
    g = [[0] * 8 for _ in range(7)]
    g[0][2] = 2
    g[2][0] = 1
    g[4][5] = 2
    g[6][7] = 4
    return g


def changed_cells(left, right):
    return [
        (r, c, left[r][c], right[r][c])
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def audit(module=None, *, per_band: int = 40):
    """Return compact, JSON-serializable distribution and rival evidence."""
    gen = module or load_generator()
    report = {"task": TASK, "bands": {}, "canonical_rival_fit": {}}
    pairs = canonical_pairs()
    for name, rival in (
        ("left_border_rows_only", left_border_rows_only),
        ("all_red_columns", all_red_columns),
    ):
        report["canonical_rival_fit"][name] = all(
            rival(pair["input"]) == pair["output"] for pair in pairs
        )
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(per_band):
            grid = gen.generate(1700 + index, index, difficulty=band)
            stats = observed(grid)
            stats.update(
                {
                    "self_check": gen.self_check(grid),
                    "off_border": any(
                        value == 1 and c > 0
                        for row in grid
                        for c, value in enumerate(row)
                    ),
                    "off_top_red": any(
                        value == 2 and r > 0
                        for r, row in enumerate(grid)
                        for value in row
                    ),
                }
            )
            rows.append(stats)
        report["bands"][band] = {
            "samples": len(rows),
            "self_check_failures": sum(bool(row["self_check"]) for row in rows),
            "shapes": sorted({(row["grid_h"], row["grid_w"]) for row in rows}),
            "off_border_count": sum(row["off_border"] for row in rows),
            "off_top_red_count": sum(row["off_top_red"] for row in rows),
            "palette_sizes": sorted(
                {
                    len({value for line in gen.generate(1700 + i, i, difficulty=band) for value in line})
                    for i in range(per_band)
                }
            ),
        }
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
