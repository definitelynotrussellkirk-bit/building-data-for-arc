"""Independent oracle and probes for generator 506e262f9354.

The canonical Racket rule remains label authority.  This helper deliberately
re-implements the geometry without importing production helpers so reviewers
can test generated inputs, rivals, and counterexamples independently.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

TASK_ID = "506e262f9354"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_506e262f9354", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _facts(grid):
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("non-rectangular grid")
    sevens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7]
    if not sevens:
        raise ValueError("missing color-7 source")
    source_col = sevens[0][1]
    bottom_row = max(r for r, _ in sevens)
    top_row = min(r for r, _ in sevens)
    decoys = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value not in (0, 7)]
    return {
        "h": h,
        "w": w,
        "source_col": source_col,
        "top_row": top_row,
        "bottom_row": bottom_row,
        "n_sevens": len(sevens),
        "decoys": decoys,
    }


def intended_output(grid):
    """Independent statement of the selected Racket authority."""
    facts = _facts(grid)
    out = [[0 for _ in range(facts["w"])] for _ in range(facts["h"])]
    for r in range(facts["h"]):
        vertical_reach = facts["bottom_row"] - r
        for c in range(facts["w"]):
            horizontal_distance = abs(c - facts["source_col"])
            if vertical_reach >= 0 and horizontal_distance <= vertical_reach:
                out[r][c] = 7 if horizontal_distance % 2 == 0 else 8
    return out


def line_length_rival(grid):
    """Canonical-fitting shortcut: triangle height equals source-line length.

    All canonical sources start in row zero, so line length and bottom-row+1
    coincide there.  A vertically shifted source separates the two rules.
    """
    facts = _facts(grid)
    out = [[0 for _ in range(facts["w"])] for _ in range(facts["h"])]
    first_triangle_row = facts["bottom_row"] - facts["n_sevens"] + 1
    for r in range(first_triangle_row, facts["bottom_row"] + 1):
        vertical_reach = facts["bottom_row"] - r
        for c in range(facts["w"]):
            horizontal_distance = abs(c - facts["source_col"])
            if horizontal_distance <= vertical_reach:
                out[r][c] = 7 if horizontal_distance % 2 == 0 else 8
    return out


def preserve_decoys_rival(grid):
    """Canonical-fitting shortcut: preserve input cells outside the triangle."""
    out = intended_output(grid)
    intended_nonzero = {(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and (r, c) not in intended_nonzero:
                out[r][c] = value
    return out


def column_position(grid):
    facts = _facts(grid)
    c, w = facts["source_col"], facts["w"]
    if c == 0:
        return "left"
    if c == w - 1:
        return "right"
    if c == w // 2:
        return "center"
    return "interior"


def observed(grid):
    facts = _facts(grid)
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "n_sevens": facts["n_sevens"],
        "column_position": column_position(grid),
        "decoy_count": len(facts["decoys"]),
    }


def features(grid):
    facts = _facts(grid)
    return {
        "canonical_like": facts["top_row"] == 0 and not facts["decoys"],
        "shifted_column": facts["top_row"] > 0,
        "erasable_decoy": bool(facts["decoys"]),
        "left_clipped": facts["source_col"] < facts["bottom_row"],
        "right_clipped": facts["w"] - 1 - facts["source_col"] < facts["bottom_row"],
    }


def explicit_counterexample():
    grid = [[0] * 9 for _ in range(6)]
    for row in (2, 3, 4):
        grid[row][4] = 7
    return grid


def decoy_counterexample():
    grid = explicit_counterexample()
    grid[5][0] = 3
    return grid


def clone(grid):
    return deepcopy(grid)
