"""Generator for H29 — arrow-driven sweep shadows.

Every color-5..9 object has one touching code cell.  The code, not the side on
which it is attached, selects the sweep direction: 1=up, 2=right, 3=down,
4=left.  Code cells disappear and every original object cell paints a ray in
its own color through the grid edge.

The ordinary curriculum deliberately separates three cues confounded by the
small canonical set: marker attachment side, object color, and bounding-box
shape.  Generated markers cycle independently through all code/side pairs;
colors are not direction labels; and every default input contains a concave
object whose cellwise sweep differs from sweeping its full bounding box.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e64c021e29ad"
TASK_ID = "e64c021e29ad"
VERSION = "3.0.1"
RULE_HASH = "69a4bb5ee756"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25
LESSON_SCHEDULE_PERIOD = 48

SUMMARY = (
    "Each color-5..9 object has one touching code cell. Codes 1/2/3/4 mean "
    "up/right/down/left. Remove every code, then paint a same-color ray from "
    "each original object cell in its coded direction through the grid edge."
)

INVARIANTS = [
    "grids are 9..16 rows by 10..20 columns",
    "one to three distinct-color 4-connected objects use colors 5..9",
    "every object has exactly one adjacent code cell in 1..4",
    "every code cell is adjacent to exactly one object",
    "ordinary inputs contain at least two objects and decouple code, color, and attachment side",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9..11 easy, 10..14 medium, 12..16 hard; every fourth sample uses a linked canonical profile",
        "valid": "9..16",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "10..13 easy, 12..16 medium, 14..20 hard; every fourth sample uses a linked canonical profile",
        "valid": "10..20",
        "doc": "Grid width.",
    },
    "n_objects": {
        "type": "int",
        "default": "2 easy, 2..3 medium, 3 hard; linked canonical profiles use 2,2,3",
        "valid": "1..3",
        "doc": "Number of independently coded color-5..9 objects.",
    },
}

# Direction codes and matching geometric side numbers.
_DIRS = {
    1: (-1, 0),
    2: (0, 1),
    3: (1, 0),
    4: (0, -1),
}
_SIDES = (1, 2, 3, 4)  # top, right, bottom, left

# The first object in every ordinary input uses the code-specific concavity
# below.  Sweeping the full bounding rectangle adds at least one cell that the
# selected rule does not add.
_WITNESS_SHAPES = {
    1: ((0, 0), (0, 1), (1, 0)),       # missing lower-right; distinguishes up
    2: ((0, 0), (0, 1), (1, 1)),       # missing lower-left; distinguishes right
    3: ((0, 0), (1, 0), (1, 1)),       # missing upper-right; distinguishes down
    4: ((0, 0), (1, 0), (1, 1)),       # missing upper-right; distinguishes left
}
_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)

# These are the three canonical (height, width, distinct input colors) profiles.
_CANONICAL_PROFILES = frozenset({(9, 10, 5), (10, 11, 5), (12, 12, 7)})
_CANONICAL_SCHEDULE = (
    (9, 10, 2),
    (10, 11, 2),
    (12, 12, 3),
)

# A shortcut that exactly fits every labeled canonical pair: canonical color 5
# is always left, 6 up, 7 down and 8 right.  Color 9 never occurs canonically.
_COLOR_DIRECTION = {5: 4, 6: 1, 7: 3, 8: 2, 9: 1}


def _is_arc_int(value) -> bool:
    return type(value) is int and 0 <= value <= 9


def _component_records(grid):
    """Return row-major object records for a structurally valid grid.

    Callers that accept arbitrary user input should invoke ``self_check`` first.
    """
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color < 5 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo = [(r, c)]
            cells: list[tuple[int, int]] = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS.values():
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            cells = sorted(cells)
            markers = {
                (rr + dr, cc + dc)
                for rr, cc in cells
                for dr, dc in _DIRS.values()
                if 0 <= rr + dr < h
                and 0 <= cc + dc < w
                and grid[rr + dr][cc + dc] in _DIRS
            }
            marker = min(markers) if markers else None
            marker_side = None
            code = None
            if marker is not None:
                mr, mc = marker
                code = grid[mr][mc]
                min_r = min(rr for rr, _ in cells)
                max_r = max(rr for rr, _ in cells)
                min_c = min(cc for _, cc in cells)
                max_c = max(cc for _, cc in cells)
                if mr < min_r:
                    marker_side = 1
                elif mc > max_c:
                    marker_side = 2
                elif mr > max_r:
                    marker_side = 3
                elif mc < min_c:
                    marker_side = 4
                else:
                    # Legal concavity attachment: derive the first cardinal side
                    # from an adjacent object cell in code order.
                    for side, (dr, dc) in _DIRS.items():
                        if (mr - dr, mc - dc) in cells:
                            marker_side = side
                            break
            components.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "markers": frozenset(markers),
                    "marker": marker,
                    "code": code,
                    "marker_side": marker_side,
                }
            )
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or ambiguous inputs without throwing exceptions."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-sequence grid"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    if not grid[0]:
        return ["empty row"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)

    errors: list[str] = []
    if not (9 <= h <= 16 and 10 <= w <= 20):
        errors.append(f"dims {h}x{w} outside 9..16 by 10..20")
    bad_values = sorted(
        {value for row in grid for value in row if not _is_arc_int(value)},
        key=repr,
    )
    if bad_values:
        errors.append(f"invalid ARC values: {bad_values!r}")
        return errors

    records = _component_records(grid)
    if not (1 <= len(records) <= 3):
        errors.append(f"expected 1-3 color-5..9 objects, found {len(records)}")
    colors = [int(record["color"]) for record in records]
    if len(colors) != len(set(colors)):
        errors.append("each object must use a distinct color")

    arrow_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in _DIRS
    }
    marker_to_objects: dict[tuple[int, int], list[int]] = {
        marker: [] for marker in arrow_cells
    }
    for index, record in enumerate(records):
        markers = set(record["markers"])
        if len(markers) != 1:
            errors.append(
                f"object color {record['color']} has {len(markers)} adjacent code cells"
            )
        for marker in markers:
            marker_to_objects.setdefault(marker, []).append(index)
    for marker, owners in sorted(marker_to_objects.items()):
        if not owners:
            errors.append(f"code cell {marker} is not adjacent to an object")
        elif len(owners) != 1:
            errors.append(f"code cell {marker} is shared by {len(owners)} objects")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public control from visible pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_objects": len(_component_records(grid)) if grid and grid[0] else 0,
    }


def _paint_sweep(
    grid,
    direction_for: Callable[[dict[str, object]], int],
    *,
    bounding_box: bool = False,
    selected: Callable[[dict[str, object]], bool] | None = None,
):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for record in _component_records(grid):
        if selected is not None and not selected(record):
            continue
        cells: Iterable[tuple[int, int]] = record["cells"]
        if bounding_box:
            source = list(cells)
            min_r = min(r for r, _ in source)
            max_r = max(r for r, _ in source)
            min_c = min(c for _, c in source)
            max_c = max(c for _, c in source)
            cells = (
                (r, c)
                for r in range(min_r, max_r + 1)
                for c in range(min_c, max_c + 1)
            )
        direction = direction_for(record)
        dr, dc = _DIRS[direction]
        for r, c in sorted(cells):
            rr, cc = r, c
            while 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = int(record["color"])
                rr += dr
                cc += dc
    return out


def _python_apply(grid):
    """Independent executable spelling of the selected canonical Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid sweep input: " + "; ".join(errors))
    return _paint_sweep(grid, lambda record: int(record["code"]))


def _profile_signature(grid):
    if not grid or not grid[0]:
        return None
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return [f"self_check: {reason}" for reason in reasons]
    signature = _profile_signature(grid)
    if signature not in _CANONICAL_PROFILES:
        return [f"canonical size/palette profile mismatch: {signature!r}"]
    return []


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _shape_size(shape):
    return (
        max(r for r, _ in shape) - min(r for r, _ in shape) + 1,
        max(c for _, c in shape) - min(c for _, c in shape) + 1,
    )


def _marker_offsets(shape, side):
    if side == 1:
        edge = min(r for r, _ in shape)
        return tuple((edge - 1, c) for r, c in shape if r == edge)
    if side == 2:
        edge = max(c for _, c in shape)
        return tuple((r, edge + 1) for r, c in shape if c == edge)
    if side == 3:
        edge = max(r for r, _ in shape)
        return tuple((edge + 1, c) for r, c in shape if r == edge)
    edge = min(c for _, c in shape)
    return tuple((r, edge - 1) for r, c in shape if c == edge)


def _sweep_cells(cells, code, h, w):
    swept = set()
    dr, dc = _DIRS[code]
    for r, c in cells:
        rr, cc = r, c
        while 0 <= rr < h and 0 <= cc < w:
            swept.add((rr, cc))
            rr += dr
            cc += dc
    return frozenset(swept)


def _candidate_placements(h, w, shape, code, side):
    """Enumerate all in-bounds object+marker placements for one specification."""
    sh, sw = _shape_size(shape)
    for top in range(1, h - sh):
        for left in range(1, w - sw):
            object_cells = frozenset((top + r, left + c) for r, c in shape)
            for mr0, mc0 in _marker_offsets(shape, side):
                marker = (top + mr0, left + mc0)
                if not (0 <= marker[0] < h and 0 <= marker[1] < w):
                    continue
                if marker in object_cells:
                    continue
                yield {
                    "object": object_cells,
                    "marker": marker,
                    "code": code,
                    "sweep": _sweep_cells(object_cells, code, h, w),
                }


def _separated(candidate, placed) -> bool:
    """Keep independently coded units at least one king move apart."""
    actual = set(candidate["object"]) | {candidate["marker"]}
    for other in placed:
        other_actual = set(other["object"]) | {other["marker"]}
        if any(
            max(abs(r - rr), abs(c - cc)) <= 1
            for r, c in actual
            for rr, cc in other_actual
        ):
            return False
        # A later object's trail can otherwise overwrite the one-cell notch
        # that distinguishes cellwise sweeping from bounding-box sweeping.
        if not set(candidate["sweep"]).isdisjoint(other["sweep"]):
            return False
    return True


def _place_specs(rng, h, w, specs):
    candidate_lists = []
    for spec in specs:
        candidates = list(
            _candidate_placements(
                h, w, spec["shape"], spec["code"], spec["side"]
            )
        )
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    # Place the most constrained lists first, preserving object identity in the
    # final result.  Exhaustive backtracking makes exact min-size overrides safe.
    order = sorted(range(len(specs)), key=lambda i: len(candidate_lists[i]))
    result: list[dict[str, object] | None] = [None] * len(specs)

    def search(depth, placed):
        if depth == len(order):
            return True
        index = order[depth]
        for candidate in candidate_lists[index]:
            if not _separated(candidate, placed):
                continue
            result[index] = candidate
            if search(depth + 1, placed + [candidate]):
                return True
            result[index] = None
        return False

    if not search(0, []):
        raise ValueError(
            f"could not place {len(specs)} separated coded objects in {h}x{w}"
        )
    return [candidate for candidate in result if candidate is not None]


def _scheduled_colors(ctx, codes, sample_index):
    """Choose distinct colors while guaranteeing a color-direction counterexample."""
    n_objects = len(codes)
    rng = ctx.draw_rng("object_colors")
    if n_objects == 1:
        candidates = [color for color in range(5, 10) if _COLOR_DIRECTION[color] != codes[0]]
        return [rng.choice(candidates)]

    # Every ordinary input contains color 9, but its object position rotates.
    nine_index = sample_index % n_objects
    colors: list[int | None] = [None] * n_objects
    colors[nine_index] = 9
    available = [5, 6, 7, 8]
    rng.shuffle(available)
    for index in range(n_objects):
        if colors[index] is None:
            colors[index] = available.pop()

    # If all pairs happened to reproduce the canonical color mapping, change
    # one non-9 color to another unused mismatch.  This retains matching pairs
    # elsewhere while making every generated input a killing witness.
    if all(_COLOR_DIRECTION[int(color)] == code for color, code in zip(colors, codes)):
        for index, (color, code) in enumerate(zip(colors, codes)):
            if color == 9:
                continue
            used = {int(value) for value in colors if value is not None}
            replacements = [
                candidate
                for candidate in range(5, 9)
                if candidate not in used and _COLOR_DIRECTION[candidate] != code
            ]
            if replacements:
                colors[index] = rng.choice(replacements)
                break
    return [int(color) for color in colors]


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic curriculum branch without exposing RNG state."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    side = _SIDES[(sample_index // 4) % len(_SIDES)]
    if sample_index % 4 == 0:
        return ("canonical", (sample_index // 4) % len(_CANONICAL_SCHEDULE), side)
    return ("ordinary", sample_index % 4, side)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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
    band = difficulty or "medium"
    has_override = any(value is not None for value in overrides.values())
    canonical_slot = not has_override and sample_index % 4 == 0

    if canonical_slot:
        h0, w0, n0 = _CANONICAL_SCHEDULE[(sample_index // 4) % 3]
        h = ctx.draw_int_strict("grid_h", h0, h0)
        w = ctx.draw_int_strict("grid_w", w0, w0)
        n_objects = ctx.draw_int_strict("n_objects", n0, n0)
    else:
        if band == "easy":
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 9, 11, 10, 13, 2, 2
        elif band == "hard":
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 12, 16, 14, 20, 3, 3
        else:
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 10, 14, 12, 16, 2, 3
        h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 9, 16)
        w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 10, 20)
        n_objects = _banded_int(ctx, overrides, "n_objects", n_lo, n_hi, 1, 3)

    codes = [((sample_index + index) % 4) + 1 for index in range(n_objects)]
    marker_side = _SIDES[(sample_index // 4) % len(_SIDES)]
    # A one-object override has no second unit to break a code/attachment tie.
    # Rotate only that degenerate curriculum case so the visible example still
    # falsifies the canonical marker-side shortcut.
    if n_objects == 1 and marker_side == codes[0]:
        marker_side = _SIDES[marker_side % len(_SIDES)]
    colors = _scheduled_colors(ctx, codes, sample_index)
    shape_rng = ctx.draw_rng("shapes")
    specs = []
    for index, (code, color) in enumerate(zip(codes, colors)):
        shape = _WITNESS_SHAPES[code] if index == 0 else shape_rng.choice(_SHAPES)
        specs.append(
            {
                "code": code,
                "color": color,
                "side": marker_side,
                "shape": shape,
            }
        )

    placements = _place_specs(ctx.draw_rng("layout"), h, w, specs)
    grid = full_grid(h, w, 0)
    for spec, placement in zip(specs, placements):
        for r, c in placement["object"]:
            grid[r][c] = spec["color"]
        mr, mc = placement["marker"]
        grid[mr][mc] = spec["code"]

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generator error: " + "; ".join(errors))
    # The constructive schedule promises these ordinary teaching facts.  Fail
    # loudly if a future placement or shape edit accidentally masks one.
    intended = _python_apply(grid)
    checks = (
        ("marker-side", _rival_marker_side(grid)),
        ("object-color", _rival_object_color(grid)),
        ("bounding-box", _rival_bounding_box(grid)),
    )
    for name, rival in checks:
        if rival == intended:
            raise ValueError(f"internal generator error: {name} rival survived")
    if n_objects >= 2 and _rival_ignore_color_9(grid) == intended:
        raise ValueError("internal generator error: color-9 rival survived")
    return grid


# ---------------------------------------------------------------------------
# Executable rivals and witnesses
# ---------------------------------------------------------------------------


def _rival_marker_side(grid):
    return _paint_sweep(grid, lambda record: int(record["marker_side"]))


def _rival_object_color(grid):
    return _paint_sweep(grid, lambda record: _COLOR_DIRECTION[int(record["color"])])


def _rival_bounding_box(grid):
    return _paint_sweep(
        grid, lambda record: int(record["code"]), bounding_box=True
    )


def _rival_ignore_color_9(grid):
    return _paint_sweep(
        grid,
        lambda record: int(record["code"]),
        selected=lambda record: int(record["color"]) != 9,
    )


def _rival_largest_only(grid):
    records = _component_records(grid)
    largest = max(
        records,
        key=lambda record: (
            len(record["cells"]),
            -min(record["cells"])[0],
            -min(record["cells"])[1],
        ),
    )
    target = (int(largest["color"]), tuple(largest["cells"]))
    return _paint_sweep(
        grid,
        lambda record: int(record["code"]),
        selected=lambda record: (int(record["color"]), tuple(record["cells"])) == target,
    )


def _rival_fixed_up(grid):
    return _paint_sweep(grid, lambda _record: 1)


def _witness_marker_side(grid):
    return any(
        int(record["code"]) != int(record["marker_side"])
        for record in _component_records(grid)
    )


def _witness_color_direction(grid):
    return _python_apply(grid) != _rival_object_color(grid)


def _witness_bounding_box(grid):
    return _python_apply(grid) != _rival_bounding_box(grid)


def _witness_color_9(grid):
    return any(int(record["color"]) == 9 for record in _component_records(grid))


def _witness_multiple_objects(grid):
    return len(_component_records(grid)) >= 2


SEMANTIC_WITNESSES = {
    "marker_side_is_not_direction": _witness_marker_side,
    "color_does_not_encode_direction": _witness_color_direction,
    "cellwise_not_bounding_box": _witness_bounding_box,
    "color_9_is_an_object": _witness_color_9,
    "multiple_objects_sweep": _witness_multiple_objects,
}

SEMANTIC_RIVALS = {
    "marker_side_sweep": _rival_marker_side,
    "object_color_direction": _rival_object_color,
    "bounding_box_sweep": _rival_bounding_box,
    "ignore_color_9": _rival_ignore_color_9,
    "largest_object_only": _rival_largest_only,
    "fixed_up": _rival_fixed_up,
}

WITNESS_RIVALS = {
    "marker_side_is_not_direction": ["marker_side_sweep"],
    "color_does_not_encode_direction": ["object_color_direction"],
    "cellwise_not_bounding_box": ["bounding_box_sweep"],
    "color_9_is_an_object": ["ignore_color_9"],
    "multiple_objects_sweep": ["largest_object_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "object_color_direction": _rival_object_color,
    "bounding_box_sweep": _rival_bounding_box,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check the declared four-example teaching contract and named rivals."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        intended = _python_apply(grid)
        if output != intended:
            reasons.append(f"demo {index} output disagrees with coded cellwise sweep")
        valid_demos.append(pair)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"{name} rival survives every demonstration")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != _python_apply(q_grid):
        reasons.append("query output disagrees with coded cellwise sweep")
    return reasons


def mutation_fixtures():
    """Small task-semantic near misses that the validator must reject."""
    no_marker = full_grid(9, 10, 0)
    no_marker[3][3] = 6
    no_marker[3][4] = 6
    no_marker[4][3] = 6

    stray_marker = deepcopy(no_marker)
    stray_marker[7][8] = 1

    two_markers = deepcopy(no_marker)
    two_markers[2][3] = 1
    two_markers[3][5] = 2

    shared_marker = full_grid(9, 10, 0)
    shared_marker[4][3] = 6
    shared_marker[4][5] = 7
    shared_marker[4][4] = 2

    repeated_color = full_grid(9, 10, 0)
    repeated_color[2][2] = 6
    repeated_color[2][3] = 1
    repeated_color[6][7] = 6
    repeated_color[6][8] = 2

    return [
        ("object_without_code", no_marker),
        ("stray_code", stray_marker),
        ("two_codes_for_one_object", two_markers),
        ("one_code_shared_by_two_objects", shared_marker),
        ("same_color_split_into_two_objects", repeated_color),
    ]
