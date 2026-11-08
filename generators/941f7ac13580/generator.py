"""Generator for ARC task 941f7ac13580: read component sizes in top-left order.

The input is a zero-background grid containing two to five one-cell-separated,
monochromatic 4-connected objects.  Every object has 1..9 cells.  The output is
a single row containing the component sizes after sorting components by their
(top, left) coordinates.

All declared controls are strict and observable.  In particular ``size_range``
is the realized maximum object size, not merely a sampling upper bound.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "941f7ac13580"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f9bdf0e04d21"

SUMMARY = (
    "Zero-background grids with 2..5 separated monochromatic objects of size "
    "1..9. Output their cell counts in top-left reading order. Exact dimension, "
    "count, maximum-size, palette-size, position, and texture controls are "
    "validated and realized."
)

INVARIANTS = [
    "each nonzero object is monochromatic and 4-connected",
    "different objects have at least one background cell between them, including diagonally",
    "each object has 1..9 cells",
    "the output is one row of object sizes sorted by top-left coordinate",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("two_objects", "single_cells")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = PALETTE_KINDS
TEXTURES = PALETTE_KINDS + DEGENERATE_TEXTURES
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"texture": "two_objects", "n_objects": "must equal 2"},
    {"texture": "single_cells", "size_range": "must equal 1"},
)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed", "valid": "10..22"},
    "grid_w": {"type": "int", "default": "difficulty-skewed", "valid": "10..22"},
    "n_objects": {"type": "int", "default": "difficulty-skewed", "valid": "2..5"},
    "size_range": {
        "type": "int",
        "default": "difficulty-skewed realized maximum",
        "valid": "1..9",
    },
    "palette_size": {"type": "int", "default": "2..min(5,n_objects)", "valid": "2..5"},
    "position_bias": {
        "type": "str",
        "default": "scattered",
        "valid": "scattered",
        "probe": "diagnostic",
    },
    "texture": {
        "type": "str",
        "default": "default",
        "valid": "|".join(TEXTURES),
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALL_COLORS = tuple(range(1, 10))
_PALETTE_POOLS = {
    "default": _ALL_COLORS,
    "varied": (9, 1, 8, 2, 7, 3, 6, 4, 5),
    "warm": (2, 4, 7, 9, 1),
    "cool": (1, 3, 5, 8, 6),
    "two_objects": _ALL_COLORS,
    "single_cells": _ALL_COLORS,
}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _strict_int(name: str, value: Any, lo: int, hi: int) -> None:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (
        ("grid_h", 10, 22),
        ("grid_w", 10, 22),
        ("n_objects", 2, 5),
        ("size_range", 1, 9),
        ("palette_size", 2, 5),
    ):
        if name in overrides and overrides[name] is not None:
            _strict_int(name, overrides[name], lo, hi)
    if overrides.get("position_bias") not in (None, "scattered"):
        raise ValueError("position_bias must be 'scattered'")
    if "texture" in overrides and overrides["texture"] is not None:
        texture = overrides["texture"]
        if type(texture) is not str or texture not in TEXTURES:
            raise ValueError(f"texture must be one of {TEXTURES}")
        if texture == "two_objects" and overrides.get("n_objects") not in (None, 2):
            raise ValueError("texture='two_objects' requires n_objects=2")
        if texture == "single_cells" and overrides.get("size_range") not in (None, 1):
            raise ValueError("texture='single_cells' requires size_range=1")
    n = overrides.get("n_objects")
    palette = overrides.get("palette_size")
    effective_n = 2 if overrides.get("texture") == "two_objects" else n
    if effective_n is not None and palette is not None and palette > effective_n:
        raise ValueError("palette_size cannot exceed n_objects")


def _effective_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    result = dict(overrides)
    texture = result.get("texture", "default")
    if texture == "two_objects":
        result["n_objects"] = 2
    if texture == "single_cells":
        result["size_range"] = 1
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _random_polyomino(rng, size: int) -> tuple[tuple[int, int], ...]:
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(tuple(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((row + dr, col + dc))
    return _normalize(cells)


def _shape_candidates(rng, size: int) -> list[tuple[tuple[int, int], ...]]:
    horizontal = tuple((0, col) for col in range(size))
    vertical = tuple((row, 0) for row in range(size))
    width = min(3, size)
    snake = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        snake.append((row, col))
    values = [horizontal, vertical, _normalize(snake)]
    for _ in range(8):
        values.append(_random_polyomino(rng, size))
    unique: list[tuple[tuple[int, int], ...]] = []
    seen = set()
    for shape in values:
        shape = _normalize(shape)
        if shape not in seen:
            seen.add(shape)
            unique.append(shape)
    rng.shuffle(unique)
    return unique


def _blocked(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < h and 0 <= cc < w:
                    result.add((rr, cc))
    return result


def _place_rich(
    rng, h: int, w: int, sizes: list[int]
) -> list[tuple[tuple[int, int], ...]] | None:
    order = sorted(range(len(sizes)), key=lambda index: (-sizes[index], index))
    placed: dict[int, tuple[tuple[int, int], ...]] = {}
    occupied: set[tuple[int, int]] = set()

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        object_index = order[depth]
        size = sizes[object_index]
        candidates: list[tuple[tuple[int, int], ...]] = []
        for shape in _shape_candidates(rng, size):
            shape_h = max(row for row, _ in shape) + 1
            shape_w = max(col for _, col in shape) + 1
            if shape_h > h or shape_w > w:
                continue
            offsets = [
                (top, left)
                for top in range(h - shape_h + 1)
                for left in range(w - shape_w + 1)
            ]
            rng.shuffle(offsets)
            for top, left in offsets[: min(len(offsets), 160)]:
                cells = tuple((top + row, left + col) for row, col in shape)
                if occupied.isdisjoint(_blocked(cells, h, w)):
                    candidates.append(cells)
        rng.shuffle(candidates)
        for cells in candidates[:240]:
            occupied.update(cells)
            placed[object_index] = cells
            if search(depth + 1):
                return True
            del placed[object_index]
            occupied.difference_update(cells)
        return False

    if not search(0):
        return None
    return [placed[index] for index in range(len(sizes))]


def _place_guaranteed(rng, h: int, w: int, sizes: list[int]):
    """Complete strip construction for every declared dimension/count/size."""
    horizontal = rng.randrange(2) == 0
    if horizontal:
        slots = list(range(0, 2 * len(sizes), 2))
        rng.shuffle(slots)
        return [
            tuple((slots[index], left + offset) for offset in range(size))
            for index, size in enumerate(sizes)
            for left in [rng.randrange(w - size + 1)]
        ]
    slots = list(range(0, 2 * len(sizes), 2))
    rng.shuffle(slots)
    return [
        tuple((top + offset, slots[index]) for offset in range(size))
        for index, size in enumerate(sizes)
        for top in [rng.randrange(h - size + 1)]
    ]


def _components(grid: Any) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if type(grid) not in (list, tuple) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if type(grid[0]) not in (list, tuple) or not grid[0]:
        return [], ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(type(row) not in (list, tuple) or len(row) != width for row in grid):
        return [], ["grid must be rectangular"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return [], ["cells must be exact ARC integers 0..9"]

    h, w = len(grid), width
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "top": top,
                    "left": left,
                    "bottom": max(r for r, _ in cells),
                    "right": max(c for _, c in cells),
                }
            )
    components.sort(key=lambda comp: (comp["top"], comp["left"]))
    return components, errors


def semantic_observables(grid: Any) -> dict[str, Any]:
    components, errors = _components(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    owner: dict[tuple[int, int], int] = {}
    for index, comp in enumerate(components):
        owner.update({cell: index for cell in comp["cells"]})
    separated = True
    for (row, col), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = owner.get((row + dr, col + dc))
                if other is not None and other != index:
                    separated = False
    sizes = tuple(comp["size"] for comp in components)
    colors = tuple(sorted({comp["color"] for comp in components}))
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "n_objects": len(components),
        "object_sizes": sizes,
        "max_object_size": max(sizes, default=0),
        "palette_size": len(colors),
        "colors": colors,
        "top_lefts": tuple((comp["top"], comp["left"]) for comp in components),
        "one_cell_separated": separated,
        "position_bias": "scattered",
        "components": components,
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_objects": facts["n_objects"],
        "size_range": facts["max_object_size"],
        "palette_size": facts["palette_size"],
        "position_bias": "scattered",
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    effective = _effective_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", 10, 22)
    w = ctx.draw_int_diff("grid_w", 10, 22)
    requested_palette = effective.get("palette_size")
    object_floor = (
        requested_palette
        if requested_palette is not None and effective.get("n_objects") is None
        else 2
    )
    n_objects = ctx.draw_int_diff("n_objects", object_floor, 5)
    size_limit = ctx.draw_int_diff("size_range", 1, 9)
    texture = ctx.draw_choice("texture", TEXTURES)
    ctx.draw_choice("position_bias", ("scattered",))
    palette_hi = min(5, n_objects, len(_PALETTE_POOLS[texture]))
    palette_size = ctx.draw_int_strict("palette_size", 2, palette_hi)

    sizes_rng = ctx.draw_rng("object_sizes")
    sizes = [size_limit]
    sizes.extend(sizes_rng.randint(1, size_limit) for _ in range(n_objects - 1))
    sizes_rng.shuffle(sizes)

    layout_rng = ctx.draw_rng("layout")
    placements = _place_rich(layout_rng, h, w, sizes)
    if placements is None:
        placements = _place_guaranteed(layout_rng, h, w, sizes)

    palette_rng = ctx.draw_rng("palette")
    pool = list(_PALETTE_POOLS[texture])
    palette = palette_rng.sample(pool, palette_size)
    object_colors = list(palette)
    object_colors.extend(palette_rng.choice(palette) for _ in range(n_objects - palette_size))
    palette_rng.shuffle(object_colors)

    grid = full_grid(h, w, 0)
    for cells, color in zip(placements, object_colors):
        for row, col in cells:
            grid[row][col] = color

    requested = {key: value for key, value in effective.items() if value is not None}
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": requested})
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None):
    messages: list[str] = []
    try:
        _validate_difficulty(difficulty)
    except ValueError as exc:
        messages.append(str(exc))
    facts = semantic_observables(grid)
    messages.extend(facts.get("errors", []))
    if facts.get("errors"):
        return messages
    if not 10 <= facts["grid_h"] <= 22 or not 10 <= facts["grid_w"] <= 22:
        messages.append("grid dimensions must be in 10..22")
    if not 2 <= facts["n_objects"] <= 5:
        messages.append(f"expected 2..5 separated objects, got {facts['n_objects']}")
    if any(not 1 <= size <= 9 for size in facts["object_sizes"]):
        messages.append("object size must be 1..9 so it is a valid output color")
    if not facts["one_cell_separated"]:
        messages.append("objects must be separated by at least one background cell")
    if not 2 <= facts["palette_size"] <= min(5, facts["n_objects"]):
        messages.append("palette size must be 2..min(5,n_objects)")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if requested is None or name in ("texture",):
            continue
        actual = observed.get(name)
        if actual != requested:
            messages.append(f"override {name}={requested!r} realized as {actual!r}")
    return messages


def rule_mirror(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid component-size grid: " + "; ".join(errors))
    return [list(facts["object_sizes"])]
