"""Generator for ARC task e048c9ed.

A single color-5 marker in row 0 selects an output column.  Monochrome
horizontal bars occupy alternating rows below it and stop strictly before the
marker column.  The Racket rule writes a one-digit squared length code at that
column for every bar row:

* normally ``(bar_length - 1) ** 2 mod 10``;
* when the non-5 bars contain one repeated length, bars of any other length use
  ``(bar_length - repeated_length) ** 2 mod 10``.

Rows whose bar color is 5 are deliberately excluded when the repeated length
is selected, matching the canonical program.  The five-slot schedule contains two answer-changing color-5 exclusions and
two duplicate-length scenes whose bars begin on row 2.  Consequently every
cyclic window of four default samples refutes both the plausible shortcut that
counts color-5 bars when selecting the repeated length and the shortcut that
applies duplicate adjustment only when bars begin on row 1.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fe97c2dd8a4"
VERSION = "2.2.1"
TASK_ID = "9fe97c2dd8a4"
RULE_HASH = "c7281f787d6e"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = tuple(range(5))

# Declaring the empty matrix opts into the strict override contract.  Dynamic
# geometric conflicts are instead attached to the ValueError that reports
# them, so the checker can verify the exact participating axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

SUMMARY = (
    "A row-0 color-5 marker selects a column. Alternating monochrome bars "
    "write squared length codes there; one repeated non-5 length changes the "
    "code for the other lengths, while color-5 bars are excluded from the "
    "repeated-length census."
)

INVARIANTS = [
    "background is color 0 and the marker row contains exactly one nonzero cell, color 5",
    "1..6 monochrome contiguous horizontal bars lie on alternating rows below the marker",
    "every bar has length at least 2 and ends strictly before the marker column",
    "at least one bar is not color 5",
    "eligible non-5 bar lengths are either all distinct or have exactly one repeated value plus a distinct value",
]

_H_MIN, _H_MAX = 4, 14
_W_MIN, _W_MAX = 3, 18
_BAR_MIN, _BAR_MAX = 1, 6

AXES = {
    "grid_h": {
        "type": "int",
        "default": "banded 4..8 easy, 6..11 medium, 9..14 hard; grows to fit bars",
        "valid": "4..14",
    },
    "grid_w": {
        "type": "int",
        "default": "banded 3..8 easy, 6..13 medium, 10..18 hard; grows to fit marker",
        "valid": "3..18",
    },
    "marker_col": {
        "type": "int",
        "default": "rng 2..grid_w-1 (>=3 for repeated-length scenes)",
        "valid": "2..w-1",
    },
    "bar_count": {
        "type": "int",
        "default": "scheduled 3/4/4/5 then banded random 1..6",
        "valid": "1..6",
    },
    "duplicate_mode": {
        "type": "bool",
        "default": "scheduled false,true,false,true then rng",
        "valid": "false|true",
    },
}


def schedule_profile(
    seed: int, sample_index: int, difficulty: str | None = None
) -> int:
    """Expose the deterministic five-way curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _incompatible(message: str, *axes: str) -> ValueError:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    return exc

# Exact canonical (height, width, marker column, bar rows/lengths, palette)
# profiles.  A 30% no-override prior anchors the real canonical envelope while
# colors and horizontal offsets remain freshly sampled.
_CANONICAL_PROFILES = (
    {
        "grid_h": 4,
        "grid_w": 3,
        "marker_col": 2,
        "row_start": 2,
        "lengths": (2,),
        "duplicate_mode": False,
        "include_five": False,
        "palette_size": 3,
    },
    {
        "grid_h": 10,
        "grid_w": 10,
        "marker_col": 7,
        "row_start": 2,
        "lengths": (3, 2, 4, 5),
        "duplicate_mode": False,
        "include_five": False,
        "palette_size": 6,
    },
    {
        "grid_h": 8,
        "grid_w": 11,
        "marker_col": 9,
        "row_start": 1,
        "lengths": (2, 2, 5, 2),
        "duplicate_mode": True,
        "include_five": False,
        "palette_size": 6,
    },
    {
        "grid_h": 6,
        "grid_w": 6,
        "marker_col": 5,
        "row_start": 1,
        "lengths": (2, 3, 4),
        "duplicate_mode": False,
        "include_five": False,
        "palette_size": 3,
    },
    {
        "grid_h": 10,
        "grid_w": 12,
        "marker_col": 4,
        "row_start": 2,
        "lengths": (2, 3, 2, 4),
        "duplicate_mode": False,
        "include_five": True,
        "five_index": 2,
        "palette_size": 4,
    },
)


def _coerce_bool(value: Any, *, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise ValueError(f"{label} must be bool or 'true'/'false', got {value!r}")


def _pin_int(ctx, label: str, value: int, lo: int, hi: int) -> int:
    """Record an internally scheduled exact value through GenCtx."""
    ctx.overrides[label] = value
    return ctx.draw_int_strict(label, lo, hi)


def _pin_bool(ctx, label: str, value: bool) -> bool:
    ctx.overrides[label] = value
    return bool(ctx.draw_choice(label, [False, True]))


def _max_bars(grid_h: int, row_start: int) -> int:
    if row_start >= grid_h:
        return 0
    return min(_BAR_MAX, ((grid_h - 1 - row_start) // 2) + 1)


def _minimum_height(bar_count: int, row_start: int) -> int:
    return row_start + 2 * (bar_count - 1) + 1


def _bar_rows(grid: list[list[int]], marker_col: int | None = None) -> list[int]:
    if not grid:
        return []
    rows = []
    for r in range(1, len(grid)):
        if any(value != 0 for value in grid[r]):
            rows.append(r)
    return rows


def _bar_info(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return structural information for every nonempty row below row 0."""
    info: list[dict[str, Any]] = []
    for r in _bar_rows(grid):
        cells = [(c, value) for c, value in enumerate(grid[r]) if value != 0]
        colors = {value for _, value in cells}
        info.append(
            {
                "row": r,
                "positions": [c for c, _ in cells],
                "colors": colors,
                "color": next(iter(colors)) if len(colors) == 1 else None,
                "length": len(cells),
            }
        )
    return info


def _duplicate_state(grid: list[list[int]]) -> tuple[bool, int | None]:
    eligible = [
        row["length"]
        for row in _bar_info(grid)
        if row["color"] is not None and row["color"] != 5
    ]
    counts = Counter(eligible)
    repeated = [length for length, count in counts.items() if count > 1]
    return (len(repeated) == 1 and len(counts) >= 2,
            repeated[0] if len(repeated) == 1 else None)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone scenes, including all canonical
    inputs as lawful members of the teaching grammar."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width
                         for row in grid):
        return ["ragged grid"]

    height = len(grid)
    errs: list[str] = []
    if not (_H_MIN <= height <= _H_MAX and _W_MIN <= width <= _W_MAX):
        errs.append(
            f"dims {height}x{width} outside {_H_MIN}..{_H_MAX} x "
            f"{_W_MIN}..{_W_MAX}"
        )
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errs.append("grid contains a non-integer or color outside 0..9")

    marker_cells = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    marker_col = None
    if len(marker_cells) != 1 or marker_cells[0][1] != 5:
        errs.append(
            "row 0 must contain exactly one nonzero marker cell of color 5"
        )
    else:
        marker_col = marker_cells[0][0]
        if marker_col < 2:
            errs.append("marker column must be at least 2 so bars have length >=2")

    info = _bar_info(grid)
    if not (_BAR_MIN <= len(info) <= _BAR_MAX):
        errs.append(f"expected {_BAR_MIN}..{_BAR_MAX} bar rows, found {len(info)}")
    rows = [row["row"] for row in info]
    if len(rows) >= 2 and any(b - a != 2 for a, b in zip(rows, rows[1:])):
        errs.append("bar rows must be alternating with exactly one blank row between")

    non_five = 0
    for row in info:
        positions = row["positions"]
        if row["color"] is None:
            errs.append(f"row {row['row']} contains more than one bar color")
        elif row["color"] != 5:
            non_five += 1
        if not positions:
            continue
        if positions != list(range(positions[0], positions[-1] + 1)):
            errs.append(f"row {row['row']} bar is not contiguous")
        if row["length"] < 2:
            errs.append(f"row {row['row']} bar length {row['length']} is below 2")
        if marker_col is not None and positions[-1] >= marker_col:
            errs.append(
                f"row {row['row']} reaches marker column {marker_col}; bars must stop before it"
            )

    if non_five == 0:
        errs.append("at least one bar must use a color other than 5")

    eligible_lengths = [
        row["length"] for row in info
        if row["color"] is not None and row["color"] != 5
    ]
    counts = Counter(eligible_lengths)
    repeated = [length for length, count in counts.items() if count > 1]
    if len(repeated) > 1:
        errs.append(
            f"multiple repeated eligible lengths {sorted(repeated)} make the anchor ambiguous"
        )
    elif len(repeated) == 1 and len(counts) < 2:
        errs.append(
            "a repeated eligible length needs at least one distinct eligible length"
        )
    return errs


def observe_overrides(grid) -> dict[str, int | bool | None]:
    """Recover every exact non-dimension axis from the returned grid."""
    marker_col = None
    if grid and grid[0]:
        row0 = [c for c, value in enumerate(grid[0]) if value != 0]
        if len(row0) == 1 and grid[0][row0[0]] == 5:
            marker_col = row0[0]
    duplicate_mode, _ = _duplicate_state(grid)
    return {
        "marker_col": marker_col,
        "bar_count": len(_bar_info(grid)),
        "duplicate_mode": duplicate_mode,
    }


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is intentionally the task's canonical manifold."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription of the unchanged canonical Racket rule."""
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    marker = next(
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 5
    )
    marker_row, marker_col = marker
    bars: list[tuple[int, int]] = []
    for r in range(height):
        length = sum(
            1
            for c in range(width)
            if grid[r][c] != 0 and not (r == marker_row and c == marker_col)
        )
        if length:
            bars.append((r, length))

    eligible_lengths = [
        length
        for r, length in bars
        if all(grid[r][c] != 5 for c in range(width))
    ]
    duplicate = next(
        (length for length in eligible_lengths
         if eligible_lengths.count(length) > 1),
        None,
    )
    for r, length in bars:
        base = length - duplicate if duplicate is not None and length != duplicate else length - 1
        out[r][marker_col] = (base * base) % 10
    return out


def _include_color_5_in_duplicate_census(
    grid: list[list[int]],
) -> list[list[int]]:
    """Plausible wrong rule: count gray/color-5 bars as duplicate evidence.

    This shortcut reproduces all four public training demonstrations because
    they contain no color-5 bar.  The canonical held-out test and the repaired
    generated curriculum both falsify it.
    """
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    marker_row, marker_col = next(
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 5
    )
    bars: list[tuple[int, int]] = []
    for r in range(height):
        length = sum(
            1
            for c in range(width)
            if grid[r][c] != 0
            and not (r == marker_row and c == marker_col)
        )
        if length:
            bars.append((r, length))

    all_lengths = [length for _, length in bars]
    duplicate = next(
        (length for length in all_lengths if all_lengths.count(length) > 1),
        None,
    )
    for r, length in bars:
        base = (
            length - duplicate
            if duplicate is not None and length != duplicate
            else length - 1
        )
        out[r][marker_col] = (base * base) % 10
    return out


def _duplicate_adjustment_only_when_bars_start_row_1(
    grid: list[list[int]],
) -> list[list[int]]:
    """Plausible wrong rule: row placement gates duplicate-length semantics.

    It applies the canonical repeated-length adjustment only when the first bar
    begins on row 1.  Otherwise every bar receives the ordinary ``length - 1``
    code.  The canonical examples do not refute this correlation, so generated
    lessons must include an answer-changing duplicate scene beginning on row 2.
    """
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    marker_row, marker_col = next(
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 5
    )
    bars: list[tuple[int, int]] = []
    for r in range(height):
        length = sum(
            1
            for c in range(width)
            if grid[r][c] != 0
            and not (r == marker_row and c == marker_col)
        )
        if length:
            bars.append((r, length))

    duplicate = None
    if bars and bars[0][0] == 1:
        eligible_lengths = [
            length
            for r, length in bars
            if all(grid[r][c] != 5 for c in range(width))
        ]
        duplicate = next(
            (
                length
                for length in eligible_lengths
                if eligible_lengths.count(length) > 1
            ),
            None,
        )

    for r, length in bars:
        base = (
            length - duplicate
            if duplicate is not None and length != duplicate
            else length - 1
        )
        out[r][marker_col] = (base * base) % 10
    return out


def _has_five_bar(grid) -> bool:
    return any(row["color"] == 5 for row in _bar_info(grid))


def _has_multiple_bar_colors(grid) -> bool:
    return len({row["color"] for row in _bar_info(grid)}) >= 2


def _starts_on_row(grid, row: int) -> bool:
    rows = _bar_rows(grid)
    return bool(rows) and rows[0] == row


def _has_unique_adjustment(grid) -> bool:
    duplicate_mode, duplicate = _duplicate_state(grid)
    if not duplicate_mode or duplicate is None:
        return False
    return any(
        row["color"] != 5 and row["length"] != duplicate
        for row in _bar_info(grid)
    )


def _five_exclusion_changes_answer(grid) -> bool:
    return (
        _has_five_bar(grid)
        and _include_color_5_in_duplicate_census(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "ordinary_no_duplicate": lambda grid: not _duplicate_state(grid)[0],
    "repeated_length_with_unique_adjustment": _has_unique_adjustment,
    "color_5_distractor_bar": _has_five_bar,
    "color_5_exclusion_changes_answer": _five_exclusion_changes_answer,
    "multiple_bar_colors": _has_multiple_bar_colors,
    "bars_start_row_1": lambda grid: _starts_on_row(grid, 1),
    "bars_start_row_2": lambda grid: _starts_on_row(grid, 2),
}

BRANCH_WITNESSES = {
    "ordinary_no_duplicate",
    "repeated_length_with_unique_adjustment",
    "color_5_distractor_bar",
    "multiple_bar_colors",
    "bars_start_row_1",
    "bars_start_row_2",
}

SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "include_color_5_in_duplicate_census": (
        _include_color_5_in_duplicate_census
    ),
}

WITNESS_RIVALS = {
    "color_5_exclusion_changes_answer": [
        "include_color_5_in_duplicate_census"
    ],
}

# These executable alternatives are lesson competitors, not claims about the
# selected authority.  The row-start rival fits every canonical pair, while the
# color-5 census rival fits the four canonical demonstrations; generated lessons
# must refute both before the query.
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "duplicate_adjustment_only_when_bars_start_row_1": (
        _duplicate_adjustment_only_when_bars_start_row_1
    ),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful outputs and refute every declared lesson competitor."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, received {len(demos)}"
        )
        return reasons

    demo_inputs = []
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        if output != rule_mirror(grid):
            reasons.append(f"demo {index} output does not match the canonical rule")
            continue
        demo_inputs.append(grid)

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query output does not match the canonical rule")

    if demo_inputs:
        if not any(not _duplicate_state(grid)[0] for grid in demo_inputs):
            reasons.append("demonstrations omit the ordinary no-duplicate branch")
        if not any(_has_unique_adjustment(grid) for grid in demo_inputs):
            reasons.append("demonstrations omit the repeated-length adjustment branch")
        if not any(_has_five_bar(grid) for grid in demo_inputs):
            reasons.append("demonstrations omit the color-5 distractor-bar case")
        lengths = {
            row["length"]
            for grid in demo_inputs
            for row in _bar_info(grid)
            if row["color"] != 5
        }
        if len(lengths) < 3:
            reasons.append("demonstrations expose fewer than three eligible bar lengths")

        for name, competitor in LESSON_COMPETITORS.items():
            if all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
            ):
                reasons.append(
                    f"demonstrations do not refute rival: {name}"
                )
    return reasons


def _select_profile(ctx, phase: int, overrides: dict[str, Any]):
    # Phases 1 and 3 are deterministic row-2 duplicate witnesses.  Phase 0
    # always anchors an exact ordinary canonical profile; the other eligible
    # slots retain the 30% prior.  This makes per-band canonical support robust
    # to VERSION-driven RNG changes instead of relying on a lucky census.
    if overrides or phase in (1, 3):
        return None
    if phase == 0:
        choices = (_CANONICAL_PROFILES[0], _CANONICAL_PROFILES[1],
                   _CANONICAL_PROFILES[3])
    else:
        if ctx.draw_rng("canonical_prior").random() >= 0.30:
            return None
        if phase == 2:
            choices = (_CANONICAL_PROFILES[4],)
        else:
            choices = _CANONICAL_PROFILES
    return ctx.draw_rng("canonical_profile").choice(choices)


def _choose_dimensions_and_axes(ctx, overrides, profile, phase, difficulty):
    raw_h = overrides.get("grid_h")
    raw_w = overrides.get("grid_w")
    raw_marker = overrides.get("marker_col")
    raw_count = overrides.get("bar_count")
    raw_duplicate = overrides.get("duplicate_mode")

    if raw_duplicate is not None:
        duplicate_requested = _coerce_bool(raw_duplicate, label="duplicate_mode")
        overrides["duplicate_mode"] = duplicate_requested
        ctx.overrides["duplicate_mode"] = duplicate_requested
    else:
        duplicate_requested = phase in (1, 3)
        if phase == 4:
            duplicate_requested = ctx.draw_rng("duplicate_mode_default").random() < 0.5

    include_five = phase in (2, 3)
    if phase == 4:
        include_five = ctx.draw_rng("five_bar_default").random() < 0.35

    if profile is not None:
        grid_w = _pin_int(ctx, "grid_w", profile["grid_w"], _W_MIN, _W_MAX)
        marker_col = _pin_int(
            ctx, "marker_col", profile["marker_col"], 2, grid_w - 1
        )
        bar_count = _pin_int(
            ctx, "bar_count", len(profile["lengths"]), _BAR_MIN, _BAR_MAX
        )
        duplicate_mode = _pin_bool(
            ctx, "duplicate_mode", bool(profile["duplicate_mode"])
        )
        row_start = int(profile["row_start"])
        grid_h = _pin_int(ctx, "grid_h", profile["grid_h"], _H_MIN, _H_MAX)
        return grid_h, grid_w, marker_col, bar_count, duplicate_mode, row_start, bool(profile["include_five"])

    band = difficulty or "medium"
    if band == "easy":
        w_lo, w_hi = 3, 8
        h_lo, h_hi = 4, 8
        count_lo, count_hi = 1, 3
    elif band == "hard":
        w_lo, w_hi = 10, 18
        h_lo, h_hi = 9, 14
        count_lo, count_hi = 3, 6
    else:
        w_lo, w_hi = 6, 13
        h_lo, h_hi = 6, 11
        count_lo, count_hi = 2, 5

    # Exact semantic overrides are band-independent.  In particular,
    # duplicate_mode=true may need four bars when the scheduled sample also
    # carries a color-5 distractor, even on the easy band.
    if raw_duplicate is not None and duplicate_requested:
        count_hi = _BAR_MAX

    explicit_w = raw_w is not None
    explicit_marker = raw_marker is not None
    if explicit_w:
        grid_w = ctx.draw_int_strict("grid_w", _W_MIN, _W_MAX)
    elif explicit_marker:
        marker_value = int(raw_marker)
        if not 2 <= marker_value <= _W_MAX - 1:
            raise ValueError(f"marker_col={marker_value} outside 2..{_W_MAX - 1}")
        grid_w = ctx.draw_int_strict("grid_w", max(_W_MIN, marker_value + 1), _W_MAX)
    else:
        # Default scheduled scenes reserve enough distinct lengths that phases
        # 0/1 do not accidentally need gray filler bars, while phases 2/3 have
        # at least two non-gray lengths for an answer-changing gray witness.
        scheduled_marker_lo = {0: 4, 1: 4, 2: 4, 3: 4}.get(phase, 2)
        min_width = max(
            4 if duplicate_requested else _W_MIN,
            scheduled_marker_lo + 1,
        )
        grid_w = ctx.draw_int_strict("grid_w", max(w_lo, min_width), max(w_hi, min_width))

    if explicit_marker:
        marker_col = ctx.draw_int_strict("marker_col", 2, _W_MAX - 1)
        if marker_col >= grid_w:
            raise _incompatible(
                f"marker_col={marker_col} must be smaller than grid_w={grid_w}",
                "marker_col",
                "grid_w",
            )
    else:
        marker_lo = 3 if duplicate_requested and grid_w >= 4 else 2
        if raw_w is None:
            marker_lo = max(
                marker_lo,
                {0: 4, 1: 4, 2: 4, 3: 4}.get(phase, 2),
            )
        if marker_lo > grid_w - 1:
            marker_lo = 2
        marker_col = ctx.draw_int_strict("marker_col", marker_lo, grid_w - 1)

    if duplicate_requested and marker_col < 3:
        if raw_duplicate is not None:
            conflict_axis = "marker_col" if raw_marker is not None else "grid_w"
            raise _incompatible(
                f"duplicate_mode=true needs {conflict_axis} to permit "
                f"marker_col >= 3, got {marker_col}",
                "duplicate_mode",
                conflict_axis,
            )
        duplicate_requested = False

    row_start = 2
    explicit_h = raw_h is not None
    explicit_count = raw_count is not None
    h_value = int(raw_h) if explicit_h else None
    if explicit_h and not _H_MIN <= h_value <= _H_MAX:
        raise ValueError(f"grid_h={h_value} outside {_H_MIN}..{_H_MAX}")

    # When only grid_h is exact, adapt the free row phase/count.  When both
    # exact quantities conflict, reject the multi-axis case loudly.
    if explicit_h and _max_bars(h_value, row_start) == 0:
        row_start = 1
    if explicit_h and explicit_count:
        count_value = int(raw_count)
        if not _BAR_MIN <= count_value <= _BAR_MAX:
            raise ValueError(f"bar_count={count_value} outside {_BAR_MIN}..{_BAR_MAX}")
        if _max_bars(h_value, row_start) < count_value and _max_bars(h_value, 1) >= count_value:
            row_start = 1
        if _max_bars(h_value, row_start) < count_value:
            raise _incompatible(
                f"bar_count={count_value} cannot fit alternating rows in grid_h={h_value}",
                "bar_count",
                "grid_h",
            )

    max_from_h = _max_bars(h_value, row_start) if explicit_h else _BAR_MAX
    min_for_branch = 3 if duplicate_requested else 1
    if include_five:
        min_for_branch = max(min_for_branch, 4 if duplicate_requested else 2)

    if explicit_count:
        bar_count = ctx.draw_int_strict("bar_count", _BAR_MIN, _BAR_MAX)
    else:
        scheduled = {0: 3, 1: 4, 2: 4, 3: 5}.get(phase)
        if scheduled is not None:
            target = min(max(scheduled, min_for_branch), max_from_h)
            if target < min_for_branch:
                if raw_duplicate is not None and duplicate_requested:
                    raise _incompatible(
                        f"duplicate_mode=true cannot fit grid_h={h_value}",
                        "duplicate_mode",
                        "grid_h",
                    )
                duplicate_requested = False
                min_for_branch = 2 if include_five else 1
                target = min(max(scheduled, min_for_branch), max_from_h)
            bar_count = _pin_int(ctx, "bar_count", target, _BAR_MIN, _BAR_MAX)
        else:
            # An exact small grid_h is a lawful single-axis request even on
            # the hard band; its geometry, not the band's ordinary lower
            # bound, determines the free bar-count domain.
            base_count_lo = _BAR_MIN if explicit_h else count_lo
            lo = max(base_count_lo, min_for_branch)
            hi = min(count_hi, max_from_h)
            if hi < lo:
                if raw_duplicate is not None and duplicate_requested:
                    conflict_axis = "grid_h" if explicit_h else "bar_count"
                    raise _incompatible(
                        "duplicate_mode=true has no feasible bar_count for "
                        f"{conflict_axis}",
                        "duplicate_mode",
                        conflict_axis,
                    )
                duplicate_requested = False
                if include_five and max_from_h < 2:
                    include_five = False
                lo = max(base_count_lo, 2 if include_five else 1)
                hi = min(count_hi, max_from_h)
            if hi < lo:
                lo = hi = max_from_h
            bar_count = ctx.draw_int_strict("bar_count", lo, hi)

    if duplicate_requested and bar_count < 3:
        if raw_duplicate is not None:
            raise _incompatible(
                f"duplicate_mode=true needs bar_count >= 3, got {bar_count}",
                "duplicate_mode",
                "bar_count",
            )
        duplicate_requested = False
    if include_five and bar_count < 2:
        include_five = False

    if explicit_h:
        grid_h = ctx.draw_int_strict("grid_h", _H_MIN, _H_MAX)
        if _max_bars(grid_h, row_start) < bar_count and _max_bars(grid_h, 1) >= bar_count:
            row_start = 1
        if _max_bars(grid_h, row_start) < bar_count:
            raise _incompatible(
                f"bar_count={bar_count} cannot fit alternating rows in grid_h={grid_h}",
                "bar_count",
                "grid_h",
            )
    else:
        min_height = _minimum_height(bar_count, row_start)
        if explicit_count:
            grid_h = ctx.draw_int_strict("grid_h", max(_H_MIN, min_height), _H_MAX)
        else:
            lo = max(h_lo, min_height)
            hi = max(h_hi, lo)
            grid_h = ctx.draw_int_strict("grid_h", lo, min(hi, _H_MAX))

    duplicate_mode = (
        bool(ctx.draw_choice("duplicate_mode", [False, True]))
        if raw_duplicate is not None
        else _pin_bool(ctx, "duplicate_mode", duplicate_requested)
    )
    return grid_h, grid_w, marker_col, bar_count, duplicate_mode, row_start, include_five


def _make_lengths_and_colors(
    ctx,
    *,
    marker_col: int,
    bar_count: int,
    duplicate_mode: bool,
    include_five: bool,
    phase: int,
    profile,
):
    rng = ctx.draw_rng("bar_semantics")
    domain = list(range(2, marker_col + 1))
    if duplicate_mode and len(domain) < 2:
        raise _incompatible(
            "duplicate_mode requires marker_col >= 3 for two possible bar lengths",
            "duplicate_mode",
            "marker_col",
        )

    if profile is not None:
        lengths = list(profile["lengths"])
        five_indices = set()
        if profile["include_five"]:
            five_indices.add(int(profile.get("five_index", len(lengths) - 1)))
        non_five_palette_count = int(profile["palette_size"]) - 2
    else:
        max_eligible = len(domain) + (1 if duplicate_mode else 0)
        eligible_count = min(bar_count, max_eligible)
        if duplicate_mode:
            eligible_count = max(3, eligible_count)
        else:
            eligible_count = max(1, eligible_count)
        if include_five and bar_count >= 2:
            eligible_count = min(eligible_count, bar_count - 1)
            if duplicate_mode:
                eligible_count = max(3, eligible_count)
        five_count = bar_count - eligible_count
        if include_five and five_count == 0 and bar_count > (3 if duplicate_mode else 1):
            five_count = 1
            eligible_count -= 1
        indices = list(range(bar_count))
        rng.shuffle(indices)
        five_indices = set(indices[:five_count])

        non_five_indices = [i for i in range(bar_count) if i not in five_indices]
        lengths = [0] * bar_count
        if duplicate_mode:
            def ordinary_code(length: int) -> int:
                return ((length - 1) * (length - 1)) % 10

            def duplicate_code(length: int, anchor: int) -> int:
                base = length - anchor if length != anchor else length - 1
                return (base * base) % 10

            anchor_candidates = []
            for candidate in domain:
                changing = [
                    value
                    for value in domain
                    if value != candidate
                    and duplicate_code(value, candidate) != ordinary_code(value)
                ]
                if changing:
                    anchor_candidates.append((candidate, changing))
            if not anchor_candidates:
                raise _incompatible(
                    "duplicate_mode needs an answer-changing distinct length",
                    "duplicate_mode",
                    "marker_col",
                )
            anchor, changing_values = rng.choice(anchor_candidates)
            witness = rng.choice(changing_values)
            remaining = [
                value for value in domain if value not in {anchor, witness}
            ]
            rng.shuffle(remaining)
            values = [anchor, anchor, witness] + remaining[: max(0, len(non_five_indices) - 3)]
            rng.shuffle(values)
            for i, value in zip(non_five_indices, values):
                lengths[i] = value
        else:
            values = rng.sample(domain, len(non_five_indices))
            for i, value in zip(non_five_indices, values):
                lengths[i] = value
        for i in five_indices:
            lengths[i] = rng.choice(domain)

        if len(non_five_indices) >= 2:
            # The duplicate-only lesson has four eligible bars, so use four
            # distinct non-gray colors there.  Besides varying irrelevant color
            # identity, this keeps the canonical six-color palette reachable in
            # the exact distribution-gate census.
            if phase == 1:
                non_five_palette_count = 4
            elif phase in (2, 3):
                non_five_palette_count = 2
            else:
                non_five_palette_count = 1
            if phase == 4:
                non_five_palette_count = rng.randint(1, min(4, len(non_five_indices)))
            non_five_palette_count = min(non_five_palette_count, len(non_five_indices))
        else:
            non_five_palette_count = 1

    colors_pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(colors_pool)
    palette = colors_pool[:non_five_palette_count]
    non_five_indices = [i for i in range(bar_count) if i not in five_indices]
    assigned = []
    for i in range(len(non_five_indices)):
        assigned.append(palette[i % len(palette)])
    rng.shuffle(assigned)
    colors = [5 if i in five_indices else 0 for i in range(bar_count)]
    for i, color in zip(non_five_indices, assigned):
        colors[i] = color

    # In every ordinary scheduled gray scene, make the exclusion of color 5
    # causally observable.  A gray bar repeats a non-gray length.  For the
    # no-duplicate phase this creates a false anchor only for the rival.  For
    # the true duplicate phase, place a gray/unique-length pair before the
    # real repeated anchor so the rival selects the wrong repeated length.
    if profile is None and include_five and five_indices:
        non_five_indices = [
            i for i in range(bar_count) if i not in five_indices
        ]
        counts = Counter(lengths[i] for i in non_five_indices)
        intended_duplicate = next(
            (
                lengths[i]
                for i in non_five_indices
                if counts[lengths[i]] > 1
            ),
            None,
        )
        if duplicate_mode:
            candidates = [
                i for i in non_five_indices if counts[lengths[i]] == 1
            ]
        else:
            candidates = (
                list(non_five_indices) if len(counts) >= 2 else []
            )

        def encoded(length: int, duplicate: int | None) -> int:
            base = (
                length - duplicate
                if duplicate is not None and length != duplicate
                else length - 1
            )
            return (base * base) % 10

        # Merely changing which length is called the duplicate is not enough:
        # modulo-10 squaring can collide.  Select a gray-matched length only
        # when it provably changes at least one output digit.
        candidates = [
            i
            for i in candidates
            if any(
                encoded(lengths[j], intended_duplicate)
                != encoded(lengths[j], lengths[i])
                for j in non_five_indices
            )
        ]

        if candidates:
            matched_non_five = candidates[0]
            witness_length = lengths[matched_non_five]
            ordered_five = sorted(five_indices)
            for i in ordered_five:
                lengths[i] = witness_length
            order = [ordered_five[0], matched_non_five]
            order.extend(i for i in ordered_five[1:])
            order.extend(
                i for i in non_five_indices if i != matched_non_five
            )
            lengths = [lengths[i] for i in order]
            colors = [colors[i] for i in order]
    return lengths, colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty is not None and type(difficulty) is not str:
        raise TypeError("difficulty must be None or one of: easy, medium, hard")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None or one of: easy, medium, hard")

    overrides = dict(overrides)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "marker_col", "bar_count"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    phase = sample_index % 5
    profile = _select_profile(ctx, phase, overrides)
    (
        grid_h,
        grid_w,
        marker_col,
        bar_count,
        duplicate_mode,
        row_start,
        include_five,
    ) = _choose_dimensions_and_axes(
        ctx, overrides, profile, phase, difficulty
    )
    lengths, colors = _make_lengths_and_colors(
        ctx,
        marker_col=marker_col,
        bar_count=bar_count,
        duplicate_mode=duplicate_mode,
        include_five=include_five,
        phase=phase,
        profile=profile,
    )

    layout_rng = ctx.draw_rng("bar_placement")
    grid = full_grid(grid_h, grid_w, 0)
    grid[0][marker_col] = 5
    for index, (length, color) in enumerate(zip(lengths, colors)):
        row = row_start + 2 * index
        start = layout_rng.randint(0, marker_col - length)
        for col in range(start, start + length):
            grid[row][col] = color
    return grid
