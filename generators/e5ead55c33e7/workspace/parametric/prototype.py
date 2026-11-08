#!/usr/bin/env python3
"""Episode-fixed front/rear sequential packing orders for e5ead55c33e7."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

TASK_ID = "e5ead55c33e7"
PACKING_ORDERS = ("front_first", "rear_first")
DEFAULT_PACKING_ORDER = "front_first"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
HOME = Path(__file__).resolve().parent
CANONICAL_PATH = HOME / "canonical.rkt"

# (cells, contact-row).  Every object in a band is placed so its contact-row
# meets the band's shared row, guaranteeing a genuine collision chain.
_SHAPES = (
    (((0, 0), (0, 1), (0, 2)), 0),
    (((0, 0), (1, 0), (1, 1), (1, 2)), 1),
    (((0, 0), (0, 1), (1, 0), (1, 1)), 1),
    (((0, 0), (0, 1), (0, 2), (1, 1)), 0),
    (((0, 0), (1, 0), (1, 1), (2, 1)), 1),
    (((0, 1), (1, 0), (1, 1), (2, 0), (2, 1)), 1),
    (((0, 0), (0, 1), (1, 1), (1, 2)), 1),
    (((0, 0), (1, 0), (2, 0)), 1),
)


def _validate_packing_order(packing_order: str) -> None:
    if type(packing_order) is not str or packing_order not in PACKING_ORDERS:
        raise ValueError(
            f"packing_order must be one of {PACKING_ORDERS}, got {packing_order!r}"
        )


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact nonnegative integer below 2**63")


def _validate_grid(grid: list[list[int]], *, name: str = "grid") -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError(f"{name} must be a nonempty rectangular grid")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError(f"{name} must contain exact integer colors 0..9")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"{name} must fit inside 30x30")
    return len(grid), width


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def canonical_source() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError("canonical.rkt is empty")
    return source


def program_for(packing_order: str = DEFAULT_PACKING_ORDER) -> str:
    """Return exact Racket for one object-order policy."""
    _validate_packing_order(packing_order)
    source = canonical_source()
    if packing_order == "front_first":
        return source
    needle = """(lambda (a b)
              (if (= (obj-c2 a) (obj-c2 b))
                  (> (obj-r1 a) (obj-r1 b))
                  (> (obj-c2 a) (obj-c2 b))))"""
    replacement = """(lambda (a b)
              (if (= (obj-c2 a) (obj-c2 b))
                  (> (obj-r1 a) (obj-r1 b))
                  (< (obj-c2 a) (obj-c2 b))))"""
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded order comparator")
    return source.replace(needle, replacement, 1)


def extract_objects(grid: list[list[int]]) -> list[dict]:
    """Return four-connected color-2/3/4 components with canonical bbox fields."""
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    objects: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color not in (2, 3, 4) or (r, c) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = sorted({rr for rr, _ in cells})
            objects.append(
                {
                    "color": color,
                    "cells": cells,
                    "r1": min(rr for rr, _ in cells),
                    "r2": max(rr for rr, _ in cells),
                    "c1": min(cc for _, cc in cells),
                    "c2": max(cc for _, cc in cells),
                    "rows": rows,
                }
            )
    return objects


def _ordered_objects(objects: list[dict], packing_order: str) -> list[dict]:
    _validate_packing_order(packing_order)
    if packing_order == "front_first":
        return sorted(objects, key=lambda obj: (-obj["c2"], -obj["r1"]))
    return sorted(objects, key=lambda obj: (obj["c2"], -obj["r1"]))


def solve_python(
    grid: list[list[int]], *, packing_order: str = DEFAULT_PACKING_ORDER
) -> list[list[int]]:
    """Mirror the canonical clear/sort/slide/paint sequence."""
    h, w = _validate_grid(grid)
    objects = extract_objects(grid)
    out = [row[:] for row in grid]
    for obj in objects:
        for r, c in obj["cells"]:
            out[r][c] = 0
    occupied = {(r, c) for r in range(h) for c in range(w) if out[r][c] == 5}
    for obj in _ordered_objects(objects, packing_order):
        landed = list(obj["cells"])
        while True:
            shifted = [(r, c + 1) for r, c in landed]
            if any(
                not (0 <= r < h and 0 <= c < w) or (r, c) in occupied
                for r, c in shifted
            ):
                break
            landed = shifted
        for r, c in landed:
            out[r][c] = obj["color"]
            occupied.add((r, c))
    return out


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene_spec(seed: int, role: str, index: int) -> tuple[int, int, list[tuple[int, int]]]:
    """Return h, w, and (shared_row, object_count) bands."""
    if role == "test" and index == 3:
        return 30, 30, [(3, 5), (13, 5), (24, 5)]
    salt = seed + index * 5 + (0 if role == "train" else 19)
    if role == "train":
        h = 9 + salt % 5
        w = 16 + (salt // 2) % 5
        if index < 2:
            return h, w, [(max(2, h // 2), 3 + index % 2)]
        return max(h, 12), max(w, 19), [(3, 3 + index % 2), (8, 3)]
    specs = (
        (11, 18, [(4, 4)]),
        (15, 22, [(3, 4), (10, 3)]),
        (21, 26, [(4, 5), (15, 4)]),
    )
    return specs[index]


def _required_canvas_width(seed: int, index: int, bands: list[tuple[int, int]]) -> int:
    """Minimum width that fits every selected band plus a clear pre-wall column."""
    required = 0
    for band_index, (_shared_row, count) in enumerate(bands):
        shape_offset = (seed + index * 2 + band_index * 3) % len(_SHAPES)
        selected = [_SHAPES[(shape_offset + item) % len(_SHAPES)] for item in range(count)]
        widths = [max(c for _, c in cells) + 1 for cells, _contact in selected]
        mandatory_columns = sum(widths) + max(0, count - 1)
        start_left = 1 + band_index
        required = max(required, start_left + mandatory_columns + 2)
    return required


def _place_band(
    grid: list[list[int]],
    *,
    shared_row: int,
    count: int,
    start_left: int,
    shape_offset: int,
    color_offset: int,
    rng: random.Random,
) -> list[dict]:
    h, w = len(grid), len(grid[0])
    wall = w - 1
    selected = [_SHAPES[(shape_offset + index) % len(_SHAPES)] for index in range(count)]
    widths = [max(c for _, c in cells) + 1 for cells, _contact in selected]
    available_columns = wall - start_left - 1  # through wall-2, inclusive
    mandatory_columns = sum(widths) + max(0, count - 1)
    if mandatory_columns > available_columns:
        raise ValueError("band cannot fit while retaining one clear pre-wall column")
    extra_capacity = min(available_columns - mandatory_columns, max(0, count - 1))
    extra_gaps = [0 for _ in range(max(0, count - 1))]
    gap_indices = list(range(len(extra_gaps)))
    rng.shuffle(gap_indices)
    extra_count = rng.randrange(extra_capacity + 1) if extra_capacity else 0
    for gap_index in gap_indices[:extra_count]:
        extra_gaps[gap_index] = 1

    left = start_left
    placed: list[dict] = []
    for index, (cells, contact) in enumerate(selected):
        top = shared_row - contact
        width = widths[index]
        height = max(r for r, _ in cells) + 1
        if top < 0 or top + height > h:
            raise ValueError("band object does not fit vertically")
        if left + width - 1 >= wall - 1:
            raise AssertionError("precomputed band budget was violated")
        color = (2, 3, 4)[(color_offset + index) % 3]
        absolute = [(top + r, left + c) for r, c in cells]
        if any(grid[r][c] != 0 for r, c in absolute):
            raise ValueError("band objects overlap")
        for r, c in absolute:
            grid[r][c] = color
        placed.append({"color": color, "cells": absolute})
        if index < count - 1:
            left += width + 1 + extra_gaps[index]
    return placed


def build_input(seed: int, *, role: str, index: int) -> list[list[int]]:
    _validate_seed(seed)
    if role not in {"train", "test"}:
        raise ValueError("role must be train or test")
    limit = 6 if role == "train" else 4
    if type(index) is not int or not 0 <= index < limit:
        raise ValueError("sample index is out of range")
    h, w, bands = _scene_spec(seed, role, index)
    w = max(w, _required_canvas_width(seed, index, bands))
    if w > 30:
        raise ValueError("selected object bands exceed the 30-column canvas limit")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        grid[r][w - 1] = 5
    rng = _rng(seed, role, index)
    all_placed = []
    for band_index, (shared_row, count) in enumerate(bands):
        # Distinct starts reduce bbox ties across bands; the canonical row tie-break
        # remains mirrored for the few lawful ties that survive.
        all_placed.extend(
            _place_band(
                grid,
                shared_row=shared_row,
                count=count,
                start_left=1 + band_index,
                shape_offset=(seed + index * 2 + band_index * 3) % len(_SHAPES),
                color_offset=(seed + index * 2 + band_index) % 3,
                rng=rng,
            )
        )
    if len(all_placed) < 3:
        raise AssertionError("scene must contain an interacting chain")
    if solve_python(grid, packing_order="front_first") == solve_python(
        grid, packing_order="rear_first"
    ):
        raise AssertionError("scene does not expose the packing-order parameter")
    return grid


def generate_claims(
    seed: int,
    *,
    packing_order: str = DEFAULT_PACKING_ORDER,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict:
    _validate_seed(seed)
    _validate_packing_order(packing_order)
    _validate_counts(demos, queries)
    train_inputs = [build_input(seed, role="train", index=i) for i in range(demos)]
    test_inputs = [build_input(seed, role="test", index=i) for i in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({grid_key(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("episode inputs must be distinct")
    pair = lambda grid: {
        "input": grid,
        "output": solve_python(grid, packing_order=packing_order),
    }
    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program_for(packing_order),
    }
