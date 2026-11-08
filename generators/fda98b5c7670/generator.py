"""Generator for ``fda98b5c7670`` — a corner marker selects closure axis.

The cell at ``(0, 0)`` is a control marker, not part of the shape.  Marker 2
selects row closure and marker 3 selects column closure.  Every occupied line
is closed from its first to last non-marker cell and painted cyan (8) on a
blank output grid.

The ordinary schedule deliberately interleaves exact canonical anchors with
color-agnostic variants.  This keeps the training distribution tied to the
source puzzle while refuting marker-color and same-color-pair shortcuts.
"""
from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fda98b5c7670"
VERSION = "4.0.0"
TASK_ID = "fda98b5c7670"
RULE_HASH = "0c8b818049c0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A control marker at (0,0) selects the closure axis: 2 means close each "
    "occupied row and 3 means close each occupied column. Ignore the marker, "
    "then on a blank same-size grid paint color 8 from the first through last "
    "non-marker cell of every occupied line. Endpoint colors do not determine "
    "the output color. Ordinary draws include exact canonical-profile anchors "
    "and three disjoint color-agnostic variants."
)

INVARIANTS = [
    "(0,0) is marker 2 (row closure) or 3 (column closure)",
    "the marker's own row or column contains no other foreground cell",
    "there are 1..5 occupied lines and every line contains the same 2..4 points",
    "each occupied line spans at least one blank cell, so closure is nontrivial",
    "input never contains output color 8 and the output authority always paints 8",
]

PALETTE_KINDS = (
    "canonical",
    "single_blue",
    "single_yellow",
    "mixed",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled by difficulty; canonical roles use 8 or 9",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled by difficulty; canonical roles use 8, 9, or 10",
        "valid": "6..14",
    },
    "axis": {
        "type": "str",
        "default": "alternates row|col by sample_index",
        "valid": "row|col",
    },
    "n_lines": {
        "type": "int",
        "default": "1..2 easy / 2..3 medium / 3..5 hard; 2 in canonical roles",
        "valid": "1..5",
    },
    "points_per_line": {
        "type": "int",
        "default": "scheduled 2..4; 2 in canonical roles",
        "valid": "2..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "8-role schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}

_CANONICAL_PROFILES = ((8, 9), (9, 8), (8, 10))
_ALLOWED_ENDPOINT_COLORS = {1, 2, 3, 4, 5, 6}
SCHEDULE_PROFILES = (
    "canonical_row",
    "canonical_col",
    "single_blue_row",
    "single_blue_col",
    "single_yellow_row",
    "single_yellow_col",
    "mixed_row",
    "mixed_col",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic teaching role for semantic schedule audits."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_value(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    label: str,
    values: tuple[int, ...],
) -> int:
    """Choose a deterministic schedule value without touching process RNG."""
    digest = hashlib.sha256(
        f"{TASK_ID}|{VERSION}|{seed}|{sample_index}|{difficulty}|{label}".encode()
    ).digest()
    return values[int.from_bytes(digest[:8], "big") % len(values)]


def _lesson_defaults(
    seed: int, sample_index: int, difficulty: str | None
) -> dict[str, int | str]:
    role = sample_index % len(SCHEDULE_PROFILES)
    axis = "row" if role % 2 == 0 else "col"
    palette_kind = PALETTE_KINDS[role // 2]

    if palette_kind == "canonical":
        height, width = _CANONICAL_PROFILES[
            _scheduled_value(
                seed,
                sample_index,
                difficulty,
                "canonical_profile",
                tuple(range(len(_CANONICAL_PROFILES))),
            )
        ]
        return {
            "grid_h": height,
            "grid_w": width,
            "axis": axis,
            "n_lines": 2,
            "points_per_line": 2,
            "palette_kind": palette_kind,
        }

    if difficulty == "easy":
        heights = tuple(range(6, 10))
        widths = tuple(range(6, 10))
        line_counts = (1, 2)
    elif difficulty == "hard":
        heights = tuple(range(9, 15))
        widths = tuple(range(9, 15))
        line_counts = (3, 4, 5)
    else:
        heights = tuple(range(7, 12))
        widths = tuple(range(7, 12))
        line_counts = (2, 3)

    return {
        "grid_h": _scheduled_value(
            seed, sample_index, difficulty, "grid_h", heights
        ),
        "grid_w": _scheduled_value(
            seed, sample_index, difficulty, "grid_w", widths
        ),
        "axis": axis,
        "n_lines": _scheduled_value(
            seed, sample_index, difficulty, "n_lines", line_counts
        ),
        "points_per_line": _scheduled_value(
            seed, sample_index, difficulty, "points_per_line", (2, 3, 4)
        ),
        "palette_kind": palette_kind,
    }


def _line_positions(length: int, count: int, rng) -> list[int]:
    """Return exactly ``count`` positions with a nontrivial first/last span."""
    if not 2 <= count <= 4:
        raise ValueError(f"points_per_line must be 2..4, got {count}")
    if length < count + 1:
        raise ValueError(
            f"line length {length} cannot hold {count} points plus a blank gap"
        )
    start = rng.randint(0, length - count - 1)
    end = rng.randint(start + count, length - 1)
    middle = list(range(start + 1, end))
    extras = rng.sample(middle, count - 2)
    return sorted([start, end, *extras])


def _colors_for_line(
    *, marker: int, palette_kind: str, count: int, line_number: int
) -> list[int]:
    del line_number
    if palette_kind == "canonical":
        return [marker] * count
    if palette_kind == "single_blue":
        return [1] * count
    if palette_kind == "single_yellow":
        return [4] * count
    if palette_kind == "mixed":
        # Every line contains both colors even at the minimum count of two.
        return [5 if index % 2 == 0 else 6 for index in range(count)]
    raise ValueError(f"unknown palette_kind {palette_kind!r}")


def _place_line(
    grid: list[list[int]],
    line_index: int,
    positions: list[int],
    colors: list[int],
    axis: str,
) -> None:
    for position, color in zip(positions, colors, strict=True):
        if axis == "row":
            grid[line_index][position] = color
        else:
            grid[position][line_index] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    effective_overrides = _lesson_defaults(seed, sample_index, difficulty)
    effective_overrides.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    height = ctx.draw_int("grid_h", 6, 14)
    width = ctx.draw_int("grid_w", 6, 14)
    axis = ctx.draw_choice("axis", ("row", "col"))
    n_lines = ctx.draw_int("n_lines", 1, 5)
    points_per_line = ctx.draw_int("points_per_line", 2, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    rng = ctx.draw_rng("layout")

    marker = 2 if axis == "row" else 3
    grid = full_grid(height, width, 0)
    grid[0][0] = marker

    if axis == "row":
        line_pool = list(range(1, height))
        line_length = width
    else:
        line_pool = list(range(1, width))
        line_length = height
    if n_lines > len(line_pool):
        raise ValueError(
            f"n_lines={n_lines} exceeds available {axis} lines={len(line_pool)}"
        )

    for line_number, line_index in enumerate(rng.sample(line_pool, n_lines)):
        positions = _line_positions(line_length, points_per_line, rng)
        colors = _colors_for_line(
            marker=marker,
            palette_kind=palette_kind,
            count=points_per_line,
            line_number=line_number,
        )
        _place_line(grid, line_index, positions, colors, axis)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _foreground_without_marker(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row_index, col_index, value)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 0 and (row_index, col_index) != (0, 0)
    ]


def _analyse(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("grid cells must be integer ARC colors 0..9")
                break
        if errors:
            break

    marker = grid[0][0]
    if marker not in (2, 3):
        errors.append("top-left cell must be marker 2 or 3")
        axis = None
    else:
        axis = "row" if marker == 2 else "col"

    cells = _foreground_without_marker(grid)
    if not cells:
        errors.append("at least one occupied non-marker line is required")

    if any(value == 8 for _, _, value in cells):
        errors.append("output color 8 must not occur in the input")
    if any(value not in _ALLOWED_ENDPOINT_COLORS for _, _, value in cells):
        errors.append("endpoint colors must be among 1..6, excluding output color 8")
    opposite_marker = 3 if marker == 2 else 2
    if marker in (2, 3) and any(value == opposite_marker for _, _, value in cells):
        errors.append("the opposite axis-marker color may not appear as an endpoint")

    line_rows: list[dict[str, Any]] = []
    if axis == "row":
        if any(value != 0 for value in grid[0][1:]):
            errors.append("row marker's own row must otherwise be background")
        grouped: dict[int, list[tuple[int, int]]] = {}
        for row_index, col_index, value in cells:
            grouped.setdefault(row_index, []).append((col_index, value))
        for row_index, entries in sorted(grouped.items()):
            positions = sorted(position for position, _ in entries)
            line_rows.append(
                {
                    "index": row_index,
                    "positions": positions,
                    "colors": [value for _, value in entries],
                }
            )
    elif axis == "col":
        if any(grid[row_index][0] != 0 for row_index in range(1, height)):
            errors.append("column marker's own column must otherwise be background")
        grouped = {}
        for row_index, col_index, value in cells:
            grouped.setdefault(col_index, []).append((row_index, value))
        for col_index, entries in sorted(grouped.items()):
            positions = sorted(position for position, _ in entries)
            line_rows.append(
                {
                    "index": col_index,
                    "positions": positions,
                    "colors": [value for _, value in entries],
                }
            )

    if not 1 <= len(line_rows) <= 5:
        errors.append(f"expected 1..5 occupied lines, found {len(line_rows)}")

    counts = [len(row["positions"]) for row in line_rows]
    if counts and len(set(counts)) != 1:
        errors.append("every occupied line must contain the same number of points")
    if any(not 2 <= count <= 4 for count in counts):
        errors.append("each occupied line must contain 2..4 points")
    for row in line_rows:
        positions = row["positions"]
        if len(positions) >= 2 and positions[-1] - positions[0] < len(positions):
            errors.append(
                "each occupied line must contain at least one blank inside its span"
            )
            break

    endpoint_colors = {value for _, _, value in cells}
    palette_kind = None
    if marker in (2, 3):
        if endpoint_colors == {marker}:
            palette_kind = "canonical"
        elif endpoint_colors == {1}:
            palette_kind = "single_blue"
        elif endpoint_colors == {4}:
            palette_kind = "single_yellow"
        elif endpoint_colors == {5, 6} and all(
            {value for value in row["colors"]} == {5, 6} for row in line_rows
        ):
            palette_kind = "mixed"
        elif cells:
            errors.append("endpoint palette does not match a declared palette_kind")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "marker": marker,
        "axis": axis,
        "lines": line_rows,
        "n_lines": len(line_rows),
        "points_per_line": counts[0] if counts and len(set(counts)) == 1 else None,
        "palette_kind": palette_kind,
        "endpoint_colors": endpoint_colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked teaching grammar; empty means lawful."""
    del difficulty, meta
    return list(_analyse(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require the exact canonical dimensions, counts, and marker-color palette."""
    analysis = _analyse(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) not in _CANONICAL_PROFILES:
        reasons.append("dimensions are not one of the three canonical profiles")
    if analysis["n_lines"] != 2:
        reasons.append("canonical inputs contain exactly two occupied lines")
    if analysis["points_per_line"] != 2:
        reasons.append("canonical inputs contain exactly two points per line")
    if analysis["palette_kind"] != "canonical":
        reasons.append("canonical endpoints use the axis-marker color")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from the returned input grid."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "axis": analysis["axis"],
        "n_lines": analysis["n_lines"],
        "points_per_line": analysis["points_per_line"],
        "palette_kind": analysis["palette_kind"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for task-local tests and rival definitions."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    axis = analysis["axis"]
    for line in analysis["lines"]:
        start, end = line["positions"][0], line["positions"][-1]
        for position in range(start, end + 1):
            if axis == "row":
                output[line["index"]][position] = 8
            else:
                output[position][line["index"]] = 8
    return output


def _rival_fixed_row(grid: list[list[int]]) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    cells = _foreground_without_marker(grid)
    by_row: dict[int, list[int]] = {}
    for row_index, col_index, _ in cells:
        by_row.setdefault(row_index, []).append(col_index)
    for row_index, columns in by_row.items():
        for col_index in range(min(columns), max(columns) + 1):
            output[row_index][col_index] = 8
    return output


def _rival_fixed_col(grid: list[list[int]]) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    cells = _foreground_without_marker(grid)
    by_col: dict[int, list[int]] = {}
    for row_index, col_index, _ in cells:
        by_col.setdefault(col_index, []).append(row_index)
    for col_index, rows in by_col.items():
        for row_index in range(min(rows), max(rows) + 1):
            output[row_index][col_index] = 8
    return output


def _rival_preserve_endpoint_color(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for line in analysis["lines"]:
        color = line["colors"][0]
        start, end = line["positions"][0], line["positions"][-1]
        for position in range(start, end + 1):
            if analysis["axis"] == "row":
                output[line["index"]][position] = color
            else:
                output[position][line["index"]] = color
    return output


def _rival_same_color_groups(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: close independent same-color groups instead of whole lines."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for line in analysis["lines"]:
        positions_by_color: dict[int, list[int]] = {}
        if analysis["axis"] == "row":
            for position in line["positions"]:
                positions_by_color.setdefault(grid[line["index"]][position], []).append(position)
        else:
            for position in line["positions"]:
                positions_by_color.setdefault(grid[position][line["index"]], []).append(position)
        for positions in positions_by_color.values():
            if len(positions) < 2:
                continue
            for position in range(min(positions), max(positions) + 1):
                if analysis["axis"] == "row":
                    output[line["index"]][position] = 8
                else:
                    output[position][line["index"]] = 8
    return output


def _rival_keep_marker(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    output[0][0] = grid[0][0]
    return output


def _is_axis(grid: list[list[int]], axis: str) -> bool:
    analysis = _analyse(grid)
    return not analysis["errors"] and analysis["axis"] == axis


def _witness_canonical_anchor(grid: list[list[int]]) -> bool:
    return not strict_canonical_like(grid)


def _witness_row_mode(grid: list[list[int]]) -> bool:
    return _is_axis(grid, "row") and _rival_fixed_col(grid) != rule_mirror(grid)


def _witness_col_mode(grid: list[list[int]]) -> bool:
    return _is_axis(grid, "col") and _rival_fixed_row(grid) != rule_mirror(grid)


def _witness_color_agnostic_fill(grid: list[list[int]]) -> bool:
    analysis = _analyse(grid)
    return (
        not analysis["errors"]
        and analysis["palette_kind"] != "canonical"
        and _rival_preserve_endpoint_color(grid) != rule_mirror(grid)
    )


def _witness_mixed_colors_share_line(grid: list[list[int]]) -> bool:
    analysis = _analyse(grid)
    return (
        not analysis["errors"]
        and analysis["palette_kind"] == "mixed"
        and _rival_same_color_groups(grid) != rule_mirror(grid)
    )


def _witness_marker_removed(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _rival_keep_marker(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canonical_anchor": _witness_canonical_anchor,
    "row_marker_selects_row_closure": _witness_row_mode,
    "column_marker_selects_column_closure": _witness_col_mode,
    "endpoint_colors_do_not_set_output_color": _witness_color_agnostic_fill,
    "mixed_colors_close_as_one_line": _witness_mixed_colors_share_line,
    "control_marker_is_removed": _witness_marker_removed,
}

SEMANTIC_RIVALS = {
    "fixed_row": _rival_fixed_row,
    "fixed_col": _rival_fixed_col,
    "preserve_endpoint_color": _rival_preserve_endpoint_color,
    "same_color_groups": _rival_same_color_groups,
    "keep_marker": _rival_keep_marker,
}

WITNESS_RIVALS = {
    "canonical_anchor": ["keep_marker"],
    "row_marker_selects_row_closure": ["fixed_col"],
    "column_marker_selects_column_closure": ["fixed_row"],
    "endpoint_colors_do_not_set_output_color": ["preserve_endpoint_color"],
    "mixed_colors_close_as_one_line": ["same_color_groups"],
    "control_marker_is_removed": ["keep_marker"],
}

LESSON_COMPETITORS = {
    "fixed_row": _rival_fixed_row,
    "fixed_col": _rival_fixed_col,
    "preserve_endpoint_color": _rival_preserve_endpoint_color,
    "keep_marker": _rival_keep_marker,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named wrong rule survives demos but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes that the structural checker must reject."""
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_marker = full_grid(8, 9, 0)
    no_marker[2][1] = 2
    no_marker[2][5] = 2
    fixtures.append(("no_axis_marker", no_marker))

    marker_only = full_grid(8, 9, 0)
    marker_only[0][0] = 2
    fixtures.append(("marker_without_lines", marker_only))

    marker_row_leak = full_grid(8, 9, 0)
    marker_row_leak[0][0] = 2
    marker_row_leak[0][5] = 2
    marker_row_leak[3][1] = 2
    marker_row_leak[3][5] = 2
    fixtures.append(("foreground_on_marker_row", marker_row_leak))

    singleton_line = full_grid(8, 9, 0)
    singleton_line[0][0] = 2
    singleton_line[3][4] = 2
    fixtures.append(("singleton_occupied_line", singleton_line))

    adjacent_points = full_grid(8, 9, 0)
    adjacent_points[0][0] = 2
    adjacent_points[3][4] = 2
    adjacent_points[3][5] = 2
    fixtures.append(("no_blank_inside_span", adjacent_points))

    uneven_counts = full_grid(8, 9, 0)
    uneven_counts[0][0] = 2
    uneven_counts[2][1] = 2
    uneven_counts[2][5] = 2
    uneven_counts[5][1] = 2
    uneven_counts[5][3] = 2
    uneven_counts[5][6] = 2
    fixtures.append(("unequal_points_per_line", uneven_counts))

    output_color_input = full_grid(8, 9, 0)
    output_color_input[0][0] = 2
    output_color_input[3][1] = 8
    output_color_input[3][5] = 8
    fixtures.append(("output_color_leaks_into_input", output_color_input))

    wrong_axis_color = full_grid(8, 9, 0)
    wrong_axis_color[0][0] = 2
    wrong_axis_color[3][1] = 3
    wrong_axis_color[3][5] = 3
    fixtures.append(("opposite_marker_color_as_endpoint", wrong_axis_color))

    return [(name, copy.deepcopy(grid)) for name, grid in fixtures]
