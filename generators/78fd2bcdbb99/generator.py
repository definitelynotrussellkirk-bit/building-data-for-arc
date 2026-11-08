"""Generator for canonical near-symmetry repair task 78fd2bcdbb99.

The reference rule counts left/right and up/down mismatches, chooses the axis
with fewer mismatches (left/right on ties), and copies each nonzero mirror into
an empty cell.  The curriculum deliberately covers both selected axes and both
single- and multi-color patterns; canonical inputs are therefore inside the
validated grammar instead of being rejected by a narrower teaching subset.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78fd2bcdbb99"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
SUMMARY = (
    "A grid is almost symmetric left/right or up/down. Count mismatches for "
    "both axes, choose the axis with fewer mismatches (left/right on a tie), "
    "then restore empty cells from their nonzero mirrors. Patterns may use "
    "one or several colors."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and all cells are ARC colors",
    "the selected axis is determined by the reference mismatch comparison",
    "at least one empty cell has a nonzero mirror on the selected axis",
    "ordinary schedules cover both left/right and up/down selection",
    "ordinary schedules include single- and multi-color patterns",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("full_symmetric", "no_pattern", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "5..14"},
    "color": {"type": "color", "default": "rng !0", "valid": "1..9"},
    "density": {"type": "float", "default": "difficulty-aware", "valid": "0.2..0.6"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "n_missing": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "anchor_corner": {"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size": {"type": "int", "default": "schedule 1,1,2,3", "valid": "1..3"},
    "symmetry_axis": {"type": "str", "default": "schedule lr,ud", "valid": "lr|ud"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _exact_int(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (4, 10),
        "grid_w": (5, 14),
        "color": (1, 9),
        "n_missing": (1, 3),
        "palette_size": (1, 3),
    }
    for name, (low, high) in bounds.items():
        if name in overrides:
            _exact_int(name, overrides[name], low, high)
    if "density" in overrides:
        value = overrides["density"]
        if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value) or not 0.2 <= value <= 0.6:
            raise ValueError("density must be a finite number in [0.2, 0.6]")
    if "anchor_corner" in overrides and type(overrides["anchor_corner"]) is not bool:
        raise ValueError("anchor_corner must be a boolean")
    if "symmetry_axis" in overrides and overrides["symmetry_axis"] not in ("lr", "ud"):
        raise ValueError("symmetry_axis must be 'lr' or 'ud'")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError("palette_kind must be one of " + ", ".join(PALETTE_KINDS))
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("texture is not a supported palette or degenerate texture")


def _axis_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in overrides:
        return _exact_int(label, overrides[label], valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _mirror(h, w, axis, row, col):
    if axis == "lr":
        return row, w - 1 - col
    return h - 1 - row, col


def _mismatch_count(grid, axis):
    h, w = len(grid), len(grid[0])
    return sum(
        grid[r][c] != grid[mr][mc]
        for r in range(h)
        for c in range(w)
        for mr, mc in [_mirror(h, w, axis, r, c)]
    )


def selected_axis(grid):
    """Return the exact axis selected by the canonical mismatch comparison."""
    return "lr" if _mismatch_count(grid, "lr") <= _mismatch_count(grid, "ud") else "ud"


def semantic_observables(grid) -> dict:
    issues = _grid_issues(grid)
    if issues:
        raise ValueError("; ".join(issues))
    h, w = len(grid), len(grid[0])
    axis = selected_axis(grid)
    fillable = [
        (r, c)
        for r in range(h)
        for c in range(w)
        for mr, mc in [_mirror(h, w, axis, r, c)]
        if grid[r][c] == 0 and grid[mr][mc] != 0
    ]
    colors = sorted({value for row in grid for value in row if value != 0})
    return {
        "height": h,
        "width": w,
        "lr_mismatches": _mismatch_count(grid, "lr"),
        "ud_mismatches": _mismatch_count(grid, "ud"),
        "selected_axis": axis,
        "palette_size": len(colors),
        "colors": colors,
        "fillable_count": len(fillable),
        "fillable": fillable,
    }


def _grid_issues(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must lie within 1..30"]
    if any(type(cell) is not int or isinstance(cell, bool) or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["cells must be exact integer ARC colors 0..9"]
    return []


def rule_mirror(grid):
    """Pure Python mirror of the selected canonical Racket rule."""
    issues = _grid_issues(grid)
    if issues:
        raise ValueError("; ".join(issues))
    h, w = len(grid), len(grid[0])
    axis = selected_axis(grid)
    output = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            mr, mc = _mirror(h, w, axis, r, c)
            if grid[r][c] == 0 and grid[mr][mc] != 0:
                output[r][c] = grid[mr][mc]
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the canonical rule's actual domain, not a narrower LR-only subset."""
    del difficulty, meta
    issues = _grid_issues(grid)
    if issues:
        return issues
    facts = semantic_observables(grid)
    if facts["palette_size"] == 0:
        issues.append("pattern must contain at least one nonzero cell")
    if facts["fillable_count"] == 0:
        issues.append("selected axis has no empty cell with a nonzero mirror")
    return issues


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [2, 3, 4, 5]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout_" + str(difficulty))
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, rng)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, density_default = 4, 6, 5, 8, 0.3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, density_default = 9, 10, 11, 14, 0.55
    else:
        h_lo, h_hi, w_lo, w_hi, density_default = 6, 8, 7, 10, 0.42

    h = _axis_int(ctx, overrides, "grid_h", h_lo, h_hi, 4, 10)
    w = _axis_int(ctx, overrides, "grid_w", w_lo, w_hi, 5, 14)
    role = sample_index % 4
    axis = overrides.get("symmetry_axis", ("lr", "ud", "lr", "ud")[role])
    palette_size = overrides.get("palette_size", (1, 1, 2, 3)[role])
    n_missing = overrides.get("n_missing")
    if n_missing is None:
        n_missing = ctx.draw_int("n_missing", 1, min(3, max(1, (h // 2) * (w // 2) - 1)))
    density = float(overrides.get("density", density_default))
    anchor_corner = overrides.get("anchor_corner", False)

    palette_kind = (
        texture
        or overrides.get("palette_kind")
        or ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    )
    pool = _build_palette(palette_kind, rng)
    primary = overrides.get("color")
    colors = []
    if primary is not None:
        colors.append(primary)
    colors.extend(color for color in pool if color not in colors)
    colors = colors[:palette_size]
    if len(colors) < palette_size:
        colors.extend(color for color in range(1, 10) if color not in colors)
        colors = colors[:palette_size]

    anchors = [(r, c) for r in range(h // 2) for c in range(w // 2)]
    minimum_pairs = max(n_missing + 1, palette_size)
    target_pairs = max(minimum_pairs, int(round(len(anchors) * density)))
    target_pairs = min(len(anchors), target_pairs)
    if target_pairs < minimum_pairs:
        raise ValueError("requested grid is too small for n_missing/palette_size")

    chosen = []
    corner = (0, 0)
    if anchor_corner:
        chosen.append(corner)
    remaining = [cell for cell in anchors if cell not in chosen]
    rng.shuffle(remaining)
    chosen.extend(remaining[: target_pairs - len(chosen)])
    rng.shuffle(chosen)

    grid = full_grid(h, w, 0)
    for index, (r, c) in enumerate(chosen):
        mr, mc = _mirror(h, w, axis, r, c)
        color = colors[index % len(colors)]
        grid[r][c] = color
        grid[mr][mc] = color

    holes = list(chosen)
    rng.shuffle(holes)
    for r, c in holes[:n_missing]:
        mr, mc = _mirror(h, w, axis, r, c)
        if rng.randrange(2):
            grid[r][c] = 0
        else:
            grid[mr][mc] = 0

    facts = semantic_observables(grid)
    if facts["selected_axis"] != axis:
        raise AssertionError(f"constructed {axis} lesson selected {facts['selected_axis']}")
    if facts["fillable_count"] != n_missing:
        raise AssertionError("constructed missing-cell count differs from request")
    if facts["palette_size"] != palette_size:
        raise AssertionError("constructed palette size differs from request")
    issues = self_check(grid, difficulty=difficulty)
    if issues:
        raise AssertionError("generated invalid lesson: " + "; ".join(issues))
    return grid


def _draw_from_degenerate(name, rng):
    del rng
    h, w = 6, 8
    grid = full_grid(h, w, 0)
    if name == "full_symmetric":
        for r in range(1, h - 1):
            for c in range(1, w // 2):
                grid[r][c] = 3
                grid[r][w - 1 - c] = 3
    elif name == "full_grid":
        for r in range(h):
            for c in range(w):
                grid[r][c] = 3
    return grid
