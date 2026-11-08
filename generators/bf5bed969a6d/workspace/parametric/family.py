"""Template-orientation family for bf5bed969a6d.

Step A extracts and normalizes the input's color-2 template.  Step B centers a
frame-colored copy in every non-template same-color component.  The alternative
rotates the extracted intermediate 90 degrees clockwise before Step B.
"""
from __future__ import annotations

from collections import deque
import hashlib
import random

TASK_ID = "bf5bed969a6d"
VERSION = "native-template-orientation-v1"
TRANSFORMS = ("as_is", "rotate_cw")
PALETTE = (1, 3, 4, 5, 6, 7, 8, 9)

_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (2, 2)),
)

_DEMO_SPECS = (
    {"canvas": (12, 15), "shape": 0, "frames": ((1, 5, 6, 5), (1, 10, 7, 5)), "template": (8, 1)},
    {"canvas": (14, 17), "shape": 1, "frames": ((1, 6, 8, 7), (5, 3, 7, 11)), "template": (1, 1)},
    {"canvas": (16, 19), "shape": 2, "frames": ((1, 1, 8, 8), (1, 11, 9, 7)), "template": (11, 2)},
    {"canvas": (18, 21), "shape": 3, "frames": ((2, 8, 10, 9), (7, 4, 9, 14)), "template": (1, 1)},
    {"canvas": (23, 25), "shape": 4, "frames": ((2, 2, 11, 10), (2, 14, 12, 9)), "template": (16, 3)},
    {"canvas": (27, 29), "shape": 5, "frames": ((2, 10, 15, 14), (10, 4, 14, 22)), "template": (2, 2)},
)
_QUERY_SPECS = (
    {"canvas": (15, 18), "shape": 6, "frames": ((1, 1, 8, 8), (1, 10, 10, 7)), "template": (11, 3)},
    {"canvas": (20, 23), "shape": 7, "frames": ((2, 8, 12, 10), (8, 3, 10, 17)), "template": (2, 2)},
    {"canvas": (25, 28), "shape": 8, "frames": ((2, 2, 13, 11), (2, 16, 14, 10)), "template": (18, 4)},
    {"canvas": (30, 30), "shape": 9, "frames": ((2, 6, 24, 22), (7, 3, 20, 25)), "template": (1, 1)},
)


def _exact_int(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_transform(value: object) -> str:
    if type(value) is not str or value not in TRANSFORMS:
        raise ValueError(f"template_transform must be one of {TRANSFORMS}")
    return value


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells):
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _d4(cells, transform: int):
    cells = _normalize(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    if transform == 0:
        raw = cells
    elif transform == 1:
        raw = ((c, h - 1 - r) for r, c in cells)
    elif transform == 2:
        raw = ((h - 1 - r, w - 1 - c) for r, c in cells)
    elif transform == 3:
        raw = ((w - 1 - c, r) for r, c in cells)
    elif transform == 4:
        raw = ((r, w - 1 - c) for r, c in cells)
    elif transform == 5:
        raw = ((c, r) for r, c in cells)
    elif transform == 6:
        raw = ((h - 1 - r, c) for r, c in cells)
    elif transform == 7:
        raw = ((w - 1 - c, h - 1 - r) for r, c in cells)
    else:
        raise ValueError("bad D4 transform")
    return _normalize(raw)


def _rotate_grid(grid: list[list[int]], turns: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _draw_frame(grid, top, left, height, width, color):
    if top < 0 or left < 0 or top + height > len(grid) or left + width > len(grid[0]):
        raise ValueError("frame outside canvas")
    for c in range(left, left + width):
        grid[top][c] = color
        grid[top + height - 1][c] = color
    for r in range(top, top + height):
        grid[r][left] = color
        grid[r][left + width - 1] = color


def _render(spec: dict, rng: random.Random) -> list[list[int]]:
    height, width = spec["canvas"]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    colors = rng.sample(PALETTE, 2)
    for frame, color in zip(spec["frames"], colors):
        _draw_frame(grid, *frame, color)
    shape = _d4(_SHAPES[spec["shape"]], rng.randrange(8))
    top, left = spec["template"]
    if any(not (0 <= top + r < height and 0 <= left + c < width) for r, c in shape):
        raise ValueError("template outside canvas")
    if any(grid[top + r][left + c] != 0 for r, c in shape):
        raise ValueError("template overlaps frame")
    for r, c in shape:
        grid[top + r][left + c] = 2
    return _rotate_grid(grid, rng.randrange(4))


def _components(grid: list[list[int]]):
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)):
        raise ValueError("grid must be nonempty rectangular lists")
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def same_color_component_count(grid: list[list[int]]) -> int:
    return len(_components(grid))


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def template_intermediate(grid: list[list[int]], template_transform: str) -> dict:
    mode = validate_transform(template_transform)
    templates = [cells for color, cells in _components(grid) if color == 2]
    if len(templates) != 1:
        raise ValueError("expected exactly one color-2 template component")
    source = templates[0]
    offsets = _normalize(source)
    if mode == "rotate_cw":
        offsets = _rotate_cw(offsets)
    height = max(r for r, _ in offsets) + 1
    width = max(c for _, c in offsets) + 1
    return {"source_cells": source, "offsets": offsets, "height": height, "width": width}


def _paint_with_intermediate(grid: list[list[int]], intermediate: dict) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    th, tw = intermediate["height"], intermediate["width"]
    for color, cells in _components(grid):
        if color == 2:
            continue
        r0, c0, r1, c1 = _bbox(cells)
        interior_h = r1 - r0 - 1
        interior_w = c1 - c0 - 1
        start_r = r0 + 1 + ((interior_h - th) // 2)
        start_c = c0 + 1 + ((interior_w - tw) // 2)
        for r, c in cells:
            output[r][c] = color
        for dr, dc in intermediate["offsets"]:
            rr, cc = start_r + dr, start_c + dc
            if not (0 <= rr < len(output) and 0 <= cc < len(output[0])):
                raise ValueError("stamped template escaped canvas")
            output[rr][cc] = color
    return output


def transform(grid: list[list[int]], template_transform: str) -> list[list[int]]:
    return _paint_with_intermediate(grid, template_intermediate(grid, template_transform))


def transform_with_fixed_intermediate(grid: list[list[int]], template_transform: str) -> list[list[int]]:
    validate_transform(template_transform)
    fixed = {"source_cells": (), "offsets": ((0, 0), (0, 1), (1, 0)), "height": 2, "width": 2}
    return _paint_with_intermediate(grid, fixed)


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _DEMO_SPECS if split == "train" else _QUERY_SPECS
    return _render(specs[index], _rng(seed, split, index))


def generate_episode(seed: int, *, template_transform: str, demos: int, queries: int,
                     program_solution: str | None = None) -> dict:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    mode = validate_transform(template_transform)
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    train_inputs = [_input(seed, "train", i) for i in range(demos)]
    test_inputs = [_input(seed, "test", i) for i in range(queries)]
    result = {
        "train": [{"input": grid, "output": transform(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, mode)} for grid in test_inputs],
    }
    if program_solution is not None:
        result["program_solution"] = program_solution
    return result
