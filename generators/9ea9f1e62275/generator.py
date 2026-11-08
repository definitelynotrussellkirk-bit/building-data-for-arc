"""Generator for H42 — Voronoi-fill the interior of a color-1 frame.

The input contains one rectangular color-1 outline and two to eight distinct
colored seed cells strictly inside it.  The canonical rule keeps the frame and
assigns every interior cell the color of its uniquely nearest seed under
Manhattan distance; cells tied between different seed colors remain 0.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "9ea9f1e62275"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "caf596654388"

SUMMARY = (
    "One color-1 rectangular frame contains distinct colored seeds; fill each "
    "interior cell from its uniquely nearest seed by Manhattan distance and "
    "leave cross-color ties black."
)

EXAMPLES_NEEDED = 3
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

INVARIANTS = [
    "the returned grid is 8..30 rows by 10..30 columns",
    "exactly one complete color-1 rectangular outline lies inside zero padding",
    "the frame is at least 6 rows by 8 columns",
    "2..8 strictly interior seed cells use distinct colors from 2..9",
    "all non-frame, non-seed input cells are 0",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "8..30",
        "doc": "Full returned input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "10..30",
        "doc": "Full returned input-grid width.",
    },
    "n_seeds": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "2..8",
        "doc": "Number of distinct-colored seed cells inside the frame.",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
Grid = list[list[int]]
Seed = tuple[int, int, int]


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def _grid_errors(grid) -> list[str]:
    if type(grid) is not list or not grid:
        return ["grid must be a non-empty list"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be in 1..30"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _one_components(grid: Sequence[Sequence[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def analyze_grid(grid) -> dict[str, object]:
    """Return structural facts; errors are descriptive and never mutate ``grid``."""
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "frame_bbox": None, "seeds": [], "outside_nonzero": []}

    h, w = len(grid), len(grid[0])
    components = _one_components(grid)
    if len(components) != 1:
        errors.append(f"expected exactly one connected color-1 frame, found {len(components)} components")
        return {"errors": errors, "frame_bbox": None, "seeds": [], "outside_nonzero": []}

    ones = components[0]
    rows = [r for r, _ in ones]
    cols = [c for _, c in ones]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    perimeter = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if ones != perimeter:
        missing = len(perimeter - ones)
        extra = len(ones - perimeter)
        errors.append(f"color-1 cells do not form one complete rectangular outline (missing={missing}, extra={extra})")

    seeds: list[Seed] = []
    outside_nonzero: list[Seed] = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if r1 < r < r2 and c1 < c < c2:
                if value not in (0, 1):
                    seeds.append((r, c, value))
                elif value == 1:
                    errors.append("color 1 appears inside the frame")
            elif (r, c) not in perimeter and value != 0:
                outside_nonzero.append((r, c, value))
    if outside_nonzero:
        errors.append(f"found {len(outside_nonzero)} nonzero cell(s) outside the frame")

    return {
        "errors": errors,
        "frame_bbox": (r1, c1, r2, c2),
        "frame_cells": tuple(sorted(perimeter)),
        "seeds": tuple(seeds),
        "outside_nonzero": tuple(outside_nonzero),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    facts = analyze_grid(grid)
    errors = list(facts["errors"])
    bbox = facts["frame_bbox"]
    if bbox is None:
        return errors
    r1, c1, r2, c2 = bbox
    if r2 - r1 + 1 < 6 or c2 - c1 + 1 < 8:
        errors.append("frame must be at least 6 rows by 8 columns")
    seeds = list(facts["seeds"])
    if not 2 <= len(seeds) <= 8:
        errors.append(f"expected 2..8 interior seeds, found {len(seeds)}")
    colors = [value for _, _, value in seeds]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    facts = analyze_grid(grid)
    if facts["errors"]:
        raise ValueError(f"cannot observe malformed grid: {facts['errors']}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_seeds": len(facts["seeds"])}


def _distance(seed: Seed, r: int, c: int, metric: str) -> int:
    dr = abs(seed[0] - r)
    dc = abs(seed[1] - c)
    if metric == "manhattan":
        return dr + dc
    if metric == "chebyshev":
        return max(dr, dc)
    if metric == "euclidean_sq":
        return dr * dr + dc * dc
    raise ValueError(f"unknown metric: {metric!r}")


def rule_mirror(grid, *, metric: str = "manhattan") -> Grid:
    """Pure Python mirror used only for tests/prototypes; Racket stays authoritative."""
    facts = analyze_grid(grid)
    if facts["errors"]:
        raise ValueError(f"invalid Voronoi input: {facts['errors']}")
    r1, c1, r2, c2 = facts["frame_bbox"]
    seeds: tuple[Seed, ...] = facts["seeds"]
    out = _copy_grid(grid)
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            distances = [_distance(seed, r, c, metric) for seed in seeds]
            minimum = min(distances)
            colors = {seed[2] for seed, distance in zip(seeds, distances) if distance == minimum}
            out[r][c] = next(iter(colors)) if len(colors) == 1 else 0
    return out


def _draw_axis(ctx, overrides, label: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]) -> int:
    bounds = full_bounds if overrides.get(label) is not None else default_bounds
    return ctx.draw_int_strict(label, *bounds)


def _default_bounds(difficulty):
    return {
        "easy": ((8, 12), (10, 15), (2, 3)),
        "medium": ((10, 20), (12, 22), (3, 5)),
        "hard": ((14, 30), (16, 30), (4, 8)),
        None: ((9, 18), (11, 20), (3, 5)),
    }[difficulty]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one strict input grid; the production runner applies canonical Racket."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_seeds = _default_bounds(difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", default_h, (8, 30))
    w = _draw_axis(ctx, overrides, "grid_w", default_w, (10, 30))
    n_seeds = _draw_axis(ctx, overrides, "n_seeds", default_seeds, (2, 8))

    layout = ctx.draw_rng("frame-layout")
    frame_h = layout.randint(6, h - 2)
    frame_w = layout.randint(8, w - 2)
    top = layout.randint(1, h - frame_h - 1)
    left = layout.randint(1, w - frame_w - 1)

    grid = full_grid(h, w, 0)
    draw_rect_outline(grid, top, left, frame_h, frame_w, 1)
    interior = [
        (r, c)
        for r in range(top + 1, top + frame_h - 1)
        for c in range(left + 1, left + frame_w - 1)
    ]
    if len(interior) < n_seeds:
        raise ValueError("frame interior cannot hold requested seeds")
    positions = ctx.draw_rng("seed-positions").sample(interior, n_seeds)
    colors = ctx.draw_rng("seed-colors").sample(list(range(2, 10)), n_seeds)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid Voronoi input: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}
    if observed != expected:
        raise ValueError(f"constructed scene did not realize axes: {observed!r} != {expected!r}")
    return _copy_grid(grid)
