"""Generator for ARC task 4e16917b1bde: mirror across a divider bar.

A nonzero, full-height divider column is the reflection axis.  Every other
nonzero input cell lies on exactly one side of the divider.  The output keeps
all input cells and copies each source cell, preserving its color, to the
column reflected across the divider.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e16917b1bde"
TASK_ID = "4e16917b1bde"
VERSION = "2.1.0"
RULE_HASH = "de4ea202a020"
SUMMARY = "A full-height divider bar mirrors every colored source cell across its column."
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "exactly one uniform nonzero full-height divider column exists",
    "all non-divider colored cells lie strictly on one side of the divider",
    "every reflected destination is in bounds and initially background",
    "reflection preserves each source cell and its color",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "9..17"},
    "divider_color": {"type": "color", "default": "rng", "valid": "1..9"},
    "divider_bias": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "left|center|right",
    },
    "source_side": {
        "type": "str",
        "default": "lesson-balanced",
        "valid": "left|right",
    },
    "source_cells": {
        "type": "int",
        "default": "difficulty-aware",
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
    {"grid_h", "grid_w", "divider_color", "source_cells", "n_distinct_colors"}
)
_DIVIDER_COLORS = tuple(range(1, 10))

# The first four sequential samples deliberately demonstrate both directions,
# a centered and off-center axis, one- and multi-color sources, and compact and
# disconnected source geometry.  Callers' exact overrides always win.
_LESSON_SCHEDULE = (
    {"source_side": "left", "divider_bias": "center", "pattern": "compact", "n_distinct_colors": 1},
    {"source_side": "right", "divider_bias": "left", "pattern": "compact", "n_distinct_colors": 1},
    {"source_side": "left", "divider_bias": "right", "pattern": "split", "n_distinct_colors": 3, "source_cells": 6},
    {"source_side": "right", "divider_bias": "center", "pattern": "split", "n_distinct_colors": 2, "source_cells": 5},
    {"source_side": "left", "divider_bias": "left", "pattern": "compact", "n_distinct_colors": 4},
    {"source_side": "right", "divider_bias": "right", "pattern": "split", "n_distinct_colors": 2, "source_cells": 6},
    {"source_side": "left", "divider_bias": "center", "pattern": "compact", "n_distinct_colors": 3, "source_cells": 6},
    {"source_side": "right", "divider_bias": "left", "pattern": "split", "n_distinct_colors": 4},
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
    """Return exact teaching defaults without masking caller overrides.

    The two single-color lesson slots anchor the two canonical size profiles.
    Aligning size and color-count anchors guarantees exact canonical-profile
    support without erasing any shortcut-rebutting multicolor lesson.  A
    separate every-fifth divider-color anchor preserves frequent canonical
    color-role examples while the wider pool uses every lawful nonzero color.
    """
    effective = dict(overrides)
    lesson_slot = sample_index % len(_LESSON_SCHEDULE)
    scheduled = _LESSON_SCHEDULE[lesson_slot]
    for key, value in scheduled.items():
        effective.setdefault(key, value)
    if sample_index % 5 == 0:
        # Preserve frequent exact canonical color-role examples while allowing
        # all other nonzero colors to serve as the divider in the wider pool.
        effective.setdefault("divider_color", 5)
    if lesson_slot in (0, 1) and not (
        {"grid_h", "grid_w", "n_distinct_colors"} & set(overrides)
    ):
        profile = ((5, 9), (6, 10))[lesson_slot]
        effective["grid_h"], effective["grid_w"] = profile
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


def _divider_groups(width: int) -> dict[str, tuple[int, ...]]:
    legal = tuple(range(2, width - 2))
    midpoint = (width - 1) / 2
    center = tuple(col for col in legal if abs(col - midpoint) <= 0.5)
    left = tuple(col for col in legal if col < min(center))
    right = tuple(col for col in legal if col > max(center))
    if not left or not center or not right:
        raise ValueError(f"width {width} cannot realize all divider_bias values")
    return {"left": left, "center": center, "right": right}


def _divider_bias(width: int, divider_col: int) -> str:
    for name, cols in _divider_groups(width).items():
        if divider_col in cols:
            return name
    raise ValueError(f"divider column {divider_col} is outside the legal axis band")


def _source_columns(width: int, divider_col: int, side: str) -> tuple[int, ...]:
    span = min(divider_col, width - 1 - divider_col)
    if side == "left":
        return tuple(divider_col - offset for offset in range(1, span + 1))
    if side == "right":
        return tuple(divider_col + offset for offset in range(1, span + 1))
    raise ValueError(f"invalid source side {side!r}")


def _compact_cells(height: int, columns: tuple[int, ...], count: int, rng):
    allowed = {(row, col) for row in range(height) for col in columns}
    start = rng.choice(sorted(allowed))
    chosen = {start}
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
            raise ValueError("compact source growth exhausted its frontier")
        chosen.add(rng.choice(frontier))
    return sorted(chosen)


def _split_cells(height: int, columns: tuple[int, ...], count: int, rng):
    separator = height // 2
    top = [(row, col) for row in range(separator) for col in columns]
    bottom = [
        (row, col)
        for row in range(separator + 1, height)
        for col in columns
    ]
    lo_top = max(1, count - len(bottom))
    hi_top = min(len(top), count - 1)
    if lo_top > hi_top:
        raise ValueError("split pattern has insufficient separated capacity")
    n_top = rng.randint(lo_top, hi_top)
    return sorted(rng.sample(top, n_top) + rng.sample(bottom, count - n_top))


def _source_color_sequence(
    palette: tuple[int, ...], count: int, rng
) -> list[int]:
    """Use every source color and include real minority frequencies when possible.

    The previous round-robin assignment kept every color count within one of
    the modal count.  That made a plausible "ignore rare colors" shortcut
    indistinguishable from the intended rule over the entire generated pool.
    """
    if count < len(palette):
        raise ValueError("source cell count cannot be smaller than its palette")
    if len(palette) == 1:
        return [palette[0]] * count

    minimum_gap = 2 if count >= len(palette) + 2 else 1
    for _ in range(64):
        colors = list(palette)
        colors.extend(rng.choice(palette) for _ in range(count - len(palette)))
        counts = Counter(colors)
        if max(counts.values()) - min(counts.values()) >= minimum_gap:
            rng.shuffle(colors)
            return colors

    # Deterministic fallback for completeness; it meets the same gap whenever
    # the requested count makes that gap mathematically possible.
    colors = list(palette) + [palette[0]] * (count - len(palette))
    rng.shuffle(colors)
    return colors


def _analyze(grid) -> tuple[list[str], dict]:
    """Return structural errors plus recoverable semantic facts."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], {}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be non-empty sequences"], {}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], {}

    height = len(grid)
    errors: list[str] = []
    if not 3 <= height <= 30 or not 5 <= width <= 30:
        errors.append("grid dimensions must be h=3..30 and w=5..30")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                return errors, {}

    divider_cols = []
    for col in range(width):
        values = {grid[row][col] for row in range(height)}
        if len(values) == 1 and next(iter(values)) != 0:
            divider_cols.append(col)
    if len(divider_cols) != 1:
        errors.append(
            f"expected exactly one uniform nonzero full-height divider, found {len(divider_cols)}"
        )
        return errors, {"grid_h": height, "grid_w": width}

    divider_col = divider_cols[0]
    divider_color = grid[0][divider_col]
    sources = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if col != divider_col and grid[row][col] != 0
    ]
    if not sources:
        errors.append("at least one non-divider source cell is required")
    if any(value == divider_color for _, _, value in sources):
        errors.append("divider color may not occur outside the divider column")

    left = [(row, col, value) for row, col, value in sources if col < divider_col]
    right = [(row, col, value) for row, col, value in sources if col > divider_col]
    if left and right:
        errors.append("source cells must lie on exactly one side of the divider")
    source_side = "left" if left and not right else "right" if right and not left else None

    for row, col, _ in sources:
        reflected_col = 2 * divider_col - col
        if not 0 <= reflected_col < width:
            errors.append(
                f"source cell {(row, col)} reflects out of bounds to column {reflected_col}"
            )
            continue
        if grid[row][reflected_col] != 0:
            errors.append(
                f"reflected destination {(row, reflected_col)} is not background"
            )

    facts = {
        "grid_h": height,
        "grid_w": width,
        "divider_col": divider_col,
        "divider_color": divider_color,
        "source_side": source_side,
        "sources": sources,
    }
    if source_side is not None:
        source_coords = [(row, col) for row, col, _ in sources]
        facts.update(
            {
                "divider_bias": _divider_bias(width, divider_col)
                if 2 <= divider_col <= width - 3
                else None,
                "source_cells": len(sources),
                "n_distinct_colors": len({value for _, _, value in sources}),
                "pattern": "compact"
                if len(_components(source_coords)) == 1
                else "split",
            }
        )
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed axes, two-sided sources, collisions, and no-op scenes."""
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical task permits recoloring, resizing, and either source side."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict:
    """Recover every exact declared axis from a lawful returned grid."""
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

    height = ctx.draw_int_diff("grid_h", 5, 12)
    width = ctx.draw_int_diff("grid_w", 9, 17)
    divider_color = ctx.draw_color(
        "divider_color", exclude=set(range(10)) - set(_DIVIDER_COLORS)
    )
    divider_bias = ctx.draw_choice("divider_bias", ("left", "center", "right"))
    source_side = ctx.draw_choice("source_side", ("left", "right"))
    source_cells = ctx.draw_int_diff("source_cells", 4, 8)
    n_colors = ctx.draw_int_diff("n_distinct_colors", 1, 4)
    pattern = ctx.draw_choice("pattern", ("compact", "split"))

    if n_colors > source_cells:
        raise ValueError(
            f"n_distinct_colors={n_colors} exceeds source_cells={source_cells}"
        )

    rng = ctx.draw_rng("layout")
    palette = ctx.draw_distinct_colors(
        "source_palette", n=n_colors, exclude={0, divider_color}
    )
    source_colors = _source_color_sequence(
        palette, source_cells, ctx.draw_rng("source_color_counts")
    )
    divider_options = _divider_groups(width)[divider_bias]

    for _ in range(128):
        divider_col = rng.choice(divider_options)
        columns = _source_columns(width, divider_col, source_side)
        capacity = height * len(columns)
        if source_cells > capacity:
            raise ValueError(
                f"source_cells={source_cells} exceeds side capacity {capacity}"
            )
        if pattern == "compact":
            positions = _compact_cells(height, columns, source_cells, rng)
        else:
            positions = _split_cells(height, columns, source_cells, rng)

        ordered_positions = list(positions)
        rng.shuffle(ordered_positions)
        grid = full_grid(height, width, 0)
        for row in range(height):
            grid[row][divider_col] = divider_color
        for (row, col), color in zip(ordered_positions, source_colors):
            grid[row][col] = color

        if not self_check(grid):
            return [list(row) for row in grid]

    raise RuntimeError("failed to construct a lawful divider-mirror scene")


def rule_mirror(grid):
    """Diagnostic Python oracle used only by audits and lesson checks."""
    errors, facts = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    result = [list(row) for row in grid]
    divider_col = facts["divider_col"]
    for row, col, value in facts["sources"]:
        result[row][2 * divider_col - col] = value
    return result


def _mirror_selected(grid, predicate):
    errors, facts = _analyze(grid)
    if errors:
        return None
    result = [list(row) for row in grid]
    for row, col, value in facts["sources"]:
        if predicate(row, col, value, facts):
            result[row][2 * facts["divider_col"] - col] = value
    return result


def _competitor_left_only(grid):
    return _mirror_selected(grid, lambda _r, c, _v, f: c < f["divider_col"])


def _competitor_right_only(grid):
    return _mirror_selected(grid, lambda _r, c, _v, f: c > f["divider_col"])


def _competitor_modal_color(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    counts = Counter(value for _, _, value in facts["sources"])
    modal = min(value for value, count in counts.items() if count == max(counts.values()))
    return _mirror_selected(grid, lambda _r, _c, value, _f: value == modal)


def _competitor_common_colors(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    counts = Counter(value for _, _, value in facts["sources"])
    cutoff = max(counts.values()) - 1
    return _mirror_selected(
        grid, lambda _r, _c, value, _f: counts[value] >= cutoff
    )


def _competitor_largest_component(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    source_coords = {(row, col) for row, col, _ in facts["sources"]}
    components = _components(source_coords)
    largest = max(components, key=lambda component: (len(component), tuple(sorted(component))))
    return _mirror_selected(grid, lambda row, col, _v, _f: (row, col) in largest)


def _competitor_grid_center(grid):
    errors, facts = _analyze(grid)
    if errors:
        return None
    result = [list(row) for row in grid]
    width = facts["grid_w"]
    for row, col, value in facts["sources"]:
        reflected_col = width - 1 - col
        if 0 <= reflected_col < width:
            result[row][reflected_col] = value
    return result


LESSON_COMPETITORS = {
    "mirror left-to-right only": _competitor_left_only,
    "mirror right-to-left only": _competitor_right_only,
    "mirror only the modal source color": _competitor_modal_color,
    "mirror only colors within one count of the modal color": _competitor_common_colors,
    "mirror only the largest connected source component": _competitor_largest_component,
    "mirror across the geometric grid center": _competitor_grid_center,
}
_LESSON_COMPETITORS = LESSON_COMPETITORS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a documented shortcut survives every demo."""
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
            return [f"demo {index} output does not match divider reflection"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    try:
        query_expected = rule_mirror(query["input"])
    except ValueError as exc:
        return [f"query is off-grammar: {exc}"]
    query_output = query.get("output", query_expected)
    if query_output != query_expected:
        reasons.append("query output does not match divider reflection")

    for name, competitor in _LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_expected:
                reasons.append(
                    f"competing rule '{name}' fits every demo but changes the query answer"
                )
    return reasons


def _w_left_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["source_side"] == "left"


def _w_right_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["source_side"] == "right"


def _w_off_center_divider(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["divider_bias"] != "center"


def _w_multicolor_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["n_distinct_colors"] >= 2


def _w_split_source(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["pattern"] == "split"


def _w_multiple_offsets(grid) -> bool:
    errors, facts = _analyze(grid)
    if errors:
        return False
    divider_col = facts["divider_col"]
    return len({abs(col - divider_col) for _, col, _ in facts["sources"]}) >= 2


def _w_strong_color_frequency_skew(grid) -> bool:
    errors, facts = _analyze(grid)
    if errors:
        return False
    counts = Counter(value for _, _, value in facts["sources"])
    return len(counts) >= 2 and max(counts.values()) - min(counts.values()) >= 2


SEMANTIC_WITNESSES = {
    "left_source": _w_left_source,
    "right_source": _w_right_source,
    "off_center_divider": _w_off_center_divider,
    "multicolor_source": _w_multicolor_source,
    "split_source": _w_split_source,
    "multiple_reflection_offsets": _w_multiple_offsets,
    "strong_color_frequency_skew": _w_strong_color_frequency_skew,
}

# The public semantic contract distinguishes branch-coverage witnesses from a
# genuine generated counterexample.  The rival below fits every canonical
# example because each has only one source color, but fails whenever a lesson
# contains a source color at least two cells rarer than the modal color.
SEMANTIC_RIVALS = {
    "mirror only colors within one count of the modal color": _competitor_common_colors,
}
WITNESS_RIVALS = {
    "strong_color_frequency_skew": [
        "mirror only colors within one count of the modal color"
    ],
}
BRANCH_WITNESSES = tuple(
    name for name in SEMANTIC_WITNESSES if name not in WITNESS_RIVALS
)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
