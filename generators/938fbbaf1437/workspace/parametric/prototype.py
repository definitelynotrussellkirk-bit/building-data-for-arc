"""Deterministic two-setting episode family for nested frame counting."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path

TASK_ID = "938fbbaf1437"
ALLOWED_MODES = ("all", "squares")
HOME = Path(__file__).resolve().parent


def _validate_mode(value) -> str:
    if type(value) is not str or value not in ALLOWED_MODES:
        raise ValueError(f"counted_frames must be one of {ALLOWED_MODES}")
    return value


def _validate_counts(demos, queries) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def program_for(counted_frames: str) -> str:
    mode = _validate_mode(counted_frames)
    name = "canonical.rkt" if mode == "all" else "square_only.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def _draw_outline(grid, box) -> None:
    r0, c0, h, w = box
    r1, c1 = r0 + h - 1, c0 + w - 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = 1
    for r in range(r0, r1 + 1):
        grid[r][c0] = grid[r][c1] = 1


def _boxes(seed: int, sample_index: int, total: int, h: int, w: int):
    salt = hashlib.sha256(f"{TASK_ID}:{seed}:{sample_index}:{total}".encode()).digest()
    base = min(h, w) - 2
    if base < 17:
        raise ValueError("scene too small for mixed nested frame shapes")

    # Cycle which proper nesting depth is square.  This prevents a fixed
    # outer/middle/inner selector from fitting the visible lesson while keeping
    # every scene mixed between square and non-square frames.
    square_depth = sample_index % 3
    if square_depth == 0:
        dimensions = [(base, base), (base - 4, base - 6), (base - 8, base - 10)]
    elif square_depth == 1:
        dimensions = [(base, base - 2), (base - 6, base - 6), (base - 10, base - 12)]
    else:
        dimensions = [(base, base - 2), (base - 4, base - 6), (base - 10, base - 10)]
    if salt[2] % 2:
        dimensions = [(width, height) for height, width in dimensions]

    outer_h, outer_w = dimensions[0]
    row_slack = h - outer_h
    col_slack = w - outer_w
    r0 = 1 + salt[0] % (row_slack - 1)
    c0 = 1 + salt[1] % (col_slack - 1)
    boxes = [(r0, c0, outer_h, outer_w)]
    for level, (height, width) in enumerate(dimensions[1:], start=1):
        pr, pc, ph, pw = boxes[-1]
        row_shift = 2 + salt[3 + 2 * level] % (ph - height - 3)
        col_shift = 2 + salt[4 + 2 * level] % (pw - width - 3)
        boxes.append((pr + row_shift, pc + col_shift, height, width))
    return boxes


def build_input(seed: int, sample_index: int, total: int) -> list[list[int]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or not 0 <= sample_index < total:
        raise ValueError("sample_index outside episode")
    if sample_index == total - 1:
        h = w = 30
    else:
        # The largest supported episode has ten pairs.  Give every non-stress
        # pair a distinct shape so uniqueness does not depend on incidental
        # layout hashes.
        h = 19 + sample_index
        w = 29 - sample_index
    grid = [[0 for _ in range(w)] for _ in range(h)]
    boxes = _boxes(seed, sample_index, total, h, w)
    for box in boxes:
        _draw_outline(grid, box)
    r0, c0, fh, fw = boxes[-1]
    grid[r0 + fh // 2][c0 + fw // 2] = 1
    # On alternating inputs add an isolated exterior singleton when the margin permits.
    if sample_index % 2 and boxes[0][0] >= 2 and boxes[0][1] >= 2:
        grid[0][0] = 1
    return grid


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def _frame(cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    border = (
        {(r0, c) for c in range(c0, c1 + 1)}
        | {(r1, c) for c in range(c0, c1 + 1)}
        | {(r, c0) for r in range(r0, r1 + 1)}
        | {(r, c1) for r in range(r0, r1 + 1)}
    )
    return (r0, r1, c0, c1) if cells == border else None


def frames(grid):
    return [box for cells in _components(grid) if (box := _frame(cells)) is not None]


def frame_shape_kinds(grid) -> set[str]:
    result = set()
    for r0, r1, c0, c1 in frames(grid):
        h, w = r1 - r0 + 1, c1 - c0 + 1
        if h == w == 1:
            continue
        result.add("square" if h == w else "rectangle")
    return result


def python_mirror(grid, *, counted_frames: str):
    mode = _validate_mode(counted_frames)
    selected = [
        box
        for box in frames(grid)
        if mode == "all" or box[1] - box[0] == box[3] - box[2]
    ]
    return [
        [
            0
            if value == 0
            else 1 + sum(r0 <= r <= r1 and c0 <= c <= c1 for r0, r1, c0, c1 in selected)
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def generate_claims(seed: int, counted_frames: str, *, demos=3, queries=4):
    mode = _validate_mode(counted_frames)
    _validate_counts(demos, queries)
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    total = demos + queries
    pairs = []
    for index in range(total):
        grid = build_input(seed, index, total)
        pairs.append({"input": grid, "output": python_mirror(grid, counted_frames=mode)})
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(mode),
    }
