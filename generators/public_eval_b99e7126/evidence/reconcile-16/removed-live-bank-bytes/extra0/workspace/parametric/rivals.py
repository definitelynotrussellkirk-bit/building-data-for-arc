"""Executable semantic rivals for the b99e7126 teaching audit."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_NAME = "_b99e7126_rival_family_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def _write_rare(grid, info, target):
    out = [row[:] for row in grid]
    for macro_row, macro_col in target:
        for local_row, values in enumerate(info["rare_tile"]):
            for local_col, value in enumerate(values):
                out[info["row_runs"][macro_row][local_row]][info["col_runs"][macro_col][local_col]] = value
    return out


def _highlight(completed, info, positions):
    out = [row[:] for row in completed]
    for macro_row, macro_col in positions:
        for local_row, local_col in info["mask"]:
            out[info["row_runs"][macro_row][local_row]][info["col_runs"][macro_col][local_col]] = family.HIGHLIGHT
    return out


def _max_key(counter):
    return max(counter, key=lambda key: (counter[key], -key))


def predict(grid, selected_setting=None):
    completed, _, info = family.complete(grid)
    target = set(info["target"])
    current = set(info["current"])
    completed_row = _max_key(Counter(row for row, _ in target))
    visible_row = _max_key(Counter(row for row, _ in current))
    completed_col = _max_key(Counter(col for _, col in target))
    correct_highlight = _highlight(
        completed, info, {position for position in target if position[0] == completed_row}
    )
    visible_highlight = _highlight(
        completed, info, {position for position in target if position[0] == visible_row}
    )
    column_highlight = _highlight(
        completed, info, {position for position in target if position[1] == completed_col}
    )
    all_highlight = _highlight(completed, info, target)

    min_row = min(row for row, _ in current)
    max_row = max(row for row, _ in current)
    min_col = min(col for _, col in current)
    max_col = max(col for _, col in current)
    bbox_target = {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
    }
    anchor_row, anchor_col = info["anchor"]
    size = len(info["rare_tile"])
    rotate_target = {
        (anchor_row + col, anchor_col + size - 1 - row)
        for row, col in info["mask"]
    }
    reflect_target = {
        (anchor_row + row, anchor_col + size - 1 - col)
        for row, col in info["mask"]
    }
    complement_target = {
        (anchor_row + row, anchor_col + col)
        for row in range(size)
        for col in range(size)
        if (row, col) not in info["mask"]
    }
    return {
        "complete_only": [row[:] for row in completed],
        "complete_then_highlight_densest_row": correct_highlight,
        "highlight_visible_densest_row": visible_highlight,
        "highlight_densest_column": column_highlight,
        "highlight_all_completed": all_highlight,
        "leave_input_unchanged": [row[:] for row in grid],
        "complete_bounding_box": _write_rare(grid, info, bbox_target),
        "complete_rotated_mask": _write_rare(grid, info, rotate_target | current),
        "complete_reflected_mask": _write_rare(grid, info, reflect_target | current),
        "complete_complement_mask": _write_rare(grid, info, complement_target | current),
    }
