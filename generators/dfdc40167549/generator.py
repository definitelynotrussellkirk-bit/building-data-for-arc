"""Generator for ``S11_H5`` / content hash ``dfdc40167549``.

The unique color-1 and color-2 markers define a translation vector.  Translate
the unique non-marker object by that vector onto an otherwise empty grid,
painting its 4-neighbor boundary orange (7) and its strict interior cyan (8).
Cells translated outside the canvas are clipped.

A five-slot schedule keeps every consecutive lesson identifiable: two
canonical-scale rectangle anchors (including the clipped held-out branch), all
four vector quadrants, a lawful overlapping translation, and concave objects
whose topological boundary differs from their bounding-box border.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "dfdc40167549"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8c8aa2055364"

SUMMARY = (
    "On a 0-background grid, locate the unique color-1 source marker, the "
    "unique color-2 destination marker, and the unique monochrome non-marker "
    "object. Translate every object cell by marker2-marker1 onto an otherwise "
    "empty grid. Paint translated 4-neighbor boundary cells orange (7) and "
    "strict interior cells cyan (8); clip translated cells that leave the "
    "canvas. Ordinary five-example windows include canonical-scale full and "
    "clipped rectangles, all vector quadrants, overlap, and a concave object "
    "that distinguishes topological boundary from bounding-box border."
)

INVARIANTS = [
    "the input is a rectangular 9..16 by 12..18 ARC grid with background 0",
    "there is exactly one color-1 marker and exactly one color-2 marker",
    "there is exactly one 4-connected monochrome non-marker object",
    "the source object has at least one boundary cell and one strict interior cell",
    "at least one translated boundary cell and one translated interior cell remain visible",
    "the output is newly constructed: source object and markers are not copied",
    "the Racket rule is the sole output authority; rule_mirror is test-only parity logic",
]

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.20

DIRECTIONS = ("down_right", "down_left", "up_left", "up_right")
TRANSLATION_MODES = ("full", "clipped", "overlap")
SHAPE_MODES = ("rectangle", "concave")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "12..18",
    },
    "vector_direction": {
        "type": "str",
        "default": "five-slot schedule",
        "valid": "|".join(DIRECTIONS),
    },
    "translation_mode": {
        "type": "str",
        "default": "five-slot schedule",
        "valid": "|".join(TRANSLATION_MODES),
    },
    "shape_mode": {
        "type": "str",
        "default": "five-slot schedule",
        "valid": "|".join(SHAPE_MODES),
    },
}

# Every Cartesian combination of the exact declared axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_SCHEDULE = (
    ("canonical_full", "down_right", "full", "rectangle"),
    ("canonical_clipped", "down_right", "clipped", "rectangle"),
    ("down_left_full_concave", "down_left", "full", "concave"),
    ("up_left_overlap_rectangle", "up_left", "overlap", "rectangle"),
    ("up_right_clipped_concave", "up_right", "clipped", "concave"),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SOURCE_COLORS = (3, 4, 5, 6, 9)
_CANONICAL_COLORS = (3, 4, 5)
_CANONICAL_DIMS = ((9, 12), (9, 13))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the semantic schedule slot used by a generated sample."""
    del seed, difficulty
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)][0]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _components_4_color(grid: Sequence[Sequence[int]], background: int = 0):
    height, width = len(grid), len(grid[0])
    seen: set[Point] = set()
    components: list[tuple[int, set[Point], tuple[int, int, int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == background or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells: set[Point] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for row_delta, column_delta in _CARDINAL:
                    neighbor = (current[0] + row_delta, current[1] + column_delta)
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] != color:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)
            rows = [point[0] for point in cells]
            columns = [point[1] for point in cells]
            components.append(
                (color, cells, (min(rows), min(columns), max(rows), max(columns)))
            )
    return components


def _markers(grid: Sequence[Sequence[int]]) -> tuple[list[Point], list[Point]]:
    ones: list[Point] = []
    twos: list[Point] = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 1:
                ones.append((row_index, column_index))
            elif value == 2:
                twos.append((row_index, column_index))
    return ones, twos


def _source_component(
    grid: Sequence[Sequence[int]],
) -> tuple[int, set[Point], tuple[int, int, int, int]]:
    components = [
        component
        for component in _components_4_color(grid)
        if component[0] not in (1, 2)
    ]
    if len(components) != 1:
        raise ValueError(f"expected exactly one non-marker object, found {len(components)}")
    return components[0]


def _boundary_cells(cells: set[Point]) -> set[Point]:
    return {
        point
        for point in cells
        if any(
            (point[0] + row_delta, point[1] + column_delta) not in cells
            for row_delta, column_delta in _CARDINAL
        )
    }


def _translation_geometry(grid: Sequence[Sequence[int]]):
    ones, twos = _markers(grid)
    if len(ones) != 1 or len(twos) != 1:
        raise ValueError("expected exactly one color-1 and one color-2 marker")
    color, cells, bbox = _source_component(grid)
    row_delta = twos[0][0] - ones[0][0]
    column_delta = twos[0][1] - ones[0][1]
    translated = {
        (row + row_delta, column + column_delta) for row, column in cells
    }
    return color, cells, bbox, row_delta, column_delta, translated


def _direction(row_delta: int, column_delta: int) -> str:
    if row_delta == 0 or column_delta == 0:
        return "axis_aligned"
    vertical = "down" if row_delta > 0 else "up"
    horizontal = "right" if column_delta > 0 else "left"
    return f"{vertical}_{horizontal}"


def _translation_mode(
    cells: set[Point], translated: set[Point], height: int, width: int
) -> str:
    if any(not (0 <= row < height and 0 <= column < width) for row, column in translated):
        return "clipped"
    if cells & translated:
        return "overlap"
    return "full"


def _shape_mode(cells: set[Point], bbox: tuple[int, int, int, int]) -> str:
    top, left, bottom, right = bbox
    full = {
        (row, column)
        for row in range(top, bottom + 1)
        for column in range(left, right + 1)
    }
    return "rectangle" if cells == full else "concave"


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding lesson inputs."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 9 <= height <= 16:
        errors.append(f"height {height} outside declared envelope 9..16")
    if not 12 <= width <= 18:
        errors.append(f"width {width} outside declared envelope 12..18")

    ones, twos = _markers(grid)
    if len(ones) != 1:
        errors.append(f"expected exactly one color-1 marker, found {len(ones)}")
    if len(twos) != 1:
        errors.append(f"expected exactly one color-2 marker, found {len(twos)}")
    if len(ones) != 1 or len(twos) != 1:
        return errors

    components = [
        component
        for component in _components_4_color(grid)
        if component[0] not in (1, 2)
    ]
    if len(components) != 1:
        errors.append(f"expected exactly one non-marker object, found {len(components)}")
        return errors

    color, cells, bbox = components[0]
    if color in (7, 8):
        errors.append(f"source color {color} collides with output role colors 7/8")
    top, left, bottom, right = bbox
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        errors.append("source object bbox must be at least 3x3")

    boundary = _boundary_cells(cells)
    interior = cells - boundary
    if not boundary:
        errors.append("source object has no boundary cells")
    if not interior:
        errors.append("source object has no strict interior cell")

    row_delta = twos[0][0] - ones[0][0]
    column_delta = twos[0][1] - ones[0][1]
    if row_delta == 0 or column_delta == 0:
        errors.append("marker vector must have nonzero row and column components")

    translated_boundary = {
        (row + row_delta, column + column_delta) for row, column in boundary
    }
    translated_interior = {
        (row + row_delta, column + column_delta) for row, column in interior
    }
    visible_boundary = {
        point
        for point in translated_boundary
        if 0 <= point[0] < height and 0 <= point[1] < width
    }
    visible_interior = {
        point
        for point in translated_interior
        if 0 <= point[0] < height and 0 <= point[1] < width
    }
    if not visible_boundary:
        errors.append("translation leaves no visible boundary cell")
    if not visible_interior:
        errors.append("translation leaves no visible interior cell")

    marker_cells = {ones[0], twos[0]}
    if marker_cells & cells:
        errors.append("a marker occupies a source-object cell")
    if marker_cells & (visible_boundary | visible_interior):
        errors.append("a marker occupies a translated target cell")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Empirical canonical envelope for the two train and one held-out inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in _CANONICAL_DIMS:
        reasons.append(f"dimensions {dimensions} are outside canonical profiles {_CANONICAL_DIMS}")
    color, cells, bbox, row_delta, column_delta, _ = _translation_geometry(grid)
    top, left, bottom, right = bbox
    shape = (bottom - top + 1, right - left + 1)
    if _shape_mode(cells, bbox) != "rectangle":
        reasons.append("canonical source objects are solid rectangles")
    if shape not in {(3, 4), (4, 4)}:
        reasons.append(f"source shape {shape} is outside canonical rectangle sizes")
    if color not in _CANONICAL_COLORS:
        reasons.append(f"source color {color} is outside canonical colors {_CANONICAL_COLORS}")
    if row_delta != 1 or column_delta not in (5, 6, 7):
        reasons.append(
            f"marker vector {(row_delta, column_delta)} is outside canonical vectors"
        )
    return reasons


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    _, cells, bbox, row_delta, column_delta, translated = _translation_geometry(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "vector_direction": _direction(row_delta, column_delta),
        "translation_mode": _translation_mode(
            cells, translated, len(grid), len(grid[0])
        ),
        "shape_mode": _shape_mode(cells, bbox),
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; Racket remains authoritative."""
    _, cells, _, row_delta, column_delta, _ = _translation_geometry(grid)
    boundary = _boundary_cells(cells)
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, column in cells:
        target_row = row + row_delta
        target_column = column + column_delta
        if 0 <= target_row < len(grid) and 0 <= target_column < len(grid[0]):
            output[target_row][target_column] = 7 if (row, column) in boundary else 8
    return output


def _paint_at_fixed_anchor(grid: Sequence[Sequence[int]]) -> Grid:
    """Canonical-train shortcut: always place the object bbox at row 2, col 8."""
    _, cells, bbox = _source_component(grid)
    top, left, _, _ = bbox
    boundary = _boundary_cells(cells)
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, column in cells:
        target_row = 2 + (row - top)
        target_column = 8 + (column - left)
        if 0 <= target_row < len(grid) and 0 <= target_column < len(grid[0]):
            output[target_row][target_column] = 7 if (row, column) in boundary else 8
    return output


def _bbox_border_translation(grid: Sequence[Sequence[int]]) -> Grid:
    """Plausible rectangle shortcut: use bbox border instead of true boundary."""
    _, cells, bbox, row_delta, column_delta, _ = _translation_geometry(grid)
    top, left, bottom, right = bbox
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, column in cells:
        target_row = row + row_delta
        target_column = column + column_delta
        if 0 <= target_row < len(grid) and 0 <= target_column < len(grid[0]):
            border = row in (top, bottom) or column in (left, right)
            output[target_row][target_column] = 7 if border else 8
    return output


def _clamp_translation_in_bounds(grid: Sequence[Sequence[int]]) -> Grid:
    """Plausible no-clipping shortcut: shift the whole bbox back onto canvas."""
    _, cells, bbox, row_delta, column_delta, _ = _translation_geometry(grid)
    top, left, bottom, right = bbox
    row_delta = min(max(row_delta, -top), len(grid) - 1 - bottom)
    column_delta = min(max(column_delta, -left), len(grid[0]) - 1 - right)
    boundary = _boundary_cells(cells)
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, column in cells:
        target_row = row + row_delta
        target_column = column + column_delta
        output[target_row][target_column] = 7 if (row, column) in boundary else 8
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "fixed_target_anchor": _paint_at_fixed_anchor,
    "bbox_border_not_topological_boundary": _bbox_border_translation,
    "clamp_instead_of_clip": _clamp_translation_in_bounds,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _has_mode(grid: Any, mode: str) -> bool:
    return not self_check(grid) and observe_overrides(grid)["translation_mode"] == mode


def _has_direction(grid: Any, direction: str) -> bool:
    return not self_check(grid) and observe_overrides(grid)["vector_direction"] == direction


SEMANTIC_WITNESSES = {
    "clipped_translation_refutes_clamp": lambda grid: (
        _has_mode(grid, "clipped")
        and _valid_and_refutes(grid, "clamp_instead_of_clip")
    ),
    "concave_boundary_refutes_bbox_border": lambda grid: (
        not self_check(grid)
        and observe_overrides(grid)["shape_mode"] == "concave"
        and _valid_and_refutes(grid, "bbox_border_not_topological_boundary")
    ),
    "variable_target_refutes_fixed_anchor": lambda grid: _valid_and_refutes(
        grid, "fixed_target_anchor"
    ),
}

WITNESS_RIVALS = {
    "clipped_translation_refutes_clamp": ["clamp_instead_of_clip"],
    "concave_boundary_refutes_bbox_border": [
        "bbox_border_not_topological_boundary"
    ],
    "variable_target_refutes_fixed_anchor": ["fixed_target_anchor"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require exact demonstrations that collectively refute every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def _draw_axis(ctx: Any, label: str, options: Sequence[str], scheduled: str) -> str:
    draw_options = options if label in ctx.overrides else (scheduled,)
    return str(ctx.draw_choice(label, draw_options))


def _band_bounds(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (9, 11), (12, 14)
    if difficulty == "hard":
        return (12, 16), (15, 18)
    return (10, 13), (13, 16)


def _draw_dimension(
    ctx: Any, label: str, bounds: tuple[int, int], anchor: int | None
) -> int:
    full_bounds = (9, 16) if label == "grid_h" else (12, 18)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, *full_bounds)
    if anchor is not None:
        return ctx.draw_int(label, anchor, anchor)
    return ctx.draw_int(label, *bounds)


def _normalized_shape(height: int, width: int, shape_mode: str) -> set[Point]:
    cells = {
        (row, column)
        for row in range(height)
        for column in range(width)
    }
    if shape_mode == "concave":
        cells.remove((0, width // 2))
    return cells


def _shape_size(ctx: Any, shape_mode: str, difficulty: Any) -> tuple[int, int]:
    rng = ctx.draw_rng("shape_size_internal")
    if shape_mode == "concave":
        if difficulty == "hard":
            return rng.randint(4, 5), rng.randint(4, 6)
        return 4, rng.randint(4, 5)
    if difficulty == "easy":
        return 3, rng.randint(3, 4)
    if difficulty == "hard":
        return rng.randint(4, 5), rng.randint(4, 6)
    return rng.randint(3, 4), rng.randint(4, 5)


def _signed(direction: str) -> tuple[int, int]:
    mapping = {
        "down_right": (1, 1),
        "down_left": (1, -1),
        "up_left": (-1, -1),
        "up_right": (-1, 1),
    }
    return mapping[direction]


def _choose_inclusive(rng: Any, low: int, high: int, label: str) -> int:
    if high < low:
        raise ValueError(f"no legal {label} range [{low}, {high}]")
    return rng.randint(low, high)


def _fit_range(canvas: int, extent: int, delta: int) -> tuple[int, int]:
    return max(0, -delta), min(canvas - extent, canvas - extent - delta)


def _construct_layout(
    ctx: Any,
    *,
    height: int,
    width: int,
    blob_height: int,
    blob_width: int,
    direction: str,
    translation_mode: str,
) -> tuple[int, int, int, int]:
    row_sign, column_sign = _signed(direction)
    rng = ctx.draw_rng("layout")

    if translation_mode == "overlap":
        row_delta = row_sign
        column_delta = column_sign
        row_low, row_high = _fit_range(height, blob_height, row_delta)
        col_low, col_high = _fit_range(width, blob_width, column_delta)
        top = _choose_inclusive(rng, row_low, row_high, "overlap row")
        left = _choose_inclusive(rng, col_low, col_high, "overlap column")
        return top, left, row_delta, column_delta

    if translation_mode == "full":
        row_delta = row_sign
        column_delta = column_sign * blob_width
        row_low, row_high = _fit_range(height, blob_height, row_delta)
        col_low, col_high = _fit_range(width, blob_width, column_delta)
        top = _choose_inclusive(rng, row_low, row_high, "full row")
        left = _choose_inclusive(rng, col_low, col_high, "full column")
        return top, left, row_delta, column_delta

    row_delta = row_sign
    row_low, row_high = _fit_range(height, blob_height, row_delta)
    top = _choose_inclusive(rng, row_low, row_high, "clipped row")
    if column_sign > 0:
        left = _choose_inclusive(rng, 0, width - 2 * blob_width, "right-clip source column")
        column_delta = width - blob_width + 1 - left
    else:
        left = _choose_inclusive(
            rng, blob_width, width - blob_width, "left-clip source column"
        )
        column_delta = -(left + 1)
    return top, left, row_delta, column_delta


def _choose_markers(
    ctx: Any,
    *,
    height: int,
    width: int,
    row_delta: int,
    column_delta: int,
    forbidden: set[Point],
) -> tuple[Point, Point]:
    candidates: list[tuple[Point, Point]] = []
    for row in range(height):
        for column in range(width):
            target = (row + row_delta, column + column_delta)
            source = (row, column)
            if not (0 <= target[0] < height and 0 <= target[1] < width):
                continue
            if source in forbidden or target in forbidden:
                continue
            candidates.append((source, target))
    if not candidates:
        raise ValueError("no legal marker pair remains outside source and target cells")
    return ctx.draw_rng("markers").choice(candidates)


def _canonical_anchor(ctx: Any, slot: int, source_color: int) -> Grid:
    height, width = _CANONICAL_DIMS[slot]
    rng = ctx.draw_rng("canonical_anchor_layout")
    blob_height = rng.choice((3, 4))
    blob_width = 4
    row_delta = 1
    column_delta = rng.choice((5, 6, 7))
    top = rng.randint(1, height - blob_height - row_delta)
    if slot == 0:
        # Fully visible and horizontally disjoint, as in both train examples.
        left = rng.randint(0, width - blob_width - column_delta)
    else:
        # Translate exactly one column beyond the right edge, as in held-out.
        left = width + 1 - blob_width - column_delta

    source_cells = {
        (row, column)
        for row in range(top, top + blob_height)
        for column in range(left, left + blob_width)
    }
    visible_target = {
        (row + row_delta, column + column_delta)
        for row, column in source_cells
        if 0 <= row + row_delta < height and 0 <= column + column_delta < width
    }
    marker_one, marker_two = _choose_markers(
        ctx,
        height=height,
        width=width,
        row_delta=row_delta,
        column_delta=column_delta,
        forbidden=source_cells | visible_target,
    )

    grid = full_grid(height, width, 0)
    for row, column in source_cells:
        grid[row][column] = source_color
    grid[marker_one[0]][marker_one[1]] = 1
    grid[marker_two[0]][marker_two[1]] = 2
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = int(sample_index) % len(_SCHEDULE)
    _, scheduled_direction, scheduled_translation, scheduled_shape = _SCHEDULE[slot]
    direction = _draw_axis(ctx, "vector_direction", DIRECTIONS, scheduled_direction)
    translation_mode = _draw_axis(
        ctx, "translation_mode", TRANSLATION_MODES, scheduled_translation
    )
    shape_mode = _draw_axis(ctx, "shape_mode", SHAPE_MODES, scheduled_shape)

    band_height, band_width = _band_bounds(difficulty)
    anchor = _CANONICAL_DIMS[slot] if slot in (0, 1) else None
    height = _draw_dimension(ctx, "grid_h", band_height, anchor[0] if anchor else None)
    width = _draw_dimension(ctx, "grid_w", band_width, anchor[1] if anchor else None)

    source_color_rng = ctx.draw_rng("source_color")
    if not overrides and slot in (0, 1):
        grid = _canonical_anchor(ctx, slot, source_color_rng.choice(_CANONICAL_COLORS))
        errors = self_check(grid)
        if errors:
            raise RuntimeError(f"canonical anchor construction failed: {errors}")
        return grid

    blob_height, blob_width = _shape_size(ctx, shape_mode, difficulty)
    blob_height = min(blob_height, height // 2)
    blob_width = min(blob_width, width // 2)
    if shape_mode == "concave":
        blob_height = max(4, blob_height)
        blob_width = max(4, blob_width)

    top, left, row_delta, column_delta = _construct_layout(
        ctx,
        height=height,
        width=width,
        blob_height=blob_height,
        blob_width=blob_width,
        direction=direction,
        translation_mode=translation_mode,
    )
    normalized = _normalized_shape(blob_height, blob_width, shape_mode)
    source_cells = {(top + row, left + column) for row, column in normalized}
    translated_cells = {
        (row + row_delta, column + column_delta) for row, column in source_cells
    }
    visible_translated = {
        point
        for point in translated_cells
        if 0 <= point[0] < height and 0 <= point[1] < width
    }
    marker_one, marker_two = _choose_markers(
        ctx,
        height=height,
        width=width,
        row_delta=row_delta,
        column_delta=column_delta,
        forbidden=source_cells | visible_translated,
    )

    grid = full_grid(height, width, 0)
    source_color = source_color_rng.choice(_SOURCE_COLORS)
    for row, column in source_cells:
        grid[row][column] = source_color
    grid[marker_one[0]][marker_one[1]] = 1
    grid[marker_two[0]][marker_two[1]] = 2

    errors = self_check(grid)
    if errors:
        raise RuntimeError(
            "generator constructed an invalid scene "
            f"for direction={direction}, mode={translation_mode}, shape={shape_mode}: {errors}"
        )
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "vector_direction": direction,
        "translation_mode": translation_mode,
        "shape_mode": shape_mode,
    }
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid
