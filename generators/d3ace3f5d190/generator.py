"""Generator for the main-diagonal mirror-and-replace rule.

For every output cell, inspect the input cell reflected across the main
 diagonal.  When that reflected cell is nonzero it takes precedence;
otherwise the original cell is retained.  Thus a one-sided mark is copied to
its mirror, while two nonzero transposed cells exchange colors.  Ordinary
samples deliberately include marks on both sides and at least one conflicting
transposed pair, so the weaker "copy only into blanks" shortcut is observable.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d3ace3f5d190"
VERSION = "2.0.0"
TASK_ID = "d3ace3f5d190"
SUMMARY = "Reflect nonzero cells across the main diagonal; a reflected nonzero value replaces its counterpart."

INVARIANTS = [
    "the grid is square so diagonal reflection is in bounds",
    "ordinary samples contain marks on both sides of the main diagonal",
    "ordinary samples include a conflicting transposed pair that distinguishes replacement from blank-only copying",
]

PALETTES = {
    "warm": (1, 2, 4, 7),
    "cool": (3, 5, 6, 9),
    "broad": (1, 3, 4, 6, 7, 9),
    "primary": (1, 2, 4),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_marks", "on_diagonal", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "same as grid_size", "valid": "6..9"},
    "grid_w": {"type": "int", "default": "same as grid_size", "valid": "6..9"},
    "grid_size": {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner": {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force": {"type": "bool", "default": "true", "valid": "true|false"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _exact_int(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def _exact_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _resolve_size(ctx, difficulty: object, overrides: dict[str, object]) -> int:
    explicit: dict[str, int] = {}
    for name in ("grid_size", "grid_h", "grid_w"):
        if name in overrides:
            explicit[name] = _exact_int(overrides[name], 6, 9, name)
    if explicit and len(set(explicit.values())) != 1:
        raise ValueError("grid_size, grid_h, and grid_w must agree for a square grid")
    if explicit:
        return next(iter(explicit.values()))
    if difficulty == "easy":
        return ctx.draw_int("grid_size", 6, 7)
    if difficulty == "hard":
        return ctx.draw_int("grid_size", 8, 9)
    return ctx.draw_int("grid_size", 6, 9)


def _resolve_palette(ctx, overrides: dict[str, object]) -> str:
    texture = overrides.get("texture")
    explicit = overrides.get("palette_kind")
    if texture in PALETTE_KINDS:
        if explicit is not None and explicit != texture:
            raise ValueError("helpful texture and palette_kind must agree")
        explicit = texture
    if explicit is None:
        return ctx.draw_choice("palette_kind", PALETTE_KINDS)
    if type(explicit) is not str or explicit not in PALETTE_KINDS:
        raise ValueError("palette_kind must be one of " + ", ".join(PALETTE_KINDS))
    return explicit


def _axis_partner(n: int, r: int, c: int, axis: str) -> tuple[int, int]:
    if axis == "main":
        return c, r
    if axis == "anti":
        return n - 1 - c, n - 1 - r
    raise ValueError("axis must be main or anti")


def rule_mirror(grid: object, axis: str = "main") -> list[list[int]]:
    """Apply the exact mirror-with-reflected-nonzero-precedence rule."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(grid)  # type: ignore[arg-type]
    result: list[list[int]] = []
    for r in range(n):
        row: list[int] = []
        for c in range(n):
            rr, cc = _axis_partner(n, r, c, axis)
            mirror = grid[rr][cc]  # type: ignore[index]
            row.append(mirror if mirror != 0 else grid[r][c])  # type: ignore[index]
        result.append(row)
    return result


def copy_blank_only_rival(grid: object, axis: str = "main") -> list[list[int]]:
    """Weaker rival: copy reflected marks only into currently blank cells."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(grid)  # type: ignore[arg-type]
    result = [list(row) for row in grid]  # type: ignore[arg-type]
    for r in range(n):
        for c in range(n):
            rr, cc = _axis_partner(n, r, c, axis)
            if result[r][c] == 0 and grid[rr][cc] != 0:  # type: ignore[index]
                result[r][c] = grid[rr][cc]  # type: ignore[index]
    return result


def move_only_rival(grid: object, axis: str = "main") -> list[list[int]]:
    """Weaker rival: retain only the reflected source, erasing unmatched originals."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(grid)  # type: ignore[arg-type]
    return [
        [grid[_axis_partner(n, r, c, axis)[0]][_axis_partner(n, r, c, axis)[1]] for c in range(n)]  # type: ignore[index]
        for r in range(n)
    ]


def _conflict_count(grid: list[list[int]], axis: str) -> int:
    n = len(grid)
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    count = 0
    for r in range(n):
        for c in range(n):
            rr, cc = _axis_partner(n, r, c, axis)
            if (r, c) == (rr, cc):
                continue
            key = tuple(sorted(((r, c), (rr, cc))))
            if key in seen:
                continue
            seen.add(key)
            if grid[r][c] and grid[rr][cc] and grid[r][c] != grid[rr][cc]:
                count += 1
    return count


def analyze_scene(grid: object) -> dict[str, object]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(grid)  # type: ignore[arg-type]
    upper = sum(grid[r][c] != 0 for r in range(n) for c in range(n) if r < c)  # type: ignore[index]
    lower = sum(grid[r][c] != 0 for r in range(n) for c in range(n) if r > c)  # type: ignore[index]
    corners = [(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)]
    anchors = [[r, c] for r, c in corners if grid[r][c] == 8]  # type: ignore[index]
    return {
        "size": n,
        "upper_marks": upper,
        "lower_marks": lower,
        "main_conflicts": _conflict_count(grid, "main"),  # type: ignore[arg-type]
        "anti_conflicts": _conflict_count(grid, "anti"),  # type: ignore[arg-type]
        "corner_anchors": anchors,
        "colors": sorted({value for row in grid for value in row if value != 0}),  # type: ignore[union-attr]
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={},
    )
    n = _resolve_size(ctx, difficulty, overrides)
    texture = overrides.get("texture")
    if texture is not None and (type(texture) is not str or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES):
        raise ValueError("invalid texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, n)

    palette_kind = _resolve_palette(ctx, overrides)
    anchor = _exact_bool(overrides.get("anchor_corner", False), "anchor_corner")
    force_conflict = _exact_bool(overrides.get("asymmetry_force", True), "asymmetry_force")

    pool = list(PALETTES[palette_kind])
    order_rng = ctx.draw_rng("palette_order")
    order_rng.shuffle(pool)
    colors = pool[:3]
    if len(colors) < 3:
        raise AssertionError("palette must provide at least three colors")

    grid = full_grid(n, n, 0)
    candidates = [(r, c) for r in range(n) for c in range(r + 1, n)]
    position_rng = ctx.draw_rng("off_diagonal_positions")
    position_rng.shuffle(candidates)
    selected = candidates[:5]

    r, c = selected[0]
    if force_conflict:
        grid[r][c] = colors[0]
        grid[c][r] = colors[1]
    else:
        grid[r][c] = colors[0]

    r, c = selected[1]
    grid[r][c] = colors[2]
    r, c = selected[2]
    grid[c][r] = colors[0]
    r, c = selected[3]
    grid[r][c] = colors[1]
    r, c = selected[4]
    grid[c][r] = colors[2]

    if anchor:
        corner = ctx.draw_choice("anchor_corner_position", ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)))
        grid[corner[0]][corner[1]] = 8
    return grid


def _draw_from_degenerate(name: str, n: int) -> list[list[int]]:
    grid = full_grid(n, n, 0)
    if name == "no_marks":
        return grid
    if name == "on_diagonal":
        for i in range(n):
            grid[i][i] = 3
        return grid
    if name == "full_grid":
        for r in range(n):
            for c in range(n):
                grid[r][c] = 3
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")


def _shape_errors(grid: object) -> list[str]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid must be a non-empty rectangle"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be a non-empty rectangle"]
    if len(grid) != width:
        return [f"diagonal reflection requires a square grid; got {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be exact integers in 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    msgs = _shape_errors(grid)
    if msgs:
        return msgs
    n = len(grid)
    off_diag = [(r, c) for r in range(n) for c in range(n) if r != c and grid[r][c] != 0]
    if len(off_diag) < 3:
        msgs.append("expected at least three off-diagonal marks")
    colors = {grid[r][c] for r, c in off_diag if grid[r][c] != 8}
    if len(colors) < 3:
        msgs.append("expected at least three source colors to disambiguate transpose copying")
    anchors = [(r, c) for r, c in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)) if grid[r][c] == 8]
    if len(anchors) > 1:
        msgs.append("expected at most one color-8 corner anchor")
    return msgs
