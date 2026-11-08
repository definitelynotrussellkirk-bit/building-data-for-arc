"""Episode-fixed row/column closure variants for ``ccbf7456811b``.

The canonical setting closes each candidate on occupied rows.  The alternative
closes on occupied columns.  Both then score the resulting, input-dependent
closures against the orange target, select by overlap/extra/color, and crop the
winning closure in cyan.  Input scenes are matched across settings.

Python outputs are deterministic claims; native qualification re-executes every
label through protected Racket.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

TASK_ID = "ccbf7456811b"
HERE = Path(__file__).resolve().parent
SETTINGS = ({"closure_axis": "row"}, {"closure_axis": "column"})

# height, width, target row, target col, target height, target width,
# target-pattern id, candidate-geometry id, optional tie axis, edge stress.
_DEMO_PROFILES = (
    (13, 15, 5, 5, 3, 4, 0, 0, "row", False),
    (13, 15, 5, 5, 3, 4, 0, 1, "column", False),
    (15, 17, 5, 6, 4, 5, 1, 2, "row", False),
    (18, 20, 6, 7, 6, 6, 2, 3, None, False),
    (22, 24, 7, 8, 8, 8, 3, 4, None, False),
    (26, 27, 8, 9, 10, 9, 4, 5, None, False),
)
_QUERY_PROFILES = (
    (13, 14, 5, 5, 3, 4, 5, 6, None, False),
    (17, 19, 5, 6, 6, 7, 6, 7, "column", False),
    (24, 27, 7, 8, 10, 11, 7, 8, None, False),
    (30, 30, 8, 8, 14, 14, 8, 9, None, True),
)

_ROW_CYCLES = (
    ((1, 3), (2, 1), (1, 2), (3, 1)),
    ((3, 1), (1, 2), (2, 3), (1, 3)),
    ((1, 2), (3, 1), (2, 3), (1, 3)),
    ((2, 1), (1, 3), (3, 2), (1, 2)),
)
_COL_CYCLES = (
    ((2, 1), (1, 3), (3, 1), (1, 2)),
    ((1, 3), (2, 1), (1, 2), (3, 1)),
    ((3, 1), (1, 2), (2, 3), (1, 3)),
    ((1, 2), (3, 1), (2, 1), (1, 3)),
)
_TIE_MAIN = ((1, 3), (2, 1), (1, 2), (3, 1))
_TIE_OTHER = ((3, 1), (1, 2), (2, 1), (1, 3))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _axis(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"closure_axis"}
        or type(settings["closure_axis"]) is not str
        or settings["closure_axis"] not in {"row", "column"}
    ):
        raise ValueError("settings must be exactly {'closure_axis': 'row'|'column'}")
    return settings["closure_axis"]


def program(settings):
    axis = _axis(settings)
    return (HERE / ("canonical.rkt" if axis == "row" else "column.rkt")).read_text()


def _rng(seed, split, index):
    payload = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _target_cells(r0, c0, height, width, pattern):
    active_rows = [
        row
        for row in range(height)
        if row in {0, height - 1} or height < 5 or (row + pattern) % 5 != 2
    ]
    active_cols = [
        col
        for col in range(width)
        if col in {0, width - 1} or width < 6 or (col + 2 * pattern) % 6 != 3
    ]
    cells = set()
    for row in active_rows:
        for col in active_cols:
            if (3 * row + 5 * col + pattern) % 5 in {0, 1, 3}:
                cells.add((r0 + row, c0 + col))
    # Pin every declared row/column into the target while keeping the mask
    # irregular.  This makes the closure intermediate genuinely input-derived.
    for index, row in enumerate(active_rows):
        cells.add((r0 + row, c0 + active_cols[(2 * index + pattern) % len(active_cols)]))
    for index, col in enumerate(active_cols):
        cells.add((r0 + active_rows[(3 * index + pattern) % len(active_rows)], c0 + col))
    return cells


def _paint(grid, cells, color):
    for row, col in cells:
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise AssertionError("profile cell escapes grid")
        if grid[row][col] != 0:
            raise AssertionError(f"profile roles overlap at {(row, col)}")
        grid[row][col] = color


def _pairs(cycle, count, offset):
    return [cycle[(index + offset) % len(cycle)] for index in range(count)]


def _row_markers(active_rows, left, right, margins):
    return {
        point
        for row, (l_margin, r_margin) in zip(active_rows, margins)
        for point in ((row, left - l_margin), (row, right + r_margin))
    }


def _column_markers(active_cols, top, bottom, margins):
    return {
        point
        for col, (t_margin, b_margin) in zip(active_cols, margins)
        for point in ((top - t_margin, col), (bottom + b_margin, col))
    }


def _profile(split, index):
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    return profiles[index]


def sample_input(seed, split, index):
    """Return a deterministic setting-independent input for one source slot."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    h, w, r0, c0, th, tw, pattern, geometry, tie_axis, edge = _profile(split, index)
    target = _target_cells(r0, c0, th, tw, pattern)
    active_rows = sorted({row for row, _ in target})
    active_cols = sorted({col for _, col in target})
    top, bottom = r0, r0 + th - 1
    left, right = c0, c0 + tw - 1

    rng = _rng(seed, split, index)
    colors = sorted(rng.sample([1, 2, 3, 4, 5, 6, 9], 6))
    if tie_axis == "row":
        role_colors = {
            "row_main": colors[0],
            "extra": colors[5],
            "column_main": colors[4],
            "row_decoy": colors[1],
            "column_decoy": colors[2],
            "partial": colors[3],
        }
    elif tie_axis == "column":
        role_colors = {
            "column_main": colors[0],
            "extra": colors[5],
            "row_main": colors[4],
            "row_decoy": colors[2],
            "column_decoy": colors[1],
            "partial": colors[3],
        }
    else:
        # Rank-based role schedules deliberately make a lower-colored decoy
        # beat each intended winner under color/frequency shortcuts in the
        # minimum profiles, while the actual overlap/extra rule still wins.
        schedules = (
            (4, 5, 2, 0, 3, 1),
            (5, 4, 0, 2, 3, 1),
            (3, 5, 0, 1, 4, 2),
            (5, 3, 1, 0, 4, 2),
        )
        ranks = schedules[geometry % len(schedules)]
        role_colors = dict(
            zip(
                ("row_main", "column_main", "row_decoy", "column_decoy", "extra", "partial"),
                (colors[rank] for rank in ranks),
            )
        )

    if tie_axis == "row":
        row_main_margins = _pairs(_TIE_MAIN, len(active_rows), 0)
        extra_margins = _pairs(_TIE_OTHER, len(active_rows), 0)
    else:
        row_main_margins = _pairs(_ROW_CYCLES[geometry % len(_ROW_CYCLES)], len(active_rows), geometry)
        extra_margins = None
    if tie_axis == "column":
        col_main_margins = _pairs(_TIE_MAIN, len(active_cols), 0)
        extra_margins = _pairs(_TIE_OTHER, len(active_cols), 0)
    else:
        col_main_margins = _pairs(_COL_CYCLES[geometry % len(_COL_CYCLES)], len(active_cols), geometry)

    if edge:
        row_decoy_margins = [(left, w - 1 - right) for _ in active_rows]
        col_decoy_margins = [(top, h - 1 - bottom) for _ in active_cols]
    else:
        row_decoy_margins = [(5, 5) for _ in active_rows]
        col_decoy_margins = [(5, 5) for _ in active_cols]

    grid = [[0 for _ in range(w)] for _ in range(h)]
    _paint(grid, target, 7)
    _paint(grid, _row_markers(active_rows, left, right, row_main_margins), role_colors["row_main"])
    _paint(grid, _column_markers(active_cols, top, bottom, col_main_margins), role_colors["column_main"])
    _paint(grid, _row_markers(active_rows, left, right, row_decoy_margins), role_colors["row_decoy"])
    _paint(grid, _column_markers(active_cols, top, bottom, col_decoy_margins), role_colors["column_decoy"])

    partial_rows = active_rows[::2]
    if len(partial_rows) == len(active_rows):
        partial_rows = partial_rows[:-1]
    partial_cols = active_cols[1::2] or active_cols[:1]
    if len(partial_cols) == len(active_cols):
        partial_cols = partial_cols[:-1]
    partial_cells = _row_markers(
        partial_rows, left, right, [(4, 4) for _ in partial_rows]
    ) | _column_markers(
        partial_cols, top, bottom, [(4, 4) for _ in partial_cols]
    )
    _paint(grid, partial_cells, role_colors["partial"])

    if tie_axis == "row":
        _paint(grid, _row_markers(active_rows, left, right, extra_margins), role_colors["extra"])
    elif tie_axis == "column":
        _paint(grid, _column_markers(active_cols, top, bottom, extra_margins), role_colors["extra"])
    else:
        # A small no-overlap distractor.  Search deterministically so it remains
        # disjoint even in edge-stress profiles.
        placed = None
        for row in range(h):
            for col in range(w - 1):
                cells = {(row, col), (row, col + 1)}
                if all(grid[r][c] == 0 for r, c in cells):
                    placed = cells
                    break
            if placed is not None:
                break
        if placed is None:
            raise AssertionError("profile has no room for distractor")
        _paint(grid, placed, role_colors["extra"])
    return grid


def _grid(value):
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return value


def _points(grid, color):
    return {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color}


def target_mask(grid):
    _grid(grid)
    return sorted(_points(grid, 7))


def close_cells(cells, axis):
    if axis not in {"row", "column"}:
        raise ValueError("axis must be row or column")
    closed = set()
    if axis == "row":
        for row in {r for r, _ in cells}:
            cols = [c for r, c in cells if r == row]
            closed.update((row, col) for col in range(min(cols), max(cols) + 1))
    else:
        for col in {c for _, c in cells}:
            rows = [r for r, c in cells if c == col]
            closed.update((row, col) for row in range(min(rows), max(rows) + 1))
    return closed


def score_candidates(grid, axis):
    grid = _grid(grid)
    if axis not in {"row", "column"}:
        raise ValueError("axis must be row or column")
    target = _points(grid, 7)
    if not target:
        raise ValueError("missing color-7 target")
    rows = []
    for color in sorted({value for values in grid for value in values} - {0, 7}):
        closed = close_cells(_points(grid, color), axis)
        overlap = len(closed & target)
        rows.append({
            "color": color,
            "overlap": overlap,
            "extra": len(closed) - overlap,
            "closed": sorted(closed),
        })
    if not rows:
        raise ValueError("missing candidate colors")
    return sorted(rows, key=lambda row: (-row["overlap"], row["extra"], row["color"]))


def solve(grid, axis):
    winner = score_candidates(grid, axis)[0]["closed"]
    r0 = min(row for row, _ in winner)
    r1 = max(row for row, _ in winner)
    c0 = min(col for _, col in winner)
    c1 = max(col for _, col in winner)
    output = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for row, col in winner:
        output[row - r0][col - c0] = 8
    return output


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    axis = _axis(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate generated input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": solve(grid, axis)})
    return result
