"""Generator for ARC task ``86af5978a32a``.

The input is two equal square panels composed horizontally or vertically.  The
panel with multiple nonzero colors is a layout; the panel with one nonzero
color is a binary shape mask.  Every nonzero layout cell places a recolored
copy of the mask into the corresponding block of a ``k² × k²`` output.

The public demonstrations always use color 8 in the shape panel, so
``fixed_eight_shape`` is a real canonical-fitting shortcut.  Ordinary lessons
therefore alternate which semantic role owns color 8 and also cross both panel
orders and both composition orientations.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "86af5978a32a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "80100e676959"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Compose two equal 3..5 square panels horizontally or vertically. The "
    "panel with 2..4 nonzero colors is a layout and the one-color panel is a "
    "shape mask. Expand each nonzero layout cell into a recolored copy of the "
    "mask. A four-step teaching schedule crosses orientation, panel order, "
    "and whether color 8 belongs to the shape or the layout."
)

INVARIANTS = [
    "the input is exactly two equal square panels of side 3..5",
    "one panel has 2..4 nonzero layout colors and the other exactly one shape color",
    "layout and shape palettes are disjoint and each panel retains background cells",
    "both panels span at least two rows and two columns",
    "color 8 occurs in exactly one panel, but alternates between the semantic roles",
    "every default four-step profile has an exact canonical dimension/palette profile",
]

AXES = {
    "half_size": {
        "type": "int",
        "default": "four-step canonical-profile schedule",
        "valid": "3..5",
    },
    "orientation": {
        "type": "str",
        "default": "four-step horizontal|vertical schedule",
        "valid": "horizontal|vertical",
    },
    "layout_position": {
        "type": "str",
        "default": "four-step first|second schedule",
        "valid": "first|second",
    },
    "n_layout_colors": {
        "type": "int",
        "default": "four-step canonical-palette schedule",
        "valid": "2..4",
    },
    "color_role": {
        "type": "str",
        "default": "four-step shape_is_8|layout_has_8 teaching schedule",
        "valid": "shape_is_8|layout_has_8",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

SCHEDULE_PROFILES = (0, 1, 2, 3)
_PROFILE_SCHEDULE = (
    {
        "half_size": 3,
        "orientation": "horizontal",
        "layout_position": "first",
        "n_layout_colors": 3,
        "color_role": "layout_has_8",
    },
    {
        "half_size": 4,
        "orientation": "vertical",
        "layout_position": "second",
        "n_layout_colors": 3,
        "color_role": "shape_is_8",
    },
    {
        "half_size": 4,
        "orientation": "horizontal",
        "layout_position": "second",
        "n_layout_colors": 2,
        "color_role": "shape_is_8",
    },
    {
        "half_size": 4,
        "orientation": "vertical",
        "layout_position": "first",
        "n_layout_colors": 3,
        "color_role": "layout_has_8",
    },
)
_ALLOWED_DIFFICULTIES = frozenset(("easy", "medium", "hard"))
_ALLOWED_OVERRIDES = frozenset(AXES)
_ORIENTATIONS = ("horizontal", "vertical")
_LAYOUT_POSITIONS = ("first", "second")
_COLOR_ROLES = ("shape_is_8", "layout_has_8")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the deterministic four-step curriculum residue."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    return sample_index % len(SCHEDULE_PROFILES)


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    if difficulty is None:
        band = "medium"
    elif type(difficulty) is str and difficulty in _ALLOWED_DIFFICULTIES:
        band = difficulty
    else:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    for name, lo, hi in (("half_size", 3, 5), ("n_layout_colors", 2, 4)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    for name, domain in (
        ("orientation", _ORIENTATIONS),
        ("layout_position", _LAYOUT_POSITIONS),
        ("color_role", _COLOR_ROLES),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        if value not in domain:
            raise ValueError(f"{name} must be one of {domain}")
    return band


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _draw_scheduled_choice(
    ctx,
    name: str,
    domain: Sequence[Any],
    scheduled: Any,
) -> Any:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, tuple(domain))
    return ctx.draw_choice(name, (scheduled,))


def _count_bounds(kind: str, band: str, k: int, n_layout_colors: int) -> tuple[int, int]:
    maximum = k * k - 1
    if kind == "layout":
        if band == "easy":
            return n_layout_colors, min(maximum, n_layout_colors + 1)
        if band == "hard":
            return min(maximum, max(n_layout_colors, k + 1)), maximum
        return n_layout_colors, min(maximum, n_layout_colors + k)
    if band == "easy":
        return 3, min(maximum, 4)
    if band == "hard":
        return min(maximum, k + 1), maximum
    return 3, min(maximum, k + 2)


def _spanning_positions(k: int, count: int, rng, *, three_point: bool) -> list[tuple[int, int]]:
    """Choose distinct cells while guaranteeing two-row/two-column support."""
    rows = rng.sample(range(k), 2)
    cols = rng.sample(range(k), 2)
    if three_point:
        mandatory = [
            (rows[0], cols[0]),
            (rows[0], cols[1]),
            (rows[1], cols[0]),
        ]
    else:
        mandatory = [(rows[0], cols[0]), (rows[1], cols[1])]
    candidates = [
        (row, col)
        for row in range(k)
        for col in range(k)
        if (row, col) not in mandatory
    ]
    rng.shuffle(candidates)
    return mandatory + candidates[: count - len(mandatory)]


def _draw_palette(ctx, n_layout_colors: int, color_role: str) -> tuple[list[int], int]:
    if color_role == "shape_is_8":
        layout_colors = list(
            ctx.draw_distinct_colors(
                "layout_palette",
                n=n_layout_colors,
                exclude={0, 8},
            )
        )
        return layout_colors, 8

    shape_color = ctx.draw_color("shape_color", exclude={0, 8})
    other_layout = list(
        ctx.draw_distinct_colors(
            "layout_palette_without_8",
            n=n_layout_colors - 1,
            exclude={0, 8, shape_color},
        )
    )
    layout_colors = [8, *other_layout]
    ctx.draw_rng("layout_palette_order").shuffle(layout_colors)
    return layout_colors, shape_color


def _make_panels(
    ctx,
    *,
    band: str,
    k: int,
    n_layout_colors: int,
    color_role: str,
) -> tuple[list[list[int]], list[list[int]]]:
    layout_colors, shape_color = _draw_palette(ctx, n_layout_colors, color_role)

    layout_lo, layout_hi = _count_bounds("layout", band, k, n_layout_colors)
    shape_lo, shape_hi = _count_bounds("shape", band, k, n_layout_colors)
    layout_count = ctx.draw_rng("layout_count").randint(layout_lo, layout_hi)
    shape_count = ctx.draw_rng("shape_count").randint(shape_lo, shape_hi)

    layout_positions = _spanning_positions(
        k,
        layout_count,
        ctx.draw_rng("layout_positions"),
        three_point=layout_count >= 3,
    )
    shape_positions = _spanning_positions(
        k,
        shape_count,
        ctx.draw_rng("shape_positions"),
        three_point=True,
    )

    layout = [[0 for _ in range(k)] for _ in range(k)]
    assignment_rng = ctx.draw_rng("layout_color_assignment")
    assignment = list(layout_colors)
    assignment_rng.shuffle(assignment)
    for index, (row, col) in enumerate(layout_positions):
        color = assignment[index] if index < len(assignment) else assignment_rng.choice(layout_colors)
        layout[row][col] = color

    shape = [[0 for _ in range(k)] for _ in range(k)]
    for row, col in shape_positions:
        shape[row][col] = shape_color
    return layout, shape


def _compose(
    first: list[list[int]],
    second: list[list[int]],
    orientation: str,
) -> list[list[int]]:
    if orientation == "horizontal":
        return [list(left) + list(right) for left, right in zip(first, second)]
    return [list(row) for row in first] + [list(row) for row in second]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful, exact-axis, shortcut-resistant input grid."""
    band = _validate_call(seed, sample_index, difficulty, overrides)
    profile_index = schedule_profile(seed, sample_index, difficulty=band)
    scheduled = _PROFILE_SCHEDULE[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    k = _draw_scheduled_int(
        ctx,
        "half_size",
        3,
        5,
        int(scheduled["half_size"]),
    )
    orientation = _draw_scheduled_choice(
        ctx,
        "orientation",
        _ORIENTATIONS,
        scheduled["orientation"],
    )
    layout_position = _draw_scheduled_choice(
        ctx,
        "layout_position",
        _LAYOUT_POSITIONS,
        scheduled["layout_position"],
    )
    n_layout_colors = _draw_scheduled_int(
        ctx,
        "n_layout_colors",
        2,
        4,
        int(scheduled["n_layout_colors"]),
    )
    color_role = _draw_scheduled_choice(
        ctx,
        "color_role",
        _COLOR_ROLES,
        scheduled["color_role"],
    )

    layout, shape = _make_panels(
        ctx,
        band=band,
        k=k,
        n_layout_colors=n_layout_colors,
        color_role=color_role,
    )
    first, second = (layout, shape) if layout_position == "first" else (shape, layout)
    grid = _compose(first, second, orientation)

    expected = {
        "half_size": k,
        "orientation": orientation,
        "layout_position": layout_position,
        "n_layout_colors": n_layout_colors,
        "color_role": color_role,
    }
    observed = observe_overrides(grid)
    if observed != expected:  # pragma: no cover - fail-loud construction guard
        raise RuntimeError(
            f"generated scene lost exact axes: expected {expected}, observed {observed}"
        )
    errors = self_check(grid)
    if errors:  # pragma: no cover - fail-loud construction guard
        raise RuntimeError("generated invalid layout/shape scene: " + "; ".join(errors))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int:
                return ["cells must be literal ARC integers (not bool)"]
            if not 0 <= value <= 9:
                return ["cell values must lie in 0..9"]
    return []


def _split_geometry(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0])
    if width == 2 * height:
        k = height
        first = [list(row[:k]) for row in grid]
        second = [list(row[k:]) for row in grid]
        orientation = "horizontal"
    elif height == 2 * width:
        k = width
        first = [list(row) for row in grid[:k]]
        second = [list(row) for row in grid[k:]]
        orientation = "vertical"
    else:
        raise ValueError(
            f"input must be two equal square halves; found {height}x{width}"
        )
    return {
        "height": height,
        "width": width,
        "half_size": k,
        "orientation": orientation,
        "first": first,
        "second": second,
    }


def _nonzero_colors(panel: Sequence[Sequence[int]]) -> set[int]:
    return {value for row in panel for value in row if value != 0}


def _nonzero_positions(panel: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    ]


def _spans_two_axes(positions: Sequence[tuple[int, int]]) -> bool:
    return (
        len({row for row, _ in positions}) >= 2
        and len({col for _, col in positions}) >= 2
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    try:
        scene = _split_geometry(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    k = scene["half_size"]
    if not 3 <= k <= 5:
        errors.append(f"half size must be in 3..5, found {k}")

    first = scene["first"]
    second = scene["second"]
    first_colors = _nonzero_colors(first)
    second_colors = _nonzero_colors(second)
    scene["first_colors"] = first_colors
    scene["second_colors"] = second_colors

    if 2 <= len(first_colors) <= 4 and len(second_colors) == 1:
        layout_position = "first"
        layout, shape = first, second
        layout_colors, shape_colors = first_colors, second_colors
    elif 2 <= len(second_colors) <= 4 and len(first_colors) == 1:
        layout_position = "second"
        layout, shape = second, first
        layout_colors, shape_colors = second_colors, first_colors
    else:
        errors.append(
            "one half must have 2..4 nonzero colors and the other exactly one; "
            f"found {len(first_colors)} and {len(second_colors)}"
        )
        scene["errors"] = errors
        return scene

    scene.update(
        {
            "layout_position": layout_position,
            "layout": layout,
            "shape": shape,
            "layout_colors": layout_colors,
            "shape_colors": shape_colors,
            "n_layout_colors": len(layout_colors),
            "shape_color": next(iter(shape_colors)),
        }
    )

    overlap = layout_colors & shape_colors
    if overlap:
        errors.append(f"layout and shape palettes must be disjoint; overlap={sorted(overlap)}")

    eight_sides = int(8 in first_colors) + int(8 in second_colors)
    if eight_sides != 1:
        errors.append(f"color 8 must occur in exactly one half, found {eight_sides}")
    elif 8 in shape_colors:
        scene["color_role"] = "shape_is_8"
    else:
        scene["color_role"] = "layout_has_8"

    layout_positions = _nonzero_positions(layout)
    shape_positions = _nonzero_positions(shape)
    scene["layout_positions"] = layout_positions
    scene["shape_positions"] = shape_positions

    if len(layout_positions) >= k * k:
        errors.append("layout half must retain at least one background cell")
    if len(shape_positions) < 3:
        errors.append("shape mask must contain at least three cells")
    if len(shape_positions) >= k * k:
        errors.append("shape half must retain at least one background cell")
    if not _spans_two_axes(layout_positions):
        errors.append("layout anchors must span at least two rows and two columns")
    if not _spans_two_axes(shape_positions):
        errors.append("shape mask must span at least two rows and two columns")

    scene["errors"] = errors
    return scene


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete declared layout/shape input grammar."""
    del difficulty, meta
    return list(_analysis(grid).get("errors", ()))


def strict_canonical_like(grid) -> list[str]:
    """Generated and canonical inputs share the same exact structural grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from returned pixels."""
    scene = _analysis(grid)
    if scene.get("errors"):
        raise ValueError("; ".join(scene["errors"]))
    return {
        "half_size": scene["half_size"],
        "orientation": scene["orientation"],
        "layout_position": scene["layout_position"],
        "n_layout_colors": scene["n_layout_colors"],
        "color_role": scene["color_role"],
    }


def _stamp(layout: Sequence[Sequence[int]], shape: Sequence[Sequence[int]]) -> list[list[int]]:
    k = len(layout)
    mask = _nonzero_positions(shape)
    output = [[0 for _ in range(k * k)] for _ in range(k * k)]
    for layout_row in range(k):
        for layout_col in range(k):
            color = layout[layout_row][layout_col]
            if color == 0:
                continue
            for shape_row, shape_col in mask:
                output[layout_row * k + shape_row][layout_col * k + shape_col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python audit mirror of the selected Racket rule."""
    scene = _analysis(grid)
    if scene.get("errors"):
        raise ValueError("; ".join(scene["errors"]))
    return _stamp(scene["layout"], scene["shape"])


def _fixed_eight_shape(grid) -> list[list[int]]:
    geometry = _split_geometry(grid)
    first, second = geometry["first"], geometry["second"]
    first_has_eight = 8 in _nonzero_colors(first)
    second_has_eight = 8 in _nonzero_colors(second)
    if first_has_eight != second_has_eight:
        shape, layout = (first, second) if first_has_eight else (second, first)
        return _stamp(layout, shape)
    return rule_mirror(grid)


def _first_half_is_layout(grid) -> list[list[int]]:
    geometry = _split_geometry(grid)
    return _stamp(geometry["first"], geometry["second"])


def _horizontal_only(grid) -> list[list[int]]:
    geometry = _split_geometry(grid)
    if geometry["orientation"] == "horizontal":
        return rule_mirror(grid)
    return deepcopy(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "fixed_eight_shape": _fixed_eight_shape,
    "first_half_is_layout": _first_half_is_layout,
    "horizontal_only": _horizontal_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_eight_shape": _fixed_eight_shape}


def _lawful_scene(grid) -> dict[str, Any] | None:
    scene = _analysis(grid)
    return None if scene.get("errors") else scene


def _witness_eight_in_layout(grid) -> bool:
    scene = _lawful_scene(grid)
    return bool(
        scene
        and scene["color_role"] == "layout_has_8"
        and _fixed_eight_shape(grid) != rule_mirror(grid)
    )


def _witness_layout_is_second(grid) -> bool:
    scene = _lawful_scene(grid)
    return bool(
        scene
        and scene["layout_position"] == "second"
        and _first_half_is_layout(grid) != rule_mirror(grid)
    )


def _witness_vertical_composition(grid) -> bool:
    scene = _lawful_scene(grid)
    return bool(
        scene
        and scene["orientation"] == "vertical"
        and _horizontal_only(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "eight_in_layout": _witness_eight_in_layout,
    "layout_is_second": _witness_layout_is_second,
    "vertical_composition": _witness_vertical_composition,
}
WITNESS_RIVALS = {
    "eight_in_layout": ["fixed_eight_shape"],
    "layout_is_second": ["first_half_is_layout"],
    "vertical_composition": ["horizontal_only"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the teaching grammar: {errors[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output disagrees with the layout-times-shape rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons in which a declared plausible rival survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                errors.append(
                    f"competitor {name!r} fits every demo but changes the query"
                )
            else:
                errors.append(f"competitor {name!r} fits every demonstration")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked near misses that the semantic validator must reject."""
    good = generate(
        1701,
        0,
        half_size=4,
        orientation="horizontal",
        layout_position="first",
        n_layout_colors=3,
        color_role="layout_has_8",
    )
    blank = [[0 for _ in range(8)] for _ in range(4)]

    no_shape = deepcopy(good)
    for row in range(4):
        for col in range(4, 8):
            no_shape[row][col] = 0

    no_eight = deepcopy(good)
    replacement = next(
        color
        for color in range(1, 10)
        if color != 8 and all(color not in row for row in good)
    )
    for row in range(4):
        for col in range(8):
            if no_eight[row][col] == 8:
                no_eight[row][col] = replacement

    overlap = deepcopy(good)
    shape_color = next(value for row in overlap for value in row[4:] if value)
    layout_row, layout_col = next(
        (row, col)
        for row in range(4)
        for col in range(4)
        if overlap[row][col] != 0
    )
    overlap[layout_row][layout_col] = shape_color

    return [
        ("blank", blank),
        ("missing_shape", no_shape),
        ("missing_color_eight", no_eight),
        ("palette_overlap", overlap),
    ]
