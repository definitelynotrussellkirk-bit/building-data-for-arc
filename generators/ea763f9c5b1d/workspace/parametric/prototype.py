"""Native episode generator for area parity and an input-derived anchor threshold.

The default setting returns the canonical Racket source byte-for-byte.  The
alternative first finds the unique red component, binds its area as a threshold,
then classifies every component relative to that input-derived value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
from typing import Callable


RULE_MODES = ("area_parity", "anchor_threshold")
_HOME = Path(__file__).resolve().parent
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_OTHER_COLORS = (2, 5, 6, 7, 8, 9)

# Each profile deliberately contains a component below, equal to, and above the
# red anchor's area.  Repeating the equality case teaches the strict boundary.
_DEMO_PROFILES = (
    (10, 13, (4, 2, 3, 4, 5, 6), False),
    (11, 14, (5, 2, 4, 5, 6, 7), False),
    (12, 15, (3, 2, 3, 4, 5, 6), False),
    (14, 16, (6, 3, 5, 6, 7, 8), True),
    (15, 18, (7, 3, 5, 6, 7, 8, 9), True),
    (16, 20, (4, 2, 3, 4, 5, 7, 8), True),
)
_QUERY_PROFILES = (
    (13, 15, (5, 2, 3, 4, 5, 6, 7), False),
    (17, 19, (6, 3, 4, 5, 6, 7, 8), True),
    (20, 22, (4, 2, 3, 4, 5, 6, 7, 8), True),
    (30, 30, (7, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), True),
)

_ANCHOR_SHAPES = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    7: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (1, 1)),
}


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"rule_mode"}:
        raise ValueError("settings must contain exactly rule_mode")
    value = settings["rule_mode"]
    if value not in RULE_MODES:
        raise ValueError("rule_mode must be area_parity or anchor_threshold")
    return value


def program(settings) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "area_parity" else "anchor_threshold.rkt"
    return (_HOME / name).read_text(encoding="utf-8")


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return len(grid), width


def _components(grid) -> list[tuple[tuple[int, int], ...]]:
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while pending:
                current = pending.pop()
                cells.append(current)
                for dr, dc in _DIR4:
                    nxt = current[0] + dr, current[1] + dc
                    if (0 <= nxt[0] < h and 0 <= nxt[1] < w
                            and grid[nxt[0]][nxt[1]] != 0 and nxt not in seen):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(tuple(sorted(cells)))
    return result


def analyze_scene(grid) -> dict:
    components = _components(grid)
    if not components:
        raise ValueError("scene requires nonzero components")
    colors = []
    anchors = []
    for component in components:
        palette = {grid[row][col] for row, col in component}
        if len(palette) != 1:
            raise ValueError("each four-connected component must be one input color")
        color = next(iter(palette))
        colors.append(color)
        if color == 1:
            anchors.append(component)
    if len(anchors) != 1:
        raise ValueError("scene requires exactly one red anchor component")
    all_cells = tuple(cell for component in components for cell in component)
    return {
        "components": tuple(components),
        "component_colors": tuple(colors),
        "component_sizes": [len(component) for component in components],
        "anchor_count": len(anchors),
        "anchor": anchors[0],
        "anchor_size": len(anchors[0]),
        "all_cells": all_cells,
        "occupied_rows": len({row for row, _ in all_cells}),
        "occupied_cols": len({col for _, col in all_cells}),
    }


def _paint_by(grid, chooser: Callable[[tuple[tuple[int, int], ...]], int]) -> list[list[int]]:
    facts = analyze_scene(grid)
    output = [[0 for _ in row] for row in grid]
    for component in facts["components"]:
        color = chooser(component)
        for row, col in component:
            output[row][col] = color
    return output


def solve_python(grid, mode: str) -> list[list[int]]:
    if mode not in RULE_MODES:
        raise ValueError("invalid rule_mode")
    facts = analyze_scene(grid)
    if mode == "area_parity":
        return _paint_by(grid, lambda component: 3 if len(component) % 2 else 4)
    threshold = facts["anchor_size"]
    return _paint_by(grid, lambda component: 3 if len(component) < threshold else 4)


def _threshold_solver(threshold_of, *, equal_is_low: bool = False):
    def solve(grid):
        facts = analyze_scene(grid)
        threshold = threshold_of(grid, facts)
        return _paint_by(
            grid,
            lambda component: 3 if (
                len(component) <= threshold if equal_is_low else len(component) < threshold
            ) else 4,
        )
    return solve


def _anchor_bbox_area(_grid, facts):
    rows = [row for row, _ in facts["anchor"]]
    cols = [col for _, col in facts["anchor"]]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def declared_rivals(mode: str):
    """Finite plausible shortcuts used by the teaching audit, not a uniqueness proof."""
    if mode not in RULE_MODES:
        raise ValueError("invalid rule_mode")
    fixed = {
        f"fixed_threshold_{value}": _threshold_solver(lambda _g, _f, value=value: value)
        for value in range(3, 8)
    }
    common = {
        **fixed,
        "all_green": lambda grid: _paint_by(grid, lambda _component: 3),
        "all_yellow": lambda grid: _paint_by(grid, lambda _component: 4),
    }
    if mode == "area_parity":
        return {
            "anchor_threshold": lambda grid: solve_python(grid, "anchor_threshold"),
            "swapped_parity": lambda grid: _paint_by(
                grid, lambda component: 4 if len(component) % 2 else 3
            ),
            **common,
        }
    return {
        "area_parity": lambda grid: solve_python(grid, "area_parity"),
        "non_strict_threshold": _threshold_solver(
            lambda _grid, facts: facts["anchor_size"], equal_is_low=True
        ),
        "anchor_bbox_area": _threshold_solver(_anchor_bbox_area),
        "smallest_component_threshold": _threshold_solver(
            lambda _grid, facts: min(facts["component_sizes"])
        ),
        "largest_component_threshold": _threshold_solver(
            lambda _grid, facts: max(facts["component_sizes"])
        ),
        **common,
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"ea763f9c5b1d:parametric-anchor-threshold:v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _balanced_spans(length: int, parts: int, rng: random.Random):
    usable = length - (parts - 1)
    if usable < parts:
        raise ValueError("canvas too small for separated slots")
    base, remainder = divmod(usable, parts)
    sizes = [base] * parts
    order = list(range(parts))
    rng.shuffle(order)
    for index in order[:remainder]:
        sizes[index] += 1
    spans = []
    start = 0
    for size in sizes:
        spans.append((start, start + size))
        start += size + 1
    return spans


def _slot_grid(h: int, w: int, count: int, rng: random.Random):
    if count <= 4:
        rows, cols = 2, 2
    elif count <= 6:
        rows, cols = (2, 3) if w >= h else (3, 2)
    elif count <= 9:
        rows, cols = 3, 3
    elif count <= 12:
        rows, cols = (3, 4) if w >= h else (4, 3)
    else:
        raise ValueError("unsupported component count")
    row_spans = _balanced_spans(h, rows, rng)
    col_spans = _balanced_spans(w, cols, rng)
    slots = [
        (r0, r1, c0, c1)
        for r0, r1 in row_spans
        for c0, c1 in col_spans
    ]
    if count < len(slots):
        # Keep broad coverage: select the four corners first when available,
        # then a deterministic shuffled subset of the remaining slots.
        corner_indexes = [0, cols - 1, (rows - 1) * cols, rows * cols - 1]
        selected = []
        for index in corner_indexes:
            if index not in selected and len(selected) < count:
                selected.append(index)
        remaining = [index for index in range(len(slots)) if index not in selected]
        rng.shuffle(remaining)
        selected.extend(remaining[:count - len(selected)])
        slots = [slots[index] for index in selected]
    return slots


def _variants(shape):
    variants = set()
    for swap in (False, True):
        for sr in (-1, 1):
            for sc in (-1, 1):
                transformed = []
                for row, col in shape:
                    first, second = (col, row) if swap else (row, col)
                    transformed.append((sr * first, sc * second))
                top = min(row for row, _ in transformed)
                left = min(col for _, col in transformed)
                variants.add(tuple(sorted((row - top, col - left) for row, col in transformed)))
    return sorted(variants)


def _offset_shape(shape, slot, rng, *, spread_edges: bool):
    r0, r1, c0, c1 = slot
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    if height > r1 - r0 or width > c1 - c0:
        raise ValueError("shape does not fit slot")
    row_choices = list(range(r0, r1 - height + 1))
    col_choices = list(range(c0, c1 - width + 1))
    if spread_edges and r0 == 0:
        top = r0
    elif spread_edges and r1 == max(r1, 30) and r1 == 30:
        top = r1 - height
    else:
        top = rng.choice(row_choices)
    if spread_edges and c0 == 0:
        left = c0
    elif spread_edges and c1 == max(c1, 30) and c1 == 30:
        left = c1 - width
    else:
        left = rng.choice(col_choices)
    return tuple(sorted((row + top, col + left) for row, col in shape))


def _grow_component(slot, size: int, rng: random.Random, *, corner: str | None = None):
    r0, r1, c0, c1 = slot
    if size > (r1 - r0) * (c1 - c0):
        raise ValueError("component does not fit slot")
    if corner == "tl":
        start = (r0, c0)
    elif corner == "tr":
        start = (r0, c1 - 1)
    elif corner == "bl":
        start = (r1 - 1, c0)
    elif corner == "br":
        start = (r1 - 1, c1 - 1)
    else:
        start = (rng.randrange(r0, r1), rng.randrange(c0, c1))
    cells = {start}
    while len(cells) < size:
        frontier = sorted({
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in _DIR4
            if r0 <= row + dr < r1 and c0 <= col + dc < c1
            and (row + dr, col + dc) not in cells
        })
        if not frontier:
            raise RuntimeError("slot growth exhausted")
        cells.add(rng.choice(frontier))
    return tuple(sorted(cells))


def _anchor_component(slot, size: int, rng: random.Random, *, spread_edges: bool):
    candidates = []
    r0, r1, c0, c1 = slot
    for shape in _variants(_ANCHOR_SHAPES[size]):
        if max(row for row, _ in shape) < r1 - r0 and max(col for _, col in shape) < c1 - c0:
            candidates.append(shape)
    if not candidates:
        raise ValueError("anchor shape does not fit slot")
    shape = rng.choice(candidates)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    top = r0 if spread_edges and r0 == 0 else rng.randrange(r0, r1 - height + 1)
    left = c0 if spread_edges and c0 == 0 else rng.randrange(c0, c1 - width + 1)
    return tuple(sorted((row + top, col + left) for row, col in shape))


def _scene(profile, rng: random.Random):
    h, w, sizes, spread_edges = profile
    slots = _slot_grid(h, w, len(sizes), rng)
    # Keep the anchor's slot seed-dependent while preserving broad placement.
    anchor_index = rng.randrange(len(slots))
    slots[0], slots[anchor_index] = slots[anchor_index], slots[0]
    components = []
    components.append(_anchor_component(slots[0], sizes[0], rng, spread_edges=spread_edges))
    corner_by_slot = {}
    if spread_edges:
        for index, (r0, r1, c0, c1) in enumerate(slots[1:], start=1):
            corner = None
            if r0 == 0 and c0 == 0: corner = "tl"
            elif r0 == 0 and c1 == w: corner = "tr"
            elif r1 == h and c0 == 0: corner = "bl"
            elif r1 == h and c1 == w: corner = "br"
            corner_by_slot[index] = corner
    for index, (slot, size) in enumerate(zip(slots[1:], sizes[1:]), start=1):
        components.append(_grow_component(slot, size, rng, corner=corner_by_slot.get(index)))
    grid = [[0] * w for _ in range(h)]
    for row, col in components[0]:
        grid[row][col] = 1
    palette = list(_OTHER_COLORS)
    rng.shuffle(palette)
    for index, component in enumerate(components[1:]):
        color = palette[index % len(palette)]
        for row, col in component:
            grid[row][col] = color
    facts = analyze_scene(grid)
    if facts["component_sizes"].count(facts["anchor_size"]) < 2:
        raise AssertionError("profile lost its equality witness")
    return grid


def _input(seed: int, split: str, index: int):
    profiles = _DEMO_PROFILES if split == "demonstrations" else _QUERY_PROFILES
    return _scene(profiles[index], _rng(seed, split, index))


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    if type(seed) is not int or isinstance(seed, bool) or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2**63-1]")
    if type(demos) is not int or isinstance(demos, bool) or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in [2, 6]")
    if type(queries) is not int or isinstance(queries, bool) or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in [1, 4]")

    def pair(grid):
        return {"input": grid, "output": solve_python(grid, mode)}

    train = [pair(_input(seed, "demonstrations", index)) for index in range(demos)]
    test = [pair(_input(seed, "queries", index)) for index in range(queries)]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(keys) != len(set(keys)):
        raise AssertionError("episode inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--rule-mode", choices=RULE_MODES, default="anchor_threshold")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {"rule_mode": args.rule_mode}, args.demos, args.queries), separators=(",", ":")))
