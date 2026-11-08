"""Generator for ``ebc5c876edba`` — mirror red cells across a gray guide.

The input has one full-height color-5 vertical bar.  A color-2 source pattern
lies wholly on one side of that bar and every source cell has an in-bounds,
empty mirror destination.  The Racket oracle preserves the input and paints
those reflected destinations color 8.

This generator deliberately varies guide position, source side, connectedness,
size, and canvas dimensions.  Those variations rebut fixed-side, fixed-center,
fixed-shape, fixed-size, and count-only shortcuts while staying on the exact
canonical rule.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ebc5c876edba"
# 3.0.0 repairs the v14 exact-override contract, removes dead pseudo-axes,
# adds task-semantic branch coverage, and strengthens mutation rejection.
VERSION = "3.0.0"
TASK_ID = "ebc5c876edba"
RULE_HASH = "4f52e6c7b24b"  # sha256[:12] of normalized canonical program_solution

SUMMARY = (
    "A 6..14 by 7..18 background-0 grid contains exactly one full-height "
    "color-5 vertical guide. Exactly 2..8 color-2 source cells lie wholly on "
    "one side, form either one connected component or two separated components, "
    "and have empty in-bounds mirror destinations. The output preserves the "
    "input and paints color 8 at (r, 2*guide_col-c) for every color-2 source."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "rectangular 6..14 by 7..18 grid with palette exactly contained in {0,2,5}",
    "exactly one full-height color-5 guide column and no stray color-5 cells",
    "2..8 color-2 source cells lie wholly on exactly one side of the guide",
    "every source cell has an in-bounds background mirror destination",
    "the source union has exactly one or two 4-connected components",
    "at least one source cell is two or more columns from the guide",
]

# Malformed semantic probes for defect-lint and focused tests.  They are not
# lawful training axes, so they intentionally stay outside AXES.
DEGENERATE_TEXTURES = (
    "no_bar",
    "multiple_bars",
    "no_cells",
    "cells_both_sides",
    "clipped_reflection",
    "occupied_mirror",
    "unexpected_color",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..18",
        "valid": "7..18",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-aware 2..8",
        "valid": "2..8",
    },
    "source_side": {
        "type": "str",
        "default": "scheduled left|right",
        "valid": "left|right",
    },
    "layout": {
        "type": "str",
        "default": "scheduled connected|split",
        "valid": "connected|split",
    },
    "axis_position": {
        "type": "str",
        "default": "scheduled center|off_center",
        "valid": "center|off_center",
    },
}


def _full_bar_columns(grid: list[list[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    return [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        queue = deque([remaining.pop()])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _grow_connected(
    rng,
    allowed: set[tuple[int, int]],
    count: int,
    *,
    start: tuple[int, int],
) -> set[tuple[int, int]]:
    """Grow exactly ``count`` 4-connected cells inside a rectangular region."""
    if count < 1 or count > len(allowed) or start not in allowed:
        raise ValueError(
            f"cannot grow {count} connected cells in region of size {len(allowed)}"
        )
    cells = {start}
    frontier = {
        (start[0] + dr, start[1] + dc)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if (start[0] + dr, start[1] + dc) in allowed
    }
    while len(cells) < count:
        if not frontier:
            raise ValueError("connected-growth frontier exhausted")
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        cells.add(cell)
        r, c = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in allowed and nxt not in cells:
                frontier.add(nxt)
    return cells


def _source_region(h: int, w: int, axis: int, side: str) -> set[tuple[int, int]]:
    """All cells on ``side`` whose equal-distance reflection is in-bounds."""
    span = min(axis, w - 1 - axis)
    if span < 2:
        raise ValueError("guide leaves fewer than two mirrorable source columns")
    if side == "left":
        columns = range(axis - span, axis)
    elif side == "right":
        columns = range(axis + 1, axis + span + 1)
    else:
        raise ValueError(f"unknown source_side {side!r}")
    return {(r, c) for r in range(h) for c in columns}


def _far_column(region: set[tuple[int, int]], side: str) -> int:
    return min(c for _, c in region) if side == "left" else max(c for _, c in region)


def _draw_source_cells(
    rng,
    region: set[tuple[int, int]],
    count: int,
    layout: str,
    h: int,
    side: str,
) -> set[tuple[int, int]]:
    far_col = _far_column(region, side)
    if layout == "connected":
        starts = sorted(p for p in region if p[1] == far_col)
        return _grow_connected(rng, region, count, start=rng.choice(starts))
    if layout != "split":
        raise ValueError(f"unknown layout {layout!r}")

    # A completely empty separator row makes the intended two-component branch
    # unambiguous.  h>=6 and n_cells<=8 guarantee both bands have capacity even
    # at the minimum two-column mirrorable span.
    gap_row = h // 2
    top = {p for p in region if p[0] < gap_row}
    bottom = {p for p in region if p[0] > gap_row}
    first_count = count // 2
    second_count = count - first_count
    if first_count > len(top) or second_count > len(bottom):
        raise ValueError(
            "split layout incompatible with requested dimensions and cell count"
        )
    first_starts = sorted(p for p in top if p[1] == far_col)
    second_starts = sorted(p for p in bottom if p[1] == far_col)
    first = _grow_connected(
        rng, top, first_count, start=rng.choice(first_starts)
    )
    second = _grow_connected(
        rng, bottom, second_count, start=rng.choice(second_starts)
    )
    return first | second


def _axis_column(w: int, axis_position: str, rng) -> int:
    if axis_position == "center":
        return w // 2
    if axis_position != "off_center":
        raise ValueError(f"unknown axis_position {axis_position!r}")
    central = {(w - 1) // 2, w // 2}
    candidates = [c for c in range(2, w - 2) if c not in central]
    if not candidates:
        raise ValueError(f"no off-center guide position for width {w}")
    return rng.choice(candidates)


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    result: dict[str, int | str] = {"grid_h": h, "grid_w": w}
    bars = _full_bar_columns(grid)
    if len(bars) != 1:
        return result
    axis = bars[0]
    twos = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    }
    left = any(c < axis for _, c in twos)
    right = any(c > axis for _, c in twos)
    side = "left" if left and not right else "right" if right and not left else "mixed"
    components = _component_count(twos) if twos else 0
    layout = "connected" if components == 1 else "split" if components == 2 else "other"
    axis_position = "center" if axis == w // 2 else "off_center"
    result.update(
        {
            "n_cells": len(twos),
            "source_side": side,
            "layout": layout,
            "axis_position": axis_position,
        }
    )
    return result


def _scheduled_choice(ctx, name: str, full_options: tuple[str, ...], value: str, overrides):
    """Record a deterministic lesson-schedule choice while honoring overrides."""
    options = full_options if name in overrides else (value,)
    return ctx.draw_choice(name, options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is not None:
        raise ValueError(f"unknown texture {texture!r}")

    # Full declared domains remain valid in every band. Difficulty changes only
    # the ordinary draw prior, never the explicit override contract.
    h = ctx.draw_int_diff("grid_h", 6, 14)
    w = ctx.draw_int_diff("grid_w", 7, 18)

    if "n_cells" in overrides:
        n_cells = ctx.draw_int("n_cells", 2, 8)
    elif difficulty == "easy":
        n_cells = ctx.draw_int("n_cells", 2, 4)
    elif difficulty == "hard":
        n_cells = ctx.draw_int("n_cells", 5, 8)
    else:
        n_cells = ctx.draw_int("n_cells", 3, 6)

    # Every four consecutive samples contain a centered canonical-like lesson,
    # an off-center right-source witness, and a two-component witness.
    profile = sample_index % 4
    source_side = _scheduled_choice(
        ctx,
        "source_side",
        ("left", "right"),
        "right" if profile == 1 else "left",
        overrides,
    )
    layout = _scheduled_choice(
        ctx,
        "layout",
        ("connected", "split"),
        "split" if profile == 2 else "connected",
        overrides,
    )
    axis_position = _scheduled_choice(
        ctx,
        "axis_position",
        ("center", "off_center"),
        "center" if profile in (0, 2) else "off_center",
        overrides,
    )

    axis = _axis_column(w, axis_position, ctx.draw_rng("axis_geometry"))
    region = _source_region(h, w, axis, source_side)
    if n_cells > len(region):
        raise ValueError("requested n_cells does not fit the mirrorable source region")
    cells = _draw_source_cells(
        ctx.draw_rng("source_geometry"),
        region,
        n_cells,
        layout,
        h,
        source_side,
    )

    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][axis] = 5
    for r, c in cells:
        g[r][c] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task input grammar and exact requested axes."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular and nonempty"]
    h = len(grid)
    if not (6 <= h <= 14 and 7 <= w <= 18):
        errors.append(f"grid dimensions {h}x{w} outside 6..14 by 7..18")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    unexpected = sorted({value for row in grid for value in row} - {0, 2, 5})
    if unexpected:
        errors.append(f"input contains unexpected colors {unexpected}; expected only 0,2,5")

    bars = _full_bar_columns(grid)
    if len(bars) != 1:
        errors.append(f"expected exactly one full color-5 guide column, found {len(bars)}")
        return errors
    axis = bars[0]
    stray_fives = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 5 and c != axis
    ]
    if stray_fives:
        errors.append(f"found {len(stray_fives)} stray color-5 cells outside the guide")

    twos = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    }
    if not (2 <= len(twos) <= 8):
        errors.append(f"expected 2..8 color-2 source cells, found {len(twos)}")

    left = {(r, c) for r, c in twos if c < axis}
    right = {(r, c) for r, c in twos if c > axis}
    on_bar = {(r, c) for r, c in twos if c == axis}
    if on_bar:
        errors.append("color-2 source cell lies on the color-5 guide")
    if bool(left) == bool(right):
        errors.append("color-2 source cells must lie wholly on exactly one side")

    clipped = []
    occupied = []
    for r, c in twos:
        mirror_col = 2 * axis - c
        if not 0 <= mirror_col < w:
            clipped.append((r, c, mirror_col))
        elif grid[r][mirror_col] != 0:
            occupied.append(((r, c), (r, mirror_col), grid[r][mirror_col]))
    if clipped:
        errors.append(f"{len(clipped)} source cells have out-of-bounds mirrors")
    if occupied:
        errors.append(f"{len(occupied)} source cells have non-background mirror targets")

    if twos:
        components = _component_count(twos)
        if components not in (1, 2):
            errors.append(f"source union must have one or two components, found {components}")
        if max(abs(c - axis) for _, c in twos) < 2:
            errors.append("all source cells touch the guide; need an offset >=2 cue")

    observed = observe_overrides(grid)
    requested = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    for name, value in requested.items():
        if name in observed and observed[name] != value:
            errors.append(
                f"override {name} requested {value!r}, observed {observed[name]!r}"
            )
    return errors


def _base_degenerate_grid(h: int = 7, w: int = 9, axis: int = 4):
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][axis] = 5
    return g


def _draw_from_degenerate(name: str, ctx):
    """Return varied malformed scenes that ``self_check`` must reject."""
    rng = ctx.draw_rng(f"degenerate_{name}")
    h = 7 + rng.randint(0, 2)
    w = 9 + 2 * rng.randint(0, 1)
    axis = w // 2
    g = _base_degenerate_grid(h, w, axis)

    if name == "no_bar":
        for r in range(h):
            g[r][axis] = 0
        g[1][1] = 2
        g[2][1] = 2
    elif name == "multiple_bars":
        for r in range(h):
            g[r][axis - 2] = 5
        g[1][axis - 1] = 2
        g[2][axis - 1] = 2
    elif name == "no_cells":
        pass
    elif name == "cells_both_sides":
        g[1][axis - 2] = 2
        g[2][axis - 2] = 2
        g[4][axis + 2] = 2
        g[5][axis + 2] = 2
    elif name == "clipped_reflection":
        for r in range(h):
            g[r][axis] = 0
            g[r][w - 2] = 5
        g[1][0] = 2
        g[2][0] = 2
    elif name == "occupied_mirror":
        g[1][axis - 2] = 2
        g[2][axis - 2] = 2
        g[1][axis + 2] = 8
    elif name == "unexpected_color":
        g[1][axis - 2] = 2
        g[2][axis - 2] = 2
        g[4][1] = 3
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return g


def mutation_fixtures():
    """Task-linked near-misses that every structural review must reject."""
    fixtures = []
    for index, name in enumerate(DEGENERATE_TEXTURES, start=1):
        ctx = gen_ctx(
            seed=100 + index,
            sample_index=index,
            version=VERSION,
            task_id=TASK_ID,
        )
        fixtures.append((name, _draw_from_degenerate(name, ctx)))
    return fixtures
