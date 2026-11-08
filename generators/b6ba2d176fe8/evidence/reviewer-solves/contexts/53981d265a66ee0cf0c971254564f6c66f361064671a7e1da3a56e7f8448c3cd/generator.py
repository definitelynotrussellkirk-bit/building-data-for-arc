"""Generator for ARC task b6ba2d176fe8.

The input contains two through six distinct-color solid rectangles, separated
left-to-right by at least one blank column.  The rule sorts the rectangles by
left edge and repaints their bounding boxes as a corner-overlapping staircase:
the first rectangle starts at (0, 0), and each following top-left advances by
(previous_height - 1, previous_width - 1).  The later rectangle owns the one
shared corner cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid


GENERATOR_ID = "b6ba2d176fe8"
TASK_ID = "b6ba2d176fe8"
VERSION = "3.0.0"
RULE_HASH = "6e7e6d4cfafc"

SUMMARY = (
    "Find every nonzero monochrome 4-connected object, sort the objects by "
    "their left bbox column, and paint each solid bbox rectangle on a fresh "
    "same-size zero grid. The first rectangle starts at (0,0). After painting "
    "a rectangle of height h and width w, advance the next top-left by "
    "(h-1,w-1), so consecutive rectangles share exactly one corner and the "
    "later color overwrites that shared cell."
)

INVARIANTS = [
    "the input has 2..6 distinct-color solid rectangular components",
    "rectangles are strictly left-to-right with at least one blank column between bboxes",
    "at least two rectangle dimensions differ and at least one rectangle is non-square",
    "the sorted corner-overlap staircase fits in the unchanged canvas",
    "normal draws include both exact 10x10 demonstrated geometry and broader lawful layouts",
]

ROW_LAYOUTS = ("bottom", "mixed", "scattered")
COLUMN_LAYOUTS = ("compact", "irregular", "spread")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "canonical_prior": {
        "type": "bool",
        "default": "30% true on unoverridden draws",
        "valid": "false|true",
    },
    "n_objects": {
        "type": "int",
        "default": "band rng: easy 2..3, medium 3..4, hard 4..6",
        "valid": "2..6",
    },
    "row_layout": {
        "type": "str",
        "default": "band-weighted rng",
        "valid": "bottom|mixed|scattered",
    },
    "column_layout": {
        "type": "str",
        "default": "band-weighted rng",
        "valid": "compact|irregular|spread",
    },
}

# Canonical-prior draws use only the four official 10x10 profiles.  The
# declaration is value-specific so the shared override gate can distinguish
# intentional refusals from ordinary multi-axis bugs.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"canonical_prior": True, "n_objects": (2, 5, 6)},
    {"canonical_prior": True, "row_layout": ("mixed", "scattered")},
    {"canonical_prior": True, "column_layout": ("irregular", "spread")},
]


_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EXACT_AXES = tuple(AXES)

# Exact joint geometry of every official input.  Colors are nuisance values and
# are redrawn, but canvas, ordered dimensions, starts, and bottom alignment are
# preserved.  These profiles make the demonstrated manifold a positive-measure
# part of the teaching distribution rather than four hard-coded color grids.
_CANONICAL_PROFILES = (
    (((4, 3), (2, 2), (2, 3)), (0, 4, 7)),
    (((3, 2), (2, 2), (2, 2), (4, 1)), (0, 3, 6, 9)),
    (((2, 4), (5, 1), (3, 3)), (0, 5, 7)),
    (((4, 1), (3, 2), (3, 1), (2, 2)), (0, 2, 5, 7)),
)

# Broader lawful witnesses.  Every profile has area >= 2 per rectangle,
# dimension diversity, a non-square rectangle, and enough width budget for a
# 3-column spread layout even at n=6.
_GENERAL_DIMENSION_PROFILES = {
    2: (
        ((2, 1), (2, 2)),
        ((3, 1), (2, 3)),
        ((4, 2), (2, 1)),
        ((3, 3), (2, 1)),
    ),
    3: (
        ((2, 1), (3, 2), (2, 3)),
        ((4, 1), (2, 2), (3, 1)),
        ((2, 4), (4, 1), (3, 2)),
        ((3, 2), (2, 1), (5, 2)),
    ),
    4: (
        ((2, 1), (3, 2), (2, 3), (4, 1)),
        ((4, 2), (2, 1), (3, 2), (2, 2)),
        ((3, 1), (5, 2), (2, 3), (4, 1)),
        ((2, 2), (4, 1), (3, 3), (2, 1)),
    ),
    5: (
        ((2, 1), (3, 2), (2, 3), (4, 1), (3, 2)),
        ((4, 2), (2, 1), (5, 2), (3, 3), (2, 1)),
        ((3, 1), (2, 2), (4, 1), (2, 3), (5, 2)),
        ((2, 3), (5, 1), (3, 2), (4, 1), (2, 2)),
    ),
    6: (
        ((2, 1), (3, 2), (2, 3), (4, 1), (3, 2), (2, 1)),
        ((4, 2), (2, 1), (5, 2), (3, 3), (2, 1), (4, 2)),
        ((3, 1), (2, 2), (4, 1), (2, 3), (5, 2), (3, 1)),
        ((2, 3), (5, 1), (3, 2), (4, 1), (2, 2), (3, 1)),
    ),
}


def _coerce_arc_grid(grid):
    """Return a mutable rectangular ARC grid or structural errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    errors = []
    if len(grid) > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30x30")
    result = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        result.append(converted)
    if errors:
        return None, errors
    return result, []


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _CARDINAL:
                    neighbor = (row + delta_row, col + delta_col)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _is_solid_rectangle(grid, component):
    top, left, bottom, right = component["bbox"]
    color = component["color"]
    area = (bottom - top + 1) * (right - left + 1)
    return (
        len(component["cells"]) == area
        and all(
            grid[row][col] == color
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        )
    )


def _ordered_rectangles(grid):
    components = _components(grid)
    if any(not _is_solid_rectangle(grid, component) for component in components):
        return None
    return sorted(components, key=lambda component: component["bbox"][1])


def _layout_signature(grid):
    """Recover exact semantic axes from a lawful returned input."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    rectangles = _ordered_rectangles(coerced)
    if not rectangles or len(rectangles) < 2:
        return None
    height = len(coerced)
    bottoms = [rectangle["bbox"][2] == height - 1 for rectangle in rectangles]
    if all(bottoms):
        row_layout = "bottom"
    elif any(bottoms):
        row_layout = "mixed"
    else:
        row_layout = "scattered"

    gaps = [
        right["bbox"][1] - left["bbox"][3] - 1
        for left, right in zip(rectangles, rectangles[1:])
    ]
    if any(gap < 1 for gap in gaps):
        return None
    if all(gap == 1 for gap in gaps):
        column_layout = "compact"
    elif all(gap >= 3 for gap in gaps):
        column_layout = "spread"
    else:
        column_layout = "irregular"

    dimensions = tuple(
        (
            rectangle["bbox"][2] - rectangle["bbox"][0] + 1,
            rectangle["bbox"][3] - rectangle["bbox"][1] + 1,
        )
        for rectangle in rectangles
    )
    colors = [rectangle["color"] for rectangle in rectangles]
    staircase_height = 1 + sum(rect_height - 1 for rect_height, _rect_width in dimensions)
    staircase_width = 1 + sum(rect_width - 1 for _rect_height, rect_width in dimensions)
    if (
        not 2 <= len(rectangles) <= 6
        or len(colors) != len(set(colors))
        or any(rect_height * rect_width < 2 for rect_height, rect_width in dimensions)
        or len(set(dimensions)) < 2
        or all(rect_height == rect_width for rect_height, rect_width in dimensions)
        or staircase_height > len(coerced)
        or staircase_width > len(coerced[0])
    ):
        return None
    starts = tuple(rectangle["bbox"][1] for rectangle in rectangles)
    canonical_prior = (
        len(coerced) == 10
        and len(coerced[0]) == 10
        and row_layout == "bottom"
        and column_layout == "compact"
        and (dimensions, starts) in _CANONICAL_PROFILES
    )
    return {
        "canonical_prior": canonical_prior,
        "n_objects": len(rectangles),
        "row_layout": row_layout,
        "column_layout": column_layout,
    }


def observe_overrides(grid):
    """Recover every declared exact axis from a lawful generated grid."""
    return _layout_signature(grid) or {}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed, ambiguous, degenerate, and rule-hiding inputs."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    assert coerced is not None
    height = len(coerced)
    width = len(coerced[0])
    rectangles = _ordered_rectangles(coerced)
    if rectangles is None:
        return ["every nonzero component must be a solid monochrome rectangle"]

    messages = []
    if not 2 <= len(rectangles) <= 6:
        messages.append("expected 2..6 nonzero rectangular objects")
    colors = [rectangle["color"] for rectangle in rectangles]
    if len(colors) != len(set(colors)):
        messages.append("object colors must be distinct")

    dimensions = []
    for rectangle in rectangles:
        top, left, bottom, right = rectangle["bbox"]
        rect_height = bottom - top + 1
        rect_width = right - left + 1
        dimensions.append((rect_height, rect_width))
        if rect_height * rect_width < 2:
            messages.append("1x1 objects are not lawful teaching witnesses")
            break
    if rectangles and len(set(dimensions)) < 2:
        messages.append("at least two rectangle dimensions must differ")
    if rectangles and all(rect_height == rect_width for rect_height, rect_width in dimensions):
        messages.append("at least one rectangle must be non-square")

    for left, right in zip(rectangles, rectangles[1:]):
        gap = right["bbox"][1] - left["bbox"][3] - 1
        if gap < 1:
            messages.append("neighboring rectangle bboxes need a blank separator column")
            break

    staircase_row = 0
    staircase_col = 0
    for rect_height, rect_width in dimensions:
        if staircase_row + rect_height > height or staircase_col + rect_width > width:
            messages.append("the canonical corner-overlap staircase would overflow the canvas")
            break
        staircase_row += rect_height - 1
        staircase_col += rect_width - 1

    observed = _layout_signature(coerced)
    if observed is None:
        messages.append("could not recover the declared layout axes")
    elif meta:
        requested = meta.get("overrides", meta) if isinstance(meta, dict) else {}
        if isinstance(requested, dict):
            for axis in _EXACT_AXES:
                if axis in requested and requested[axis] is not None:
                    if observed.get(axis) != requested[axis]:
                        messages.append(
                            f"override {axis}={requested[axis]!r} realized as "
                            f"{observed.get(axis)!r}"
                        )
    return messages


def _staircase_output(grid, *, later_owns_corner):
    """Return the task transformation under one explicit overlap policy.

    This helper is intentionally separate from production generation.  It is
    used only for executable semantic rivals and focused review tests.
    """
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    assert coerced is not None
    rectangles = _ordered_rectangles(coerced)
    if not rectangles:
        return None

    output = full_grid(len(coerced), len(coerced[0]), 0)
    staircase_row = 0
    staircase_col = 0
    for rectangle in rectangles:
        top, left, bottom, right = rectangle["bbox"]
        rect_height = bottom - top + 1
        rect_width = right - left + 1
        if (
            staircase_row + rect_height > len(output)
            or staircase_col + rect_width > len(output[0])
        ):
            return None
        for row in range(staircase_row, staircase_row + rect_height):
            for col in range(staircase_col, staircase_col + rect_width):
                if later_owns_corner or output[row][col] == 0:
                    output[row][col] = rectangle["color"]
        staircase_row += rect_height - 1
        staircase_col += rect_width - 1
    return output


def _earlier_corner_owner(grid):
    """Plausible wrong rule: keep the earlier rectangle at shared corners."""
    return _staircase_output(grid, later_owns_corner=False)


def _shared_corner_ownership_witness(grid):
    """Does this lawful input expose which rectangle owns each overlap?"""
    if self_check(grid):
        return False
    canonical = _staircase_output(grid, later_owns_corner=True)
    rival = _earlier_corner_owner(grid)
    return canonical is not None and rival is not None and canonical != rival


# Assigned repairs must carry an executable teaching contract, not only a
# structural validator.  Every lawful input has at least two distinct-colored
# rectangles and therefore exposes the corner-ownership branch.
strict_canonical_like = self_check
SEMANTIC_WITNESSES = {
    "shared_corner_ownership": _shared_corner_ownership_witness,
}
SEMANTIC_RIVALS = {
    "earlier_corner_owner": _earlier_corner_owner,
}
WITNESS_RIVALS = {
    "shared_corner_ownership": ["earlier_corner_owner"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _validate_override_values(overrides):
    """Reject malformed exact controls before they reach ``gen_ctx``.

    ``gen_ctx`` intentionally accepts a broad set of JSON-like scalar values.
    This generator's declared axes are narrower: exact Boolean, exact integer,
    and finite string enums.  Failing here keeps caller mistakes from surfacing
    later as internal self-check assertions.
    """
    value = overrides.get("canonical_prior")
    if value is not None and type(value) is not bool:
        raise ValueError("canonical_prior must be a literal bool")

    value = overrides.get("n_objects")
    if value is not None and (type(value) is not int or not 2 <= value <= 6):
        raise ValueError("n_objects must be a literal integer in 2..6")

    value = overrides.get("row_layout")
    if value is not None and (type(value) is not str or value not in ROW_LAYOUTS):
        raise ValueError(
            "row_layout must be one of " + "|".join(ROW_LAYOUTS)
        )

    value = overrides.get("column_layout")
    if value is not None and (
        type(value) is not str or value not in COLUMN_LAYOUTS
    ):
        raise ValueError(
            "column_layout must be one of " + "|".join(COLUMN_LAYOUTS)
        )

    if overrides.get("canonical_prior") is True:
        n_objects = overrides.get("n_objects")
        if n_objects in (2, 5, 6):
            raise ValueError(
                "incompatible overrides canonical_prior=True and "
                f"n_objects={n_objects}"
            )
        row_layout = overrides.get("row_layout")
        if row_layout in ("mixed", "scattered"):
            raise ValueError(
                "incompatible overrides canonical_prior=True and "
                f"row_layout={row_layout!r}"
            )
        column_layout = overrides.get("column_layout")
        if column_layout in ("irregular", "spread"):
            raise ValueError(
                "incompatible overrides canonical_prior=True and "
                f"column_layout={column_layout!r}"
            )


def _draw_axis_choice(ctx, overrides, label, default_options, valid_options):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, list(valid_options))
    return ctx.draw_choice(label, list(default_options))


def _draw_object_count(ctx, overrides, band):
    if overrides.get("n_objects") is not None:
        return ctx.draw_int("n_objects", 2, 6)
    if band == "easy":
        return ctx.draw_int("n_objects", 2, 3)
    if band == "hard":
        return ctx.draw_int("n_objects", 4, 6)
    return ctx.draw_int("n_objects", 3, 4)


def _draw_generalized(ctx, overrides, band):
    n_objects = _draw_object_count(ctx, overrides, band)
    if band == "easy":
        row_defaults = ("bottom", "bottom", "mixed")
        column_defaults = ("compact", "compact", "irregular")
        height_range = (7, 11)
        width_range = (8, 13)
    elif band == "hard":
        row_defaults = ("mixed", "scattered", "scattered", "bottom")
        column_defaults = ("irregular", "spread", "spread")
        height_range = (14, 24)
        width_range = (14, 30)
    else:
        row_defaults = ("bottom", "mixed", "scattered")
        column_defaults = ("compact", "irregular", "spread")
        height_range = (10, 17)
        width_range = (10, 22)

    row_layout = _draw_axis_choice(
        ctx, overrides, "row_layout", row_defaults, ROW_LAYOUTS
    )
    column_layout = _draw_axis_choice(
        ctx, overrides, "column_layout", column_defaults, COLUMN_LAYOUTS
    )

    profiles = _GENERAL_DIMENSION_PROFILES[n_objects]
    profile_index = ctx.draw_int("dimension_profile", 0, len(profiles) - 1)
    dimensions = profiles[profile_index]

    if column_layout == "compact":
        gaps = [1] * (n_objects - 1)
    elif column_layout == "spread":
        gaps = [3] * (n_objects - 1)
    else:
        gaps = [1] * (n_objects - 1)
        irregular_index = ctx.draw_int("irregular_gap_index", 0, n_objects - 2)
        gaps[irregular_index] = 2

    content_width = sum(rect_width for _rect_height, rect_width in dimensions) + sum(gaps)
    staircase_height = 1 + sum(rect_height - 1 for rect_height, _rect_width in dimensions)
    staircase_width = 1 + sum(rect_width - 1 for _rect_height, rect_width in dimensions)
    need_nonbottom = row_layout != "bottom"
    minimum_height = max(
        staircase_height,
        max(rect_height for rect_height, _rect_width in dimensions) + int(need_nonbottom),
    )
    height_low = max(height_range[0], minimum_height)
    height_high = max(height_low, min(30, height_range[1]))
    height = ctx.draw_int("canvas_height", height_low, height_high)

    minimum_width = max(content_width, staircase_width, width_range[0])
    width_high = max(minimum_width, min(30, width_range[1]))
    if minimum_width > 30:
        raise ValueError(
            f"generalized profile needs width {minimum_width}, exceeding ARC 30"
        )
    width = ctx.draw_int("canvas_width", minimum_width, width_high)
    left_padding = ctx.draw_int("left_padding", 0, width - content_width)

    starts = []
    cursor = left_padding
    for index, (_rect_height, rect_width) in enumerate(dimensions):
        starts.append(cursor)
        if index < len(gaps):
            cursor += rect_width + gaps[index]

    if row_layout == "bottom":
        rows = [height - rect_height for rect_height, _rect_width in dimensions]
    else:
        bottom_index = (
            ctx.draw_int("bottom_object_index", 0, n_objects - 1)
            if row_layout == "mixed"
            else None
        )
        rows = []
        for index, (rect_height, _rect_width) in enumerate(dimensions):
            if index == bottom_index:
                rows.append(height - rect_height)
            else:
                rows.append(
                    ctx.draw_int(
                        f"object_{index}_row",
                        0,
                        height - rect_height - 1,
                    )
                )

    colors = ctx.draw_distinct_colors(
        "object_colors", n=n_objects, exclude={0}
    )
    grid = full_grid(height, width, 0)
    for row, col, (rect_height, rect_width), color in zip(
        rows, starts, dimensions, colors
    ):
        draw_rect(grid, row, col, rect_height, rect_width, color)
    return grid


def _draw_canonical(ctx, overrides):
    requested_n = overrides.get("n_objects")
    profiles = (
        tuple(
            profile
            for profile in _CANONICAL_PROFILES
            if len(profile[0]) == requested_n
        )
        if requested_n is not None
        else _CANONICAL_PROFILES
    )
    if not profiles:
        raise ValueError(
            "incompatible overrides canonical_prior=True and "
            f"n_objects={requested_n}"
        )
    profile_index = ctx.draw_int("canonical_profile", 0, len(profiles) - 1)
    dimensions, starts = profiles[profile_index]
    n_objects = len(dimensions)
    recorded_n = ctx.draw_int("n_objects", n_objects, n_objects)
    if recorded_n != n_objects:
        raise AssertionError("unreachable object-count mismatch")
    ctx.draw_choice("row_layout", ["bottom"])
    ctx.draw_choice("column_layout", ["compact"])

    colors = ctx.draw_distinct_colors(
        "object_colors", n=n_objects, exclude={0}
    )
    grid = full_grid(10, 10, 0)
    for col, (rect_height, rect_width), color in zip(starts, dimensions, colors):
        draw_rect(grid, 10 - rect_height, col, rect_height, rect_width, color)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; explicit axes are exact-or-loud."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    _validate_override_values(overrides)
    if difficulty is not None and type(difficulty) is not str:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    band = difficulty or "medium"
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    explicit_general_axis = any(
        overrides.get(axis) is not None
        for axis in ("n_objects", "row_layout", "column_layout")
    )
    if overrides.get("canonical_prior") is not None:
        canonical_prior = ctx.draw_choice("canonical_prior", [False, True])
    elif explicit_general_axis:
        # A singleton exact override must remain accepted in every band.  It
        # therefore bypasses the empirical prior unless canonical_prior=True is
        # itself explicit; incompatible explicit combinations reject below.
        canonical_prior = ctx.draw_choice("canonical_prior", [False])
    else:
        canonical_prior = ctx.draw_choice(
            "canonical_prior", [False] * 7 + [True] * 3
        )

    grid = (
        _draw_canonical(ctx, overrides)
        if canonical_prior
        else _draw_generalized(ctx, overrides, band)
    )
    errors = self_check(
        grid,
        difficulty=band,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
