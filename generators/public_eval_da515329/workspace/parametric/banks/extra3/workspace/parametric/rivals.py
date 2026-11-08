"""Small executable semantic rivals for the da515329 teaching audit."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_NAME = "_da515329_rival_family_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def _paint(completed, cells, value=2):
    out = [row[:] for row in completed]
    for row, col in cells:
        out[row][col] = value
    return out


def predict(grid, selected_setting=None):
    """Return literal outputs for a finite set of plausible wrong rules."""
    color, _, _ = family.parse_cross(grid)
    completed = family.complete_spiral(grid)
    groups = family.components_of(completed, color)
    longest = max(groups, key=lambda cells: (len(cells), tuple(cells)))
    shortest = min(groups, key=lambda cells: (len(cells), tuple(cells)))
    topmost = min(groups, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    leftmost = min(groups, key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))
    all_cells = [cell for group in groups for cell in group]
    return {
        "spiral_only": [row[:] for row in completed],
        "highlight_longest": _paint(completed, longest),
        "highlight_shortest": _paint(completed, shortest),
        "highlight_topmost": _paint(completed, topmost),
        "highlight_leftmost": _paint(completed, leftmost),
        "highlight_all": _paint(completed, all_cells),
        "raw_cross_only": [row[:] for row in grid],
    }
