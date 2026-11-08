"""Independent parser, oracle, and audit helpers for task 81d29e66f427.

This module is test tooling, not label authority.  It deliberately does not
import implementation helpers from ``generator.py`` so it can catch parser and
layout mistakes in the selected generator.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Callable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "81d29e66f427"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_HOME = HERE.parent.parent


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py")
    source = source.resolve()
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_{source.stat().st_mtime_ns}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while q:
                rr, cc = q.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            result.append(cells)
    return result


def frames(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    result = []
    for cells in _components(grid, 5):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        box = min(rs), min(cs), max(rs), max(cs)
        r1, c1, r2, c2 = box
        border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if cells == border and r2 - r1 >= 2 and c2 - c1 >= 2:
            result.append(box)
    return sorted(result, key=lambda box: box[1])


def parse(grid: list[list[int]]) -> dict:
    boxes = frames(grid)
    if len(boxes) != 2:
        raise ValueError(f"expected two color-5 frames, found {len(boxes)}")
    left, right = boxes
    l_r1, l_c1, l_r2, l_c2 = left
    r_r1, r_c1, r_r2, r_c2 = right
    if (l_r2 - l_r1, l_c2 - l_c1) != (r_r2 - r_r1, r_c2 - r_c1):
        raise ValueError("frame interiors differ")
    ih, iw = l_r2 - l_r1 - 1, l_c2 - l_c1 - 1
    keys = [value for value in grid[0] if value != 0]
    a = {
        (r - l_r1 - 1, c - l_c1 - 1)
        for r in range(l_r1 + 1, l_r2)
        for c in range(l_c1 + 1, l_c2)
        if grid[r][c] == 2
    }
    b = {
        (r - r_r1 - 1, c - r_c1 - 1)
        for r in range(r_r1 + 1, r_r2)
        for c in range(r_c1 + 1, r_c2)
        if grid[r][c] == 3
    }
    return {
        "frames": boxes,
        "keys": keys,
        "a": a,
        "b": b,
        "interior_h": ih,
        "interior_w": iw,
        "gap": r_c1 - l_c2 - 1,
    }


def _panel(a: set[tuple[int, int]], b: set[tuple[int, int]], key: int) -> set[tuple[int, int]]:
    if key == 2:
        return a | b
    if key == 3:
        return a & b
    return a ^ b


def gallery(
    grid: list[list[int]],
    operation: Callable[[set[tuple[int, int]], set[tuple[int, int]], int], set[tuple[int, int]]] = _panel,
) -> list[list[int]]:
    info = parse(grid)
    ih, iw = info["interior_h"], info["interior_w"]
    keys = info["keys"]
    out = [[0] * (len(keys) * iw + len(keys) - 1) for _ in range(ih)]
    for index, key in enumerate(keys):
        for r, c in operation(info["a"], info["b"], key):
            out[r][index * (iw + 1) + c] = 8
    return out


def observed(grid: list[list[int]]) -> dict[str, int]:
    info = parse(grid)
    return {
        "interior_h": info["interior_h"],
        "interior_w": info["interior_w"],
        "n_keys": len(info["keys"]),
        "gap": info["gap"],
    }


def truth_state_counts(grid: list[list[int]]) -> dict[str, int]:
    info = parse(grid)
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    for r in range(info["interior_h"]):
        for c in range(info["interior_w"]):
            counts[f"{int((r, c) in info['a'])}{int((r, c) in info['b'])}"] += 1
    return counts


def key4_only_xor(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: key 4 means xor; other unknown keys are blank."""
    def operation(a, b, key):
        if key == 2:
            return a | b
        if key == 3:
            return a & b
        return a ^ b if key == 4 else set()
    return gallery(grid, operation)


def fixed_or_and_xor_order(grid: list[list[int]]) -> list[list[int]]:
    """Ignore key values and emit OR, AND, XOR cyclically in fixed order."""
    sequence = (2, 3, 4)
    call_index = -1

    def operation(a, b, _key):
        nonlocal call_index
        call_index += 1
        return _panel(a, b, sequence[call_index % len(sequence)])

    return gallery(grid, operation)


def all_one_operation(grid: list[list[int]], key: int) -> list[list[int]]:
    return gallery(grid, lambda a, b, _actual: _panel(a, b, key))
