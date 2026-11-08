"""Generator for ``easy_134_fill_between_matching_row_markers``.

For each row containing exactly two nonzero markers of the same color, fill
that inclusive horizontal span with the marker color.  Blank rows, one-marker
rows, and rows whose two markers have different colors stay unchanged.

The four-profile schedule is deliberate.  Every four consecutive examples
contain a canonical anchor, a mismatched-pair control, a one-marker control,
and a repeated-color/boundary control.  This prevents the common shortcuts
"fill between any pair", "extend every marker", and "fill one bounding box per
color" from surviving a lesson merely because the public canonical pairs do
not contain those controls.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "641108b687a1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "139629635146"

SUMMARY = (
    "In each row, if and only if there are exactly two nonzero markers and "
    "their colors match, fill every cell from the left marker through the "
    "right marker with that color. Leave blank rows, one-marker rows, and "
    "different-color marker pairs unchanged."
)

INVARIANTS = [
    "background is literal color 0",
    "every nonblank row contains one marker or exactly two separated markers",
    "matching marker pairs are the only rows changed by the rule",
    "different-color pairs and single markers are explicit unchanged controls",
    "every generated scene contains at least three matching rows",
    "every generated scene uses exactly three foreground colors",
    "four consecutive sample indexes cover every decisive curriculum profile",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_SPECS = {
    # h, w, matching rows, mismatched rows, single-marker rows
    "canonical_anchor": (7, 10, 3, 0, 0),
    "mismatched_pair_control": (6, 11, 3, 1, 0),
    "single_marker_and_reuse": (8, 12, 4, 0, 1),
    "boundary_and_both_controls": (7, 9, 3, 1, 1),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile sample-index cycle",
        "valid": "canonical_anchor|mismatched_pair_control|single_marker_and_reuse|boundary_and_both_controls",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _row_kind(row: list[int] | tuple[int, ...]) -> tuple[str, tuple[int, ...], tuple[int, ...]]:
    """Return (kind, columns, colors) for the task's row grammar."""
    marked = [(column, value) for column, value in enumerate(row) if value != 0]
    columns = tuple(column for column, _ in marked)
    colors = tuple(value for _, value in marked)
    if not marked:
        return "blank", columns, colors
    if len(marked) == 1:
        return "single", columns, colors
    if len(marked) != 2:
        return "overfull", columns, colors
    if columns[1] - columns[0] < 2:
        return "adjacent_pair", columns, colors
    if colors[0] == colors[1]:
        return "matching", columns, colors
    return "mismatched", columns, colors


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    rows = []
    counts: Counter[str] = Counter()
    foreground: set[int] = set()
    for row_index, row in enumerate(grid):
        kind, columns, colors = _row_kind(row)
        counts[kind] += 1
        foreground.update(colors)
        rows.append(
            {
                "row": row_index,
                "kind": kind,
                "columns": columns,
                "colors": colors,
            }
        )
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "rows": rows,
        "counts": counts,
        "foreground": foreground,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural input grammar and reject rule-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    counts = analysis["counts"]
    if counts["overfull"]:
        errors.append("a nonblank row has more than two markers")
    if counts["adjacent_pair"]:
        errors.append("a marker pair is adjacent, hiding the fill operation")
    if counts["matching"] == 0:
        errors.append("at least one separated same-color marker pair is required")

    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None:
        observed = _profile_of(grid)
        if observed != requested:
            errors.append(
                f"scene profile drifted from {requested!r} to {observed!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the task-linked canonical scale and row semantics."""
    errors = list(self_check(grid))
    if errors:
        return errors
    analysis = _analysis(grid)
    height, width = analysis["height"], analysis["width"]
    if not (6 <= height <= 8 and 9 <= width <= 12):
        errors.append(
            f"dimensions {(height, width)} fall outside canonical 6..8 by 9..12"
        )
    if analysis["counts"]["matching"] < 3:
        errors.append("canonical-like scenes require at least three matching rows")
    if len(analysis["foreground"]) != 3:
        errors.append("canonical-like scenes use exactly three foreground colors")
    return errors


def _profile_signature(grid: Any) -> tuple[int, int, int, int, int, int] | None:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    counts = analysis["counts"]
    if counts["overfull"] or counts["adjacent_pair"]:
        return None
    return (
        analysis["height"],
        analysis["width"],
        counts["matching"],
        counts["mismatched"],
        counts["single"],
        len(analysis["foreground"]),
    )


_PROFILE_BY_SIGNATURE = {
    (*spec, 3): profile for profile, spec in SCENE_SPECS.items()
}


def _profile_of(grid: Any) -> str | None:
    signature = _profile_signature(grid)
    return _PROFILE_BY_SIGNATURE.get(signature)


def observe_overrides(grid) -> dict[str, str]:
    """Recover the one exact declared axis from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError(f"grid signature {_profile_signature(grid)!r} is not declared")
    return {"scene_profile": profile}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every consecutive four indexes contain all decisive profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _pair_columns(rng, width: int, *, full_width: bool = False) -> tuple[int, int]:
    if full_width:
        return 0, width - 1
    # Keep both margins visible so a whole-row-fill shortcut is observably wrong.
    left = rng.randint(1, max(1, width - 4))
    right = rng.randint(left + 2, width - 2)
    return left, right


def _paint_pair(grid, row: int, left: int, right: int, left_color: int, right_color: int) -> None:
    grid[row][left] = left_color
    grid[row][right] = right_color


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    height, width, matching_count, mismatch_count, single_count = SCENE_SPECS[profile]

    colors = ctx.draw_distinct_colors("foreground_palette", n=3, exclude={0})
    layout_rng = ctx.draw_rng(f"layout:{profile}:{difficulty or 'medium'}")
    active_count = matching_count + mismatch_count + single_count
    active_rows = layout_rng.sample(range(height), active_count)
    matching_rows = active_rows[:matching_count]
    mismatch_rows = active_rows[matching_count:matching_count + mismatch_count]
    single_rows = active_rows[matching_count + mismatch_count:]

    # The reuse profile repeats colors[0] on two matching rows.  Other profiles
    # use all three colors and may repeat only after the first three rows.
    if profile == "single_marker_and_reuse":
        matching_colors = (colors[0], colors[1], colors[2], colors[0])
    else:
        matching_colors = tuple(colors[index % 3] for index in range(matching_count))

    grid = full_grid(height, width, 0)
    for index, (row, color) in enumerate(zip(matching_rows, matching_colors)):
        full_width = profile == "boundary_and_both_controls" and index == 0
        left, right = _pair_columns(layout_rng, width, full_width=full_width)
        _paint_pair(grid, row, left, right, color, color)

    for index, row in enumerate(mismatch_rows):
        left, right = _pair_columns(layout_rng, width)
        left_color = colors[index % 3]
        right_color = colors[(index + 1) % 3]
        _paint_pair(grid, row, left, right, left_color, right_color)

    for index, row in enumerate(single_rows):
        # Never place at the last column: the explicit single-marker rival must
        # have room to make a visibly wrong extension.
        column = layout_rng.randint(0, width - 2)
        grid[row][column] = colors[(index + 2) % 3]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"scene_profile": profile}},
    )
    if errors:
        raise RuntimeError(f"constructed invalid scene for {profile}: {errors}")
    return [row[:] for row in grid]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        kind, columns, colors = _row_kind(row)
        if kind != "matching":
            continue
        left, right = columns
        color = colors[0]
        for column in range(left, right + 1):
            output[row_index][column] = color
    return output


def _fill_between_any_pair(grid):
    """Wrong: ignores the requirement that the two marker colors match."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        kind, columns, colors = _row_kind(row)
        if kind not in ("matching", "mismatched"):
            continue
        left, right = columns
        for column in range(left, right + 1):
            output[row_index][column] = colors[0]
    return output


def _extend_single_markers_right(grid):
    """Wrong: applies the fill idea to a row containing only one marker."""
    output = rule_mirror(grid)
    for row_index, row in enumerate(grid):
        kind, columns, colors = _row_kind(row)
        if kind == "single":
            for column in range(columns[0], len(row)):
                output[row_index][column] = colors[0]
    return output


def _fill_same_color_bounding_boxes(grid):
    """Wrong: joins all occurrences of each color by one rectangle."""
    output = [list(row) for row in grid]
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column, color in enumerate(row):
            if color:
                by_color.setdefault(color, []).append((row_index, column))
    for color, cells in by_color.items():
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(column for _, column in cells)
        max_col = max(column for _, column in cells)
        for row in range(min_row, max_row + 1):
            for column in range(min_col, max_col + 1):
                output[row][column] = color
    return output


def _fill_entire_matching_rows(grid):
    """Wrong: identifies the right rows but paints from edge to edge."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        kind, _, colors = _row_kind(row)
        if kind == "matching":
            output[row_index] = [colors[0]] * len(row)
    return output


def _skip_boundary_spans(grid):
    """Wrong: fills matching pairs only when neither endpoint touches an edge."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        kind, columns, colors = _row_kind(row)
        if kind != "matching":
            continue
        left, right = columns
        if left == 0 or right == len(row) - 1:
            continue
        for column in range(left, right + 1):
            output[row_index][column] = colors[0]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fill_between_any_pair": _fill_between_any_pair,
    "extend_single_markers_right": _extend_single_markers_right,
    "fill_same_color_bounding_boxes": _fill_same_color_bounding_boxes,
    "fill_entire_matching_rows": _fill_entire_matching_rows,
    "skip_boundary_spans": _skip_boundary_spans,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fill_between_any_pair": _fill_between_any_pair,
    "extend_single_markers_right": _extend_single_markers_right,
    "fill_same_color_bounding_boxes": _fill_same_color_bounding_boxes,
}


def _witness_mismatched_pair(grid) -> bool:
    return _analysis(grid).get("counts", Counter())["mismatched"] > 0


def _witness_single_marker(grid) -> bool:
    for row in _analysis(grid).get("rows", []):
        if row["kind"] == "single" and row["columns"][0] < len(grid[0]) - 1:
            return True
    return False


def _witness_reused_matching_color(grid) -> bool:
    colors = [
        row["colors"][0]
        for row in _analysis(grid).get("rows", [])
        if row["kind"] == "matching"
    ]
    return any(count >= 2 for count in Counter(colors).values())


def _witness_interior_matching_span(grid) -> bool:
    width = len(grid[0]) if grid else 0
    return any(
        row["kind"] == "matching"
        and row["columns"][0] > 0
        and row["columns"][1] < width - 1
        for row in _analysis(grid).get("rows", [])
    )


def _witness_boundary_matching_span(grid) -> bool:
    width = len(grid[0]) if grid else 0
    return any(
        row["kind"] == "matching"
        and (row["columns"][0] == 0 or row["columns"][1] == width - 1)
        for row in _analysis(grid).get("rows", [])
    )


SEMANTIC_WITNESSES = {
    "mismatched_pair_stays_unfilled": _witness_mismatched_pair,
    "single_marker_stays_unextended": _witness_single_marker,
    "reused_color_is_still_row_local": _witness_reused_matching_color,
    "interior_span_stops_at_markers": _witness_interior_matching_span,
    "boundary_span_is_not_skipped": _witness_boundary_matching_span,
}

WITNESS_RIVALS = {
    "mismatched_pair_stays_unfilled": ["fill_between_any_pair"],
    "single_marker_stays_unextended": ["extend_single_markers_right"],
    "reused_color_is_still_row_local": ["fill_same_color_bounding_boxes"],
    "interior_span_stops_at_markers": ["fill_entire_matching_rows"],
    "boundary_span_is_not_skipped": ["skip_boundary_spans"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named plausible wrong rule survives."""
    reasons: list[str] = []
    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the rule domain: {exc}")
            continue
        if expected != pair.get("output"):
            reasons.append(f"pair {index} output disagrees with the row-span rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_all_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name} crashed: {exc}")
            continue
        if fits_all_demos:
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons
