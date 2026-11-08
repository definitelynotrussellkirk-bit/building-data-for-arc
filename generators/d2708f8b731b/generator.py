"""Generator for arc_puzzle_bank_21_set4:S4_H7 — match targets via a legend.

The blank column separates a left legend from neutral target objects.  Every
left neutral prototype has one colored swatch to its right.  Each neutral
object on the right is recolored with the swatch belonging to the prototype
whose normalized shape matches it.

The generator deliberately breaks row-order, object-size, and fixed-position
shortcuts: prototypes in one episode have equal cell count but different
geometry, target reading order is non-identity, and some episodes repeat one
of the target shapes.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2708f8b731b"
TASK_ID = "d2708f8b731b"
VERSION = "3.0.0"
RULE_HASH = "a1f334053a9e"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Use the left prototype-to-swatch legend to recolor every shape-matching "
    "neutral target on the right of the central blank separator."
)

INVARIANTS = [
    "the nearest-to-center all-zero column separates nonzero content on both sides",
    "each left color-1 prototype has exactly one nearby non-0/non-1 swatch",
    "left prototype normalized shapes and swatch colors are pairwise distinct",
    "every right color-1 component matches exactly one prototype shape",
    "every prototype shape occurs at least once on the right",
    "right-side inputs contain no answer colors before the rule is applied",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed rng 12..20",
        "valid": "12..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed rng 16..24",
        "valid": "16..24",
    },
    "n_shapes": {
        "type": "int",
        "default": "difficulty-skewed rng 2..4",
        "valid": "2..4",
    },
    "repeat_target": {
        "type": "bool",
        "default": "rng false|true",
        "valid": "false|true",
    },
}

# Each bank contains connected, normalized shapes with the same cell count.
# Equal-size competing prototypes make cell-count matching insufficient, while
# choosing a different bank per episode still varies absolute object size.
_SHAPES_BY_SIZE: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 2), (1, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    ),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SWATCH_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)


def _paint(grid: list[list[int]], top: int, left: int,
           cells: tuple[tuple[int, int], ...], color: int) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _shape_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _normalize(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    out: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    component.append(nxt)
        out.append(sorted(component))
    return sorted(out, key=lambda cells: min(cells))


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _choose_separator(grid: list[list[int]]) -> int | None:
    h, w = len(grid), len(grid[0])
    candidates = []
    for c in range(w):
        if not all(grid[r][c] == 0 for r in range(h)):
            continue
        has_left = any(grid[r][cc] != 0 for r in range(h) for cc in range(c))
        has_right = any(
            grid[r][cc] != 0
            for r in range(h)
            for cc in range(c + 1, w)
        )
        if has_left and has_right:
            candidates.append(c)
    if not candidates:
        return None
    return min(candidates, key=lambda c: (abs(2 * c - w), c))


def _analyze_grid(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Parse the exact lesson grammar shared by self_check and observability."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a non-empty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {}, ["grid must be rectangular and non-empty"]
    if any(
        not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
        for row in grid
        for v in row
    ):
        return {}, ["grid contains a non-ARC color"]

    h = len(grid)
    sep = _choose_separator(grid)
    if sep is None:
        return {}, ["no all-zero separator with nonzero content on both sides"]

    neutral_components = _components(grid, 1)
    left = [cells for cells in neutral_components if max(c for _, c in cells) < sep]
    right = [cells for cells in neutral_components if min(c for _, c in cells) > sep]
    crossing = [
        cells
        for cells in neutral_components
        if cells not in left and cells not in right
    ]
    errors: list[str] = []
    if crossing:
        errors.append("a neutral component crosses or occupies the separator")
    if len(left) < 2:
        errors.append("need at least two left prototype components")
    if len(right) < len(left):
        errors.append("need at least one right target for every prototype")

    mapping: dict[tuple[tuple[int, int], ...], int] = {}
    swatch_cells: set[tuple[int, int]] = set()
    prototype_records = []
    for cells in left:
        r1, _c1, r2, c2 = _bbox(cells)
        hits = [
            (r, c, grid[r][c])
            for r in range(max(0, r1 - 1), min(h, r2 + 2))
            for c in range(c2 + 1, sep)
            if grid[r][c] not in (0, 1)
        ]
        shape = _normalize(cells)
        if len(hits) != 1:
            errors.append(
                f"prototype at {_bbox(cells)} has {len(hits)} swatches; expected exactly one"
            )
            continue
        sr, sc, swatch = hits[0]
        if shape in mapping:
            errors.append("left prototype shapes are not unique")
        else:
            mapping[shape] = swatch
        swatch_cells.add((sr, sc))
        prototype_records.append(
            {
                "bbox": _bbox(cells),
                "cells": tuple(cells),
                "shape": shape,
                "size": len(cells),
                "swatch": swatch,
                "swatch_cell": (sr, sc),
            }
        )

    all_left_answer_cells = {
        (r, c)
        for r in range(h)
        for c in range(sep)
        if grid[r][c] not in (0, 1)
    }
    if all_left_answer_cells != swatch_cells:
        errors.append("left side contains answer-colored cells outside prototype swatches")
    if any(grid[r][c] not in (0, 1) for r in range(h) for c in range(sep + 1, w)):
        errors.append("right side leaks answer colors before transformation")
    swatches = [record["swatch"] for record in prototype_records]
    if len(swatches) != len(set(swatches)):
        errors.append("prototype swatch colors are not distinct")

    target_records = []
    usage = {shape: 0 for shape in mapping}
    for cells in right:
        shape = _normalize(cells)
        if shape not in mapping:
            errors.append(f"right target at {_bbox(cells)} has no matching prototype")
            swatch = None
        else:
            usage[shape] += 1
            swatch = mapping[shape]
        target_records.append(
            {
                "bbox": _bbox(cells),
                "cells": tuple(cells),
                "shape": shape,
                "size": len(cells),
                "mapped_color": swatch,
            }
        )
    missing = [shape for shape, count in usage.items() if count == 0]
    if missing:
        errors.append(f"{len(missing)} prototype shape(s) are unused on the right")

    shape_to_rank = {
        record["shape"]: rank
        for rank, record in enumerate(sorted(prototype_records, key=lambda x: x["bbox"]))
    }
    target_order = [
        shape_to_rank.get(record["shape"], -1)
        for record in sorted(target_records, key=lambda x: x["bbox"])
    ]
    analysis = {
        "grid_h": h,
        "grid_w": w,
        "separator_col": sep,
        "n_shapes": len(left),
        "n_targets": len(right),
        "repeat_target": len(right) > len(left),
        "prototype_records": prototype_records,
        "target_records": target_records,
        "target_shape_order": target_order,
        "swatch_colors": swatches,
        "shape_sizes": sorted({record["size"] for record in prototype_records}),
        "all_targets_mapped": all(record["mapped_color"] is not None for record in target_records),
    }
    return analysis, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding lessons, not just invalid grids."""
    _analysis, errors = _analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover exact semantic axes from the returned grid."""
    analysis, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "n_shapes": analysis["n_shapes"],
        "repeat_target": analysis["repeat_target"],
    }


def task_observables(grid) -> dict[str, Any]:
    """Task-linked observables used by focused tests and review censuses."""
    analysis, errors = _analyze_grid(grid)
    return {"valid": not errors, "errors": errors, **analysis}


def _place_right_targets(
    grid: list[list[int]],
    shapes: list[tuple[tuple[int, int], ...]],
    assignments: list[int],
    sep: int,
    rng,
) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    occupied: set[tuple[int, int]] = set()
    placements: list[tuple[int, int, int]] = []

    # Randomized greedy packing is ample for at most five <=2x3 objects in a
    # minimum 12x7 right panel. Restart the whole layout if a late object jams.
    for _layout_attempt in range(200):
        occupied.clear()
        placements.clear()
        success = True
        for shape_index in assignments:
            shape = shapes[shape_index]
            sh, sw = _shape_dims(shape)
            candidates = [
                (top, left)
                for top in range(0, h - sh + 1)
                for left in range(sep + 1, w - sw + 1)
            ]
            rng.shuffle(candidates)
            chosen = None
            for top, left in candidates:
                cells = {(top + dr, left + dc) for dr, dc in shape}
                if cells & occupied:
                    continue
                if any(
                    (r + dr, c + dc) in occupied
                    for r, c in cells
                    for dr, dc in _CARDINAL
                ):
                    continue
                chosen = (top, left, cells)
                break
            if chosen is None:
                success = False
                break
            top, left, cells = chosen
            occupied.update(cells)
            placements.append((top, left, shape_index))
        if not success:
            continue
        reading_order = [idx for _r, _c, idx in sorted(placements)]
        canonical_order = list(range(len(shapes)))
        if reading_order[: len(shapes)] == canonical_order:
            continue
        for top, left, shape_index in placements:
            _paint(grid, top, left, shapes[shape_index], 1)
        return list(placements)
    raise ValueError("could not place separated, non-row-aligned right targets")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 12, 20)
    w = ctx.draw_int_diff("grid_w", 16, 24)
    n_shapes = ctx.draw_int_diff("n_shapes", 2, 4)
    repeat_target = ctx.draw_choice("repeat_target", (False, True))
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    sep = w // 2
    band_heights = [
        (i + 1) * h // n_shapes - i * h // n_shapes
        for i in range(n_shapes)
    ]
    max_shape_h = min(band_heights) - 1
    eligible_sizes = [
        size
        for size, bank in _SHAPES_BY_SIZE.items()
        if sum(_shape_dims(shape)[0] <= max_shape_h for shape in bank) >= n_shapes
    ]
    if not eligible_sizes:
        raise ValueError(
            f"grid_h={h} cannot hold n_shapes={n_shapes} separated prototypes"
        )
    shape_size = rng.choice(eligible_sizes)
    shape_pool = []
    seen_shapes = set()
    for raw_shape in _SHAPES_BY_SIZE[shape_size]:
        shape = tuple(sorted(raw_shape))
        if _shape_dims(shape)[0] > max_shape_h or shape in seen_shapes:
            continue
        seen_shapes.add(shape)
        shape_pool.append(shape)
    if len(shape_pool) < n_shapes:
        raise ValueError(
            f"shape bank size={shape_size} has only {len(shape_pool)} usable distinct shapes"
        )
    shapes = list(rng.sample(shape_pool, n_shapes))
    colors = list(rng.sample(_SWATCH_COLORS, n_shapes))

    # Left legend: one prototype per vertical band, with a blank row below each
    # band placement. This keeps each swatch's canonical scan corridor isolated.
    for i, (shape, color) in enumerate(zip(shapes, colors)):
        start = i * h // n_shapes
        end = (i + 1) * h // n_shapes
        sh, sw = _shape_dims(shape)
        top = rng.randint(start, end - sh - 1)
        blank_gap = rng.choice((1, 2))
        max_left = sep - sw - blank_gap - 1
        if max_left < 0:
            raise ValueError(
                f"grid_w={w} cannot hold prototype width={sw} and swatch gap={blank_gap}"
            )
        left = rng.randint(0, max_left)
        _paint(grid, top, left, shape, 1)
        swatch_col = left + sw + blank_gap
        swatch_row = top + rng.randrange(sh)
        grid[swatch_row][swatch_col] = color

    assignments = list(range(n_shapes))
    if repeat_target:
        assignments.append(rng.randrange(n_shapes))
    # Make target order deliberately independent of prototype reading order.
    for _ in range(20):
        rng.shuffle(assignments)
        if assignments[:n_shapes] != list(range(n_shapes)):
            break
    if assignments[:n_shapes] == list(range(n_shapes)):
        assignments = assignments[1:] + assignments[:1]
    _place_right_targets(grid, shapes, assignments, sep, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid
