"""Native parametric family for the frame-docking puzzle.

The default is the exact canonical program. The alternative first performs the
same rigid slide, then uses the post-dock red/cyan contact cells as seeds for
inward yellow (4) rays through the hollow frame. Input sampling is independent
of the private episode setting and includes a substantive 30x30 query.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
FINISHES = ("dock_only", "contact_projection")
_STEP = {"right": (0, 1), "left": (0, -1), "down": (1, 0), "up": (-1, 0)}

# h, w, direction, object perpendicular span, object depth,
# frame perpendicular span, frame depth, source gap.
_DEMO_PROFILES = (
    (10, 12, "right", 3, 3, 5, 4, 1),
    (12, 14, "down", 4, 3, 7, 5, 2),
    (13, 15, "left", 5, 4, 8, 5, 2),
    (15, 16, "up", 5, 4, 9, 6, 3),
    (18, 20, "right", 6, 5, 10, 8, 3),
    (20, 22, "down", 7, 6, 12, 9, 3),
)
_QUERY_PROFILES = (
    (11, 13, "left", 4, 3, 7, 5, 1),
    (18, 20, "up", 6, 5, 11, 8, 3),
    (24, 26, "right", 8, 7, 14, 11, 4),
    (30, 30, "down", 11, 9, 18, 13, 4),
)


def _finish(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"finish"}
            or type(settings["finish"]) is not str
            or settings["finish"] not in FINISHES):
        raise ValueError("settings must contain exactly one supported finish")
    return settings["finish"]


def _integer(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")
    return value


def program(settings) -> str:
    finish = _finish(settings)
    name = "canonical.rkt" if finish == "dock_only" else "contact_projection.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be a rectangular list of lists")
    if any(type(v) is not int or v not in (0, 2, 8) for row in grid for v in row):
        raise ValueError("input cells must be exact integer colors 0, 2, or 8")
    return len(grid), width


def _cells(grid, color: int) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not cells:
        raise ValueError("required colored object is absent")
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _direction(red: set[tuple[int, int]], cyan: set[tuple[int, int]]) -> str:
    rr1, rc1, rr2, rc2 = _bbox(red)
    fr1, fc1, fr2, fc2 = _bbox(cyan)
    if rc2 < fc1:
        return "right"
    if rc1 > fc2:
        return "left"
    if rr2 < fr1:
        return "down"
    if rr1 > fr2:
        return "up"
    raise ValueError("red object must lie wholly on one cardinal side of the frame")


def _slide(red, blockers, step, h, w):
    dr, dc = step
    current = set(red)
    while True:
        nxt = {(r + dr, c + dc) for r, c in current}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in nxt) or nxt & blockers:
            return current
        current = nxt


def _paint_docked(grid, red, docked):
    out = deepcopy(grid)
    for r, c in red:
        out[r][c] = 0
    for r, c in docked:
        out[r][c] = 2
    return out


def _projection_cells(grid, contacts, step):
    h, w = len(grid), len(grid[0])
    dr, dc = step
    result = []
    for row, col in contacts:
        row, col = row + dr, col + dc
        while 0 <= row < h and 0 <= col < w and grid[row][col] == 0:
            result.append((row, col))
            row, col = row + dr, col + dc
    return sorted(set(result))


def _state(grid):
    h, w = _validate_grid(grid)
    red, cyan = _cells(grid, 2), _cells(grid, 8)
    direction = _direction(red, cyan)
    step = _STEP[direction]
    blockers = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value not in (0, 2)}
    docked = _slide(red, blockers, step, h, w)
    docked_grid = _paint_docked(grid, red, docked)
    dr, dc = step
    contacts = sorted(
        (r + dr, c + dc)
        for r, c in docked
        if 0 <= r + dr < h and 0 <= c + dc < w
        and docked_grid[r + dr][c + dc] == 8
    )
    if not contacts:
        raise ValueError("docked object must contact the cyan frame")
    rays = _projection_cells(docked_grid, contacts, step)
    if not rays:
        raise ValueError("contact cells must seed a nonempty frame-interior projection")
    return direction, step, red, cyan, docked, contacts, rays, docked_grid


def dock_intermediate(grid):
    direction, step, _red, _cyan, docked, contacts, rays, _grid = _state(grid)
    return {"direction": direction, "step": list(step),
            "docked_cells": sorted(docked), "contact_cells": contacts,
            "projection_cells": rays}


def solve(grid, finish):
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be a supported string")
    _direction_name, _step, _red, _cyan, _docked, _contacts, rays, out = _state(grid)
    if finish == "contact_projection":
        for r, c in rays:
            out[r][c] = 4
    return out


def bbox_projection_solve(grid):
    """Plausible rival: project every row/column in the docked red bbox."""
    direction, step, _red, cyan, docked, _contacts, _rays, out = _state(grid)
    r1, c1, r2, c2 = _bbox(docked)
    fr1, fc1, fr2, fc2 = _bbox(cyan)
    if direction == "right":
        contacts = [(r, fc1) for r in range(r1, r2 + 1)]
    elif direction == "left":
        contacts = [(r, fc2) for r in range(r1, r2 + 1)]
    elif direction == "down":
        contacts = [(fr1, c) for c in range(c1, c2 + 1)]
    else:
        contacts = [(fr2, c) for c in range(c1, c2 + 1)]
    for r, c in _projection_cells(out, contacts, step):
        out[r][c] = 4
    return out


def wrong_order_solve(grid):
    """Counterfactual B-before-A composition used by the causal witness."""
    h, w = _validate_grid(grid)
    red, cyan = _cells(grid, 2), _cells(grid, 8)
    direction = _direction(red, cyan)
    step = _STEP[direction]
    dr, dc = step
    early_contacts = sorted(
        (r + dr, c + dc) for r, c in red
        if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 8
    )
    preprojected = deepcopy(grid)
    for r, c in _projection_cells(preprojected, early_contacts, step):
        preprojected[r][c] = 4
    blockers = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value not in (0, 2)}
    docked = _slide(red, blockers, step, h, w)
    return _paint_docked(preprojected, red, docked)


def _comb_shape(span: int, depth: int, rng: random.Random):
    count = max(2, min(4, span // 3 + 1))
    contact_rows = set(rng.sample(range(span), count))
    low = max(2, depth // 2)
    lengths = [depth if row in contact_rows else rng.randint(low, depth - 1)
               for row in range(span)]
    for row in range(span):
        if row not in contact_rows:
            lengths[row] = depth - 1
            break
    return {(row, col) for row, length in enumerate(lengths) for col in range(length)}


def _orient(cells, span: int, depth: int, direction: str):
    if direction == "right":
        return set(cells)
    if direction == "left":
        return {(r, depth - 1 - c) for r, c in cells}
    if direction == "down":
        return {(c, r) for r, c in cells}
    return {(depth - 1 - c, r) for r, c in cells}


def _draw_frame(grid, top, left, frame_h, frame_w):
    for col in range(left, left + frame_w):
        grid[top][col] = 8
        grid[top + frame_h - 1][col] = 8
    for row in range(top + 1, top + frame_h - 1):
        grid[row][left] = 8
        grid[row][left + frame_w - 1] = 8


def _make_input(seed: int, stream: str, index: int, profile):
    h, w, direction, span, depth, frame_span, frame_depth, gap = profile
    rng = random.Random(f"43cca8eff94f:parametric-v1:{seed}:{stream}:{index}")
    shape = _orient(_comb_shape(span, depth, rng), span, depth, direction)
    obj_h = max(r for r, _ in shape) + 1
    obj_w = max(c for _, c in shape) + 1
    if direction in ("right", "left"):
        frame_h, frame_w = frame_span, frame_depth
        total = obj_w + gap + frame_w
        start = rng.randint(0, w - total)
        frame_top = rng.randint(0, h - frame_h)
        obj_top = frame_top + 1 + rng.randint(0, frame_h - 2 - obj_h)
        if direction == "right":
            obj_left, frame_left = start, start + obj_w + gap
        else:
            frame_left, obj_left = start, start + frame_w + gap
    else:
        frame_h, frame_w = frame_depth, frame_span
        total = obj_h + gap + frame_h
        start = rng.randint(0, h - total)
        frame_left = rng.randint(0, w - frame_w)
        obj_left = frame_left + 1 + rng.randint(0, frame_w - 2 - obj_w)
        if direction == "down":
            obj_top, frame_top = start, start + obj_h + gap
        else:
            frame_top, obj_top = start, start + frame_h + gap
    grid = [[0] * w for _ in range(h)]
    _draw_frame(grid, frame_top, frame_left, frame_h, frame_w)
    for row, col in shape:
        grid[obj_top + row][obj_left + col] = 2
    _state(grid)
    return grid


def generate(seed, settings, demos, queries):
    finish = _finish(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    demo_inputs = [_make_input(seed, "demo", i, profile)
                   for i, profile in enumerate(_DEMO_PROFILES)]
    query_inputs = [_make_input(seed, "query", i, profile)
                    for i, profile in enumerate(_QUERY_PROFILES)]
    keys = [tuple(map(tuple, grid)) for grid in demo_inputs + query_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("profile construction produced duplicate visible inputs")
    def pair(grid):
        return {"input": deepcopy(grid), "output": solve(grid, finish)}
    return {"train": [pair(grid) for grid in demo_inputs[:demos]],
            "test": [pair(grid) for grid in query_inputs[:queries]],
            "program_solution": program(settings)}
