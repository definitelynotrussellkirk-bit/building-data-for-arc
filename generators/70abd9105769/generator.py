"""Generator for 70abd9105769: keep the centers of filled odd squares.

The selected rule removes every filled odd-sized square except its center cell,
which keeps the square's color.  Ordinary draws intentionally include repeated
colors so the lesson is about connected square objects, not one center per color.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70abd9105769"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "82b6dc62b353"

SUMMARY = "Separated filled odd-size squares reduce to their center cells."

INVARIANTS = [
    "background is 0",
    "every nonzero 4-component is a filled odd-sized square",
    "same-color cells form filled odd squares of side at least 3",
    "colors may repeat across separated squares",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "5..30"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "5..30"},
    "squares": {"type": "int", "default": "difficulty band", "valid": "1..12"},
    "n_distinct_colors": {
        "type": "int",
        "default": "rng 1..min(squares, 4)",
        "valid": "1..min(squares, 9)",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_DIFFICULTY_BANDS = {
    None: ((9, 18), (10, 19), (2, 5)),
    "easy": ((7, 12), (7, 13), (1, 3)),
    "medium": ((12, 21), (13, 22), (3, 7)),
    "hard": ((18, 30), (18, 30), (6, 12)),
}


def _strict_int(value: Any, name: str, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")
    return value


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTY_BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    bounds = {
        "grid_h": (5, 30),
        "grid_w": (5, 30),
        "squares": (1, 12),
        "n_distinct_colors": (1, 9),
    }
    for name, value in overrides.items():
        _strict_int(value, name, *bounds[name])
    if (
        "squares" in overrides
        and "n_distinct_colors" in overrides
        and overrides["n_distinct_colors"] > overrides["squares"]
    ):
        raise ValueError("n_distinct_colors cannot exceed squares")


def _lattice_candidates(height: int, width: int) -> list[list[tuple[int, int]]]:
    """All stride-four 3x3 top-left lattices, best capacity first."""
    lattices = []
    for ro in range(4):
        rows = list(range(ro, height - 2, 4))
        for co in range(4):
            cols = list(range(co, width - 2, 4))
            cells = [(r, c) for r in rows for c in cols]
            if cells:
                lattices.append(cells)
    return sorted(lattices, key=lambda cells: (-len(cells), cells))


def _capacity(height: int, width: int) -> int:
    lattices = _lattice_candidates(height, width)
    return len(lattices[0]) if lattices else 0


def _rect(center: tuple[int, int], size: int) -> tuple[int, int, int, int]:
    radius = size // 2
    r, c = center
    return r - radius, c - radius, r + radius, c + radius


def _separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return ar2 + 1 < br1 or br2 + 1 < ar1 or ac2 + 1 < bc1 or bc2 + 1 < ac1


def _choose_layout(height: int, width: int, count: int, rng) -> list[tuple[int, int, int]]:
    feasible = [cells for cells in _lattice_candidates(height, width) if len(cells) >= count]
    if not feasible:
        raise ValueError(
            f"{count} separated 3x3 squares do not fit in {height}x{width}; "
            f"maximum supported by the constructive layout is {_capacity(height, width)}"
        )
    best = max(map(len, feasible))
    broad = [cells for cells in feasible if len(cells) >= max(count, best - 2)]
    lattice = rng.choice(broad)
    tops = rng.sample(lattice, count)
    centers = [(r + 1, c + 1) for r, c in tops]
    sizes = [3] * count

    order = list(range(count))
    rng.shuffle(order)
    enlarged = 0
    for index in order:
        candidate = _rect(centers[index], 5)
        r1, c1, r2, c2 = candidate
        if r1 < 0 or c1 < 0 or r2 >= height or c2 >= width:
            continue
        if all(
            j == index or _separated(candidate, _rect(centers[j], sizes[j]))
            for j in range(count)
        ):
            # Always take the first lawful enlargement; vary later ones.
            if enlarged == 0 or rng.randrange(3) == 0:
                sizes[index] = 5
                enlarged += 1
    return sorted(
        [(centers[i][0], centers[i][1], sizes[i]) for i in range(count)],
        key=lambda item: (item[0], item[1]),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _DIFFICULTY_BANDS[difficulty]
    if "grid_h" in overrides:
        h_lo = h_hi = overrides["grid_h"]
    if "grid_w" in overrides:
        w_lo = w_hi = overrides["grid_w"]
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)

    cap = min(12, _capacity(height, width))
    if cap < 1:
        raise ValueError(f"no filled 3x3 square fits in {height}x{width}")
    if "squares" in overrides:
        count = ctx.draw_int_strict("squares", 1, 12)
        if count > cap:
            raise ValueError(
                f"squares={count} exceeds constructive capacity {cap} for {height}x{width}"
            )
    else:
        lo = min(n_lo, cap)
        hi = min(n_hi, cap)
        count = ctx.draw_int_strict("squares", lo, hi)

    if "n_distinct_colors" in overrides:
        colors_n = ctx.draw_int_strict("n_distinct_colors", 1, 9)
        if colors_n > count:
            raise ValueError("n_distinct_colors cannot exceed squares")
    else:
        colors_n = ctx.draw_int_strict("n_distinct_colors", 1, min(count, 4))

    rng = ctx.draw_rng("layout")
    layout = _choose_layout(height, width, count, rng)
    palette = rng.sample(range(1, 10), colors_n)
    assignments = palette + [rng.choice(palette) for _ in range(count - colors_n)]
    rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    for (center_r, center_c, size), color in zip(layout, assignments):
        radius = size // 2
        for r in range(center_r - radius, center_r + radius + 1):
            for c in range(center_c - radius, center_c + radius + 1):
                grid[r][c] = color
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30x30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("grid cells must be exact integer colors 0..9")
    return len(grid), width


def _components_nonzero(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            result.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "r1": min(rows),
                    "c1": min(cols),
                    "r2": max(rows),
                    "c2": max(cols),
                    "size": len(cells),
                }
            )
    return sorted(result, key=lambda comp: (comp["r1"], comp["c1"], comp["color"]))


def semantic_observables(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    comps = _components_nonzero(grid)
    counts = Counter(comp["color"] for comp in comps)
    return {
        "grid_h": height,
        "grid_w": width,
        "square_count": len(comps),
        "n_distinct_colors": len(counts),
        "objects_per_color": dict(sorted(counts.items())),
        "square_sizes": sorted({comp["r2"] - comp["r1"] + 1 for comp in comps}),
        "components": [
            {k: comp[k] for k in ("color", "r1", "c1", "r2", "c2", "size")}
            for comp in comps
        ],
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    facts = semantic_observables(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "squares": facts["square_count"],
        "n_distinct_colors": facts["n_distinct_colors"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        height, width = _validate_grid(grid)
        comps = _components_nonzero(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if not comps:
        return ["expected at least one filled odd square"]
    for comp in comps:
        side_h = comp["r2"] - comp["r1"] + 1
        side_w = comp["c2"] - comp["c1"] + 1
        expected = {
            (r, c)
            for r in range(comp["r1"], comp["r2"] + 1)
            for c in range(comp["c1"], comp["c2"] + 1)
        }
        if side_h != side_w or side_h < 3 or side_h % 2 == 0 or set(comp["cells"]) != expected:
            return ["every nonzero component must be a filled odd-sized square"]
    return []
