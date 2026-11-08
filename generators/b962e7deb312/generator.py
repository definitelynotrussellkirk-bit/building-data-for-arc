"""Generator for ``largest_component_crop`` (task b962e7deb312).

The input contains two or three separated, uniformly colored, nonzero
4-connected components.  Exactly one component is largest by cell count.  The
canonical rule crops the input to that component's bounding box.

Version 3.2.0 repairs the previous teaching distribution: the old generator
painted the selected component with random per-cell colors, so color-aware
object diagnostics saw 6--15 fragments instead of the canonical 2--3 objects.
It also exposed dead aliases and did not structurally validate the lesson.
The five-example schedule now contains explicit width/height rival refuters,
and unknown override names are rejected instead of being silently ignored.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b962e7deb312"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "84f1bd44bdef"

SUMMARY = (
    "A zero-background 8-11 by 11-13 grid contains exactly two or three "
    "spatially separated, uniformly colored 4-connected components. Component "
    "colors and sizes are distinct, and one component is uniquely largest "
    "(6, 8, or 12 cells). The largest component may be a filled rectangle or "
    "an irregular/hollow polyomino and appears in varied positions and colors. "
    "Select the component with the greatest cell count and return the exact "
    "input subgrid spanning its bounding box. Smaller components lie outside "
    "that box and disappear from the crop."
)

INVARIANTS = [
    "exactly 2 or 3 nonzero 4-connected components",
    "each component is monochromatic and component colors are distinct",
    "component sizes are distinct; the unique largest has 6, 8, or 12 cells",
    "smaller-component bounding boxes do not intersect the largest bbox",
    "the largest bbox is a strict subrectangle of the input",
]

# The five observed canonical (height, width, palette-size) profiles.  Default
# sample_index scheduling cycles through all of them, while explicit overrides
# remain available over the full declared boundary ranges.
CANONICAL_PROFILES = (
    (10, 12, 3),
    (9, 11, 4),
    (11, 13, 3),
    (8, 12, 3),
    (10, 13, 4),
)
CANONICAL_LARGEST_SIZES = (8, 6, 8, 12, 8)
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.95

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index cycles canonical 8..11 profiles",
        "valid": "8..11",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index cycles canonical 11..13 profiles",
        "valid": "11..13",
    },
    "n_blobs": {
        "type": "int",
        "default": "sample_index cycles canonical 2..3 profiles",
        "valid": "2..3",
    },
    "largest_size": {
        "type": "int",
        "default": "sample_index cycles canonical sizes 6|8|12",
        "valid": "6|8|12",
    },
}

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

_FILLED_SHAPES = {
    6: {(r, c) for r in range(2) for c in range(3)},
    8: {(r, c) for r in range(2) for c in range(4)},
    12: {(r, c) for r in range(3) for c in range(4)},
}

_HOLLOW_SHAPES = {
    6: {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)},
    8: {
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    },
    12: {
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0),                         (1, 3),
        (2, 0),                         (2, 3),
        (3, 0), (3, 1), (3, 2), (3, 3),
    },
}

_SMALL_SHAPES = {
    4: (
        {(0, 0), (0, 1), (1, 0), (1, 1)},
        {(0, 0), (1, 0), (2, 0), (2, 1)},
        {(0, 0), (0, 1), (0, 2), (1, 1)},
    ),
    5: (
        {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)},
        {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)},
        {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)},
    ),
    6: (
        _HOLLOW_SHAPES[6],
        _FILLED_SHAPES[6],
        {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)},
    ),
}


def _normalize_grid(grid) -> list[list[int]]:
    """Return a list-of-lists view, accepting canonical row strings."""
    if not isinstance(grid, (list, tuple)):
        return []
    normalized: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                normalized.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            normalized.append(list(row))
        else:
            return []
    return normalized


def _components(grid) -> list[dict]:
    """Extract nonzero 4-connected components from a normalized grid."""
    g = _normalize_grid(grid)
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        return []
    h, w = len(g), len(g[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and g[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            colors = {g[rr][cc] for rr, cc in cells}
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "colors": frozenset(colors),
                }
            )
    return result


def _crop(grid, component: dict) -> list[list[int]]:
    g = _normalize_grid(grid)
    r1, c1, r2, c2 = component["bbox"]
    return [row[c1 : c2 + 1] for row in g[r1 : r2 + 1]]


def rule_mirror(grid) -> list[list[int]]:
    """Small Python mirror used only by focused tests and semantic hooks."""
    components = _components(grid)
    if not components:
        raise ValueError("no nonzero component")
    chosen = max(components, key=lambda component: component["size"])
    return _crop(grid, chosen)


def _normalize_shape(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return {(r - min_r, c - min_c) for r, c in cells}


def _transform_shape(
    cells: set[tuple[int, int]], transform_code: int
) -> set[tuple[int, int]]:
    """Apply one of eight D4 transforms and normalize the result."""
    transformed = set(cells)
    if transform_code >= 4:
        transformed = {(r, -c) for r, c in transformed}
    for _ in range(transform_code % 4):
        transformed = {(c, -r) for r, c in transformed}
    return _normalize_shape(transformed)


def _shape_dims(cells: set[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _random_shape(size: int, rng) -> set[tuple[int, int]]:
    """Grow a compact random polyomino with many output morphologies."""
    max_dim = 4 if size <= 8 else 5
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _NEIGHBORS4
                if (r + dr, c + dc) not in cells
            }
            choices = []
            for cell in frontier:
                candidate = _normalize_shape(cells | {cell})
                bh, bw = _shape_dims(candidate)
                if bh <= max_dim and bw <= max_dim:
                    choices.append(cell)
            if not choices:
                break
            cells.add(rng.choice(choices))
        if len(cells) == size:
            return _normalize_shape(cells)
    raise ValueError(f"could not grow a compact {size}-cell polyomino")


def _wide_small_shape(size: int) -> set[tuple[int, int]]:
    """Return a canonical small shape with maximal horizontal span."""
    if size == 4:
        return set(_SMALL_SHAPES[4][2])
    if size == 5:
        return set(_SMALL_SHAPES[5][0])
    if size == 6:
        return _transform_shape(set(_SMALL_SHAPES[6][2]), 1)
    raise ValueError(f"no wide small-shape witness for size {size}")


def _tall_small_shape(size: int) -> set[tuple[int, int]]:
    """Return a canonical small shape with maximal vertical span."""
    if size == 4:
        return _transform_shape(set(_SMALL_SHAPES[4][2]), 1)
    if size == 5:
        return set(_SMALL_SHAPES[5][0])
    if size == 6:
        return set(_SMALL_SHAPES[6][2])
    raise ValueError(f"no tall small-shape witness for size {size}")


def _draw_axis_int(ctx, overrides, label: str, scheduled: int, lo: int, hi: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_axis_choice(ctx, overrides, label: str, scheduled: int, options) -> int:
    if overrides.get(label) is not None:
        return int(ctx.draw_choice(label, options))
    return int(ctx.draw_choice(label, (scheduled,)))


def _anchor_target(sample_index: int) -> tuple[float, float]:
    # A five-sample curriculum uses all four corners plus a central control.
    # The central control also carries the positional/color rival witnesses.
    return (
        (0.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (0.5, 0.5),
    )[sample_index % EXAMPLES_NEEDED]


def _large_position(h: int, w: int, shape, sample_index: int, rng) -> tuple[int, int]:
    bh, bw = _shape_dims(shape)
    max_r, max_c = h - bh, w - bw
    tr, tc = _anchor_target(sample_index)
    candidates = [(r, c) for r in range(max_r + 1) for c in range(max_c + 1)]
    rng.shuffle(candidates)
    candidates.sort(
        key=lambda pos: (
            abs((pos[0] / max(1, max_r)) - tr)
            + abs((pos[1] / max(1, max_c)) - tc)
        )
    )
    if sample_index % EXAMPLES_NEEDED == 4:
        return candidates[0]
    return candidates[rng.randrange(min(4, len(candidates)))]


def _absolute(shape, top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _halo(cells: set[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    result = set(cells)
    for r, c in cells:
        for dr, dc in _NEIGHBORS8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                result.add((nr, nc))
    return result


def _bbox_of(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rectangles_intersect(left, right) -> bool:
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return not (lr2 < rr1 or rr2 < lr1 or lc2 < rc1 or rc2 < lc1)


def _place_small_shape(
    shape,
    *,
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    largest_bbox,
    rng,
    anchor: tuple[float, float] | None = None,
) -> set[tuple[int, int]] | None:
    bh, bw = _shape_dims(shape)
    candidates = [
        (top, left)
        for top in range(h - bh + 1)
        for left in range(w - bw + 1)
    ]
    rng.shuffle(candidates)
    if anchor is not None:
        max_r, max_c = h - bh, w - bw
        ar, ac = anchor
        candidates.sort(
            key=lambda pos: (
                abs((pos[0] / max(1, max_r)) - ar)
                + abs((pos[1] / max(1, max_c)) - ac)
            )
        )
    for top, left in candidates:
        cells = _absolute(shape, top, left)
        if cells & forbidden:
            continue
        if _rectangles_intersect(_bbox_of(cells), largest_bbox):
            continue
        return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, fresh, structurally valid input grid."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = CANONICAL_PROFILES[sample_index % len(CANONICAL_PROFILES)]
    scheduled_h, scheduled_w, scheduled_palette = profile
    scheduled_n = scheduled_palette - 1
    h = _draw_axis_int(ctx, overrides, "grid_h", scheduled_h, 8, 11)
    w = _draw_axis_int(ctx, overrides, "grid_w", scheduled_w, 11, 13)
    n_blobs = _draw_axis_int(ctx, overrides, "n_blobs", scheduled_n, 2, 3)
    scheduled_largest = CANONICAL_LARGEST_SIZES[
        sample_index % len(CANONICAL_LARGEST_SIZES)
    ]
    largest_size = _draw_axis_choice(
        ctx,
        overrides,
        "largest_size",
        scheduled_largest,
        (6, 8, 12),
    )

    band_label = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    rng = ctx.draw_rng(f"layout_{band_label}")
    # Every five consecutive samples contain one explicit width refuter, one
    # height refuter, and one three-object central control.  The central control
    # makes the target neither a positional extreme nor a color extreme.
    lesson_role = sample_index % EXAMPLES_NEEDED
    if lesson_role == 0:
        base_large = _FILLED_SHAPES[largest_size]
        large_shape = _transform_shape(base_large, rng.randrange(8))
    elif lesson_role == 1:  # narrow target; a smaller component is wider
        base_large = _FILLED_SHAPES[largest_size]
        large_shape = _transform_shape(base_large, 1)
    elif lesson_role == 2:
        base_large = _HOLLOW_SHAPES[largest_size]
        large_shape = _transform_shape(base_large, rng.randrange(8))
    elif lesson_role == 3:  # short target; a smaller component is taller
        base_large = _FILLED_SHAPES[largest_size]
        large_shape = _transform_shape(base_large, 0)
    else:  # central three-object control
        base_large = _random_shape(largest_size, rng)
        large_shape = _transform_shape(base_large, rng.randrange(8))
    large_top, large_left = _large_position(
        h, w, large_shape, sample_index, rng
    )
    large_cells = _absolute(large_shape, large_top, large_left)
    largest_bbox = _bbox_of(large_cells)

    available_sizes = [size for size in (4, 5, 6) if size < largest_size]
    if len(available_sizes) < n_blobs - 1:
        raise ValueError(
            f"largest_size={largest_size} cannot support {n_blobs} distinct sizes"
        )
    small_sizes = sorted(available_sizes, reverse=True)[: n_blobs - 1]

    components = [large_cells]
    forbidden = _halo(large_cells, h, w)
    for index, size in enumerate(small_sizes):
        if index == 0 and lesson_role == 1:
            banks = [_wide_small_shape(size)]
        elif index == 0 and lesson_role == 3:
            banks = [_tall_small_shape(size)]
        else:
            banks = list(_SMALL_SHAPES[size])
            offset = (sample_index + index) % len(banks)
            banks = banks[offset:] + banks[:offset]
        placed = None
        for base_shape in banks:
            if index == 0 and lesson_role in (1, 3):
                shape = set(base_shape)
            else:
                shape = _transform_shape(base_shape, rng.randrange(8))
            central_anchor = None
            if lesson_role == 4:
                central_anchor = (0.0, 0.0) if index == 0 else (1.0, 1.0)
            placed = _place_small_shape(
                shape,
                h=h,
                w=w,
                forbidden=forbidden,
                largest_bbox=largest_bbox,
                rng=rng,
                anchor=central_anchor,
            )
            if placed is not None:
                break
        if placed is None:
            raise ValueError(
                f"could not place small component {index + 1}/{len(small_sizes)}"
            )
        components.append(placed)
        forbidden |= _halo(placed, h, w)

    colors = sorted(rng.sample(range(1, 10), n_blobs))
    largest_rank = 1 if lesson_role == 4 and n_blobs == 3 else sample_index % n_blobs
    largest_color = colors.pop(largest_rank)
    rng.shuffle(colors)
    component_colors = [largest_color, *colors]

    grid = full_grid(h, w, 0)
    for cells, color in zip(components, component_colors):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact semantic axis from the returned grid."""
    g = _normalize_grid(grid)
    components = _components(g)
    return {
        "grid_h": len(g),
        "grid_w": len(g[0]) if g else 0,
        "n_blobs": len(components),
        "largest_size": max((component["size"] for component in components), default=0),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, not merely invalid palettes."""
    g = _normalize_grid(grid)
    if not g or not g[0]:
        return ["empty grid"]
    w = len(g[0])
    if any(len(row) != w for row in g):
        return ["ragged grid"]
    h = len(g)
    errors: list[str] = []
    if not (8 <= h <= 11 and 11 <= w <= 13):
        errors.append(f"grid dimensions {h}x{w} outside 8..11 by 11..13")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9)
        for row in g
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    components = _components(g)
    if len(components) not in (2, 3):
        errors.append(f"expected 2 or 3 nonzero components, found {len(components)}")
        return errors

    colors = []
    for index, component in enumerate(components):
        if len(component["colors"]) != 1:
            errors.append(f"component {index} is not monochromatic")
        else:
            colors.append(next(iter(component["colors"])))
        if component["size"] < 4:
            errors.append(f"component {index} has only {component['size']} cells")
    if len(colors) == len(components) and len(set(colors)) != len(colors):
        errors.append("component colors are not distinct")

    sizes = [component["size"] for component in components]
    if len(set(sizes)) != len(sizes):
        errors.append(f"component sizes are not distinct: {sorted(sizes)}")
        return errors
    largest = max(components, key=lambda component: component["size"])
    if largest["size"] not in (6, 8, 12):
        errors.append(f"largest component size {largest['size']} is not 6, 8, or 12")
    r1, c1, r2, c2 = largest["bbox"]
    if r1 == 0 and c1 == 0 and r2 == h - 1 and c2 == w - 1:
        errors.append("largest bbox is the whole input")
    for component in components:
        if component is largest:
            continue
        if _rectangles_intersect(component["bbox"], largest["bbox"]):
            errors.append("a smaller component bbox intersects the largest bbox")
    expected = _crop(g, largest)
    if not expected or expected == g:
        errors.append("largest-component crop is empty or identity")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the task's canonical structural/profile manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    g = _normalize_grid(grid)
    palette_size = len({value for row in g for value in row})
    profile = (len(g), len(g[0]), palette_size)
    if profile not in CANONICAL_PROFILES:
        return [f"profile {profile} is outside the five canonical profiles"]
    return []


def _largest_component(grid) -> dict | None:
    components = _components(grid)
    return max(components, key=lambda component: component["size"], default=None)


def _largest_in_top_half(grid) -> bool:
    component = _largest_component(grid)
    if component is None:
        return False
    r1, _, r2, _ = component["bbox"]
    return (r1 + r2) < len(_normalize_grid(grid)) - 1


def _largest_in_bottom_half(grid) -> bool:
    component = _largest_component(grid)
    if component is None:
        return False
    r1, _, r2, _ = component["bbox"]
    return (r1 + r2) > len(_normalize_grid(grid)) - 1


def _largest_not_topmost(grid) -> bool:
    components = _components(grid)
    if not components:
        return False
    largest = max(components, key=lambda component: component["size"])
    return largest["bbox"][0] > min(component["bbox"][0] for component in components)


def _largest_not_leftmost(grid) -> bool:
    components = _components(grid)
    if not components:
        return False
    largest = max(components, key=lambda component: component["size"])
    return largest["bbox"][1] > min(component["bbox"][1] for component in components)


def _largest_low_color(grid) -> bool:
    component = _largest_component(grid)
    return bool(component and next(iter(component["colors"])) <= 4)


def _largest_high_color(grid) -> bool:
    component = _largest_component(grid)
    return bool(component and next(iter(component["colors"])) >= 6)


def _largest_bbox_has_zero(grid) -> bool:
    component = _largest_component(grid)
    return bool(component and any(value == 0 for row in _crop(grid, component) for value in row))


def _largest_bbox_is_filled(grid) -> bool:
    component = _largest_component(grid)
    return bool(component and all(value != 0 for row in _crop(grid, component) for value in row))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "two_components": lambda grid: len(_components(grid)) == 2,
    "three_components": lambda grid: len(_components(grid)) == 3,
    "largest_top_half": _largest_in_top_half,
    "largest_bottom_half": _largest_in_bottom_half,
    "largest_not_topmost": _largest_not_topmost,
    "largest_not_leftmost": _largest_not_leftmost,
    "largest_low_color": _largest_low_color,
    "largest_high_color": _largest_high_color,
    "filled_largest_bbox": _largest_bbox_is_filled,
    "zero_inside_largest_bbox": _largest_bbox_has_zero,
}


def _candidate_components(grid) -> dict[str, dict]:
    components = _components(grid)
    if not components:
        return {}

    def color(component):
        return next(iter(component["colors"])) if len(component["colors"]) == 1 else -1

    def bbox_area(component):
        r1, c1, r2, c2 = component["bbox"]
        return (r2 - r1 + 1) * (c2 - c1 + 1)

    return {
        "smallest": min(components, key=lambda component: component["size"]),
        "topmost": min(components, key=lambda component: (component["bbox"][0], component["bbox"][1])),
        "bottommost": max(components, key=lambda component: (component["bbox"][2], component["bbox"][3])),
        "leftmost": min(components, key=lambda component: (component["bbox"][1], component["bbox"][0])),
        "rightmost": max(components, key=lambda component: (component["bbox"][3], component["bbox"][2])),
        "lowest_color": min(components, key=color),
        "highest_color": max(components, key=color),
        "widest_bbox": max(components, key=lambda component: component["bbox"][3] - component["bbox"][1]),
        "tallest_bbox": max(components, key=lambda component: component["bbox"][2] - component["bbox"][0]),
        "largest_bbox_area": max(components, key=bbox_area),
    }


def _candidate_solver(name: str) -> Callable[[list[list[int]]], list[list[int]]]:
    """Build a pure rival solver for lesson-level identifiability audits."""
    def solve(grid):
        candidates = _candidate_components(grid)
        if name not in candidates:
            raise ValueError(f"candidate {name!r} is unavailable")
        return _crop(grid, candidates[name])

    return solve


LESSON_COMPETITORS = {
    name: _candidate_solver(name)
    for name in (
        "smallest",
        "topmost",
        "bottommost",
        "leftmost",
        "rightmost",
        "lowest_color",
        "highest_color",
        "widest_bbox",
        "tallest_bbox",
        "largest_bbox_area",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits demos but changes the query."""
    if not isinstance(demos, list) or not demos:
        return ["no demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query lacks input/output"]

    rival_names = set(_candidate_components(demos[0]["input"]))
    for demo in demos:
        official = _normalize_grid(demo.get("output"))
        candidates = _candidate_components(demo.get("input"))
        rival_names &= {
            name
            for name, component in candidates.items()
            if _crop(demo["input"], component) == official
        }

    official_query = _normalize_grid(query["output"])
    query_candidates = _candidate_components(query["input"])
    ambiguous = [
        name
        for name in sorted(rival_names)
        if name in query_candidates
        and _crop(query["input"], query_candidates[name]) != official_query
    ]
    if ambiguous:
        return [
            "rival selector(s) fit every demo but change the query: "
            + ", ".join(ambiguous)
        ]
    return []
