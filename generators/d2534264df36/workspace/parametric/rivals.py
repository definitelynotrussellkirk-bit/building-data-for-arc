"""Finite, explicit shortcut rivals for the d2534264df36 self-audit.

These are deliberately small wrong rules.  They are not candidate production
programs and do not claim completeness over all possible shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RIVAL_NAMES = (
    "paired_only",
    "row_axis_only",
    "column_axis_only",
    "fixed_middle_hit",
    "corner_color_cross",
)


def _load_oracle():
    spec = importlib.util.spec_from_file_location(
        "d2534264df36_cross_stop_rival_oracle", HERE / "oracle.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load sibling oracle")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = _load_oracle()


def _grid(value) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("expected a nonempty grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("expected an exact rectangular color grid")
    return deepcopy(value)


def _ring_targets(height: int, width: int, row: int, col: int):
    ring = min(row, col, height - 1 - row, width - 1 - col)
    far_row = height - 1 - ring
    far_col = width - 1 - ring
    is_corner = row in (ring, far_row) and col in (ring, far_col)
    if is_corner:
        return ring, True, (
            (ring, ring),
            (ring, far_col),
            (far_row, ring),
            (far_row, far_col),
        )
    row_offsets = range(ring + 2, far_col - 1, 2)
    col_offsets = range(ring + 2, far_row - 1, 2)
    return ring, False, tuple(
        [(ring, offset) for offset in row_offsets]
        + [(far_row, offset) for offset in range(ring + 2, far_col - 1, 2)]
        + [(offset, ring) for offset in col_offsets]
        + [(offset, far_col) for offset in range(ring + 2, far_row - 1, 2)]
    )


def restricted_completion(grid, shortcut: str) -> list[list[int]]:
    """Complete corners, but restrict non-corner activation by a wrong cue."""
    if shortcut not in ("paired_only", "row_axis_only", "column_axis_only"):
        raise ValueError("unknown completion shortcut")
    source = _grid(grid)
    height, width = len(source), len(source[0])
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] > 0
    ]
    groups: dict[tuple[int, int], int] = {}
    for row, col in cells:
        ring, is_corner, _targets = _ring_targets(height, width, row, col)
        if not is_corner:
            key = (ring, source[row][col])
            groups[key] = groups.get(key, 0) + 1

    out = deepcopy(source)
    for row, col in cells:
        color = source[row][col]
        ring, is_corner, targets = _ring_targets(height, width, row, col)
        far_row = height - 1 - ring
        far_col = width - 1 - ring
        allowed = is_corner
        if not is_corner and shortcut == "paired_only":
            allowed = groups.get((ring, color), 0) >= 2
        elif not is_corner and shortcut == "row_axis_only":
            allowed = row in (ring, far_row)
        elif not is_corner and shortcut == "column_axis_only":
            allowed = col in (ring, far_col)
        if allowed:
            for target_row, target_col in targets:
                out[target_row][target_col] = color
    return out


def _cross(base, hit_row: int, color: int, *, overwrite: bool = False):
    out = _grid(base)
    height, width = len(out), len(out[0])
    if height != width:
        raise ValueError("cross shortcut expects a square grid")
    hub = height // 2
    far = height - 1 - hit_row
    cells = (
        [(row, hub) for row in range(hit_row + 1, far)]
        + [(hub, col) for col in range(hit_row + 1, far)]
    )
    for row, col in cells:
        if overwrite or out[row][col] == 0:
            out[row][col] = color
    return out


def _selected_hit(base, mode: str) -> int:
    hub = len(base) // 2
    hits = [row for row in range(hub) if base[row][hub] > 0]
    if not hits:
        raise ValueError("shortcut input has no completed north-ray hit")
    if mode == "nearest_hit":
        return max(hits)
    if mode == "farthest_hit":
        return min(hits)
    raise ValueError("selected mode has no cross hit")


def rival_output(grid, selected_mode: str, rival_name: str) -> list[list[int]]:
    if selected_mode not in oracle.MODES:
        raise ValueError("unknown selected mode")
    if rival_name not in RIVAL_NAMES:
        raise ValueError("unknown rival")

    if rival_name in ("paired_only", "row_axis_only", "column_axis_only"):
        base = restricted_completion(grid, rival_name)
        if selected_mode == "complete_only":
            return base
        try:
            hit = _selected_hit(base, selected_mode)
        except ValueError as error:
            if str(error) == "shortcut input has no completed north-ray hit":
                return base
            raise
        return _cross(base, hit, base[hit][len(base) // 2])

    base = oracle.complete_rings(grid)
    hub = len(base) // 2
    hits = [row for row in range(hub) if base[row][hub] > 0]
    if rival_name == "fixed_middle_hit":
        hit = hits[len(hits) // 2]
        return _cross(base, hit, base[hit][hub])

    # Wrongly use the same ring's corner color rather than the completed side
    # hit color.  For a no-cross selected rule, this rival still invents a
    # nearest-ring cross and is therefore observably wrong.
    mode = selected_mode if selected_mode != "complete_only" else "nearest_hit"
    hit = _selected_hit(base, mode)
    return _cross(base, hit, base[hit][hit])


def audit_episode(episode, selected_mode: str, *, rival_names=RIVAL_NAMES) -> list[dict]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    reports = []
    for name in rival_names:
        if name not in RIVAL_NAMES:
            raise ValueError(f"unknown rival: {name}")
        demo_mismatches = [
            index
            for index, pair in enumerate(episode["train"])
            if rival_output(pair["input"], selected_mode, name) != pair["output"]
        ]
        query_mismatches = [
            index
            for index, pair in enumerate(episode["test"])
            if rival_output(pair["input"], selected_mode, name) != pair["output"]
        ]
        reports.append(
            {
                "name": name,
                "fits_all_demos": not demo_mismatches,
                "demo_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )
    return reports
