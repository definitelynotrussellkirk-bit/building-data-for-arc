"""Proposed preserve-existing/complete-bbox border family for b570c79ec730.

Every generated lesson includes a connected thick component with a missing
non-corner bbox-edge cell.  That witness distinguishes the canonical policy,
which preserves only existing component boundary cells, from the retained
full-bbox-outline shortcut, which completes each bounding-box perimeter.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

TASK_ID = "b570c79ec730"
PARAMETER = "border_policy"
SETTINGS = ("preserve_existing", "complete_bbox")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "preserve_existing": _HOME / "preserve-existing.rkt",
    "complete_bbox": _HOME / "complete-bbox.rkt",
}
_TRAIN_PROFILES = (
    (8, 9, 2, 0),
    (10, 13, 2, 1),
    (12, 16, 3, 2),
    (15, 18, 3, 3),
    (20, 24, 4, 4),
    (24, 28, 4, 5),
)
_QUERY_PROFILES = (
    (8, 10, 2, 10),
    (16, 20, 3, 11),
    (23, 29, 4, 12),
    (30, 30, 5, 13),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ANCHORS = ("TL", "BR", "TR", "BL", "C")


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program(settings: dict[str, str]) -> str:
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|inputs-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _component_dims(h: int, w: int, count: int) -> list[tuple[int, int]]:
    if h <= 8:
        return [(4, 4), (4, 5)][:count]
    if h <= 10:
        return [(5, 5), (5, 6)][:count]
    bank = [(6, 7), (7, 6), (5, 8), (8, 5), (7, 7)]
    return [(min(sh, h // 2 - 1), min(sw, w // 2 - 1)) for sh, sw in bank[:count]]


def _origin(anchor: str, sh: int, sw: int, h: int, w: int) -> tuple[int, int]:
    if anchor == "TL":
        return 0, 0
    if anchor == "TR":
        return 0, w - sw
    if anchor == "BL":
        return h - sh, 0
    if anchor == "BR":
        return h - sh, w - sw
    return (h - sh) // 2, (w - sw) // 2


def _notched_rectangle(sh: int, sw: int, slot: int) -> set[tuple[int, int]]:
    if sh < 4 or sw < 4:
        raise ValueError("notched witness requires dimensions at least 4x4")
    cells = {(r, c) for r in range(sh) for c in range(sw)}
    side = slot % 4
    if side == 0:
        notch = (0, 1 + (slot % (sw - 2)))
    elif side == 1:
        notch = (sh - 1, 1 + (slot % (sw - 2)))
    elif side == 2:
        notch = (1 + (slot % (sh - 2)), 0)
    else:
        notch = (1 + (slot % (sh - 2)), sw - 1)
    cells.remove(notch)
    # A second interior hole on alternating profiles adds negative space without
    # changing the bbox or disconnecting the solid rectangle.
    if slot % 2 and sh >= 5 and sw >= 5:
        cells.remove((sh // 2, sw // 2))
    return cells


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, count, tag = (_TRAIN_PROFILES if split == "train" else _QUERY_PROFILES)[index]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    rng = _rng(seed, split, index)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    anchors = list(_ANCHORS[:count])
    if tag % 2:
        anchors[:4] = anchors[:4][1:] + anchors[:4][:1]
    for component_index, ((sh, sw), anchor, color) in enumerate(zip(_component_dims(h, w, count), anchors, colors)):
        top, left = _origin(anchor, sh, sw, h, w)
        shape = _notched_rectangle(sh, sw, tag + component_index)
        for r, c in shape:
            rr, cc = top + r, left + c
            if grid[rr][cc] != 0:
                raise RuntimeError("component packing overlap")
            grid[rr][cc] = color
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(type(row) is not list or len(row) != width or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(grid), width


def components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    found: list[tuple[int, set[tuple[int, int]]]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        found.append((color, comp))
    return found


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def missing_boundary_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    result = []
    for color, cells in components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r in (r1, r2) or c in (c1, c2)) and (r, c) not in cells:
                    result.append((r, c, color))
    return result


def apply_rule(grid: list[list[int]], border_policy: str) -> list[list[int]]:
    if type(border_policy) is not str or border_policy not in SETTINGS:
        raise ValueError(f"border_policy must be one of {SETTINGS!r}")
    _validate_grid(grid)
    output = [row[:] for row in grid]
    for color, cells in components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for r, c in cells:
            if r1 < r < r2 and c1 < c < c2:
                output[r][c] = 0
        if border_policy == "complete_bbox":
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    if r in (r1, r2) or c in (c1, c2):
                        output[r][c] = color
    return output


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    selected = _validate_settings(settings)
    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, selected)})
    serialized = [repr(pair["input"]) for pair in [*train, *test]]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}
