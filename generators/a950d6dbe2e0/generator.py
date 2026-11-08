"""Multicolour upper-left motifs for two-axis reflection.

Only inputs are sampled here. The unchanged canonical Racket rule owns labels.
Every default three-demo window contains rectangular teaching examples; canonical
square profiles recur without replaying canonical positions or colour identities.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a950d6dbe2e0"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6c2ec896ad53"
SUMMARY = "Reflect a multicolour upper-left motif across both full-grid midlines."
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "even rectangular canvas, each dimension 4..30, background 0",
    "2..64 occupied cells, all strictly in the upper-left quadrant",
    "2..9 distinct nonzero integer colours; every chosen colour occurs",
    "cell and colour counts fit the selected quadrant without truncation",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled square/rectangle; difficulty-weighted", "valid": "4..30 (even)"},
    "grid_w": {"type": "int", "default": "scheduled square/rectangle; difficulty-weighted", "valid": "4..30 (even)"},
    "n_cells": {"type": "int", "default": "5..6 on core; otherwise capacity/difficulty-weighted", "valid": "2..64"},
    "n_distinct_colors": {"type": "int", "default": "2..3 on core; otherwise 2..min(9,n_cells)", "valid": "2..9"},
}
# Conditional impossibilities are identified by the actual exception's axes.
# No broad tuple wildcard excuses an unrelated implementation failure.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical_square", "rectangle")
_DIMENSIONS = tuple(range(4, 31, 2))


def schedule_profile(seed, sample_index, difficulty=None):
    """Default schedule only; explicit controls take precedence over it."""
    return SCHEDULE_PROFILES[0 if sample_index % 3 == 0 else 1]


def _incompatible(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(axes))
    raise error


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    for name, value in active.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if name in ("grid_h", "grid_w") and value not in _DIMENSIONS:
            raise ValueError(f"{name} must be even and in 4..30")
        if name == "n_cells" and not 2 <= value <= 64:
            raise ValueError("n_cells must be in 2..64")
        if name == "n_distinct_colors" and not 2 <= value <= 9:
            raise ValueError("n_distinct_colors must be in 2..9")
    if ("n_cells" in active and "n_distinct_colors" in active
            and active["n_distinct_colors"] > active["n_cells"]):
        _incompatible("n_distinct_colors cannot exceed n_cells",
                      ("n_distinct_colors", "n_cells"))
    return active


def _weighted(values, preferred):
    return list(values) + [v for v in preferred if v in values] * 5


def _shape(ctx, active, core, difficulty):
    required = max(2, active.get("n_cells", 2), active.get("n_distinct_colors", 2))
    shapes = [(h, w) for h in _DIMENSIONS for w in _DIMENSIONS
              if h == active.get("grid_h", h) and w == active.get("grid_w", w)
              and (h // 2) * (w // 2) >= required]
    if not shapes:
        _incompatible("grid_h/grid_w quadrant cannot fit n_cells/n_distinct_colors",
                      active.keys())
    if not active:
        if core:
            shapes = [(h, w) for h, w in shapes if h == w and h in (8, 10, 12)]
        else:
            shapes = [(h, w) for h, w in shapes if h != w]
    preferred = {"easy": (6, 8, 10, 12), "medium": (8, 10, 12, 14, 16),
                 "hard": (12, 14, 16, 18, 20)}.get(difficulty, (8, 10, 12, 14))
    heights = sorted({h for h, _ in shapes})
    h = ctx.draw_choice("grid_h", _weighted(heights, preferred))
    widths = sorted({w for hh, w in shapes if hh == h})
    w = ctx.draw_choice("grid_w", _weighted(widths, preferred))
    return h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=active)
    core = not active and schedule_profile(seed, sample_index, difficulty) == "canonical_square"
    h, w = _shape(ctx, active, core, difficulty)
    capacity = (h // 2) * (w // 2)
    minimum = max(2, active.get("n_distinct_colors", 2))
    counts = list(range(minimum, min(64, capacity) + 1))
    preferred = {"easy": range(2, 7), "medium": range(4, 13),
                 "hard": range(8, 25)}.get(difficulty, range(4, 13))
    n = ctx.draw_choice("n_cells", [5, 6] if core else _weighted(counts, preferred))
    color_counts = list(range(2, min(n, 9) + 1))
    k = ctx.draw_choice("n_distinct_colors", [2, 3] if core else _weighted(color_counts, (2, 3)))
    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), k)
    color_rng = ctx.draw_rng("colour_assignment")
    colors = palette + color_rng.choices(palette, k=n-k)
    color_rng.shuffle(colors)
    coordinates = ctx.draw_rng("positions").sample(
        [(r, c) for r in range(h // 2) for c in range(w // 2)], n)
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(coordinates, colors):
        grid[r][c] = color
    return grid


def observe_overrides(grid):
    cells = [v for row in grid for v in row if v != 0]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_cells": len(cells), "n_distinct_colors": len(set(cells))}


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colours 0..9 (not booleans)"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h not in _DIMENSIONS or w not in _DIMENSIONS:
        errors.append("dimensions must be even and in 4..30")
    if any(v and (r >= h // 2 or c >= w // 2)
           for r, row in enumerate(grid) for c, v in enumerate(row)):
        errors.append("only the upper-left quadrant may contain source cells")
    observed = observe_overrides(grid)
    if not 2 <= observed["n_cells"] <= 64:
        errors.append("source must contain 2..64 cells")
    if not 2 <= observed["n_distinct_colors"] <= 9:
        errors.append("training motifs must contain at least two distinct colours")
    return errors


def strict_canonical_like(grid):
    """Task-domain membership, separately from the exact-size profile floor."""
    return self_check(grid)


def _rival_paint(grid, row_extent, col_extent):
    """Shared mechanics for deliberately incomplete/wrong rules, never labels."""
    h, w = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for r in range(h // 2):
        for c in range(w // 2):
            if grid[r][c] == 0:
                continue
            rows = (r,) if row_extent is None else (r, row_extent - 1 - r)
            cols = (c,) if col_extent is None else (c, col_extent - 1 - c)
            for rr in rows:
                for cc in cols:
                    if 0 <= rr < h and 0 <= cc < w:
                        output[rr][cc] = grid[r][c]
    return output


def _height_for_both_axes(grid):
    return _rival_paint(grid, len(grid), len(grid))


def _width_for_both_axes(grid):
    return _rival_paint(grid, len(grid[0]), len(grid[0]))


def _horizontal_only(grid):
    return _rival_paint(grid, None, len(grid[0]))


def _vertical_only(grid):
    return _rival_paint(grid, len(grid), None)


def _identity(grid):
    return [list(row) for row in grid]


def _rectangular(grid):
    return not self_check(grid) and len(grid) != len(grid[0])


SEMANTIC_WITNESSES = {"rectangular_canvas": _rectangular}
SEMANTIC_RIVALS = {"height_for_both_axes": _height_for_both_axes,
                   "width_for_both_axes": _width_for_both_axes}
WITNESS_RIVALS = {"rectangular_canvas": list(SEMANTIC_RIVALS)}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = {**SEMANTIC_RIVALS, "horizontal_only": _horizontal_only,
                      "vertical_only": _vertical_only, "identity": _identity}


def lesson_identifiable(demos, query):
    """Finite declared-rival teaching check; no claim of universal uniqueness."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
