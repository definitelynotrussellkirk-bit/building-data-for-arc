"""Generator for ARC task e44712f65f3e.

Each nonzero object is a solid square nested frame: one uniform outer-ring
color around one uniform inner-fill color.  The canonical rule expands every
such frame, centered on its original location, into a larger rounded nested
motif on an otherwise zero canvas.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e44712f65f3e"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "1a62f4b43149"
SUMMARY = (
    "A zero-background grid contains one or more disjoint solid square nested "
    "frames. Each frame has a uniform nonzero outer ring and a distinct "
    "uniform nonzero inner fill. The canonical output expands every frame "
    "about its center into a larger rounded nested frame motif."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0",
    "each nonzero component is a fully occupied square of size 3..8",
    "each component has one uniform outer-ring color and one distinct inner color",
    "each centered expanded motif fits inside the grid",
]
AXES = {
    "frame_size": {"type": "int", "default": "difficulty-aware rng 3..8", "valid": "3..8"},
    "outer_color": {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "inner_color": {"type": "color", "default": "rng nonzero distinct from outer", "valid": "1..9"},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))


def _draw_size(ctx, difficulty, overrides) -> int:
    if overrides.get("frame_size") is not None:
        return ctx.draw_int_strict("frame_size", 3, 8)
    if difficulty == "easy":
        lo, hi = 3, 4
    elif difficulty == "hard":
        lo, hi = 6, 8
    else:
        lo, hi = 3, 8
    return ctx.draw_int("frame_size", lo, hi)


def _components(grid):
    """Four-connected components of all nonzero cells, independent of color."""
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = set()
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    stack.append((nr, nc))
        result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full nested-frame source grammar, including multi-object canonicals."""
    if type(grid) is not list or not grid:
        return ["empty grid"]
    if type(grid[0]) is not list or not grid[0]:
        return ["empty first row"]
    height, width = len(grid), len(grid[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        return [f"grid dimensions {height}x{width} outside 1..30"]
    errors: list[str] = []
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid cell {value!r} at ({r},{c})")
    if errors:
        return errors

    comps = _components(grid)
    if not comps:
        return ["expected at least one nested-frame component"]
    for index, cells in enumerate(comps):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        prefix = f"component {index}"
        if frame_h != frame_w:
            errors.append(f"{prefix} bbox is not square: {frame_h}x{frame_w}")
            continue
        if not 3 <= frame_h <= 8:
            errors.append(f"{prefix} frame size {frame_h} outside 3..8")
        expected_cells = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        }
        if cells != expected_cells:
            errors.append(f"{prefix} bbox is not fully occupied")
            continue
        colors = {grid[r][c] for r, c in cells}
        if 0 in colors or len(colors) != 2:
            errors.append(
                f"{prefix} should use exactly two nonzero colors, got {sorted(colors)}"
            )
            continue
        outer = grid[r0][c0]
        inner_colors = colors - {outer}
        if len(inner_colors) != 1:
            errors.append(f"{prefix} has no unique inner color")
            continue
        inner = next(iter(inner_colors))
        mismatch = False
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                expected = outer if r in (r0, r1) or c in (c0, c1) else inner
                if grid[r][c] != expected:
                    errors.append(f"{prefix} outer ring / inner fill colors are inconsistent")
                    mismatch = True
                    break
            if mismatch:
                break
        half = frame_h // 2
        out_size = 2 * frame_h if frame_h % 2 == 0 else 2 * frame_h - 1
        if (
            r0 - half < 0
            or c0 - half < 0
            or r0 - half + out_size > height
            or c0 - half + out_size > width
        ):
            errors.append(f"{prefix} centered expanded motif would clip outside the grid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size = _draw_size(ctx, difficulty, overrides)
    outer = ctx.draw_color_strict("outer_color", exclude={0})
    inner = ctx.draw_color_strict("inner_color", exclude={0, outer})
    layout = ctx.draw_rng("layout")

    # One spare cell beyond the exact expansion margin prevents border-touching
    # shortcuts while retaining the complete lawful size range.
    margin = size // 2 + 1
    need = size + 2 * margin
    height = layout.randint(need, min(30, need + 6))
    width = layout.randint(need, min(30, need + 6))
    r0 = layout.randint(margin, height - size - margin)
    c0 = layout.randint(margin, width - size - margin)
    grid = full_grid(height, width, 0)
    for r in range(size):
        for c in range(size):
            grid[r0 + r][c0 + c] = (
                outer if r in (0, size - 1) or c in (0, size - 1) else inner
            )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid grid: " + "; ".join(errors))
    return grid
