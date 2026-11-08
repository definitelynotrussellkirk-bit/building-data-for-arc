"""Generator for ARC task f0d16ecf2012 — independently dock components east.

Color 9 forms a stack of horizontal lanes.  Every 4-connected nonzero,
non-9 component moves east as a rigid object until its next step would hit a
9-wall or the grid boundary.  Components do not block one another: the
canonical rule evaluates each object on a board containing only the walls and
that object.

Every ordinary generated scene contains both a connected asymmetric object and
a lane with multiple diagonally separated components.  Their lane assignments
and orientations vary, and wall-separated lanes may reuse a color.  This makes
three otherwise tempting rule shortcuts observable without teaching fixed
position, orientation, or palette-role correlations.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f0d16ecf2012"
TASK_ID = GENERATOR_ID
RULE_HASH = "4e0031784e59"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "3.1.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Color-9 walls form 2..5 horizontal lanes.  In each lane, every "
    "4-connected colored component slides east independently and rigidly until "
    "its next step would hit the east wall.  Width, lane count, lane height, "
    "colors (including reuse across separated lanes), placements, connected "
    "shape rotations, witness lane roles, and both diagonal orientations vary.  "
    "Every ordinary draw visibly distinguishes full sliding, rigid shape "
    "preservation, and independent component motion."
)

INVARIANTS = [
    "9-walls are the side columns and equally spaced full divider rows",
    "there are 2..5 lanes of height 2..4 and width 9..22",
    "each lane contains one non-wall color and at least one 4-connected component",
    "colors may repeat across wall-separated lanes and every component has east-slide room",
    "ordinary draws contain both witness types with variable lane roles and orientations",
]

# Only exact caller-facing controls recoverable from the returned grid are
# declared.  The previous palette/texture/bias aliases were dead or ambiguous.
AXES = {
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 9..22",
        "valid": "9..22",
    },
    "n_compartments": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 2..5",
        "valid": "2..5",
    },
    "comp_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 2..4",
        "valid": "2..4",
    },
}

_BLOB_COLORS = (2, 3, 4, 5, 6, 7, 8)

# Every shape has a nonuniform east edge, so independently pushing each
# occupied row to the wall distorts it.
_CONNECTED_TEACHING_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
)

_EXTRA_CONNECTED_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} is ragged")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _components(grid: list[list[int]], *, include_walls: bool = False) -> list[dict[str, Any]]:
    """Return row-major, same-color, 4-connected components like Racket objects."""
    h, w = len(grid), len(grid[0])
    visited: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (color == 9 and not include_walls) or (r, c) in visited:
                continue
            queue = deque([(r, c)])
            visited.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in visited
                        and grid[nr][nc] == color
                    ):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": cells})
    return result


def _shift_once(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(r, c + 1) for r, c in cells]


def _can_shift(
    cells: list[tuple[int, int]],
    *,
    h: int,
    w: int,
    static_occupied: set[tuple[int, int]],
) -> bool:
    current = set(cells)
    for r, c in cells:
        destination = (r, c + 1)
        if not (0 <= r < h and 0 <= c + 1 < w):
            return False
        if destination in static_occupied and destination not in current:
            return False
    return True


def _move_component(
    cells: list[tuple[int, int]],
    *,
    h: int,
    w: int,
    walls: set[tuple[int, int]],
    steps: int | None,
) -> list[tuple[int, int]]:
    """Move as the authority does; steps=None means continue to the blocker."""
    original = set(cells)
    static_occupied = walls | original
    current = list(cells)
    moved = 0
    while _can_shift(current, h=h, w=w, static_occupied=static_occupied):
        current = _shift_once(current)
        moved += 1
        if steps is not None and moved >= steps:
            break
    return current


def _paint_moved_objects(
    grid: list[list[int]],
    components: Iterable[dict[str, Any]],
    *,
    steps: int | None,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    out = full_grid(h, w, 0)
    for r, c in walls:
        out[r][c] = 9
    for obj in components:
        moved = _move_component(
            list(obj["cells"]), h=h, w=w, walls=walls, steps=steps
        )
        for r, c in moved:
            out[r][c] = int(obj["color"])
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; the canonical Racket remains authoritative."""
    return _paint_moved_objects(grid, _components(grid), steps=None)


def _rival_one_step(grid: list[list[int]]) -> list[list[int]]:
    return _paint_moved_objects(grid, _components(grid), steps=1)


def _horizontal_runs(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Wrong decomposition used by a row-wise right-alignment shortcut."""
    runs: list[dict[str, Any]] = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            color = row[c]
            if color in (0, 9):
                c += 1
                continue
            start = c
            while c + 1 < len(row) and row[c + 1] == color:
                c += 1
            runs.append({"color": color, "cells": [(r, cc) for cc in range(start, c + 1)]})
            c += 1
    return runs


def _rival_rowwise_right_align(grid: list[list[int]]) -> list[list[int]]:
    return _paint_moved_objects(grid, _horizontal_runs(grid), steps=None)


def _divider_rows(grid: list[list[int]]) -> list[int]:
    return [r for r, row in enumerate(grid) if row and all(value == 9 for value in row)]


def _lane_objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Wrong decomposition: all colored cells in one lane become one object."""
    lane_components: list[dict[str, Any]] = []
    dividers = _divider_rows(grid)
    for top, bottom in zip(dividers, dividers[1:]):
        cells = [
            (r, c)
            for r in range(top + 1, bottom)
            for c, value in enumerate(grid[r])
            if value not in (0, 9)
        ]
        if not cells:
            continue
        color = grid[cells[0][0]][cells[0][1]]
        lane_components.append({"color": color, "cells": cells})
    return lane_components


def _rival_lane_as_one_object(grid: list[list[int]]) -> list[list[int]]:
    return _paint_moved_objects(grid, _lane_objects(grid), steps=None)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    if not 9 <= w <= 22:
        errors.append(f"width must be in 9..22, found {w}")
    if not all(row[0] == 9 and row[-1] == 9 for row in grid):
        errors.append("side walls must be solid color-9 columns")

    dividers = _divider_rows(grid)
    if len(dividers) < 3 or dividers[0] != 0 or dividers[-1] != h - 1:
        errors.append("need top, bottom, and at least one interior full color-9 divider")
        return {"errors": errors, "height": h, "width": w, "dividers": dividers}

    ncomp = len(dividers) - 1
    gaps = [bottom - top - 1 for top, bottom in zip(dividers, dividers[1:])]
    if not 2 <= ncomp <= 5:
        errors.append(f"lane count must be in 2..5, found {ncomp}")
    if len(set(gaps)) != 1:
        errors.append(f"lane heights must be equal, found {gaps}")
        comp_h = None
    else:
        comp_h = gaps[0]
        if not 2 <= comp_h <= 4:
            errors.append(f"lane height must be in 2..4, found {comp_h}")

    divider_set = set(dividers)
    for r, row in enumerate(grid):
        if r in divider_set:
            if any(value != 9 for value in row):
                errors.append(f"divider row {r} is not fully color 9")
            continue
        if any(value == 9 for value in row[1:-1]):
            errors.append(f"lane row {r} contains an undeclared interior wall")

    lane_infos: list[dict[str, Any]] = []
    for top, bottom in zip(dividers, dividers[1:]):
        colored = [
            (r, c, grid[r][c])
            for r in range(top + 1, bottom)
            for c in range(1, w - 1)
            if grid[r][c] not in (0, 9)
        ]
        colors = sorted({color for _, _, color in colored})
        if not colored:
            errors.append(f"lane {top}-{bottom} has no movable component")
            lane_infos.append({"top": top, "bottom": bottom, "colors": colors, "components": []})
            continue
        if len(colors) != 1:
            errors.append(f"lane {top}-{bottom} must contain exactly one color, found {colors}")

        lane_grid = [row[:] for row in grid]
        for r in range(h):
            if not (top < r < bottom):
                for c in range(w):
                    if lane_grid[r][c] != 9:
                        lane_grid[r][c] = 0
        components = [
            obj for obj in _components(lane_grid)
            if any(top < r < bottom for r, _ in obj["cells"])
        ]
        if not components:
            errors.append(f"lane {top}-{bottom} has no 4-connected movable component")
        for obj in components:
            cells = list(obj["cells"])
            walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
            if not _can_shift(cells, h=h, w=w, static_occupied=walls | set(cells)):
                errors.append(f"lane {top}-{bottom} contains a component with no east-slide room")
        lane_infos.append(
            {"top": top, "bottom": bottom, "colors": colors, "components": components}
        )

    if not errors:
        out = rule_mirror(grid)
        if out == grid:
            errors.append("scene hides the rule because the output equals the input")
        input_cells = sum(value not in (0, 9) for row in grid for value in row)
        output_cells = sum(value not in (0, 9) for row in out for value in row)
        if input_cells != output_cells:
            errors.append("independent slides overlap and erase colored cells")

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "dividers": dividers,
        "n_compartments": ncomp,
        "comp_h": comp_h,
        "lanes": lane_infos,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_w": analysis["width"],
        "n_compartments": analysis["n_compartments"],
        "comp_h": analysis["comp_h"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or collision-prone lane-docking scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical 3x(height-3) lane geometry, including split components."""
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    if observed["n_compartments"] != 3:
        errors.append("canonical profile has exactly three lanes")
    if observed["comp_h"] != 3:
        errors.append("canonical profile has lane height three")
    if observed["grid_w"] not in (11, 12, 13):
        errors.append("canonical profile width is one of 11, 12, or 13")
    return errors


def _draw_axis(ctx, label: str, lo: int, hi: int, anchor: tuple[int, ...], canonical_anchor: bool) -> int:
    if label in ctx.overrides:
        return ctx.draw_int(label, lo, hi)
    if canonical_anchor:
        return ctx.draw_choice(label, anchor)
    return ctx.draw_int_diff(label, lo, hi)


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _split_shape(comp_h: int, rng) -> tuple[tuple[int, int], ...]:
    length = 2 if comp_h == 2 else rng.choice((2, 3))
    if rng.choice((False, True)):
        return tuple((index, index) for index in range(length))
    return tuple((index, length - index - 1) for index in range(length))


def _draw_palette(rng, ncomp: int, *, canonical_anchor: bool) -> list[int]:
    """Mix distinct palettes with one safe wall-separated color reuse."""
    if canonical_anchor or rng.random() < 0.5:
        return rng.sample(list(_BLOB_COLORS), ncomp)
    palette = rng.sample(list(_BLOB_COLORS), ncomp - 1)
    palette.append(rng.choice(palette))
    rng.shuffle(palette)
    return palette


def _fit_shape(shape: tuple[tuple[int, int], ...], comp_h: int) -> tuple[tuple[int, int], ...]:
    """Trim optional tall shapes without changing their connectedness."""
    if max(r for r, _ in shape) < comp_h:
        return shape
    return tuple(cell for cell in shape if cell[0] < comp_h)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic teaching input; Racket owns the official output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis(es): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_anchor = not overrides and int(sample_index) % 3 == 0
    w = _draw_axis(ctx, "grid_w", 9, 22, (11, 12, 13), canonical_anchor)
    ncomp = _draw_axis(ctx, "n_compartments", 2, 5, (3,), canonical_anchor)
    comp_h = _draw_axis(ctx, "comp_h", 2, 4, (3,), canonical_anchor)

    h = ncomp * (comp_h + 1) + 1
    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][0] = 9
        grid[r][-1] = 9
    dividers = [index * (comp_h + 1) for index in range(ncomp + 1)]
    for row in dividers:
        for c in range(w):
            grid[row][c] = 9

    palette_rng = ctx.draw_rng("palette")
    layout_rng = ctx.draw_rng("layout")
    palette = _draw_palette(palette_rng, ncomp, canonical_anchor=canonical_anchor)
    connected_lane, split_lane = layout_rng.sample(range(ncomp), 2)

    for lane_index in range(ncomp):
        top = dividers[lane_index] + 1
        if lane_index == connected_lane:
            shape = layout_rng.choice(_CONNECTED_TEACHING_SHAPES)
        elif lane_index == split_lane:
            shape = _split_shape(comp_h, layout_rng)
        elif layout_rng.random() < 0.35:
            shape = _split_shape(comp_h, layout_rng)
        else:
            shape = _fit_shape(layout_rng.choice(_EXTRA_CONNECTED_SHAPES), comp_h)

        sh, sw = _shape_size(shape)
        row_offset = layout_rng.randint(0, comp_h - sh)
        # Interior right edge is w-2.  Keep every component at least two full
        # moves away so one-step motion is never answer-equivalent.
        max_col = w - sw - 3
        if max_col < 1:  # impossible for declared dimensions; loud guard
            raise ValueError(f"shape width {sw} cannot retain two-step room in width {w}")
        col_offset = layout_rng.randint(1, max_col)
        paint_at(grid, top + row_offset, col_offset, shape, palette[lane_index])

    return grid


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    def predicate(grid):
        return not self_check(grid) and rule_mirror(grid) != rival(grid)

    return predicate


SEMANTIC_RIVALS = {
    "move_one_step": _rival_one_step,
    "right_align_each_row": _rival_rowwise_right_align,
    "treat_lane_as_one_object": _rival_lane_as_one_object,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "multi_step_motion": _differs_from(_rival_one_step),
    "rigid_shape_translation": _differs_from(_rival_rowwise_right_align),
    "independent_components": _differs_from(_rival_lane_as_one_object),
}

WITNESS_RIVALS = {
    "multi_step_motion": ["move_one_step"],
    "rigid_shape_translation": ["right_align_each_row"],
    "independent_components": ["treat_lane_as_one_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid examples that eliminate each named shortcut rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with independent east docking")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    if "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with independent east docking")

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
