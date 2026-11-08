"""Deterministic two-object ordering family for task 8265382d9c72.

The exact canonical setting counts the left object first.  The alternative
first locates the unique object with a connected one-cell top tab, then uses
that input-derived object identity to decide which count/color is packed first.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "left_first": HOME / "canonical.rkt",
    "tab_first": HOME / "tab_first.rkt",
}
SETTINGS = tuple(PROGRAM_FILES)

# (grid_h, grid_w, left_spec, right_spec); each spec is
# (base_h, width, interior_zero_count, tabbed).
DEMO_PROFILES = (
    (9, 16, (3, 6, 2, False), (5, 4, 3, True)),
    (14, 18, (8, 4, 2, True), (13, 3, 6, False)),
    (12, 20, (8, 4, 3, True), (4, 7, 2, False)),
    (14, 22, (8, 7, 3, False), (4, 6, 2, True)),
    (16, 24, (8, 8, 4, True), (10, 7, 2, False)),
    (18, 26, (10, 9, 2, False), (8, 8, 3, True)),
)
QUERY_PROFILES = (
    (10, 18, (7, 7, 4, False), (5, 5, 2, True)),
    (16, 22, (10, 8, 2, True), (12, 7, 3, False)),
    (24, 28, (20, 12, 3, False), (18, 13, 2, True)),
    (30, 30, (30, 14, 3, False), (28, 15, 2, True)),
)


def _exact_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _ordering(settings: object) -> str:
    if not isinstance(settings, dict) or set(settings) != {"ordering"}:
        raise ValueError("settings must contain exactly ordering")
    value = settings["ordering"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"ordering must be one of {SETTINGS}")
    return value


def program(settings: object) -> str:
    return PROGRAM_FILES[_ordering(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"8265382d9c72|{seed}|{split}|{index}".encode("ascii")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _profile(split: str, index: int):
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    return profiles[index]


def _hole_positions(base_h: int, width: int, count: int, rng: random.Random) -> list[tuple[int, int]]:
    interior = [(r, c) for r in range(1, base_h - 1) for c in range(1, width - 1)]
    if not 1 <= count <= len(interior):
        raise ValueError("interior hole count does not fit object")
    # Prefer a spatially spread deterministic subset, then use the local RNG to
    # rotate it so repeated dimensions do not leak fixed hole locations.
    interior.sort(key=lambda p: ((p[0] * 17 + p[1] * 31) % 97, p[0], p[1]))
    offset = rng.randrange(len(interior))
    rotated = interior[offset:] + interior[:offset]
    selected = []
    for cell in rotated:
        if all(abs(cell[0] - r) + abs(cell[1] - c) > 1 for r, c in selected):
            selected.append(cell)
            if len(selected) == count:
                return selected
    return rotated[:count]


def _draw_object(
    grid: list[list[int]],
    *,
    base_top: int,
    left: int,
    base_h: int,
    width: int,
    holes: int,
    tabbed: bool,
    color: int,
    rng: random.Random,
) -> None:
    if tabbed and base_top < 1:
        raise ValueError("tabbed object needs one row above its base")
    for r in range(base_top, base_top + base_h):
        for c in range(left, left + width):
            grid[r][c] = color
    for dr, dc in _hole_positions(base_h, width, holes, rng):
        grid[base_top + dr][left + dc] = 0
    if tabbed:
        grid[base_top - 1][left + width // 2] = color


def _top_for(grid_h: int, base_h: int, tabbed: bool, rng: random.Random, *, fixed: int | None = None) -> int:
    low = 1 if tabbed else 0
    high = grid_h - base_h
    if fixed is not None:
        if not low <= fixed <= high:
            raise ValueError("fixed placement is outside profile")
        return fixed
    return rng.randint(low, high)


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    grid_h, grid_w, left_spec, right_spec = _profile(split, index)
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(grid_w)] for _ in range(grid_h)]
    lh, lw, ln, ltab = left_spec
    rh, rw, rn, rtab = right_spec
    low_color, high_color = sorted(rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2))
    tab_should_be_low = index % 2 == 0
    tab_color = low_color if tab_should_be_low else high_color
    other_color = high_color if tab_should_be_low else low_color
    colors = [tab_color, other_color] if ltab else [other_color, tab_color]
    left_col, right_col = 0, grid_w - rw
    if left_col + lw >= right_col:
        raise ValueError("profile objects need a blank separating column")

    if split == "test" and index == 3:
        left_top = 0
        right_top = 2
    elif split == "train" and index == 0:
        # The tabbed right object is unambiguously topmost, while the left
        # object is unambiguously bottommost.
        left_top = grid_h - lh
        right_top = 1
    elif split == "train" and index == 1:
        # Reverse the vertical relation in the second demonstration.
        left_top = grid_h - lh
        right_top = 0
    elif split == "train" and index == 2:
        # Put the tabbed left object at the top and the other object at the
        # bottom; this also breaks left=fewer-cells correlations.
        left_top = 1
        right_top = grid_h - rh
    else:
        left_top = _top_for(grid_h, lh, ltab, rng)
        right_top = _top_for(grid_h, rh, rtab, rng)

    _draw_object(
        grid,
        base_top=left_top,
        left=left_col,
        base_h=lh,
        width=lw,
        holes=ln,
        tabbed=ltab,
        color=colors[0],
        rng=rng,
    )
    _draw_object(
        grid,
        base_top=right_top,
        left=right_col,
        base_h=rh,
        width=rw,
        holes=rn,
        tabbed=rtab,
        color=colors[1],
        rng=rng,
    )
    return grid


def _components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            objects.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return objects


def _tabbed(obj: dict) -> bool:
    r0, c0, _r1, c1 = obj["bbox"]
    top_count = sum(r == r0 for r, _ in obj["cells"])
    next_count = sum(r == r0 + 1 for r, _ in obj["cells"])
    return top_count == 1 and next_count == c1 - c0 + 1


def _holes(grid: list[list[int]], obj: dict) -> int:
    r0, c0, r1, c1 = obj["bbox"]
    return sum(
        grid[r][c] == 0
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    )


def _ordered(grid: list[list[int]], ordering: str) -> tuple[dict, dict]:
    objects = _components(grid)
    if len(objects) != 2:
        raise ValueError(f"expected two objects, found {len(objects)}")
    left, right = sorted(objects, key=lambda obj: obj["bbox"][1])
    if ordering == "left_first":
        first = left
    else:
        marked = [obj for obj in objects if _tabbed(obj)]
        if len(marked) != 1:
            raise ValueError(f"expected one tabbed object, found {len(marked)}")
        first = marked[0]
    return first, right if first is left else left


def _apply(grid: list[list[int]], ordering: str) -> list[list[int]]:
    first, second = _ordered(grid, ordering)
    n1, n2 = _holes(grid, first), _holes(grid, second)
    start = (n1 + 2) // 3
    if n1 > 9 or n2 > max(0, 3 - start) * 3:
        raise ValueError(f"counts do not fit output: {n1}, {n2}")
    output = [[0, 0, 0] for _ in range(3)]
    for index in range(n1):
        output[index // 3][index % 3] = first["color"]
    for index in range(n2):
        output[start + index // 3][index % 3] = second["color"]
    return output


def _pair(seed: int, split: str, index: int, ordering: str) -> dict:
    grid = _sample_input(seed, split, index)
    return {"input": grid, "output": _apply(grid, ordering)}


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    seed = _exact_int("seed", seed, 0, 2**63 - 1)
    demos = _exact_int("demos", demos, 2, 6)
    queries = _exact_int("queries", queries, 1, 4)
    ordering = _ordering(settings)
    train = [_pair(seed, "train", index, ordering) for index in range(demos)]
    test = [_pair(seed, "test", index, ordering) for index in range(queries)]
    return {"train": train, "test": test, "program_solution": program(settings)}


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    """Authoring-only rival catalog used by bounded identifiability audits."""
    objects = _components(grid)
    if len(objects) != 2:
        raise ValueError(f"rival audit expected two objects, found {len(objects)}")
    left, right = sorted(objects, key=lambda obj: obj["bbox"][1])

    def pack(first: dict) -> list[list[int]]:
        second = right if first is left else left
        n1, n2 = _holes(grid, first), _holes(grid, second)
        output = [[0, 0, 0] for _ in range(3)]
        for index in range(n1):
            output[index // 3][index % 3] = first["color"]
        start = (n1 + 2) // 3
        for index in range(n2):
            output[start + index // 3][index % 3] = second["color"]
        return output

    def height(obj: dict) -> int:
        return obj["bbox"][2] - obj["bbox"][0] + 1

    def width(obj: dict) -> int:
        return obj["bbox"][3] - obj["bbox"][1] + 1

    def area(obj: dict) -> int:
        return height(obj) * width(obj)

    def density(obj: dict) -> float:
        return len(obj["cells"]) / area(obj)

    tabbed = next(obj for obj in objects if _tabbed(obj))
    selectors = {
        "left_first": left,
        "tab_first": tabbed,
        "right_first": right,
        "taller_first": max(objects, key=lambda obj: (height(obj), -obj["bbox"][1])),
        "shorter_first": min(objects, key=lambda obj: (height(obj), obj["bbox"][1])),
        "wider_first": max(objects, key=lambda obj: (width(obj), -obj["bbox"][1])),
        "narrower_first": min(objects, key=lambda obj: (width(obj), obj["bbox"][1])),
        "smaller_count_first": min(objects, key=lambda obj: (_holes(grid, obj), obj["bbox"][1])),
        "larger_count_first": max(objects, key=lambda obj: (_holes(grid, obj), -obj["bbox"][1])),
        "larger_bbox_first": max(objects, key=lambda obj: (area(obj), -obj["bbox"][1])),
        "smaller_bbox_first": min(objects, key=lambda obj: (area(obj), obj["bbox"][1])),
        "topmost_first": min(objects, key=lambda obj: (obj["bbox"][0], obj["bbox"][1])),
        "bottommost_first": max(objects, key=lambda obj: (obj["bbox"][2], -obj["bbox"][1])),
        "lower_color_first": min(objects, key=lambda obj: (obj["color"], obj["bbox"][1])),
        "higher_color_first": max(objects, key=lambda obj: (obj["color"], -obj["bbox"][1])),
        "denser_first": max(objects, key=lambda obj: (density(obj), -obj["bbox"][1])),
        "sparser_first": min(objects, key=lambda obj: (density(obj), obj["bbox"][1])),
        "more_cells_first": max(objects, key=lambda obj: (len(obj["cells"]), -obj["bbox"][1])),
        "fewer_cells_first": min(objects, key=lambda obj: (len(obj["cells"]), obj["bbox"][1])),
    }
    return {name: pack(first) for name, first in selectors.items()}

