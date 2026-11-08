"""Small executable semantic rivals for the dbff022c teaching audit."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_NAME = "_dbff022c_rival_family_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def _highlight(completed, filled, selected):
    out = [row[:] for row in completed]
    for row, col, value, _ in filled:
        if selected is None or value == selected:
            out[row][col] = family.HIGHLIGHT
    return out


def _filled_components(filled):
    remaining = {(row, col): value for row, col, value, _ in filled}
    groups = []
    while remaining:
        seed = min(remaining)
        value = remaining.pop(seed)
        queue = [seed]
        cells = []
        for row, col in queue:
            cells.append((row, col))
            for dr, dc in family.CARDINAL:
                other = (row + dr, col + dc)
                if remaining.get(other) == value:
                    remaining.pop(other)
                    queue.append(other)
        groups.append((value, cells))
    return groups


def predict(grid, selected_setting=None):
    """Return literal outputs for a finite set of plausible wrong rules."""
    completed, filled, info = family.fill(grid)
    totals = Counter(value for _, _, value, _ in filled)
    groups = _filled_components(filled)
    hole_counts = Counter(value for value, _ in groups)
    largest_single = max(groups, key=lambda item: (len(item[1]), item[0]))[0]
    table = set(info["table"])
    raw_frames = Counter()
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (row, col) not in table and value in info["mapping"]:
                raw_frames[value] += 1
    raw_selected = info["mapping"][max(raw_frames, key=lambda value: (raw_frames[value], value))]
    dominant = max(totals, key=lambda value: (totals[value], value))
    smallest = min(totals, key=lambda value: (totals[value], value))
    most_holes = max(hole_counts, key=lambda value: (hole_counts[value], value))
    first_mapped = info["mapping"][min(info["mapping"])]
    return {
        "fill_only": [row[:] for row in completed],
        "highlight_dominant_fill": _highlight(completed, filled, dominant),
        "highlight_raw_frame": _highlight(completed, filled, raw_selected),
        "highlight_most_holes": _highlight(completed, filled, most_holes),
        "highlight_smallest_total": _highlight(completed, filled, smallest),
        "highlight_largest_single_hole": _highlight(completed, filled, largest_single),
        "highlight_first_mapping": _highlight(completed, filled, first_mapped),
        "highlight_all_filled": _highlight(completed, filled, None),
        "leave_input_unchanged": [row[:] for row in grid],
    }
