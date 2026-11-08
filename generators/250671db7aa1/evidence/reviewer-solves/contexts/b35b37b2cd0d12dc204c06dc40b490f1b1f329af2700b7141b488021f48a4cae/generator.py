"""Generator for ARC task 250671db7aa1: reflect across a painted 5-axis.

A full row or column of color 5 is the reflection axis.  Every other
nonzero cell is preserved and copied to its mirror position across that axis.
The generated domain keeps source cells on one side so reflected destinations
are unambiguous, while deliberately covering both orientations, both source
sides, off-center axes, multiple colors, and disconnected source components.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "250671db7aa1"
TASK_ID = "250671db7aa1"
VERSION = "3.0.0"
RULE_HASH = "27bdc557ee50"
SUMMARY = "Reflect every nonzero non-5 source cell across the full painted 5-axis."
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4

INVARIANTS = [
    "background is color 0",
    "exactly one full row or full column of color 5 is the axis",
    "all non-axis colored cells lie strictly on one side of the axis",
    "all reflected destinations are in bounds and initially background",
    "reflection preserves original cells and their colors",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "7..14"},
    "orientation": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "vertical|horizontal",
    },
    "axis_bias": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "start|center|end",
    },
    "source_side": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "before|after",
    },
    "source_cells": {
        "type": "int",
        "default": "lesson-balanced",
        "valid": "4..8",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "lesson-balanced",
        "valid": "1..4",
    },
    "pattern": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "compact|split",
    },
}

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_AXIS_NAMES = frozenset(AXES)
_INTEGER_AXES = frozenset(
    {"grid_h", "grid_w", "source_cells", "n_distinct_colors"}
)
_SOURCE_COLORS = tuple(color for color in range(1, 10) if color != 5)

# Five consecutive generated pairs contain a complete four-slot cycle plus one
# repeated slot.  Therefore every single-pair query holdout leaves both axis
# orientations, both source directions, a multicolor example, a disconnected
# example, and an off-center example among the four demonstrations.
_LESSON_SCHEDULE = (
    {
        "grid_h": 9,
        "grid_w": 9,
        "orientation": "vertical",
        "axis_bias": "center",
        "source_side": "before",
        "source_cells": 4,
        "n_distinct_colors": 1,
        "pattern": "compact",
    },
    {
        "grid_h": 9,
        "grid_w": 9,
        "orientation": "horizontal",
        "axis_bias": "start",
        "source_side": "before",
        "source_cells": 5,
        "n_distinct_colors": 1,
        "pattern": "split",
    },
    {
        "orientation": "vertical",
        "axis_bias": "end",
        "source_side": "after",
        "source_cells": 7,
        "n_distinct_colors": 3,
        "pattern": "compact",
    },
    {
        "orientation": "horizontal",
        "axis_bias": "start",
        "source_side": "after",
        "source_cells": 6,
        "n_distinct_colors": 2,
        "pattern": "split",
    },
)


def _validate_call(difficulty, overrides: dict) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES and not isinstance(
        difficulty, (int, float)
    ):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - _AXIS_NAMES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for axis in sorted(_INTEGER_AXES & set(overrides)):
        value = overrides[axis]
        if value is not None and type(value) is not int:
            raise TypeError(f"{axis} override must be an integer (not bool)")


def _scheduled_overrides(sample_index: int, overrides: dict) -> dict:
    effective = dict(overrides)
    scheduled = _LESSON_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]
    for key, value in scheduled.items():
        effective.setdefault(key, value)
    return effective


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for nxt in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def _axis_groups(length: int) -> dict[str, tuple[int, ...]]:
    """Partition legal, reflectable axis coordinates into three exact groups."""
    legal = tuple(range(2, length - 2))
    if len(legal) < 3:
        raise ValueError(f"dimension {length} cannot realize three axis biases")
    midpoint = (length - 1) / 2
    center_distance = min(abs(index - midpoint) for index in legal)
    center = tuple(
        index for index in legal if abs(index - midpoint) == center_distance
    )
    start = tuple(index for index in legal if index < min(center))
    end = tuple(index for index in legal if index > max(center))
    if not start or not center or not end:
        raise ValueError(f"dimension {length} cannot realize all axis biases")
    return {"start": start, "center": center, "end": end}


def _axis_bias(length: int, index: int) -> str:
    for name, values in _axis_groups(length).items():
        if index in values:
            return name
    raise ValueError(f"axis coordinate {index} is outside the legal band")


def _allowed_source_cells(
    height: int,
    width: int,
    orientation: str,
    axis_index: int,
    source_side: str,
) -> set[tuple[int, int]]:
    dimension = width if orientation == "vertical" else height
    span = min(axis_index, dimension - 1 - axis_index)
    if source_side == "before":
        coordinates = range(axis_index - span, axis_index)
    elif source_side == "after":
        coordinates = range(axis_index + 1, axis_index + span + 1)
    else:
        raise ValueError(f"invalid source_side {source_side!r}")

    if orientation == "vertical":
        return {(row, col) for row in range(height) for col in coordinates}
    if orientation == "horizontal":
        return {(row, col) for row in coordinates for col in range(width)}
    raise ValueError(f"invalid orientation {orientation!r}")


def _reflection_offset(
    cell: tuple[int, int], orientation: str, axis_index: int
) -> int:
    row, col = cell
    coordinate = col if orientation == "vertical" else row
    return abs(coordinate - axis_index)


def _compact_cells(
    allowed: set[tuple[int, int]],
    count: int,
    orientation: str,
    axis_index: int,
    rng,
) -> list[tuple[int, int]]:
    if count > len(allowed):
        raise ValueError("compact source exceeds available capacity")
    for _ in range(256):
        chosen = {rng.choice(sorted(allowed))}
        while len(chosen) < count:
            frontier = sorted(
                nxt
                for row, col in chosen
                for nxt in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
                if nxt in allowed and nxt not in chosen
            )
            if not frontier:
                break
            chosen.add(rng.choice(frontier))
        if len(chosen) != count:
            continue
        if len({_reflection_offset(cell, orientation, axis_index) for cell in chosen}) < 2:
            continue
        return sorted(chosen)
    raise RuntimeError("failed to construct a compact source with multiple offsets")


def _split_cells(
    allowed: set[tuple[int, int]],
    count: int,
    orientation: str,
    axis_index: int,
    height: int,
    width: int,
    rng,
) -> list[tuple[int, int]]:
    if count > len(allowed):
        raise ValueError("split source exceeds available capacity")

    # Split along the dimension perpendicular to the axis, leaving one blank
    # separator band so the two sampled groups can never touch orthogonally.
    if orientation == "vertical":
        separator = height // 2
        group_a = sorted(cell for cell in allowed if cell[0] < separator)
        group_b = sorted(cell for cell in allowed if cell[0] > separator)
    else:
        separator = width // 2
        group_a = sorted(cell for cell in allowed if cell[1] < separator)
        group_b = sorted(cell for cell in allowed if cell[1] > separator)

    lower = max(1, count - len(group_b))
    upper = min(len(group_a), count - 1)
    if lower > upper:
        raise ValueError("split source has insufficient separated capacity")

    for _ in range(256):
        count_a = rng.randint(lower, upper)
        chosen = set(rng.sample(group_a, count_a))
        chosen.update(rng.sample(group_b, count - count_a))
        if len(_components(chosen)) < 2:
            continue
        if len({_reflection_offset(cell, orientation, axis_index) for cell in chosen}) < 2:
            continue
        return sorted(chosen)
    raise RuntimeError("failed to construct a split source with multiple offsets")


def _source_color_sequence(
    palette: tuple[int, ...], count: int, rng
) -> list[int]:
    if count < len(palette):
        raise ValueError("source cell count cannot be smaller than its palette")
    if len(palette) == 1:
        return [palette[0]] * count

    # Deliberately make one color dominant and every other color observable.
    colors = list(palette)
    colors.extend([palette[0]] * (count - len(palette)))
    rng.shuffle(colors)
    return colors


def _analyze(grid) -> tuple[list[str], dict]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], {}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be non-empty sequences"], {}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], {}

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 30 or not 7 <= width <= 30:
        errors.append("grid dimensions must be h=7..30 and w=7..30")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return errors + ["all cells must be integer ARC colors 0..9"], {}

    full_rows = [
        row for row in range(height) if all(grid[row][col] == 5 for col in range(width))
    ]
    full_cols = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(full_rows) + len(full_cols) != 1:
        errors.append(
            "expected exactly one full color-5 row or column; "
            f"found {len(full_rows)} row(s) and {len(full_cols)} column(s)"
        )
        return errors, {"grid_h": height, "grid_w": width}

    if full_cols:
        orientation = "vertical"
        axis_index = full_cols[0]
        outside_fives = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if col != axis_index and grid[row][col] == 5
        ]
    else:
        orientation = "horizontal"
        axis_index = full_rows[0]
        outside_fives = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if row != axis_index and grid[row][col] == 5
        ]
    if outside_fives:
        errors.append("color 5 may occur only on the full reflection axis")

    sources = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    if not sources:
        errors.append("at least one non-axis source cell is required")

    signed_offsets = []
    for row, col, _value in sources:
        coordinate = col if orientation == "vertical" else row
        signed_offsets.append(coordinate - axis_index)
    before = any(offset < 0 for offset in signed_offsets)
    after = any(offset > 0 for offset in signed_offsets)
    if before and after:
        errors.append("source cells must lie on exactly one side of the axis")
    source_side = "before" if before and not after else "after" if after and not before else None

    for row, col, _value in sources:
        mirror_row, mirror_col = row, col
        if orientation == "vertical":
            mirror_col = 2 * axis_index - col
        else:
            mirror_row = 2 * axis_index - row
        if not (0 <= mirror_row < height and 0 <= mirror_col < width):
            errors.append(
                f"source cell {(row, col)} reflects out of bounds to {(mirror_row, mirror_col)}"
            )
            continue
        if grid[mirror_row][mirror_col] != 0:
            errors.append(
                f"reflected destination {(mirror_row, mirror_col)} is not background"
            )

    facts = {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "axis_index": axis_index,
        "source_side": source_side,
        "sources": sources,
    }
    try:
        dimension = width if orientation == "vertical" else height
        facts["axis_bias"] = _axis_bias(dimension, axis_index)
    except ValueError as exc:
        errors.append(str(exc))
        facts["axis_bias"] = None

    if sources:
        source_coords = [(row, col) for row, col, _ in sources]
        facts.update(
            {
                "source_cells": len(sources),
                "n_distinct_colors": len({value for _, _, value in sources}),
                "pattern": "compact" if len(_components(source_coords)) == 1 else "split",
            }
        )
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject missing/ambiguous axes, no-op scenes, collisions, and two-sided inputs."""
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Generated scenes stay within a conservative, canonical-compatible grammar."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict:
    """Recover every declared exact axis from a lawful returned grid."""
    errors, facts = _analyze(grid)
    if errors:
        return {"grid_h": len(grid), "grid_w": len(grid[0]) if grid else 0}
    return {axis: facts[axis] for axis in AXES}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=_scheduled_overrides(sample_index, overrides),
    )

    height = ctx.draw_int_diff("grid_h", 7, 14)
    width = ctx.draw_int_diff("grid_w", 7, 14)
    orientation = ctx.draw_choice("orientation", ("vertical", "horizontal"))
    axis_bias = ctx.draw_choice("axis_bias", ("start", "center", "end"))
    source_side = ctx.draw_choice("source_side", ("before", "after"))
    source_cells = ctx.draw_int_diff("source_cells", 4, 8)
    n_colors = ctx.draw_int_diff("n_distinct_colors", 1, 4)
    pattern = ctx.draw_choice("pattern", ("compact", "split"))

    if n_colors > source_cells:
        raise ValueError(
            f"n_distinct_colors={n_colors} exceeds source_cells={source_cells}"
        )

    dimension = width if orientation == "vertical" else height
    axis_options = _axis_groups(dimension)[axis_bias]
    layout_rng = ctx.draw_rng("layout")
    axis_index = layout_rng.choice(axis_options)
    allowed = _allowed_source_cells(
        height, width, orientation, axis_index, source_side
    )
    if source_cells > len(allowed):
        raise ValueError(
            f"source_cells={source_cells} exceeds side capacity {len(allowed)}"
        )

    palette = ctx.draw_distinct_colors(
        "source_palette", n=n_colors, exclude={0, 5}
    )
    colors = _source_color_sequence(
        palette, source_cells, ctx.draw_rng("source_color_counts")
    )

    for _ in range(128):
        if pattern == "compact":
            positions = _compact_cells(
                allowed, source_cells, orientation, axis_index, layout_rng
            )
        else:
            positions = _split_cells(
                allowed,
                source_cells,
                orientation,
                axis_index,
                height,
                width,
                layout_rng,
            )
        shuffled = list(positions)
        layout_rng.shuffle(shuffled)
        grid = full_grid(height, width, 0)
        if orientation == "vertical":
            for row in range(height):
                grid[row][axis_index] = 5
        else:
            for col in range(width):
                grid[axis_index][col] = 5
        for (row, col), color in zip(shuffled, colors):
            grid[row][col] = color
        if not self_check(grid):
            return [list(row) for row in grid]

    raise RuntimeError("failed to construct a lawful painted-axis reflection scene")


def rule_mirror(grid):
    """Diagnostic Python oracle matching the selected Racket rule on this domain."""
    errors, facts = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    axis_index = facts["axis_index"]
    for row, col, value in facts["sources"]:
        mirror_row, mirror_col = row, col
        if facts["orientation"] == "vertical":
            mirror_col = 2 * axis_index - col
        else:
            mirror_row = 2 * axis_index - row
        output[mirror_row][mirror_col] = value
    return output


def _unchanged(grid):
    return [list(row) for row in grid]


def _mirror_selected(grid, predicate):
    errors, facts = _analyze(grid)
    if errors:
        return None
    output = [list(row) for row in grid]
    for row, col, value in facts["sources"]:
        if not predicate(row, col, value, facts):
            continue
        mirror_row, mirror_col = row, col
        if facts["orientation"] == "vertical":
            mirror_col = 2 * facts["axis_index"] - col
        else:
            mirror_row = 2 * facts["axis_index"] - row
        output[mirror_row][mirror_col] = value
    return output


def _rival_before_only(grid):
    return _mirror_selected(
        grid,
        lambda row, col, _value, facts: (
            col < facts["axis_index"]
            if facts["orientation"] == "vertical"
            else row < facts["axis_index"]
        ),
    )


def _rival_after_only(grid):
    return _mirror_selected(
        grid,
        lambda row, col, _value, facts: (
            col > facts["axis_index"]
            if facts["orientation"] == "vertical"
            else row > facts["axis_index"]
        ),
    )


def _rival_vertical_only(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    return rule_mirror(grid) if facts["orientation"] == "vertical" else _unchanged(grid)


def _rival_horizontal_only(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    return rule_mirror(grid) if facts["orientation"] == "horizontal" else _unchanged(grid)


def _rival_modal_color(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    counts = Counter(value for _, _, value in facts["sources"])
    modal = min(value for value, count in counts.items() if count == max(counts.values()))
    return _mirror_selected(
        grid, lambda _row, _col, value, _facts: value == modal
    )


def _rival_largest_component(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    coords = {(row, col) for row, col, _ in facts["sources"]}
    components = _components(coords)
    largest = max(
        components,
        key=lambda component: (len(component), tuple(sorted(component))),
    )
    return _mirror_selected(
        grid, lambda row, col, _value, _facts: (row, col) in largest
    )


def _rival_grid_center(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    output = [list(row) for row in grid]
    if facts["orientation"] == "vertical":
        center = facts["grid_w"] // 2
        for row, col, value in facts["sources"]:
            mirror_col = 2 * center - col
            if 0 <= mirror_col < facts["grid_w"]:
                output[row][mirror_col] = value
    else:
        center = facts["grid_h"] // 2
        for row, col, value in facts["sources"]:
            mirror_row = 2 * center - row
            if 0 <= mirror_row < facts["grid_h"]:
                output[mirror_row][col] = value
    return output


LESSON_COMPETITORS = {
    "reflect only from the lower-coordinate side": _rival_before_only,
    "reflect only from the higher-coordinate side": _rival_after_only,
    "reflect only across vertical axes": _rival_vertical_only,
    "reflect only across horizontal axes": _rival_horizontal_only,
    "reflect only the modal source color": _rival_modal_color,
    "reflect only the largest source component": _rival_largest_component,
    "reflect across the geometric center": _rival_grid_center,
}
_LESSON_COMPETITORS = LESSON_COMPETITORS


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration pair is required"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            return [f"demo {index} is off-grammar: {exc}"]
        if demo["output"] != expected:
            return [f"demo {index} output does not match painted-axis reflection"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    try:
        query_expected = rule_mirror(query["input"])
    except ValueError as exc:
        return [f"query is off-grammar: {exc}"]
    query_output = query.get("output", query_expected)
    if query_output != query_expected:
        reasons.append("query output does not match painted-axis reflection")

    for name, competitor in _LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_expected:
                reasons.append(
                    f"competing rule '{name}' fits every demo but changes the query answer"
                )
    return reasons


def _w_vertical_axis(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["orientation"] == "vertical"


def _w_horizontal_axis(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["orientation"] == "horizontal"


def _w_before_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["source_side"] == "before"


def _w_after_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["source_side"] == "after"


def _w_off_center_axis(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["axis_bias"] != "center"


def _w_multicolor_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["n_distinct_colors"] >= 2


def _w_split_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["pattern"] == "split"


def _w_multiple_offsets(grid) -> bool:
    errors, facts = _analyze(grid)
    if errors:
        return False
    return len(
        {
            _reflection_offset((row, col), facts["orientation"], facts["axis_index"])
            for row, col, _ in facts["sources"]
        }
    ) >= 2


def _w_strong_color_frequency_skew(grid) -> bool:
    errors, facts = _analyze(grid)
    if errors:
        return False
    counts = Counter(value for _, _, value in facts["sources"])
    return len(counts) >= 2 and max(counts.values()) - min(counts.values()) >= 2


SEMANTIC_WITNESSES = {
    "vertical_axis": _w_vertical_axis,
    "horizontal_axis": _w_horizontal_axis,
    "before_source": _w_before_source,
    "after_source": _w_after_source,
    "off_center_axis": _w_off_center_axis,
    "multicolor_source": _w_multicolor_source,
    "split_source": _w_split_source,
    "multiple_reflection_offsets": _w_multiple_offsets,
    "strong_color_frequency_skew": _w_strong_color_frequency_skew,
}

SEMANTIC_RIVALS = {
    "reflect only from the lower-coordinate side": _rival_before_only,
    "reflect only the modal source color": _rival_modal_color,
    "reflect only the largest source component": _rival_largest_component,
    "reflect across the geometric center": _rival_grid_center,
}
WITNESS_RIVALS = {
    "after_source": ["reflect only from the lower-coordinate side"],
    "multicolor_source": ["reflect only the modal source color"],
    "split_source": ["reflect only the largest source component"],
    "off_center_axis": ["reflect across the geometric center"],
}
BRANCH_WITNESSES = tuple(
    name for name in SEMANTIC_WITNESSES if name not in WITNESS_RIVALS
)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
