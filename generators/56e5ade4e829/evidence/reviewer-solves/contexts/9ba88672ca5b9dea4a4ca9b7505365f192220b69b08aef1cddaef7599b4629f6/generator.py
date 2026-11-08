"""Input generator for H133: marker-selected set operation on two shapes.

The selected Racket rule is unchanged and remains the label authority.  Each
input contains one connected color-1 shape, one connected color-2 shape, and
one isolated singleton marker.  The shapes are independently bbox-normalized;
marker 3 selects intersection, marker 4 selects union, and any other marker
color selects symmetric difference.  The result is cropped to its own bbox and
painted color 8.

The public examples contain no color-3 marker, so the production curriculum
uses a period-three control schedule.  Five demonstrations plus one query give
six consecutive examples; every query rotation still leaves at least one XOR,
intersection, and union demonstration.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56e5ade4e829"
TASK_ID = GENERATOR_ID
RULE_HASH = "b85aae646e78"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.80

SUMMARY = (
    "An 8..10 by 10..13 zero-background grid contains one connected color-1 "
    "shape, one connected color-2 shape, and one isolated singleton marker. "
    "Normalize each shape to its own bbox. Marker 3 selects intersection, "
    "marker 4 selects union, and marker 5..9 selects symmetric difference. "
    "Crop the selected nonempty result to its bbox and paint it color 8. "
    "Normalized shapes overlap but are nonidentical; both partial-overlap and "
    "strict-subset relations are generated, and all three operation outputs "
    "are observably distinct."
)

INVARIANTS = [
    "background is 0 and the palette is exactly {0,1,2,marker}",
    "colors 1 and 2 each form one connected 3..7-cell polyomino",
    "operand bounding boxes have at least one blank separator row or column",
    "there is exactly one isolated marker cell, colored 3..9",
    "normalized operands overlap, are nonidentical, and are partial or strict-subset",
    "intersection, union, and symmetric-difference render to three distinct crops",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "periodic canonical profile",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "periodic canonical profile",
        "valid": "10..13",
    },
    "ctrl": {
        "type": "int",
        "default": "period-three schedule: 0=XOR, 1=intersection, 2=union",
        "valid": "0|1|2",
    },
    "relation": {
        "type": "str",
        "default": "weighted partial|subset",
        "valid": "partial|subset",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("xor", "intersection", "union")

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CANONICAL_DIMS = ((8, 10), (8, 11), (9, 12), (9, 13), (10, 12))
_XOR_MARKERS = (5, 6, 7, 8, 9)


def _seed_phase(seed, modulus):
    digest = hashlib.sha256(repr(seed).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def schedule_profile(seed, sample_index, difficulty=None):
    """Control branch used by the ordered teaching schedule.

    The seed contributes a stable nonlinear phase.  Consecutive sample indices
    still form a complete period-three curriculum, while common audit samplers
    that advance seed and index together cannot algebraically cancel the cycle.
    """
    phase = _seed_phase(seed, len(SCHEDULE_PROFILES))
    return SCHEDULE_PROFILES[(phase + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _scheduled_ctrl(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES.index(schedule_profile(seed, sample_index, difficulty))


def _scheduled_dimensions(seed, sample_index, difficulty=None):
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return _CANONICAL_DIMS[
        (_seed_phase(seed, len(_CANONICAL_DIMS)) + int(sample_index) + band_offset)
        % len(_CANONICAL_DIMS)
    ]


def _normalize(cells):
    cells = frozenset(cells)
    if not cells:
        return frozenset()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _extent(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _boxes_have_blank_separator(first, second):
    a = _bbox(first)
    b = _bbox(second)
    return (
        a[2] + 1 < b[0]
        or b[2] + 1 < a[0]
        or a[3] + 1 < b[1]
        or b[3] + 1 < a[1]
    )


def _shape_relation(first, second):
    if not first or not second or not first & second:
        return "other"
    if first == second:
        return "identical"
    if first < second or second < first:
        return "subset"
    if first - second and second - first:
        return "partial"
    return "other"


def _paint_crop(cells):
    cells = _normalize(cells)
    if not cells:
        return [[0]]
    height, width = _extent(cells)
    output = full_grid(height, width, 0)
    for row, col in cells:
        output[row][col] = 8
    return output


def _frozen_output(cells):
    return tuple(tuple(row) for row in _paint_crop(cells))


def _operations_are_distinct(first, second):
    return len(
        {
            _frozen_output(first & second),
            _frozen_output(first | second),
            _frozen_output(first ^ second),
        }
    ) == 3


@lru_cache(maxsize=1)
def _shape_bank():
    """All normalized connected 3..7-cell masks fitting a 4x4 bbox."""
    current = {frozenset({(0, 0)})}
    by_size = {}
    for size in range(2, 8):
        grown = set()
        for shape in current:
            for row, col in shape:
                for drow, dcol in _CARDINAL:
                    point = (row + drow, col + dcol)
                    if point in shape:
                        continue
                    candidate = _normalize(set(shape) | {point})
                    height, width = _extent(candidate)
                    if height <= 4 and width <= 4:
                        grown.add(candidate)
        current = grown
        if size >= 3:
            by_size[size] = tuple(
                sorted(current, key=lambda cells: tuple(sorted(cells)))
            )
    return by_size


@lru_cache(maxsize=None)
def _candidate_pairs(relation, size1, size2):
    candidates = []
    for first in _shape_bank()[size1]:
        for second in _shape_bank()[size2]:
            if _shape_relation(first, second) != relation:
                continue
            if not _operations_are_distinct(first, second):
                continue
            candidates.append((first, second))
    return tuple(candidates)


def _size_options(difficulty):
    # Every size remains possible in every band; repetition changes only weight.
    if difficulty == "easy":
        return (3, 4, 5, 5, 6, 6, 7, 7, 7)
    if difficulty == "hard":
        return (3, 4, 5, 5, 6, 6, 7, 7, 7)
    return (3, 4, 4, 5, 5, 6, 6, 7, 7)


def _draw_operands(rng, relation, difficulty):
    sizes = _size_options(difficulty)
    size_pairs = [
        (size1, size2)
        for size1 in sizes
        for size2 in sizes
        if relation == "partial" or size1 != size2
    ]
    # Every listed combination has at least one candidate, but keep the explicit
    # scan so a future shape-bank change fails clearly rather than looping.
    start = rng.randrange(len(size_pairs))
    for offset in range(len(size_pairs)):
        size1, size2 = size_pairs[(start + offset) % len(size_pairs)]
        candidates = _candidate_pairs(relation, size1, size2)
        if candidates:
            return rng.choice(candidates)
    raise RuntimeError(f"no {relation} operand pair for difficulty {difficulty!r}")


def _translated(shape, row, col):
    return frozenset((row + drow, col + dcol) for drow, dcol in shape)


def _marker_candidates(height, width, first, second):
    occupied = first | second
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied
        and all(
            max(abs(row - rr), abs(col - cc)) > 1
            for rr, cc in occupied
        )
    ]


def _horizontal_layout(first, second, height, width, rng, *, force_top=False):
    swap = bool(rng.randrange(2))
    left_shape, right_shape = ((second, first) if swap else (first, second))
    left_h, left_w = _extent(left_shape)
    right_h, right_w = _extent(right_shape)
    free = width - left_w - right_w - 1
    if free < 0:
        raise RuntimeError("declared minimum width cannot fit separated operands")
    left_margin = rng.randint(0, free)
    remaining = free - left_margin
    extra_gap = rng.randint(0, remaining)
    left_col = left_margin
    right_col = left_margin + left_w + 1 + extra_gap
    if force_top:
        left_row = right_row = 0
    else:
        left_row = rng.randint(0, height - left_h)
        right_row = rng.randint(0, height - right_h)
    left_cells = _translated(left_shape, left_row, left_col)
    right_cells = _translated(right_shape, right_row, right_col)
    pair = (right_cells, left_cells) if swap else (left_cells, right_cells)
    if not _boxes_have_blank_separator(*pair):
        raise RuntimeError("constructive placement lost its blank separator")
    return pair


def _place_operands(first, second, height, width, rng):
    cells1, cells2 = _horizontal_layout(first, second, height, width, rng)
    candidates = _marker_candidates(height, width, cells1, cells2)
    if not candidates:
        # With height >= 8 and operand height <= 4, top-alignment leaves a
        # guaranteed isolated lower strip.  This is a constructive fallback,
        # not a capped retry loop.
        cells1, cells2 = _horizontal_layout(
            first, second, height, width, rng, force_top=True
        )
        candidates = _marker_candidates(height, width, cells1, cells2)
    if not candidates:
        raise RuntimeError("constructive layout left no isolated marker cell")
    return cells1, cells2, rng.choice(candidates)


def _validate_request(difficulty, overrides):
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "ctrl"}:
            if type(value) is not int:
                raise ValueError(
                    f"{name} must be an integer, not {type(value).__name__}"
                )
        elif name == "relation" and type(value) is not str:
            raise ValueError(
                f"relation must be a string, not {type(value).__name__}"
            )
    if overrides.get("grid_h") is not None and not 8 <= overrides["grid_h"] <= 10:
        raise ValueError("grid_h must be in 8..10")
    if overrides.get("grid_w") is not None and not 10 <= overrides["grid_w"] <= 13:
        raise ValueError("grid_w must be in 10..13")
    if overrides.get("ctrl") is not None and overrides["ctrl"] not in (0, 1, 2):
        raise ValueError("ctrl must be 0, 1, or 2")
    if overrides.get("relation") is not None and overrides["relation"] not in {
        "partial",
        "subset",
    }:
        raise ValueError("relation must be 'partial' or 'subset'")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _scheduled_dimensions(seed, sample_index, difficulty)
    height_options = (8, 9, 10) if overrides.get("grid_h") is not None else (scheduled_h,)
    width_options = (10, 11, 12, 13) if overrides.get("grid_w") is not None else (scheduled_w,)
    ctrl_options = (0, 1, 2) if overrides.get("ctrl") is not None else (
        _scheduled_ctrl(seed, sample_index, difficulty),
    )

    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    ctrl = ctx.draw_choice("ctrl", ctrl_options)
    relation = ctx.draw_choice(
        "relation", ("partial", "partial", "partial", "partial", "subset")
    )

    first, second = _draw_operands(
        ctx.draw_rng("operand_shapes"), relation, difficulty
    )
    cells1, cells2, marker_position = _place_operands(
        first,
        second,
        height,
        width,
        ctx.draw_rng("operand_layout"),
    )
    if ctrl == 1:
        marker_color = 3
    elif ctrl == 2:
        marker_color = 4
    else:
        marker_color = ctx.draw_rng("xor_marker").choice(_XOR_MARKERS)

    grid = full_grid(height, width, 0)
    for row, col in cells1:
        grid[row][col] = 1
    for row, col in cells2:
        grid[row][col] = 2
    grid[marker_position[0]][marker_position[1]] = marker_color

    requested = {name: value for name, value in overrides.items() if value is not None}
    if requested:
        actual = observe_overrides(grid)
        mismatch = {
            name: (value, actual.get(name))
            for name, value in requested.items()
            if actual.get(name) != value
        }
        if mismatch:
            raise RuntimeError(f"exact override construction mismatch: {mismatch}")
    return grid


def _grid_structure_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["ragged grid"]
    bad = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        return [
            "cells must be integer ARC colors 0..9; "
            f"first bad cell={bad[0]!r}"
        ]
    return []


def _color_cells(grid, color):
    return frozenset(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )


def _is_connected(cells):
    if not cells:
        return False
    todo = deque([next(iter(cells))])
    seen = {todo[0]}
    while todo:
        row, col = todo.popleft()
        for drow, dcol in _CARDINAL:
            point = (row + drow, col + dcol)
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return len(seen) == len(cells)


def _marker_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1, 2)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    """Return diagnostics for grids outside the documented teaching manifold."""
    errors = _grid_structure_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 10:
        errors.append(f"grid height {height} outside 8..10")
    if not 10 <= width <= 13:
        errors.append(f"grid width {width} outside 10..13")

    markers = _marker_cells(grid)
    if len(markers) != 1:
        errors.append(f"expected exactly one non-0/1/2 marker cell, found {len(markers)}")
        marker = None
    else:
        marker = markers[0]
        if marker[2] not in range(3, 10):
            errors.append(f"marker color {marker[2]!r} outside 3..9")

    palette = {value for row in grid for value in row}
    if marker is not None:
        expected_palette = {0, 1, 2, marker[2]}
        if palette != expected_palette:
            errors.append(
                f"palette {sorted(palette)} must equal {sorted(expected_palette)}"
            )

    physical = {}
    normalized = {}
    for color in (1, 2):
        cells = _color_cells(grid, color)
        physical[color] = cells
        normalized[color] = _normalize(cells)
        if not 3 <= len(cells) <= 7:
            errors.append(f"color-{color} cell count {len(cells)} outside 3..7")
        if cells and not _is_connected(cells):
            errors.append(f"color-{color} cells are not one 4-connected component")

    if physical[1] and physical[2]:
        if not _boxes_have_blank_separator(physical[1], physical[2]):
            errors.append(
                "operand bounding boxes need at least one blank separator row or column"
            )
        relation = _shape_relation(normalized[1], normalized[2])
        if relation not in {"partial", "subset"}:
            errors.append(
                "normalized operands must overlap nonidentically as partial or subset; "
                f"observed {relation}"
            )
        if not _operations_are_distinct(normalized[1], normalized[2]):
            errors.append(
                "intersection, union, and symmetric difference must render distinctly"
            )

    if marker is not None and physical[1] and physical[2]:
        row, col, _ = marker
        if any(
            max(abs(row - rr), abs(col - cc)) <= 1
            for rr, cc in physical[1] | physical[2]
        ):
            errors.append("marker must be isolated from both operand shapes")
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    marker_color = _marker_cells(grid)[0][2]
    ctrl = 1 if marker_color == 3 else 2 if marker_color == 4 else 0
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "ctrl": ctrl,
        "relation": _shape_relation(first, second),
    }


def oracle_output(grid):
    """Transparent Python mirror used for diagnostics, never dataset labels."""
    errors = _grid_structure_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    if _color_cells(grid, 3):
        result = first & second
    elif _color_cells(grid, 4):
        result = first | second
    else:
        result = first ^ second
    return _paint_crop(result)


def _ignore_intersection_marker(grid):
    """WRONG rival: marker 4 means union; every other marker means XOR."""
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    result = first | second if _color_cells(grid, 4) else first ^ second
    return _paint_crop(result)


def strict_canonical_like(grid):
    # The generated domain is deliberately the canonical size/palette envelope.
    return self_check(grid)


def _ctrl_is(value):
    def predicate(grid):
        try:
            return observe_overrides(grid)["ctrl"] == value
        except (TypeError, ValueError, IndexError):
            return False
    return predicate


def _relation_is(value):
    def predicate(grid):
        try:
            return observe_overrides(grid)["relation"] == value
        except (TypeError, ValueError, IndexError):
            return False
    return predicate


def _intersection_marker_counterexample(grid):
    try:
        return (
            observe_overrides(grid)["ctrl"] == 1
            and oracle_output(grid) != _ignore_intersection_marker(grid)
        )
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "xor_control": _ctrl_is(0),
    "intersection_control": _ctrl_is(1),
    "union_control": _ctrl_is(2),
    "partial_operands": _relation_is("partial"),
    "subset_operands": _relation_is("subset"),
    "intersection_marker_counterexample": _intersection_marker_counterexample,
}
BRANCH_WITNESSES = {
    "xor_control",
    "intersection_control",
    "union_control",
    "partial_operands",
    "subset_operands",
}
SEMANTIC_RIVALS = {
    "ignore_intersection_marker": _ignore_intersection_marker,
}
WITNESS_RIVALS = {
    "intersection_marker_counterexample": ["ignore_intersection_marker"],
}
CANONICAL_SHORTCUTS = {
    "ignore_intersection_marker": _ignore_intersection_marker,
}
LESSON_COMPETITORS = {
    "ignore_intersection_marker": _ignore_intersection_marker,
}


def lesson_identifiable(demos, query):
    """Reject lessons that omit a control branch or leave a rival alive."""
    reasons = []
    controls = set()
    for index, demo in enumerate(demos):
        try:
            grid = demo["input"]
            truth = oracle_output(grid)
            observed = observe_overrides(grid)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"demo {index}: invalid input: {exc}")
            continue
        if demo.get("output") != truth:
            reasons.append(f"demo {index}: output disagrees with marker-selected set operation")
        controls.add(observed["ctrl"])

    missing = {0, 1, 2} - controls
    if missing:
        names = {0: "XOR", 1: "intersection", 2: "union"}
        reasons.append(
            "demonstrations omit control branch(es): "
            + ", ".join(names[value] for value in sorted(missing))
        )

    try:
        query_grid = query["input"]
        query_truth = oracle_output(query_grid)
        observe_overrides(query_grid)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reasons.append(f"query: invalid input: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_truth:
        reasons.append("query: output disagrees with marker-selected set operation")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query_grid) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demonstration but changes the query"
                )
    return reasons
