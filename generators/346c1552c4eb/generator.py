"""Generator for ARC task 346c1552c4eb — rank object colors by area.

Each nonzero color forms one isolated 4-connected object.  The output is a
single row containing the object colors sorted by increasing object area; the
canonical Racket rule uses color as the deterministic tie-breaker, while the
lawful teaching distribution uses strictly distinct areas.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "346c1552c4eb"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "12b7a90d3fc1"

SUMMARY = (
    "Place two through six isolated, distinct-colored 4-connected objects with "
    "strictly distinct areas; output their colors in increasing-area order."
)
INVARIANTS = [
    "background is color 0",
    "each nonzero color forms exactly one 4-connected object",
    "different objects do not touch orthogonally",
    "all object colors and object areas are pairwise distinct",
    "the generated area ranking is not recoverable by numeric color sort or input scan order",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "rng 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "rng 7..14", "valid": "7..14"},
    "n_blobs": {"type": "int", "default": "rng 2..6", "valid": "2..6"},
}

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _coerce_grid(grid):
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        for row in grid
    ]


def _components(grid):
    """Return monochromatic 4-connected nonzero components in scan order."""
    h = len(grid)
    w = len(grid[0]) if grid else 0
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    components = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _CARDINALS:
                neighbor = (r + dr, c + dc)
                if (
                    0 <= neighbor[0] < h
                    and 0 <= neighbor[1] < w
                    and neighbor in unseen
                    and grid[neighbor[0]][neighbor[1]] == color
                ):
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "size": len(cells),
            }
        )
    return components


def _analysis(grid):
    errors = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "grid": None, "components": ()}
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return {"errors": ["grid rows must be non-empty lists or digit strings"], "grid": None, "components": ()}

    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return {"errors": ["grid must be rectangular"], "grid": coerced, "components": ()}
    if not 7 <= len(coerced) <= 14:
        errors.append("grid height must be in 7..14")
    if not 7 <= width <= 14:
        errors.append("grid width must be in 7..14")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("every cell must be an integer color in 0..9")
        return {"errors": errors, "grid": coerced, "components": ()}
    if not any(value == 0 for row in coerced for value in row):
        errors.append("background color 0 must be present")

    components = _components(coerced)
    if not 2 <= len(components) <= 6:
        errors.append(f"scene must contain 2..6 objects, got {len(components)}")

    colors = [component["color"] for component in components]
    duplicate_colors = sorted(color for color in set(colors) if colors.count(color) > 1)
    if duplicate_colors:
        errors.append(
            "each nonzero color must form exactly one object; repeated components for "
            + ", ".join(map(str, duplicate_colors))
        )

    sizes = [component["size"] for component in components]
    if len(set(sizes)) != len(sizes):
        errors.append("object areas must be pairwise distinct")

    for r, row in enumerate(coerced):
        for c, value in enumerate(row):
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(coerced) and 0 <= nc < width:
                    neighbor = coerced[nr][nc]
                    if neighbor not in (0, value):
                        errors.append("different-colored objects must not touch orthogonally")
                        return {"errors": errors, "grid": coerced, "components": tuple(components)}

    return {"errors": errors, "grid": coerced, "components": tuple(components)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": len(analysis["grid"]),
        "grid_w": len(analysis["grid"][0]),
        "n_blobs": len(analysis["components"]),
    }


def rule_mirror(grid):
    """Python test mirror; the canonical Racket program remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    ordered = sorted(
        analysis["components"],
        key=lambda component: (component["size"], component["color"]),
    )
    return [[component["color"] for component in ordered]]


def _validate_call(difficulty, overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _draw_sizes(rng, n, h, w, difficulty):
    minimum_total = n * (n + 1) // 2
    foreground_limit = max(minimum_total, int(h * w * 0.46))
    cap_by_band = {"easy": n + 1, "medium": n + 3, "hard": n + 5}[difficulty]
    maximum_size = min(10, max(n, cap_by_band), h * w - n)
    population = list(range(1, maximum_size + 1))
    for _ in range(300):
        sizes = sorted(rng.sample(population, n))
        if sum(sizes) <= foreground_limit:
            return sizes
    return list(range(1, n + 1))


def _nontrivial_output_order(colors, rng):
    numeric = sorted(colors)
    if len(colors) == 2:
        return list(reversed(numeric))
    for _ in range(100):
        order = list(colors)
        rng.shuffle(order)
        if order != numeric:
            return order
    return numeric[1:] + numeric[:1]


def _teaching_scene(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    output_order = rule_mirror(grid)[0]
    numeric_order = sorted(component["color"] for component in analysis["components"])
    scan_order = [component["color"] for component in analysis["components"]]
    return output_order != numeric_order and output_order != scan_order


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 7, 14)
    w = ctx.draw_int("grid_w", 7, 14)
    n = ctx.draw_int("n_blobs", 2, 6)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude=(0,)))
    rng = ctx.draw_rng("layout")

    for _ in range(500):
        sorted_sizes = _draw_sizes(rng, n, h, w, band)
        output_colors = _nontrivial_output_order(colors, rng)
        size_by_color = dict(zip(output_colors, sorted_sizes))
        specs = sorted(
            ((size_by_color[color], color) for color in colors),
            reverse=True,
        )
        grid = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        placed = []
        for size, color in specs:
            cells = grow_blob(rng, h, w, used, size, max_attempts=500)
            if cells is None:
                break
            placed.append((cells, color))
            used |= cells
        if len(placed) != n:
            continue
        for cells, color in placed:
            for r, c in cells:
                grid[r][c] = color
        if _teaching_scene(grid):
            return grid

    raise ValueError(
        f"could not place a lawful {n}-object scene in {h}x{w}; "
        "the requested override combination is incompatible"
    )
