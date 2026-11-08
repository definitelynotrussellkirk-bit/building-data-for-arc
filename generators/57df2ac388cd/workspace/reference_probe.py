"""Independent reference probes for task 57df2ac388cd.

This module is test/reviewer tooling.  It derives the normalized overlay from
input geometry and never imports production helpers to compute expected labels.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "57df2ac388cd"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs  # noqa: E402

TEXTURE_PALETTES = {
    "default": (2, 3),
    "warm": (4, 7),
    "cool": (1, 5),
    "varied": (6, 9),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_57df_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def components(grid):
    """Return monochrome 4-connected nonzero components in scan order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def overlay_output(grid):
    """Independent Python mirror: normalize first two objects and overlay."""
    comps = components(grid)
    if len(comps) < 2:
        raise ValueError("need two objects")
    (ca, acells), (cb, bcells) = comps[:2]
    a, b = normalize(acells), normalize(bcells)
    h = max(max(r for r, _ in a), max(r for r, _ in b)) + 1
    w = max(max(c for _, c in a), max(c for _, c in b)) + 1
    return [
        [8 if (r, c) in a and (r, c) in b
         else ca if (r, c) in a
         else cb if (r, c) in b
         else 0
         for c in range(w)]
        for r in range(h)
    ]


def branch_support(grid):
    comps = components(grid)
    if len(comps) != 2:
        raise ValueError("expected exactly two components")
    a = normalize(comps[0][1])
    b = normalize(comps[1][1])
    return {
        "overlap": len(a & b),
        "first_only": len(a - b),
        "second_only": len(b - a),
    }


def observed(grid):
    comps = components(grid)
    if len(comps) != 2:
        raise ValueError("expected exactly two components")
    colors = frozenset(color for color, _ in comps)
    texture = next(
        name for name, pair in TEXTURE_PALETTES.items()
        if frozenset(pair) == colors
    )
    by_color = {color: len(cells) for color, cells in comps}
    ca, cb = TEXTURE_PALETTES[texture]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_a_cells": by_color[ca],
        "motif_b_cells": by_color[cb],
        "texture": texture,
    }


def subset_counterexample():
    """Load the retained normalized-subset regression fixture."""
    path = Path(__file__).resolve().parents[1] / "counterexamples/normalized_subset.json"
    return json.loads(path.read_text())["input"]


def isolated_copy(grid):
    return deepcopy(grid)
