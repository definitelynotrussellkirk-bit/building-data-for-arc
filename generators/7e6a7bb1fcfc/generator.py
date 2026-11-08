"""Generator for arc_puzzle_bank_21_set6:hard_f01.

The input contains a chain of strictly nested rectangular outline frames and
several other connected objects.  The output removes every frame and preserves
each non-frame object's cells while recoloring it by the number of frames that
strictly enclose its bounding-box center:

    depth 1 -> 2, depth 2 -> 3, depth 3 -> 8, depth 4 -> 6, otherwise -> 1.

Frame and object input colors are deliberately non-semantic and vary between
instances.  A valid generated scene contains witnesses at multiple depths, and
ordinary draws also include same-colored objects at different depths plus
same-depth objects of different colors to rebut color- and position-based
shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e6a7bb1fcfc"
VERSION = "2.0.0"
TASK_ID = "7e6a7bb1fcfc"
RULE_HASH = "b64178ea8201"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Strictly nested rectangular outline frames contain ordinary connected "
    "objects at several enclosure depths.  Drop the frames and repaint each "
    "ordinary object by the number of frames enclosing its bbox center: "
    "1→2, 2→3, 3→8, 4→6, and every other depth→1."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "at least two nonzero rectangular outline frames form one strictly nested chain",
    "at least two connected non-frame objects stay within one enclosure-depth region",
    "non-frame objects occur at at least two distinct enclosure depths",
    "input colors do not encode frame depth or output color",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 11..24", "valid": "11..24"},
    "grid_w": {"type": "int", "default": "difficulty-aware 11..24", "valid": "11..24"},
    "n_frames": {"type": "int", "default": "difficulty-aware 2..4", "valid": "2..4"},
    "n_shapes": {"type": "int", "default": "n_frames+2 up to 8", "valid": "4..8"},
}

_DEPTH_COLOR = {1: 2, 2: 3, 3: 8, 4: 6}
_COLORS = tuple(range(1, 10))
_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    """Return 4-connected, same-color non-background components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    materialized = list(cells)
    rs = [r for r, _ in materialized]
    cs = [c for _, c in materialized]
    return min(rs), min(cs), max(rs), max(cs)


def _outline_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _is_rect_outline(cells: list[tuple[int, int]]) -> bool:
    box = _bbox(cells)
    r1, c1, r2, c2 = box
    return r2 - r1 >= 2 and c2 - c1 >= 2 and set(cells) == _outline_cells(box)


def _box_area(box: tuple[int, int, int, int]) -> int:
    r1, c1, r2, c2 = box
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _strictly_contains(
    outer: tuple[int, int, int, int],
    inner: tuple[int, int, int, int],
    *,
    blank_gap: bool,
) -> bool:
    or1, oc1, or2, oc2 = outer
    ir1, ic1, ir2, ic2 = inner
    gap = 2 if blank_gap else 1
    return (
        ir1 - or1 >= gap
        and ic1 - oc1 >= gap
        and or2 - ir2 >= gap
        and oc2 - ic2 >= gap
    )


def _depth_for_center(
    cells: list[tuple[int, int]],
    frame_boxes: list[tuple[int, int, int, int]],
) -> int:
    r1, c1, r2, c2 = _bbox(cells)
    cr = (r1 + r2) / 2.0
    cc = (c1 + c2) / 2.0
    return sum(fr1 < cr < fr2 and fc1 < cc < fc2 for fr1, fc1, fr2, fc2 in frame_boxes)


def _cell_depth(r: int, c: int, frame_boxes: list[tuple[int, int, int, int]]) -> int:
    return sum(fr1 < r < fr2 and fc1 < c < fc2 for fr1, fc1, fr2, fc2 in frame_boxes)


def _analyze_scene(grid: list[list[int]]) -> dict[str, object]:
    frames: list[dict[str, object]] = []
    shapes: list[dict[str, object]] = []
    for color, cells in _components(grid):
        record = {"color": color, "cells": cells, "box": _bbox(cells)}
        if _is_rect_outline(cells):
            frames.append(record)
        else:
            shapes.append(record)
    frames.sort(key=lambda record: _box_area(record["box"]), reverse=True)  # type: ignore[arg-type]
    boxes = [record["box"] for record in frames]
    for record in shapes:
        record["depth"] = _depth_for_center(record["cells"], boxes)  # type: ignore[arg-type]
    return {"frames": frames, "shapes": shapes, "frame_boxes": boxes}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's structural input grammar, not just palette/shape."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    h = len(grid)
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC bounds: {h}x{w}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return errors + ["grid colors must be integers in 0..9"]

    scene = _analyze_scene(grid)
    frames = scene["frames"]  # type: ignore[assignment]
    shapes = scene["shapes"]  # type: ignore[assignment]
    frame_boxes = scene["frame_boxes"]  # type: ignore[assignment]
    if len(frames) < 2:
        errors.append(f"expected at least two rectangular outline frames, found {len(frames)}")
    if len(shapes) < 2:
        errors.append(f"expected at least two non-frame objects, found {len(shapes)}")

    for index in range(1, len(frame_boxes)):
        if not _strictly_contains(frame_boxes[index - 1], frame_boxes[index], blank_gap=False):
            errors.append("rectangular frames must form one strictly nested chain")
            break

    depths: list[int] = []
    for record in shapes:
        cells = record["cells"]  # type: ignore[index]
        depth = record["depth"]  # type: ignore[index]
        depths.append(depth)
        for r, c in cells:
            if _cell_depth(r, c, frame_boxes) != depth:
                errors.append("a non-frame object crosses a frame boundary")
                return errors
    if len(depths) >= 2 and len(set(depths)) < 2:
        errors.append("non-frame objects must witness at least two enclosure depths")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(scene["frames"]),  # type: ignore[arg-type]
        "n_shapes": len(scene["shapes"]),  # type: ignore[arg-type]
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python audit mirror; the canonical Racket rule remains authoritative."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for record in scene["shapes"]:  # type: ignore[union-attr]
        color = _DEPTH_COLOR.get(record["depth"], 1)  # type: ignore[index]
        for r, c in record["cells"]:  # type: ignore[index]
            out[r][c] = color
    return out


def _draw_frame(
    grid: list[list[int]],
    box: tuple[int, int, int, int],
    color: int,
) -> None:
    for r, c in _outline_cells(box):
        grid[r][c] = color


def _split_shrink(rng, total: int) -> tuple[int, int]:
    """Split total shrink between two sides, keeping >=2 cells per side."""
    first = rng.randint(2, total - 2)
    return first, total - first


def _random_frame_chain(
    rng,
    h: int,
    w: int,
    n_frames: int,
) -> list[tuple[int, int, int, int]]:
    minimum_outer = 3 + 4 * (n_frames - 1)
    if h < minimum_outer + 2 or w < minimum_outer + 2:
        raise ValueError(
            f"grid {h}x{w} is too small for {n_frames} nested frames with outside support"
        )

    # Keep a one-cell exterior on every side so depth-zero witnesses are legal.
    outer_h = rng.randint(minimum_outer, h - 2)
    outer_w = rng.randint(minimum_outer, w - 2)
    r1 = rng.randint(1, h - outer_h - 1)
    c1 = rng.randint(1, w - outer_w - 1)
    boxes = [(r1, c1, r1 + outer_h - 1, c1 + outer_w - 1)]

    for level in range(1, n_frames):
        pr1, pc1, pr2, pc2 = boxes[-1]
        prev_h = pr2 - pr1 + 1
        prev_w = pc2 - pc1 + 1
        remaining = n_frames - level
        min_h = 3 + 4 * (remaining - 1)
        min_w = 3 + 4 * (remaining - 1)
        next_h = rng.randint(min_h, min(prev_h - 4, min_h + 2))
        next_w = rng.randint(min_w, min(prev_w - 4, min_w + 2))
        top, bottom = _split_shrink(rng, prev_h - next_h)
        left, right = _split_shrink(rng, prev_w - next_w)
        boxes.append((pr1 + top, pc1 + left, pr2 - bottom, pc2 - right))
    return boxes


def _legal_cells_by_depth(
    grid: list[list[int]],
    boxes: list[tuple[int, int, int, int]],
) -> dict[int, list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    by_depth = {depth: [] for depth in range(len(boxes) + 1)}
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            by_depth[_cell_depth(r, c, boxes)].append((r, c))
    return by_depth


def _target_depths(rng, n_frames: int, n_shapes: int) -> list[int]:
    if n_shapes >= n_frames + 1:
        depths = list(range(n_frames + 1))
    else:
        depths = list(range(n_frames - n_shapes + 1, n_frames + 1))
    # First extra repeats depth 1, creating same-depth objects with different
    # colors while the first two mandatory depths share an input color.
    if len(depths) < n_shapes:
        depths.append(1)
    while len(depths) < n_shapes:
        depths.append(rng.randint(0, n_frames))
    return depths


def _shape_colors(rng, frame_colors: list[int], depths: list[int]) -> list[int]:
    available = [color for color in _COLORS if color not in frame_colors]
    palette_n = min(max(2, min(3, len(set(depths)))), len(available))
    palette = rng.sample(available, palette_n)
    colors = [palette[index % palette_n] for index in range(len(depths))]
    if len(colors) >= 2:
        colors[1] = colors[0]  # same input color at two different depths
    if len(colors) > len(set(range(max(depths) + 1))):
        colors[len(set(range(max(depths) + 1)))] = palette[1]
    return colors


def _grow_shape(
    rng,
    start: tuple[int, int],
    legal: set[tuple[int, int]],
    blocked: set[tuple[int, int]],
    desired_size: int,
) -> list[tuple[int, int]]:
    cells = [start]
    chosen = {start}
    while len(cells) < desired_size:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _NEIGHBORS4
                if (r + dr, c + dc) in legal
                and (r + dr, c + dc) not in blocked
                and (r + dr, c + dc) not in chosen
            }
        )
        if not frontier:
            break
        cell = rng.choice(frontier)
        chosen.add(cell)
        cells.append(cell)
    return cells


def _place_shapes(
    rng,
    grid: list[list[int]],
    boxes: list[tuple[int, int, int, int]],
    depths: list[int],
    colors: list[int],
) -> bool:
    candidates = _legal_cells_by_depth(grid, boxes)
    required = Counter(depths)
    if any(len(candidates[depth]) < count for depth, count in required.items()):
        return False

    blocked: set[tuple[int, int]] = set()
    placements: list[list[tuple[int, int]] | None] = [None] * len(depths)
    order = sorted(range(len(depths)), key=lambda index: (len(candidates[depths[index]]), -depths[index]))
    for index in order:
        depth = depths[index]
        available = [cell for cell in candidates[depth] if cell not in blocked]
        if not available:
            return False
        start = rng.choice(available)
        desired = 1 + ((index + depth) % 4)
        cells = _grow_shape(rng, start, set(candidates[depth]), blocked, desired)
        placements[index] = cells
        for r, c in cells:
            blocked.add((r, c))
            blocked.update((r + dr, c + dc) for dr, dc in _NEIGHBORS8)

    for index, cells in enumerate(placements):
        assert cells is not None
        for r, c in cells:
            grid[r][c] = colors[index]
    return True


def _draw_axis_int(ctx, label: str, valid: tuple[int, int], default: tuple[int, int], overrides) -> int:
    bounds = valid if overrides.get(label) is not None else default
    return ctx.draw_int(label, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    explicit_dims = [
        int(overrides[name])
        for name in ("grid_h", "grid_w")
        if overrides.get(name) is not None
    ]
    max_frames = 4
    if explicit_dims:
        smallest = min(explicit_dims)
        max_frames = 2 if smallest < 13 else 3 if smallest < 17 else 4
    if overrides.get("n_frames") is not None:
        n_frames = ctx.draw_int("n_frames", 2, 4)
    else:
        lo, hi = {"easy": (2, 2), "medium": (2, 3), "hard": (3, 4)}[band]
        hi = min(hi, max_frames)
        lo = min(lo, hi)
        n_frames = ctx.draw_int("n_frames", lo, hi)

    if overrides.get("n_shapes") is not None:
        n_shapes = ctx.draw_int("n_shapes", 4, 8)
    else:
        lo = min(8, n_frames + 2)
        hi = min(8, lo + ({"easy": 0, "medium": 1, "hard": 2}[band]))
        n_shapes = ctx.draw_int("n_shapes", lo, hi)

    minimum_dim = max(11, 5 + 4 * (n_frames - 1))
    if n_shapes >= 7:
        minimum_dim = max(minimum_dim, 15)
    default_hi = {"easy": 12, "medium": 18, "hard": 24}[band]
    default_lo = {"easy": 11, "medium": 13, "hard": 17}[band]
    dim_default = (max(default_lo, minimum_dim), max(default_hi, minimum_dim))
    h = _draw_axis_int(ctx, "grid_h", (11, 24), dim_default, overrides)
    w = _draw_axis_int(ctx, "grid_w", (11, 24), dim_default, overrides)

    required_outer = 3 + 4 * (n_frames - 1)
    if h < required_outer + 2 or w < required_outer + 2:
        raise ValueError(
            "incompatible overrides: grid dimensions must leave an exterior "
            f"margin around {n_frames} nested frames (need at least {required_outer + 2})"
        )

    rng = ctx.draw_rng("layout")
    for _attempt in range(96):
        grid = full_grid(h, w, 0)
        boxes = _random_frame_chain(rng, h, w, n_frames)
        frame_colors = rng.sample(_COLORS, n_frames)
        for box, color in zip(boxes, frame_colors):
            _draw_frame(grid, box, color)

        depths = _target_depths(rng, n_frames, n_shapes)
        colors = _shape_colors(rng, frame_colors, depths)
        if not _place_shapes(rng, grid, boxes, depths, colors):
            continue
        errors = self_check(grid)
        if errors:
            continue
        return grid
    raise ValueError(
        "incompatible overrides: unable to place the requested number of "
        "separated depth witnesses in the requested grid"
    )
