"""Input generator for canonical task 964b23808a3c.

For every column whose last non-zero marker is color 5, the unchanged Racket
rule fills from the top through successive markers.  Each segment takes the
color of its lower/current marker.  Columns whose last marker is not 5 are
left untouched, and rows below a floating terminator stay unchanged.

The four-pair schedule deliberately alternates clean canonical-scale examples
with two shortcut-refuting examples.  Python mirrors and rival functions are
review/test instrumentation only; the selected Racket program remains label
authority.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "964b23808a3c"
TASK_ID = GENERATOR_ID
RULE_HASH = "c7e69da25375"
VERSION = "3.0.2"
SUMMARY = (
    "In each column whose last nonzero marker is 5, fill from row 0 through "
    "successive markers using the current/lower marker's color. Leave other "
    "columns and rows below a floating terminator unchanged. A four-profile "
    "curriculum covers all canonical size/palette profiles and includes "
    "distractor columns, internal-5 traps, top gaps, and floating terminators."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every cell is an integer color 0..9",
    "1..3 target columns have 2..5 markers and last nonzero color 5",
    "each target contains a non-5 marker and a top gap, so the rule is nontrivial",
    "mixed profiles contain lawful non-target columns, including an internal-5 trap",
    "floating profiles leave at least one unchanged row below every terminator",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor 7|12|13|17",
        "valid": "7..20",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor 7|12|13|17",
        "valid": "7..20",
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled 1|2|2|3",
        "valid": "1..3",
    },
    "n_marks_per_target": {
        "type": "int",
        "default": "scheduled 2|4|3|5",
        "valid": "2..5",
    },
    "distractor_mode": {
        "type": "enum",
        "default": "scheduled none|none|mixed|mixed",
        "valid": "none|mixed",
    },
    "terminator_position": {
        "type": "enum",
        "default": "scheduled bottom|bottom|floating|floating",
        "valid": "bottom|floating",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_PROFILE_SPECS = (
    {
        "name": "minimal",
        "grid_h": 7,
        "grid_w": 7,
        "n_targets": 1,
        "n_marks_per_target": 2,
        "distractor_mode": "none",
        "terminator_position": "bottom",
        "palette_size": 3,
        "nonzero_count": 2,
    },
    {
        "name": "clean",
        "grid_h": 12,
        "grid_w": 12,
        "n_targets": 2,
        "n_marks_per_target": 4,
        "distractor_mode": "none",
        "terminator_position": "bottom",
        "palette_size": 7,
        "nonzero_count": 8,
    },
    {
        "name": "noisy",
        "grid_h": 13,
        "grid_w": 13,
        "n_targets": 2,
        "n_marks_per_target": 3,
        "distractor_mode": "mixed",
        "terminator_position": "floating",
        "palette_size": 9,
        "nonzero_count": 19,
    },
    {
        "name": "dense",
        "grid_h": 17,
        "grid_w": 17,
        "n_targets": 3,
        "n_marks_per_target": 5,
        "distractor_mode": "mixed",
        "terminator_position": "floating",
        "palette_size": 10,
        "nonzero_count": 31,
    },
)
SCHEDULE_PROFILES = tuple(spec["name"] for spec in _PROFILE_SPECS)
_ACTIVE_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_entrypoint(seed: int, sample_index: int) -> None:
    """Reject coercible scalar aliases before they reach profile/RNG logic."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive draws contain all four curriculum profiles."""
    _validate_entrypoint(seed, sample_index)
    del difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _profile_spec(sample_index: int) -> dict[str, Any]:
    return _PROFILE_SPECS[sample_index % len(_PROFILE_SPECS)]


def _validate_call(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    _validate_entrypoint(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _draw_exact_choice(ctx, label: str, scheduled: str, choices: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _target_rows(height: int, count: int, position: str, rng) -> list[int]:
    terminator = height - 1 if position == "bottom" else height - 2
    candidates = list(range(1, terminator))
    if len(candidates) < count - 1:
        raise ValueError(
            f"grid_h={height} cannot fit {count} target marks with {position} terminator"
        )
    # When geometry permits, reserve a blank row immediately above the
    # terminator.  This guarantees a nonempty marker-to-marker segment that
    # distinguishes current-marker color from the previous-marker shortcut.
    preferred = candidates[:-1]
    source = preferred if len(preferred) >= count - 1 else candidates
    rows = sorted(rng.sample(source, count - 1))
    return rows + [terminator]


def _paint_targets(
    grid: list[list[int]],
    target_columns: list[int],
    rows_by_column: list[list[int]],
    active_colors: list[int],
) -> set[int]:
    nonfinal_slots = sum(len(rows) - 1 for rows in rows_by_column)
    if nonfinal_slots < 1:
        raise AssertionError("target construction needs a non-5 marker")
    assigned = [active_colors[index % len(active_colors)] for index in range(nonfinal_slots)]
    used: set[int] = set()
    cursor = 0
    for column, rows in zip(target_columns, rows_by_column):
        for row in rows[:-1]:
            color = assigned[cursor]
            cursor += 1
            grid[row][column] = color
            used.add(color)
        grid[rows[-1]][column] = 5
    return used


def _add_mixed_distractors(
    grid: list[list[int]],
    target_columns: set[int],
    active_colors: list[int],
    used_colors: set[int],
    desired_nonzero: int,
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    distractor_columns = [column for column in range(width) if column not in target_columns]
    if len(distractor_columns) < 2:
        raise ValueError("mixed distractors require at least two non-target columns")
    rng.shuffle(distractor_columns)
    trap_column, plain_column = distractor_columns[:2]
    first = active_colors[0]
    second = active_colors[1 % len(active_colors)]

    # A column that contains 5 but ends in another color.  The authority leaves
    # it unchanged; the canonical-fitting 'any 5' shortcut transforms it.
    trap_rows = sorted({1, max(2, height // 2), height - 1})
    while len(trap_rows) < 3:
        trap_rows.append(trap_rows[-1] + 1)
    trap_rows = trap_rows[:3]
    for row, color in zip(trap_rows, (first, 5, second)):
        grid[row][trap_column] = color
        if color != 5:
            used_colors.add(color)

    # A separate multi-mark column with no 5 makes the column-selection branch
    # visible independently of the internal-5 trap.
    plain_rows = (0, height - 2)
    for index, row in enumerate(plain_rows):
        color = active_colors[(index + 2) % len(active_colors)]
        grid[row][plain_column] = color
        used_colors.add(color)

    candidates = [
        (row, column)
        for column in distractor_columns
        for row in range(height)
        if grid[row][column] == 0
    ]
    rng.shuffle(candidates)

    # Realize every requested non-5 palette color before adding arbitrary
    # texture.  Profile palette counts are therefore exact, not probabilistic.
    missing = [color for color in active_colors if color not in used_colors]
    for color in missing:
        if not candidates:
            raise AssertionError("insufficient distractor cells for palette coverage")
        row, column = candidates.pop()
        grid[row][column] = color
        used_colors.add(color)

    current = sum(value != 0 for row in grid for value in row)
    target = max(desired_nonzero, current)
    while current < target:
        if not candidates:
            raise AssertionError("insufficient distractor cells for requested density")
        row, column = candidates.pop()
        grid[row][column] = active_colors[rng.randrange(len(active_colors))]
        current += 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = _profile_spec(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", profile["grid_h"], 7, 20)
    width = _draw_exact_int(ctx, "grid_w", profile["grid_w"], 7, 20)
    n_targets = _draw_exact_int(ctx, "n_targets", profile["n_targets"], 1, 3)
    n_marks = _draw_exact_int(
        ctx, "n_marks_per_target", profile["n_marks_per_target"], 2, 5
    )
    distractor_mode = _draw_exact_choice(
        ctx, "distractor_mode", profile["distractor_mode"], ("none", "mixed")
    )
    terminator_position = _draw_exact_choice(
        ctx,
        "terminator_position",
        profile["terminator_position"],
        ("bottom", "floating"),
    )

    band_salt = difficulty or "none"
    layout_rng = ctx.draw_rng(f"layout:{band_salt}")
    palette_rng = ctx.draw_rng(f"palette:{band_salt}")
    all_columns = list(range(width))
    target_columns = sorted(layout_rng.sample(all_columns, n_targets))
    rows_by_column = [
        _target_rows(height, n_marks, terminator_position, ctx.draw_rng(f"rows:{band_salt}:{column}"))
        for column in target_columns
    ]

    palette = list(_ACTIVE_COLORS)
    palette_rng.shuffle(palette)
    target_slots = n_targets * (n_marks - 1)
    if distractor_mode == "none":
        active_count = min(profile["palette_size"] - 2, target_slots)
    else:
        active_count = min(profile["palette_size"] - 2, len(_ACTIVE_COLORS))
    active_count = max(1, active_count)
    active_colors = palette[:active_count]

    grid = full_grid(height, width, 0)
    used_colors = _paint_targets(grid, target_columns, rows_by_column, active_colors)
    if distractor_mode == "mixed":
        no_axis_override = not any(
            name in overrides and overrides[name] is not None for name in AXES
        )
        desired_nonzero = profile["nonzero_count"] if no_axis_override else (
            n_targets * n_marks + max(8, active_count + 3)
        )
        # Alternate the dense profile between the canonical train/test nonzero
        # counts (31 and 51) without changing its exact shape/palette profile.
        if no_axis_override and profile["name"] == "dense" and (sample_index // 4) % 2:
            desired_nonzero = 51
        _add_mixed_distractors(
            grid,
            set(target_columns),
            active_colors,
            used_colors,
            desired_nonzero,
            ctx.draw_rng(f"distractors:{band_salt}"),
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_targets": n_targets,
        "n_marks_per_target": n_marks,
        "distractor_mode": distractor_mode,
        "terminator_position": terminator_position,
    }
    if observed != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Validation, observation, and independent authoring mirror
# ---------------------------------------------------------------------------


def _shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a list or tuple"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "expected a nonempty rectangular grid"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "cells must be integer colors in 0..9 (not bool)"
    return None


def _column_marks(grid, column: int) -> list[tuple[int, int]]:
    return [(row, grid[row][column]) for row in range(len(grid)) if grid[row][column] != 0]


def _target_columns(grid) -> list[tuple[int, list[tuple[int, int]]]]:
    result = []
    for column in range(len(grid[0])):
        marks = _column_marks(grid, column)
        if marks and marks[-1][1] == 5:
            result.append((column, marks))
    return result


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only by tests and semantic probes."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for column in range(width):
        marks = [row for row in range(height) if grid[row][column] != 0]
        if not marks or grid[marks[-1]][column] != 5:
            continue
        previous = -1
        for row in marks:
            color = grid[row][column]
            for fill_row in range(previous + 1, row + 1):
                out[fill_row][column] = color
            previous = row
    return out


# Backward-compatible private name used by some review tooling.
_mirror = rule_mirror


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    errors: list[str] = []
    targets = _target_columns(grid)
    if not targets:
        errors.append("expected at least one column whose last nonzero marker is 5")
        return errors
    for column, marks in targets:
        if len(marks) < 2:
            errors.append(f"col {column}: target needs at least two markers")
        if all(color == 5 for _, color in marks):
            errors.append(f"col {column}: target needs at least one non-5 marker")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule would be a no-op")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    targets = _target_columns(grid)
    counts = {len(marks) for _, marks in targets}
    if len(counts) != 1:
        raise ValueError("target columns do not share one n_marks_per_target value")
    target_set = {column for column, _ in targets}
    has_distractor = any(
        column not in target_set and _column_marks(grid, column)
        for column in range(len(grid[0]))
    )
    bottom_rows = {marks[-1][0] for _, marks in targets}
    if bottom_rows == {len(grid) - 1}:
        terminator_position = "bottom"
    elif all(row < len(grid) - 1 for row in bottom_rows):
        terminator_position = "floating"
    else:
        raise ValueError("target terminators mix bottom and floating positions")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": len(targets),
        "n_marks_per_target": counts.pop(),
        "distractor_mode": "mixed" if has_distractor else "none",
        "terminator_position": terminator_position,
    }


# ---------------------------------------------------------------------------
# Plausible rival rules and assembled-lesson contract
# ---------------------------------------------------------------------------


def _selected_columns(grid, predicate: Callable[[list[tuple[int, int]], int], bool]):
    for column in range(len(grid[0])):
        marks = _column_marks(grid, column)
        if marks and predicate(marks, column):
            yield column, marks


def _apply_current_segments(grid, selector, *, start_at_first=False):
    out = copy.deepcopy(grid)
    for column, marks in _selected_columns(grid, selector):
        previous = marks[0][0] - 1 if start_at_first else -1
        for row, color in marks:
            for fill_row in range(previous + 1, row + 1):
                out[fill_row][column] = color
            previous = row
    return out


def _between_marks_use_previous_color(grid):
    out = copy.deepcopy(grid)
    for column, marks in _selected_columns(grid, lambda marks, _c: marks[-1][1] == 5):
        first_row, first_color = marks[0]
        for row in range(0, first_row + 1):
            out[row][column] = first_color
        for index in range(1, len(marks)):
            previous_row, previous_color = marks[index - 1]
            current_row, _ = marks[index]
            for row in range(previous_row + 1, current_row):
                out[row][column] = previous_color
    return out


def _start_at_first_marker(grid):
    return _apply_current_segments(
        grid, lambda marks, _c: marks[-1][1] == 5, start_at_first=True
    )


def _fill_every_multimark_column(grid):
    return _apply_current_segments(grid, lambda marks, _c: len(marks) >= 2)


def _any_column_containing_5(grid):
    return _apply_current_segments(
        grid, lambda marks, _c: any(color == 5 for _, color in marks)
    )


def _bottom_row_5_only(grid):
    bottom = len(grid) - 1
    return _apply_current_segments(
        grid, lambda marks, _c: marks[-1] == (bottom, 5)
    )


def _extend_5_below_terminator(grid):
    out = rule_mirror(grid)
    for column, marks in _target_columns(grid):
        for row in range(marks[-1][0] + 1, len(grid)):
            out[row][column] = 5
    return out


SEMANTIC_RIVALS = {
    "between_marks_use_previous_color": _between_marks_use_previous_color,
    "start_at_first_marker": _start_at_first_marker,
    "fill_every_multimark_column": _fill_every_multimark_column,
    "any_column_containing_5": _any_column_containing_5,
    "bottom_row_5_only": _bottom_row_5_only,
    "extend_5_below_terminator": _extend_5_below_terminator,
}
CANONICAL_SHORTCUTS = {
    "any_column_containing_5": _any_column_containing_5,
    "bottom_row_5_only": _bottom_row_5_only,
    "extend_5_below_terminator": _extend_5_below_terminator,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_top_gap(grid) -> bool:
    return any(marks[0][0] > 0 for _, marks in _target_columns(grid))


def _uses_current_marker_color(grid) -> bool:
    return _between_marks_use_previous_color(grid) != rule_mirror(grid)


def _has_distractor_counterexample(grid) -> bool:
    return _fill_every_multimark_column(grid) != rule_mirror(grid)


def _has_internal_five_distractor(grid) -> bool:
    for column in range(len(grid[0])):
        marks = _column_marks(grid, column)
        if marks and marks[-1][1] != 5 and any(color == 5 for _, color in marks):
            return _any_column_containing_5(grid) != rule_mirror(grid)
    return False


def _has_floating_terminator(grid) -> bool:
    return any(marks[-1][0] < len(grid) - 1 for _, marks in _target_columns(grid))


SEMANTIC_WITNESSES = {
    "top_gap": _has_top_gap,
    "current_marker_color": _uses_current_marker_color,
    "distractor_column": _has_distractor_counterexample,
    "internal_five_distractor": _has_internal_five_distractor,
    "floating_terminator": _has_floating_terminator,
}
WITNESS_RIVALS = {
    "top_gap": ["start_at_first_marker"],
    "current_marker_color": ["between_marks_use_previous_color"],
    "distractor_column": ["fill_every_multimark_column"],
    "internal_five_distractor": ["any_column_containing_5"],
    "floating_terminator": ["bottom_row_5_only", "extend_5_below_terminator"],
}
BRANCH_WITNESSES = (
    "distractor_column",
    "internal_five_distractor",
    "floating_terminator",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject an assembled lesson when a declared rival fits demos but changes query."""
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            findings.append(f"{name}: rival evaluation failed: {exc!r}")
            continue
        if fits and changes_query:
            findings.append(f"{name}: fits every demonstration but changes the query")
    return findings
